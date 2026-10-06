#!/usr/bin/env python3
"""Run the isolated HYPIC + MatMulAllReduce canary/performance iteration."""

from __future__ import annotations

import hashlib
import json
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from assess_hypic_e2e_gates import validate_performance_record


ROOT = Path("/cache/cch/hypic-qwen36-e2e-2048-20261006")
OUT = ROOT / "candidate-matmul-allreduce"
HERE = Path(__file__).resolve().parent
CANARY = HERE.parent / "WS-20260904-qwen38-dense-paper-to-ascend" / "hypic_semantic_canary.py"
BENCHMARK = Path("/cache/cch/hypic_vllm_ascend-v0.8.5/tools/benchmark_shared_prefix.py")
SERVICE = HERE / "matmul_allreduce_service.py"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name: str, value: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def status(stage: str, **data: object) -> None:
    write("iteration-status.json", {
        "schema": "hypic-matmul-allreduce-iteration-status/v1",
        "at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        **data,
    })
    print(json.dumps({"stage": stage, **data}, sort_keys=True), flush=True)


def run_logged(name: str, args: list[str], timeout: int) -> None:
    try:
        result = subprocess.run(args, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        (OUT / name).write_text(str(exc) + "\n", encoding="utf-8")
        raise RuntimeError(f"{name} timed out after {timeout}s") from exc
    (OUT / name).write_text(result.stdout or "", encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"{name} exit={result.returncode}: {(result.stdout or '')[-2000:]}")


def canary() -> None:
    status("canary-running")
    result = OUT / "semantic-canary.json"
    if result.exists():
        raise RuntimeError("candidate canary artifact already exists; refusing overwrite")
    run_logged("semantic-canary.log", [
        sys.executable, str(CANARY), "--base-url", "http://127.0.0.1:8223",
        "--model", "qwen36-hypic-e2e-2048",
        "--phase", "candidate-matmul-allreduce", "--output", str(result),
        "--timeout", "2400",
    ], 2700)
    candidate = json.loads(result.read_text(encoding="utf-8"))
    references = {
        arm: json.loads((ROOT / arm / "semantic-canary.json").read_text(encoding="utf-8"))
        for arm in ("no-cache", "hypic-only")
    }
    failures: list[str] = []
    if candidate.get("schema") != "hypic-active-semantic-canary/v1":
        failures.append("candidate schema")
    if candidate.get("input_tokens") != 32768 or candidate.get("answer_contains_key") is not True:
        failures.append("candidate prompt length or answer key")
    if candidate.get("request") != references["hypic-only"].get("request"):
        failures.append("candidate request protocol")
    for key in ("prompt_token_sha256", "public_segment_token_sha256", "segment_ends"):
        if candidate.get(key) != references["no-cache"].get(key) or candidate.get(key) != references["hypic-only"].get(key):
            failures.append(f"candidate/reference {key} mismatch")
    normalize = lambda item: " ".join(item.get("response_text", "").split())
    if normalize(candidate) != normalize(references["no-cache"]) or normalize(candidate) != normalize(references["hypic-only"]):
        failures.append("deterministic response mismatch")
    gate = {
        "schema": "hypic-matmul-allreduce-canary-gate/v1",
        "passed": not failures,
        "failures": failures,
        "candidate_sha256": digest(result),
        "reference_sha256": {arm: digest(ROOT / arm / "semantic-canary.json") for arm in references},
        "response_sha256": {**{arm: references[arm].get("response_text_sha256") for arm in references},
                            "candidate": candidate.get("response_text_sha256")},
    }
    write("canary-gate.json", gate)
    if failures:
        raise RuntimeError(f"candidate canary rejected: {failures}")
    status("canary-passed", gate_sha256=digest(OUT / "canary-gate.json"))


def performance() -> None:
    summaries: list[dict] = []
    for index in (1, 2, 3):
        output = OUT / f"performance.run{index}.json"
        if output.exists():
            raise RuntimeError(f"candidate run{index} already exists; refusing overwrite")
        status("performance-running", run=index)
        args = [
            sys.executable, str(BENCHMARK),
            "--base-url", "http://127.0.0.1:8223",
            "--model", "qwen36-hypic-e2e-2048",
            "--input-tokens", "32768", "--prefix-tokens", "16384",
            "--output-tokens", "1024", "--requests", "40",
            "--concurrency", "16", "--warmup-requests", "2",
            "--warmup-evidence-timeout", "300", "--timeout", "2400",
            "--json-output", str(output),
        ]
        if index == 1:
            args.extend(["--evidence-file", str(OUT / "hypic-evidence.jsonl"),
                         "--require-hot-path"])
        run_logged(f"performance.run{index}.log", args, 3000)
        record = json.loads(output.read_text(encoding="utf-8"))
        summary = validate_performance_record(record, "hypic-only", index)
        summaries.append(summary)
        status("performance-run-verified", run=index, artifact_sha256=digest(output),
               ttft_p95_ms=summary["ttft_p95_ms"], tpot_p95_ms=summary["tpot_p95_ms"],
               output_tokens_per_second=summary["output_tokens_per_second"],
               benchmark_duration_s=summary["benchmark_duration_s"])

    references = {}
    for arm in ("no-cache", "hypic-only"):
        references[arm] = [
            validate_performance_record(
                json.loads((ROOT / arm / f"performance.run{index}.json").read_text(encoding="utf-8")),
                arm, index,
            )
            for index in (1, 2, 3)
        ]
    criteria = {
        "ttft_p95_ms": ("lower", 30.0),
        "tpot_p95_ms": ("lower", 10.0),
        "output_tokens_per_second": ("higher", 20.0),
        "benchmark_duration_s": ("lower", 15.0),
    }
    comparisons = {}
    for reference_arm, reference_rows in references.items():
        comparisons[reference_arm] = {}
        for metric, (direction, threshold) in criteria.items():
            reference = statistics.median(float(row[metric]) for row in reference_rows)
            candidate = statistics.median(float(row[metric]) for row in summaries)
            improvement = (reference - candidate) / reference if direction == "lower" else (candidate - reference) / reference
            comparisons[reference_arm][metric] = {
                "reference_median": reference,
                "candidate_median": candidate,
                "improvement_percent": 100 * improvement,
                "threshold_percent": threshold,
                "passed": 100 * improvement >= threshold,
            }
    gate = {
        "schema": "hypic-matmul-allreduce-performance-comparison/v1",
        "candidate_kind": "HYPIC plus separate MatMulAllReduce optimization; not HYPIC paper-only gain",
        "original_paper_only_gate_remains_unchanged": True,
        "matched_protocol": "32768 input, 16384 prefix, 1024 output, 40 requests, concurrency 16, 3 runs",
        "comparisons": comparisons,
        "candidate_run_sha256": {
            str(index): digest(OUT / f"performance.run{index}.json") for index in (1, 2, 3)
        },
    }
    write("performance-comparison.json", gate)
    status("performance-complete", comparison_sha256=digest(OUT / "performance-comparison.json"))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    error = None
    try:
        canary()
        performance()
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        status("failed-before-cleanup", error=error)
    finally:
        try:
            run_logged("service-stop.log", [sys.executable, str(SERVICE), "stop"], 240)
            status("released", prior_error=error)
        except Exception as exc:
            status("cleanup-failed", prior_error=error, cleanup_error=f"{type(exc).__name__}: {exc}")
            return 3
    return 2 if error else 0


if __name__ == "__main__":
    raise SystemExit(main())

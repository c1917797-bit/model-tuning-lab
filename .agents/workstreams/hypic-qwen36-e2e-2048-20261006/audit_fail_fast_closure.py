#!/usr/bin/env python3
"""Audit the rejected HYPIC run without pretending partial quality is paired evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "WS-20260904-qwen38-dense-paper-to-ascend"))
from audit_hypic_historical_reproduction import (  # noqa: E402
    atomic_json, audit_performance, load_object, sha256,
)


DEADLINE = datetime.fromisoformat("2026-10-07T11:39:37+00:00")
BASELINE_CONTAINER = "qwen36_hypic2048_quality41984_baseline_npu0_3_v1"
OWNED_CONTAINERS = (
    "qwen36_hypic2048_matmulallreduce_npu0_3_v1",
    BASELINE_CONTAINER,
    "qwen36_hypic2048_quality41984_treatment_npu0_3_v1",
)
METRICS = {
    "ttft_p95_ms": (30.0, False),
    "tpot_p95_ms": (10.0, False),
    "output_tokens_per_second": (20.0, True),
    "benchmark_duration_s": (15.0, False),
}


def canonical_sha(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def check_rows(path: Path, expected: int | None, errors: list[str]) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    indexes = [row.get("index") for row in rows]
    if expected is not None and sorted(indexes) != list(range(expected)):
        errors.append(f"{path}: incomplete or duplicate sample indexes")
    if len(indexes) != len(set(indexes)) or not all(isinstance(index, int) and index >= 0 for index in indexes):
        errors.append(f"{path}: invalid or duplicate sample index")
    for row in rows:
        usage = row.get("usage") or {}
        prompt = usage.get("prompt_tokens")
        completion = usage.get("completion_tokens")
        response = row.get("response_text")
        if not (
            row.get("ok") is True and row.get("error") is None
            and isinstance(response, str)
            and row.get("response_sha256") == hashlib.sha256(response.encode()).hexdigest()
            and isinstance(prompt, int) and prompt > 0
            and isinstance(completion, int) and 0 <= completion <= 2048
            and prompt + completion <= 41984
            and row.get("finish_reason") in ("stop", "length")
            and isinstance(row.get("correct"), bool)
        ):
            errors.append(f"{path}: invalid response, hash, context, or cap at index {row.get('index')}")
    return rows


def audit_performance_rejection(root: Path, gate: dict, errors: list[str]) -> list[dict]:
    hashes = gate.get("run_sha256", {})
    aggregate = {"performance_runs": {
        arm: [
            {"path": str(root / arm / f"performance.run{run}.json"),
             "sha256": hashes[arm][run - 1]}
            for run in (1, 2, 3)
        ] for arm in ("no-cache", "hypic-only")
    }}
    units = audit_performance(root, aggregate, errors)
    if len(units) != 6:
        errors.append("formal performance evidence does not contain six checked runs")
    failed = []
    for name, (minimum, higher_is_better) in METRICS.items():
        values = {
            arm: [load_object(root / arm / f"performance.run{run}.json")["summary"][name]
                  for run in (1, 2, 3)]
            for arm in ("no-cache", "hypic-only")
        }
        baseline = statistics.median(values["no-cache"])
        treatment = statistics.median(values["hypic-only"])
        improvement = 100 * ((treatment / baseline - 1) if higher_is_better
                             else (1 - treatment / baseline))
        reported = gate["metrics"][name]
        passed = improvement >= minimum
        if not (
            math.isclose(reported["baseline_median"], baseline, rel_tol=1e-9)
            and math.isclose(reported["treatment_median"], treatment, rel_tol=1e-9)
            and math.isclose(reported["improvement_percent"], improvement, rel_tol=1e-9)
            and reported["minimum_percent"] == minimum
            and reported["passed"] is passed
        ):
            errors.append(f"{name}: frozen performance gate differs from raw medians")
        if not passed:
            failed.append(name)
    if not (gate.get("passed") is False and sorted(gate.get("failures", [])) == sorted(failed)
            and failed):
        errors.append("paper-only rejection classification differs from raw results")
    return units


def audit_longbench(quality_root: Path, contract: dict, errors: list[str]) -> list[dict]:
    units = []
    for run in (1, 2, 3):
        stem = quality_root / "quality" / "no-cache" / f"longbenchv2.run{run}"
        summary_path = Path(f"{stem}.summary.json")
        rows_path = Path(f"{stem}.jsonl")
        summary = load_object(summary_path)
        rows = check_rows(rows_path, 127, errors)
        correct = sum(row["correct"] is True for row in rows)
        reasons = dict(Counter(row["finish_reason"] for row in rows))
        tokens = sum(row["usage"]["completion_tokens"] for row in rows)
        fp = contract["fingerprint"]
        if not (
            summary.get("schema") == "hypic-quality-eval/v1"
            and summary.get("dataset") == "longbenchv2"
            and summary.get("run_id") == f"run{run}"
            and summary.get("requests") == 127
            and summary.get("successful") == 127
            and summary.get("failed") == 0
            and summary.get("max_out_len") == 2048
            and summary.get("data_sha256") == fp["longbench_sha256"]
            and summary.get("evaluator_script_sha256") == fp["quality_evaluator_sha256"]
            and Path(summary.get("details_path", "")).resolve() == rows_path.resolve()
            and summary.get("details_sha256") == sha256(rows_path)
            and summary.get("correct") == correct
            and summary.get("completion_tokens") == tokens
            and summary.get("finish_reasons") == reasons
            and math.isclose(summary.get("accuracy_pct", -1), 100 * correct / 127, rel_tol=1e-9)
        ):
            errors.append(f"LongBench run {run}: summary differs from checked raw rows")
        longest = next((row for row in rows if row["index"] == 48), None)
        if longest is None or longest["usage"]["prompt_tokens"] != 39642:
            errors.append(f"LongBench run {run}: longest prompt missing or truncated")
        for field in ("difficulty", "length"):
            categories = {str(row.get(field)) for row in rows}
            reported = summary.get("category_accuracy_pct", {}).get(field, {})
            if categories != set(reported):
                errors.append(f"LongBench run {run}: {field} categories differ")
            for category in categories & set(reported):
                subset = [row for row in rows if str(row.get(field)) == category]
                value = 100 * sum(row["correct"] is True for row in subset) / len(subset)
                if not math.isclose(reported[category], value, rel_tol=1e-9):
                    errors.append(f"LongBench run {run}: {field}/{category} score differs")
        units.append({"run": run, "rows": len(rows), "correct": correct,
                      "summary_sha256": sha256(summary_path), "raw_sha256": sha256(rows_path)})
    return units


def audit_release(quality_root: Path, contract: dict, errors: list[str]) -> dict:
    started = load_object(quality_root / "no-cache/service-start.json")
    stopped = load_object(quality_root / "no-cache/service-stop.json")
    status = load_object(quality_root / "controller-status.json")
    if not (
        started.get("container") == stopped.get("container") == BASELINE_CONTAINER
        and started.get("container_id") == stopped.get("container_id")
        and started.get("physical_npus") == [0, 1, 2, 3]
        and started.get("max_model_len") == 41984
        and started.get("max_num_batched_tokens") == 41984
        and started.get("source_snapshot_sha256") == contract["fingerprint"]["source_snapshot_sha256"]
        and started.get("health_passed") is True
        and stopped.get("owned_npus_released") is True
        and stopped.get("port_released") is True
        and stopped.get("container_removed") is True
        and status.get("stage") == "quality-arm-released"
        and "evaluator exit -15" in str(status.get("prior_error"))
        and datetime.fromisoformat(stopped["stopped_at"]) <= DEADLINE
    ):
        errors.append("fail-fast controller, service identity, or stop receipt mismatch")
    npu = subprocess.run(["npu-smi", "info"], capture_output=True, text=True,
                         timeout=30, check=True).stdout
    for index in range(4):
        if f"No running processes found in NPU {index}" not in npu:
            errors.append(f"physical NPU{index} still has a running process")
    port = subprocess.run(["ss", "-ltnp", "( sport = :8223 )"], capture_output=True,
                          text=True, timeout=30, check=True).stdout
    if ":8223" in port:
        errors.append("service port 8223 still has a listener")
    absent = {}
    for name in OWNED_CONTAINERS:
        result = subprocess.run(["docker", "inspect", name], capture_output=True,
                                text=True, timeout=30, check=False)
        absent[name] = result.returncode != 0
        if not absent[name]:
            errors.append(f"owned experiment container remains: {name}")
    at_health = quality_root / "no-cache/npu-smi-at-health.txt"
    docker_top = quality_root / "no-cache/docker-top-at-health.txt"
    observed = {match.group(1): int(match.group(2)) for match in re.finditer(
        r"^\|\s*([0-3])\s+0\s*\|\s*(\d+)\s*\|\s*VLLMWorker_TP\b",
        at_health.read_text(encoding="utf-8"), re.M)}
    container_pids = {int(parts[0]) for line in docker_top.read_text(encoding="utf-8").splitlines()[1:]
                      if (parts := line.split()) and parts[0].isdigit()}
    if not (
        started.get("npu_smi_at_health_sha256") == sha256(at_health)
        and started.get("docker_top_at_health_sha256") == sha256(docker_top)
        and started.get("worker_pid_by_physical_npu") == observed
        and set(observed) == {"0", "1", "2", "3"}
        and len(set(observed.values())) == 4
        and set(observed.values()).issubset(container_pids)
    ):
        errors.append("physical NPU0-3 workers did not match exact container at health")
    return {"service_start_sha256": sha256(quality_root / "no-cache/service-start.json"),
            "service_stop_sha256": sha256(quality_root / "no-cache/service-stop.json"),
            "npu_smi_after": npu, "port_after": port, "owned_containers_absent": absent}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    quality_root = root / "quality-context-41984"
    errors: list[str] = []
    payload = {"schema": "hypic-fail-fast-independent-audit/v1",
               "generated_at": datetime.now(timezone.utc).isoformat(),
               "paper_algorithm_accepted": False,
               "quality_classification": "incomplete-fail-fast",
               "performance_classification": "rejected"}
    try:
        parent = load_object(root / "baseline-contract.json")
        contract = load_object(quality_root / "quality-context-contract.json")
        if parent.get("fingerprint_sha256") != canonical_sha(parent["fingerprint"]):
            errors.append("parent contract fingerprint mismatch")
        fp = contract["fingerprint"]
        if not (
            contract.get("fingerprint_sha256") == canonical_sha(fp)
            and fp.get("parent_baseline_fingerprint_sha256") == parent["fingerprint_sha256"]
            and fp.get("physical_npus") == [0, 1, 2, 3]
            and fp.get("quality_max_output_tokens") == 2048
            and fp.get("max_model_len") == 41984
            and fp.get("separate_from_performance_baseline") is True
            and fp.get("longbench_max_prompt_plus_cap") == 41690
        ):
            errors.append("quality context contract identity mismatch")
        gate = load_object(root / "performance-gate.json")
        payload["performance_units"] = audit_performance_rejection(root, gate, errors)
        payload["longbench_baseline_units"] = audit_longbench(quality_root, contract, errors)
        gsm_path = quality_root / "quality/no-cache/gsm8k.run1.jsonl"
        gsm = check_rows(gsm_path, None, errors)
        if not 0 < len(gsm) < 1319 or any(row["index"] >= 1319 for row in gsm):
            errors.append("GSM8K is not a nonempty incomplete 1,319-sample run")
        if Path(f"{gsm_path.with_suffix('')}.summary.json").exists():
            errors.append("partial GSM8K run unexpectedly has a completed summary")
        payload["gsm8k_partial"] = {
            "rows": len(gsm), "raw_sha256": sha256(gsm_path),
            "correct_count_not_an_accuracy_verdict": sum(row["correct"] is True for row in gsm),
            "completion_tokens": sum(row["usage"]["completion_tokens"] for row in gsm),
        }
        if (quality_root / "no-cache-quality-registry.json").exists() or (quality_root / "quality-context-audit.json").exists():
            errors.append("incomplete quality was incorrectly frozen or classified as paired")
        canary = load_object(root / "canary-gate.json")
        if not (canary.get("passed") is True and canary.get("failures") == []):
            errors.append("real-weight canary gate did not pass")
        iteration = load_object(root / "optimization-iteration.json")
        if not (iteration.get("measured") is True and iteration.get("status") == "rejected"
                and iteration.get("paper_only_gate_unchanged_and_failed") is True):
            errors.append("measured optimization rejection differs from frozen evidence")
        for rel, digest in iteration.get("raw_sha256", {}).items():
            path = (root / rel).resolve()
            if not path.is_relative_to(root) or not path.is_file() or sha256(path) != digest:
                errors.append(f"optimization raw hash differs: {rel}")
        rollback = load_object(root / "rollback-evidence.json")
        if not (rollback.get("disabled_request_passed") is True
                and rollback.get("treatment_marker_absent") is True
                and rollback.get("owned_npus_released") is True
                and rollback.get("port_released") is True):
            errors.append("disabled-control rollback did not pass")
        payload["live_release"] = audit_release(quality_root, contract, errors)
        if datetime.now(timezone.utc) > DEADLINE:
            errors.append("negative closure was not audited before the 24-hour deadline")
    except Exception as exc:
        errors.append(f"independent fail-fast audit could not complete: {type(exc).__name__}: {exc}")
    payload["evidence_integrity_ok"] = not errors
    payload["errors"] = errors
    atomic_json(args.output.resolve(), payload)
    print(json.dumps({"evidence_integrity_ok": not errors, "errors": errors,
                      "gsm8k_partial_rows": payload.get("gsm8k_partial", {}).get("rows")}, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())

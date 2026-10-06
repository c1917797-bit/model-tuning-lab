#!/usr/bin/env python3
"""Freeze the measured one-switch fusion iteration without changing HYPIC-only gates."""

from __future__ import annotations

import hashlib
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

from assess_hypic_e2e_gates import validate_performance_record


ROOT = Path("/cache/cch/hypic-qwen36-e2e-2048-20261006")
CANDIDATE = ROOT / "candidate-matmul-allreduce"
METRICS = {
    "ttft_p95_ms": ("lower", 30.0),
    "tpot_p95_ms": ("lower", 10.0),
    "output_tokens_per_second": ("higher", 20.0),
    "benchmark_duration_s": ("lower", 15.0),
}


def read(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: JSON object required")
    return data


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    baseline_contract = read(ROOT / "baseline-contract.json")
    baseline_hash = baseline_contract["fingerprint_sha256"]
    fingerprint = baseline_contract["fingerprint"]
    if hashlib.sha256(
        json.dumps(fingerprint, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest() != baseline_hash:
        raise RuntimeError("baseline fingerprint integrity failure")
    original_gate = read(ROOT / "performance-gate.json")
    if original_gate.get("passed") is not False:
        raise RuntimeError("original paper-only gate was modified")
    canary = read(CANDIDATE / "canary-gate.json")
    if canary.get("passed") is not True or canary.get("failures") != []:
        raise RuntimeError("candidate real-weight canary did not pass")
    responses = canary.get("response_sha256", {})
    if len(set(responses.values())) != 1 or len(responses) != 3:
        raise RuntimeError("candidate canary differs from original arms")
    start = read(CANDIDATE / "service-start.json")
    stop = read(CANDIDATE / "service-stop.json")
    if not (
        start.get("schema") == "hypic-matmul-allreduce-service-start/v1"
        and start.get("health_passed") is True
        and start.get("single_behavior_change") == "VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE=1"
        and start.get("physical_npus") == [0, 1, 2, 3]
        and start.get("container_id") == stop.get("container_id")
        and stop.get("owned_npus_released") is True
        and stop.get("port_released") is True
        and stop.get("container_removed") is True
    ):
        raise RuntimeError("candidate identity or rollback receipt mismatch")
    summary_by_arm: dict[str, list[dict]] = {}
    for arm in ("no-cache", "hypic-only"):
        summary_by_arm[arm] = []
        for index in (1, 2, 3):
            path = ROOT / arm / f"performance.run{index}.json"
            summary_by_arm[arm].append(
                validate_performance_record(read(path), arm, index)
            )
            if original_gate["run_sha256"][arm][index - 1] != sha256(path):
                raise RuntimeError(f"{arm} original raw hash drift")
    summary_by_arm["candidate-matmul-allreduce"] = []
    for index in (1, 2, 3):
        path = CANDIDATE / f"performance.run{index}.json"
        summary_by_arm["candidate-matmul-allreduce"].append(
            validate_performance_record(read(path), "hypic-only", index)
        )
    comparison = read(CANDIDATE / "performance-comparison.json")
    if (
        comparison.get("schema") != "hypic-matmul-allreduce-performance-comparison/v1"
        or comparison.get("original_paper_only_gate_remains_unchanged") is not True
    ):
        raise RuntimeError("candidate comparison boundary mismatch")
    recomputed = {}
    for reference_arm in ("no-cache", "hypic-only"):
        recomputed[reference_arm] = {}
        for metric, (direction, threshold) in METRICS.items():
            reference = statistics.median(
                float(row[metric]) for row in summary_by_arm[reference_arm]
            )
            candidate = statistics.median(
                float(row[metric])
                for row in summary_by_arm["candidate-matmul-allreduce"]
            )
            improvement = (
                (reference - candidate) / reference if direction == "lower"
                else (candidate - reference) / reference
            ) * 100
            observed = comparison["comparisons"][reference_arm][metric]
            if not (
                abs(observed["reference_median"] - reference) < 1e-6
                and abs(observed["candidate_median"] - candidate) < 1e-6
                and abs(observed["improvement_percent"] - improvement) < 1e-6
                and observed["threshold_percent"] == threshold
                and observed["passed"] is (improvement >= threshold)
            ):
                raise RuntimeError(f"candidate comparison arithmetic drift: {reference_arm}/{metric}")
            recomputed[reference_arm][metric] = observed
    passed = all(value["passed"] for value in recomputed["no-cache"].values())
    raw_paths = [
        "performance-gate.json", "profiles/profile-diagnostic.json",
        "candidate-matmul-allreduce/semantic-canary.json",
        "candidate-matmul-allreduce/canary-gate.json",
        "candidate-matmul-allreduce/performance-comparison.json",
        "candidate-matmul-allreduce/service-start.json",
        "candidate-matmul-allreduce/service-stop.json",
        *(f"candidate-matmul-allreduce/performance.run{index}.json" for index in (1, 2, 3)),
    ]
    result = {
        "schema": "hypic-e2e-optimization-iteration/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "baseline_fingerprint_sha256": baseline_hash,
        "candidate_id": "hypic-v085-plus-matmul-allreduce-qwen36-tp4-npu03",
        "one_switch": "VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE=1",
        "paper_only_gate_unchanged_and_failed": True,
        "measured": True,
        "status": "accepted" if passed else "rejected",
        "candidate_canary_passed": True,
        "candidate_context": 40960,
        "candidate_performance_protocol": {
            "input_tokens": 32768, "prefix_tokens": 16384,
            "output_tokens": 1024, "requests": 40,
            "concurrency": 16, "repetitions": 3,
        },
        "comparison": recomputed,
        "raw_sha256": {rel: sha256(ROOT / rel) for rel in raw_paths},
        "physical_npus_released": True,
        "candidate_container_removed": True,
    }
    target = ROOT / "optimization-iteration.json"
    if target.exists():
        existing = read(target)
        if existing.get("raw_sha256") != result["raw_sha256"] or existing.get("status") != result["status"]:
            raise RuntimeError("existing frozen optimization iteration differs")
        print(json.dumps({"status": existing["status"], "sha256": sha256(target), "reused": True}))
        return 0
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "sha256": sha256(target), "reused": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

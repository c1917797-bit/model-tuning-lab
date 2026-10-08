#!/usr/bin/env python3
"""Replay the bounded CPU-binding-off inference-tuning case from raw files."""

from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

import yaml


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
EXPERIMENT = REPO / ".agents/experiments/exp-20261007-hypic-npu03-cpu-binding-fix.yaml"
PHASES = (
    ("screen_20261007", "screen"),
    ("repeat2_20261007", "repeat2"),
    ("repeat3_20261007", "repeat3"),
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def verify_hash(path: Path, expected: str) -> None:
    require(path.is_file(), f"raw artifact absent: {path}")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    require(actual == expected, f"raw artifact SHA256 drift: {path}")


def verify() -> dict:
    record = yaml.safe_load(EXPERIMENT.read_text(encoding="utf-8"))
    require(record["id"] == "exp-20261007-hypic-npu03-cpu-binding-fix"
            and record["status"] == "partial_component",
            "experiment identity or decision drift")
    require(record["candidate"]["primary_variable"]
            == "Add only --additional-config '{\"enable_cpu_binding\":false}' to the frozen serving command.",
            "declared treatment drift")
    baseline_root = Path(record["baseline_reuse"]["root"])
    candidate_root = Path(record["scope"]["artifact_root"]) / "no-cache"
    expected_config = None
    baseline_tpot: list[float] = []
    candidate_tpot: list[float] = []
    for index in (1, 2, 3):
        path = baseline_root / f"performance.run{index}.json"
        verify_hash(path, record["baseline_reuse"][f"run{index}_sha256"])
        raw = json.loads(path.read_text(encoding="utf-8"))
        summary = raw["summary"]
        require(summary["fixed_output_verified"] is True
                and summary["fixed_output_requests"] == 40
                and summary["failed"] == 0,
                f"baseline run{index} invalid")
        if expected_config is None:
            expected_config = raw["config"]
        require(raw["config"] == expected_config,
                "baseline workload configuration drift")
        baseline_tpot.append(float(summary["tpot_weighted_ms"]))
    for phase, directory in PHASES:
        base = candidate_root / directory
        artifacts = record[phase]["artifacts"]
        for filename, key in (
            ("performance.json", "performance_sha256"),
            ("contract.json", "contract_sha256"),
            ("cleanup.json", "cleanup_sha256"),
        ):
            verify_hash(base / filename, artifacts[key])
        performance = json.loads((base / "performance.json").read_text())
        contract = json.loads((base / "contract.json").read_text())
        cleanup = json.loads((base / "cleanup.json").read_text())
        summary = performance["summary"]
        require(performance["config"] == expected_config,
                f"{phase}: candidate workload differs from baseline")
        require(summary["fixed_output_verified"] is True
                and summary["fixed_output_requests"] == 40
                and summary["failed"] == 0,
                f"{phase}: incomplete fixed-output run")
        require(contract["physical_npus"] == [0, 1, 2, 3]
                and contract["phase"] == directory
                and contract["source_commit"] == record["scope"]["source_commit"]
                and contract["image"] == record["scope"]["image_digest"]
                and contract["benchmark_sha256"] == record["scope"]["benchmark_sha256"]
                and contract["cpuset"] == record["scope"]["cpuset"]
                and contract["only_serving_change"]
                == "--additional-config '{\"enable_cpu_binding\":false}'",
                f"{phase}: source, lane, or treatment drift")
        require(cleanup["container_id"] == contract["container_id"]
                and cleanup["container_removed"] is True
                and cleanup["owned_npus_released"] is True
                and cleanup["port_released"] is True,
                f"{phase}: owned-resource release unproven")
        candidate_tpot.append(float(summary["tpot_weighted_ms"]))
    baseline_median = statistics.median(baseline_tpot)
    candidate_median = statistics.median(candidate_tpot)
    improvement = 100 * (baseline_median - candidate_median) / baseline_median
    require(improvement >= 20, "predeclared TPOT fail-fast gate not met")
    return {
        "schema": "ascend-inference-tuning-loop-bounded-replay/v1",
        "baseline_weighted_tpot_ms": baseline_tpot,
        "candidate_weighted_tpot_ms": candidate_tpot,
        "baseline_median_ms": baseline_median,
        "candidate_median_ms": candidate_median,
        "median_tpot_reduction_percent": improvement,
        "raw_runs_verified": 6,
        "candidate_exact_output_and_cleanup_verified": 3,
        "case_scope": "CPU-binding-off no-cache performance only",
        "full_2048_quality_verified": False,
        "hypic_paper_effect_verified": False,
    }


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))

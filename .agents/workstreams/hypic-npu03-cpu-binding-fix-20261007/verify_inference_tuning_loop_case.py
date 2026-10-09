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
RETRY14_ROOT = Path(
    "/cache/cch/hypic-npu03-cpu-binding-fix-20261007/"
    "performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry14"
)
RETRY14_REPORT = (
    REPO / ".agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/"
    "HOTPATH_CACHE10PERF_RETRY14_TERMINAL_AUDIT.md"
)
RETRY14_RECEIPTS = {
    "contract.json": "b260e81ab4f766ee1b5ee3c485d5d3f993dfdbb4ba8733dff339700616dd2c2a",
    "arm-result.json": "8438fbd58b4be0c06412667c57442e7340e5dc08d1d7889a059f736113eaae0a",
    "hypic-only/hypic-evidence.jsonl": "fb3f7f0f342b3738e637ecb517d90dc5b2f603ddc3ce0978dbb6a8cc6c9389be",
    "hypic-only/lane-guard.json": "71f8ece8c31869544653661b26c9f520ed6a7a8210b93c2c4b79dfa8ad89b0ed",
    "hypic-only/pre-health-release.json": "7afb397349d54ce1c19725bcd5e22523d84ac3e9d3d44cb8ed8222439e7ffc09",
}
RETRY14_REPORT_SHA256 = "362a8c5708584bd726003aa0825190b4b9c69eb2879d9673baf90f176e3394af"


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
    for relative, expected in RETRY14_RECEIPTS.items():
        verify_hash(RETRY14_ROOT / relative, expected)
    verify_hash(RETRY14_REPORT, RETRY14_REPORT_SHA256)
    retry14_contract = json.loads((RETRY14_ROOT / "contract.json").read_text())
    retry14_arm = json.loads((RETRY14_ROOT / "arm-result.json").read_text())
    retry14_guard = json.loads(
        (RETRY14_ROOT / "hypic-only/lane-guard.json").read_text()
    )
    retry14_release = json.loads(
        (RETRY14_ROOT / "hypic-only/pre-health-release.json").read_text()
    )
    foreign_seen = any(
        process.get("pid") == 242978
        and process.get("physical_npu") == 1
        and process.get("container_id")
        == "efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6"
        for sample in retry14_guard["foreign"]
        for process in sample["processes"]
    )
    require(retry14_contract["phase"] == "repeat3"
            and retry14_contract["arm"] == "hypic-only"
            and retry14_contract["fingerprint"]["physical_npus"] == [0, 1, 2, 3],
            "retry14 frozen phase or physical lane drift")
    require(retry14_arm["contract_sha256"] == RETRY14_RECEIPTS["contract.json"]
            and retry14_arm["valid"] is False
            and retry14_arm["metrics"] is None
            and retry14_arm["performance_sha256"] is None
            and "lane guard" in retry14_arm["error"],
            "retry14 must remain an environmental zero-metric outcome")
    require(retry14_guard["samples"] == 18
            and retry14_guard["probe_errors"] == []
            and foreign_seen,
            "retry14 foreign physical process evidence drift")
    require(retry14_release["container_id"] == retry14_arm["container_id"]
            and retry14_release["container_removed"] is True,
            "retry14 exact owned-service cleanup is not proven")
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
        "retry14_classification": "environmental-pre-health-isolation-failure",
        "retry14_scored_requests": 0,
        "retry14_performance_metrics_valid": False,
        "retry14_foreign_process": "PID 242978 on physical NPU1",
        "retry14_owned_service_removed": True,
    }


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))

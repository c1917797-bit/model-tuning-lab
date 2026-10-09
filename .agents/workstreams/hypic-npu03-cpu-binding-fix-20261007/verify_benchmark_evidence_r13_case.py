#!/usr/bin/env python3
"""Read-only benchmark-evidence replay; a speed win cannot override quality."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RAW = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007")
QUALITY_SHA = "f66b9760bfb4f9391863cd386658211c58ab07d0dfc2de58ea2091ed4d2c9b7b"
PERFORMANCE_SHA = "d8f710f6ccd79ad79a31a36926963eac650761c921924d08b4fb0d2a1a206062"


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_summary(summary: dict, case: dict) -> None:
    observed = case["observed"]
    require(summary["r13_quality_pair_complete"] is True
            and summary["r13_correct"] == [230, 219]
            and summary["r13_deployment_quality"] == "REJECT_OR_QUALIFY"
            and summary["r13_strict_hot"] == [368, 381]
            and summary["r13_strict_hot_decision"] == "NOT_ACCEPTED_HOT_COVERAGE",
            "r13 quality or mechanism evidence changed")
    require(summary["r13_performance_all_six_phases_valid"] is True
            and summary["r13_performance_strict_hot"] == [120, 120]
            and math.isclose(summary["r13_performance_weighted_tpot_saved_pct"],
                             21.524278158508903, abs_tol=1e-9)
            and math.isclose(summary["r13_performance_ttft_p95_saved_s"],
                             40.86937530996511, abs_tol=1e-9),
            "r13 matched performance evidence changed")
    require(observed["r13_single_dataset_quality_pair_complete"] is True
            and observed["r13_fixed_output_six_phase_performance_complete"] is True
            and observed["r13_quality_correct_baseline_candidate"] == [230, 219]
            and observed["r13_quality_decision"] == "REJECT_OR_QUALIFY"
            and observed["r13_quality_strict_hot"] == [368, 381]
            and observed["r13_performance_strict_hot"] == [120, 120]
            and observed["r13_performance_screen_decision"] == "EFFECT_SCREEN_PASS"
            and observed["full_default_skill_ruler_complete"] is False
            and case["long_term_acceptance"] == "partial-evidence",
            "benchmark case conflates bounded measurements with full acceptance")
    require(case["external_raw_receipts"]["r13_quality_audit_sha256"] == QUALITY_SHA
            and case["external_raw_receipts"]["r13_performance_audit_sha256"] == PERFORMANCE_SHA,
            "benchmark case raw audit identity drift")


def main() -> int:
    for name, expected in (("hotpath-quality-cache10r13-dual-audit.json", QUALITY_SHA),
                           ("hotpath-cache10r13-matched-performance-audit.json", PERFORMANCE_SHA)):
        require(sha256(RAW / name) == expected, f"raw audit hash drift: {name}")
    run = subprocess.run(
        (sys.executable, "-B", str(HERE / "verify_paper_to_ascend_reproduction_case.py")),
        cwd=REPO, text=True, capture_output=True, check=True,
    )
    summary = json.loads(run.stdout.strip().splitlines()[-1])
    performance = subprocess.run(
        (sys.executable, "-B", str(HERE / "verify_hotpath_cache10_matched_performance.py")),
        cwd=REPO, text=True, capture_output=True, check=True,
    )
    require("6/6 phases, 120/120 strict hot requests, quality remains qualified"
            in performance.stdout, "independent six-phase replay did not pass")
    case = json.loads((HERE / "skill-cases/ascend-benchmark-evidence.json").read_text())
    validate_summary(summary, case)
    print(json.dumps({"schema": "ascend-benchmark-r13-bounded-case/v1",
                      "quality_pair": "127x3 each arm, REJECT_OR_QUALIFY",
                      "performance": "6/6 phases, EFFECT_SCREEN_PASS",
                      "strict_quality_hot": "368/381 FAIL",
                      "strict_performance_hot": "120/120 PASS",
                      "full_skill_acceptance": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Independent r17 cap-1024 quality audit; diagnostic, never an adoption verdict."""

from __future__ import annotations

import argparse
import json

from r17_cap1024_offline_adapter import SOURCE_COMMIT, configure


controller = configure("no-cache")
quality = controller.quality
from hotpath_quality_audit import (  # noqa: E402
    audit_arm, decide, frozen_cases, frozen_pair_seam, require,
)


BASE = quality.ROOT / "quality-context-41984-hotpath-cache10r17-cap1024-full-baseline"
CAND = quality.ROOT / "quality-context-41984-hotpath-cache10r17-cap1024-full-hypic"
OUT = quality.ROOT / "hypic-r17-cap1024-full-quality-audit.json"


def audit_one(root, arm, cases, evaluator):
    return audit_arm(root, arm, cases, evaluator, scored_cap=1024,
                     allow_hot_shortfall=(arm == "hypic-only"),
                     require_source_attestation=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--baseline-only", action="store_true")
    args = parser.parse_args()
    require(not (args.check and args.baseline_only), "choose one audit mode")
    cases, evaluator = frozen_cases()
    seam = frozen_pair_seam()
    require(len(cases) == 127 and controller.CONCURRENCY == 8
            and controller.REPETITIONS == 3 and controller.MAX_OUTPUT == 1024,
            "r17 auditor case/controller drift")
    if args.check:
        require(not BASE.exists() and not CAND.exists() and not OUT.exists(),
                "r17 root already exists; offline check is no longer prospective")
        print(json.dumps({"audit_ready": True, "device_run_admitted": False,
                          "sample_count": len(cases), "max_output_tokens": 1024,
                          "pair_seam": seam}, sort_keys=True))
        return 0
    baseline = audit_one(BASE, "no-cache", cases, evaluator)
    if args.baseline_only:
        print(json.dumps({"valid": True, "scope": "baseline-only; no quality conclusion",
                          "correct": baseline["correct"],
                          "scored_rows": baseline["scored_rows"],
                          "guard_samples": baseline["guard_samples"],
                          "contract_sha256": baseline["contract_sha256"],
                          "arm_result_sha256": baseline["arm_result_sha256"]},
                         sort_keys=True))
        return 0
    require(not OUT.exists(), "r17 paired audit exists; never overwrite")
    candidate = audit_one(CAND, "hypic-only", cases, evaluator)
    require(baseline["fingerprint"] == candidate["fingerprint"],
            "r17 arms differ beyond HYPIC enablement")
    fp = baseline["fingerprint"]
    require(fp["source_commit"] == SOURCE_COMMIT
            and fp["physical_npus"] == [0, 1, 2, 3]
            and fp["max_output_tokens"] == 1024
            and fp["gpu_memory_utilization"] == 0.85
            and fp["material_cache_max_mb"] == 3584
            and fp["max_materialized_segments"] == 10,
            "r17 frozen source/service identity drift")
    paired = decide(baseline, candidate)
    base_run_correct = paired["baseline_run_correct"]
    base_length_by_run = [
        sum(row["finish_reason"] == "length" for row in baseline["rows"]
            if row["repetition"] == repeat)
        for repeat in (1, 2, 3)
    ]
    candidate_mean_correct = candidate["correct"] / 3
    candidate_mean_length = candidate["length_limit"] / 3
    gate_pass = (candidate_mean_correct >= min(base_run_correct)
                 and not paired["category_cliffs"]
                 and candidate_mean_length <= max(base_length_by_run))
    report = {
        "schema": "hypic-r17-cap1024-diagnostic-audit/v1",
        "evidence_valid": True,
        "scope": "diagnostic full LongBench-v2 127x3 per arm, c8, natural-EOS max1024, physical NPU0-3",
        "source_commit": SOURCE_COMMIT,
        "r16_decision_unchanged": "REJECT_OR_QUALIFY",
        "pair_seam": seam,
        "all_request_quality": paired,
        "r16_style_variability_gate": {
            "baseline_run_correct": base_run_correct,
            "candidate_mean_correct": candidate_mean_correct,
            "candidate_meets_baseline_run_floor":
                candidate_mean_correct >= min(base_run_correct),
            "category_cliffs": paired["category_cliffs"],
            "baseline_length_by_run": base_length_by_run,
            "candidate_mean_length": candidate_mean_length,
            "candidate_meets_length_ceiling":
                candidate_mean_length <= max(base_length_by_run),
        },
        "descriptive_baseline_range": {
            "baseline_run_accuracy_range_pp":
                100 * (max(base_run_correct) - min(base_run_correct)) / len(cases),
            "candidate_delta_within_baseline_range":
                abs(paired["delta_pp"]) <=
                100 * (max(base_run_correct) - min(base_run_correct)) / len(cases),
            "is_acceptance_gate": False,
        },
        "diagnostic_quality_decision": (
            "NO_MATERIAL_REGRESSION_OBSERVED" if gate_pass else "REJECT_OR_QUALIFY"),
        "historical_1024_c32_reproduction": False,
        "current_2048_skill_acceptance": False,
        "activation_boundary": (
            "historical source has aggregate worker-hot evidence and a serialized "
            "four-worker sentinel; per-request four-worker telemetry is unavailable"),
        "performance_decision": "not-measured-under-this-identity",
        "paper_c3_decision": "not-implemented",
        "baseline": {key: value for key, value in baseline.items() if key != "rows"},
        "candidate": {key: value for key, value in candidate.items() if key != "rows"},
    }
    quality.write_json(OUT, report)
    print(json.dumps({"audit": str(OUT),
                      "diagnostic_quality_decision": report["diagnostic_quality_decision"],
                      "baseline_correct": baseline["correct"],
                      "candidate_correct": candidate["correct"],
                      "delta_pp": paired["delta_pp"],
                      "aggregate_verified_hot_requests": candidate["verified_hot_requests"]},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

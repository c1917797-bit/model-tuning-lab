#!/usr/bin/env python3
"""Independent full r16 paired quality audit; r13 remains immutable."""

from __future__ import annotations

import argparse
import json

from r16_original_source_full_adapter import SOURCE_COMMIT, configure


controller = configure("no-cache")
quality = controller.quality
from hotpath_quality_audit import (  # noqa: E402
    audit_arm, decide, frozen_cases, frozen_pair_seam, require,
)


BASE = quality.ROOT / "quality-context-41984-hotpath-cache10r16-full-baseline"
CAND = quality.ROOT / "quality-context-41984-hotpath-cache10r16-full-hypic"
OUT = quality.ROOT / "hypic-r16-original-source-full-quality-audit.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-only", action="store_true")
    args = parser.parse_args()
    cases, evaluator = frozen_cases()
    seam = frozen_pair_seam()
    baseline = audit_arm(BASE, "no-cache", cases, evaluator,
                         require_source_attestation=True)
    if args.baseline_only:
        print(json.dumps({
            "valid": True, "scope": "baseline-only; no quality conclusion",
            "correct": baseline["correct"], "scored_rows": baseline["scored_rows"],
            "guard_samples": baseline["guard_samples"],
            "contract_sha256": baseline["contract_sha256"],
            "arm_result_sha256": baseline["arm_result_sha256"],
        }, sort_keys=True))
        return 0
    require(not OUT.exists(), "r16 paired audit exists; never overwrite")
    candidate = audit_arm(CAND, "hypic-only", cases, evaluator,
                          allow_hot_shortfall=True,
                          require_source_attestation=True)
    require(baseline["fingerprint"] == candidate["fingerprint"],
            "r16 arms differ beyond HYPIC enablement")
    fp = baseline["fingerprint"]
    require(fp["source_commit"] == SOURCE_COMMIT
            and fp["physical_npus"] == [0, 1, 2, 3]
            and fp["max_output_tokens"] == 2048
            and fp["gpu_memory_utilization"] == 0.85
            and fp["material_cache_max_mb"] == 3584
            and fp["max_materialized_segments"] == 10,
            "r16 frozen source/service identity drift")
    paired = decide(baseline, candidate)
    base_run_correct = paired["baseline_run_correct"]
    candidate_mean_correct = candidate["correct"] / 3
    base_length_by_run = [
        sum(row["finish_reason"] == "length" for row in baseline["rows"]
            if row["repetition"] == repeat)
        for repeat in (1, 2, 3)
    ]
    candidate_mean_length = candidate["length_limit"] / 3
    quality_pass = (
        candidate_mean_correct >= min(base_run_correct)
        and not paired["category_cliffs"]
        and candidate_mean_length <= max(base_length_by_run)
    )
    report = {
        "schema": "hypic-r16-original-source-quality-audit/v1",
        "evidence_valid": True,
        "scope": "full LongBench-v2 127x3 per arm, c8, natural-EOS max2048, physical NPU0-3",
        "source_commit": SOURCE_COMMIT,
        "r13_decision_unchanged": "REJECT_OR_QUALIFY",
        "pair_seam": seam,
        "all_request_quality": paired,
        "predeclared_variability_gate": {
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
        "quality_decision": (
            "NO_MATERIAL_REGRESSION_OBSERVED"
            if quality_pass else "REJECT_OR_QUALIFY"),
        "activation_boundary": (
            "historical source has aggregate worker-hot evidence and a serialized "
            "four-worker sentinel; per-request four-worker telemetry is unavailable"),
        "performance_decision": "not-measured-under-this-identity",
        "paper_c3_decision": "not-implemented",
        "baseline": {key: value for key, value in baseline.items() if key != "rows"},
        "candidate": {key: value for key, value in candidate.items() if key != "rows"},
    }
    quality.write_json(OUT, report)
    print(json.dumps({
        "audit": str(OUT), "quality_decision": report["quality_decision"],
        "baseline_correct": baseline["correct"],
        "candidate_correct": candidate["correct"],
        "delta_pp": paired["delta_pp"],
        "aggregate_verified_hot_requests": candidate["verified_hot_requests"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

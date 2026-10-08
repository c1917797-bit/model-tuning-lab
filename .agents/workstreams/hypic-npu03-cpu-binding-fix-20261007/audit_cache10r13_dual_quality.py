#!/usr/bin/env python3
"""Independent terminal r13 pair audit: deployed all-request versus strict hot."""

from __future__ import annotations

import json
import os
from pathlib import Path

os.environ["HYPIC_HOTPATH_AUDIT_CAMPAIGN"] = "cache10r13"
os.environ["HYPIC_QUALITY_PLUGIN_REPO"] = (
    "/cache/cch/hypic_vllm_ascend-fallback-telemetry-20261008"
)
os.environ["HYPIC_QUALITY_PLUGIN_COMMIT"] = (
    "c12060cd47e7575ead059983d7a8bb4704165c98"
)

from diagnose_partial_hotpath_coverage import diagnose
from r13_quality_cohorts import cohort_summary
from hotpath_quality_audit import (
    BASE, CAND, audit_arm, decide, frozen_cases, frozen_pair_seam, quality, require,
)
from verify_hotpath_request_coverage import audit_coverage, load_worker_namespace_pids


OUT = quality.ROOT / "hotpath-quality-cache10r13-dual-audit.json"
SOURCE = "c12060cd47e7575ead059983d7a8bb4704165c98"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    require(not OUT.exists(), "r13 dual audit output exists; do not overwrite")
    cases, evaluator = frozen_cases()
    seam = frozen_pair_seam()
    baseline = audit_arm(BASE, "no-cache", cases, evaluator,
                         require_source_attestation=True)
    candidate = audit_arm(CAND, "hypic-only", cases, evaluator,
                          allow_hot_shortfall=True,
                          require_source_attestation=True)
    require(baseline["fingerprint"] == candidate["fingerprint"],
            "r13 arms differ beyond HYPIC switch")
    fp = baseline["fingerprint"]
    require(fp.get("source_commit") == SOURCE
            and fp.get("physical_npus") == [0, 1, 2, 3]
            and fp.get("gpu_memory_utilization") == 0.85
            and fp.get("material_cache_max_mb") == 3584
            and fp.get("max_materialized_segments") == 10
            and fp.get("max_output_tokens") == 2048,
            "r13 source/device/quality fingerprint drift")
    result = decide(baseline, candidate)
    raw_rows = [read_json(path) for path in sorted((CAND / "samples").glob("*.json"))]
    start = read_json(CAND / "hypic-only/service-start.json")
    workers = load_worker_namespace_pids(CAND, start)
    evidence = CAND / "hypic-only/hypic-evidence.jsonl"
    events = [json.loads(line) for line in evidence.read_text(encoding="utf-8").splitlines()
              if line.strip()]
    diagnostic = diagnose(raw_rows, events, workers)
    require(diagnostic["scored_requests"] == 381
            and diagnostic["completed_samples"] == 127,
            "r13 request-level diagnostic is not full")
    cold_keys = {(item["index"], item["repetition"]) for item in diagnostic["issues"]}
    require(len(cold_keys) == diagnostic["issue_count"],
            "r13 cold request key duplication")
    cohorts = cohort_summary(baseline["rows"], candidate["rows"], cold_keys)
    strict_hot = diagnostic["issue_count"] == 0
    if strict_hot:
        scored_ids = [score["request_id"] for row in raw_rows for score in row["scores"]]
        coverage = audit_coverage(scored_ids, events, workers)
        require(coverage["four_worker_post_repair_verified_requests"] == 381,
                "r13 strict coverage count drift")
        require(candidate["controller_error"] is None,
                "r13 controller failed despite full strict proof")
    else:
        require(candidate["controller_error"] ==
                "RuntimeError: candidate scored boundary/hot coverage incomplete",
                "r13 cold requests lack exact controller failure classification")
    report = {
        "schema": "hypic-cache10r13-dual-quality-audit/v1",
        "evidence_valid": True,
        "scope": "LongBench-v2 127x3 explicit-boundary natural-EOS max2048 c8 TP4 physical NPU0-3",
        "source_commit": SOURCE,
        "pair_seam": seam,
        "all_request_quality": result,
        "deployed_quality_decision": result["decision"],
        "strict_c1_c2_hot_coverage": {
            "decision": "PASS" if strict_hot else "FAIL",
            "four_worker_verified_scored_requests": diagnostic["four_worker_verified_requests"],
            "expected_scored_requests": 381,
            "controller_error": candidate["controller_error"],
            "cold_issues": diagnostic["issues"],
        },
        "strict_quality_decision": (
            result["decision"] if strict_hot else "NOT_ACCEPTED_HOT_COVERAGE"
        ),
        "hot_cold_descriptive_quality": cohorts,
        "performance_decision": "not-measured",
        "paper_c3_decision": "not-implemented",
        "baseline": {key: value for key, value in baseline.items() if key != "rows"},
        "candidate": {key: value for key, value in candidate.items() if key != "rows"},
    }
    quality.write_json(OUT, report)
    print(json.dumps({"audit": str(OUT), "deployed_quality_decision":
                      report["deployed_quality_decision"],
                      "strict_hot_decision":
                      report["strict_c1_c2_hot_coverage"]["decision"],
                      "hot_requests": diagnostic["four_worker_verified_requests"],
                      "cold_requests": diagnostic["issue_count"],
                      "delta_pp": result["delta_pp"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Read-only raw-audited statistics for the frozen current-source campaign."""
import json
import math
import statistics
from pathlib import Path

ORDER = (("no-cache", "screen"), ("hypic-only", "screen"),
         ("hypic-only", "repeat2"), ("no-cache", "repeat2"),
         ("no-cache", "repeat3"), ("hypic-only", "repeat3"))
METRICS = ("tpot_weighted_ms", "ttft_p95_ms", "output_tokens_per_second",
           "benchmark_duration_s", "tpot_p95_ms")

def summarize(phases):
    if [(p["arm"], p["phase"]) for p in phases] != list(ORDER):
        raise ValueError("six phases/order required")
    rows = {arm: [p["metrics"] for p in phases if p["arm"] == arm]
            for arm in ("no-cache", "hypic-only")}
    if any(not isinstance(r[k], (int, float)) or isinstance(r[k], bool)
           or not math.isfinite(r[k]) or r[k] <= 0
           for arm in rows.values() for r in arm for k in METRICS):
        raise ValueError("positive finite metrics required")
    stats = {arm: {k: {"values": [r[k] for r in values],
                       "mean": statistics.mean(r[k] for r in values),
                       "sample_sd": statistics.stdev(r[k] for r in values),
                       "median": statistics.median(r[k] for r in values),
                       "min": min(r[k] for r in values),
                       "max": max(r[k] for r in values)}
                   for k in METRICS} for arm, values in rows.items()}
    changes = [{k: 100 * (c[k] / b[k] - 1) for k in METRICS}
               for b, c in zip(rows["no-cache"], rows["hypic-only"])]
    return {"statistics": stats, "paired_relative_change_pct": changes,
            "median_relative_change_pct": {
                k: 100 * (stats["hypic-only"][k]["median"] /
                          stats["no-cache"][k]["median"] - 1) for k in METRICS},
            "sign_convention": "candidate/baseline-1; negative latency is improvement",
            "dispersion_unit": "same as metric; sample SD across three run summaries",
            "p95_aggregation": "per-run nearest-rank P95; no pooled-request percentile"}

def main():
    import current_source_performance_20261013 as c
    phases = [c.audit_one(*pair) for pair in ORDER]
    aggregate = c.ROOT / (c.CAMPAIGN + "-audit.json")
    if not aggregate.is_file():
        raise RuntimeError("aggregate absent: do not fabricate final report")
    frozen = json.loads(aggregate.read_text())
    actual = [{k:v for k,v in p.items() if k != "normalized_spec"} for p in phases]
    if frozen["phases"] != actual or frozen["source_commit"] != c.COMMIT:
        raise RuntimeError("aggregate versus raw audit drift")
    if frozen["quality_decision"] != "REJECT_OR_QUALIFY" or frozen["deployment_allowed"] is not False:
        raise RuntimeError("quality/deployment boundary drift")
    if not all(p["normalized_spec"] == phases[0]["normalized_spec"] for p in phases):
        raise RuntimeError("one-switch configuration drift")
    result = summarize(phases)
    for arm in result["statistics"]:
        for metric in METRICS:
            if result["statistics"][arm][metric]["median"] != frozen["medians"][arm][metric]:
                raise RuntimeError("median drift")
    if not math.isclose(-result["median_relative_change_pct"]["tpot_weighted_ms"],
                        frozen["effect"]["weighted_tpot_saved_pct"], abs_tol=1e-9):
        raise RuntimeError("effect drift")
    result.update({"aggregate_path": str(aggregate), "aggregate_sha256": c.sha(aggregate),
                   "source_commit": c.COMMIT, "strict_hot_coverage": frozen["strict_hot_coverage"],
                   "quality_decision": frozen["quality_decision"], "deployment_allowed": False,
                   "no_device_execution": True, "no_raw_writes": True})
    print(json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()

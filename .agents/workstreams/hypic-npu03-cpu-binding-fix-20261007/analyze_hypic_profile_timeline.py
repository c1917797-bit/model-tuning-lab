#!/usr/bin/env python3
"""Post-hoc CSV timeline analysis of immutable HYPIC profiles; no device calls."""
import argparse
import collections
import csv
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path

BASE = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007")
ROOTS = {
    "prefill": BASE / "profiler-offline-parse-20261009-r2-prefill",
    "decode": BASE / "profiler-offline-parse-20261009-r6-decode-manager",
}
COMPUTE = {"AI_CORE", "AI_VECTOR_CORE", "MIX_AIC", "MIX_AIV"}


def ns(value):
    number = Decimal(str(value).strip())
    if not number.is_finite() or number < 0:
        raise ValueError("invalid nonnegative profiler timestamp/duration")
    return int(number * 1000)


def merge(intervals):
    result = []
    for start, end in sorted(intervals):
        if end < start:
            raise ValueError("reversed interval")
        if end == start:
            continue
        if result and start <= result[-1][1]:
            result[-1] = (result[-1][0], max(end, result[-1][1]))
        else:
            result.append((start, end))
    return result


def length(intervals):
    return sum(end - start for start, end in merge(intervals))


def intersection(left, right):
    left, right = merge(left), merge(right)
    i = j = total = 0
    while i < len(left) and j < len(right):
        a, b = left[i], right[j]
        total += max(0, min(a[1], b[1]) - max(a[0], b[0]))
        if a[1] <= b[1]:
            i += 1
        else:
            j += 1
    return total


def csv_rows(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def analyze_rank(directory, rank):
    output = directory / "ASCEND_PROFILER_OUTPUT"
    names = ["kernel_details.csv", "op_statistic.csv", "api_statistic.csv",
             "step_trace_time.csv"]
    identity = {}
    for name in names:
        path = output / name
        identity[name] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                          "bytes": path.stat().st_size}
    info_path = directory / ("profiler_info_%d.json" % rank)
    info = json.loads(info_path.read_text())
    assert info["rank_id"] == rank
    assert info["cann_version"] == "9.1.0" and info["torch_npu_version"] == "2.10.0.post4"
    identity[info_path.name] = {"sha256": hashlib.sha256(info_path.read_bytes()).hexdigest()}
    rows = csv_rows(output / "kernel_details.csv")
    assert rows
    groups = collections.defaultdict(list)
    operators = collections.defaultdict(lambda: {"calls": 0, "sum_duration_us": 0.0, "shapes": set()})
    metrics = {k: [0.0, 0.0, 0] for k in ("aic_mac_ratio", "aic_mte2_ratio", "aiv_vec_ratio")}
    for row in rows:
        start, duration = ns(row["Start Time(us)"]), ns(row["Duration(us)"])
        groups[row["Accelerator Core"]].append((start, start + duration))
        op = operators[row["Type"]]
        op["calls"] += 1
        op["sum_duration_us"] += duration / 1000
        if len(op["shapes"]) < 3:
            op["shapes"].add(row["Input Shapes"])
        for key, values in metrics.items():
            weight_key = "aiv_time(us)" if key.startswith("aiv_") else "aicore_time(us)"
            try:
                weight, ratio = float(row[weight_key]), float(row[key])
            except (ValueError, TypeError):
                continue
            if weight > 0 and math.isfinite(weight) and math.isfinite(ratio):
                values[0] += weight * ratio
                values[1] += weight
                values[2] += 1
    all_intervals = merge([pair for pairs in groups.values() for pair in pairs])
    compute = [pair for key in COMPUTE for pair in groups.get(key, [])]
    communication = groups.get("COMMUNICATION", [])
    first, last = all_intervals[0][0], all_intervals[-1][1]
    span, active = last - first, length(all_intervals)
    comp, comm = length(compute), length(communication)
    overlap = intersection(compute, communication)
    assert 0 <= overlap <= min(comp, comm) and active <= span
    top = sorted(operators.items(), key=lambda item: item[1]["sum_duration_us"], reverse=True)[:6]
    for _, values in top:
        values["shapes"] = sorted(values["shapes"])
    steps = csv_rows(output / "step_trace_time.csv")
    apis = sorted(csv_rows(output / "api_statistic.csv"),
                  key=lambda row: float(row["Time(us)"]), reverse=True)[:5]
    summary = {
        "rank": rank, "directory": str(directory), "inputs": identity,
        "kernel_rows": len(rows), "task_core_counts": {k: len(v) for k, v in groups.items()},
        "first_utc_ns": str(first), "last_utc_ns": str(last),
        "exported_kernel_span_ms": span / 1e6,
        "all_kernel_union_ms": active / 1e6,
        "no_exported_kernel_ms": (span - active) / 1e6,
        "largest_no_exported_kernel_gap_ms": max(
            (b[0] - a[1] for a, b in zip(all_intervals, all_intervals[1:])), default=0) / 1e6,
        "compute_union_ms": comp / 1e6, "communication_union_ms": comm / 1e6,
        "compute_communication_overlap_ms": overlap / 1e6,
        "communication_without_compute_ms": (comm - overlap) / 1e6,
        "top_operator_sum_not_wall_time": dict(top),
        "duration_weighted_pipeline_ratios": {
            k: {"ratio": v[0] / v[1] if v[1] else None, "valid_rows": v[2],
                "core_duration_weight_us": v[1]} for k, v in metrics.items()},
        "step_rows": steps,
        "per_step_latency_proven": bool(steps) and all(r.get("Step", "").strip() for r in steps),
        "top_api_sum_not_wall_time": apis,
        "cpu_numa_causality_proven": False,
    }
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = {"schema": "hypic-posthoc-profile-timeline/v1",
              "source_commit": "c12060cd47e7575ead059983d7a8bb4704165c98",
              "scope": "separate exported-kernel spans, not service TTFT/TPOT or a baseline/candidate pair",
              "causal_hccl_or_quality_root_proven": False, "phases": {}}
    for phase, root in ROOTS.items():
        dirs = sorted(root.glob("rank*_ascend_pt"))
        assert len(dirs) == 4
        ranks = [analyze_rank(directory, rank) for rank, directory in enumerate(dirs)]
        starts = [int(r["first_utc_ns"]) for r in ranks]
        ends = [int(r["last_utc_ns"]) for r in ranks]
        result["phases"][phase] = {
            "ranks": ranks, "first_timestamp_spread_ms": (max(starts) - min(starts)) / 1e6,
            "last_timestamp_spread_ms": (max(ends) - min(ends)) / 1e6,
            "cross_rank_clock_calibration_proven": False}
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    with args.output.open("x") as stream:
        stream.write(encoded)
    print(json.dumps({"path": str(args.output), "sha256": hashlib.sha256(encoded.encode()).hexdigest(),
                      "phases": {p: [{k: r[k] for k in (
                          "rank", "kernel_rows", "exported_kernel_span_ms", "compute_union_ms",
                          "communication_union_ms", "compute_communication_overlap_ms",
                          "no_exported_kernel_ms", "largest_no_exported_kernel_gap_ms",
                          "per_step_latency_proven")} for r in value["ranks"]]
                                 for p, value in result["phases"].items()}}, sort_keys=True))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Summarize MMAR timing; matching task IDs are diagnostic, not causal proof."""
import argparse
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import statistics

def stats(values):
    a = sorted(float(v) for v in values)
    return {"count": len(a), "mean_us": statistics.mean(a),
            "median_us": statistics.median(a),
            "p95_lower_us": a[int((len(a)-1)*.95)]} if a else {"count": 0}

def analyze(paths):
    ranks = []
    for path in paths:
        records = {}
        occurrences = {}
        intervals = []
        groups = {}
        with path.open() as stream:
            for row in csv.DictReader(stream):
                op = row["OP Type"]
                if op not in ("MatmulAllReduce", "MatmulAllReduceMc2AicpuKernel"):
                    continue
                start = Decimal(row["Task Start Time(us)"].strip())
                duration = Decimal(row["Task Duration(us)"])
                if duration < 0:
                    raise ValueError("negative duration")
                intervals.append((start, start + duration))
                shape = row["Input Shapes"].strip('"')
                groups.setdefault((op, shape), []).append(duration)
                if op == "MatmulAllReduce":
                    key = (row["Model ID"], row["Stream ID"], row["Task ID"])
                    occurrences[key] = occurrences.get(key, 0) + 1
                    key = key + (occurrences[key],)
                    records[key] = (shape, start, start + duration)
        if not records:
            raise ValueError("no MMAR records")
        union = Decimal(0)
        end = None
        for left, right in sorted(intervals):
            union += max(Decimal(0), right - max(left, end if end is not None else left))
            end = max(right, end) if end is not None else right
        total = sum((right-left for left,right in intervals), Decimal(0))
        ranks.append({"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                      "selected_sum_us": float(total), "selected_union_us": float(union),
                      "overlap_excess_us": float(total-union),
                      "groups": [{"op": op, "shape": shape, **stats(v)}
                                 for (op,shape),v in sorted(groups.items())],
                      "_records": records})
    keys = set(ranks[0]["_records"])
    if any(set(rank["_records"]) != keys for rank in ranks):
        raise ValueError("rank task keys differ; no cross-rank alignment")
    aligned = {}
    for key in sorted(keys):
        rows = [rank["_records"][key] for rank in ranks]
        if len({row[0] for row in rows}) != 1:
            raise ValueError("aligned task shapes differ")
        values = aligned.setdefault(rows[0][0], {"start_spread": [], "end_spread": []})
        values["start_spread"].append(max(row[1] for row in rows)-min(row[1] for row in rows))
        values["end_spread"].append(max(row[2] for row in rows)-min(row[2] for row in rows))
    for rank in ranks:
        del rank["_records"]
    return {"schema": "qwen35-mmar-timeline/v1",
            "limitations": ["Profiling durations are not unprofiled E2E latency.",
                           "Cross-device timestamps require clock alignment validation.",
                           "Task ID/stream/model/replay occurrence/shape agreement is diagnostic only.",
                           "Interval overlap does not prove removable overhead or causality."],
            "ranks": ranks,
            "cross_rank": {shape: {k: stats(v) for k,v in values.items()}
                           for shape,values in sorted(aligned.items())}}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile_root", type=Path)
    args = parser.parse_args()
    paths = sorted(args.profile_root.glob("rank*/PROF_*/mindstudio_profiler_output/op_summary*.csv"))
    if len(paths) != 4:
        parser.error("expected exactly four rank CSV files")
    print(json.dumps(analyze(paths), indent=2))

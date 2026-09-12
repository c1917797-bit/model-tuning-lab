#!/usr/bin/env python3
"""Measure the exclusive T16 GDN terminal-chain budget from msprof CSVs."""

import argparse
import bisect
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics

AICPU = "MatmulAllReduceMc2AicpuKernel"
CORE = "MatmulAllReduce"
NORM = "_layer_norm_fwd_1pass_kernel_npu"
DECODE_SHAPE = "1,1536;1536,5120"


def percentile_lower(values, fraction):
    ordered = sorted(values)
    return ordered[max(0, math.ceil(fraction * len(ordered)) - 1)]


def summarize(values):
    return {
        "count": len(values),
        "median_us": statistics.median(values),
        "p95_lower_us": percentile_lower(values, 0.95),
        "min_us": min(values),
        "max_us": max(values),
    }


def load_rows(path):
    rows = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for raw in csv.DictReader(handle):
            try:
                start = float(raw["Task Start Time(us)"].strip())
                duration = float(raw["Task Duration(us)"].strip())
            except (KeyError, TypeError, ValueError):
                continue
            rows.append(
                {
                    "start": start,
                    "end": start + duration,
                    "duration": duration,
                    "name": raw.get("Op Name", ""),
                    "shape": raw.get("Input Shapes", ""),
                    "stream": raw.get("Stream ID", ""),
                }
            )
    rows.sort(key=lambda item: item["start"])
    return rows


def analyze_rows(
    rows,
    lookback=15,
    norm_gap_max_us=25.0,
    pair_window_us=1000.0,
    tail_slack_us=25.0,
):
    aicpu = [row for row in rows if row["name"] == AICPU]
    starts = [row["start"] for row in aicpu]
    samples = []
    target_count = 0
    missing_norm = 0
    missing_aicpu = 0

    for index, core in enumerate(rows):
        if core["name"] != CORE or DECODE_SHAPE not in core["shape"]:
            continue
        target_count += 1
        norm = None
        for previous in range(index - 1, max(-1, index - lookback - 1), -1):
            candidate = rows[previous]
            gap = core["start"] - candidate["end"]
            if (
                candidate["stream"] == core["stream"]
                and candidate["name"] == NORM
                and 0.0 <= gap <= norm_gap_max_us
            ):
                norm = candidate
                break
        if norm is None:
            missing_norm += 1
            continue

        aicpu_index = bisect.bisect_right(starts, core["start"]) - 1
        envelope = None
        while aicpu_index >= 0:
            candidate = aicpu[aicpu_index]
            if core["start"] - candidate["start"] >= pair_window_us:
                break
            if candidate["end"] >= core["end"] - tail_slack_us:
                envelope = candidate
                break
            aicpu_index -= 1
        if envelope is None:
            missing_aicpu += 1
            continue

        samples.append(
            {
                "aicpu_start_to_norm_start_us": norm["start"] - envelope["start"],
                "norm_duration_us": norm["duration"],
                "norm_start_to_core_start_us": core["start"] - norm["start"],
                "norm_start_to_envelope_end_us": max(core["end"], envelope["end"])
                - norm["start"],
                "full_envelope_us": max(core["end"], envelope["end"])
                - envelope["start"],
            }
        )

    metrics = {}
    if samples:
        for key in samples[0]:
            metrics[key] = summarize([sample[key] for sample in samples])
    return {
        "target_k1536_calls": target_count,
        "paired_gdn_calls": len(samples),
        "missing_preceding_gdn_norm": missing_norm,
        "missing_aicpu_envelope": missing_aicpu,
        "metrics": metrics,
    }


def analyze_files(paths, required_saving_ms, gdn_layers):
    ranks = []
    for rank, path in enumerate(paths):
        result = analyze_rows(load_rows(path))
        result["rank"] = rank
        result["path"] = str(path)
        result["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        ranks.append(result)

    medians = [
        rank["metrics"]["norm_start_to_envelope_end_us"]["median_us"]
        for rank in ranks
        if rank["paired_gdn_calls"]
    ]
    if len(medians) != len(ranks):
        raise ValueError("every rank must contain paired GDN terminal samples")
    upper_bound_ms = max(medians) * gdn_layers / 1000.0
    coverage = upper_bound_ms / required_saving_ms
    decision = (
        "admit-as-standalone-opportunity"
        if upper_bound_ms >= required_saving_ms
        else "reject-as-standalone-retain-as-stack-component"
    )
    return {
        "schema": "qwen35-t19-gdn-terminal-budget/v1",
        "method": (
            "Pair each decode M=1 K1536 MMAR core with the nearest preceding "
            "same-stream GDN norm and its enclosing MMAR AICPU interval."
        ),
        "evidence_boundary": (
            "Profile-derived zero-cost upper bound, not unprofiled E2E speedup; "
            "overlap does not prove removability."
        ),
        "ranks": ranks,
        "opportunity": {
            "gdn_layers_per_token": gdn_layers,
            "required_c1_tpot_saving_ms_per_token": required_saving_ms,
            "max_rank_median_norm_to_envelope_end_us": max(medians),
            "zero_cost_upper_bound_ms_per_token": upper_bound_ms,
            "required_budget_coverage_fraction": coverage,
        },
        "decision": decision,
        "next_gate": (
            "Do not build GDN terminal fusion as the sole TPOT treatment. "
            "Only compose it with an independently gated dense-tail mechanism "
            "whose conservative combined saving covers the required budget."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", nargs="+", type=Path)
    parser.add_argument("--required-saving-ms", type=float, default=6.098464807517281)
    parser.add_argument("--gdn-layers", type=int, default=48)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = analyze_files(sorted(args.csv), args.required_saving_ms, args.gdn_layers)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()

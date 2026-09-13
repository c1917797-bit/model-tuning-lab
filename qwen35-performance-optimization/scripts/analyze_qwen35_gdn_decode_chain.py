#!/usr/bin/env python3
"""Measure non-overlapping Qwen3.5 GDN decode preprocessing envelopes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path

TRANSPOSE = "aclnnContiguous_TransposeAiCore_Transpose"
TRANSPOSE_SHAPE = '"2560,4;2"'
CAUSAL = "CausalConv1d"
CAUSAL_SHAPE = '"1,2560;4,2560;;901,3,2560;2;1;;"'
CAT = "aclnnCat_ConcatD_ConcatD"
CAT_SHAPE = '"512;512;1536"'
COPY = "aclnnInplaceCopy_CastAiCore_Cast"
COPY_SHAPE = '"12"'
GATING = "aclnnFusedGdnGating_FusedGdnGating_FusedGdnGating"
GATING_SHAPE = '"12;1,12;1,12;12"'
L2NORM = "l2norm_fwd_kernel2"
L2NORM_SHAPE = "N/A"
RECURRENT = "aclnnRecurrentGatedDeltaRule_RecurrentGatedDeltaRule_RecurrentGatedDeltaRule"
RECURRENT_SHAPE = '"1,4,128;1,4,128;1,12,128;1,12;901,12,128,128;2;1;1,12"'

REVERSE_SEQUENCE = (
    ("l2norm_b", L2NORM, L2NORM_SHAPE),
    ("l2norm_a", L2NORM, L2NORM_SHAPE),
    ("gating", GATING, GATING_SHAPE),
    ("copy", COPY, COPY_SHAPE),
    ("cat", CAT, CAT_SHAPE),
    ("causal_conv1d", CAUSAL, CAUSAL_SHAPE),
    ("weight_transpose", TRANSPOSE, TRANSPOSE_SHAPE),
)


def percentile_lower(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(fraction * len(ordered)) - 1)]


def summarize(values: list[float]) -> dict[str, float | int]:
    return {
        "count": len(values),
        "median_us": statistics.median(values),
        "p95_lower_us": percentile_lower(values, 0.95),
        "min_us": min(values),
        "max_us": max(values),
    }


def load_rows(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
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
    rows.sort(key=lambda row: float(row["start"]))
    return rows


def _matches(row: dict[str, object], name: str, shape: str) -> bool:
    return row["name"] == name and row["shape"] == shape


def analyze_rows(
    rows: list[dict[str, object]],
    *,
    lookback_rows: int = 80,
    max_envelope_us: float = 1000.0,
) -> dict[str, object]:
    by_stream: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        by_stream.setdefault(str(row["stream"]), []).append(row)

    target_count = 0
    samples: list[dict[str, float]] = []
    rejection_counts: dict[str, int] = {}
    for stream_rows in by_stream.values():
        for index, recurrent in enumerate(stream_rows):
            if not _matches(recurrent, RECURRENT, RECURRENT_SHAPE):
                continue
            target_count += 1
            cursor = index - 1
            found: dict[str, dict[str, object]] = {"recurrent": recurrent}
            rejected = None
            for label, name, shape in REVERSE_SEQUENCE:
                lower = max(-1, cursor - lookback_rows)
                match = None
                while cursor > lower:
                    candidate = stream_rows[cursor]
                    if float(recurrent["end"]) - float(candidate["start"]) > max_envelope_us:
                        break
                    if _matches(candidate, name, shape):
                        match = candidate
                        cursor -= 1
                        break
                    cursor -= 1
                if match is None:
                    rejected = f"missing_{label}"
                    rejection_counts[rejected] = rejection_counts.get(rejected, 0) + 1
                    break
                found[label] = match
            if rejected is not None:
                continue

            recurrent_end = float(recurrent["end"])
            sample = {
                f"{label}_duration_us": float(found[label]["duration"])
                for label in found
            }
            for label in (
                "weight_transpose",
                "causal_conv1d",
                "cat",
                "gating",
            ):
                sample[f"{label}_start_to_recurrent_end_us"] = (
                    recurrent_end - float(found[label]["start"])
                )
            samples.append(sample)

    metrics: dict[str, dict[str, float | int]] = {}
    if samples:
        for key in samples[0]:
            metrics[key] = summarize([sample[key] for sample in samples])
    return {
        "target_recurrent_calls": target_count,
        "paired_chains": len(samples),
        "rejection_counts": rejection_counts,
        "metrics": metrics,
    }


def _rank(path: Path) -> int:
    for part in path.parts:
        if part.startswith("rank") and part[4:].isdigit():
            return int(part[4:])
    raise ValueError(f"cannot determine rank from {path}")


def analyze_files(
    paths: list[Path],
    *,
    decode_steps: int,
    gdn_layers: int,
    required_saving_ms: float,
) -> dict[str, object]:
    expected_calls = decode_steps * gdn_layers
    ranks = []
    for path in sorted(paths, key=_rank):
        result = analyze_rows(load_rows(path))
        if result["target_recurrent_calls"] != expected_calls:
            raise ValueError(
                f"{path}: expected {expected_calls} recurrent calls, "
                f"found {result['target_recurrent_calls']}"
            )
        if result["paired_chains"] != expected_calls:
            raise ValueError(f"{path}: not every recurrent call has a complete chain")
        result["rank"] = _rank(path)
        result["path"] = str(path)
        result["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        ranks.append(result)

    transpose_medians = [
        float(rank["metrics"]["weight_transpose_duration_us"]["median_us"])
        for rank in ranks
    ]
    chain_medians = [
        float(
            rank["metrics"]["weight_transpose_start_to_recurrent_end_us"][
                "median_us"
            ]
        )
        for rank in ranks
    ]
    prepack_upper_ms = max(transpose_medians) * gdn_layers / 1000.0
    chain_upper_ms = max(chain_medians) * gdn_layers / 1000.0
    return {
        "schema": "qwen35-gdn-decode-chain/v1",
        "method": (
            "Pair each exact M=1 recurrent GDN kernel backwards on the same stream "
            "with two l2norms, gating, copy, cat, causal-conv, and weight transpose."
        ),
        "evidence_boundary": (
            "Each envelope is non-overlapping within one chain but remains a "
            "profile-derived zero-cost upper bound, not claimed end-to-end savings."
        ),
        "decode_steps": decode_steps,
        "gdn_layers_per_token": gdn_layers,
        "ranks": ranks,
        "opportunity": {
            "required_c1_tpot_saving_ms_per_token": required_saving_ms,
            "max_rank_median_weight_transpose_us": max(transpose_medians),
            "conv_prepack_zero_cost_upper_bound_ms_per_token": prepack_upper_ms,
            "conv_prepack_required_gap_coverage_fraction": (
                prepack_upper_ms / required_saving_ms
            ),
            "max_rank_median_full_chain_us": max(chain_medians),
            "full_chain_zero_cost_upper_bound_ms_per_token": chain_upper_ms,
            "full_chain_required_gap_coverage_fraction": (
                chain_upper_ms / required_saving_ms
            ),
        },
        "decision": (
            "admit-conv-prepack-as-stack-component-and-chain-as-follow-up-target"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", nargs="+", type=Path)
    parser.add_argument("--decode-steps", type=int, required=True)
    parser.add_argument("--gdn-layers", type=int, default=48)
    parser.add_argument("--required-saving-ms", type=float, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = analyze_files(
        args.csv,
        decode_steps=args.decode_steps,
        gdn_layers=args.gdn_layers,
        required_saving_ms=args.required_saving_ms,
    )
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()

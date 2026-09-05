#!/usr/bin/env python3
"""Aggregate Qwen3.5 ShortGPT Block Influence without prompt data."""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import math
import statistics
from pathlib import Path


def resolve_paths(values: list[str]) -> list[Path]:
    paths: set[Path] = set()
    for value in values:
        candidate = Path(value)
        if candidate.is_dir():
            paths.update(candidate.glob("*.jsonl"))
        elif candidate.is_file():
            paths.add(candidate)
        else:
            paths.update(Path(item) for item in glob.glob(value))
    resolved = sorted(path.resolve() for path in paths)
    if not resolved:
        raise ValueError("no Block Influence JSONL files found")
    return resolved


def load_records(paths: list[Path], expected_layers: int) -> list[dict]:
    records: list[dict] = []
    for path in paths:
        with path.open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                row = json.loads(line)
                layer = int(row["layer"])
                sample_tokens = int(row["sample_tokens"])
                influence_sum = float(row["influence_sum"])
                influence_mean = float(row["influence_mean"])
                if not 0 <= layer < expected_layers:
                    raise ValueError(
                        f"{path}:{line_number}: layer {layer} out of range"
                    )
                if sample_tokens < 1:
                    raise ValueError(
                        f"{path}:{line_number}: non-positive sample_tokens"
                    )
                if not (
                    math.isfinite(influence_sum)
                    and math.isfinite(influence_mean)
                ):
                    raise ValueError(
                        f"{path}:{line_number}: non-finite influence"
                    )
                records.append(
                    {
                        "layer": layer,
                        "layer_type": str(row["layer_type"]),
                        "sample_tokens": sample_tokens,
                        "influence_sum": influence_sum,
                        "influence_mean": influence_mean,
                    }
                )
    if not records:
        raise ValueError("Block Influence files contain no records")
    return records


def rank_values(values: dict[int, float]) -> dict[int, float]:
    ordered = sorted(values.items(), key=lambda item: (item[1], item[0]))
    ranks: dict[int, float] = {}
    cursor = 0
    while cursor < len(ordered):
        end = cursor + 1
        while end < len(ordered) and ordered[end][1] == ordered[cursor][1]:
            end += 1
        average_rank = (cursor + end - 1) / 2.0
        for index in range(cursor, end):
            ranks[ordered[index][0]] = average_rank
        cursor = end
    return ranks


def pearson(left: list[float], right: list[float]) -> float:
    left_mean = statistics.fmean(left)
    right_mean = statistics.fmean(right)
    numerator = sum(
        (a - left_mean) * (b - right_mean)
        for a, b in zip(left, right)
    )
    left_scale = math.sqrt(sum((a - left_mean) ** 2 for a in left))
    right_scale = math.sqrt(sum((b - right_mean) ** 2 for b in right))
    if left_scale == 0 or right_scale == 0:
        return 1.0 if left == right else 0.0
    return numerator / (left_scale * right_scale)


def spearman(left: dict[int, float], right: dict[int, float]) -> float:
    if set(left) != set(right):
        raise ValueError("rankings cover different layer sets")
    keys = sorted(left)
    left_ranks = rank_values(left)
    right_ranks = rank_values(right)
    return pearson(
        [left_ranks[key] for key in keys],
        [right_ranks[key] for key in keys],
    )


def compress_layers(layers: list[int]) -> str:
    if not layers:
        return ""
    ordered = sorted(layers)
    ranges: list[str] = []
    start = previous = ordered[0]
    for layer in ordered[1:]:
        if layer == previous + 1:
            previous = layer
            continue
        ranges.append(str(start) if start == previous else f"{start}-{previous}")
        start = previous = layer
    ranges.append(str(start) if start == previous else f"{start}-{previous}")
    return ",".join(ranges)


def summarize(
    records: list[dict],
    expected_layers: int,
    stability_splits: int,
    candidate_sizes: list[int],
    min_observations: int,
    min_spearman: float,
) -> dict:
    by_layer: dict[int, list[dict]] = {
        layer: [] for layer in range(expected_layers)
    }
    for row in records:
        by_layer[row["layer"]].append(row)

    missing = [layer for layer, rows in by_layer.items() if not rows]
    if missing:
        raise ValueError(f"missing layer observations: {missing}")

    layer_summaries: list[dict] = []
    overall_values: dict[int, float] = {}
    for layer, rows in by_layer.items():
        layer_types = {row["layer_type"] for row in rows}
        if len(layer_types) != 1:
            raise ValueError(
                f"layer {layer} has inconsistent types: {sorted(layer_types)}"
            )
        total_tokens = sum(row["sample_tokens"] for row in rows)
        total_influence = sum(row["influence_sum"] for row in rows)
        weighted_mean = total_influence / total_tokens
        overall_values[layer] = weighted_mean
        layer_summaries.append(
            {
                "layer": layer,
                "layer_type": next(iter(layer_types)),
                "observation_count": len(rows),
                "sample_tokens": total_tokens,
                "weighted_influence": weighted_mean,
                "unweighted_mean": statistics.fmean(
                    row["influence_mean"] for row in rows
                ),
            }
        )

    ranked = sorted(
        layer_summaries,
        key=lambda row: (row["weighted_influence"], row["layer"]),
    )
    for rank, row in enumerate(ranked, start=1):
        row["global_rank_lowest_first"] = rank

    type_rankings: dict[str, list[int]] = {}
    for layer_type in sorted({row["layer_type"] for row in ranked}):
        type_rankings[layer_type] = [
            row["layer"]
            for row in ranked
            if row["layer_type"] == layer_type
        ]

    split_values: list[dict[int, float]] = []
    for split in range(stability_splits):
        values: dict[int, float] = {}
        for layer, rows in by_layer.items():
            selected = [
                row for index, row in enumerate(rows)
                if index % stability_splits == split
            ]
            if not selected:
                raise ValueError(
                    f"layer {layer} has no observations in split {split}"
                )
            values[layer] = sum(
                row["influence_sum"] for row in selected
            ) / sum(row["sample_tokens"] for row in selected)
        split_values.append(values)

    correlations = [
        spearman(split_values[left], split_values[right])
        for left in range(stability_splits)
        for right in range(left + 1, stability_splits)
    ]
    minimum_observations = min(len(rows) for rows in by_layer.values())
    minimum_correlation = min(correlations) if correlations else 1.0
    ready = (
        minimum_observations >= min_observations
        and minimum_correlation >= min_spearman
    )

    candidates = []
    for size in candidate_sizes:
        if not 0 < size < expected_layers:
            raise ValueError(f"invalid candidate size: {size}")
        layers = sorted(row["layer"] for row in ranked[:size])
        candidates.append(
            {
                "removed_layer_count": size,
                "layers": layers,
                "env_spec": compress_layers(layers),
            }
        )

    return {
        "expected_layers": expected_layers,
        "record_count": len(records),
        "minimum_observations_per_layer": minimum_observations,
        "ranking_stability": {
            "split_count": stability_splits,
            "pairwise_spearman": correlations,
            "minimum_spearman": minimum_correlation,
            "required_minimum_spearman": min_spearman,
        },
        "ready_to_freeze": ready,
        "ranked_layers": ranked,
        "ranked_layers_by_type": type_rankings,
        "candidate_sets_lowest_global_influence": candidates,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-layers", type=int, default=64)
    parser.add_argument("--stability-splits", type=int, default=4)
    parser.add_argument("--candidate-sizes", default="8,16,20")
    parser.add_argument("--min-observations-per-layer", type=int, default=8)
    parser.add_argument("--min-spearman", type=float, default=0.80)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.expected_layers < 2:
        raise ValueError("--expected-layers must be at least 2")
    if args.stability_splits < 2:
        raise ValueError("--stability-splits must be at least 2")
    candidate_sizes = [
        int(item) for item in args.candidate_sizes.split(",") if item
    ]
    paths = resolve_paths(args.inputs)
    records = load_records(paths, args.expected_layers)
    report = summarize(
        records,
        args.expected_layers,
        args.stability_splits,
        candidate_sizes,
        args.min_observations_per_layer,
        args.min_spearman,
    )
    report.update(
        {
            "schema": "qwen35-shortgpt-bi-analysis/v1",
            "input_files": [
                {
                    "name": path.name,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
                for path in paths
            ],
            "privacy": "input contains aggregate layer metrics only",
        }
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0 if report["ready_to_freeze"] else 3


if __name__ == "__main__":
    raise SystemExit(main())

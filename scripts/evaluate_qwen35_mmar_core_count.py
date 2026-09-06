#!/usr/bin/env python3
"""Evaluate immutable Qwen3.5 MMAR core-count microbenchmark artifacts."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


SHAPES = ((1, 1536, 5120), (1, 4352, 5120))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--minimum-speedup", type=float, default=1.02)
    parser.add_argument(
        "--correctness-envelope-factor", type=float, default=2.0
    )
    return parser.parse_args()


def load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def cells_by_shape(result: dict[str, Any]) -> dict[tuple[int, int, int], dict[str, Any]]:
    return {
        (int(cell["m"]), int(cell["k"]), int(cell["n"])): cell
        for cell in result["cells"]
    }


def compare_outputs(
    baseline_cell: dict[str, Any], candidate_cell: dict[str, Any]
) -> dict[str, float]:
    baseline_outputs = baseline_cell["output_by_rank"]
    candidate_outputs = candidate_cell["output_by_rank"]
    if len(baseline_outputs) != len(candidate_outputs):
        raise RuntimeError("candidate rank count differs from baseline")
    absolute_differences: list[float] = []
    baseline_squared_sum = 0.0
    difference_squared_sum = 0.0
    for baseline_rank, candidate_rank in zip(
        baseline_outputs, candidate_outputs
    ):
        if len(baseline_rank) != len(candidate_rank):
            raise RuntimeError("candidate output size differs from baseline")
        for baseline_value, candidate_value in zip(
            baseline_rank, candidate_rank
        ):
            baseline_float = float(baseline_value)
            difference = abs(float(candidate_value) - baseline_float)
            absolute_differences.append(difference)
            baseline_squared_sum += baseline_float * baseline_float
            difference_squared_sum += difference * difference
    if not absolute_differences:
        raise RuntimeError("empty output evidence")
    baseline_l2 = math.sqrt(baseline_squared_sum)
    return {
        "max_abs": max(absolute_differences),
        "mean_abs": sum(absolute_differences) / len(absolute_differences),
        "relative_l2": (
            math.sqrt(difference_squared_sum) / baseline_l2
            if baseline_l2 > 0.0
            else math.inf
        ),
    }


def main() -> int:
    args = parse_args()
    baseline_path = args.root / "core-default.json"
    baseline = cells_by_shape(load(baseline_path))
    if set(baseline) != set(SHAPES):
        raise RuntimeError(f"unexpected baseline shapes: {sorted(baseline)}")
    for shape in SHAPES:
        if len(baseline[shape].get("output_by_rank", [])) != 4:
            raise RuntimeError(f"baseline lacks four-rank output evidence for {shape}")

    candidates: list[dict[str, Any]] = []
    for path in sorted(args.root.glob("core-[0-9]*.json")):
        result = load(path)
        cells = cells_by_shape(result)
        if set(cells) != set(SHAPES):
            raise RuntimeError(f"unexpected shapes in {path}: {sorted(cells)}")
        speedups = {
            f"m{m}_k{k}_n{n}": (
                float(baseline[(m, k, n)]["median_max_rank_us"])
                / float(cells[(m, k, n)]["median_max_rank_us"])
            )
            for m, k, n in SHAPES
        }
        comparisons = {
            f"m{m}_k{k}_n{n}": compare_outputs(
                baseline[(m, k, n)], cells[(m, k, n)]
            )
            for m, k, n in SHAPES
        }
        correctness_gates: dict[str, dict[str, Any]] = {}
        for shape in SHAPES:
            m, k, n = shape
            key = f"m{m}_k{k}_n{n}"
            baseline_reference = baseline[shape]["correctness"]
            thresholds = {
                "max_abs": (
                    args.correctness_envelope_factor
                    * float(baseline_reference["max_abs"])
                ),
                "mean_abs": (
                    args.correctness_envelope_factor
                    * float(baseline_reference["max_rank_mean_abs"])
                ),
                "relative_l2": (
                    args.correctness_envelope_factor
                    * float(baseline_reference["max_rank_relative_l2"])
                ),
            }
            metric_passes = {
                metric: comparisons[key][metric] <= threshold
                for metric, threshold in thresholds.items()
            }
            correctness_gates[key] = {
                "candidate_vs_default": comparisons[key],
                "thresholds_from_default_reference_error": thresholds,
                "metric_passes": metric_passes,
                "passes": all(metric_passes.values()),
            }
        correct = all(item["passes"] for item in correctness_gates.values())
        passes = correct and all(
            speedup >= args.minimum_speedup for speedup in speedups.values()
        )
        candidates.append(
            {
                "label": result.get("label"),
                "path": str(path),
                "correct": correct,
                "correctness_gates": correctness_gates,
                "speedups_vs_default": speedups,
                "minimum_shape_speedup": min(speedups.values()),
                "passes_e2e_gate": passes,
            }
        )

    decision = {
        "schema": "qwen35-mmar-core-count-decision/v2",
        "baseline": str(baseline_path),
        "minimum_speedup": args.minimum_speedup,
        "correctness_envelope_factor": args.correctness_envelope_factor,
        "correctness_policy": (
            "candidate fused output must remain within the configured factor "
            "of the frozen default "
            "fused-vs-unfused BF16 error envelope for max_abs, mean_abs, and "
            "relative_l2 on every real shape"
        ),
        "required_shapes": [list(shape) for shape in SHAPES],
        "candidates": candidates,
        "passing_labels": [
            item["label"] for item in candidates if item["passes_e2e_gate"]
        ],
    }
    destination = args.root / "decision.json"
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite {destination}")
    destination.write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

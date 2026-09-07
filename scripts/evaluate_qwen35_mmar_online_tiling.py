#!/usr/bin/env python3
"""Evaluate the immutable arch22 MMAR online-HCCL-tiling A/B artifacts."""

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
    parser.add_argument("--selected-k", type=int)
    parser.add_argument("--nonselected-minimum-speedup", type=float, default=0.98)
    parser.add_argument("--correctness-envelope-factor", type=float, default=2.0)
    return parser.parse_args()


def load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def by_shape(result: dict[str, Any]) -> dict[tuple[int, int, int], dict[str, Any]]:
    return {
        (int(cell["m"]), int(cell["k"]), int(cell["n"])): cell
        for cell in result["cells"]
    }


def output_error(
    baseline_cell: dict[str, Any], candidate_cell: dict[str, Any]
) -> dict[str, float]:
    baseline_outputs = baseline_cell["output_by_rank"]
    candidate_outputs = candidate_cell["output_by_rank"]
    if len(baseline_outputs) != len(candidate_outputs):
        raise RuntimeError("candidate rank count differs from baseline")
    differences: list[float] = []
    baseline_squared_sum = 0.0
    difference_squared_sum = 0.0
    for baseline_rank, candidate_rank in zip(baseline_outputs, candidate_outputs):
        if len(baseline_rank) != len(candidate_rank):
            raise RuntimeError("candidate output size differs from baseline")
        for baseline_value, candidate_value in zip(baseline_rank, candidate_rank):
            baseline_float = float(baseline_value)
            difference = abs(float(candidate_value) - baseline_float)
            differences.append(difference)
            baseline_squared_sum += baseline_float * baseline_float
            difference_squared_sum += difference * difference
    if not differences:
        raise RuntimeError("empty output evidence")
    baseline_l2 = math.sqrt(baseline_squared_sum)
    return {
        "max_abs": max(differences),
        "mean_abs": sum(differences) / len(differences),
        "relative_l2": (
            math.sqrt(difference_squared_sum) / baseline_l2
            if baseline_l2 > 0.0
            else math.inf
        ),
    }


def main() -> int:
    args = parse_args()
    default_path = args.root / "default.json"
    online_path = args.root / "online.json"
    default = by_shape(load(default_path))
    online = by_shape(load(online_path))
    if set(default) != set(SHAPES) or set(online) != set(SHAPES):
        raise RuntimeError(
            f"unexpected shapes: default={sorted(default)}, online={sorted(online)}"
        )

    cells: dict[str, Any] = {}
    for shape in SHAPES:
        key = f"m{shape[0]}_k{shape[1]}_n{shape[2]}"
        baseline_cell = default[shape]
        candidate_cell = online[shape]
        if len(baseline_cell.get("output_by_rank", [])) != 4:
            raise RuntimeError(f"default lacks four-rank output evidence for {shape}")
        if len(candidate_cell.get("output_by_rank", [])) != 4:
            raise RuntimeError(f"online lacks four-rank output evidence for {shape}")
        cross_launch_comparison = output_error(baseline_cell, candidate_cell)
        reference = baseline_cell["deterministic_correctness"]
        comparison = candidate_cell["deterministic_correctness"]
        thresholds = {
            "max_abs": args.correctness_envelope_factor * float(reference["max_abs"]),
            "mean_abs": args.correctness_envelope_factor
            * float(reference["max_rank_mean_abs"]),
            "relative_l2": args.correctness_envelope_factor
            * float(reference["max_rank_relative_l2"]),
        }
        metric_passes = {
            metric: comparison[metric] <= threshold
            for metric, threshold in thresholds.items()
        }
        speedup = float(baseline_cell["median_max_rank_us"]) / float(
            candidate_cell["median_max_rank_us"]
        )
        required_speedup = (
            args.minimum_speedup
            if args.selected_k is None or shape[1] == args.selected_k
            else args.nonselected_minimum_speedup
        )
        cells[key] = {
            "default_median_max_rank_us": baseline_cell["median_max_rank_us"],
            "online_median_max_rank_us": candidate_cell["median_max_rank_us"],
            "speedup_vs_default": speedup,
            "required_speedup": required_speedup,
            "speedup_gate_passes": speedup >= required_speedup,
            "candidate_vs_default_diagnostic": cross_launch_comparison,
            "baseline_deterministic_reference_error": reference,
            "candidate_deterministic_reference_error": comparison,
            "thresholds_from_default_reference_error": thresholds,
            "metric_passes": metric_passes,
            "baseline_hccl_reference_diagnostic": baseline_cell["correctness"],
            "candidate_hccl_reference_diagnostic": candidate_cell["correctness"],
            "correct": all(metric_passes.values()),
        }

    correct = all(cell["correct"] for cell in cells.values())
    minimum_shape_speedup = min(
        float(cell["speedup_vs_default"]) for cell in cells.values()
    )
    speedup_gate_passes = all(
        bool(cell["speedup_gate_passes"]) for cell in cells.values()
    )
    passes = correct and speedup_gate_passes
    decision = {
        "schema": "qwen35-mmar-online-tiling-decision/v2",
        "baseline": str(default_path),
        "candidate": str(online_path),
        "required_shapes": [list(shape) for shape in SHAPES],
        "minimum_speedup": args.minimum_speedup,
        "selected_k": args.selected_k,
        "nonselected_minimum_speedup": args.nonselected_minimum_speedup,
        "correctness_envelope_factor": args.correctness_envelope_factor,
        "correctness_policy": (
            "candidate fused output versus a fixed-rank-order CPU FP32 sum of "
            "rank-local NPU BF16 matmul outputs must remain within the configured "
            "factor of the frozen predecessor error envelope; cross-launch fused "
            "output differences and HCCL all-reduce references are diagnostic "
            "because HCCL reduction order is not stable across process launches"
        ),
        "cells": cells,
        "correct": correct,
        "minimum_shape_speedup": minimum_shape_speedup,
        "speedup_gate_passes": speedup_gate_passes,
        "passes_e2e_gate": passes,
        "decision": "promote-to-e2e" if passes else "reject",
    }
    destination = args.root / "decision.json"
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite {destination}")
    destination.write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(decision, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

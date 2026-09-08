#!/usr/bin/env python3
"""Evaluate stock MMAR versus the opt-in Qwen3.5 M=1 IPC fullmesh path."""

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
    parser.add_argument("--per-shape-minimum-speedup", type=float, default=1.0)
    parser.add_argument("--geomean-minimum-speedup", type=float, default=1.03)
    parser.add_argument("--correctness-envelope-factor", type=float, default=2.0)
    parser.add_argument("--stress-envelope-factor", type=float, default=2.0)
    return parser.parse_args()


def load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def by_shape(result: dict[str, Any]) -> dict[tuple[int, int, int], dict[str, Any]]:
    return {
        (int(cell["m"]), int(cell["k"]), int(cell["n"])): cell
        for cell in result["cells"]
    }


def stress_structure_passes(result: dict[str, Any]) -> bool:
    stress = result["stress"]
    ranks = stress["ranks"]
    expected = int(stress["requested_calls_per_rank"])
    expected_samples = {
        str(shape): (expected + len(SHAPES) - 1 - index) // len(SHAPES)
        for index, shape in enumerate(SHAPES)
    }
    return (
        bool(stress["alternating_shapes"])
        and expected >= 5000
        and len(ranks) == 4
        and all(
            int(rank["calls"]) == expected
            and bool(rank["finite"])
            and bool(rank["checkpoints"])
            and set(rank["metrics_by_shape"]) == set(expected_samples)
            and all(
                int(rank["metrics_by_shape"][shape]["samples"]) == samples
                and math.isfinite(
                    float(rank["metrics_by_shape"][shape]["max_abs_drift"])
                )
                and math.isfinite(
                    float(
                        rank["metrics_by_shape"][shape][
                            "max_relative_l2_drift"
                        ]
                    )
                )
                for shape, samples in expected_samples.items()
            )
            for rank in ranks
        )
    )


def maximum_stress_metrics(
    result: dict[str, Any],
) -> dict[str, dict[str, float]]:
    ranks = result["stress"]["ranks"]
    return {
        str(shape): {
            metric: max(
                float(rank["metrics_by_shape"][str(shape)][metric])
                for rank in ranks
            )
            for metric in ("max_abs_drift", "max_relative_l2_drift")
        }
        for shape in SHAPES
    }


def main() -> int:
    args = parse_args()
    baseline_result = load(args.root / "default.json")
    candidate_result = load(args.root / "candidate.json")
    baseline = by_shape(baseline_result)
    candidate = by_shape(candidate_result)
    if set(baseline) != set(SHAPES) or set(candidate) != set(SHAPES):
        raise RuntimeError("unexpected benchmark shapes")
    cells: dict[str, Any] = {}
    speedups: list[float] = []
    for shape in SHAPES:
        reference = baseline[shape]
        trial = candidate[shape]
        if len(reference.get("output_by_rank", [])) != 4:
            raise RuntimeError(f"baseline lacks four-rank output evidence for {shape}")
        if len(trial.get("output_by_rank", [])) != 4:
            raise RuntimeError(f"candidate lacks four-rank output evidence for {shape}")
        reference_error = reference["deterministic_correctness"]
        trial_error = trial["deterministic_correctness"]
        thresholds = {
            "max_abs": args.correctness_envelope_factor
            * float(reference_error["max_abs"]),
            "max_rank_mean_abs": args.correctness_envelope_factor
            * float(reference_error["max_rank_mean_abs"]),
            "max_rank_relative_l2": args.correctness_envelope_factor
            * float(reference_error["max_rank_relative_l2"]),
        }
        correctness = {
            metric: float(trial_error[metric]) <= threshold
            for metric, threshold in thresholds.items()
        }
        speedup = float(reference["median_max_rank_us"]) / float(
            trial["median_max_rank_us"]
        )
        speedups.append(speedup)
        cells[f"m{shape[0]}_k{shape[1]}_n{shape[2]}"] = {
            "baseline_median_max_rank_us": reference["median_max_rank_us"],
            "candidate_median_max_rank_us": trial["median_max_rank_us"],
            "speedup": speedup,
            "per_shape_perf_pass": speedup >= args.per_shape_minimum_speedup,
            "candidate_deterministic_correctness": trial_error,
            "correctness_thresholds": thresholds,
            "correctness_metric_passes": correctness,
            "correctness_pass": all(correctness.values()),
        }
    geomean = math.prod(speedups) ** (1.0 / len(speedups))
    baseline_stress_structure_pass = stress_structure_passes(baseline_result)
    candidate_stress_structure_pass = stress_structure_passes(candidate_result)
    stress_cells: dict[str, Any] = {}
    stress_numerical_pass = False
    if baseline_stress_structure_pass and candidate_stress_structure_pass:
        baseline_stress = maximum_stress_metrics(baseline_result)
        candidate_stress = maximum_stress_metrics(candidate_result)
        for shape in SHAPES:
            shape_key = str(shape)
            thresholds = {
                metric: args.stress_envelope_factor * value
                for metric, value in baseline_stress[shape_key].items()
            }
            metric_passes = {
                metric: candidate_stress[shape_key][metric] <= threshold
                for metric, threshold in thresholds.items()
            }
            stress_cells[f"m{shape[0]}_k{shape[1]}_n{shape[2]}"] = {
                "baseline_max_drift": baseline_stress[shape_key],
                "candidate_max_drift": candidate_stress[shape_key],
                "candidate_thresholds": thresholds,
                "metric_passes": metric_passes,
                "pass": all(metric_passes.values()),
            }
        stress_numerical_pass = all(
            cell["pass"] for cell in stress_cells.values()
        )
    decision = {
        "schema": "qwen35-mmar-m1-ipc-fullmesh-decision/v2",
        "gate": {
            "per_shape_minimum_speedup": args.per_shape_minimum_speedup,
            "geomean_minimum_speedup": args.geomean_minimum_speedup,
            "correctness_envelope_factor": args.correctness_envelope_factor,
            "stress_envelope_factor": args.stress_envelope_factor,
            "minimum_stress_calls_per_rank": 5000,
        },
        "cells": cells,
        "geomean_speedup": geomean,
        "correctness_pass": all(cell["correctness_pass"] for cell in cells.values()),
        "performance_pass": (
            all(cell["per_shape_perf_pass"] for cell in cells.values())
            and geomean >= args.geomean_minimum_speedup
        ),
        "stress_cells": stress_cells,
        "baseline_stress_pass": baseline_stress_structure_pass,
        "candidate_stress_pass": (
            candidate_stress_structure_pass and stress_numerical_pass
        ),
    }
    decision["accepted"] = (
        decision["correctness_pass"]
        and decision["performance_pass"]
        and decision["baseline_stress_pass"]
        and decision["candidate_stress_pass"]
    )
    output = args.root / "decision.json"
    if output.exists():
        raise FileExistsError(f"refusing to overwrite {output}")
    output.write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(decision, sort_keys=True))
    return 0 if decision["accepted"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

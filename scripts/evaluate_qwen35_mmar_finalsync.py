#!/usr/bin/env python3
"""Evaluate the frozen-baseline vs opt-in M=1 MMAR final-sync A/B."""

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
    parser.add_argument("--geomean-minimum-speedup", type=float, default=1.02)
    parser.add_argument("--correctness-envelope-factor", type=float, default=2.0)
    return parser.parse_args()

def load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)

def by_shape(result: dict[str, Any]) -> dict[tuple[int, int, int], dict[str, Any]]:
    return {(int(cell["m"]), int(cell["k"]), int(cell["n"])): cell for cell in result["cells"]}

def main() -> int:
    args = parse_args()
    baseline = by_shape(load(args.root / "default.json"))
    candidate = by_shape(load(args.root / "candidate.json"))
    if set(baseline) != set(SHAPES) or set(candidate) != set(SHAPES):
        raise RuntimeError(f"unexpected shapes: baseline={sorted(baseline)}, candidate={sorted(candidate)}")
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
            "max_abs": args.correctness_envelope_factor * float(reference_error["max_abs"]),
            "max_rank_mean_abs": args.correctness_envelope_factor * float(reference_error["max_rank_mean_abs"]),
            "max_rank_relative_l2": args.correctness_envelope_factor * float(reference_error["max_rank_relative_l2"]),
        }
        correctness_passes = {metric: float(trial_error[metric]) <= threshold for metric, threshold in thresholds.items()}
        speedup = float(reference["median_max_rank_us"]) / float(trial["median_max_rank_us"])
        speedups.append(speedup)
        key = f"m{shape[0]}_k{shape[1]}_n{shape[2]}"
        cells[key] = {
            "baseline_median_max_rank_us": reference["median_max_rank_us"],
            "candidate_median_max_rank_us": trial["median_max_rank_us"],
            "speedup": speedup,
            "per_shape_perf_pass": speedup >= args.per_shape_minimum_speedup,
            "candidate_deterministic_correctness": trial_error,
            "correctness_thresholds": thresholds,
            "correctness_metric_passes": correctness_passes,
            "correctness_pass": all(correctness_passes.values()),
        }
    geomean_speedup = math.prod(speedups) ** (1.0 / len(speedups))
    decision = {
        "schema": "qwen35-mmar-m1-finalsync-decision/v1",
        "gate": {
            "per_shape_minimum_speedup": args.per_shape_minimum_speedup,
            "geomean_minimum_speedup": args.geomean_minimum_speedup,
            "correctness_envelope_factor": args.correctness_envelope_factor,
        },
        "cells": cells,
        "geomean_speedup": geomean_speedup,
        "correctness_pass": all(cell["correctness_pass"] for cell in cells.values()),
        "performance_pass": all(cell["per_shape_perf_pass"] for cell in cells.values()) and geomean_speedup >= args.geomean_minimum_speedup,
    }
    decision["accepted"] = decision["correctness_pass"] and decision["performance_pass"]
    output = args.root / "decision.json"
    if output.exists():
        raise FileExistsError(f"refusing to overwrite {output}")
    output.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(decision, sort_keys=True))
    return 0 if decision["accepted"] else 2

if __name__ == "__main__":
    raise SystemExit(main())

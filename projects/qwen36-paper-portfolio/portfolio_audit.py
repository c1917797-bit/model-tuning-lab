#!/usr/bin/env python3
"""Compute conservative overlap-aware paper opportunity bounds."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def amdahl_speedup(share: float, local_speedup: float) -> float:
    if not 0 <= share < 1:
        raise ValueError("share must be in [0, 1)")
    if local_speedup < 1:
        raise ValueError("local speedup must be >= 1")
    return 1.0 / ((1.0 - share) + share / local_speedup)


def disjoint_speedup(components: list[tuple[float, float]]) -> float:
    removed = 0.0
    occupied = 0.0
    for share, local_speedup in components:
        if share < 0 or local_speedup < 1:
            raise ValueError("invalid component")
        occupied += share
        removed += share * (1.0 - 1.0 / local_speedup)
    if occupied >= 1 or removed >= 1:
        raise ValueError("components exceed the baseline")
    return 1.0 / (1.0 - removed)


def local_speedup_required(share: float, target_speedup: float) -> float | None:
    if not 0 < share < 1 or target_speedup <= 1:
        raise ValueError("invalid requirement")
    denominator = (1.0 / target_speedup) - (1.0 - share)
    return None if denominator <= 0 else share / denominator


def build_report() -> dict:
    inversion = (0.02957, 5.2)
    recurrent = (0.04840, 1.86)
    full_megagdn = (0.10870, 1.087)
    combined = disjoint_speedup([inversion, recurrent])
    perfect = disjoint_speedup(
        [(inversion[0], float("inf")), (recurrent[0], float("inf"))]
    )
    return {
        "schema": "qwen36-ascend-paper-opportunity-audit/v1",
        "claim": "diagnostic Amdahl screen only; not an end-to-end benchmark",
        "best_non_overlapping_observed_components": {
            "inversion": {
                "share": inversion[0],
                "local_speedup": inversion[1],
                "implied_speedup": amdahl_speedup(*inversion),
            },
            "recurrent_state_decode": {
                "share": recurrent[0],
                "local_speedup": recurrent[1],
                "implied_speedup": amdahl_speedup(*recurrent),
            },
            "combined": {
                "implied_speedup": combined,
                "gain_pct": (combined - 1.0) * 100,
            },
            "perfect_elimination_upper_bound": {
                "implied_speedup": perfect,
                "gain_pct": (perfect - 1.0) * 100,
            },
        },
        "official_six_stage_megagdn": {
            "share": full_megagdn[0],
            "measured_local_speedup": full_megagdn[1],
            "implied_speedup": amdahl_speedup(*full_megagdn),
            "local_speedup_required_for_1_10x": local_speedup_required(
                full_megagdn[0], 1.10
            ),
        },
        "decision": "fresh dense profiling required; do not add overlapping paper claims",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("refusing to overwrite an existing audit")
    args.output.write_text(json.dumps(build_report(), indent=2) + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Evaluate immutable Qwen3.5 MMAR core-count microbenchmark artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SHAPES = ((1, 1536, 5120), (1, 4352, 5120))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--minimum-speedup", type=float, default=1.02)
    return parser.parse_args()


def load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def cells_by_shape(result: dict[str, Any]) -> dict[tuple[int, int, int], dict[str, Any]]:
    return {
        (int(cell["m"]), int(cell["k"]), int(cell["n"])): cell
        for cell in result["cells"]
    }


def main() -> int:
    args = parse_args()
    baseline_path = args.root / "core-default.json"
    baseline = cells_by_shape(load(baseline_path))
    if set(baseline) != set(SHAPES):
        raise RuntimeError(f"unexpected baseline shapes: {sorted(baseline)}")
    if not all(bool(baseline[shape]["correctness"]["allclose"]) for shape in SHAPES):
        raise RuntimeError("default custom-OPP baseline failed correctness")

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
        correct = all(
            bool(cells[shape]["correctness"]["allclose"]) for shape in SHAPES
        )
        passes = correct and all(
            speedup >= args.minimum_speedup for speedup in speedups.values()
        )
        candidates.append(
            {
                "label": result.get("label"),
                "path": str(path),
                "correct": correct,
                "speedups_vs_default": speedups,
                "minimum_shape_speedup": min(speedups.values()),
                "passes_e2e_gate": passes,
            }
        )

    decision = {
        "schema": "qwen35-mmar-core-count-decision/v1",
        "baseline": str(baseline_path),
        "minimum_speedup": args.minimum_speedup,
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

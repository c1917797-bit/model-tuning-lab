#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import pathlib
from collections import defaultdict
from typing import Any


def _duration(row: dict[str, str]) -> float:
    return float(row["Task Duration(us)"].strip())


def _rank(path: pathlib.Path) -> int:
    for part in path.parts:
        if part.startswith("rank") and part[4:].isdigit():
            return int(part[4:])
    raise ValueError(f"cannot determine rank from {path}")


def _sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def analyze(
    profile_root: str,
    *,
    decode_steps: int,
    max_calls_per_step: int = 256,
    top: int = 40,
) -> dict[str, Any]:
    if decode_steps <= 0:
        raise ValueError("decode_steps must be positive")
    root = pathlib.Path(profile_root)
    paths = sorted(root.glob("rank*/PROF*/mindstudio_profiler_output/op_summary_*.csv"))
    if not paths:
        raise FileNotFoundError(f"no op_summary CSV files under {root}")

    rank_rows: dict[int, dict[tuple[str, str, str], list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    rank_paths: dict[int, pathlib.Path] = {}
    for path in paths:
        rank = _rank(path)
        if rank in rank_paths:
            raise ValueError(f"multiple op_summary CSV files for rank{rank}")
        rank_paths[rank] = path
        with path.open(newline="") as handle:
            for row in csv.DictReader(handle):
                key = (
                    row.get("Op Name", ""),
                    row.get("Input Shapes", ""),
                    row.get("Task Type", ""),
                )
                rank_rows[rank][key].append(_duration(row))

    ranks: list[dict[str, Any]] = []
    cross_rank: dict[tuple[str, str, str], dict[int, float]] = defaultdict(dict)
    for rank in sorted(rank_rows):
        groups: list[dict[str, Any]] = []
        for key, durations in rank_rows[rank].items():
            count = len(durations)
            if count % decode_steps:
                continue
            calls_per_step = count // decode_steps
            if calls_per_step < 1 or calls_per_step > max_calls_per_step:
                continue
            total_us = sum(durations)
            us_per_step = total_us / decode_steps
            op, shapes, task_type = key
            item = {
                "op": op,
                "input_shapes": shapes,
                "task_type": task_type,
                "count": count,
                "calls_per_step": calls_per_step,
                "mean_call_us": total_us / count,
                "us_per_step": us_per_step,
                "overlap_warning": (
                    "AICPU/host duration may enclose or overlap device kernels"
                    if "AICPU" in op.upper() or "CPU" in task_type.upper()
                    else None
                ),
            }
            groups.append(item)
            cross_rank[key][rank] = us_per_step
        groups.sort(key=lambda item: item["us_per_step"], reverse=True)
        ranks.append(
            {
                "rank": rank,
                "path": str(rank_paths[rank]),
                "sha256": _sha256(rank_paths[rank]),
                "eligible_groups": len(groups),
                "top_groups": groups[:top],
            }
        )

    common: list[dict[str, Any]] = []
    expected_ranks = set(rank_rows)
    for key, values in cross_rank.items():
        if set(values) != expected_ranks:
            continue
        op, shapes, task_type = key
        common.append(
            {
                "op": op,
                "input_shapes": shapes,
                "task_type": task_type,
                "min_us_per_step": min(values.values()),
                "max_us_per_step": max(values.values()),
                "per_rank_us_per_step": {
                    f"rank{rank}": value for rank, value in sorted(values.items())
                },
                "overlap_warning": (
                    "AICPU/host duration may enclose or overlap device kernels"
                    if "AICPU" in op.upper() or "CPU" in task_type.upper()
                    else None
                ),
            }
        )
    common.sort(key=lambda item: item["max_us_per_step"], reverse=True)

    return {
        "schema": "qwen35-decode-op-groups/v1",
        "profile_root": str(root),
        "decode_steps": decode_steps,
        "selection_rule": (
            "Keep groups whose occurrence count is an integer 1.."
            f"{max_calls_per_step} calls per each of {decode_steps} decode steps."
        ),
        "claim_boundary": (
            "Diagnostic grouped profiler durations only. Groups can overlap; their "
            "durations must not be summed into end-to-end TPOT or claimed savings."
        ),
        "ranks": ranks,
        "common_top_groups": common[:top],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("profile_root")
    parser.add_argument("--decode-steps", type=int, required=True)
    parser.add_argument("--max-calls-per-step", type=int, default=256)
    parser.add_argument("--top", type=int, default=40)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = analyze(
        args.profile_root,
        decode_steps=args.decode_steps,
        max_calls_per_step=args.max_calls_per_step,
        top=args.top,
    )
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        pathlib.Path(args.output).write_text(payload)
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()


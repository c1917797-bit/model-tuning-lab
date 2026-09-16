#!/usr/bin/env python3
"""Independently audit GQA-group partition evidence in a selector manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dynamic_programming_optimum(
    weights: list[int],
    *,
    bins: int,
    groups_per_bin: int,
) -> int:
    """Return the exact min-max load using an unlabeled-bin state space."""

    if len(weights) != bins * groups_per_bin:
        raise ValueError("weights do not fill equal-cardinality bins")
    states: set[tuple[tuple[int, int], ...]] = {
        tuple((0, 0) for _ in range(bins))
    }
    for weight in weights:
        next_states: set[tuple[tuple[int, int], ...]] = set()
        for state in states:
            seen: set[tuple[int, int]] = set()
            for index, (count, load) in enumerate(state):
                if (count, load) in seen:
                    continue
                seen.add((count, load))
                if count >= groups_per_bin:
                    continue
                updated = list(state)
                updated[index] = (count + 1, load + weight)
                next_states.add(tuple(sorted(updated)))
        states = next_states
        if not states:
            raise AssertionError("partition DP exhausted all states")

    complete = [
        state
        for state in states
        if all(count == groups_per_bin for count, _ in state)
    ]
    if not complete:
        raise AssertionError("partition DP found no complete state")
    return min(max(load for _, load in state) for state in complete)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")

    source = json.loads(args.manifest.read_text(encoding="utf-8"))
    if source.get("schema") != "mst.dasc.selector-manifest/v3":
        raise ValueError("expected selector manifest schema v3")
    if not source.get("ok"):
        raise ValueError("source selector manifest is not successful")

    bins = int(source["tp_size"])
    key_heads = int(source["linear_num_key_heads"])
    value_heads_per_group = int(source["value_heads_per_gqa_group"])
    groups_per_bin = int(source["gqa_groups_per_rank"])
    if key_heads != bins * groups_per_bin:
        raise ValueError("manifest GQA cardinalities disagree")

    total_retained = 0
    total_group_padded = 0
    rows = []
    for row in source["layers"]:
        counts = [int(value) for value in row["gqa_group_counts"]]
        if len(counts) != key_heads:
            raise ValueError(f"layer {row['layer']} has wrong group count")
        if any(value < 0 or value > value_heads_per_group for value in counts):
            raise ValueError(f"layer {row['layer']} has invalid group weight")

        assignments = row["gqa_group_assignment"]
        if len(assignments) != bins:
            raise ValueError(f"layer {row['layer']} has wrong rank count")
        if any(len(rank) != groups_per_bin for rank in assignments):
            raise ValueError(f"layer {row['layer']} violates rank cardinality")
        flattened = sorted(group for rank in assignments for group in rank)
        if flattened != list(range(key_heads)):
            raise ValueError(f"layer {row['layer']} loses or duplicates a group")

        loads = [
            sum(counts[group] for group in assignment)
            for assignment in assignments
        ]
        optimum = dynamic_programming_optimum(
            counts,
            bins=bins,
            groups_per_bin=groups_per_bin,
        )
        retained = sum(counts)
        padded = optimum * bins
        layer_ok = bool(
            loads == row["gqa_group_rank_loads"]
            and max(loads) == int(row["gqa_group_common_count"])
            and optimum == int(row["gqa_group_common_count"])
            and retained == int(row["manifest_retained"])
            and padded == int(row["gqa_group_padded_heads"])
            and padded - retained
            == int(row["gqa_group_padding_overhead_heads"])
        )
        if not layer_ok:
            raise ValueError(f"layer {row['layer']} partition evidence disagrees")

        total_retained += retained
        total_group_padded += padded
        rows.append(
            {
                "layer": int(row["layer"]),
                "dp_optimum": optimum,
                "assignment_loads": loads,
                "ok": True,
            }
        )

    total_heads = sum(int(row["heads"]) for row in source["layers"])
    aggregate_ok = bool(
        len(rows) == int(source["layer_count"])
        and total_retained == int(source["retained_heads"])
        and total_group_padded
        == int(source["gqa_group_balanced_padded_heads"])
        and total_group_padded - total_retained
        == int(source["gqa_group_balanced_padding_overhead_heads"])
        and total_heads - total_group_padded
        == int(source["gqa_group_balanced_removed_heads"])
    )
    if not aggregate_ok:
        raise ValueError("aggregate partition evidence disagrees")

    result = {
        "schema": "mst.dasc.selector-group-partition-audit/v1",
        "ok": True,
        "source_manifest": str(args.manifest),
        "source_manifest_sha256": sha256(args.manifest),
        "algorithm": "independent unlabeled-bin dynamic programming",
        "layer_count": len(rows),
        "tp_size": bins,
        "gqa_groups": key_heads,
        "groups_per_rank": groups_per_bin,
        "retained_heads": total_retained,
        "gqa_group_balanced_padded_heads": total_group_padded,
        "gqa_group_balanced_padding_overhead_heads": (
            total_group_padded - total_retained
        ),
        "gqa_group_balanced_removed_heads": total_heads - total_group_padded,
        "layers": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

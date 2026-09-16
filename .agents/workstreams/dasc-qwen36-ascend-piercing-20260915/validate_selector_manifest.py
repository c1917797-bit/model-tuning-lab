#!/usr/bin/env python3
"""Cross-check the plugin selector against raw Qwen3.6 checkpoint weights."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace

import torch
from safetensors import safe_open

from dasc_vllm_ascend.selector import head_horizons, retained_head_indices


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scalar_horizons(
    a_log: torch.Tensor,
    dt_bias: torch.Tensor,
    *,
    representative_a: float,
    epsilon: float,
) -> list[float]:
    return [
        math.log(epsilon)
        / (
            -math.exp(float(a_value))
            * math.log1p(math.exp(float(dt_value) + representative_a))
        )
        for a_value, dt_value in zip(a_log.float(), dt_bias.float())
    ]


def optimal_group_partition(
    weights: list[int],
    *,
    bins: int,
    groups_per_bin: int,
) -> tuple[int, list[list[int]]]:
    """Minimize maximum retained-head load while keeping whole GQA groups."""

    if bins <= 0 or groups_per_bin <= 0:
        raise ValueError("bins and groups_per_bin must be positive")
    if len(weights) != bins * groups_per_bin:
        raise ValueError("weights do not fill the requested equal-size bins")
    if any(weight < 0 for weight in weights):
        raise ValueError("group weights must be non-negative")

    order = sorted(range(len(weights)), key=lambda index: (-weights[index], index))
    lower_bound = max(
        max(weights, default=0),
        math.ceil(sum(weights) / bins),
    )

    for limit in range(lower_bound, sum(weights) + 1):
        loads = [0] * bins
        assignments: list[list[int]] = [[] for _ in range(bins)]

        def search(position: int) -> bool:
            if position == len(order):
                return all(
                    len(assignment) == groups_per_bin
                    for assignment in assignments
                )

            remaining_weight = sum(weights[index] for index in order[position:])
            remaining_capacity = sum(limit - load for load in loads)
            if remaining_weight > remaining_capacity:
                return False

            group = order[position]
            weight = weights[group]
            seen_bin_states: set[tuple[int, int]] = set()
            for bin_index in range(bins):
                state = (loads[bin_index], len(assignments[bin_index]))
                if state in seen_bin_states:
                    continue
                seen_bin_states.add(state)
                if len(assignments[bin_index]) >= groups_per_bin:
                    continue
                if loads[bin_index] + weight > limit:
                    continue

                loads[bin_index] += weight
                assignments[bin_index].append(group)
                if search(position + 1):
                    return True
                assignments[bin_index].pop()
                loads[bin_index] -= weight
            return False

        if search(0):
            normalized = sorted(
                (sorted(assignment) for assignment in assignments),
                key=lambda assignment: tuple(assignment),
            )
            return limit, normalized

    raise AssertionError("no equal-size group partition found")


def check_partition_solver() -> None:
    cases = [
        ([0] * 16, 0),
        ([3] * 16, 12),
        ([3] * 8 + [0] * 8, 6),
        ([3] * 5 + [0] * 11, 6),
        ([3, 2, 1, 0] * 4, 6),
        ([3] * 7 + [2] * 9, 10),
    ]
    for weights, expected in cases:
        optimum, assignments = optimal_group_partition(
            weights,
            bins=4,
            groups_per_bin=4,
        )
        if optimum != expected:
            raise AssertionError(
                f"partition self-test expected {expected}, got {optimum}"
            )
        flattened = sorted(group for rank in assignments for group in rank)
        if flattened != list(range(16)):
            raise AssertionError("partition self-test lost or duplicated a group")
        if any(len(rank) != 4 for rank in assignments):
            raise AssertionError("partition self-test violated rank cardinality")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tp-size", type=int, default=4)
    parser.add_argument("--w-max", type=int, default=64)
    parser.add_argument("--epsilon", type=float, default=0.001)
    parser.add_argument("--representative-a", type=float, default=-0.3)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    check_partition_solver()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")
    if args.tp_size <= 0:
        raise ValueError("tp-size must be positive")

    index_path = args.model_dir / "model.safetensors.index.json"
    model_config_path = args.model_dir / "config.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    model_config = json.loads(model_config_path.read_text(encoding="utf-8"))
    linear_config = model_config.get("text_config", model_config)
    num_key_heads = int(linear_config["linear_num_key_heads"])
    num_value_heads = int(linear_config["linear_num_value_heads"])
    if num_value_heads % num_key_heads:
        raise ValueError("linear value heads are not divisible by key heads")
    if num_key_heads % args.tp_size:
        raise ValueError("linear key heads are not divisible by TP size")
    value_heads_per_group = num_value_heads // num_key_heads
    groups_per_rank = num_key_heads // args.tp_size
    weight_map = index["weight_map"]
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    config = SimpleNamespace(
        representative_a=args.representative_a,
        epsilon=args.epsilon,
        w_max=args.w_max,
    )

    tensor_names: dict[int, tuple[str, str]] = {}
    needed_by_file: dict[str, set[str]] = {}
    for row in manifest["layers"]:
        layer = int(row["layer"])
        prefix = f"model.language_model.layers.{layer}.linear_attn"
        names = (f"{prefix}.A_log", f"{prefix}.dt_bias")
        tensor_names[layer] = names
        for name in names:
            filename = weight_map[name]
            needed_by_file.setdefault(filename, set()).add(name)

    tensors: dict[str, torch.Tensor] = {}
    for filename, names in sorted(needed_by_file.items()):
        with safe_open(
            args.model_dir / filename, framework="pt", device="cpu"
        ) as handle:
            for name in sorted(names):
                tensors[name] = handle.get_tensor(name)

    rows = []
    all_ok = True
    for manifest_row in manifest["layers"]:
        layer = int(manifest_row["layer"])
        a_name, dt_name = tensor_names[layer]
        a_log = tensors[a_name].reshape(-1)
        dt_bias = tensors[dt_name].reshape(-1)
        if a_log.shape != dt_bias.shape:
            raise ValueError(f"layer {layer} decay tensors differ in shape")
        if a_log.numel() % args.tp_size:
            raise ValueError(f"layer {layer} cannot shard across TP{args.tp_size}")
        if a_log.numel() != num_value_heads:
            raise ValueError(
                f"layer {layer} has {a_log.numel()} decay heads; "
                f"config declares {num_value_heads}"
            )

        module = SimpleNamespace(A_log=a_log, dt_bias=dt_bias)
        plugin_horizon = head_horizons(module, config).cpu()
        reference_horizon = torch.tensor(
            scalar_horizons(
                a_log,
                dt_bias,
                representative_a=args.representative_a,
                epsilon=args.epsilon,
            ),
            dtype=torch.float32,
        )
        reference_indices = (
            (reference_horizon > args.w_max)
            .nonzero(as_tuple=False)
            .flatten()
        )
        plugin_indices = retained_head_indices(module, config).cpu()
        manifest_count = int(
            manifest_row["retained_heads_gt_threshold"][str(args.w_max)]
        )

        local_counts = []
        local_exact = []
        shard_width = a_log.numel() // args.tp_size
        for rank in range(args.tp_size):
            start = rank * shard_width
            stop = start + shard_width
            shard = SimpleNamespace(
                A_log=a_log[start:stop],
                dt_bias=dt_bias[start:stop],
            )
            selected = retained_head_indices(shard, config).cpu()
            expected = (
                (reference_horizon[start:stop] > args.w_max)
                .nonzero(as_tuple=False)
                .flatten()
            )
            local_counts.append(int(selected.numel()))
            local_exact.append(bool(torch.equal(selected, expected)))

        common_count = max(local_counts)
        padded_exact = []
        for rank in range(args.tp_size):
            start = rank * shard_width
            stop = start + shard_width
            shard = SimpleNamespace(
                A_log=a_log[start:stop],
                dt_bias=dt_bias[start:stop],
            )
            padded = retained_head_indices(
                shard, config, target_count=common_count
            ).cpu()
            threshold = (
                (reference_horizon[start:stop] > args.w_max)
                .nonzero(as_tuple=False)
                .flatten()
            )
            padded_exact.append(
                bool(
                    padded.numel() == common_count
                    and set(threshold.tolist()).issubset(
                        set(padded.tolist())
                    )
                )
            )

        retained_mask = reference_horizon > args.w_max
        group_counts = (
            retained_mask.reshape(num_key_heads, value_heads_per_group)
            .sum(dim=1)
            .to(torch.int64)
            .tolist()
        )
        group_optimum, group_assignment = optimal_group_partition(
            group_counts,
            bins=args.tp_size,
            groups_per_bin=groups_per_rank,
        )
        group_rank_loads = [
            sum(group_counts[group] for group in assignment)
            for assignment in group_assignment
        ]
        if max(group_rank_loads) != group_optimum:
            raise AssertionError("partition assignment does not match optimum")

        layer_ok = bool(
            torch.allclose(
                plugin_horizon,
                reference_horizon,
                rtol=2e-6,
                atol=2e-5,
            )
            and torch.equal(plugin_indices, reference_indices)
            and plugin_indices.numel() == manifest_count
            and all(local_exact)
            and all(padded_exact)
        )
        all_ok = all_ok and layer_ok
        rows.append(
            {
                "layer": layer,
                "heads": int(a_log.numel()),
                "manifest_retained": manifest_count,
                "plugin_retained": int(plugin_indices.numel()),
                "local_counts": local_counts,
                "tp_common_count": common_count,
                "tp_padded_heads": common_count * args.tp_size,
                "tp_padding_overhead_heads": (
                    common_count * args.tp_size - manifest_count
                ),
                "gqa_group_counts": group_counts,
                "gqa_group_assignment": group_assignment,
                "gqa_group_rank_loads": group_rank_loads,
                "gqa_group_common_count": group_optimum,
                "gqa_group_padded_heads": group_optimum * args.tp_size,
                "gqa_group_padding_overhead_heads": (
                    group_optimum * args.tp_size - manifest_count
                ),
                "ok": layer_ok,
            }
        )

    threshold_retained = sum(row["plugin_retained"] for row in rows)
    tp_padded = sum(row["tp_padded_heads"] for row in rows)
    balanced_padded = sum(
        math.ceil(row["plugin_retained"] / args.tp_size) * args.tp_size
        for row in rows
    )
    group_balanced_padded = sum(
        row["gqa_group_padded_heads"] for row in rows
    )
    result = {
        "schema": "mst.dasc.selector-manifest/v3",
        "ok": all_ok,
        "model_dir": str(args.model_dir),
        "index_sha256": sha256(index_path),
        "model_config_sha256": sha256(model_config_path),
        "manifest": str(args.manifest),
        "manifest_sha256": sha256(args.manifest),
        "epsilon": args.epsilon,
        "representative_a": args.representative_a,
        "w_max": args.w_max,
        "tp_size": args.tp_size,
        "linear_num_key_heads": num_key_heads,
        "linear_num_value_heads": num_value_heads,
        "value_heads_per_gqa_group": value_heads_per_group,
        "gqa_groups_per_rank": groups_per_rank,
        "partition_solver_self_tests": 6,
        "layer_count": len(rows),
        "retained_heads": threshold_retained,
        "tp_padded_heads": tp_padded,
        "tp_padding_overhead_heads": tp_padded - threshold_retained,
        "ideal_balanced_padded_heads": balanced_padded,
        "ideal_balanced_padding_overhead_heads": (
            balanced_padded - threshold_retained
        ),
        "gqa_group_balanced_padded_heads": group_balanced_padded,
        "gqa_group_balanced_padding_overhead_heads": (
            group_balanced_padded - threshold_retained
        ),
        "current_removed_heads": (
            len(rows) * rows[0]["heads"] - tp_padded
        ),
        "ideal_balanced_removed_heads": (
            len(rows) * rows[0]["heads"] - balanced_padded
        ),
        "gqa_group_balanced_removed_heads": (
            len(rows) * rows[0]["heads"] - group_balanced_padded
        ),
        "layers": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if not all_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

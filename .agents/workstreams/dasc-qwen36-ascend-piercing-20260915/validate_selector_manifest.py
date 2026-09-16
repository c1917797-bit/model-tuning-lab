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
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")
    if args.tp_size <= 0:
        raise ValueError("tp-size must be positive")

    index_path = args.model_dir / "model.safetensors.index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
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
                "ok": layer_ok,
            }
        )

    result = {
        "schema": "mst.dasc.selector-manifest/v1",
        "ok": all_ok,
        "model_dir": str(args.model_dir),
        "index_sha256": sha256(index_path),
        "manifest": str(args.manifest),
        "manifest_sha256": sha256(args.manifest),
        "epsilon": args.epsilon,
        "representative_a": args.representative_a,
        "w_max": args.w_max,
        "tp_size": args.tp_size,
        "layer_count": len(rows),
        "retained_heads": sum(row["plugin_retained"] for row in rows),
        "tp_padded_heads": sum(row["tp_padded_heads"] for row in rows),
        "tp_padding_overhead_heads": sum(
            row["tp_padding_overhead_heads"] for row in rows
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

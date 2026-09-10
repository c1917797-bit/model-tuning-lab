#!/usr/bin/env python3
"""Validate adapter decoders against one real NVFP4 and one real FP8 row."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import torch
from safetensors import safe_open

from nvfp4_codec import dequantize_nvfp4
from qwen38_nvfp4_ascend.adapter import (
    decode_fp8_weight,
    decode_nvfp4_weight,
)


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _first_layer(layers: dict, algorithm: str) -> str:
    for name, spec in layers.items():
        if spec.get("quant_algo") == algorithm:
            return name
    raise RuntimeError(f"checkpoint has no {algorithm} layer")


def validate(model_dir: str | Path) -> dict[str, object]:
    root = Path(model_dir)
    quant = _load_json(root / "hf_quant_config.json")["quantization"]
    layers = quant["quantized_layers"]
    weight_map = _load_json(root / "model.safetensors.index.json")["weight_map"]
    result: dict[str, object] = {}

    nv_name = _first_layer(layers, "NVFP4")
    nv_weight = f"{nv_name}.weight"
    nv_scale = f"{nv_name}.weight_scale"
    nv_scale_2 = f"{nv_name}.weight_scale_2"
    nv_shard = root / weight_map[nv_weight]
    if len({weight_map[nv_weight], weight_map[nv_scale], weight_map[nv_scale_2]}) != 1:
        raise RuntimeError("NVFP4 sample tensors are not co-located")
    with safe_open(nv_shard, framework="pt", device="cpu") as handle:
        packed = handle.get_slice(nv_weight)[0:1]
        local = handle.get_slice(nv_scale)[0:1]
        global_scale = handle.get_tensor(nv_scale_2).reshape(1)
    actual_nv = decode_nvfp4_weight(
        packed,
        local,
        global_scale,
        [1],
        output_dtype=torch.float32,
        rows_per_chunk=1,
    ).reshape(-1)
    expected_nv = torch.tensor(
        dequantize_nvfp4(
            packed.reshape(-1).numpy().tobytes(),
            local.reshape(-1).float().tolist(),
            global_scale.item(),
        ),
        dtype=torch.float32,
    )
    if not torch.equal(actual_nv, expected_nv):
        raise AssertionError("real NVFP4 row does not match independent codec")
    result["nvfp4"] = {
        "tensor": nv_weight,
        "shard": nv_shard.name,
        "decoded_values": actual_nv.numel(),
        "exact_match": True,
        "sha256": hashlib.sha256(actual_nv.numpy().tobytes()).hexdigest(),
    }

    fp8_name = _first_layer(layers, "FP8")
    fp8_weight = f"{fp8_name}.weight"
    fp8_scale = f"{fp8_name}.weight_scale"
    fp8_shard = root / weight_map[fp8_weight]
    if weight_map[fp8_weight] != weight_map[fp8_scale]:
        raise RuntimeError("FP8 sample tensors are not co-located")
    with safe_open(fp8_shard, framework="pt", device="cpu") as handle:
        weight = handle.get_slice(fp8_weight)[0:1]
        scale = handle.get_tensor(fp8_scale).reshape(1)
    actual_fp8 = decode_fp8_weight(
        weight,
        scale,
        [1],
        output_dtype=torch.float32,
        rows_per_chunk=1,
    ).reshape(-1)
    expected_fp8 = weight.reshape(-1).float() * scale.item()
    if not torch.equal(actual_fp8, expected_fp8):
        raise AssertionError("real FP8 row does not match per-tensor decode")
    result["fp8"] = {
        "tensor": fp8_weight,
        "shard": fp8_shard.name,
        "decoded_values": actual_fp8.numel(),
        "exact_match": True,
        "sha256": hashlib.sha256(actual_fp8.numpy().tobytes()).hexdigest(),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_dir")
    args = parser.parse_args()
    print(json.dumps(validate(args.model_dir), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

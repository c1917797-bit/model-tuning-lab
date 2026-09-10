#!/usr/bin/env python3
"""Cross-check one real checkpoint row against NVIDIA ModelOpt semantics."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import torch
from safetensors import safe_open

from nvfp4_codec import dequantize_nvfp4


E2M1_VALUES = torch.tensor(
    [0, 0.5, 1, 1.5, 2, 3, 4, 6, 0, -0.5, -1, -1.5, -2, -3, -4, -6],
    dtype=torch.float32,
)
MODELOPT_REFERENCE_COMMIT = "079078de9d3cd26fa5baafdb754bba29dde24f7d"


def validate_row(model_dir: str | Path, tensor_name: str, row: int) -> dict[str, object]:
    root = Path(model_dir)
    index = json.loads((root / "model.safetensors.index.json").read_text(encoding="utf-8"))
    shard_name = index["weight_map"][tensor_name]
    scale_name = tensor_name.removesuffix(".weight") + ".weight_scale"
    scale_2_name = tensor_name.removesuffix(".weight") + ".weight_scale_2"
    if index["weight_map"].get(scale_name) != shard_name:
        raise RuntimeError("weight and local scale are not in the same shard")
    if index["weight_map"].get(scale_2_name) != shard_name:
        raise RuntimeError("weight and global scale are not in the same shard")
    shard_path = root / shard_name
    if not shard_path.is_file():
        raise FileNotFoundError(shard_path)

    with safe_open(shard_path, framework="pt", device="cpu") as handle:
        packed = handle.get_slice(tensor_name)[row : row + 1].reshape(-1)
        local_scales = handle.get_slice(scale_name)[row : row + 1].reshape(-1)
        global_scale = handle.get_tensor(scale_2_name).float().item()

    packed_bytes = packed.numpy().tobytes()
    actual = torch.tensor(
        dequantize_nvfp4(
            packed_bytes,
            local_scales.float().tolist(),
            global_scale,
        ),
        dtype=torch.float32,
    )

    # Independent transcription of NVIDIA ModelOpt NVFP4QTensor.dequantize.
    codes = torch.empty(packed.numel() * 2, dtype=torch.uint8)
    codes[1::2] = packed >> 4
    codes[0::2] = packed & 0x0F
    expected = (
        E2M1_VALUES[codes.long()]
        * local_scales.float().repeat_interleave(16)
        * global_scale
    )
    max_abs_error = torch.max(torch.abs(actual - expected)).item()
    if not torch.equal(actual, expected):
        raise AssertionError(f"real tensor decode mismatch, max_abs_error={max_abs_error}")

    return {
        "modelopt_reference_commit": MODELOPT_REFERENCE_COMMIT,
        "tensor": tensor_name,
        "row": row,
        "shard": shard_name,
        "packed_values": packed.numel(),
        "decoded_values": actual.numel(),
        "local_scales": local_scales.numel(),
        "global_scale": global_scale,
        "packed_row_sha256": hashlib.sha256(packed_bytes).hexdigest(),
        "max_abs_error": max_abs_error,
        "exact_match": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_dir")
    parser.add_argument("--tensor", default="lm_head.weight")
    parser.add_argument("--row", type=int, default=0)
    args = parser.parse_args()
    print(json.dumps(validate_row(args.model_dir, args.tensor, args.row), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


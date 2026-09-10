#!/usr/bin/env python3
"""Fail-closed inspection for a ModelOpt mixed NVFP4 checkpoint."""

from __future__ import annotations

import argparse
import json
import struct
from collections import Counter
from pathlib import Path
from typing import Any


class CheckpointContractError(RuntimeError):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise CheckpointContractError(f"missing required file: {path.name}")
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise CheckpointContractError(f"{path.name} must contain a JSON object")
    return value


def _read_safetensors_header(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        prefix = handle.read(8)
        if len(prefix) != 8:
            raise CheckpointContractError(f"invalid safetensors header: {path.name}")
        header_size = struct.unpack("<Q", prefix)[0]
        if header_size > 64 * 1024 * 1024:
            raise CheckpointContractError(f"unreasonable safetensors header: {path.name}")
        raw_header = handle.read(header_size)
    try:
        header = json.loads(raw_header)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CheckpointContractError(
            f"invalid safetensors JSON header: {path.name}"
        ) from error
    if not isinstance(header, dict):
        raise CheckpointContractError(f"invalid safetensors header object: {path.name}")
    header.pop("__metadata__", None)
    return header


def inspect_checkpoint(model_dir: str | Path) -> dict[str, Any]:
    root = Path(model_dir)
    config = _read_json(root / "config.json")
    quant = _read_json(root / "hf_quant_config.json")
    index = _read_json(root / "model.safetensors.index.json")

    quant_method = config.get("quantization_config", {}).get("quant_method")
    if quant_method != "modelopt":
        raise CheckpointContractError(
            f"expected config quant_method=modelopt, got {quant_method!r}"
        )

    quantization = quant.get("quantization")
    if not isinstance(quantization, dict):
        raise CheckpointContractError("hf_quant_config.json lacks quantization object")
    if quantization.get("quant_algo") != "MIXED_PRECISION":
        raise CheckpointContractError("expected MIXED_PRECISION quantization")

    layers = quantization.get("quantized_layers")
    if not isinstance(layers, dict) or not layers:
        raise CheckpointContractError("quantized_layers must be a non-empty object")
    algorithms = Counter(
        spec.get("quant_algo") for spec in layers.values() if isinstance(spec, dict)
    )
    nvfp4_group_sizes = sorted(
        {
            spec.get("group_size")
            for spec in layers.values()
            if isinstance(spec, dict) and spec.get("quant_algo") == "NVFP4"
        }
    )
    if not algorithms.get("NVFP4"):
        raise CheckpointContractError("checkpoint declares no NVFP4 layer")
    if nvfp4_group_sizes != [16]:
        raise CheckpointContractError(
            f"all NVFP4 layers must use group_size=16, got {nvfp4_group_sizes}"
        )

    weight_map = index.get("weight_map")
    if not isinstance(weight_map, dict) or not weight_map:
        raise CheckpointContractError("weight index has no weight_map")
    referenced_shards = sorted(set(weight_map.values()))
    missing_shards = [name for name in referenced_shards if not (root / name).is_file()]

    tensor_headers: dict[str, Any] = {}
    for shard_name in referenced_shards:
        shard_path = root / shard_name
        if shard_path.is_file():
            tensor_headers.update(_read_safetensors_header(shard_path))

    nvfp4_tensor_contract_errors: list[str] = []
    validated_nvfp4_layers = 0
    for layer_name, spec in layers.items():
        if not isinstance(spec, dict) or spec.get("quant_algo") != "NVFP4":
            continue
        names = {
            "weight": f"{layer_name}.weight",
            "scale": f"{layer_name}.weight_scale",
            "scale_2": f"{layer_name}.weight_scale_2",
        }
        layer_shards = {weight_map.get(name) for name in names.values()}
        if None in layer_shards or any(shard in missing_shards for shard in layer_shards):
            continue
        entries = {kind: tensor_headers.get(name) for kind, name in names.items()}
        if any(entry is None for entry in entries.values()):
            nvfp4_tensor_contract_errors.append(f"{layer_name}: tensor missing from shard header")
            continue
        weight = entries["weight"]
        scale = entries["scale"]
        scale_2 = entries["scale_2"]
        if weight.get("dtype") != "U8":
            nvfp4_tensor_contract_errors.append(f"{layer_name}: weight dtype is not U8")
        if scale.get("dtype") != "F8_E4M3":
            nvfp4_tensor_contract_errors.append(f"{layer_name}: local scale is not F8_E4M3")
        if scale_2.get("dtype") != "F32" or scale_2.get("shape") != []:
            nvfp4_tensor_contract_errors.append(f"{layer_name}: global scale is not scalar F32")
        weight_shape = weight.get("shape")
        scale_shape = scale.get("shape")
        if (
            not isinstance(weight_shape, list)
            or not isinstance(scale_shape, list)
            or len(weight_shape) != 2
            or len(scale_shape) != 2
            or weight_shape[0] != scale_shape[0]
            or weight_shape[1] != scale_shape[1] * 8
        ):
            nvfp4_tensor_contract_errors.append(
                f"{layer_name}: packed weight/local-scale shapes violate group16"
            )
        validated_nvfp4_layers += 1
    if not missing_shards and validated_nvfp4_layers != algorithms["NVFP4"]:
        nvfp4_tensor_contract_errors.append(
            f"validated {validated_nvfp4_layers} of {algorithms['NVFP4']} NVFP4 layers"
        )
    if not missing_shards and nvfp4_tensor_contract_errors:
        raise CheckpointContractError(
            "NVFP4 tensor contract failed: " + "; ".join(nvfp4_tensor_contract_errors[:8])
        )

    return {
        "model_dir": str(root.resolve()),
        "quant_method": quant_method,
        "quant_algo": quantization["quant_algo"],
        "producer": quant.get("producer"),
        "quantized_layer_count": len(layers),
        "algorithms": dict(sorted(algorithms.items())),
        "nvfp4_group_sizes": nvfp4_group_sizes,
        "excluded_modules": quantization.get("exclude_modules", []),
        "tensor_count": len(weight_map),
        "referenced_shard_count": len(referenced_shards),
        "missing_shards": missing_shards,
        "validated_nvfp4_layers": validated_nvfp4_layers,
        "nvfp4_tensor_contract_errors": nvfp4_tensor_contract_errors,
        "complete": not missing_shards,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_dir")
    args = parser.parse_args()
    try:
        result = inspect_checkpoint(args.model_dir)
    except CheckpointContractError as error:
        print(json.dumps({"complete": False, "contract_error": str(error)}, indent=2))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["complete"] else 3


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Fail-closed inspection for a ModelOpt mixed NVFP4 checkpoint."""

from __future__ import annotations

import argparse
import json
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


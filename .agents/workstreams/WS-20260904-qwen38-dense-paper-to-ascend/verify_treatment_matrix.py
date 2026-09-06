#!/usr/bin/env python3
"""Verify model inventories, native patch identity, and G1-G4 orthogonality."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_GROUPS = {
    "G1": (False, False),
    "G2": (True, False),
    "G3": (False, True),
    "G4": (True, True),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_object(path: Path, label: str, errors: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{label} unreadable: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{label} must be a JSON object")
        return {}
    return value


def verify_model(entry: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    model_id = str(entry.get("id", "<missing-id>"))
    root = Path(str(entry.get("path", "")))
    config_path = root / "config.json"
    index_path = root / "model.safetensors.index.json"
    config = load_object(config_path, f"{model_id} config", errors)
    text_config = config.get("text_config", config)
    if not isinstance(text_config, dict):
        errors.append(f"{model_id} text_config must be an object")
        text_config = {}

    actual = {
        "text_architecture": text_config.get("model_type"),
        "hidden_size": text_config.get("hidden_size"),
        "layers": text_config.get("num_hidden_layers"),
        "linear_value_heads": text_config.get("linear_num_value_heads"),
    }
    layer_types = text_config.get("layer_types")
    if isinstance(layer_types, list):
        actual["linear_attention_layers"] = layer_types.count("linear_attention")
        actual["full_attention_layers"] = layer_types.count("full_attention")
    else:
        errors.append(f"{model_id} layer_types is missing or not a list")

    for field, actual_value in actual.items():
        if entry.get(field) != actual_value:
            errors.append(
                f"{model_id} {field} mismatch: matrix={entry.get(field)!r}, "
                f"config={actual_value!r}"
            )

    index = load_object(index_path, f"{model_id} safetensors index", errors)
    weight_map = index.get("weight_map")
    shards: set[str] = set()
    if not isinstance(weight_map, dict) or not weight_map:
        errors.append(f"{model_id} weight_map is missing or empty")
    else:
        shards = {str(name) for name in weight_map.values()}
        for shard in sorted(shards):
            shard_path = root / shard
            if not shard_path.is_file() or shard_path.stat().st_size <= 0:
                errors.append(f"{model_id} missing/non-empty shard requirement: {shard_path}")

    return {
        "id": model_id,
        "path": str(root),
        "config_sha256": sha256(config_path) if config_path.is_file() else None,
        "index_sha256": sha256(index_path) if index_path.is_file() else None,
        "shard_count": len(shards),
        **actual,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    matrix = load_object(args.matrix, "treatment matrix", errors)
    model_entries = matrix.get("models")
    models: list[dict[str, Any]] = []
    if not isinstance(model_entries, list) or len(model_entries) < 2:
        errors.append("matrix must declare at least two models")
    else:
        for entry in model_entries:
            if not isinstance(entry, dict):
                errors.append("each model entry must be an object")
                continue
            models.append(verify_model(entry, errors))
        architectures = {m.get("text_architecture") for m in models}
        hidden_sizes = {m.get("hidden_size") for m in models}
        if len(architectures) != 1 or None in architectures:
            errors.append(f"models must share one concrete text architecture: {architectures}")
        if len(hidden_sizes) < 2:
            errors.append(f"models must have different sizes: hidden_sizes={hidden_sizes}")

    native = matrix.get("native_treatment")
    if not isinstance(native, dict):
        errors.append("native_treatment must be an object")
    else:
        patch_path = Path(str(native.get("source_patch", "")))
        expected_hash = native.get("sha256")
        if not patch_path.is_file():
            errors.append(f"native patch missing: {patch_path}")
        elif sha256(patch_path) != expected_hash:
            errors.append("native patch SHA256 mismatch")
        if native.get("operator") != "torch_npu.npu_chunk_gated_delta_rule":
            errors.append("native operator identity mismatch")
        if native.get("runtime_proof_required") is not True:
            errors.append("native treatment must require runtime activation proof")

    observed_groups: dict[str, tuple[bool, bool]] = {}
    groups = matrix.get("groups")
    if isinstance(groups, list):
        for group in groups:
            if isinstance(group, dict):
                observed_groups[str(group.get("id"))] = (
                    group.get("native_treatment"),
                    group.get("drrqr"),
                )
    if observed_groups != EXPECTED_GROUPS:
        errors.append(
            f"G1-G4 switches are not the exact orthogonal matrix: {observed_groups}"
        )

    report = {
        "schema": "paper-to-ascend-treatment-verification/v1",
        "valid": not errors,
        "matrix_sha256": sha256(args.matrix) if args.matrix.is_file() else None,
        "models": models,
        "native_patch_sha256": (
            native.get("sha256") if isinstance(native, dict) else None
        ),
        "groups": observed_groups,
        "errors": errors,
    }
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_suffix(args.output.suffix + ".tmp")
        temporary.write_text(payload, encoding="utf-8")
        temporary.replace(args.output)
    print(payload, end="")
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())

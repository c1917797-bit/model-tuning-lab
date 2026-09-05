#!/usr/bin/env python3
"""Freeze one stable Block Influence candidate into a hashed run contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


SOURCE_COMMIT = "18c4d061529d226dd0d699d9e3e1df16dadf29d7"
MODEL_CONFIG_SHA256 = (
    "191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze(analysis_path: Path, removed_layer_count: int) -> dict:
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    if analysis.get("schema") != "qwen35-shortgpt-bi-analysis/v1":
        raise ValueError("unexpected Block Influence analysis schema")
    if not analysis.get("ready_to_freeze"):
        raise ValueError("Block Influence analysis is not ready to freeze")
    if int(analysis.get("expected_layers", 0)) != 64:
        raise ValueError("analysis must cover exactly 64 layers")
    candidates = analysis.get("candidate_sets_lowest_global_influence") or []
    selected = next(
        (
            row
            for row in candidates
            if int(row["removed_layer_count"]) == removed_layer_count
        ),
        None,
    )
    if selected is None:
        raise ValueError(
            f"analysis has no {removed_layer_count}-layer candidate"
        )
    layers = [int(layer) for layer in selected["layers"]]
    if len(layers) != removed_layer_count or len(set(layers)) != len(layers):
        raise ValueError("candidate layer list is not unique and complete")
    if any(layer < 0 or layer >= 64 for layer in layers):
        raise ValueError("candidate contains an out-of-range layer")
    return {
        "schema": "qwen35-shortgpt-layer-set/v1",
        "status": "frozen",
        "method": "ShortGPT lowest global Block Influence",
        "analysis_path": str(analysis_path.resolve()),
        "analysis_sha256": sha256(analysis_path),
        "source_commit": SOURCE_COMMIT,
        "model_config_sha256": MODEL_CONFIG_SHA256,
        "removed_layer_count": removed_layer_count,
        "layers": sorted(layers),
        "env_spec": str(selected["env_spec"]),
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "selection_policy": (
            "Select the requested planning point from a stability-passing "
            "real query_rewrite Block Influence analysis; do not edit the "
            "layer list after this artifact is hashed."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument(
        "--removed-layer-count", type=int, choices=(8, 16, 20), required=True
    )
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to replace layer set: {args.output}")
    payload = freeze(args.analysis, args.removed_layer_count)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"{args.output} {sha256(args.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

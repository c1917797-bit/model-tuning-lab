#!/usr/bin/env python3
"""Verify hash-bound G1-versus-candidate native profile evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


GROUPS = {"G2", "G3", "G4"}
BINDING_FIELDS = (
    "frozen_inputs_sha256",
    "invariant_config_sha256",
    "treatment_matrix_sha256",
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".tmp.{os.getpid()}")
    with temp.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    os.replace(temp, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--minimum-models", type=int, default=2)
    args = parser.parse_args()
    if args.minimum_models < 2:
        raise ValueError("--minimum-models must be at least 2")
    try:
        document = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid profile manifest JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise ValueError("profile manifest root must be an object")

    errors = []
    if document.get("schema") != "paper-to-ascend-profile-evidence/v1":
        errors.append("profile evidence schema is invalid")
    if document.get("fixture_only") is not False:
        errors.append("production profile evidence requires fixture_only=false")
    candidate = document.get("candidate_group")
    if candidate not in GROUPS:
        errors.append("candidate_group must be G2, G3 or G4")
    workload_hash = str(document.get("profile_workload_sha256"))
    if not SHA256_RE.fullmatch(workload_hash):
        errors.append("profile_workload_sha256 is not canonical SHA256")
    bindings = document.get("global_bindings")
    if not isinstance(bindings, dict) or any(
        not SHA256_RE.fullmatch(str(bindings.get(field)))
        for field in BINDING_FIELDS
    ):
        errors.append("global_bindings must contain canonical ruler SHA256 values")

    cells = document.get("cells")
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    if not isinstance(cells, list):
        errors.append("cells must be a list")
        cells = []
    for index, cell in enumerate(cells, 1):
        if not isinstance(cell, dict):
            errors.append(f"cell {index}: must be an object")
            continue
        model = str(cell.get("model", ""))
        group = cell.get("group")
        if not model or group not in {"G1", candidate}:
            errors.append(f"cell {index}: invalid model/group")
            continue
        key = (model, str(group))
        if key in by_key:
            errors.append(f"cell {index}: duplicate {key}")
            continue
        by_key[key] = cell
        if cell.get("capture_environment_disabled") is not True:
            errors.append(f"cell {index}: capture environment was not disabled")
        if cell.get("profiler_enabled") is not True:
            errors.append(f"cell {index}: profiler_enabled must be true")
        artifact = Path(str(cell.get("profile_artifact", "")))
        if (
            not artifact.is_absolute()
            or not artifact.is_file()
            or artifact.is_symlink()
            or artifact.stat().st_size <= 0
        ):
            errors.append(f"cell {index}: profile artifact must be an absolute non-empty regular file")
        else:
            expected = str(cell.get("profile_artifact_sha256"))
            if not SHA256_RE.fullmatch(expected) or sha256(artifact) != expected:
                errors.append(f"cell {index}: profile artifact SHA256 mismatch")
        for field in ("target_region_operator_time_ms", "total_operator_time_ms"):
            try:
                value = float(cell[field])
                if not math.isfinite(value) or value <= 0:
                    raise ValueError
            except (KeyError, TypeError, ValueError, OverflowError):
                errors.append(f"cell {index}: {field} must be finite and positive")
        try:
            invocations = int(cell["target_region_invocations"])
            if invocations <= 0:
                raise ValueError
        except (KeyError, TypeError, ValueError, OverflowError):
            errors.append(f"cell {index}: target_region_invocations must be positive")

    models = sorted({model for model, _ in by_key})
    if len(models) < args.minimum_models:
        errors.append(f"profile evidence requires at least {args.minimum_models} models")
    expected_keys = {
        (model, group) for model in models for group in ("G1", str(candidate))
    }
    if set(by_key) != expected_keys:
        errors.append("profile cells must contain exactly G1 and candidate per model")

    improvements = {}
    if not errors:
        for model in models:
            baseline = float(by_key[(model, "G1")]["target_region_operator_time_ms"])
            treatment = float(by_key[(model, str(candidate))]["target_region_operator_time_ms"])
            improvement = 100.0 * (baseline - treatment) / baseline
            improvements[model] = improvement
            if improvement <= 0:
                errors.append(
                    f"{model}: candidate target-region operator time did not improve"
                )
    report = {
        "schema": "paper-to-ascend-profile-verification/v1",
        "valid": not errors,
        "errors": errors,
        "candidate_group": candidate,
        "models": models,
        "profile_workload_sha256": workload_hash,
        "global_bindings": bindings,
        "target_region_improvement_percent": improvements,
        "manifest_path": str(args.manifest.resolve()),
        "manifest_sha256": sha256(args.manifest),
    }
    atomic_json(args.output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc

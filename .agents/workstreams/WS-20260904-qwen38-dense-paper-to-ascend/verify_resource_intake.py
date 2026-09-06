#!/usr/bin/env python3
"""Read-only verifier for centrally delivered piercing resources."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

EXPECTED_DATASETS = {"NIAH+", "LongBench v2", "GSM8K", "CEval"}
EXPECTED_EVALUATION_ASSETS = {
    "longbenchv2_gen",
    "vllm_api_general_chat",
    "performance_driver",
    "quality_postprocessor",
    "metric_parser",
}
EXPECTED_MODELS = {"qwen38-27b", "qwen35-4b"}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_path(path: Path) -> dict[str, Any]:
    if not path.is_absolute():
        raise ValueError("path must be absolute")
    if path.is_symlink():
        raise ValueError("top-level symbolic links are forbidden")
    if path.is_file():
        size = path.stat().st_size
        if size <= 0:
            raise ValueError("file is empty")
        return {"kind": "file", "file_count": 1, "size_bytes": size, "sha256": file_sha256(path)}
    if not path.is_dir():
        raise ValueError("path does not exist as a file or directory")

    rows: list[dict[str, Any]] = []
    total = 0
    for root, directories, files in os.walk(path, followlinks=False):
        root_path = Path(root)
        for name in list(directories):
            child = root_path / name
            if child.is_symlink():
                raise ValueError(f"directory contains symbolic link: {child.relative_to(path)}")
        for name in files:
            child = root_path / name
            if child.is_symlink():
                raise ValueError(f"directory contains symbolic link: {child.relative_to(path)}")
            size = child.stat().st_size
            total += size
            rows.append(
                {
                    "path": child.relative_to(path).as_posix(),
                    "size_bytes": size,
                    "sha256": file_sha256(child),
                }
            )
    if not rows:
        raise ValueError("directory contains no files")
    rows.sort(key=lambda row: row["path"])
    canonical = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        "kind": "directory",
        "file_count": len(rows),
        "size_bytes": total,
        "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def verify_artifact(label: str, value: Any, errors: list[str], report: dict[str, Any]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return False
    raw_path = value.get("path")
    expected = value.get("sha256")
    if not isinstance(raw_path, str) or "REQUIRED" in raw_path:
        errors.append(f"{label} path is unresolved")
        return False
    if not isinstance(expected, str) or "REQUIRED" in expected:
        errors.append(f"{label} sha256 is unresolved")
        return False
    try:
        observed = inspect_path(Path(raw_path))
    except (OSError, ValueError) as exc:
        errors.append(f"{label} invalid: {exc}")
        return False
    observed["path"] = raw_path
    report[label] = observed
    if observed["sha256"] != expected:
        errors.append(f"{label} SHA256 mismatch: expected={expected}, observed={observed['sha256']}")
        return False
    return True


def keyed_rows(value: Any, key: str, label: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, list):
        errors.append(f"{label} must be a list")
        return {}
    result: dict[str, Any] = {}
    for row in value:
        if not isinstance(row, dict) or not isinstance(row.get(key), str):
            errors.append(f"every {label} row must contain string {key}")
            continue
        identity = row[key]
        if identity in result:
            errors.append(f"duplicate {label} {key}: {identity}")
        result[identity] = row
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    errors: list[str] = []
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, indent=2))
        return 2
    if manifest.get("schema") != "paper-to-ascend-resource-intake/v1":
        errors.append("resource intake schema mismatch")
    artifacts: dict[str, Any] = {}
    verify_artifact("benchmark_bundle", manifest.get("benchmark_bundle"), errors, artifacts)

    datasets = keyed_rows(manifest.get("datasets"), "name", "datasets", errors)
    if set(datasets) != EXPECTED_DATASETS:
        errors.append(f"dataset names must be exactly {sorted(EXPECTED_DATASETS)}")
    for name, row in datasets.items():
        verify_artifact(f"dataset:{name}", row, errors, artifacts)

    evaluation = keyed_rows(
        manifest.get("evaluation_assets"), "id", "evaluation_assets", errors
    )
    if set(evaluation) != EXPECTED_EVALUATION_ASSETS:
        errors.append(
            f"evaluation asset ids must be exactly {sorted(EXPECTED_EVALUATION_ASSETS)}"
        )
    for identity, row in evaluation.items():
        verify_artifact(f"evaluation:{identity}", row, errors, artifacts)

    drrqr = manifest.get("drrqr")
    implementation_valid = False
    checkpoint_valid: set[str] = set()
    if not isinstance(drrqr, dict):
        errors.append("drrqr must be an object")
    else:
        implementation = drrqr.get("implementation")
        if implementation is not None:
            implementation_valid = verify_artifact(
                "drrqr:implementation", implementation, errors, artifacts
            )
        checkpoints = keyed_rows(drrqr.get("checkpoints"), "model_id", "checkpoints", errors)
        for model_id, row in checkpoints.items():
            if "REQUIRED" not in str(row.get("path")) and "REQUIRED" not in str(row.get("sha256")):
                if verify_artifact(f"drrqr:checkpoint:{model_id}", row, errors, artifacts):
                    checkpoint_valid.add(model_id)
        if not implementation_valid and checkpoint_valid != EXPECTED_MODELS:
            errors.append("provide a valid DRRQR implementation or valid checkpoints for both models")

    provenance = manifest.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("provenance must be an object")
    else:
        for field in ("owner", "version_or_commit", "received_at_utc"):
            value = provenance.get(field)
            if not isinstance(value, str) or not value or "REQUIRED" in value:
                errors.append(f"provenance.{field} is unresolved")

    result = {
        "schema": "paper-to-ascend-resource-intake-verification/v1",
        "valid": not errors,
        "read_only": True,
        "artifacts": artifacts,
        "errors": errors,
    }
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())

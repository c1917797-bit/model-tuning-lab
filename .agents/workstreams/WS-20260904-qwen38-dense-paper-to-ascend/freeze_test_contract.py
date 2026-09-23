#!/usr/bin/env python3
"""Freeze dataset and experiment inputs into a reproducible SHA256 manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def find_placeholders(value: Any, location: str = "$") -> list[str]:
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            found.extend(find_placeholders(child, f"{location}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(find_placeholders(child, f"{location}[{index}]"))
    elif isinstance(value, str) and "REQUIRED" in value:
        found.append(location)
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--runtime-config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--dataset",
        action="append",
        default=[],
        metavar="NAME=PATH",
        help="Repeat once per frozen dataset.",
    )
    args = parser.parse_args()

    contract = load_json(args.contract)
    runtime_config = load_json(args.runtime_config)
    datasets = []
    seen = set()
    errors = []
    placeholders = find_placeholders(runtime_config)
    if placeholders:
        errors.append(
            "runtime config contains REQUIRED placeholders at: "
            + ", ".join(placeholders)
        )
    for item in args.dataset:
        if "=" not in item:
            errors.append(f"invalid --dataset value: {item}")
            continue
        name, raw_path = item.split("=", 1)
        name = name.strip()
        path = Path(raw_path).expanduser().resolve()
        if not name or name in seen:
            errors.append(f"empty or duplicate dataset name: {name!r}")
            continue
        seen.add(name)
        if not path.is_file():
            errors.append(f"dataset is not a regular file: {path}")
            continue
        if path.stat().st_size == 0:
            errors.append(f"dataset is empty: {path}")
            continue
        stat = path.stat()
        datasets.append(
            {
                "name": name,
                "path": str(path),
                "size_bytes": stat.st_size,
                "sha256": sha256_file(path),
            }
        )

    required = {
        row["name"]
        for row in contract.get("datasets", [])
        if row.get("required", False)
    }
    missing = sorted(required - seen)
    if missing:
        errors.append("missing required datasets: " + ", ".join(missing))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 2

    manifest = {
        "schema": "paper-to-ascend-frozen-inputs/v1",
        "contract_path": str(args.contract.resolve()),
        "contract_sha256": sha256_file(args.contract),
        "runtime_config_path": str(args.runtime_config.resolve()),
        "runtime_config_sha256": sha256_file(args.runtime_config),
        "runtime_config_canonical_sha256": canonical_sha256(runtime_config),
        "datasets": sorted(datasets, key=lambda row: row["name"]),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "freeze_complete": True,
    }
    manifest["frozen_inputs_sha256"] = canonical_sha256(
        {
            "contract_sha256": manifest["contract_sha256"],
            "runtime_config_canonical_sha256": manifest[
                "runtime_config_canonical_sha256"
            ],
            "datasets": manifest["datasets"],
        }
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temp = args.output.with_name(args.output.name + f".tmp.{os.getpid()}")
    with temp.open("w", encoding="utf-8") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    os.replace(temp, args.output)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

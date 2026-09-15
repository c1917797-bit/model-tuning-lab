#!/usr/bin/env python3
"""Create a deterministic byte manifest for one formal A/B arm."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def digest(path: Path) -> dict:
    hasher = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            hasher.update(chunk)
            size += len(chunk)
    return {"path": str(path), "size": size, "sha256": hasher.hexdigest()}


def build(entries: list[str]) -> dict:
    files = {}
    for entry in entries:
        if "=" not in entry:
            raise ValueError(f"expected LABEL=PATH, got {entry!r}")
        label, raw_path = entry.split("=", 1)
        if not label or label in files:
            raise ValueError(f"invalid or duplicate label: {label!r}")
        path = Path(raw_path)
        if not path.is_file():
            raise ValueError(f"{label}: missing regular file: {path}")
        files[label] = digest(path)
    return {"schema": "dasc-formal-runtime-manifest/v1", "files": files}


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--file", action="append", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = build(args.file)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

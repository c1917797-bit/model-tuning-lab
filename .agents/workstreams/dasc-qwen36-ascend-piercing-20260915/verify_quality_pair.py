#!/usr/bin/env python3
"""Fail closed when deciding whether one v13 quality run is reusable."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from verify_formal_decision import verify_quality_run


def read_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def read_rows(path: Path) -> list[dict]:
    rows = []
    for number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{number}: expected JSON object")
        rows.append(value)
    return rows


def verify(dataset: str, summary: Path, details: Path) -> dict:
    checks = verify_quality_run(
        {
            "run_id": read_object(summary).get("run_id"),
            "summary": read_object(summary),
            "details": read_rows(details),
            "details_sha256": hashlib.sha256(details.read_bytes()).hexdigest(),
        },
        dataset,
    )
    return {"ok": all(checks.values()), "checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--dataset", required=True, choices=("longbenchv2", "gsm8k"))
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--details", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.dataset, args.summary, args.details)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        result = {"ok": False, "error": str(error)}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

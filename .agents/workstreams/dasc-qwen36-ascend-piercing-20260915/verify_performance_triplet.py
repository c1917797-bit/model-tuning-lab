#!/usr/bin/env python3
"""Fail closed when deciding whether one v13 performance run is reusable."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from verify_formal_decision import verify_performance_run


def read_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def verify(report: Path, metrics_before: Path, metrics_after: Path) -> dict:
    checks = verify_performance_run(
        {
            "report": read_object(report),
            "metrics_before": read_object(metrics_before),
            "metrics_after": read_object(metrics_after),
        }
    )
    return {"ok": all(checks.values()), "checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--metrics-before", required=True, type=Path)
    parser.add_argument("--metrics-after", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.report, args.metrics_before, args.metrics_after)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        result = {"ok": False, "error": str(error)}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

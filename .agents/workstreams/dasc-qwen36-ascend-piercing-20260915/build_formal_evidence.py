#!/usr/bin/env python3
"""Build the normalized DASC v13 decision input from immutable raw artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ARMS = ("dense", "candidate")
DATASETS = ("longbenchv2", "gsm8k")
RUN_IDS = ("run1", "run2", "run3")


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{number}: expected JSON object")
            rows.append(value)
    return rows


def build(root: Path) -> dict:
    arms = {}
    for arm in ARMS:
        arm_root = root / arm
        performance = []
        for run_id in RUN_IDS:
            performance.append(
                {
                    "run_id": run_id,
                    "report": read_json(arm_root / f"performance.{run_id}.json"),
                    "metrics_before": read_json(
                        arm_root / f"performance.{run_id}.metrics.before.json"
                    ),
                    "metrics_after": read_json(
                        arm_root / f"performance.{run_id}.metrics.after.json"
                    ),
                }
            )
        quality = {}
        for dataset in DATASETS:
            quality[dataset] = []
            for run_id in RUN_IDS:
                quality_root = root / "quality" / arm
                quality[dataset].append(
                    {
                        "run_id": run_id,
                        "summary": read_json(
                            quality_root / f"{dataset}.{run_id}.summary.json"
                        ),
                        "details": read_jsonl(
                            quality_root / f"{dataset}.{run_id}.jsonl"
                        ),
                    }
                )
        arms[arm] = {
            "identity": read_json(arm_root / "identity.json"),
            "performance": performance,
            "quality": quality,
        }
    return {"schema": "dasc-formal-v13-normalized/v1", "arms": arms}


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = build(args.root)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

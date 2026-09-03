#!/usr/bin/env python3
"""Score HumanEval completions. MUST run inside the repository sandbox command."""

from __future__ import annotations

import argparse
import gzip
import json
import os
import subprocess
import sys
from pathlib import Path


def clean_completion(text: str) -> str:
    return text.replace("```python", "").replace("```", "")


def main() -> int:
    if os.environ.get("HUMANEVAL_SANDBOX") != "1":
        raise SystemExit("Refusing to execute generated code outside the HumanEval sandbox")
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", required=True)
    parser.add_argument("--data", default="/data/HumanEval.jsonl.gz")
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()
    result = json.loads(Path(args.result).read_text())
    completions = {
        row["key"]: row["completion"]
        for row in result["records"]
        if row["dataset"] == "humaneval" and not row["error"]
    }
    with gzip.open(args.data, "rt", encoding="utf-8") as f:
        tasks = [json.loads(line) for line in f if line.strip()]
    details = []
    for task in tasks:
        task_id = task["task_id"]
        completion = completions.get(task_id)
        if completion is None:
            details.append({"task_id": task_id, "passed": False, "reason": "missing completion"})
            continue
        program = (
            task["prompt"]
            + clean_completion(completion)
            + "\n"
            + task["test"]
            + f"\ncheck({task['entry_point']})\n"
        )
        try:
            completed = subprocess.run(
                [sys.executable, "-I", "-c", program],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=args.timeout,
                text=True,
            )
            passed = completed.returncode == 0
            reason = "pass" if passed else (completed.stderr[-500:] or f"exit {completed.returncode}")
        except subprocess.TimeoutExpired:
            passed, reason = False, "timeout"
        details.append({"task_id": task_id, "passed": passed, "reason": reason})
    passed = sum(row["passed"] for row in details)
    summary = {
        "n": len(details),
        "passed": passed,
        "pass_at_1": passed / len(details) if details else None,
        "details": details,
    }
    Path(args.output).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "details"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

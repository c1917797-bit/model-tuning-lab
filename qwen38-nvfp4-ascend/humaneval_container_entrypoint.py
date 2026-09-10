#!/usr/bin/env python3
"""Run the pinned HumanEval evaluator inside the outer Docker sandbox."""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--samples", required=True)
    parser.add_argument("--problems", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=3.0)
    args = parser.parse_args()

    temp_root = Path(tempfile.mkdtemp(prefix="humaneval-"))
    copied = temp_root / "source"
    shutil.copytree(args.source, copied)
    execution = copied / "human_eval" / "execution.py"
    text = execution.read_text(encoding="utf-8")
    disabled = "                    # exec(check_program, exec_globals)"
    enabled = "                    exec(check_program, exec_globals)"
    disabled_count = text.count(disabled)
    enabled_count = sum(line == enabled for line in text.splitlines())
    if disabled_count == 1 and enabled_count == 0:
        text = text.replace(disabled, enabled)
    elif disabled_count == 0 and enabled_count == 1:
        pass
    else:
        raise SystemExit("pinned HumanEval execution guard changed; refusing to run")
    execution.write_text(text, encoding="utf-8")
    sys.path.insert(0, str(copied))

    sample_copy = temp_root / "samples.jsonl"
    shutil.copy2(args.samples, sample_copy)

    from human_eval.evaluation import evaluate_functional_correctness

    result = evaluate_functional_correctness(
        sample_file=str(sample_copy),
        k=[1],
        n_workers=args.workers,
        timeout=args.timeout,
        problem_file=args.problems,
    )
    result_path = Path(str(sample_copy) + "_results.jsonl")
    shutil.copy2(result_path, args.result)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

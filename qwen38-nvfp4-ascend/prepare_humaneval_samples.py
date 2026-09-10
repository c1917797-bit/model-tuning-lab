#!/usr/bin/env python3
"""Convert raw serving responses into the official HumanEval sample schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def prepare(requests: list[dict], responses: list[dict]) -> list[dict]:
    expected = {row["id"] for row in requests if row.get("suite") == "humaneval"}
    if len(expected) != len(requests):
        raise ValueError("request manifest is not exclusively HumanEval")
    indexed = {}
    for row in responses:
        item_id = row.get("id")
        if item_id in indexed:
            raise ValueError(f"duplicate response id: {item_id}")
        indexed[item_id] = row
    if set(indexed) != expected:
        raise ValueError("response population does not match HumanEval requests")
    samples = []
    for item_id in sorted(expected, key=lambda value: int(value.rsplit("/", 1)[-1])):
        row = indexed[item_id]
        if row.get("error"):
            raise ValueError(f"failed response: {item_id}")
        if not row.get("rendered_prompt_sha256"):
            raise ValueError(f"missing rendered prompt hash: {item_id}")
        if not isinstance(row.get("text"), str):
            raise ValueError(f"missing completion text: {item_id}")
        samples.append({"task_id": item_id, "completion": row["text"]})
    return samples


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", type=Path, required=True)
    parser.add_argument("--responses", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    samples = prepare(read_jsonl(args.requests), read_jsonl(args.responses))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        for sample in samples:
            handle.write(json.dumps(sample, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps({"samples": len(samples), "output": str(args.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

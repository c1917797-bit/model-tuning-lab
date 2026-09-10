#!/usr/bin/env python3
"""Pair-compare one-sample-per-task HumanEval result artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def index_unique(rows: list[dict], key: str, label: str) -> dict[str, dict]:
    indexed = {}
    for row in rows:
        item_id = row.get(key)
        if not isinstance(item_id, str) or item_id in indexed:
            raise ValueError(f"{label}: missing or duplicate {key}: {item_id!r}")
        indexed[item_id] = row
    return indexed


def compare(
    control_responses: list[dict],
    candidate_responses: list[dict],
    control_results: list[dict],
    candidate_results: list[dict],
    expected_count: int = 164,
) -> dict:
    cr = index_unique(control_responses, "id", "control responses")
    xr = index_unique(candidate_responses, "id", "candidate responses")
    ce = index_unique(control_results, "task_id", "control results")
    xe = index_unique(candidate_results, "task_id", "candidate results")
    ids = set(cr)
    if len(ids) != expected_count or set(xr) != ids or set(ce) != ids or set(xe) != ids:
        raise ValueError("HumanEval populations do not match the expected task set")
    prompt_hash_mismatches = 0
    disagreements = []
    control_passed = candidate_passed = 0
    for item_id in sorted(ids, key=lambda value: int(value.rsplit("/", 1)[-1])):
        if cr[item_id].get("error") or xr[item_id].get("error"):
            raise ValueError(f"serving error for {item_id}")
        hashes = {cr[item_id].get("rendered_prompt_sha256"), xr[item_id].get("rendered_prompt_sha256")}
        if None in hashes or len(hashes) != 1:
            prompt_hash_mismatches += 1
        c_pass = bool(ce[item_id].get("passed"))
        x_pass = bool(xe[item_id].get("passed"))
        control_passed += int(c_pass)
        candidate_passed += int(x_pass)
        if c_pass != x_pass:
            disagreements.append({
                "id": item_id,
                "control_passed": c_pass,
                "candidate_passed": x_pass,
                "control_result": ce[item_id].get("result"),
                "candidate_result": xe[item_id].get("result"),
            })
    return {
        "schema": "qwen38-paired-humaneval/v1",
        "total": expected_count,
        "prompt_hash_mismatches": prompt_hash_mismatches,
        "control": {"passed": control_passed, "pass_at_1": control_passed / expected_count},
        "candidate": {"passed": candidate_passed, "pass_at_1": candidate_passed / expected_count},
        "pass_at_1_delta": (candidate_passed - control_passed) / expected_count,
        "outcome_disagreements": len(disagreements),
        "gate_pass": prompt_hash_mismatches == 0 and candidate_passed >= control_passed,
        "disagreements": disagreements,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control-responses", type=Path, required=True)
    parser.add_argument("--candidate-responses", type=Path, required=True)
    parser.add_argument("--control-results", type=Path, required=True)
    parser.add_argument("--candidate-results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = compare(
        read_jsonl(args.control_responses), read_jsonl(args.candidate_responses),
        read_jsonl(args.control_results), read_jsonl(args.candidate_results),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "disagreements"}, indent=2))
    return 0 if report["gate_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Score and pair-compare MMLU/GSM8K response JSONL artifacts."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

CHOICE_RE = re.compile(r"(?:^|\b)([ABCD])(?:\b|[.)])", re.IGNORECASE)
NUMBER_RE = re.compile(r"[-+]?(?:\d[\d,]*\.?\d*|\.\d+)")


def normalize_number(value: str) -> str | None:
    match = NUMBER_RE.fullmatch(value.strip().replace("$", "").replace("%", ""))
    if not match:
        return None
    normalized = match.group(0).replace(",", "")
    try:
        number = float(normalized)
    except ValueError:
        return None
    return str(int(number)) if number.is_integer() else format(number, ".15g")


def extract_answer(suite: str, text: str) -> str | None:
    if suite == "mmlu":
        match = CHOICE_RE.search(text.strip())
        return match.group(1).upper() if match else None
    if suite == "gsm8k":
        if "####" not in text:
            return None
        return normalize_number(text.rsplit("####", 1)[-1].strip())
    raise ValueError(f"unsupported suite: {suite}")


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def index_unique(rows: list[dict], label: str) -> dict[str, dict]:
    indexed = {}
    for row in rows:
        item_id = row.get("id")
        if not isinstance(item_id, str) or item_id in indexed:
            raise SystemExit(f"{label}: missing or duplicate id {item_id!r}")
        indexed[item_id] = row
    return indexed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", type=Path, required=True)
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    requests = index_unique(load_jsonl(args.requests), "requests")
    control = index_unique(load_jsonl(args.control), "control")
    candidate = index_unique(load_jsonl(args.candidate), "candidate")
    expected = set(requests)
    for label, rows in (("control", control), ("candidate", candidate)):
        if set(rows) != expected:
            raise SystemExit(f"{label}: request id population mismatch")

    details = []
    scores = {"control": 0, "candidate": 0}
    parse_failures = {"control": 0, "candidate": 0}
    prompt_hash_mismatches = 0
    for item_id in sorted(expected):
        request = requests[item_id]
        suite = request["suite"]
        if suite not in {"mmlu", "gsm8k"}:
            raise SystemExit(f"unsupported suite in text scorer: {suite}")
        c0, c1 = control[item_id], candidate[item_id]
        if c0.get("error") or c1.get("error"):
            raise SystemExit(f"request failure for {item_id}")
        hashes = {c0.get("rendered_prompt_sha256"), c1.get("rendered_prompt_sha256")}
        if None in hashes or len(hashes) != 1:
            prompt_hash_mismatches += 1
        answers = {
            "control": extract_answer(suite, str(c0.get("text", ""))),
            "candidate": extract_answer(suite, str(c1.get("text", ""))),
        }
        reference = request["reference"]
        if suite == "gsm8k":
            reference = normalize_number(reference)
        correct = {}
        for arm in ("control", "candidate"):
            if answers[arm] is None:
                parse_failures[arm] += 1
            correct[arm] = answers[arm] == reference
            scores[arm] += int(correct[arm])
        if answers["control"] != answers["candidate"]:
            details.append({
                "id": item_id,
                "reference": reference,
                "control_answer": answers["control"],
                "candidate_answer": answers["candidate"],
                "control_correct": correct["control"],
                "candidate_correct": correct["candidate"],
            })

    total = len(expected)
    report = {
        "schema": "qwen38-paired-quality/v1",
        "suite": next(iter(requests.values()))["suite"],
        "total": total,
        "prompt_hash_mismatches": prompt_hash_mismatches,
        "parse_failures": parse_failures,
        "control": {"correct": scores["control"], "accuracy": scores["control"] / total},
        "candidate": {"correct": scores["candidate"], "accuracy": scores["candidate"] / total},
        "accuracy_delta": (scores["candidate"] - scores["control"]) / total,
        "answer_disagreements": len(details),
        "gate_pass": prompt_hash_mismatches == 0 and scores["candidate"] >= scores["control"],
        "disagreements": details,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "disagreements"}, indent=2))
    return 0 if report["gate_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

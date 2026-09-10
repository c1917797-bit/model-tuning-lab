#!/usr/bin/env python3
"""Freeze deterministic MMLU, GSM8K and HumanEval request manifests."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
from typing import Iterable

CHOICES = "ABCD"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def format_mmlu(row: list[str], include_answer: bool) -> str:
    question, *tail = row
    options, answer = tail[:4], tail[4]
    text = question + "\n" + "\n".join(
        f"{letter}. {option}" for letter, option in zip(CHOICES, options)
    )
    return text + f"\nAnswer: {answer if include_answer else ''}"


def mmlu_records(root: Path) -> Iterable[dict]:
    for test_path in sorted((root / "test").glob("*_test.csv")):
        subject = test_path.name.removesuffix("_test.csv")
        dev_path = root / "dev" / f"{subject}_dev.csv"
        with dev_path.open(encoding="utf-8", newline="") as handle:
            examples = list(csv.reader(handle))
        header = (
            "The following are multiple choice questions (with answers) about "
            + subject.replace("_", " ")
            + ".\n\n"
        )
        shots = "\n\n".join(format_mmlu(row, True) for row in examples)
        with test_path.open(encoding="utf-8", newline="") as handle:
            for index, row in enumerate(csv.reader(handle)):
                yield {
                    "id": f"mmlu/{subject}/{index}",
                    "suite": "mmlu",
                    "subject": subject,
                    "prompt_mode": "chat",
                    "prompt": header + shots + "\n\n" + format_mmlu(row, False),
                    "reference": row[5],
                    "generation": {"temperature": 0, "top_p": 1, "max_tokens": 8},
                }


def gsm8k_records(path: Path) -> Iterable[dict]:
    instruction = (
        "Solve the following grade-school math problem. Show concise reasoning, "
        "then end with exactly '#### ' followed by the final numeric answer.\n\n"
    )
    with path.open(encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            item = json.loads(line)
            yield {
                "id": f"gsm8k/{index}",
                "suite": "gsm8k",
                "prompt_mode": "chat",
                "prompt": instruction + item["question"],
                "reference": item["answer"].rsplit("####", 1)[-1].strip(),
                "generation": {"temperature": 0, "top_p": 1, "max_tokens": 768},
            }


def humaneval_records(path: Path) -> Iterable[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            item = json.loads(line)
            yield {
                "id": item["task_id"],
                "suite": "humaneval",
                "prompt_mode": "completion",
                "prompt": item["prompt"],
                "reference": {
                    "entry_point": item["entry_point"],
                    "test": item["test"],
                },
                "generation": {
                    "temperature": 0,
                    "top_p": 1,
                    "max_tokens": 1024,
                    "stop": ["\nclass ", "\nif __name__", "\n# Test"],
                },
            }


def write_jsonl(path: Path, records: Iterable[dict]) -> tuple[int, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count, sha256(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mmlu", type=Path, required=True)
    parser.add_argument("--gsm8k", type=Path, required=True)
    parser.add_argument("--humaneval", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    sources = {
        "mmlu_dev": sorted((args.mmlu / "dev").glob("*_dev.csv")),
        "mmlu_test": sorted((args.mmlu / "test").glob("*_test.csv")),
        "gsm8k": [args.gsm8k],
        "humaneval": [args.humaneval],
    }
    if len(sources["mmlu_dev"]) != 57 or len(sources["mmlu_test"]) != 57:
        raise SystemExit("MMLU must contain exactly 57 dev and 57 test files")

    outputs = {}
    generators = {
        "mmlu": mmlu_records(args.mmlu),
        "gsm8k": gsm8k_records(args.gsm8k),
        "humaneval": humaneval_records(args.humaneval),
    }
    for suite, records in generators.items():
        count, digest = write_jsonl(args.output / f"{suite}.jsonl", records)
        outputs[suite] = {"count": count, "sha256": digest}

    expected = {"mmlu": 14042, "gsm8k": 1319, "humaneval": 164}
    if {key: value["count"] for key, value in outputs.items()} != expected:
        raise SystemExit(f"unexpected population: {outputs}")

    source_manifest = {
        name: [
            {"path": str(path), "size": path.stat().st_size, "sha256": sha256(path)}
            for path in paths
        ]
        for name, paths in sources.items()
    }
    manifest = {"schema": "qwen38-quality-manifest/v1", "sources": source_manifest, "outputs": outputs}
    manifest_path = args.output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Local-only data providers for lm-eval custom_dataset (no prompt/scorer edits).

Call via custom_dataset with metadata data_root and (MMLU only) subject.
These providers do not execute HumanEval code or contact the network.
Dataset identity must be bound to the run separately.
"""
import csv
import gzip
import json
from pathlib import Path


def read_rows(data_root, suite, subject=None):
    root = Path(data_root)
    if suite == "mmlu":
        available = {p.name[:-9] for p in (root / "prepared/mmlu/test").glob("*_test.csv")}
        if subject not in available:
            raise ValueError("Unknown local MMLU subject")
        result = {}
        for split in ("dev", "test"):
            path = root / "prepared/mmlu" / split / (subject + "_" + split + ".csv")
            with path.open(newline="", encoding="utf-8") as stream:
                raw = list(csv.reader(stream))
            if not raw or any(len(r) != 6 or r[5] not in "ABCD" or len(r[5]) != 1 for r in raw):
                raise ValueError("Invalid MMLU CSV schema")
            result[split] = [
                {"question": r[0], "choices": r[1:5], "answer": "ABCD".index(r[5])}
                for r in raw
            ]
        if len(result["dev"]) != 5:
            raise ValueError("Expected five development examples")
        return result
    if suite == "gsm8k":
        result = {}
        for split, expected in (("train", 7473), ("test", 1319)):
            path = root / "unpack/gsm8k/grade_school_math/data" / (split + ".jsonl")
            with path.open(encoding="utf-8") as stream:
                rows = [json.loads(line) for line in stream if line.strip()]
            if len(rows) != expected or any(
                not isinstance(r.get("question"), str) or not isinstance(r.get("answer"), str)
                for r in rows
            ):
                raise ValueError("Invalid GSM8K population/schema")
            result[split] = rows
        return result
    if suite == "humaneval":
        path = root / "unpack/humaneval/data/HumanEval.jsonl.gz"
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            rows = [json.loads(line) for line in stream if line.strip()]
        keys = ("task_id", "prompt", "canonical_solution", "test", "entry_point")
        if len(rows) != 164 or any(not all(isinstance(r.get(k), str) for k in keys) for r in rows):
            raise ValueError("Invalid HumanEval population/schema")
        if len({r["task_id"] for r in rows}) != 164:
            raise ValueError("Duplicate HumanEval task")
        return {"test": rows}
    raise ValueError("Unsupported suite")


def _dataset(data_root, suite, subject=None):
    from datasets import Dataset, DatasetDict
    return DatasetDict({
        split: Dataset.from_list(rows)
        for split, rows in read_rows(data_root, suite, subject).items()
    })


def mmlu(data_root, subject, **metadata):
    return _dataset(data_root, "mmlu", subject)


def gsm8k(data_root, **metadata):
    return _dataset(data_root, "gsm8k")


def humaneval(data_root, **metadata):
    return _dataset(data_root, "humaneval")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("data_root")
    args = parser.parse_args()
    subjects = sorted(p.name[:-9] for p in
                      (Path(args.data_root) / "prepared/mmlu/test").glob("*_test.csv"))
    populations = [read_rows(args.data_root, "mmlu", s) for s in subjects]
    assert len(subjects) == 57
    assert sum(len(p["test"]) for p in populations) == 14042
    assert sum(len(p["dev"]) for p in populations) == 285
    for bad in ("../test", "nonexistent_subject"):
        try:
            read_rows(args.data_root, "mmlu", bad)
        except ValueError:
            pass
        else:
            raise AssertionError("Unknown subject accepted")
    read_rows(args.data_root, "gsm8k")
    read_rows(args.data_root, "humaneval")
    print("PASS: MMLU 57/14042/285; GSM8K 7473/1319; HumanEval 164; invalid subject rejected")


#!/usr/bin/env python3
"""Deterministic MMLU, GSM8K and HumanEval evaluator for a vLLM endpoint."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import re
import statistics
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any


LETTERS = "ABCD"
NUMBER_RE = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")


@dataclass
class Case:
    dataset: str
    key: str
    prompt: str
    gold: str | None
    max_tokens: int
    meta: dict[str, Any]


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    pos = (len(xs) - 1) * p
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return xs[lo]
    return xs[lo] * (hi - pos) + xs[hi] * (pos - lo)


def mmlu_format(row: list[str], include_answer: bool) -> str:
    text = row[0].strip() + "\n"
    for i, choice in enumerate(row[1:5]):
        text += f"{LETTERS[i]}. {choice.strip()}\n"
    text += "Answer:"
    if include_answer:
        text += f" {row[5].strip()}\n\n"
    return text


def load_mmlu(data_dir: Path, per_subject: int) -> tuple[list[Case], list[Case]]:
    dev_dir = data_dir / "mmlu" / "dev"
    test_dir = data_dir / "mmlu" / "test"
    cases, warmups = [], []
    test_files = sorted(test_dir.glob("*_test.csv"))
    if len(test_files) < 50:
        raise RuntimeError(f"Expected MMLU subjects, found {len(test_files)}")
    for test_path in test_files:
        subject = test_path.name.removesuffix("_test.csv")
        dev_path = dev_dir / f"{subject}_dev.csv"
        if not dev_path.exists():
            raise RuntimeError(f"Missing MMLU dev file for {subject}")
        with dev_path.open(newline="", encoding="utf-8") as f:
            dev = list(csv.reader(f))[:5]
        with test_path.open(newline="", encoding="utf-8") as f:
            test = list(csv.reader(f))
        header = (
            "The following are multiple choice questions (with answers) about "
            + subject.replace("_", " ")
            + ".\n\n"
        )
        prefix = header + "".join(mmlu_format(row, True) for row in dev)
        warm = test[0]
        warmups.append(
            Case("mmlu", f"{subject}:warmup", prefix + mmlu_format(warm, False), warm[5], 8, {"subject": subject})
        )
        for idx, row in enumerate(test[1 : 1 + per_subject], start=1):
            cases.append(
                Case("mmlu", f"{subject}:{idx}", prefix + mmlu_format(row, False), row[5].strip(), 8, {"subject": subject})
            )
    return cases, warmups


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def load_gsm8k(data_dir: Path, limit: int) -> tuple[list[Case], list[Case]]:
    train = read_jsonl(data_dir / "gsm8k_train.jsonl")
    test = read_jsonl(data_dir / "gsm8k_test.jsonl")
    prefix = "Solve each math problem. Show the reasoning, then end with `#### <number>`.\n\n"
    for example in train[:8]:
        prefix += f"Question: {example['question']}\nAnswer: {example['answer']}\n\n"

    def make(example: dict[str, Any], key: str) -> Case:
        gold = example["answer"].rsplit("####", 1)[-1].strip().replace(",", "")
        return Case("gsm8k", key, prefix + f"Question: {example['question']}\nAnswer:", gold, 512, {})

    return (
        [make(example, f"gsm8k:{i}") for i, example in enumerate(test[1 : 1 + limit], start=1)],
        [make(test[0], "gsm8k:warmup")],
    )


def load_humaneval(data_dir: Path, limit: int) -> tuple[list[Case], list[Case]]:
    with gzip.open(data_dir / "HumanEval.jsonl.gz", "rt", encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    cases = [
        Case("humaneval", row["task_id"], row["prompt"], None, 512, {"entry_point": row["entry_point"]})
        for row in rows[:limit]
    ]
    warmup = Case("humaneval", "humaneval:warmup", "def add_two_numbers(a, b):\n    ", None, 64, {})
    return cases, [warmup]


def parse_mmlu(text: str) -> str | None:
    match = re.search(r"(?:^|\b)([ABCD])(?:\b|[.)])", text.strip(), re.I)
    return match.group(1).upper() if match else None


def parse_gsm8k(text: str) -> str | None:
    if "####" in text:
        match = NUMBER_RE.search(text.rsplit("####", 1)[-1])
        if match:
            return match.group(0).replace(",", "")
    numbers = NUMBER_RE.findall(text)
    return numbers[-1].replace(",", "") if numbers else None


def stream_completion(base_url: str, model: str, case: Case, timeout: float) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": model,
        "prompt": case.prompt,
        "temperature": 0,
        "max_tokens": case.max_tokens,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    if case.dataset == "humaneval":
        body["stop"] = ["\nclass ", "\nif __name__", "\n# Test", "\n```"]
    request = urllib.request.Request(
        base_url.rstrip("/") + "/v1/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    start = time.perf_counter()
    first = None
    chunks: list[str] = []
    usage: dict[str, Any] = {}
    error = None
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            for raw in response:
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload == "[DONE]":
                    break
                obj = json.loads(payload)
                if obj.get("usage"):
                    usage = obj["usage"]
                for choice in obj.get("choices") or []:
                    piece = choice.get("text") or ""
                    if piece:
                        if first is None:
                            first = time.perf_counter()
                        chunks.append(piece)
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    end = time.perf_counter()
    text = "".join(chunks)
    prediction, correct = None, None
    if case.dataset == "mmlu":
        prediction = parse_mmlu(text)
        correct = prediction == case.gold
    elif case.dataset == "gsm8k":
        prediction = parse_gsm8k(text)
        correct = prediction == case.gold
    return {
        "dataset": case.dataset,
        "key": case.key,
        "gold": case.gold,
        "prediction": prediction,
        "correct": correct,
        "completion": text,
        "meta": case.meta,
        "ttft_ms": (first - start) * 1000 if first is not None else None,
        "e2e_ms": (end - start) * 1000,
        "usage": usage,
        "error": error,
    }


def summarize(records: list[dict[str, Any]], wall_s: float) -> dict[str, Any]:
    e2e = [r["e2e_ms"] for r in records if not r["error"]]
    ttft = [r["ttft_ms"] for r in records if not r["error"] and r["ttft_ms"] is not None]
    output_tokens = sum((r.get("usage") or {}).get("completion_tokens") or 0 for r in records)
    summary: dict[str, Any] = {
        "requests": len(records),
        "completed": sum(not r["error"] for r in records),
        "errors": sum(bool(r["error"]) for r in records),
        "wall_s": wall_s,
        "requests_per_s": len(records) / wall_s if wall_s else None,
        "completion_tokens": output_tokens,
        "output_tokens_per_s": output_tokens / wall_s if wall_s and output_tokens else None,
        "e2e_ms": {
            "mean": statistics.fmean(e2e) if e2e else None,
            "p50": percentile(e2e, 0.50),
            "p95": percentile(e2e, 0.95),
            "p99": percentile(e2e, 0.99),
        },
        "ttft_ms": {
            "mean": statistics.fmean(ttft) if ttft else None,
            "p50": percentile(ttft, 0.50),
            "p95": percentile(ttft, 0.95),
            "p99": percentile(ttft, 0.99),
        },
    }
    for dataset in ("mmlu", "gsm8k"):
        rows = [r for r in records if r["dataset"] == dataset]
        scored = [r for r in rows if r["correct"] is not None and not r["error"]]
        summary[dataset] = {
            "n": len(rows),
            "scored": len(scored),
            "accuracy": sum(bool(r["correct"]) for r in scored) / len(scored) if scored else None,
        }
    summary["humaneval"] = {
        "n": sum(r["dataset"] == "humaneval" for r in records),
        "pass_at_1": None,
        "note": "score with score_humaneval_sandbox.py",
    }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8200")
    parser.add_argument("--model", default="qwen38")
    parser.add_argument("--data-dir", default="/cache/austinov/eval-data/general/prepared")
    parser.add_argument("--output", required=False)
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--mmlu-per-subject", type=int, default=5)
    parser.add_argument("--gsm8k-limit", type=int, default=64)
    parser.add_argument("--humaneval-limit", type=int, default=164)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        assert parse_mmlu("B") == "B"
        assert parse_mmlu("Answer: C.") == "C"
        assert parse_gsm8k("work\n#### 1,234") == "1234"
        assert abs(float(parse_gsm8k("answer is -2.5")) + 2.5) < 1e-9
        print("self-test: PASS")
        return 0
    if not args.output:
        parser.error("--output is required unless --self-test is used")

    data_dir = Path(args.data_dir)
    mmlu, mmlu_warmups = load_mmlu(data_dir, args.mmlu_per_subject)
    gsm8k, gsm8k_warmups = load_gsm8k(data_dir, args.gsm8k_limit)
    humaneval, humaneval_warmups = load_humaneval(data_dir, args.humaneval_limit)
    for case in [*mmlu_warmups, *gsm8k_warmups, *humaneval_warmups]:
        warmup = stream_completion(args.base_url, args.model, case, args.timeout)
        if warmup["error"]:
            raise RuntimeError(f"warmup failed for {case.key}: {warmup['error']}")

    cases = [*mmlu, *gsm8k, *humaneval]
    records: list[dict[str, Any]] = []
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = {pool.submit(stream_completion, args.base_url, args.model, case, args.timeout): case for case in cases}
        for i, future in enumerate(as_completed(futures), start=1):
            records.append(future.result())
            if i % 50 == 0:
                print(f"completed {i}/{len(cases)}", flush=True)
    wall_s = time.perf_counter() - start
    records.sort(key=lambda r: (r["dataset"], r["key"]))
    result = {
        "schema": "qwen38-general-eval/v1",
        "endpoint": args.base_url,
        "model": args.model,
        "protocol": {
            "concurrency": args.concurrency,
            "mmlu_per_subject": args.mmlu_per_subject,
            "gsm8k_limit": args.gsm8k_limit,
            "humaneval_limit": args.humaneval_limit,
            "temperature": 0,
            "mmlu_fewshot": 5,
            "gsm8k_fewshot": 8,
        },
        "summary": summarize(records, wall_s),
        "records": records,
    }
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 1 if result["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Measure one reproducible query_rewrite serving cell via OpenAI streaming.

The runner keeps prompts and generated text in memory only.  Its JSON artifact
contains latency distributions, completion metadata, and SHA256 identifiers so
BF16 and NVFP4 service runs can be compared without copying private traffic
into Git.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import math
import statistics
import time
import urllib.request
from pathlib import Path


ALLOWED_CONCURRENCY = (1, 5, 8, 16)


def percentile(values: list[float], quantile: float) -> float:
    if not values:
        raise ValueError("cannot summarize empty values")
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def summarize(values: list[float]) -> dict[str, float]:
    return {
        "mean": statistics.fmean(values),
        "p50": percentile(values, 0.50),
        "p95": percentile(values, 0.95),
        "p99": percentile(values, 0.99),
        "min": min(values),
        "max": max(values),
    }


def read_questions(dataset: Path, limit: int) -> list[str]:
    questions: list[str] = []
    with dataset.open(encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip():
                continue
            question = json.loads(line).get("question")
            if not isinstance(question, str) or not question:
                raise ValueError(f"dataset row {line_no} has no non-empty question")
            questions.append(question)
            if len(questions) == limit:
                break
    if len(questions) != limit:
        raise ValueError(f"expected {limit} questions, found {len(questions)}")
    return questions


def post_json(url: str, payload: dict[str, object], timeout: float):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    return urllib.request.urlopen(request, timeout=timeout)


def token_budget(base_url: str, model: str, prompt: str, timeout: float) -> int:
    with post_json(
        base_url.rstrip("/") + "/tokenize", {"model": model, "prompt": prompt}, timeout
    ) as response:
        tokenized = json.load(response)
    remaining = int(tokenized["max_model_len"]) - int(tokenized["count"])
    if remaining < 1:
        raise ValueError("prompt has no remaining generation capacity")
    return remaining


def one_request(
    base_url: str,
    model: str,
    prompt: str,
    max_tokens: int,
    seed: int,
    timeout: float,
    cache_salt: str,
) -> dict[str, object]:
    payload = {
        "model": model,
        "prompt": prompt,
        "temperature": 0,
        "seed": seed,
        "max_tokens": max_tokens,
        "stream": True,
        "stream_options": {"include_usage": True},
        "cache_salt": cache_salt,
    }
    started = time.perf_counter()
    first_token_at: float | None = None
    output: list[str] = []
    completion_tokens: int | None = None
    prompt_tokens: int | None = None
    finish_reason: str | None = None
    with post_json(base_url.rstrip("/") + "/v1/completions", payload, timeout) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8").strip()
            if not line.startswith("data:"):
                continue
            event = line[5:].strip()
            if event == "[DONE]":
                break
            row = json.loads(event)
            usage = row.get("usage")
            if usage:
                prompt_tokens = usage.get("prompt_tokens", prompt_tokens)
                completion_tokens = usage.get("completion_tokens", completion_tokens)
            for choice in row.get("choices", []):
                if first_token_at is None:
                    first_token_at = time.perf_counter()
                text = choice.get("text")
                if text:
                    output.append(text)
                if choice.get("finish_reason") is not None:
                    finish_reason = str(choice["finish_reason"])
    ended = time.perf_counter()
    if first_token_at is None or not completion_tokens or completion_tokens < 1:
        raise RuntimeError("stream lacks a positive completion-token event")
    return {
        "ttft_ms": (first_token_at - started) * 1000,
        "tpot_ms": (ended - first_token_at) * 1000 / max(completion_tokens - 1, 1),
        "e2e_ms": (ended - started) * 1000,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "finish_reason": finish_reason,
        "response_sha256": hashlib.sha256("".join(output).encode("utf-8")).hexdigest(),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--dataset-sha256", required=True)
    parser.add_argument("--concurrency", type=int, choices=ALLOWED_CONCURRENCY, required=True)
    parser.add_argument("--repeat-index", type=int, choices=(1, 2, 3), required=True)
    parser.add_argument("--requests", type=int, default=32)
    parser.add_argument("--seed", type=int, default=1024)
    parser.add_argument("--timeout", type=float, default=600)
    parser.add_argument("--cache-salt-prefix", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset_hash = hashlib.sha256(args.dataset.read_bytes()).hexdigest()
    if dataset_hash != args.dataset_sha256:
        raise ValueError(f"dataset SHA256 mismatch: {dataset_hash}")
    questions = read_questions(args.dataset, args.requests)
    budgets = [token_budget(args.base_url, args.model, prompt, args.timeout) for prompt in questions]
    warmup = one_request(
        args.base_url, args.model, questions[0], budgets[0], args.seed, args.timeout,
        f"{args.cache_salt_prefix}:c{args.concurrency}:r{args.repeat_index}:warmup",
    )
    if warmup["finish_reason"] != "stop":
        raise RuntimeError("warmup did not stop naturally")
    started = time.perf_counter()
    rows: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [
            pool.submit(
                one_request, args.base_url, args.model, prompt, budgets[index],
                args.seed, args.timeout,
                f"{args.cache_salt_prefix}:c{args.concurrency}:r{args.repeat_index}:i{index}",
            )
            for index, prompt in enumerate(questions)
        ]
        for index, future in enumerate(futures):
            try:
                rows.append(future.result())
            except Exception as exc:
                failures.append({
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "question_sha256": hashlib.sha256(questions[index].encode("utf-8")).hexdigest(),
                })
    wall_s = time.perf_counter() - started
    if not rows:
        raise RuntimeError(f"all requests failed: {failures}")
    finish_reasons: dict[str, int] = {}
    for row in rows:
        reason = str(row["finish_reason"])
        finish_reasons[reason] = finish_reasons.get(reason, 0) + 1
    report = {
        "schema": "qwen38-query-rewrite-benchmark/v1",
        "base_url": args.base_url,
        "model": args.model,
        "dataset": str(args.dataset),
        "dataset_sha256": dataset_hash,
        "concurrency": args.concurrency,
        "repeat_index": args.repeat_index,
        "requests": args.requests,
        "completed": len(rows),
        "errors": len(failures),
        "failure_summary": failures,
        "seed": args.seed,
        "temperature": 0,
        "natural_eos": True,
        "prefix_cache_isolation": True,
        "cache_salt_prefix": args.cache_salt_prefix,
        "wall_s": wall_s,
        "request_throughput": len(rows) / wall_s,
        "output_token_throughput": sum(int(row["completion_tokens"]) for row in rows) / wall_s,
        "ttft_ms": summarize([float(row["ttft_ms"]) for row in rows]),
        "tpot_ms": summarize([float(row["tpot_ms"]) for row in rows]),
        "e2e_ms": summarize([float(row["e2e_ms"]) for row in rows]),
        "finish_reasons": finish_reasons,
        "response_sha256": [row["response_sha256"] for row in rows],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "response_sha256"}, sort_keys=True))
    return 0 if not failures and finish_reasons == {"stop": len(rows)} else 2


if __name__ == "__main__":
    raise SystemExit(main())

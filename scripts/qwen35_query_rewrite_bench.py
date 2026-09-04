#!/usr/bin/env python3
"""Benchmark OpenAI-compatible chat serving with frozen query_rewrite inputs.

The output contains metrics and response hashes, never raw questions or model
responses. One invocation measures one concurrency/repetition cell.
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


def percentile(values: list[float], quantile: float) -> float:
    if not values:
        raise ValueError("cannot summarize an empty metric")
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def summarize(values: list[float]) -> dict[str, float]:
    return {
        "mean": statistics.fmean(values),
        "p50": percentile(values, 0.50),
        "p95": percentile(values, 0.95),
        "p99": percentile(values, 0.99),
        "min": min(values),
        "max": max(values),
    }


def load_questions(path: Path, limit: int) -> list[str]:
    questions: list[str] = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            question = row.get("question")
            if not isinstance(question, str) or not question:
                raise ValueError(f"record {line_number} has no non-empty question")
            questions.append(question)
            if limit and len(questions) >= limit:
                break
    if not questions:
        raise ValueError("dataset contains no questions")
    return questions


def token_info(
    base_url: str,
    model: str,
    question: str,
    timeout: float,
) -> tuple[int, int]:
    payload = {"model": model, "prompt": question}
    request = urllib.request.Request(
        base_url.rstrip("/") + "/tokenize",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=min(timeout, 120)) as response:
        result = json.load(response)
    prompt_tokens = int(result["count"])
    max_model_len = int(result["max_model_len"])
    remaining = max_model_len - prompt_tokens
    if remaining <= 0:
        raise ValueError("prompt exceeds model context")
    return prompt_tokens, remaining


def request_one(
    base_url: str,
    model: str,
    question: str,
    max_tokens: int,
    seed: int,
    timeout: float,
) -> dict[str, object]:
    payload = {
        "model": model,
        "prompt": question,
        "temperature": 0,
        "seed": seed,
        "max_tokens": max_tokens,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    request = urllib.request.Request(
        base_url.rstrip("/") + "/v1/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    started = time.perf_counter()
    first_content_at: float | None = None
    output_parts: list[str] = []
    completion_tokens: int | None = None
    prompt_tokens: int | None = None
    finish_reason: str | None = None
    with urllib.request.urlopen(request, timeout=timeout) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8").strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            event = json.loads(data)
            usage = event.get("usage")
            if usage:
                prompt_tokens = usage.get("prompt_tokens", prompt_tokens)
                completion_tokens = usage.get(
                    "completion_tokens", completion_tokens
                )
            for choice in event.get("choices", []):
                content = choice.get("text")
                if content:
                    if first_content_at is None:
                        first_content_at = time.perf_counter()
                    output_parts.append(content)
                if choice.get("finish_reason") is not None:
                    finish_reason = str(choice["finish_reason"])
    ended = time.perf_counter()
    if first_content_at is None:
        raise RuntimeError("stream completed without content")
    if not completion_tokens or completion_tokens < 1:
        raise RuntimeError("stream did not report positive completion_tokens")
    ttft_s = first_content_at - started
    generation_s = ended - first_content_at
    tpot_s = generation_s / max(completion_tokens - 1, 1)
    output = "".join(output_parts)
    return {
        "ttft_ms": ttft_s * 1000,
        "tpot_ms": tpot_s * 1000,
        "e2e_ms": (ended - started) * 1000,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "finish_reason": finish_reason,
        "response_sha256": hashlib.sha256(output.encode()).hexdigest(),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--dataset-sha256", required=True)
    parser.add_argument("--concurrency", type=int, required=True)
    parser.add_argument("--repeat-index", type=int, choices=(1, 2, 3), required=True)
    parser.add_argument("--seed", type=int, default=1024)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--timeout", type=float, default=600)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.concurrency not in (1, 5, 8, 16):
        raise ValueError("concurrency must be one of 1, 5, 8, 16")
    actual_hash = hashlib.sha256(args.dataset.read_bytes()).hexdigest()
    if actual_hash != args.dataset_sha256:
        raise ValueError(
            f"dataset SHA256 mismatch: expected {args.dataset_sha256}, "
            f"got {actual_hash}"
        )
    questions = load_questions(args.dataset, args.limit)
    token_limits = [
        token_info(args.base_url, args.model, question, args.timeout)
        for question in questions
    ]
    warmup = request_one(
        args.base_url,
        args.model,
        questions[0],
        token_limits[0][1],
        args.seed,
        args.timeout,
    )
    if warmup["finish_reason"] != "stop":
        raise RuntimeError("warmup did not terminate naturally")
    started = time.perf_counter()
    results: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=args.concurrency
    ) as executor:
        futures = [
            executor.submit(
                request_one,
                args.base_url,
                args.model,
                question,
                token_limits[index][1],
                args.seed,
                args.timeout,
            )
            for index, question in enumerate(questions)
        ]
        for index, future in enumerate(futures):
            try:
                results.append(future.result())
            except Exception as exc:  # Preserve count/type without prompt data.
                errors.append(
                    {
                        "type": type(exc).__name__,
                        "reason": str(exc),
                        "question_sha256": hashlib.sha256(
                            questions[index].encode()
                        ).hexdigest(),
                    }
                )
    wall_s = time.perf_counter() - started
    if not results:
        raise RuntimeError(f"all requests failed: {errors}")
    completion_tokens = sum(int(row["completion_tokens"]) for row in results)
    finish_reasons: dict[str, int] = {}
    for row in results:
        reason = str(row["finish_reason"])
        finish_reasons[reason] = finish_reasons.get(reason, 0) + 1
    report = {
        "schema": "qwen35-query-rewrite-benchmark/v1",
        "base_url": args.base_url,
        "model": args.model,
        "dataset": str(args.dataset),
        "dataset_sha256": actual_hash,
        "requests": len(questions),
        "completed": len(results),
        "errors": len(errors),
        "error_types": sorted({row["type"] for row in errors}),
        "error_reasons": {
            reason: sum(row["reason"] == reason for row in errors)
            for reason in sorted({row["reason"] for row in errors})
        },
        "failed_question_sha256": [
            row["question_sha256"] for row in errors
        ],
        "concurrency": args.concurrency,
        "repeat_index": args.repeat_index,
        "max_tokens": "per-request model context remainder",
        "natural_eos": True,
        "seed": args.seed,
        "wall_s": wall_s,
        "request_throughput": len(results) / wall_s,
        "output_token_throughput": completion_tokens / wall_s,
        "ttft_ms": summarize([float(row["ttft_ms"]) for row in results]),
        "tpot_ms": summarize([float(row["tpot_ms"]) for row in results]),
        "e2e_ms": summarize([float(row["e2e_ms"]) for row in results]),
        "prompt_tokens": sum(
            int(row["prompt_tokens"] or 0) for row in results
        ),
        "completion_tokens": completion_tokens,
        "finish_reasons": finish_reasons,
        "pretokenized_prompt_tokens": summarize(
            [float(item[0]) for item in token_limits]
        ),
        "response_sha256": [row["response_sha256"] for row in results],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({k: v for k, v in report.items() if k != "response_sha256"}))
    valid = not errors and finish_reasons == {"stop": len(results)}
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())

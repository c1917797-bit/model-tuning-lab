#!/usr/bin/env python3
"""Deterministic OpenAI-compatible fixed-output serving screen.

This harness deliberately uses prompt token IDs so input length and the shared
prefix boundary are exact and independent of tokenizer text normalization.
It records every request, TTFT, end-to-end duration, output-token count, and
output digest.  A result is accepted only when all requests finish with exactly
the requested number of output tokens.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import statistics
import time
from pathlib import Path
from typing import Any

import aiohttp


def _prompt(index: int, input_tokens: int, prefix_tokens: int) -> list[int]:
    if not 0 < prefix_tokens <= input_tokens:
        raise ValueError("prefix_tokens must be in (0, input_tokens]")
    prefix = [1000 + (i % 257) for i in range(prefix_tokens)]
    suffix = [
        2000 + ((index * 131 + i * 17) % 4093)
        for i in range(input_tokens - prefix_tokens)
    ]
    return prefix + suffix


async def _one(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    *,
    base_url: str,
    model: str,
    index: int,
    input_tokens: int,
    prefix_tokens: int,
    output_tokens: int,
    timeout_s: float,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "prompt": _prompt(index, input_tokens, prefix_tokens),
        "max_tokens": output_tokens,
        "min_tokens": output_tokens,
        "temperature": 0,
        "seed": 0,
        "ignore_eos": True,
        "stream": True,
        "stream_options": {"include_usage": True},
        "vllm_xargs": {
            # OpenAI protocol constrains vllm_xargs values to scalars. Keep the
            # established transport name and encode the two boundaries as JSON.
            "hypic_segment_ends": json.dumps([prefix_tokens, input_tokens]),
        },
    }
    started = time.perf_counter()
    first_token_at: float | None = None
    text_parts: list[str] = []
    streamed_chunks = 0
    usage_tokens: int | None = None
    finish_reason: str | None = None
    error: str | None = None

    try:
        async with semaphore:
            async with session.post(
                f"{base_url.rstrip('/')}/v1/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout_s),
            ) as response:
                if response.status >= 400:
                    body = await response.text()
                    raise RuntimeError(
                        f"HTTP {response.status}: {body[:2000]}"
                    )
                while True:
                    raw = await response.content.readline()
                    if not raw:
                        break
                    line = raw.decode("utf-8", errors="replace").strip()
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if not data or data == "[DONE]":
                        continue
                    chunk = json.loads(data)
                    usage = chunk.get("usage")
                    if usage and usage.get("completion_tokens") is not None:
                        usage_tokens = int(usage["completion_tokens"])
                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    choice = choices[0]
                    piece = choice.get("text") or ""
                    if piece:
                        if first_token_at is None:
                            first_token_at = time.perf_counter()
                        text_parts.append(piece)
                        streamed_chunks += 1
                    if choice.get("finish_reason") is not None:
                        finish_reason = str(choice["finish_reason"])
    except Exception as exc:  # preserve the first failure in the report
        error = f"{type(exc).__name__}: {exc}"

    ended = time.perf_counter()
    observed_tokens = usage_tokens if usage_tokens is not None else streamed_chunks
    text = "".join(text_parts)
    return {
        "index": index,
        "ok": error is None and observed_tokens == output_tokens,
        "error": error,
        "duration_s": ended - started,
        "ttft_ms": (
            (first_token_at - started) * 1000.0
            if first_token_at is not None
            else None
        ),
        "output_tokens": observed_tokens,
        "streamed_chunks": streamed_chunks,
        "requested_output_tokens": output_tokens,
        "finish_reason": finish_reason,
        "output_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return float("nan")
    position = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * fraction)))
    return ordered[position]


async def _run(args: argparse.Namespace) -> dict[str, Any]:
    output = Path(args.output)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    progress = output.with_suffix(output.suffix + ".progress")
    semaphore = asyncio.Semaphore(args.concurrency)
    connector = aiohttp.TCPConnector(limit=args.concurrency + args.warmup_requests)

    async with aiohttp.ClientSession(connector=connector) as session:
        warmups = await asyncio.gather(
            *[
                _one(
                    session,
                    semaphore,
                    base_url=args.base_url,
                    model=args.model,
                    index=-(i + 1),
                    input_tokens=args.input_tokens,
                    prefix_tokens=args.prefix_tokens,
                    output_tokens=1,
                    timeout_s=args.timeout_s,
                )
                for i in range(args.warmup_requests)
            ]
        )
        if not all(item["ok"] for item in warmups):
            raise RuntimeError(f"warmup failed: {warmups}")

        benchmark_started = time.perf_counter()
        tasks = [
            asyncio.create_task(
                _one(
                    session,
                    semaphore,
                    base_url=args.base_url,
                    model=args.model,
                    index=i,
                    input_tokens=args.input_tokens,
                    prefix_tokens=args.prefix_tokens,
                    output_tokens=args.output_tokens,
                    timeout_s=args.timeout_s,
                )
            )
            for i in range(args.requests)
        ]
        completed: list[dict[str, Any]] = []
        for future in asyncio.as_completed(tasks):
            completed.append(await future)
            progress.write_text(
                json.dumps(
                    {
                        "completed": len(completed),
                        "successful": sum(x["ok"] for x in completed),
                        "failed": sum(not x["ok"] for x in completed),
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
        benchmark_duration = time.perf_counter() - benchmark_started

    results = sorted(completed, key=lambda item: item["index"])
    successful = [item for item in results if item["ok"]]
    durations_ms = [item["duration_s"] * 1000.0 for item in successful]
    ttfts = [float(item["ttft_ms"]) for item in successful]
    decode_ms = [
        item["duration_s"] * 1000.0 - float(item["ttft_ms"])
        for item in successful
    ]
    decode_intervals = [
        max(0, int(item["output_tokens"]) - 1) for item in successful
    ]
    total_output = sum(int(item["output_tokens"]) for item in successful)
    total_intervals = sum(decode_intervals)
    weighted_tpot = (
        sum(decode_ms) / total_intervals if total_intervals else float("nan")
    )
    summary = {
        "requests": args.requests,
        "successful": len(successful),
        "failed": args.requests - len(successful),
        "fixed_output_requests": sum(
            int(item["output_tokens"]) == args.output_tokens for item in successful
        ),
        "fixed_output_verified": (
            len(successful) == args.requests
            and all(
                int(item["output_tokens"]) == args.output_tokens
                for item in successful
            )
        ),
        "expected_output_tokens": args.requests * args.output_tokens,
        "output_tokens": total_output,
        "output_token_completion_ratio": (
            total_output / (args.requests * args.output_tokens)
        ),
        "benchmark_duration_s": benchmark_duration,
        "output_tokens_per_second": total_output / benchmark_duration,
        "measured_concurrency": args.concurrency,
        "measured_waves": (args.requests + args.concurrency - 1)
        // args.concurrency,
        "ttft_mean_ms": statistics.fmean(ttfts) if ttfts else float("nan"),
        "ttft_median_ms": statistics.median(ttfts) if ttfts else float("nan"),
        "ttft_p95_ms": _percentile(ttfts, 0.95),
        "ttft_max_ms": max(ttfts) if ttfts else float("nan"),
        "tpot_weighted_ms": weighted_tpot,
        "tpot_mean_ms": weighted_tpot,
        "request_duration_mean_ms": (
            statistics.fmean(durations_ms) if durations_ms else float("nan")
        ),
        "request_duration_median_ms": (
            statistics.median(durations_ms) if durations_ms else float("nan")
        ),
        "request_duration_p95_ms": _percentile(durations_ms, 0.95),
        "request_duration_max_ms": (
            max(durations_ms) if durations_ms else float("nan")
        ),
    }
    report = {
        "config": {
            "base_url": args.base_url,
            "model": args.model,
            "requests": args.requests,
            "concurrency": args.concurrency,
            "input_tokens": args.input_tokens,
            "prefix_tokens": args.prefix_tokens,
            "output_tokens": args.output_tokens,
            "ignore_eos": True,
            "prompt_transport": "exact_token_ids",
            "prompt_generator": "fixed-prefix-v1",
            "segment_ends": [args.prefix_tokens, args.input_tokens],
            "warmup_requests": args.warmup_requests,
            "profiler_enabled": False,
        },
        "warmup_results": warmups,
        "results": results,
        "summary": summary,
    }
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, output)
    progress.unlink(missing_ok=True)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--requests", type=int, default=40)
    parser.add_argument("--concurrency", type=int, default=16)
    parser.add_argument("--input-tokens", type=int, default=32768)
    parser.add_argument("--prefix-tokens", type=int, default=16384)
    parser.add_argument("--output-tokens", type=int, default=1024)
    parser.add_argument("--warmup-requests", type=int, default=2)
    parser.add_argument("--timeout-s", type=float, default=1200.0)
    args = parser.parse_args()
    report = asyncio.run(_run(args))
    print(json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()

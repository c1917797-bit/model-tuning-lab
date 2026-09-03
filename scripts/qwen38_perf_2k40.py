#!/usr/bin/env python3
"""Fixed-shape 2048-input-token / 40-output-token vLLM performance benchmark."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    pos = (len(xs) - 1) * p
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return xs[lo]
    return xs[lo] * (hi - pos) + xs[hi] * (pos - lo)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_snapshot(path: Path) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if not rows:
        raise RuntimeError("Empty performance snapshot")
    bad = [r for r in rows if r.get("input_tokens") != 2048]
    if bad:
        raise RuntimeError(f"Snapshot contains non-2048-token prompts: {len(bad)}")
    return rows


def stream_completion(base_url: str, model: str, row: dict, timeout: float) -> dict:
    body = {
        "model": model,
        "prompt": row["prompt_token_ids"],
        "temperature": 0,
        "max_tokens": 40,
        "min_tokens": 40,
        "ignore_eos": True,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    request = urllib.request.Request(
        base_url.rstrip("/") + "/v1/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    start = time.perf_counter()
    first = None
    usage = {}
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
                    if choice.get("text") and first is None:
                        first = time.perf_counter()
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    end = time.perf_counter()
    if not error:
        if usage.get("prompt_tokens") != 2048:
            error = f"protocol prompt_tokens={usage.get('prompt_tokens')} expected=2048"
        elif usage.get("completion_tokens") != 40:
            error = f"protocol completion_tokens={usage.get('completion_tokens')} expected=40"
    return {
        "dataset": row["dataset"],
        "key": row["key"],
        "ttft_ms": (first - start) * 1000 if first is not None else None,
        "e2e_ms": (end - start) * 1000,
        "usage": usage,
        "error": error,
    }


def metric(values: list[float]) -> dict:
    return {
        "mean": statistics.fmean(values),
        "p50": percentile(values, 0.50),
        "p95": percentile(values, 0.95),
        "p99": percentile(values, 0.99),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", default="http://127.0.0.1:8200")
    p.add_argument("--model", default="qwen38")
    p.add_argument("--snapshot", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--concurrency", type=int, default=8)
    p.add_argument("--timeout", type=float, default=180.0)
    args = p.parse_args()

    snapshot = Path(args.snapshot)
    rows = load_snapshot(snapshot)

    # Warm one request from each dataset without including it in the measured window.
    seen = set()
    for row in rows:
        if row["dataset"] in seen:
            continue
        seen.add(row["dataset"])
        result = stream_completion(args.base_url, args.model, row, args.timeout)
        if result["error"]:
            raise RuntimeError(f"warmup failed: {result['error']}")

    records = []
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = {pool.submit(stream_completion, args.base_url, args.model, row, args.timeout): row for row in rows}
        for i, future in enumerate(as_completed(futures), start=1):
            records.append(future.result())
            if i % 50 == 0:
                print(f"completed {i}/{len(rows)}", flush=True)
    wall_s = time.perf_counter() - start
    records.sort(key=lambda r: (r["dataset"], r["key"]))

    good = [r for r in records if not r["error"]]
    ttft = [r["ttft_ms"] for r in good if r["ttft_ms"] is not None]
    e2e = [r["e2e_ms"] for r in good]
    input_tokens = sum(r["usage"].get("prompt_tokens", 0) for r in good)
    output_tokens = sum(r["usage"].get("completion_tokens", 0) for r in good)
    summary = {
        "requests": len(records),
        "completed": len(good),
        "errors": len(records) - len(good),
        "wall_s": wall_s,
        "requests_per_s": len(good) / wall_s if wall_s else None,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_tokens_per_s": input_tokens / wall_s if wall_s else None,
        "output_tokens_per_s": output_tokens / wall_s if wall_s else None,
        "total_tokens_per_s": (input_tokens + output_tokens) / wall_s if wall_s else None,
        "ttft_ms": metric(ttft),
        "e2e_ms": metric(e2e),
    }
    result = {
        "schema": "qwen38-perf-2k40/v1",
        "endpoint": args.base_url,
        "model": args.model,
        "protocol": {
            "input_tokens": 2048,
            "output_tokens": 40,
            "concurrency": args.concurrency,
            "temperature": 0,
            "ignore_eos": True,
            "snapshot_sha256": sha256(snapshot),
        },
        "summary": summary,
        "records": records,
    }
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

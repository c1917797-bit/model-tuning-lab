#!/usr/bin/env python3
"""Exact dense eager prefix-hit control for the v12r28 discriminator."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
import urllib.request


def post(base_url: str, payload: dict) -> tuple[dict, float]:
    request = urllib.request.Request(
        base_url + "/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    started = time.perf_counter_ns()
    with urllib.request.urlopen(request, timeout=900) as response:
        body = json.loads(response.read().decode())
    return body, (time.perf_counter_ns() - started) / 1e6


def metric_sum(base_url: str, needle: str) -> float:
    with urllib.request.urlopen(base_url + "/metrics", timeout=30) as response:
        lines = response.read().decode().splitlines()
    return sum(
        float(line.rsplit(" ", 1)[1])
        for line in lines
        if needle in line and not line.startswith("#")
    )


def exact_verified(run: dict) -> bool:
    return (
        run.get("content") == "VERIFIED"
        and run.get("finish_reason") == "stop"
        and run.get("reasoning_content") is None
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8030")
    parser.add_argument("--model", default="/models/Qwen3.6-27B")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--activation", type=Path, required=True)
    args = parser.parse_args()

    prefix = "\n".join(
        "Record "
        f"{index:04d}: DASC recurrent-state reuse must preserve exact "
        "deterministic semantics."
        for index in range(100)
    )
    prompt = prefix + "\nQuestion: Return exactly the word VERIFIED."
    payload = {
        "model": args.model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Follow the requested exact output. Do not show hidden "
                    "reasoning."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "seed": 0,
        "max_tokens": 16,
        "stream": False,
        "chat_template_kwargs": {"enable_thinking": False},
    }

    before = metric_sum(args.base_url, "prefix_cache_hits_total")
    runs = []
    for _ in range(3):
        body, elapsed_ms = post(args.base_url, payload)
        choice = body["choices"][0]
        message = choice["message"]
        runs.append(
            {
                "content": message.get("content"),
                "finish_reason": choice.get("finish_reason"),
                "reasoning_content": message.get("reasoning"),
                "usage": body.get("usage"),
                "elapsed_ms": elapsed_ms,
            }
        )

    hit_delta = metric_sum(args.base_url, "prefix_cache_hits_total") - before
    contents = [run["content"] for run in runs]
    result = {
        "schema": "mst.dasc.dense-eager-replay-control/v1",
        "execution_mode": "eager",
        "runs": runs,
        "identical_replays": len(set(contents)) == 1,
        "exact_verified_replays": all(exact_verified(run) for run in runs),
        "prefix_cache_hit_delta": hit_delta,
        "prefix_cache_hit_observed": hit_delta > 0,
    }
    result["ok"] = (
        result["identical_replays"]
        and result["exact_verified_replays"]
        and result["prefix_cache_hit_observed"]
    )
    path = args.output_dir / "dense-eager-replay-control.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

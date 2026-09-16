#!/usr/bin/env python3
"""Strict DASC physical-cache reachability and semantic canary."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import time
import urllib.error
import urllib.request


def atomic_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def get(base_url: str, path: str, timeout: int = 30) -> str:
    with urllib.request.urlopen(base_url + path, timeout=timeout) as response:
        return response.read().decode("utf-8")


def post(base_url: str, path: str, payload: dict, timeout: int = 900) -> tuple[dict, float]:
    request = urllib.request.Request(
        base_url + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    started = time.perf_counter_ns()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {error.code}: {raw}") from error
    return json.loads(raw), (time.perf_counter_ns() - started) / 1e6


def metrics(base_url: str) -> dict[str, float]:
    selected: dict[str, float] = {}
    needles = (
        "prefix_cache_queries_total",
        "prefix_cache_hits_total",
        "prompt_tokens_cached_total",
        "request_success_total",
        "prompt_tokens_total",
        "generation_tokens_total",
    )
    for line in get(base_url, "/metrics").splitlines():
        if line.startswith("#") or not any(needle in line for needle in needles):
            continue
        name, value = line.rsplit(" ", 1)
        selected[name] = float(value)
    return selected


def metric_sum(snapshot: dict[str, float], needle: str) -> float:
    return sum(value for name, value in snapshot.items() if needle in name)


def request_record(base_url: str, model: str, prompt: str, max_tokens: int = 16) -> dict:
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "Follow the requested exact output. Do not show hidden reasoning.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "seed": 0,
        "max_tokens": max_tokens,
        "stream": False,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    body, elapsed_ms = post(base_url, "/v1/chat/completions", payload)
    choice = body["choices"][0]
    message = choice["message"]
    return {
        "elapsed_ms": elapsed_ms,
        "content": message.get("content"),
        "reasoning_content": message.get("reasoning_content"),
        "finish_reason": choice.get("finish_reason"),
        "usage": body.get("usage"),
        "response": body,
    }


def exact_stopped(record: dict, expected: str) -> bool:
    return record.get("content") == expected and record.get("finish_reason") == "stop"


def load_activation(path: Path) -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    errors: list[str] = []
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            errors.append(f"line {index}: {error}")
            continue
        if not isinstance(value, dict):
            errors.append(f"line {index}: expected object")
            continue
        rows.append(value)
    return rows, errors


def activation_summary(
    rows: list[dict], parse_errors: list[str], *, allow_dense_pages: bool = False
) -> dict:
    counts = Counter(row.get("event") for row in rows)
    physical = [row for row in rows if row.get("event") == "physical_cache_bound"]

    def pids(event: str) -> list[int]:
        return sorted(
            {
                row["pid"]
                for row in rows
                if row.get("event") == event and isinstance(row.get("pid"), int)
            }
        )

    page_relation_ok = bool(physical) and all(
        isinstance(row.get("compact_page_bytes"), int)
        and isinstance(row.get("dense_page_bytes"), int)
        and (
            row["compact_page_bytes"] <= row["dense_page_bytes"]
            if allow_dense_pages
            else row["compact_page_bytes"] < row["dense_page_bytes"]
        )
        for row in physical
    )
    positive_blocks = bool(physical) and all(
        isinstance(row.get("num_blocks"), int) and row["num_blocks"] > 0
        for row in physical
    )
    physical_pids = pids("physical_cache_bound")
    geometry_pids = pids("tp_geometry_aligned")
    dispatch_pids = pids("worker_dispatch_verified")
    worker_cohort_aligned = (
        len(physical_pids) == 4
        and physical_pids == geometry_pids
        and physical_pids == dispatch_pids
    )
    summary = {
        "row_count": len(rows),
        "parse_errors": parse_errors,
        "event_counts": dict(sorted(counts.items(), key=lambda pair: str(pair[0]))),
        "physical_cache_pids": physical_pids,
        "tp_geometry_pids": geometry_pids,
        "worker_dispatch_pids": dispatch_pids,
        "worker_cohort_aligned": worker_cohort_aligned,
        "compact_lt_dense": page_relation_ok and not allow_dense_pages,
        "page_relation_ok": page_relation_ok,
        "allow_dense_pages": allow_dense_pages,
        "positive_blocks": positive_blocks,
        "aggregate_compact_page_bytes": sum(
            row.get("compact_page_bytes", 0) for row in physical
        ),
        "aggregate_dense_page_bytes": sum(
            row.get("dense_page_bytes", 0) for row in physical
        ),
    }
    summary["ok"] = (
        not parse_errors
        and worker_cohort_aligned
        and (
            counts["aligned_hybrid_cache_grouped"] >= 1
            if allow_dense_pages
            else counts["heterogeneous_cache_grouped"] >= 1
        )
        and page_relation_ok
        and positive_blocks
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8030")
    parser.add_argument("--model", default="/models/Qwen3.6-27B")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--activation", type=Path, required=True)
    parser.add_argument("--allow-dense-pages", action="store_true")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    result: dict = {
        "schema": "mst.dasc.physical-canary/v1",
        "base_url": args.base_url,
        "model": args.model,
        "started_ns": time.time_ns(),
        "runs": [],
    }
    exit_code = 1
    try:
        result["metrics_before"] = metrics(args.base_url)
        result["short"] = request_record(
            args.base_url,
            args.model,
            "Return exactly the two uppercase letters OK and nothing else.",
            max_tokens=8,
        )
        prefix = "\n".join(
            f"Record {index:04d}: DASC recurrent-state reuse must preserve exact deterministic semantics."
            for index in range(100)
        )
        prompt = prefix + "\nQuestion: Return exactly the word VERIFIED."
        result["runs"] = [
            request_record(args.base_url, args.model, prompt) for _ in range(3)
        ]
        result["variant"] = request_record(
            args.base_url,
            args.model,
            prefix + "\nQuestion: Return exactly the word ASCEND.",
        )
        result["metrics_after"] = metrics(args.base_url)
        rows, parse_errors = load_activation(args.activation)
        result["activation"] = activation_summary(
            rows, parse_errors, allow_dense_pages=args.allow_dense_pages
        )
        contents = [run["content"] for run in result["runs"]]
        no_reasoning = all(not run["reasoning_content"] for run in result["runs"])
        no_reasoning = no_reasoning and not result["short"]["reasoning_content"]
        no_reasoning = no_reasoning and not result["variant"]["reasoning_content"]
        hit_delta = metric_sum(
            result["metrics_after"], "prefix_cache_hits_total"
        ) - metric_sum(result["metrics_before"], "prefix_cache_hits_total")
        result["gates"] = {
            "short_exact_ok": exact_stopped(result["short"], "OK"),
            "identical_replays": len(set(contents)) == 1,
            "replay_exact_verified": all(
                exact_stopped(run, "VERIFIED") for run in result["runs"]
            ),
            "variant_exact_ascend": exact_stopped(result["variant"], "ASCEND"),
            "reasoning_disabled": no_reasoning,
            "prefix_cache_hit_delta": hit_delta,
            "prefix_cache_hit_observed": hit_delta > 0,
            "activation_ok": result["activation"]["ok"],
        }
        result["ok"] = all(
            value
            for key, value in result["gates"].items()
            if key != "prefix_cache_hit_delta"
        )
        exit_code = 0 if result["ok"] else 1
    except Exception as error:
        result["error"] = repr(error)
        result["ok"] = False
    finally:
        result["finished_ns"] = time.time_ns()
        atomic_json(args.output_dir / "physical-canary.json", result)
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

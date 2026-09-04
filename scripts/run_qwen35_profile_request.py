#!/usr/bin/env python3
"""Capture one isolated real query_rewrite request under the vLLM profiler."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.request
from pathlib import Path

from qwen35_query_rewrite_bench import load_questions, request_one, token_info

SCHEMA = "qwen35-query-rewrite-profile-request/v1"


def post_control(base_url: str, endpoint: str, timeout: float) -> dict:
    request = urllib.request.Request(
        base_url.rstrip("/") + endpoint,
        data=b"",
        method="POST",
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=min(timeout, 120)) as response:
        body = response.read()
        status = int(response.status)
    return {
        "endpoint": endpoint,
        "status": status,
        "duration_ms": (time.perf_counter() - started) * 1000,
        "response_sha256": hashlib.sha256(body).hexdigest(),
    }


def cache_salt(run_id: str, role: str, dataset_sha256: str, index: int) -> str:
    material = f"{run_id}:{role}:{dataset_sha256}:{index}".encode()
    return hashlib.sha256(material).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--dataset-sha256", required=True)
    parser.add_argument("--profile-index", type=int, default=31)
    parser.add_argument("--warmup-index", type=int, default=0)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--seed", type=int, default=1024)
    parser.add_argument("--timeout", type=float, default=600)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    actual_hash = hashlib.sha256(args.dataset.read_bytes()).hexdigest()
    if actual_hash != args.dataset_sha256:
        raise ValueError(
            f"dataset SHA256 mismatch: expected {args.dataset_sha256}, got {actual_hash}"
        )
    questions = load_questions(args.dataset, 0)
    for label, index in (
        ("warmup-index", args.warmup_index),
        ("profile-index", args.profile_index),
    ):
        if not 0 <= index < len(questions):
            raise ValueError(f"{label} is outside dataset")
    if args.warmup_index == args.profile_index:
        raise ValueError("warmup-index and profile-index must differ")
    warmup_question = questions[args.warmup_index]
    profile_question = questions[args.profile_index]
    warmup_hash = hashlib.sha256(warmup_question.encode()).hexdigest()
    profile_hash = hashlib.sha256(profile_question.encode()).hexdigest()
    if warmup_hash == profile_hash:
        raise ValueError("warmup and profile questions must differ")

    warmup_tokens, warmup_max = token_info(
        args.base_url, args.model, warmup_question, args.timeout
    )
    profile_tokens, profile_max = token_info(
        args.base_url, args.model, profile_question, args.timeout
    )
    warmup = request_one(
        args.base_url,
        args.model,
        warmup_question,
        warmup_max,
        args.seed,
        args.timeout,
        cache_salt(
            args.run_id, "warmup", actual_hash, args.warmup_index
        ),
    )
    if warmup["finish_reason"] != "stop":
        raise RuntimeError("warmup did not terminate naturally")

    report = {
        "schema": SCHEMA,
        "performance_evidence": False,
        "performance_note": (
            "Profiler overhead invalidates TTFT/TPOT for acceptance; use only "
            "the frozen non-profile E2E benchmark for performance decisions."
        ),
        "base_url": args.base_url,
        "model": args.model,
        "dataset": str(args.dataset),
        "dataset_sha256": actual_hash,
        "run_id": args.run_id,
        "seed": args.seed,
        "warmup": {
            "record_index": args.warmup_index,
            "question_sha256": warmup_hash,
            "prompt_tokens": warmup_tokens,
            "response_sha256": warmup["response_sha256"],
            "finish_reason": warmup["finish_reason"],
        },
        "profile_request": {
            "record_index": args.profile_index,
            "question_sha256": profile_hash,
            "prompt_tokens": profile_tokens,
            "max_tokens": profile_max,
        },
        "start_profile": None,
        "stop_profile": None,
        "result": None,
        "error_type": None,
    }
    exit_code = 0
    started = False
    try:
        report["start_profile"] = post_control(
            args.base_url, "/start_profile", args.timeout
        )
        started = report["start_profile"]["status"] == 200
        if not started:
            raise RuntimeError("start_profile did not return HTTP 200")
        report["result"] = request_one(
            args.base_url,
            args.model,
            profile_question,
            profile_max,
            args.seed,
            args.timeout,
            cache_salt(
                args.run_id, "profile", actual_hash, args.profile_index
            ),
        )
        if report["result"]["finish_reason"] != "stop":
            raise RuntimeError("profile request did not terminate naturally")
    except Exception as exc:
        report["error_type"] = type(exc).__name__
        exit_code = 2
    finally:
        if started:
            try:
                report["stop_profile"] = post_control(
                    args.base_url, "/stop_profile", args.timeout
                )
                if report["stop_profile"]["status"] != 200:
                    exit_code = 2
            except Exception as exc:
                report["stop_profile"] = {
                    "endpoint": "/stop_profile",
                    "status": None,
                    "error_type": type(exc).__name__,
                }
                exit_code = 2
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    safe = dict(report)
    if safe["result"]:
        safe["result"] = {
            key: value
            for key, value in safe["result"].items()
            if key != "response_sha256"
        }
    print(json.dumps(safe, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

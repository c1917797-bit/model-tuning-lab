#!/usr/bin/env python3
"""Capture deterministic Qwen3.5 outputs for paired quality review.

Unlike the latency benchmark, this diagnostic intentionally stores raw prompts
and responses. Keep its output in the experiment evidence directory with
restricted permissions; do not publish it.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import urllib.request
from pathlib import Path
from typing import Any


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            question = row.get("question")
            if not isinstance(question, str) or not question:
                raise ValueError(
                    f"record {line_number} has no non-empty question"
                )
            rows.append(row)
    if not rows:
        raise ValueError("dataset contains no questions")
    return rows


def stratified_indices(rows: list[dict[str, Any]], count: int) -> list[int]:
    if count < 1:
        raise ValueError("sample count must be positive")
    count = min(count, len(rows))
    ordered = sorted(
        range(len(rows)),
        key=lambda index: (len(rows[index]["question"]), index),
    )
    if count == 1:
        return [ordered[len(ordered) // 2]]
    positions = [
        round(sample * (len(ordered) - 1) / (count - 1))
        for sample in range(count)
    ]
    return [ordered[position] for position in positions]


def post_json(url: str, payload: dict[str, Any], timeout: float):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    return urllib.request.urlopen(request, timeout=timeout)


def token_info(
    base_url: str,
    model: str,
    question: str,
    timeout: float,
) -> tuple[int, int]:
    with post_json(
        base_url.rstrip("/") + "/tokenize",
        {"model": model, "prompt": question},
        min(timeout, 120),
    ) as response:
        result = json.load(response)
    prompt_tokens = int(result["count"])
    remaining = int(result["max_model_len"]) - prompt_tokens
    if remaining <= 0:
        raise ValueError("prompt exceeds model context")
    return prompt_tokens, remaining


def complete(
    base_url: str,
    model: str,
    question: str,
    max_tokens: int,
    seed: int,
    timeout: float,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "prompt": question,
        "temperature": 0,
        "seed": seed,
        "max_tokens": max_tokens,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    output_parts: list[str] = []
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    finish_reason: str | None = None
    with post_json(
        base_url.rstrip("/") + "/v1/completions",
        payload,
        timeout,
    ) as response:
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
                text = choice.get("text")
                if text:
                    output_parts.append(text)
                if choice.get("finish_reason") is not None:
                    finish_reason = str(choice["finish_reason"])
    output = "".join(output_parts)
    if finish_reason != "stop":
        raise RuntimeError(f"completion did not end naturally: {finish_reason}")
    if not completion_tokens or completion_tokens < 1:
        raise RuntimeError("completion did not report positive token usage")
    return {
        "response": output,
        "response_sha256": sha256_text(output),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "finish_reason": finish_reason,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--dataset-sha256", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--sample-count", type=int, default=16)
    parser.add_argument("--seed", type=int, default=1024)
    parser.add_argument("--timeout", type=float, default=600)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    actual_hash = hashlib.sha256(args.dataset.read_bytes()).hexdigest()
    if actual_hash != args.dataset_sha256:
        raise ValueError(
            f"dataset SHA256 mismatch: expected {args.dataset_sha256}, "
            f"got {actual_hash}"
        )
    rows = load_rows(args.dataset)
    selected = stratified_indices(rows, args.sample_count)
    captures = []
    for ordinal, index in enumerate(selected, start=1):
        question = rows[index]["question"]
        prompt_tokens, remaining = token_info(
            args.base_url, args.model, question, args.timeout
        )
        result = complete(
            args.base_url,
            args.model,
            question,
            remaining,
            args.seed,
            args.timeout,
        )
        if result["prompt_tokens"] not in (None, prompt_tokens):
            raise RuntimeError(
                f"token count changed for dataset index {index}: "
                f"{prompt_tokens} != {result['prompt_tokens']}"
            )
        captures.append(
            {
                "ordinal": ordinal,
                "dataset_index": index,
                "question": question,
                "question_sha256": sha256_text(question),
                **result,
            }
        )
        print(
            json.dumps(
                {
                    "ordinal": ordinal,
                    "dataset_index": index,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": result["completion_tokens"],
                    "finish_reason": result["finish_reason"],
                    "response_sha256": result["response_sha256"],
                },
                sort_keys=True,
            ),
            flush=True,
        )
    report = {
        "schema": "qwen35-quality-output-capture/v1",
        "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "label": args.label,
        "base_url": args.base_url,
        "model": args.model,
        "dataset": str(args.dataset),
        "dataset_sha256": actual_hash,
        "dataset_rows": len(rows),
        "selection": "question-character-length quantiles",
        "sample_count": len(captures),
        "seed": args.seed,
        "temperature": 0,
        "max_tokens": "per-request model context remainder",
        "natural_eos_required": True,
        "privacy": (
            "contains raw prompts and responses; local restricted evidence only"
        ),
        "captures": captures,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.chmod(temporary, 0o600)
    os.replace(temporary, args.output)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "sample_count": len(captures),
                "output_sha256": hashlib.sha256(
                    args.output.read_bytes()
                ).hexdigest(),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Drive privacy-safe Qwen3.5 Block Influence collection.

The server must be started separately with the default-off ShortGPT source
overlay, eager execution, and VLLM_ASCEND_QWEN35_BI_DIR pointing at a fresh
task-owned directory. This client persists only hashes, token counts, status,
and timing; it never writes prompts or completions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.request
from pathlib import Path


def load_questions(path: Path, limit: int) -> list[str]:
    questions: list[str] = []
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
            questions.append(question)
            if limit and len(questions) >= limit:
                break
    if not questions:
        raise ValueError("dataset contains no questions")
    return questions


def post_json(url: str, payload: dict[str, object], timeout: float) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--dataset-sha256", required=True)
    parser.add_argument("--limit", type=int, default=32)
    parser.add_argument("--seed", type=int, default=1024)
    parser.add_argument("--timeout", type=float, default=600)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.limit < 1:
        raise ValueError("--limit must be positive")
    actual_hash = hashlib.sha256(args.dataset.read_bytes()).hexdigest()
    if actual_hash != args.dataset_sha256:
        raise ValueError(
            f"dataset SHA256 mismatch: expected {args.dataset_sha256}, "
            f"got {actual_hash}"
        )

    questions = load_questions(args.dataset, args.limit)
    base_url = args.base_url.rstrip("/")
    records: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []
    started = time.time()

    for index, question in enumerate(questions):
        question_hash = hashlib.sha256(question.encode()).hexdigest()
        request_started = time.perf_counter()
        try:
            tokenized = post_json(
                base_url + "/tokenize",
                {"model": args.model, "prompt": question},
                min(args.timeout, 120),
            )
            result = post_json(
                base_url + "/v1/completions",
                {
                    "model": args.model,
                    "prompt": question,
                    "temperature": 0,
                    "seed": args.seed,
                    "max_tokens": 1,
                    "cache_salt": f"shortgpt-bi-{index}-{question_hash[:16]}",
                },
                args.timeout,
            )
            choices = result.get("choices") or []
            if not choices:
                raise RuntimeError("completion response has no choices")
            text = str(choices[0].get("text", ""))
            usage = result.get("usage") or {}
            records.append(
                {
                    "request_index": index,
                    "question_sha256": question_hash,
                    "prompt_tokens": int(tokenized["count"]),
                    "completion_tokens": int(
                        usage.get("completion_tokens", 0)
                    ),
                    "finish_reason": choices[0].get("finish_reason"),
                    "response_sha256": hashlib.sha256(
                        text.encode()
                    ).hexdigest(),
                    "elapsed_ms": (
                        time.perf_counter() - request_started
                    )
                    * 1000,
                }
            )
        except Exception as exc:
            errors.append(
                {
                    "request_index": index,
                    "question_sha256": question_hash,
                    "type": type(exc).__name__,
                    "reason": str(exc),
                }
            )

    artifact = {
        "schema": "qwen35-shortgpt-bi-collection/v1",
        "dataset_sha256": actual_hash,
        "model": args.model,
        "source_commit": args.source_commit,
        "started_at_unix": started,
        "request_count": len(questions),
        "completed_count": len(records),
        "error_count": len(errors),
        "records": records,
        "errors": errors,
        "privacy": "prompts and completions omitted",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0 if not errors and len(records) == len(questions) else 2


if __name__ == "__main__":
    raise SystemExit(main())

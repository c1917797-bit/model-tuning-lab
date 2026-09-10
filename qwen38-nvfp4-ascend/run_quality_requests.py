#!/usr/bin/env python3
"""Run a frozen quality manifest against an OpenAI-compatible vLLM endpoint."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def render_prompt(record: dict, tokenizer) -> str:
    if record["prompt_mode"] == "completion":
        return record["prompt"]
    if record["prompt_mode"] != "chat":
        raise ValueError(f"unsupported prompt mode: {record['prompt_mode']}")
    return tokenizer.apply_chat_template(
        [{"role": "user", "content": record["prompt"]}],
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )


def request_payload(record: dict, model: str) -> tuple[str, dict]:
    generation = dict(record["generation"])
    payload = {"model": model, "seed": 1024, "n": 1, **generation}
    if record["prompt_mode"] == "chat":
        payload["messages"] = [{"role": "user", "content": record["prompt"]}]
        payload["chat_template_kwargs"] = {"enable_thinking": False}
        return "/v1/chat/completions", payload
    payload["prompt"] = record["prompt"]
    return "/v1/completions", payload


def post_json(url: str, payload: dict, timeout: float) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def response_text(record: dict, response: dict) -> str:
    choice = response["choices"][0]
    if record["prompt_mode"] == "chat":
        return choice["message"]["content"]
    return choice["text"]


def load_completed(path: Path) -> set[str]:
    if not path.exists():
        return set()
    completed = set()
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            item = json.loads(line)
            if item["id"] in completed:
                raise SystemExit(f"duplicate output id: {item['id']}")
            completed.add(item["id"])
    return completed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--endpoint", default="http://127.0.0.1:10110")
    parser.add_argument("--model", required=True)
    parser.add_argument("--tokenizer", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=900)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        args.tokenizer, trust_remote_code=True, local_files_only=True
    )
    completed = load_completed(args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    attempted = 0
    with args.requests.open(encoding="utf-8") as requests_handle, args.output.open(
        "a", encoding="utf-8", newline="\n"
    ) as output_handle:
        for line in requests_handle:
            record = json.loads(line)
            if record["id"] in completed:
                continue
            if args.limit is not None and attempted >= args.limit:
                break
            attempted += 1
            rendered = render_prompt(record, tokenizer)
            route, payload = request_payload(record, args.model)
            started = time.monotonic()
            result = {
                "id": record["id"],
                "suite": record["suite"],
                "rendered_prompt_sha256": sha256_text(rendered),
                "error": None,
            }
            try:
                response = post_json(args.endpoint.rstrip("/") + route, payload, args.timeout)
                result.update(
                    text=response_text(record, response),
                    finish_reason=response["choices"][0].get("finish_reason"),
                    usage=response.get("usage"),
                    response=response,
                )
            except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as error:
                result["error"] = f"{type(error).__name__}: {error}"
            result["elapsed_seconds"] = time.monotonic() - started
            output_handle.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")
            output_handle.flush()
            if result["error"]:
                print(json.dumps(result, ensure_ascii=False))
                return 2
    print(json.dumps({"attempted": attempted, "output": str(args.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

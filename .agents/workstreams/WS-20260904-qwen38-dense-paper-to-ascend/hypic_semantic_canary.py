#!/usr/bin/env python3
"""Run a deterministic semantic canary through a relocated HYPIC segment."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


ANSWER_KEY = "ZEBRA-41729"
NATIVE_TOKENS = 8192
BRIDGE_TOKENS = 1024
PUBLIC_TOKENS = 16384
INPUT_TOKENS = 32768
WARM_TAIL_TOKENS = 512


def post_json(url: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


def tokenize(base_url: str, model: str, text: str, timeout: float) -> list[int]:
    data = post_json(
        base_url.rstrip("/") + "/tokenize",
        {"model": model, "prompt": text, "add_special_tokens": False},
        timeout,
    )
    tokens = data.get("tokens")
    if not isinstance(tokens, list) or not tokens:
        raise RuntimeError(f"tokenizer returned no tokens: {data!r}")
    return [int(token) for token in tokens]


def repeated_tokens(
    base_url: str,
    model: str,
    seed: str,
    count: int,
    timeout: float,
) -> list[int]:
    repeats = max(1, count // 4)
    while True:
        tokens = tokenize(base_url, model, seed * repeats, timeout)
        if len(tokens) >= count:
            return tokens[:count]
        repeats *= 2


def token_sha256(tokens: list[int]) -> str:
    body = ",".join(str(token) for token in tokens).encode("ascii")
    return hashlib.sha256(body).hexdigest()


def completion(
    base_url: str,
    model: str,
    prompt: list[int],
    segment_ends: tuple[int, ...],
    max_tokens: int,
    timeout: float,
    ignore_eos: bool,
) -> tuple[dict[str, Any], float]:
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": 0,
        "seed": 0,
        "ignore_eos": ignore_eos,
        "stream": False,
        "vllm_xargs": {
            "hypic_segment_ends": ",".join(str(end) for end in segment_ends),
        },
    }
    started = time.perf_counter()
    data = post_json(base_url.rstrip("/") + "/v1/completions", payload, timeout)
    return data, time.perf_counter() - started


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8221")
    parser.add_argument("--model", default="qwen36-hypic-piercing")
    parser.add_argument("--phase", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=2400)
    args = parser.parse_args()

    native = repeated_tokens(
        args.base_url,
        args.model,
        "Private native prefix. This material is position dependent.\n",
        NATIVE_TOKENS,
        args.timeout,
    )
    bridge = repeated_tokens(
        args.base_url,
        args.model,
        "Private relocation bridge. It changes the public segment position.\n",
        BRIDGE_TOKENS,
        args.timeout,
    )
    public = repeated_tokens(
        args.base_url,
        args.model,
        f"Project Aster's exact access code is {ANSWER_KEY}. Remember it.\n",
        PUBLIC_TOKENS,
        args.timeout,
    )
    question = tokenize(
        args.base_url,
        args.model,
        "\nQuestion: What is Project Aster's exact access code? Answer only with the code.\nAnswer:",
        args.timeout,
    )
    private_tail_tokens = INPUT_TOKENS - NATIVE_TOKENS - BRIDGE_TOKENS - PUBLIC_TOKENS
    if len(question) >= private_tail_tokens:
        raise RuntimeError("question does not fit the private tail")
    tail_filler = repeated_tokens(
        args.base_url,
        args.model,
        "Private tail filler. Preserve the earlier Project Aster fact.\n",
        private_tail_tokens - len(question),
        args.timeout,
    )
    tail = tail_filler + question
    warm_tail = repeated_tokens(
        args.base_url,
        args.model,
        "Public-segment producer warmup tail.\n",
        WARM_TAIL_TOKENS,
        args.timeout,
    )

    warm_prompt = public + warm_tail
    warm_segment_ends = (PUBLIC_TOKENS, len(warm_prompt))
    warm_data, warm_duration = completion(
        args.base_url,
        args.model,
        warm_prompt,
        warm_segment_ends,
        1,
        args.timeout,
        True,
    )

    prompt = native + bridge + public + tail
    segment_ends = (
        NATIVE_TOKENS + BRIDGE_TOKENS,
        NATIVE_TOKENS + BRIDGE_TOKENS + PUBLIC_TOKENS,
        INPUT_TOKENS,
    )
    if len(prompt) != INPUT_TOKENS:
        raise RuntimeError(f"prompt length is {len(prompt)}, expected {INPUT_TOKENS}")
    data, duration = completion(
        args.base_url,
        args.model,
        prompt,
        segment_ends,
        32,
        args.timeout,
        False,
    )
    choice = data["choices"][0]
    text = str(choice.get("text") or "")
    output_tokens = tokenize(args.base_url, args.model, text, args.timeout) if text else []
    result = {
        "schema": "hypic-active-semantic-canary/v1",
        "phase": args.phase,
        "model": args.model,
        "base_url": args.base_url,
        "answer_key": ANSWER_KEY,
        "answer_contains_key": ANSWER_KEY in text,
        "input_tokens": len(prompt),
        "prompt_token_sha256": token_sha256(prompt),
        "public_segment_token_sha256": token_sha256(public),
        "segment_ends": list(segment_ends),
        "warmup": {
            "input_tokens": len(warm_prompt),
            "prompt_token_sha256": token_sha256(warm_prompt),
            "segment_ends": list(warm_segment_ends),
            "duration_s": warm_duration,
            "finish_reason": warm_data["choices"][0].get("finish_reason"),
            "usage": warm_data.get("usage"),
        },
        "request": {
            "max_tokens": 32,
            "temperature": 0,
            "seed": 0,
            "ignore_eos": False,
        },
        "duration_s": duration,
        "finish_reason": choice.get("finish_reason"),
        "usage": data.get("usage"),
        "response_text": text,
        "response_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "response_token_ids": output_tokens,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    return 0 if result["answer_contains_key"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

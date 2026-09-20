#!/usr/bin/env python3
"""Fail-closed token replay gate for Sparse Prefix Ascend.

The probe creates or reloads one immutable prompt-token artifact, submits that
exact prompt repeatedly, and compares returned token IDs rather than decoded
text.  A candidate may only pass when the dense reference is deterministic,
every candidate replay matches the dense token sequence, and (when requested)
the Sparse Prefix atomic transaction is present in the runtime evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


def _post_json(url: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        value = json.load(response)
    if not isinstance(value, dict):
        raise RuntimeError(f"expected a JSON object from {url}")
    return value


def _tokenize(base_url: str, model: str, text: str, timeout: float) -> list[int]:
    value = _post_json(
        f"{base_url}/tokenize",
        {"model": model, "prompt": text, "add_special_tokens": False},
        timeout,
    )
    tokens = value.get("tokens")
    if not isinstance(tokens, list) or not tokens:
        raise RuntimeError("/tokenize returned no token IDs")
    return [int(token) for token in tokens]


def _tokens_at_least(
    base_url: str,
    model: str,
    seed: str,
    count: int,
    timeout: float,
) -> list[int]:
    repeats = max(1, math.ceil(count / 8))
    while True:
        tokens = _tokenize(base_url, model, seed * repeats, timeout)
        if len(tokens) >= count:
            return tokens[:count]
        repeats *= 2


def _prompt_digest(tokens: list[int]) -> str:
    encoded = ",".join(str(token) for token in tokens).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _load_or_create_prompt(args: argparse.Namespace) -> tuple[list[int], str]:
    if args.prompt_json.exists():
        value = json.loads(args.prompt_json.read_text(encoding="utf-8"))
        tokens = value.get("prompt_token_ids")
        if not isinstance(tokens, list) or not tokens:
            raise RuntimeError("prompt artifact has no prompt_token_ids")
        prompt = [int(token) for token in tokens]
        if len(prompt) != args.input_tokens:
            raise RuntimeError(
                f"prompt artifact length {len(prompt)} != {args.input_tokens}"
            )
        digest = _prompt_digest(prompt)
        if value.get("prompt_sha256") != digest:
            raise RuntimeError("prompt artifact digest mismatch")
        return prompt, digest

    prefix_seed = (
        "Reusable technical context. The cached boundary state must remain "
        "identical across requests. Record value 17.\n"
    )
    tail_seed = (
        "Fixed replay request 00000. This suffix is immutable across all "
        "dense and candidate executions. Continue processing this context.\n"
    )
    prefix = _tokens_at_least(
        args.base_url, args.model, prefix_seed, args.prefix_tokens, args.timeout
    )
    tail = _tokens_at_least(
        args.base_url,
        args.model,
        tail_seed,
        args.input_tokens - args.prefix_tokens,
        args.timeout,
    )
    prompt = prefix + tail
    digest = _prompt_digest(prompt)
    args.prompt_json.parent.mkdir(parents=True, exist_ok=True)
    args.prompt_json.write_text(
        json.dumps(
            {
                "schema": 1,
                "input_tokens": args.input_tokens,
                "prefix_tokens": args.prefix_tokens,
                "prompt_sha256": digest,
                "prompt_token_ids": prompt,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return prompt, digest


def _completion_token_ids(value: dict[str, Any]) -> list[int]:
    choices = value.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        raise RuntimeError("completion response must contain exactly one choice")
    tokens = choices[0].get("token_ids")
    if not isinstance(tokens, list) or not tokens:
        raise RuntimeError("completion response has no token_ids")
    return [int(token) for token in tokens]


def _read_sparse_transactions(
    evidence_file: Path | None,
    start_offset: int,
) -> list[dict[str, Any]]:
    if evidence_file is None or not evidence_file.exists():
        return []
    transactions: list[dict[str, Any]] = []
    with evidence_file.open("r", encoding="utf-8") as handle:
        handle.seek(start_offset)
        for line in handle:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if item.get("event") != "sparse_prefix_native_kv_transaction":
                continue
            if (
                item.get("checkpoint_tokens")
                and item.get("native_kv_owner") is True
                and item.get("recurrent_owner") == "hypic_material_store"
            ):
                transactions.append(item)
    return transactions


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--prompt-json", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--reference-json", type=Path)
    parser.add_argument("--evidence-file", type=Path)
    parser.add_argument("--require-sparse-transaction", action="store_true")
    parser.add_argument("--input-tokens", type=int, default=9216)
    parser.add_argument("--prefix-tokens", type=int, default=7680)
    parser.add_argument("--output-tokens", type=int, default=16)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=900)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if not 0 < args.prefix_tokens < args.input_tokens:
        raise SystemExit("prefix_tokens must be between zero and input_tokens")
    if args.repeats < 3:
        raise SystemExit("repeats must be at least three")
    if args.warmups < 1:
        raise SystemExit("warmups must be at least one")

    prompt, prompt_sha256 = _load_or_create_prompt(args)
    evidence_offset = (
        args.evidence_file.stat().st_size
        if args.evidence_file is not None and args.evidence_file.exists()
        else 0
    )
    request_payload = {
        "model": args.model,
        "prompt": prompt,
        "max_tokens": args.output_tokens,
        "temperature": 0,
        "seed": 0,
        "ignore_eos": True,
        "return_token_ids": True,
        "vllm_xargs": {
            "hypic_segment_ends": (
                f"{args.prefix_tokens},{args.input_tokens}"
            )
        },
    }

    def run_once(index: int) -> dict[str, Any]:
        started = time.perf_counter()
        value = _post_json(
            f"{args.base_url}/v1/completions",
            request_payload,
            args.timeout,
        )
        token_ids = _completion_token_ids(value)
        return {
            "index": index,
            "duration_s": time.perf_counter() - started,
            "token_ids": token_ids,
            "token_sha256": _prompt_digest(token_ids),
        }

    warmup_runs = [run_once(index) for index in range(args.warmups)]
    runs = [run_once(index) for index in range(args.repeats)]

    unique_sequences = {tuple(run["token_ids"]) for run in runs}
    deterministic = len(unique_sequences) == 1
    reference_matches: list[bool] = []
    reference_deterministic: bool | None = None
    if args.reference_json is not None:
        reference = json.loads(args.reference_json.read_text(encoding="utf-8"))
        reference_runs = reference.get("runs")
        if reference.get("prompt_sha256") != prompt_sha256:
            raise RuntimeError("reference prompt digest differs")
        if not isinstance(reference_runs, list) or not reference_runs:
            raise RuntimeError("reference report has no runs")
        reference_sequences = {
            tuple(int(token) for token in run["token_ids"])
            for run in reference_runs
        }
        reference_deterministic = len(reference_sequences) == 1
        reference_sequence = next(iter(reference_sequences))
        reference_matches = [
            tuple(run["token_ids"]) == reference_sequence for run in runs
        ]

    transactions = _read_sparse_transactions(args.evidence_file, evidence_offset)
    passed = deterministic
    if reference_deterministic is not None:
        passed = passed and reference_deterministic and all(reference_matches)
    if args.require_sparse_transaction:
        passed = passed and bool(transactions)

    report = {
        "schema": 1,
        "model": args.model,
        "input_tokens": args.input_tokens,
        "prefix_tokens": args.prefix_tokens,
        "output_tokens": args.output_tokens,
        "warmups": args.warmups,
        "repeats": args.repeats,
        "prompt_sha256": prompt_sha256,
        "deterministic": deterministic,
        "reference_deterministic": reference_deterministic,
        "reference_matches": reference_matches,
        "sparse_transaction_count": len(transactions),
        "passed": passed,
        "warmup_runs": warmup_runs,
        "runs": runs,
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

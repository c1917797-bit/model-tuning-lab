#!/usr/bin/env python3
"""Prepare a deterministic 2048-token prompt snapshot from general eval datasets."""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

from qwen38_general_eval import load_gsm8k, load_humaneval, load_mmlu


def post_json(url: str, body: dict, timeout: float = 30.0) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def tokenize(base_url: str, model: str, prompt: str) -> list[int]:
    return post_json(base_url.rstrip("/") + "/tokenize", {"model": model, "prompt": prompt})["tokens"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", default="http://127.0.0.1:8200")
    p.add_argument("--model", default="qwen38")
    p.add_argument("--data-dir", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--target-input-tokens", type=int, default=2048)
    p.add_argument("--mmlu-per-subject", type=int, default=5)
    p.add_argument("--gsm8k-limit", type=int, default=64)
    p.add_argument("--humaneval-limit", type=int, default=164)
    args = p.parse_args()

    data_dir = Path(args.data_dir)
    mmlu, _ = load_mmlu(data_dir, args.mmlu_per_subject)
    gsm8k, _ = load_gsm8k(data_dir, args.gsm8k_limit)
    humaneval, _ = load_humaneval(data_dir, args.humaneval_limit)
    cases = [*mmlu, *gsm8k, *humaneval]

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        for i, case in enumerate(cases, start=1):
            source = tokenize(args.base_url, args.model, case.prompt)
            if len(source) >= args.target_input_tokens:
                shaped = source[: args.target_input_tokens]
                mode = "head-truncate"
            else:
                need = args.target_input_tokens - len(source)
                seed = hashlib.sha256(f"{case.dataset}:{case.key}".encode()).hexdigest()
                filler_text = ((f" benchmark-padding-{seed} ") * (need + 32))
                filler = tokenize(args.base_url, args.model, filler_text)
                if len(filler) < need:
                    raise RuntimeError(f"Insufficient deterministic filler tokens for {case.dataset}/{case.key}")
                shaped = source + filler[:need]
                mode = "unique-right-pad"
            row = {
                "dataset": case.dataset,
                "key": case.key,
                "prompt_token_ids": shaped,
                "source_tokens": len(source),
                "input_tokens": len(shaped),
                "shape_mode": mode,
            }
            f.write(json.dumps(row, sort_keys=True) + "\n")
            if i % 50 == 0:
                print(f"prepared {i}/{len(cases)}", flush=True)

    print(json.dumps({"requests": len(cases), "target_input_tokens": args.target_input_tokens, "sha256": sha256(output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

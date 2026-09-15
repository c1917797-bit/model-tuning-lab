#!/usr/bin/env python3
"""Measure exact chat-template token budgets for the formal DASC quality ruler."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from transformers import AutoTokenizer

import dasc_quality_eval


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def percentile(sorted_values: list[int], fraction: float) -> int:
    if not sorted_values:
        raise ValueError("cannot summarize an empty sequence")
    return sorted_values[math.ceil(fraction * len(sorted_values)) - 1]


def summarize(lengths: list[int], output_tokens: int) -> dict:
    ordered = sorted(lengths)
    if not ordered:
        raise ValueError("cannot summarize an empty sequence")
    maximum = ordered[-1]
    required = maximum + output_tokens
    return {
        "samples": len(ordered),
        "min_input_tokens": ordered[0],
        "p50_input_tokens": percentile(ordered, 0.50),
        "p95_input_tokens": percentile(ordered, 0.95),
        "max_input_tokens": maximum,
        "output_tokens": output_tokens,
        "required_context_tokens": required,
        "recommended_max_model_len": math.ceil(required / 1024) * 1024,
    }


def chat_tokens(tokenizer, prompt: str) -> int:
    value = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}],
        tokenize=True,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    if isinstance(value, dict):
        value = value.get("input_ids")
    elif hasattr(value, "input_ids"):
        value = value.input_ids
    if hasattr(value, "tolist"):
        value = value.tolist()
    if not isinstance(value, list):
        raise TypeError(f"unsupported tokenizer result: {type(value).__name__}")
    if value and isinstance(value[0], list):
        if len(value) != 1:
            raise ValueError(f"expected one token sequence, observed {len(value)}")
        value = value[0]
    if not value or not all(isinstance(token, int) for token in value):
        raise ValueError("tokenizer returned an empty or non-integer token sequence")
    return len(value)


def dataset_audit(
    base,
    tokenizer,
    dataset: str,
    path: Path,
    prefix: str,
    output_tokens: int,
) -> dict:
    samples = base.load_samples(dataset, path)
    base_lengths: list[int] = []
    prefixed_lengths: list[int] = []
    longest: list[dict] = []
    for index, sample in enumerate(samples):
        prompt, _ = base.build_case(dataset, sample)
        base_length = chat_tokens(tokenizer, prompt)
        prefixed_length = chat_tokens(tokenizer, prefix + "\n\n" + prompt)
        base_lengths.append(base_length)
        prefixed_lengths.append(prefixed_length)
        longest.append(
            {
                "index": index,
                "sample_id": sample.get("_id"),
                "base_input_tokens": base_length,
                "prefixed_input_tokens": prefixed_length,
                "added_tokens": prefixed_length - base_length,
            }
        )
    longest.sort(key=lambda item: item["prefixed_input_tokens"], reverse=True)
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "base": summarize(base_lengths, output_tokens),
        "prefixed": summarize(prefixed_lengths, output_tokens),
        "added_tokens": summarize(
            [
                prefixed - original
                for original, prefixed in zip(base_lengths, prefixed_lengths)
            ],
            0,
        ),
        "longest_five": longest[:5],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--model", type=Path, default=Path("/cache/efim/Qwen3.6-27B"))
    parser.add_argument(
        "--longbench",
        type=Path,
        default=Path("/cache/cch/hhs-aisbench/ais_bench/datasets/LongBench-v2/data.json"),
    )
    parser.add_argument(
        "--gsm8k",
        type=Path,
        default=Path("/cache/cch/hhs-aisbench/ais_bench/datasets/gsm8k/test.jsonl"),
    )
    parser.add_argument("--shared-prefix-lines", type=int, default=96)
    parser.add_argument("--output-tokens", type=int, default=1024)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    base, base_path = dasc_quality_eval.load_base(args.repo)
    prefix = dasc_quality_eval.build_shared_prefix(args.shared_prefix_lines)
    tokenizer = AutoTokenizer.from_pretrained(
        args.model,
        local_files_only=True,
        trust_remote_code=True,
    )
    tokenizer_files = {}
    for name in ("tokenizer.json", "tokenizer_config.json"):
        path = args.model / name
        tokenizer_files[name] = sha256_file(path)
    result = {
        "schema": "mst.dasc.quality-context-audit/v1",
        "model": str(args.model),
        "tokenizer_files_sha256": tokenizer_files,
        "base_evaluator": str(base_path),
        "base_evaluator_sha256": dasc_quality_eval.BASE_EVALUATOR_SHA256,
        "shared_prefix_lines": args.shared_prefix_lines,
        "shared_prefix_sha256": hashlib.sha256(prefix.encode("utf-8")).hexdigest(),
        "datasets": {
            "longbenchv2": dataset_audit(
                base, tokenizer, "longbenchv2", args.longbench, prefix, args.output_tokens
            ),
            "gsm8k": dataset_audit(
                base, tokenizer, "gsm8k", args.gsm8k, prefix, args.output_tokens
            ),
        },
    }
    encoded = json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Fail-closed static cache-budget audit for the DASC formal A/B."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def audit(
    config: dict,
    *,
    tensor_parallel_size: int,
    block_size: int,
    cache_bytes_per_rank: int,
    cache_dtype_bytes: int,
    max_model_len: int,
    max_num_seqs: int,
    performance_input_tokens: int,
    performance_prefix_tokens: int,
    performance_output_tokens: int,
    performance_concurrency: int,
) -> dict:
    text = config["text_config"]
    layer_types = text["layer_types"]
    full_layers = layer_types.count("full_attention")
    gdn_layers = layer_types.count("linear_attention")
    if full_layers + gdn_layers != len(layer_types):
        raise ValueError("unrecognized layer type in model config")

    kv_heads = int(text["num_key_value_heads"])
    value_heads = int(text["linear_num_value_heads"])
    key_heads = int(text["linear_num_key_heads"])
    for name, value in {
        "num_key_value_heads": kv_heads,
        "linear_num_value_heads": value_heads,
        "linear_num_key_heads": key_heads,
    }.items():
        if value % tensor_parallel_size:
            raise ValueError(f"{name} is not divisible by TP size")

    attention_page_per_layer = (
        block_size
        * 2
        * (kv_heads // tensor_parallel_size)
        * int(text["head_dim"])
        * cache_dtype_bytes
    )
    conv_elements_per_layer = (
        (
            int(text["linear_key_head_dim"]) * key_heads * 2
            + int(text["linear_value_head_dim"]) * value_heads
        )
        // tensor_parallel_size
        * (int(text["linear_conv_kernel_dim"]) - 1)
    )
    temporal_elements_per_layer = (
        (value_heads // tensor_parallel_size)
        * int(text["linear_value_head_dim"])
        * int(text["linear_key_head_dim"])
    )
    gdn_page_per_layer = (
        conv_elements_per_layer + temporal_elements_per_layer
    ) * cache_dtype_bytes
    dense_aggregate_page_bytes = (
        full_layers * attention_page_per_layer
        + gdn_layers * gdn_page_per_layer
    )
    dense_blocks = cache_bytes_per_rank // dense_aggregate_page_bytes
    dense_token_capacity = dense_blocks * block_size
    longest_blocks = math.ceil(max_model_len / block_size)

    unique_suffix = performance_input_tokens - performance_prefix_tokens
    if unique_suffix < 0:
        raise ValueError("performance prefix exceeds input length")
    full_residency_tokens = performance_prefix_tokens + performance_concurrency * (
        unique_suffix + performance_output_tokens
    )
    full_residency_blocks = math.ceil(full_residency_tokens / block_size)
    candidate_page_ceiling = cache_bytes_per_rank // full_residency_blocks
    active_workspace_bytes_per_rank = (
        max_num_seqs
        * temporal_elements_per_layer
        * cache_dtype_bytes
        * gdn_layers
    )

    checks = {
        "known_64_layer_3_to_1_hybrid": (
            len(layer_types) == 64 and gdn_layers == 48 and full_layers == 16
        ),
        "positive_dense_page": dense_aggregate_page_bytes > 0,
        "dense_single_max_sequence_fits": dense_blocks >= longest_blocks,
        "cache_budget_is_exact_multiple_of_gib": cache_bytes_per_rank
        % (1024**3)
        == 0,
        "max_num_seqs_covers_quality_concurrency": max_num_seqs >= 32,
    }
    return {
        "schema": "dasc-formal-resource-budget/v1",
        "inputs": {
            "tensor_parallel_size": tensor_parallel_size,
            "block_size": block_size,
            "cache_bytes_per_rank": cache_bytes_per_rank,
            "cache_dtype_bytes": cache_dtype_bytes,
            "max_model_len": max_model_len,
            "max_num_seqs": max_num_seqs,
        },
        "model": {
            "full_attention_layers": full_layers,
            "gdn_layers": gdn_layers,
            "attention_page_bytes_per_layer_per_rank": attention_page_per_layer,
            "gdn_conv_bytes_per_layer_per_rank": conv_elements_per_layer
            * cache_dtype_bytes,
            "gdn_temporal_bytes_per_layer_per_rank": temporal_elements_per_layer
            * cache_dtype_bytes,
            "gdn_dense_page_bytes_per_layer_per_rank": gdn_page_per_layer,
        },
        "dense_capacity": {
            "aggregate_page_bytes_per_rank": dense_aggregate_page_bytes,
            "blocks_per_rank": dense_blocks,
            "token_capacity_per_rank": dense_token_capacity,
            "longest_sequence_blocks": longest_blocks,
            "spare_blocks_after_longest_sequence": dense_blocks - longest_blocks,
        },
        "performance_residency": {
            "tokens_if_all_requests_resident": full_residency_tokens,
            "blocks_if_all_requests_resident": full_residency_blocks,
            "candidate_page_ceiling_for_full_residency_bytes": candidate_page_ceiling,
            "dense_requires_scheduler_queueing": dense_blocks < full_residency_blocks,
        },
        "candidate_active_bridge": {
            "dense_temporal_workspace_bytes_per_rank_upper_bound": active_workspace_bytes_per_rank
        },
        "checks": checks,
        "ok": all(checks.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--model-config", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--tensor-parallel-size", type=int, default=4)
    parser.add_argument("--block-size", type=int, default=128)
    parser.add_argument("--cache-bytes-per-rank", type=int, default=9663676416)
    parser.add_argument("--cache-dtype-bytes", type=int, default=2)
    parser.add_argument("--max-model-len", type=int, default=44032)
    parser.add_argument("--max-num-seqs", type=int, default=32)
    parser.add_argument("--performance-input-tokens", type=int, default=32768)
    parser.add_argument("--performance-prefix-tokens", type=int, default=16384)
    parser.add_argument("--performance-output-tokens", type=int, default=1024)
    parser.add_argument("--performance-concurrency", type=int, default=16)
    args = parser.parse_args()

    result = audit(
        json.loads(args.model_config.read_text(encoding="utf-8")),
        tensor_parallel_size=args.tensor_parallel_size,
        block_size=args.block_size,
        cache_bytes_per_rank=args.cache_bytes_per_rank,
        cache_dtype_bytes=args.cache_dtype_bytes,
        max_model_len=args.max_model_len,
        max_num_seqs=args.max_num_seqs,
        performance_input_tokens=args.performance_input_tokens,
        performance_prefix_tokens=args.performance_prefix_tokens,
        performance_output_tokens=args.performance_output_tokens,
        performance_concurrency=args.performance_concurrency,
    )
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if result["ok"] else 3


if __name__ == "__main__":
    raise SystemExit(main())

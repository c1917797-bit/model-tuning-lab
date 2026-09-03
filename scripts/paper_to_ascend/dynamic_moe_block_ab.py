#!/usr/bin/env python3
"""Ascend-native Dynamic MoE whole-block A/B diagnostic benchmark.

This is deliberately stronger than a router-only microbenchmark: both the fixed
Top-2 baseline and Dynamic top-p candidate run routing, compact token/expert
dispatch, CANN MoE permutation, BF16 grouped-matmul/SwiGLU/grouped-matmul expert
compute, and weighted token combine on the target NPU.

It is still not a full-model quality benchmark. The result must therefore be
treated as block-level performance evidence only.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import time
from pathlib import Path

import torch
import torch.nn.functional as F
import torch_npu


def synchronize() -> None:
    torch.npu.synchronize()


def fixed_top2_pairs(route_probs: torch.Tensor, token_grid: torch.Tensor):
    weights, expert_ids = torch.topk(route_probs, k=2, dim=-1, sorted=True)
    token_ids = token_grid[:, :2].reshape(-1)
    return token_ids, expert_ids.reshape(-1).to(torch.int32), weights.reshape(-1)


def dynamic_top_p_pairs(route_probs: torch.Tensor, token_grid: torch.Tensor, top_p: float):
    sorted_probs, sorted_ids = torch.sort(route_probs, dim=-1, descending=True)
    cumulative = torch.cumsum(sorted_probs, dim=-1)
    keep = cumulative - sorted_probs < top_p
    token_ids = token_grid[keep]
    expert_ids = sorted_ids[keep].to(torch.int32)
    weights = sorted_probs[keep]
    return token_ids, expert_ids, weights


def expert_block_from_pairs(
    hidden_states: torch.Tensor,
    token_ids: torch.Tensor,
    expert_ids: torch.Tensor,
    pair_weights: torch.Tensor,
    w1_t: torch.Tensor,
    w2_t: torch.Tensor,
    num_experts: int,
) -> torch.Tensor:
    """Execute compact token/expert pairs using Ascend native MoE + GMM ops."""
    expanded = hidden_states[token_ids]
    sorted_hidden, reverse_map, group_boundaries, _ = torch_npu.npu_moe_init_routing_v2(
        expanded,
        expert_ids.unsqueeze(-1),
        expert_num=num_experts,
        expert_tokens_num_flag=True,
        active_expert_range=[0, num_experts],
    )
    # npu_moe_init_routing_v2 returns cumulative expert boundaries here, hence
    # group_list_type=0. This was checked against a per-expert BF16 reference.
    expert_out = torch_npu.npu_grouped_matmul(
        x=[sorted_hidden],
        weight=[w1_t],
        split_item=2,
        group_list_type=0,
        group_type=0,
        group_list=group_boundaries,
    )[0]
    expert_out = torch_npu.npu_swiglu(expert_out)
    expert_out = torch_npu.npu_grouped_matmul(
        x=[expert_out],
        weight=[w2_t],
        split_item=2,
        group_list_type=0,
        group_type=0,
        group_list=group_boundaries,
    )[0]
    pair_out = torch_npu.npu_moe_token_unpermute(expert_out, reverse_map)
    pair_out = pair_out * pair_weights.to(pair_out.dtype).unsqueeze(-1)
    combined = torch.zeros_like(hidden_states)
    combined.index_add_(0, token_ids, pair_out)
    return combined


def whole_block(
    mode: str,
    hidden_states: torch.Tensor,
    route_probs: torch.Tensor,
    token_grid: torch.Tensor,
    w1_t: torch.Tensor,
    w2_t: torch.Tensor,
    num_experts: int,
    top_p: float,
):
    if mode == "fixed_top2":
        pairs = fixed_top2_pairs(route_probs, token_grid)
    elif mode == "dynamic_top_p":
        pairs = dynamic_top_p_pairs(route_probs, token_grid, top_p)
    else:
        raise ValueError(mode)
    output = expert_block_from_pairs(hidden_states, *pairs, w1_t, w2_t, num_experts)
    return output, pairs


def naive_pair_reference(
    hidden_states: torch.Tensor,
    token_ids: torch.Tensor,
    expert_ids: torch.Tensor,
    pair_weights: torch.Tensor,
    w1: torch.Tensor,
    w2: torch.Tensor,
    num_experts: int,
) -> torch.Tensor:
    out = torch.zeros_like(hidden_states)
    for expert in range(num_experts):
        mask = expert_ids == expert
        if not bool(mask.any().cpu()):
            continue
        x = hidden_states[token_ids[mask]]
        gate_up = x @ w1[expert].transpose(0, 1)
        width = gate_up.shape[-1] // 2
        act = F.silu(gate_up[:, :width]) * gate_up[:, width:]
        y = act @ w2[expert].transpose(0, 1)
        y = y * pair_weights[mask].to(y.dtype).unsqueeze(-1)
        out.index_add_(0, token_ids[mask], y)
    return out


def correctness_check(device: str, top_p: float) -> dict:
    torch.manual_seed(17)
    e, h, n, t = 8, 64, 48, 16
    hidden = (torch.randn(t, h, device=device, dtype=torch.bfloat16) / 10).contiguous()
    logits = torch.randn(t, e, device=device, dtype=torch.float32)
    probs = torch.softmax(logits, dim=-1)
    token_grid = torch.arange(t, device=device, dtype=torch.int64).unsqueeze(1).expand(t, e)
    w1 = (torch.randn(e, 2 * n, h, device=device, dtype=torch.bfloat16) / 10).contiguous()
    w2 = (torch.randn(e, h, n, device=device, dtype=torch.bfloat16) / 10).contiguous()
    result = {}
    for mode in ("fixed_top2", "dynamic_top_p"):
        got, pairs = whole_block(mode, hidden, probs, token_grid, w1.transpose(1, 2), w2.transpose(1, 2), e, top_p)
        ref = naive_pair_reference(hidden, *pairs, w1, w2, e)
        synchronize()
        delta = (got.float() - ref.float()).abs()
        max_abs = float(delta.max().cpu())
        mean_abs = float(delta.mean().cpu())
        if max_abs > 0.02 or mean_abs > 0.002:
            raise AssertionError(f"{mode} GMM path mismatch: max_abs={max_abs} mean_abs={mean_abs}")
        result[mode] = {"max_abs_error": max_abs, "mean_abs_error": mean_abs, "pairs": int(pairs[0].numel())}
    return result


def timed_samples(fn, warmup: int, iterations: int) -> list[float]:
    for _ in range(warmup):
        fn()
    synchronize()
    samples = []
    for _ in range(iterations):
        start = time.perf_counter_ns()
        fn()
        synchronize()
        samples.append((time.perf_counter_ns() - start) / 1_000.0)
    return samples


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    idx = max(0, min(len(ordered) - 1, math.ceil(p * len(ordered)) - 1))
    return ordered[idx]


def summarize(samples: list[float]) -> dict:
    return {
        "n": len(samples),
        "median_us": statistics.median(samples),
        "mean_us": statistics.fmean(samples),
        "p95_us": percentile(samples, 0.95),
        "p99_us": percentile(samples, 0.99),
        "min_us": min(samples),
        "max_us": max(samples),
    }


def benchmark_case(args, tokens: int, w1: torch.Tensor, w2: torch.Tensor) -> dict:
    device = args.device
    all_samples = {"fixed_top2": [], "dynamic_top_p": []}
    repetitions = []
    activation_means = []
    pair_reductions = []

    for rep in range(args.repetitions):
        torch.manual_seed(args.seed + tokens * 100 + rep)
        hidden = (torch.randn(tokens, args.hidden_size, device=device, dtype=torch.bfloat16) / 10).contiguous()
        logits = torch.randn(tokens, args.experts, device=device, dtype=torch.float32)
        probs = torch.softmax(logits, dim=-1)
        token_grid = torch.arange(tokens, device=device, dtype=torch.int64).unsqueeze(1).expand(tokens, args.experts)

        # Compute pair statistics outside the timed loops without changing the
        # data subsequently used by either candidate.
        dyn_pairs = dynamic_top_p_pairs(probs, token_grid, args.top_p)
        dyn_pair_count = int(dyn_pairs[0].numel())
        fixed_pair_count = tokens * 2
        activation_means.append(dyn_pair_count / tokens)
        pair_reductions.append(1.0 - dyn_pair_count / fixed_pair_count)

        def fixed_fn():
            return whole_block(
                "fixed_top2", hidden, probs, token_grid, w1.transpose(1, 2), w2.transpose(1, 2), args.experts, args.top_p
            )[0]

        def dynamic_fn():
            return whole_block(
                "dynamic_top_p", hidden, probs, token_grid, w1.transpose(1, 2), w2.transpose(1, 2), args.experts, args.top_p
            )[0]

        order = ["fixed_top2", "dynamic_top_p"] if rep % 2 == 0 else ["dynamic_top_p", "fixed_top2"]
        rep_result = {"rep": rep, "order": order, "dynamic_pairs": dyn_pair_count, "fixed_pairs": fixed_pair_count}
        for mode in order:
            fn = fixed_fn if mode == "fixed_top2" else dynamic_fn
            samples = timed_samples(fn, args.warmup, args.iterations)
            all_samples[mode].extend(samples)
            rep_result[mode] = summarize(samples)
        repetitions.append(rep_result)

    fixed = summarize(all_samples["fixed_top2"])
    dynamic = summarize(all_samples["dynamic_top_p"])
    median_improvement = 1.0 - dynamic["median_us"] / fixed["median_us"]
    p95_improvement = 1.0 - dynamic["p95_us"] / fixed["p95_us"]
    return {
        "tokens": tokens,
        "fixed_top2": fixed,
        "dynamic_top_p": dynamic,
        "median_latency_improvement_pct": median_improvement * 100.0,
        "p95_latency_improvement_pct": p95_improvement * 100.0,
        "speedup_x": fixed["median_us"] / dynamic["median_us"],
        "mean_activated_experts": statistics.fmean(activation_means),
        "mean_pair_compute_reduction_pct": statistics.fmean(pair_reductions) * 100.0,
        "repetitions": repetitions,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="npu:0")
    parser.add_argument("--experts", type=int, default=8)
    parser.add_argument("--hidden-size", type=int, default=2048)
    parser.add_argument("--intermediate-size", type=int, default=768)
    parser.add_argument("--tokens", type=int, nargs="+", default=[128, 512, 2048, 4096])
    parser.add_argument("--top-p", type=float, default=0.4)
    parser.add_argument("--warmup", type=int, default=20)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20260904)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.experts < 2:
        raise ValueError("experts must be >= 2")
    if not 0.0 < args.top_p <= 1.0:
        raise ValueError("top-p must be in (0, 1]")

    correctness = correctness_check(args.device, args.top_p)
    torch.manual_seed(args.seed)
    w1 = (
        torch.randn(args.experts, 2 * args.intermediate_size, args.hidden_size, device=args.device, dtype=torch.bfloat16)
        / math.sqrt(args.hidden_size)
    ).contiguous()
    w2 = (
        torch.randn(args.experts, args.hidden_size, args.intermediate_size, device=args.device, dtype=torch.bfloat16)
        / math.sqrt(args.intermediate_size)
    ).contiguous()
    synchronize()

    cases = [benchmark_case(args, tokens, w1, w2) for tokens in args.tokens]
    successes = [
        case
        for case in cases
        if case["median_latency_improvement_pct"] >= 5.0 and case["p95_latency_improvement_pct"] >= 0.0
    ]
    result = {
        "schema": "paper-to-ascend/dynamic-moe-block-ab/v1",
        "scope": "single-NPU whole MoE block diagnostic; not full-model quality evidence",
        "device": args.device,
        "torch": torch.__version__,
        "torch_npu": torch_npu.__version__,
        "config": {
            "experts": args.experts,
            "hidden_size": args.hidden_size,
            "intermediate_size": args.intermediate_size,
            "dtype": "bfloat16",
            "tokens": args.tokens,
            "top_p": args.top_p,
            "warmup": args.warmup,
            "iterations": args.iterations,
            "repetitions": args.repetitions,
            "seed": args.seed,
        },
        "correctness": correctness,
        "cases": cases,
        "diagnostic_threshold": "median latency >=5% better and p95 non-regressing at the same token count",
        "diagnostic_threshold_met": bool(successes),
        "threshold_met_token_counts": [case["tokens"] for case in successes],
        "paper_acceptance": "pending: no local full MoE checkpoint/quality A/B was available",
    }
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

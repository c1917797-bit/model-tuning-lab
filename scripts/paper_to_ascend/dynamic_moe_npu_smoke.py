#!/usr/bin/env python3
"""NPU-native Dynamic MoE routing correctness + microbenchmark smoke test.

Run this inside a torch-npu/CANN environment. It does not require paper model weights; it
validates the migration unit (dynamic router selection) directly on the target NPU before
the full-model integration stage.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time

import torch

try:
    import torch_npu  # noqa: F401  # registers the NPU device backend
except ImportError:
    torch_npu = None


def dynamic_top_p_route(route_probs: torch.Tensor, top_p: float):
    """Vectorized equivalent of the upstream Dynamic_MoE cumulative-mass selection."""
    sorted_probs, sorted_indices = torch.sort(route_probs, dim=-1, descending=True)
    cumulative = torch.cumsum(sorted_probs, dim=-1)
    # Keep an expert iff the probability mass before that expert is still below top_p.
    # This yields the minimal prefix whose cumulative probability reaches/exceeds top_p.
    keep = cumulative - sorted_probs < top_p
    selected_probs = torch.where(keep, sorted_probs, torch.zeros_like(sorted_probs))
    selected_indices = torch.where(keep, sorted_indices, torch.full_like(sorted_indices, -1))
    counts = keep.sum(dim=-1)
    return selected_probs, selected_indices, counts


def fixed_top2_route(route_probs: torch.Tensor):
    return torch.topk(route_probs, k=2, dim=-1, sorted=True)


def synchronize(device: str) -> None:
    if device.startswith("npu"):
        torch.npu.synchronize()
    elif device.startswith("cuda"):
        torch.cuda.synchronize()


def benchmark(fn, warmup: int, iterations: int, device: str) -> list[float]:
    for _ in range(warmup):
        fn()
    synchronize(device)
    samples = []
    for _ in range(iterations):
        start = time.perf_counter_ns()
        fn()
        synchronize(device)
        samples.append((time.perf_counter_ns() - start) / 1_000.0)
    return samples


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="npu:0")
    parser.add_argument("--experts", type=int, default=8)
    parser.add_argument("--tokens", type=int, default=4096)
    parser.add_argument("--top-p", type=float, default=0.4)
    parser.add_argument("--warmup", type=int, default=20)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20260904)
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    logits_cpu = torch.randn(args.tokens, args.experts, dtype=torch.float32)
    probs_cpu = torch.softmax(logits_cpu, dim=-1)
    probs_device = probs_cpu.to(args.device)

    npu_probs, npu_indices, npu_counts = dynamic_top_p_route(probs_device, args.top_p)
    synchronize(args.device)
    cpu_probs, cpu_indices, cpu_counts = dynamic_top_p_route(probs_cpu, args.top_p)

    torch.testing.assert_close(npu_probs.cpu(), cpu_probs, rtol=0.0, atol=0.0)
    if not torch.equal(npu_indices.cpu(), cpu_indices):
        raise AssertionError("NPU selected expert ids differ from reference")
    if not torch.equal(npu_counts.cpu(), cpu_counts):
        raise AssertionError("NPU activated-expert counts differ from reference")

    dynamic_us = benchmark(
        lambda: dynamic_top_p_route(probs_device, args.top_p),
        args.warmup,
        args.iterations,
        args.device,
    )
    top2_us = benchmark(
        lambda: fixed_top2_route(probs_device),
        args.warmup,
        args.iterations,
        args.device,
    )

    counts = npu_counts.float().cpu()
    histogram = {
        str(k): int((counts == k).sum().item()) for k in range(1, args.experts + 1) if (counts == k).any()
    }
    result = {
        "schema": "paper-to-ascend/dynamic-moe-router-smoke/v1",
        "device": args.device,
        "tokens": args.tokens,
        "experts": args.experts,
        "top_p": args.top_p,
        "correctness": "pass",
        "activated_experts": {
            "mean": float(counts.mean().item()),
            "min": int(counts.min().item()),
            "max": int(counts.max().item()),
            "histogram": histogram,
        },
        "router_latency_us": {
            "dynamic_median": statistics.median(dynamic_us),
            "dynamic_p95": sorted(dynamic_us)[max(0, int(0.95 * len(dynamic_us)) - 1)],
            "fixed_top2_median": statistics.median(top2_us),
            "fixed_top2_p95": sorted(top2_us)[max(0, int(0.95 * len(top2_us)) - 1)],
        },
        "note": "Router latency is diagnostic only; paper acceptance requires full MoE end-to-end quality/performance evidence.",
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

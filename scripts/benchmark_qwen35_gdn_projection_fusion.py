#!/usr/bin/env python3
"""Ascend BF16 microbenchmark for fusing Qwen3.5 GDN qkvz and ba projections."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import torch
import torch_npu


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--warmup", type=int, default=20)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--repeats", type=int, default=5)
    return parser.parse_args()


def timed_us(fn, iterations: int) -> float:
    torch_npu.npu.synchronize()
    start = time.perf_counter_ns()
    result = None
    for _ in range(iterations):
        result = fn()
    torch_npu.npu.synchronize()
    assert result is not None
    return (time.perf_counter_ns() - start) / iterations / 1_000.0


def main() -> None:
    args = parse_args()
    torch.manual_seed(1024)
    torch_npu.npu.set_device(0)
    device = torch.device("npu:0")
    dtype = torch.bfloat16
    k, n_qkvz, n_ba = 5120, 4096, 24
    rows = []

    for m in (1, 5, 8, 16):
        x = (torch.randn(m, k, device=device, dtype=dtype) * 0.02).contiguous()
        w_qkvz = (torch.randn(n_qkvz, k, device=device, dtype=dtype) * 0.02).contiguous()
        w_ba = (torch.randn(n_ba, k, device=device, dtype=dtype) * 0.02).contiguous()
        w_fused = torch.cat((w_qkvz, w_ba), dim=0).contiguous()

        def separate():
            return torch.cat((torch.matmul(x, w_qkvz.t()), torch.matmul(x, w_ba.t())), dim=-1)

        def fused():
            return torch.matmul(x, w_fused.t())

        ref = separate()
        got = fused()
        torch_npu.npu.synchronize()
        max_abs_error = float((ref.float() - got.float()).abs().max().item())
        correct = bool(torch.allclose(ref.float(), got.float(), rtol=0.01, atol=0.01))

        samples = {"separate": [], "fused": []}
        for repeat in range(args.repeats):
            order = ("separate", "fused") if repeat % 2 == 0 else ("fused", "separate")
            for name in order:
                fn = separate if name == "separate" else fused
                for _ in range(args.warmup):
                    fn()
                samples[name].append(timed_us(fn, args.iterations))

        separate_median = statistics.median(samples["separate"])
        fused_median = statistics.median(samples["fused"])
        rows.append({
            "m": m,
            "separate_us": samples["separate"],
            "fused_us": samples["fused"],
            "separate_median_us": separate_median,
            "fused_median_us": fused_median,
            "speedup": separate_median / fused_median,
            "max_abs_error": max_abs_error,
            "correct": correct,
        })

    payload = {
        "schema": "qwen35-gdn-projection-fusion-microbench/v1",
        "platform": "Ascend 910B4",
        "dtype": "bfloat16",
        "shapes": {"k": k, "n_qkvz": n_qkvz, "n_ba": n_ba},
        "protocol": {"warmup": args.warmup, "iterations": args.iterations, "repeats": args.repeats, "rotated_order": True},
        "rows": rows,
        "all_correct": all(row["correct"] for row in rows),
        "geomean_speedup": float(torch.tensor([row["speedup"] for row in rows]).log().mean().exp().item()),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

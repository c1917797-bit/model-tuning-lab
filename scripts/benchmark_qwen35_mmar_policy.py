#!/usr/bin/env python3
"""Benchmark fused MMAR against MatMul + AllReduce on Qwen3.5 TP4 shapes."""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import statistics
import time
from pathlib import Path
from typing import Any, Callable


DEFAULT_SHAPES = ((1536, 5120), (4352, 5120))
DEFAULT_M_VALUES = (1, 2, 4, 6, 8, 10, 12, 14, 16)


def geometric_mean(values: list[float]) -> float:
    return math.exp(sum(math.log(value) for value in values) / len(values))


def recommend_bypass_max_m(
    cells: list[dict[str, Any]], min_speedup: float = 1.02
) -> int | None:
    """Return the largest contiguous M where separate ops win for all shapes."""
    candidates = sorted({int(cell["m"]) for cell in cells})
    accepted: list[int] = []
    for m in candidates:
        current = [cell for cell in cells if int(cell["m"]) == m]
        if not current or not all(
            cell.get("correctness", {}).get("allclose", False)
            and float(cell["separate_speedup_vs_fused"]) >= min_speedup
            for cell in current
        ):
            break
        accepted.append(m)
    return max(accepted) if accepted else None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--m-values",
        default=",".join(str(value) for value in DEFAULT_M_VALUES),
    )
    parser.add_argument("--warmup", type=int, default=20)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--min-speedup", type=float, default=1.02)
    parser.add_argument("--master-port", type=int, default=29641)
    parser.add_argument("--seed", type=int, default=1024)
    return parser.parse_args()


def time_callable(
    function: Callable[[], Any],
    torch_module: Any,
    dist_module: Any,
    warmup: int,
    iterations: int,
) -> float:
    for _ in range(warmup):
        function()
    torch_module.npu.synchronize()
    dist_module.barrier()
    started = time.perf_counter_ns()
    for _ in range(iterations):
        function()
    torch_module.npu.synchronize()
    elapsed_us = (time.perf_counter_ns() - started) / iterations / 1000.0
    per_rank: list[float | None] = [None] * dist_module.get_world_size()
    dist_module.all_gather_object(per_rank, elapsed_us)
    return max(float(value) for value in per_rank if value is not None)


def worker(rank: int, world_size: int, args: argparse.Namespace) -> None:
    import torch
    import torch.distributed as dist
    import torch_npu
    from torch.distributed.distributed_c10d import _get_default_group

    torch.npu.set_device(rank)
    dist.init_process_group(
        backend="hccl",
        rank=rank,
        world_size=world_size,
        init_method=f"tcp://127.0.0.1:{args.master_port}",
    )
    default_group = _get_default_group()
    backend = default_group._get_backend(torch.device("npu"))
    hcomm_info = backend.get_hccl_comm_name(rank)

    m_values = [int(value) for value in args.m_values.split(",")]
    rank_zero_cells: list[dict[str, Any]] = []
    for shape_index, (k, n) in enumerate(DEFAULT_SHAPES):
        generator = torch.Generator(device="cpu")
        generator.manual_seed(args.seed + rank * 1000 + shape_index)
        weight = torch.randn((k, n), generator=generator, dtype=torch.bfloat16).npu()
        for m_index, m in enumerate(m_values):
            generator.manual_seed(args.seed + rank * 1000 + shape_index * 100 + m)
            x = torch.randn((m, k), generator=generator, dtype=torch.bfloat16).npu()

            def fused():
                return torch_npu.npu_mm_all_reduce_base(
                    x, weight, hcomm_info, reduce_op="sum"
                )

            def separate():
                output = torch.matmul(x, weight)
                dist.all_reduce(output)
                return output

            fused_output = fused()
            separate_output = separate()
            torch.npu.synchronize()
            difference = (fused_output.float() - separate_output.float()).abs()
            local_correctness = {
                "allclose": bool(
                    torch.allclose(
                        fused_output.float(),
                        separate_output.float(),
                        rtol=0.02,
                        atol=0.02,
                    )
                ),
                "max_abs": float(difference.max().item()),
                "mean_abs": float(difference.mean().item()),
            }
            all_correctness: list[dict[str, Any] | None] = [None] * world_size
            dist.all_gather_object(all_correctness, local_correctness)
            correctness = {
                "allclose": all(
                    bool(item and item["allclose"]) for item in all_correctness
                ),
                "max_abs": max(
                    float(item["max_abs"])
                    for item in all_correctness
                    if item is not None
                ),
                "max_rank_mean_abs": max(
                    float(item["mean_abs"])
                    for item in all_correctness
                    if item is not None
                ),
            }

            timings = {"fused": [], "separate": []}
            for repeat in range(args.repeats):
                order = (
                    ("fused", fused),
                    ("separate", separate),
                )
                if (shape_index + m_index + repeat) % 2 == 0:
                    order = tuple(reversed(order))
                for name, function in order:
                    timings[name].append(
                        time_callable(
                            function,
                            torch,
                            dist,
                            args.warmup,
                            args.iterations,
                        )
                    )

            if rank == 0:
                fused_us = statistics.median(timings["fused"])
                separate_us = statistics.median(timings["separate"])
                rank_zero_cells.append(
                    {
                        "m": m,
                        "k": k,
                        "n": n,
                        "dtype": "bfloat16",
                        "correctness": correctness,
                        "fused_max_rank_repeat_us": timings["fused"],
                        "separate_max_rank_repeat_us": timings["separate"],
                        "fused_median_max_rank_us": fused_us,
                        "separate_median_max_rank_us": separate_us,
                        "separate_speedup_vs_fused": fused_us / separate_us,
                    }
                )

    if rank == 0:
        bypass_max_m = recommend_bypass_max_m(
            rank_zero_cells, min_speedup=args.min_speedup
        )
        speedups = [
            float(cell["separate_speedup_vs_fused"]) for cell in rank_zero_cells
        ]
        result = {
            "schema": "qwen35-mmar-policy-microbenchmark/v1",
            "model_shape_source": (
                "Qwen3.5-27B TP4 decode op_summary: "
                "[M,1536]x[1536,5120] and [M,4352]x[4352,5120]"
            ),
            "world_size": world_size,
            "physical_devices": [4, 5, 6, 7],
            "logical_devices": [0, 1, 2, 3],
            "dtype": "bfloat16",
            "quantized": False,
            "warmup": args.warmup,
            "iterations": args.iterations,
            "repeats": args.repeats,
            "min_speedup": args.min_speedup,
            "cells": rank_zero_cells,
            "summary": {
                "geomean_separate_speedup_vs_fused": geometric_mean(speedups),
                "minimum_separate_speedup_vs_fused": min(speedups),
                "recommended_decode_bypass_max_m": bypass_max_m,
                "decision": (
                    "promote-policy-to-e2e"
                    if bypass_max_m is not None
                    else "reject-separate-decode-policy"
                ),
            },
            "environment": {
                "python": platform.python_version(),
                "torch": torch.__version__,
                "torch_npu": torch_npu.__version__,
                "cann_package_version": os.environ.get("ASCEND_VERSION", "unknown"),
                "hccl_buffsize": os.environ.get("HCCL_BUFFSIZE"),
                "task_queue_enable": os.environ.get("TASK_QUEUE_ENABLE"),
            },
        }
        if args.output.exists():
            raise FileExistsError(f"refusing to overwrite {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result["summary"], sort_keys=True))
    dist.destroy_process_group()


def main() -> int:
    args = parse_args()
    m_values = [int(value) for value in args.m_values.split(",")]
    if not m_values or any(value <= 0 for value in m_values):
        raise ValueError("--m-values must contain positive integers")
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")
    import torch.multiprocessing as mp

    mp.spawn(worker, args=(4, args), nprocs=4, join=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Compare live-style transposed-view and contiguous-KN MMAR weights."""

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


SHAPES = ((1536, 5120), (4352, 5120))
M_VALUES = (1, 5, 8, 16)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--warmup", type=int, default=20)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--master-port", type=int, default=29653)
    parser.add_argument("--seed", type=int, default=1024)
    parser.add_argument("--min-speedup", type=float, default=1.02)
    return parser.parse_args()


def timed(
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
    start = time.perf_counter_ns()
    for _ in range(iterations):
        function()
    torch_module.npu.synchronize()
    elapsed_us = (time.perf_counter_ns() - start) / iterations / 1000.0
    rank_times: list[float | None] = [None] * dist_module.get_world_size()
    dist_module.all_gather_object(rank_times, elapsed_us)
    return max(float(value) for value in rank_times if value is not None)


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
    backend = _get_default_group()._get_backend(torch.device("npu"))
    hcomm_info = backend.get_hccl_comm_name(rank)
    cells: list[dict[str, Any]] = []

    for shape_index, (k, n) in enumerate(SHAPES):
        generator = torch.Generator(device="cpu")
        generator.manual_seed(args.seed + rank * 1000 + shape_index)
        # vLLM RowParallelLinear stores [N,K] and passes weight.t().
        weight_nk = (
            torch.randn((n, k), generator=generator, dtype=torch.bfloat16)
            .mul_(0.1)
            .npu()
            .contiguous()
        )
        weight_transposed_view = weight_nk.t()
        weight_kn_contiguous = weight_transposed_view.contiguous()

        for m_index, m in enumerate(M_VALUES):
            generator.manual_seed(args.seed + rank * 1000 + shape_index * 100 + m)
            x = (
                torch.randn((m, k), generator=generator, dtype=torch.bfloat16)
                .mul_(0.1)
                .npu()
                .contiguous()
            )

            def control():
                return torch_npu.npu_mm_all_reduce_base(
                    x, weight_transposed_view, hcomm_info, reduce_op="sum"
                )

            def candidate():
                return torch_npu.npu_mm_all_reduce_base(
                    x, weight_kn_contiguous, hcomm_info, reduce_op="sum"
                )

            control_output = control()
            candidate_output = candidate()
            torch.npu.synchronize()
            difference = (control_output.float() - candidate_output.float()).abs()
            local = {
                "allclose": bool(
                    torch.allclose(
                        control_output.float(),
                        candidate_output.float(),
                        rtol=0.005,
                        atol=0.1,
                    )
                ),
                "max_abs": float(difference.max().item()),
                "mean_abs": float(difference.mean().item()),
            }
            gathered: list[dict[str, Any] | None] = [None] * world_size
            dist.all_gather_object(gathered, local)
            correctness = {
                "allclose": all(bool(item and item["allclose"]) for item in gathered),
                "max_abs": max(
                    float(item["max_abs"])
                    for item in gathered
                    if item is not None
                ),
                "max_rank_mean_abs": max(
                    float(item["mean_abs"])
                    for item in gathered
                    if item is not None
                ),
            }

            timings = {"control": [], "candidate": []}
            for repeat in range(args.repeats):
                order = (("control", control), ("candidate", candidate))
                if (shape_index + m_index + repeat) % 2 == 0:
                    order = tuple(reversed(order))
                for name, function in order:
                    timings[name].append(
                        timed(
                            function,
                            torch,
                            dist,
                            args.warmup,
                            args.iterations,
                        )
                    )

            if rank == 0:
                control_us = statistics.median(timings["control"])
                candidate_us = statistics.median(timings["candidate"])
                cells.append(
                    {
                        "m": m,
                        "k": k,
                        "n": n,
                        "correctness": correctness,
                        "control_max_rank_repeat_us": timings["control"],
                        "candidate_max_rank_repeat_us": timings["candidate"],
                        "control_median_max_rank_us": control_us,
                        "candidate_median_max_rank_us": candidate_us,
                        "candidate_speedup_vs_control": control_us / candidate_us,
                    }
                )

    if rank == 0:
        speedups = [float(cell["candidate_speedup_vs_control"]) for cell in cells]
        correct = all(bool(cell["correctness"]["allclose"]) for cell in cells)
        geomean = math.exp(sum(math.log(value) for value in speedups) / len(speedups))
        promote = correct and geomean >= args.min_speedup and min(speedups) >= 1.0
        result = {
            "schema": "qwen35-mmar-weight-layout-microbenchmark/v1",
            "hypothesis": (
                "Avoid the transposed-view x2 contract of live RowParallelLinear "
                "by storing MMAR weight directly as contiguous [K,N]."
            ),
            "control": "contiguous [N,K] parameter passed as weight.t() view",
            "candidate": "pre-transposed contiguous [K,N] weight",
            "world_size": world_size,
            "physical_devices": [0, 1, 2, 3],
            "dtype": "bfloat16",
            "quantized": False,
            "warmup": args.warmup,
            "iterations": args.iterations,
            "repeats": args.repeats,
            "cells": cells,
            "summary": {
                "correctness_pass": correct,
                "geomean_candidate_speedup_vs_control": geomean,
                "minimum_candidate_speedup_vs_control": min(speedups),
                "maximum_candidate_speedup_vs_control": max(speedups),
                "decision": (
                    "investigate-load-time-layout-integration"
                    if promote
                    else "reject-contiguous-kn-before-integration"
                ),
            },
            "environment": {
                "python": platform.python_version(),
                "torch": torch.__version__,
                "torch_npu": torch_npu.__version__,
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
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")
    import torch.multiprocessing as mp

    mp.spawn(worker, args=(4, args), nprocs=4, join=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

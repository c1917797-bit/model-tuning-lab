#!/usr/bin/env python3
"""Measure official MMAR, matmul-only, and all-reduce-only decode costs."""

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--master-port", type=int, required=True)
    parser.add_argument("--warmup", type=int, default=40)
    parser.add_argument("--iterations", type=int, default=200)
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--seed", type=int, default=1024)
    return parser.parse_args()


def time_max_rank_us(
    function: Callable[[], Any], torch_module: Any, dist_module: Any, args: argparse.Namespace
) -> list[float]:
    timings = []
    for _ in range(args.repeats):
        for _ in range(args.warmup):
            function()
        torch_module.npu.synchronize()
        dist_module.barrier()
        started = time.perf_counter_ns()
        for _ in range(args.iterations):
            function()
        torch_module.npu.synchronize()
        elapsed_us = (time.perf_counter_ns() - started) / args.iterations / 1000.0
        gathered: list[float | None] = [None] * dist_module.get_world_size()
        dist_module.all_gather_object(gathered, elapsed_us)
        timings.append(max(float(value) for value in gathered if value is not None))
    return timings


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
    cells = []
    for shape_index, (k, n) in enumerate(SHAPES):
        generator = torch.Generator(device="cpu")
        generator.manual_seed(args.seed + rank * 1000 + shape_index)
        weight = torch.randn((k, n), generator=generator, dtype=torch.bfloat16).npu()
        generator.manual_seed(args.seed + rank * 1000 + shape_index * 100)
        x = torch.randn((1, k), generator=generator, dtype=torch.bfloat16).npu()

        def matmul_only(x=x, weight=weight):
            return torch.matmul(x, weight)

        def all_reduce_only(x=x, weight=weight):
            output = torch.matmul(x, weight)
            dist.all_reduce(output)
            return output

        def official_mmar(x=x, weight=weight):
            return torch_npu.npu_mm_all_reduce_base(
                x, weight, hcomm_info, reduce_op="sum"
            )

        reference = all_reduce_only().float().cpu()
        fused = official_mmar().float().cpu()
        difference = (fused - reference).abs()
        reference_l2 = float(torch.linalg.vector_norm(reference).item())
        diff_l2 = float(torch.linalg.vector_norm(difference).item())
        local_correctness = {
            "max_abs_vs_matmul_plus_all_reduce": float(difference.max().item()),
            "relative_l2_vs_matmul_plus_all_reduce": (
                diff_l2 / reference_l2 if reference_l2 > 0 else math.inf
            ),
        }
        correctness_by_rank: list[dict[str, float] | None] = [None] * world_size
        dist.all_gather_object(correctness_by_rank, local_correctness)
        measurements = {
            "matmul_only_us": time_max_rank_us(matmul_only, torch, dist, args),
            "matmul_plus_all_reduce_us": time_max_rank_us(all_reduce_only, torch, dist, args),
            "official_mmar_us": time_max_rank_us(official_mmar, torch, dist, args),
        }
        if rank == 0:
            cell = {
                "m": 1,
                "k": k,
                "n": n,
                "dtype": "bfloat16",
                "correctness_by_rank": [item for item in correctness_by_rank if item],
                "measurements": {},
            }
            for name, values in measurements.items():
                cell["measurements"][name] = {
                    "repeat_max_rank_us": values,
                    "median_max_rank_us": statistics.median(values),
                }
            cells.append(cell)
    if rank == 0:
        result = {
            "schema": "qwen35-mmar-component-breakdown/v1",
            "shape_source": "Qwen3.5 decode row-parallel MMAR shapes from msprof control",
            "world_size": world_size,
            "physical_devices": [0, 1, 2, 3],
            "warmup": args.warmup,
            "iterations": args.iterations,
            "repeats": args.repeats,
            "cells": cells,
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
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps({
            "schema": result["schema"],
            "output": str(args.output),
            "median_us": {
                f"k{cell['k']}": {
                    key: value["median_max_rank_us"]
                    for key, value in cell["measurements"].items()
                }
                for cell in cells
            },
        }, sort_keys=True))
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

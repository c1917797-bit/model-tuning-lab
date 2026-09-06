#!/usr/bin/env python3
"""Measure HCCL buffer-size impact on the two real Qwen3.5 decode MMAR shapes."""

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
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--warmup", type=int, default=40)
    parser.add_argument("--iterations", type=int, default=200)
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--master-port", type=int, default=29711)
    parser.add_argument("--seed", type=int, default=1024)
    parser.add_argument(
        "--schema",
        default="qwen35-mmar-hccl-buffer-microbenchmark/v1",
    )
    parser.add_argument("--label")
    return parser.parse_args()


def time_max_rank_us(
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
    values: list[float | None] = [None] * dist_module.get_world_size()
    dist_module.all_gather_object(values, elapsed_us)
    return max(float(value) for value in values if value is not None)


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
        weight = torch.randn((k, n), generator=generator, dtype=torch.bfloat16).npu()
        generator.manual_seed(args.seed + rank * 1000 + shape_index * 100)
        x = torch.randn((1, k), generator=generator, dtype=torch.bfloat16).npu()

        def fused():
            return torch_npu.npu_mm_all_reduce_base(
                x, weight, hcomm_info, reduce_op="sum"
            )

        fused_output = fused()
        reference = torch.matmul(x, weight)
        dist.all_reduce(reference)
        torch.npu.synchronize()
        difference = (fused_output.float() - reference.float()).abs()
        reference_l2 = float(torch.linalg.vector_norm(reference.float()).item())
        difference_l2 = float(torch.linalg.vector_norm(difference).item())
        local = {
            "allclose": bool(
                torch.allclose(
                    fused_output.float(), reference.float(), rtol=0.02, atol=0.02
                )
            ),
            "max_abs": float(difference.max().item()),
            "mean_abs": float(difference.mean().item()),
            "relative_l2": (
                difference_l2 / reference_l2 if reference_l2 > 0.0 else math.inf
            ),
            "output_fp32": fused_output.float().cpu().reshape(-1).tolist(),
        }
        gathered: list[dict[str, Any] | None] = [None] * world_size
        dist.all_gather_object(gathered, local)

        timings = [
            time_max_rank_us(
                fused, torch, dist, args.warmup, args.iterations
            )
            for _ in range(args.repeats)
        ]
        if rank == 0:
            cells.append(
                {
                    "m": 1,
                    "k": k,
                    "n": n,
                    "dtype": "bfloat16",
                    "max_rank_repeat_us": timings,
                    "median_max_rank_us": statistics.median(timings),
                    "correctness": {
                        "allclose": all(
                            bool(item and item["allclose"]) for item in gathered
                        ),
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
                        "max_rank_relative_l2": max(
                            float(item["relative_l2"])
                            for item in gathered
                            if item is not None
                        ),
                    },
                    "output_by_rank": [
                        item["output_fp32"] for item in gathered if item is not None
                    ],
                }
            )

    if rank == 0:
        result = {
            "schema": args.schema,
            "label": args.label,
            "shape_source": (
                "real 910B4 rank-0 op_summary; each decode shape occurred "
                "6720 times in the profiled request"
            ),
            "world_size": world_size,
            "physical_devices": [0, 1, 2, 3],
            "dtype": "bfloat16",
            "quantized": False,
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
                "mmar_m1_core_num": os.environ.get(
                    "ASCEND_MATMUL_ALLREDUCE_M1_CORE_NUM"
                ),
                "ascend_custom_opp_path": os.environ.get(
                    "ASCEND_CUSTOM_OPP_PATH"
                ),
                "operator_commit": os.environ.get(
                    "QWEN35_MMAR_OPERATOR_COMMIT"
                ),
                "package_sha256": os.environ.get(
                    "QWEN35_MMAR_PACKAGE_SHA256"
                ),
            },
        }
        if args.output.exists():
            raise FileExistsError(f"refusing to overwrite {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(
            json.dumps(
                {
                    "schema": result["schema"],
                    "label": result["label"],
                    "output": str(args.output),
                    "cells": [
                        {
                            "m": cell["m"],
                            "k": cell["k"],
                            "n": cell["n"],
                            "median_max_rank_us": cell["median_max_rank_us"],
                            "correctness": cell["correctness"],
                        }
                        for cell in cells
                    ],
                },
                sort_keys=True,
            )
        )
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

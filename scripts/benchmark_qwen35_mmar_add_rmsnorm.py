#!/usr/bin/env python3
"""Benchmark CANN MMAR+Add+RMSNorm on Qwen3.5 TP4 decode shapes."""

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
    if not values or any(value <= 0 for value in values):
        raise ValueError("geometric mean requires positive values")
    return math.exp(sum(math.log(value) for value in values) / len(values))


def summarize(cells: list[dict[str, Any]], min_speedup: float) -> dict[str, Any]:
    if not cells:
        raise ValueError("at least one benchmark cell is required")
    speedups = [float(cell["candidate_speedup_vs_control"]) for cell in cells]
    correctness_pass = all(
        bool(cell.get("correctness", {}).get("allclose_both", False))
        for cell in cells
    )
    geomean_speedup = geometric_mean(speedups)
    minimum_speedup = min(speedups)
    promote = (
        correctness_pass
        and geomean_speedup >= min_speedup
        and minimum_speedup >= 1.0
    )
    return {
        "correctness_pass": correctness_pass,
        "geomean_candidate_speedup_vs_control": geomean_speedup,
        "minimum_candidate_speedup_vs_control": minimum_speedup,
        "decision": (
            "promote-fused-tail-to-e2e"
            if promote
            else "reject-fused-tail-before-e2e"
        ),
    }


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
    parser.add_argument("--master-port", type=int, default=29643)
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


def _error_stats(actual: Any, expected: Any, torch_module: Any) -> dict[str, Any]:
    actual_float = actual.float()
    expected_float = expected.float()
    difference = (actual_float - expected_float).abs()
    return {
        "allclose": bool(
            torch_module.allclose(
                actual_float,
                expected_float,
                rtol=0.005,
                atol=0.1,
            )
        ),
        "max_abs": float(difference.max().item()),
        "mean_abs": float(difference.mean().item()),
    }


def worker(rank: int, world_size: int, args: argparse.Namespace) -> None:
    import torch
    import torch.distributed as dist
    import torch_npu
    from torch.distributed.distributed_c10d import _get_default_group

    torch.npu.set_device(rank)
    torch_npu.npu.config.allow_internal_format = True
    from vllm_ascend.utils import enable_custom_op

    if not enable_custom_op():
        raise RuntimeError("vLLM-Ascend custom operator library did not load")
    op = torch.ops._C_ascend.npu_matmul_all_reduce_add_rms_norm

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
        weight = (
            torch.randn((k, n), generator=generator, dtype=torch.bfloat16)
            .mul_(0.1)
            .npu()
            .contiguous()
        )
        raw_norm_weight = torch.randn(
            (n,), generator=generator, dtype=torch.bfloat16
        ).mul_(0.02)
        # Qwen3.5 aliases GemmaRMSNorm, whose effective gamma is 1 + weight.
        gamma = (1.0 + raw_norm_weight).npu().contiguous()

        for m_index, m in enumerate(m_values):
            generator.manual_seed(args.seed + rank * 1000 + shape_index * 100 + m)
            x = (
                torch.randn((m, k), generator=generator, dtype=torch.bfloat16)
                .mul_(0.1)
                .npu()
                .contiguous()
            )
            residual = (
                torch.randn(
                    (1, m, n), generator=generator, dtype=torch.bfloat16
                )
                .mul_(0.1)
                .npu()
                .contiguous()
            )

            def control():
                mmar = torch_npu.npu_mm_all_reduce_base(
                    x, weight, hcomm_info, reduce_op="sum"
                )
                norm_out, _, add_out = torch_npu.npu_add_rms_norm(
                    mmar.view(1, m, n), residual, gamma, 1e-6
                )
                return add_out, norm_out

            def candidate():
                return op(
                    x,
                    weight,
                    None,
                    residual,
                    gamma,
                    1e-6,
                    hcomm_info,
                    "sum",
                    0,
                    1,
                )

            control_add, control_norm = control()
            candidate_add, candidate_norm = candidate()
            torch.npu.synchronize()
            local_correctness = {
                "add_out": _error_stats(candidate_add, control_add, torch),
                "norm_out": _error_stats(candidate_norm, control_norm, torch),
            }
            local_correctness["allclose_both"] = bool(
                local_correctness["add_out"]["allclose"]
                and local_correctness["norm_out"]["allclose"]
            )
            all_correctness: list[dict[str, Any] | None] = [None] * world_size
            dist.all_gather_object(all_correctness, local_correctness)
            correctness = {
                "allclose_both": all(
                    bool(item and item["allclose_both"])
                    for item in all_correctness
                ),
                "add_out_max_abs": max(
                    float(item["add_out"]["max_abs"])
                    for item in all_correctness
                    if item is not None
                ),
                "norm_out_max_abs": max(
                    float(item["norm_out"]["max_abs"])
                    for item in all_correctness
                    if item is not None
                ),
                "add_out_max_rank_mean_abs": max(
                    float(item["add_out"]["mean_abs"])
                    for item in all_correctness
                    if item is not None
                ),
                "norm_out_max_rank_mean_abs": max(
                    float(item["norm_out"]["mean_abs"])
                    for item in all_correctness
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
                        time_callable(
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
                rank_zero_cells.append(
                    {
                        "m": m,
                        "k": k,
                        "n": n,
                        "dtype": "bfloat16",
                        "correctness": correctness,
                        "control_max_rank_repeat_us": timings["control"],
                        "candidate_max_rank_repeat_us": timings["candidate"],
                        "control_median_max_rank_us": control_us,
                        "candidate_median_max_rank_us": candidate_us,
                        "candidate_speedup_vs_control": control_us / candidate_us,
                    }
                )

    if rank == 0:
        result = {
            "schema": "qwen35-mmar-add-rmsnorm-microbenchmark/v1",
            "hypothesis": (
                "Fuse each row-parallel MatMulAllReduce tail with residual add "
                "and the following GemmaRMSNorm for decode M=1..16."
            ),
            "model_shape_source": (
                "Qwen3.5-27B TP4 decode op_summary: "
                "[M,1536]x[1536,5120] and [M,4352]x[4352,5120]"
            ),
            "control": "npu_mm_all_reduce_base + npu_add_rms_norm",
            "candidate": "CANN aclnnMatmulAllReduceAddRmsNorm",
            "gemma_gamma_semantics": "effective gamma = 1 + checkpoint weight",
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
            "summary": summarize(rank_zero_cells, args.min_speedup),
            "environment": {
                "python": platform.python_version(),
                "torch": torch.__version__,
                "torch_npu": torch_npu.__version__,
                "custom_extension_commit": os.environ.get(
                    "VLLM_ASCEND_CUSTOM_EXTENSION_COMMIT"
                ),
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

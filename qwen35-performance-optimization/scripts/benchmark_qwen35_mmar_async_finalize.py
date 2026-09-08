#!/usr/bin/env python3
"""Benchmark an opt-in M=1 MMAR path on real Qwen3.5 decode shapes."""

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
    parser.add_argument("--stress-calls", type=int, default=5000)
    parser.add_argument("--stress-batch", type=int, default=250)
    parser.add_argument("--master-port", type=int, required=True)
    parser.add_argument("--seed", type=int, default=1024)
    parser.add_argument("--label", required=True)
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
    cases: list[dict[str, Any]] = []
    cells: list[dict[str, Any]] = []
    progress_output = args.output.with_name(
        f"{args.output.stem}.rank{rank}.progress.jsonl"
    )
    if progress_output.exists():
        raise FileExistsError(f"refusing to overwrite {progress_output}")

    for shape_index, (k, n) in enumerate(SHAPES):
        generator = torch.Generator(device="cpu")
        generator.manual_seed(args.seed + rank * 1000 + shape_index)
        weight = torch.randn((k, n), generator=generator, dtype=torch.bfloat16).npu()
        generator.manual_seed(args.seed + rank * 1000 + shape_index * 100)
        x = torch.randn((1, k), generator=generator, dtype=torch.bfloat16).npu()

        def fused(x=x, weight=weight):
            return torch_npu.npu_mm_all_reduce_base(
                x, weight, hcomm_info, reduce_op="sum"
            )

        fused_output = fused()
        local_product = torch.matmul(x, weight)
        local_product_fp32 = local_product.float().cpu()
        local_products: list[list[float] | None] = [None] * world_size
        dist.all_gather_object(local_products, local_product_fp32.reshape(-1).tolist())
        deterministic_reference = torch.zeros_like(local_product_fp32)
        for product in local_products:
            if product is None:
                raise RuntimeError("missing rank-local matmul output")
            deterministic_reference.add_(
                torch.tensor(product, dtype=torch.float32).reshape_as(
                    deterministic_reference
                )
            )
        torch.npu.synchronize()
        fused_output_fp32 = fused_output.float().cpu()
        difference = (fused_output_fp32 - deterministic_reference).abs()
        reference_l2 = float(
            torch.linalg.vector_norm(deterministic_reference).item()
        )
        difference_l2 = float(torch.linalg.vector_norm(difference).item())
        local = {
            "max_abs": float(difference.max().item()),
            "mean_abs": float(difference.mean().item()),
            "relative_l2": (
                difference_l2 / reference_l2 if reference_l2 > 0.0 else math.inf
            ),
            "output_fp32": fused_output_fp32.reshape(-1).tolist(),
        }
        gathered: list[dict[str, Any] | None] = [None] * world_size
        dist.all_gather_object(gathered, local)
        timings = [
            time_max_rank_us(fused, torch, dist, args.warmup, args.iterations)
            for _ in range(args.repeats)
        ]
        stress_reference_fp32 = fused().float().cpu()
        cases.append(
            {
                "shape": (1, k, n),
                "fused": fused,
                "stress_reference_fp32": stress_reference_fp32,
                "stress_reference_l2": float(
                    torch.linalg.vector_norm(stress_reference_fp32).item()
                ),
            }
        )
        if rank == 0:
            cells.append(
                {
                    "m": 1,
                    "k": k,
                    "n": n,
                    "dtype": "bfloat16",
                    "max_rank_repeat_us": timings,
                    "median_max_rank_us": statistics.median(timings),
                    "deterministic_correctness": {
                        "reference": (
                            "rank-local NPU BF16 matmul outputs converted to FP32 "
                            "and summed on CPU in fixed rank order"
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

    if args.stress_calls < 5000:
        raise ValueError("--stress-calls must be at least 5000")
    if args.stress_batch <= 0:
        raise ValueError("--stress-batch must be positive")
    stress_local = {
        "rank": rank,
        "calls": 0,
        "finite": True,
        "metrics_by_shape": {
            str(case["shape"]): {
                "samples": 0,
                "max_abs_drift": 0.0,
                "max_relative_l2_drift": 0.0,
            }
            for case in cases
        },
        "checkpoints": [],
    }
    while stress_local["calls"] < args.stress_calls:
        batch_count = min(
            args.stress_batch, args.stress_calls - int(stress_local["calls"])
        )
        pending: list[tuple[int, Any]] = []
        for _ in range(batch_count):
            call_index = int(stress_local["calls"]) + len(pending)
            case_index = call_index % len(cases)
            pending.append((case_index, cases[case_index]["fused"]()))
        torch.npu.synchronize()
        for case_index, output in pending:
            output_fp32 = output.float().cpu()
            finite = bool(torch.isfinite(output_fp32).all().item())
            stress_local["finite"] = bool(stress_local["finite"]) and finite
            difference = (
                output_fp32 - cases[case_index]["stress_reference_fp32"]
            ).abs()
            difference_l2 = float(torch.linalg.vector_norm(difference).item())
            reference_l2 = float(cases[case_index]["stress_reference_l2"])
            relative_l2 = (
                difference_l2 / reference_l2
                if reference_l2 > 0.0
                else math.inf
            )
            shape_key = str(cases[case_index]["shape"])
            metrics = stress_local["metrics_by_shape"][shape_key]
            metrics["samples"] = int(metrics["samples"]) + 1
            metrics["max_abs_drift"] = max(
                float(metrics["max_abs_drift"]),
                float(difference.max().item()),
            )
            metrics["max_relative_l2_drift"] = max(
                float(metrics["max_relative_l2_drift"]),
                relative_l2,
            )
        stress_local["calls"] = int(stress_local["calls"]) + batch_count
        checkpoint = {
            "rank": rank,
            "completed_calls": stress_local["calls"],
            "max_numerical_drift_by_shape": {
                shape: dict(metrics)
                for shape, metrics in stress_local["metrics_by_shape"].items()
            },
        }
        stress_local["checkpoints"].append(checkpoint)
        with progress_output.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(checkpoint, sort_keys=True) + "\n")

    stress_by_rank: list[dict[str, Any] | None] = [None] * world_size
    dist.all_gather_object(stress_by_rank, stress_local)
    if rank == 0:
        result = {
            "schema": "qwen35-mmar-m1-ipc-fullmesh-frozen-ab/v2",
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
            "stress": {
                "alternating_shapes": True,
                "requested_calls_per_rank": args.stress_calls,
                "batch_size": args.stress_batch,
                "ranks": [item for item in stress_by_rank if item is not None],
            },
            "environment": {
                "python": platform.python_version(),
                "torch": torch.__version__,
                "torch_npu": torch_npu.__version__,
                "hccl_buffsize": os.environ.get("HCCL_BUFFSIZE"),
                "task_queue_enable": os.environ.get("TASK_QUEUE_ENABLE"),
                "mmar_m1_ipc_fullmesh": os.environ.get(
                    "ASCEND_MATMUL_ALLREDUCE_M1_IPC_FULLMESH"
                ),
                "ascend_custom_opp_path": os.environ.get("ASCEND_CUSTOM_OPP_PATH"),
                "operator_commit": os.environ.get("QWEN35_MMAR_OPERATOR_COMMIT"),
                "package_sha256": os.environ.get("QWEN35_MMAR_PACKAGE_SHA256"),
            },
        }
        if args.output.exists():
            raise FileExistsError(f"refusing to overwrite {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(
            json.dumps(
                {
                    "schema": result["schema"],
                    "label": args.label,
                    "output": str(args.output),
                    "median_max_rank_us": {
                        f"k{cell['k']}": cell["median_max_rank_us"]
                        for cell in cells
                    },
                    "stress_pass": all(
                        bool(item["finite"])
                        and int(item["calls"]) == args.stress_calls
                        and all(
                            int(metrics["samples"]) > 0
                            and math.isfinite(float(metrics["max_abs_drift"]))
                            and math.isfinite(
                                float(metrics["max_relative_l2_drift"])
                            )
                            for metrics in item["metrics_by_shape"].values()
                        )
                        for item in result["stress"]["ranks"]
                    ),
                },
                sort_keys=True,
            )
        )
    dist.destroy_process_group()


def main() -> int:
    args = parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")
    stale_progress = list(
        args.output.parent.glob(f"{args.output.stem}.rank*.progress.jsonl")
    )
    if stale_progress:
        raise FileExistsError(f"refusing to overwrite {stale_progress}")
    if args.label == "candidate":
        if os.environ.get("ASCEND_MATMUL_ALLREDUCE_M1_IPC_FULLMESH") != "1":
            raise RuntimeError("candidate IPC fullmesh gate is not enabled")
        custom_opp_roots = [
            Path(item)
            for item in os.environ.get("ASCEND_CUSTOM_OPP_PATH", "").split(":")
            if item
        ]
        if not custom_opp_roots or not all(
            path.is_dir() for path in custom_opp_roots
        ):
            raise RuntimeError(
                "candidate ASCEND_CUSTOM_OPP_PATH is absent or inaccessible: "
                f"{custom_opp_roots}"
            )
    import torch.multiprocessing as mp

    mp.spawn(worker, args=(4, args), nprocs=4, join=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

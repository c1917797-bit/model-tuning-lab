#!/usr/bin/env python3
"""Bounded, fresh-process HCCL AllReduce latency diagnostic on four visible NPUs.

This is an isolated communication diagnostic, not a vLLM performance benchmark.
Run only after the host-side physical-device ownership preflight.
"""

from __future__ import annotations

import json
import os
import statistics
import time
from datetime import timedelta

import torch
import torch.distributed as dist
import torch_npu  # noqa: F401 - registers the NPU device


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, max(0, int(fraction * len(ordered))))]


def main() -> None:
    rank = int(os.environ["LOCAL_RANK"])
    torch.npu.set_device(rank)
    dist.init_process_group("hccl", timeout=timedelta(seconds=75))
    try:
        if dist.get_world_size() != 4:
            raise RuntimeError("This diagnostic requires exactly four ranks")
        for rows in (4, 16):
            tensor = torch.ones(
                (rows, 5120), dtype=torch.bfloat16, device=f"npu:{rank}"
            )
            dist.barrier()
            for _ in range(12):
                dist.all_reduce(tensor)
                torch.npu.synchronize()
            dist.barrier()
            durations_ms: list[float] = []
            for _ in range(80):
                start_ns = time.perf_counter_ns()
                dist.all_reduce(tensor)
                torch.npu.synchronize()
                durations_ms.append((time.perf_counter_ns() - start_ns) / 1e6)
            print(
                json.dumps(
                    {
                        "schema": "hypic-npu03-hccl-standalone/v1",
                        "rank": rank,
                        "physical_device_preflight": "host-side, not inferred here",
                        "expansion_mode": os.environ.get(
                            "HCCL_OP_EXPANSION_MODE", "<unset>"
                        ),
                        "rows": rows,
                        "hidden_size": 5120,
                        "bytes": tensor.numel() * tensor.element_size(),
                        "warmup_calls": 12,
                        "measured_calls": len(durations_ms),
                        "median_ms": statistics.median(durations_ms),
                        "p95_ms": percentile(durations_ms, 0.95),
                        "max_ms": max(durations_ms),
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            dist.barrier()
    finally:
        dist.destroy_process_group()


if __name__ == "__main__":
    main()

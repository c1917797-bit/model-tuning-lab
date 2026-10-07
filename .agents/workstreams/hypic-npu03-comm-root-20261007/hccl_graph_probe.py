#!/usr/bin/env python3
"""Isolate four-rank AIV AllReduce graph replay from the full vLLM service."""

from __future__ import annotations

import json
import os
import statistics
import time
from datetime import timedelta

import torch
import torch.distributed as dist
import torch_npu


def main() -> None:
    rank = int(os.environ["LOCAL_RANK"])
    torch.npu.set_device(rank)
    dist.init_process_group("hccl", timeout=timedelta(seconds=75))
    try:
        if dist.get_world_size() != 4:
            raise RuntimeError("Expected exactly four visible ranks")
        tensor = torch.ones((4, 5120), dtype=torch.bfloat16, device=f"npu:{rank}")
        for _ in range(12):
            dist.all_reduce(tensor)
        torch.npu.synchronize()
        dist.barrier()
        graph = torch_npu.npu.NPUGraph()
        with torch_npu.npu.graph(graph):
            for _ in range(16):
                dist.all_reduce(tensor)
        dist.barrier()
        for _ in range(8):
            graph.replay()
            torch.npu.synchronize()
        dist.barrier()
        times_ms: list[float] = []
        for _ in range(48):
            start = time.perf_counter_ns()
            graph.replay()
            torch.npu.synchronize()
            times_ms.append((time.perf_counter_ns() - start) / 1e6)
        values = sorted(times_ms)
        print(
            json.dumps(
                {
                    "schema": "hypic-npu03-hccl-graph/v1",
                    "rank": rank,
                    "expansion_mode": os.environ.get(
                        "HCCL_OP_EXPANSION_MODE", "<unset>"
                    ),
                    "tensor_bytes": tensor.numel() * tensor.element_size(),
                    "allreduces_per_replay": 16,
                    "warmup_replays": 8,
                    "measured_replays": len(values),
                    "replay_median_ms": statistics.median(values),
                    "replay_p95_ms": values[int(0.95 * len(values))],
                    "replay_max_ms": values[-1],
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

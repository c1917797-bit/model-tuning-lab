#!/usr/bin/env python3
"""Fresh-process NPU screen for packed QKV rearrangement plus Q/K L2."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from statistics import median
import time

import torch
import torch_npu

from drror_vllm_ascend.kernels.packed_qkv_l2 import packed_qkv_l2
from vllm.model_executor.layers.fla.ops.l2norm import l2norm_fwd


H_QK, H_V, D_K, D_V = 4, 12, 64, 128
PACKED = 2 * H_QK * D_K + H_V * D_V
BATCHES = (1, 16)
WARMUP = 20
BLOCKS = 7
CALLS_PER_BLOCK = 100


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def reference(mixed):
    tokens = mixed.shape[0]
    qk_width = H_QK * D_K
    v_width = H_V * D_V
    query, key, value = torch.split(
        mixed, [qk_width, qk_width, v_width], dim=-1
    )
    fused = torch.cat(
        [query.reshape(-1), key.reshape(-1), value.reshape(-1)], dim=0
    )
    query = fused[:tokens * qk_width].view(1, tokens, H_QK, D_K)
    key = fused[tokens * qk_width:tokens * 2 * qk_width].view(
        1, tokens, H_QK, D_K
    )
    value = fused[tokens * 2 * qk_width:].view(1, tokens, H_V, D_V)
    return l2norm_fwd(query), l2norm_fwd(key), value


def measure(operation):
    for _ in range(WARMUP):
        operation()
    torch.npu.synchronize()
    device_ms, wall_ms = [], []
    for _ in range(BLOCKS):
        start = torch.npu.Event(enable_timing=True)
        end = torch.npu.Event(enable_timing=True)
        torch.npu.synchronize()
        start.record()
        wall_start = time.perf_counter()
        for _ in range(CALLS_PER_BLOCK):
            result = operation()
        end.record()
        end.synchronize()
        wall_ms.append(
            (time.perf_counter() - wall_start) * 1000 / CALLS_PER_BLOCK
        )
        device_ms.append(start.elapsed_time(end) / CALLS_PER_BLOCK)
        if not all(bool(torch.isfinite(item).all()) for item in result):
            raise RuntimeError("non-finite output during timing")
    return {
        "device_ms": device_ms,
        "wall_ms": wall_ms,
        "median_device_ms": median(device_ms),
        "median_wall_ms": median(wall_ms),
    }


def run_case(batch, operation):
    generator = torch.Generator().manual_seed(20260911 + batch)
    host = torch.randn((batch, PACKED), generator=generator).to(torch.bfloat16)
    eager_input = host.to("npu:0")
    eager = measure(lambda: operation(eager_input))

    graph_input = host.to("npu:0")
    for _ in range(3):
        operation(graph_input)
    torch.npu.synchronize()
    graph = torch.npu.NPUGraph()
    try:
        with torch.npu.graph(graph):
            graph_output = operation(graph_input)
        torch.npu.synchronize()
        graphed = measure(lambda: graph.replay() or graph_output)
    finally:
        graph.reset()
    return {"batch": batch, "eager": eager, "graph": graphed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--implementation", required=True, choices=("reference", "candidate")
    )
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if Path("/drrqr-results") not in output.parents or output.exists():
        parser.error("a fresh directory below /drrqr-results is required")
    if os.environ.get("ASCEND_RT_VISIBLE_DEVICES") != "0,1,2,3":
        parser.error("requires audited physical4-7 to logical0-3 mapping")
    output.mkdir(parents=True)
    report_path = output / "report.json"
    operation = reference if args.implementation == "reference" else packed_qkv_l2
    report = {
        "schema": "drrqr-packed-qkv-l2-micro-screen/v1",
        "status": "running",
        "label": args.label,
        "implementation": args.implementation,
        "script_sha256": sha256(__file__),
        "kernel_source_sha256": sha256(packed_qkv_l2.__code__.co_filename),
        "device": "logical npu:0; externally verified physical NPU4",
        "protocol": {
            "shape": {
                "H_QK": H_QK, "H_V": H_V, "D_K": D_K, "D_V": D_V
            },
            "batches": list(BATCHES),
            "dtype": "bfloat16",
            "warmup_calls": WARMUP,
            "blocks": BLOCKS,
            "calls_per_block": CALLS_PER_BLOCK,
            "paths": ["eager", "NPUGraph replay"],
            "comparison": "independent fresh processes in ABBA order",
        },
        "limits": (
            "Synthetic operator-composition screen only; not endpoint "
            "throughput, TTFT, TPOT, accuracy, integration, or portability proof."
        ),
        "cases": [],
    }

    def save():
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )

    save()
    try:
        from vllm_ascend.ops.triton.triton_utils import (
            init_device_properties_triton,
        )
        torch_npu.npu.set_compile_mode(jit_compile=False)
        torch.npu.set_device(0)
        init_device_properties_triton()
        with torch.inference_mode():
            for batch in BATCHES:
                report["cases"].append(run_case(batch, operation))
                save()
        report["status"] = "passed"
    except BaseException as error:
        report.update(
            status="failed", error_type=type(error).__name__, error=repr(error)
        )
        raise
    finally:
        report["completed_unix_ns"] = time.time_ns()
        save()
    print(json.dumps({"status": report["status"], "report": str(report_path)}))


if __name__ == "__main__":
    main()

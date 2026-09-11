#!/usr/bin/env python3
"""Exact NPU and graph probe for plugin packed-QKV plus Q/K L2 kernel."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import time

import torch
import torch_npu

from drror_vllm_ascend.kernels.packed_qkv_l2 import packed_qkv_l2
from vllm.model_executor.layers.fla.ops.l2norm import l2norm_fwd


H_QK, H_V, D_K, D_V = 4, 12, 64, 128
PACKED = 2 * H_QK * D_K + H_V * D_V


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def exact(left, right):
    return (
        left.shape == right.shape
        and left.dtype == right.dtype
        and bool(torch.isfinite(left).all())
        and bool(torch.isfinite(right).all())
        and torch.equal(left.cpu(), right.cpu())
    )


def reference(mixed):
    tokens = mixed.shape[0]
    q_width = H_QK * D_K
    k_width = q_width
    v_width = H_V * D_V
    query, key, value = torch.split(
        mixed, [q_width, k_width, v_width], dim=-1
    )
    fused = torch.cat(
        [query.reshape(-1), key.reshape(-1), value.reshape(-1)], dim=0
    )
    query = fused[:tokens * q_width].view(1, tokens, H_QK, D_K)
    key = fused[
        tokens * q_width:tokens * (q_width + k_width)
    ].view(1, tokens, H_QK, D_K)
    value = fused[tokens * (q_width + k_width):].view(
        1, tokens, H_V, D_V
    )
    return l2norm_fwd(query), l2norm_fwd(key), value


def run_case(batch):
    generator = torch.Generator().manual_seed(20260911 + batch)
    host = torch.empty((batch, PACKED), dtype=torch.bfloat16)
    mixed_eager = torch.empty_like(host, device="npu:0")
    mixed_graph = torch.empty_like(host, device="npu:0")
    graph = torch.npu.NPUGraph()
    try:
        mixed_graph.copy_(host)
        with torch.npu.graph(graph):
            graph_outputs = packed_qkv_l2(mixed_graph)
        torch.npu.synchronize()
        pointers = [tensor.data_ptr() for tensor in graph_outputs]
        steps = []
        for step in range(8):
            host.copy_(torch.randn(host.shape, generator=generator))
            mixed_eager.copy_(host)
            mixed_graph.copy_(host)
            reference_outputs = reference(mixed_eager)
            eager_outputs = packed_qkv_l2(mixed_eager)
            graph.replay()
            torch.npu.synchronize()
            checks = {
                "eager_exact": all(
                    exact(a, b) for a, b in zip(eager_outputs, reference_outputs)
                ),
                "graph_exact": all(
                    exact(a, b) for a, b in zip(graph_outputs, reference_outputs)
                ),
                "graph_pointers_stable": pointers == [
                    tensor.data_ptr() for tensor in graph_outputs
                ],
                "candidate_views_contiguous": all(
                    tensor.is_contiguous()
                    for tensor in (*eager_outputs, *graph_outputs)
                ),
            }
            steps.append({"step": step + 1, **checks})
            if not all(checks.values()):
                raise RuntimeError("packed QKV L2 exact parity failed")
        return {"batch": batch, "status": "passed", "steps": steps}
    finally:
        graph.reset()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if Path("/drrqr-results") not in output.parents or output.exists():
        parser.error("a fresh output directory below /drrqr-results is required")
    if os.environ.get("ASCEND_RT_VISIBLE_DEVICES") != "0,1,2,3":
        parser.error("requires audited physical4-7 to logical0-3 mapping")
    output.mkdir(parents=True)
    report_path = output / "report.json"
    report = {
        "schema": "drrqr-packed-qkv-l2-parity/v1",
        "status": "running",
        "created_unix_ns": time.time_ns(),
        "device": "logical npu:0; externally verified physical NPU4",
        "protocol": {
            "shape": {
                "H_QK": H_QK, "H_V": H_V, "D_K": D_K, "D_V": D_V
            },
            "batches": [1, 16],
            "steps": 8,
            "dtype": "bfloat16",
            "reference": "torch.split + torch.cat + two l2norm_fwd calls",
            "criterion": "bitwise Q/K/V eager and NPUGraph equality",
        },
        "script_sha256": sha256(__file__),
        "kernel_source": {
            "path": str(Path(packed_qkv_l2.__code__.co_filename).resolve()),
            "sha256": sha256(packed_qkv_l2.__code__.co_filename),
        },
        "limits": (
            "Packed rearrangement/L2 correctness only; not recurrent-state, "
            "endpoint performance, accuracy, integration, or portability proof."
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
            for batch in (1, 16):
                report["cases"].append(run_case(batch))
                save()
        report["status"] = "passed"
    except BaseException as error:
        report.update(
            status="failed", error_type=type(error).__name__,
            error=repr(error),
        )
        raise
    finally:
        report["completed_unix_ns"] = time.time_ns()
        save()
    print(json.dumps({"status": report["status"], "report": str(report_path)}))


if __name__ == "__main__":
    main()

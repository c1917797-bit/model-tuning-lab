#!/usr/bin/env python3
"""Single-process DRRQR recurrent-operator performance screen.

Each invocation loads exactly one implementation.  Compare independent runs in
an order-balanced sequence; this is an operator screen, not endpoint evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from statistics import median
import sys
import time

import torch
import torch.nn.functional as F
import torch_npu


H_QK, H_V, D_V, D_K = 4, 12, 128, 64
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


def load_bridge(path):
    spec = importlib.util.spec_from_file_location(
        "drrqr_recurrent_layout_control_v1_bridge", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot create bridge module spec")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_inputs(batch):
    generator = torch.Generator().manual_seed(20260911 + batch)
    slots = batch + 3
    q = F.normalize(
        torch.randn((batch, H_QK, D_K), generator=generator), dim=-1
    ).to(torch.bfloat16).to("npu:0")
    k = F.normalize(
        torch.randn((batch, H_QK, D_K), generator=generator), dim=-1
    ).to(torch.bfloat16).to("npu:0")
    v = (torch.randn((batch, H_V, D_V), generator=generator) * 0.1
         ).to(torch.bfloat16).to("npu:0")
    g = F.logsigmoid(
        torch.randn((batch, H_V), generator=generator) * 0.25 + 2.0
    ).to("npu:0")
    beta = torch.sigmoid(
        torch.randn((batch, H_V), generator=generator)
    ).to(torch.bfloat16).to("npu:0")
    lengths = torch.cat((
        torch.zeros(1, dtype=torch.int32),
        torch.ones(batch, dtype=torch.int32),
    )).to("npu:0")
    indices = torch.arange(batch, dtype=torch.int32).to("npu:0")
    state = (torch.randn(
        (slots, H_V, D_V, D_K), generator=generator
    ) * 0.01).to(torch.bfloat16).to("npu:0")
    return {
        "q": q, "k": k, "v": v, "g": g, "beta": beta,
        "lengths": lengths, "indices": indices,
    }, state


def call_native(inputs, state):
    return torch.ops._C_ascend.npu_recurrent_gated_delta_rule(
        query=inputs["q"], key=inputs["k"], value=inputs["v"],
        g=inputs["g"], beta=inputs["beta"], state=state,
        scale=D_K ** -0.5, actual_seq_lengths=inputs["lengths"],
        ssm_state_indices=inputs["indices"],
    )


def call_plugin(inputs, state):
    return torch.ops.drrqr_ascend.recurrent_layout_control_v1(
        query=inputs["q"], key=inputs["k"], value=inputs["v"],
        g=inputs["g"], beta=inputs["beta"], state=state,
        scale=D_K ** -0.5, actual_seq_lengths=inputs["lengths"],
        ssm_state_indices=inputs["indices"],
    )


def measure(operation):
    for _ in range(WARMUP):
        operation()
    torch.npu.synchronize()
    device_ms, wall_ms = [], []
    for _ in range(BLOCKS):
        torch.npu.synchronize()
        start = torch.npu.Event(enable_timing=True)
        end = torch.npu.Event(enable_timing=True)
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
        if not bool(torch.isfinite(result).all()):
            raise RuntimeError("non-finite output during timing")
    return {
        "device_ms": device_ms,
        "wall_ms": wall_ms,
        "median_device_ms": median(device_ms),
        "median_wall_ms": median(wall_ms),
    }


def run_case(batch, operation_factory):
    eager_inputs, eager_state = make_inputs(batch)
    eager = measure(lambda: operation_factory(eager_inputs, eager_state))

    graph_inputs, graph_state = make_inputs(batch)
    for _ in range(3):
        operation_factory(graph_inputs, graph_state)
    torch.npu.synchronize()
    graph = torch.npu.NPUGraph()
    try:
        with torch.npu.graph(graph):
            graph_output = operation_factory(graph_inputs, graph_state)
        torch.npu.synchronize()
        graphed = measure(lambda: graph.replay() or graph_output)
    finally:
        graph.reset()
    return {"batch": batch, "eager": eager, "graph": graphed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--implementation", required=True,
                        choices=("native", "plugin"))
    parser.add_argument("--label", required=True)
    parser.add_argument("--bridge", type=Path)
    parser.add_argument("--opapi", type=Path)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if Path("/drrqr-results") not in output.parents or output.exists():
        parser.error("a fresh directory below /drrqr-results is required")
    if os.environ.get("ASCEND_RT_VISIBLE_DEVICES") != "0,1,2,3":
        parser.error("requires audited physical4-7 to logical0-3 mapping")
    if args.implementation == "plugin":
        if not args.bridge or not args.opapi:
            parser.error("plugin requires --bridge and --opapi")
        if not args.bridge.is_file() or not args.opapi.is_file():
            parser.error("missing plugin runtime artifact")
    elif args.bridge or args.opapi:
        parser.error("native does not accept plugin artifacts")

    output.mkdir(parents=True)
    report_path = output / "report.json"
    report = {
        "schema": "drrqr-recurrent-micro-screen/v1",
        "status": "running",
        "label": args.label,
        "implementation": args.implementation,
        "script_sha256": sha256(__file__),
        "device": "logical npu:0; externally verified physical NPU4",
        "protocol": {
            "shape": {"H_QK": H_QK, "H_V": H_V, "D_V": D_V, "D_K": D_K},
            "batches": list(BATCHES), "state_dtype": "bfloat16",
            "warmup_calls": WARMUP, "blocks": BLOCKS,
            "calls_per_block": CALLS_PER_BLOCK,
            "paths": ["eager", "NPUGraph replay"],
            "comparison": "use independent runs in ABCCBA order",
        },
        "limits": (
            "Synthetic single-operator screen only; not endpoint throughput, "
            "TTFT, TPOT, accuracy, cache integration, or cross-host evidence."
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
        from vllm_ascend.utils import enable_custom_op
        torch_npu.npu.set_compile_mode(jit_compile=False)
        if not enable_custom_op():
            raise RuntimeError("native custom operators unavailable")
        torch.npu.set_device(0)
        init_device_properties_triton()
        operation = call_native
        if args.implementation == "plugin":
            bridge = load_bridge(args.bridge.resolve())
            bridge.configure_exact_opapi(str(args.opapi.resolve()))
            report["bridge"] = {
                "path": str(args.bridge.resolve()),
                "sha256": sha256(args.bridge),
            }
            report["opapi"] = {
                "path": str(args.opapi.resolve()),
                "sha256": sha256(args.opapi),
            }
            report["configured_opapi_path"] = bridge.configured_opapi_path()
            operation = call_plugin
        with torch.inference_mode():
            for batch in BATCHES:
                report["cases"].append(run_case(batch, operation))
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

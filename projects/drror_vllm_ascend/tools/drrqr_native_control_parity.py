#!/usr/bin/env python3
"""Exact NPU parity probe for the isolated DRRQR recurrent control operator.

This validates native-vs-plugin numerical and mutable-state behavior.  It is
not cache-manager integration, an endpoint performance result, or accuracy
evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

import torch
import torch.nn.functional as F
import torch_npu


H_QK, H_V, D_V, D_K = 4, 12, 128, 64
STEPS = 8
ALIGNMENT_BYTES = 512
SENTINEL = 123.0
STATE_DTYPES = {"bfloat16": torch.bfloat16, "float32": torch.float32}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def exact(left, right):
    if left.shape != right.shape or left.dtype != right.dtype:
        return False
    left = left.detach().cpu().contiguous()
    right = right.detach().cpu().contiguous()
    if not bool(torch.isfinite(left).all() and torch.isfinite(right).all()):
        return False
    return bool(torch.equal(
        left.reshape(-1).view(torch.uint8),
        right.reshape(-1).view(torch.uint8),
    ))


def guarded_state(slots, dtype):
    element_size = torch.empty((), dtype=dtype).element_size()
    if ALIGNMENT_BYTES % element_size:
        raise ValueError("guard alignment is incompatible with state dtype")
    guard = ALIGNMENT_BYTES // element_size
    size = slots * H_V * D_V * D_K
    if size * element_size % ALIGNMENT_BYTES:
        raise ValueError("state size does not preserve arena alignment")
    storage = torch.full(
        (size + 2 * guard,), SENTINEL, dtype=dtype, device="npu:0"
    )
    state = storage.narrow(0, guard, size).view(slots, H_V, D_V, D_K)
    return storage, state, (storage[:guard], storage[-guard:])


def metadata(tensor):
    return {
        "shape": list(tensor.shape),
        "stride": list(tensor.stride()),
        "dtype": str(tensor.dtype),
        "device": str(tensor.device),
        "data_ptr": tensor.data_ptr(),
        "storage_ptr": tensor.untyped_storage().data_ptr(),
        "storage_offset": tensor.storage_offset(),
    }


def unchanged_slots(before, after, selected):
    unselected = [i for i in range(before.shape[0]) if i not in set(selected)]
    return exact(before[unselected], after[unselected])


def reset_graph(graph, record, original_error):
    try:
        graph.reset()
    except BaseException as error:
        record["graph_cleanup_error"] = repr(error)
        if original_error is None:
            record.update(status="failed", passed=False)
            raise


def native_operation(inputs, state):
    return torch.ops._C_ascend.npu_recurrent_gated_delta_rule(
        query=inputs["q"], key=inputs["k"], value=inputs["v"],
        g=inputs["g"], beta=inputs["beta"], state=state,
        scale=D_K ** -0.5, actual_seq_lengths=inputs["lengths"],
        ssm_state_indices=inputs["indices"],
    )


def plugin_operation(inputs, state):
    return torch.ops.drrqr_ascend.recurrent_layout_control_v1(
        query=inputs["q"], key=inputs["k"], value=inputs["v"],
        g=inputs["g"], beta=inputs["beta"], state=state,
        scale=D_K ** -0.5, actual_seq_lengths=inputs["lengths"],
        ssm_state_indices=inputs["indices"],
    )


def run_case(batch, state_dtype, record, save):
    slots = batch + 3
    generator = torch.Generator().manual_seed(20260911 + batch)
    initial = (
        torch.randn((slots, H_V, D_V, D_K), generator=generator) * 0.01
    ).to(state_dtype)
    reference = initial.to("npu:0")
    eager_storage, eager, eager_guards = guarded_state(slots, state_dtype)
    graph_storage, graphed, graph_guards = guarded_state(slots, state_dtype)
    eager.copy_(initial)
    graphed.copy_(initial)
    inputs = {
        "q": torch.zeros((batch, H_QK, D_K), dtype=torch.bfloat16,
                         device="npu:0"),
        "k": torch.zeros((batch, H_QK, D_K), dtype=torch.bfloat16,
                         device="npu:0"),
        "v": torch.zeros((batch, H_V, D_V), dtype=torch.bfloat16,
                         device="npu:0"),
        "g": torch.full((batch, H_V), -0.15, dtype=torch.float32,
                        device="npu:0"),
        "beta": torch.full((batch, H_V), 0.5, dtype=torch.bfloat16,
                           device="npu:0"),
        "lengths": torch.cat((
            torch.zeros(1, dtype=torch.int32),
            torch.ones(batch, dtype=torch.int32),
        )).to("npu:0"),
        "indices": torch.arange(batch, dtype=torch.int32).to("npu:0"),
    }
    record.update(
        batch=batch, slots=slots, state_dtype=str(state_dtype),
        status="running", passed=False, steps=[],
        pointer_alignment={
            "reference": reference.data_ptr() % ALIGNMENT_BYTES,
            "eager": eager.data_ptr() % ALIGNMENT_BYTES,
            "graph": graphed.data_ptr() % ALIGNMENT_BYTES,
        },
    )
    if any(record["pointer_alignment"].values()):
        raise RuntimeError("state pointer alignment failed")

    for _ in range(3):
        plugin_operation(inputs, graphed)
        torch.npu.synchronize()
    graph = torch.npu.NPUGraph()
    try:
        with torch.npu.graph(graph):
            graph_output = plugin_operation(inputs, graphed)
        torch.npu.synchronize()
        reference.copy_(initial)
        eager.copy_(initial)
        graphed.copy_(initial)
        torch.npu.synchronize()
        tracked = {
            "reference": reference, "eager.storage": eager_storage,
            "eager.state": eager, "graph.storage": graph_storage,
            "graph.state": graphed, "graph.output": graph_output,
            **{f"input.{name}": value for name, value in inputs.items()},
        }
        original_metadata = {
            name: metadata(value) for name, value in tracked.items()
        }
        previous = {
            "reference": reference.detach().cpu(),
            "eager": eager.detach().cpu(),
            "graph": graphed.detach().cpu(),
        }
        for step in range(STEPS):
            selected = (
                (torch.arange(batch, dtype=torch.int32) + step) % slots
            ).tolist()
            for name in ("q", "k"):
                value = torch.randn(
                    (batch, H_QK, D_K), generator=generator
                )
                inputs[name].copy_(
                    F.normalize(value, dim=-1).to(torch.bfloat16)
                )
            inputs["v"].copy_((
                torch.randn((batch, H_V, D_V), generator=generator) * 0.1
            ).to(torch.bfloat16))
            inputs["g"].copy_(F.logsigmoid(
                torch.randn((batch, H_V), generator=generator) * 0.25 + 2.0
            ))
            inputs["beta"].copy_(torch.sigmoid(
                torch.randn((batch, H_V), generator=generator)
            ).to(torch.bfloat16))
            inputs["indices"].copy_(torch.tensor(selected, dtype=torch.int32))
            reference_output = native_operation(inputs, reference)
            eager_output = plugin_operation(inputs, eager)
            graph.replay()
            torch.npu.synchronize()
            current = {
                "reference": reference.detach().cpu(),
                "eager": eager.detach().cpu(),
                "graph": graphed.detach().cpu(),
            }
            observed_metadata = {
                name: metadata(value) for name, value in tracked.items()
            }
            checks = {
                "eager_output_exact": exact(
                    eager_output, reference_output
                ),
                "graph_output_exact": exact(
                    graph_output, reference_output
                ),
                "eager_full_state_exact": exact(
                    current["eager"], current["reference"]
                ),
                "graph_full_state_exact": exact(
                    current["graph"], current["reference"]
                ),
                "eager_unselected_slots_unchanged": unchanged_slots(
                    previous["eager"], current["eager"], selected
                ),
                "graph_unselected_slots_unchanged": unchanged_slots(
                    previous["graph"], current["graph"], selected
                ),
                "reference_unselected_slots_unchanged": unchanged_slots(
                    previous["reference"], current["reference"], selected
                ),
                "guards_intact": all(
                    bool((guard.cpu() == SENTINEL).all())
                    for guard in (*eager_guards, *graph_guards)
                ),
                "metadata_unchanged": (
                    observed_metadata == original_metadata
                ),
                "outputs_bfloat16": all(
                    output.dtype == torch.bfloat16
                    for output in (
                        reference_output, eager_output, graph_output
                    )
                ),
            }
            record["steps"].append({"step": step + 1, **checks})
            save()
            if not all(checks.values()):
                record["failed_checks"] = [
                    name for name, passed in checks.items() if not passed
                ]
                raise RuntimeError("native-vs-plugin exact parity failed")
            previous = current
        record.update(status="passed", passed=True)
    finally:
        reset_graph(graph, record, sys.exc_info()[1])


def load_bridge(path):
    spec = importlib.util.spec_from_file_location(
        "drrqr_recurrent_layout_control_v1_bridge", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot create bridge module spec")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--bridge", required=True, type=Path)
    parser.add_argument("--opapi", required=True, type=Path)
    parser.add_argument(
        "--state-dtype", choices=tuple(STATE_DTYPES), default="bfloat16"
    )
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if Path("/drrqr-results") not in output.parents or output.exists():
        parser.error("a fresh directory below /drrqr-results is required")
    if os.environ.get("ASCEND_RT_VISIBLE_DEVICES") != "0,1,2,3":
        parser.error("requires audited physical4-7 to logical0-3 mapping")
    for path in (args.bridge, args.opapi):
        if not path.resolve().is_file():
            parser.error(f"missing runtime artifact: {path}")

    output.mkdir(parents=True)
    report = {
        "schema": "drrqr-native-control-parity/v1",
        "status": "running",
        "created_unix_ns": time.time_ns(),
        "script_sha256": sha256(__file__),
        "bridge": {
            "path": str(args.bridge.resolve()),
            "sha256": sha256(args.bridge),
        },
        "opapi": {
            "path": str(args.opapi.resolve()),
            "sha256": sha256(args.opapi),
        },
        "device": "logical npu:0; externally verified physical NPU4",
        "protocol": {
            "shape": {"H_QK": H_QK, "H_V": H_V, "D_V": D_V, "D_K": D_K},
            "batches": [1, 16], "steps": STEPS,
            "state_dtype": args.state_dtype,
            "criterion": (
                "finite logical bytes exactly equal for native-vs-plugin "
                "output and full mutable state; guards, untouched slots and "
                "tensor metadata invariant"
            ),
            "paths": ["native eager", "plugin eager", "plugin NPUGraph"],
            "budget": "one single-dtype matrix; no automatic retry",
        },
        "limits": (
            "Operator numerical/storage/graph control only; not cache-manager "
            "integration, endpoint performance, accuracy, or cross-host proof."
        ),
        "cases": [],
    }
    report_path = output / "report.json"

    def save():
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True, allow_nan=False)
            + "\n"
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
        bridge = load_bridge(args.bridge.resolve())
        bridge.configure_exact_opapi(str(args.opapi.resolve()))
        report["configured_opapi_path"] = bridge.configured_opapi_path()
        report["schemas"] = {
            "native": str(
                torch.ops._C_ascend.npu_recurrent_gated_delta_rule
                .default._schema
            ),
            "plugin": str(
                torch.ops.drrqr_ascend.recurrent_layout_control_v1
                .default._schema
            ),
        }
        state_dtype = STATE_DTYPES[args.state_dtype]
        for batch in (1, 16):
            record = {"batch": batch, "status": "running", "steps": []}
            report["cases"].append(record)
            save()
            run_case(batch, state_dtype, record, save)
            save()
        report["status"] = "passed"
    except BaseException as error:
        report["status"] = "failed"
        report["error_type"] = type(error).__name__
        report["error"] = repr(error)
        raise
    finally:
        try:
            libraries = sorted({
                line.split()[-1]
                for line in Path("/proc/self/maps").read_text().splitlines()
                if "/" in line and (
                    "drrqr" in line or "libcust_opapi" in line
                )
            })
            report["loaded_libraries"] = [
                {"path": path, "sha256": sha256(path)}
                for path in libraries if Path(path).is_file()
            ]
        except Exception as error:
            report["library_evidence_error"] = repr(error)
            report["status"] = "failed"
        report["completed_unix_ns"] = time.time_ns()
        save()
    if report["status"] != "passed":
        raise RuntimeError("DRRQR parity evidence collection failed")
    print(json.dumps({"status": "passed", "report": str(report_path)}))


if __name__ == "__main__":
    main()

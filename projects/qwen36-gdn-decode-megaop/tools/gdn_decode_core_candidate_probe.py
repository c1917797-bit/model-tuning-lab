#!/usr/bin/env python3
"""Real-NPU correctness gate for the fused post-convolution GDN decode core.

The candidate consumes the BF16 packed output of causal_conv1d and fuses QKV
layout extraction, GDN gating, Q/K L2 normalization, and the recurrent
gated-delta update.  It is compared against the current vLLM-Ascend v0.23
native chain in eager and NPUGraph replay over changing state slots.

This is not a service benchmark, an accuracy result, or evidence for the
eventual causal-convolution-inclusive mega-op.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
from typing import Any

import torch
import torch_npu


H_QK = 4
H_V = 12
HEAD_DIM = 128
PACKED_WIDTH = 2 * H_QK * HEAD_DIM + H_V * HEAD_DIM
SCALE = HEAD_DIM**-0.5
STEPS = 8
BATCHES = (1, 16)
QUEUE_ORDERING_ITERATIONS = 32
ASCEND_GDN_SHA256 = "d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_bytes(left: torch.Tensor, right: torch.Tensor) -> bool:
    if left.shape != right.shape or left.dtype != right.dtype:
        return False
    left_cpu = left.detach().cpu().contiguous()
    right_cpu = right.detach().cpu().contiguous()
    return bool(
        torch.isfinite(left_cpu).all()
        and torch.isfinite(right_cpu).all()
        and torch.equal(left_cpu.view(torch.uint8), right_cpu.view(torch.uint8))
    )


def error_metrics(
    actual: torch.Tensor,
    expected: torch.Tensor,
    *,
    rtol: float,
    atol: float,
) -> dict[str, Any]:
    actual_cpu = actual.detach().float().cpu()
    expected_cpu = expected.detach().float().cpu()
    delta = actual_cpu - expected_cpu
    expected_l2_sq = float(expected_cpu.square().sum(dtype=torch.float64))
    expected_max = float(expected_cpu.abs().max())
    finite = bool(torch.isfinite(actual_cpu).all() and torch.isfinite(expected_cpu).all())
    return {
        "shape_match": list(actual.shape) == list(expected.shape),
        "actual_dtype": str(actual.dtype),
        "expected_dtype": str(expected.dtype),
        "finite": finite,
        "max_abs": float(delta.abs().max()),
        "relative_l2": math.sqrt(
            float(delta.square().sum(dtype=torch.float64)) / max(expected_l2_sq, 1e-30)
        ),
        "normalized_max_abs": float(delta.abs().max()) / max(expected_max, 1e-30),
        "rtol": rtol,
        "atol": atol,
        "allclose": bool(
            finite and torch.allclose(actual_cpu, expected_cpu, rtol=rtol, atol=atol)
        ),
    }


def tensor_metadata(tensor: torch.Tensor) -> dict[str, Any]:
    return {
        "shape": list(tensor.shape),
        "stride": list(tensor.stride()),
        "dtype": str(tensor.dtype),
        "device": str(tensor.device),
        "data_ptr": tensor.data_ptr(),
        "storage_ptr": tensor.untyped_storage().data_ptr(),
        "storage_offset": tensor.storage_offset(),
    }


def unchanged_slots(
    before: torch.Tensor,
    after: torch.Tensor,
    selected: list[int],
) -> bool:
    unselected = [slot for slot in range(before.shape[0]) if slot not in set(selected)]
    return exact_bytes(before[unselected], after[unselected])


def run_native(group: dict[str, torch.Tensor]) -> torch.Tensor:
    from vllm.model_executor.layers.fla.ops.l2norm import l2norm_fwd
    from vllm_ascend.device.device_op import DeviceOperator

    query, key, value = torch.split(
        group["packed_qkv"],
        [H_QK * HEAD_DIM, H_QK * HEAD_DIM, H_V * HEAD_DIM],
        dim=-1,
    )
    query = query.reshape(1, group["packed_qkv"].shape[0], H_QK, HEAD_DIM).contiguous()
    key = key.reshape(1, group["packed_qkv"].shape[0], H_QK, HEAD_DIM).contiguous()
    value = value.reshape(1, group["packed_qkv"].shape[0], H_V, HEAD_DIM).contiguous()
    g, beta = DeviceOperator.fused_gdn_gating(
        group["a_log"], group["a"], group["b"], group["dt_bias"]
    )
    query = l2norm_fwd(query)
    key = l2norm_fwd(key)
    return torch.ops._C_ascend.npu_recurrent_gated_delta_rule(
        query=query.squeeze(0),
        key=key.squeeze(0),
        value=value.squeeze(0),
        g=g.squeeze(0),
        beta=beta.squeeze(0),
        state=group["state"],
        scale=SCALE,
        actual_seq_lengths=group["actual_seq_lengths"],
        ssm_state_indices=group["state_indices"],
    )


def run_candidate(group: dict[str, torch.Tensor]) -> torch.Tensor:
    from vllm.model_executor.layers.fla.ops.l2norm import l2norm_fwd

    query, key, value = torch.split(
        group["packed_qkv"],
        [H_QK * HEAD_DIM, H_QK * HEAD_DIM, H_V * HEAD_DIM],
        dim=-1,
    )
    query = l2norm_fwd(
        query.reshape(1, group["packed_qkv"].shape[0], H_QK, HEAD_DIM).contiguous()
    ).squeeze(0)
    key = l2norm_fwd(
        key.reshape(1, group["packed_qkv"].shape[0], H_QK, HEAD_DIM).contiguous()
    ).squeeze(0)
    value = value.reshape(
        group["packed_qkv"].shape[0], H_V, HEAD_DIM
    ).contiguous()
    return torch.ops.qwen36_gdn.decode_core(
        query,
        key,
        value,
        group["a_log"],
        group["a"],
        group["b"],
        group["dt_bias"],
        group["state"],
        group["actual_seq_lengths"],
        group["state_indices"],
    )


def allocate_group(
    batch: int,
    slots: int,
    state_initial: torch.Tensor,
    a_log: torch.Tensor,
    dt_bias: torch.Tensor,
) -> dict[str, torch.Tensor]:
    return {
        "packed_qkv": torch.empty(
            (batch, PACKED_WIDTH), dtype=torch.bfloat16, device="npu:0"
        ),
        "a": torch.empty((batch, H_V), dtype=torch.bfloat16, device="npu:0"),
        "b": torch.empty((batch, H_V), dtype=torch.bfloat16, device="npu:0"),
        "a_log": a_log.to("npu:0"),
        "dt_bias": dt_bias.to("npu:0"),
        "state": state_initial.to("npu:0"),
        "actual_seq_lengths": torch.cat(
            (torch.zeros(1, dtype=torch.int32), torch.ones(batch, dtype=torch.int32))
        ).to("npu:0"),
        "state_indices": torch.empty((batch,), dtype=torch.int32, device="npu:0"),
    }


def make_step_inputs(
    batch: int,
    slots: int,
    step: int,
    generator: torch.Generator,
) -> dict[str, torch.Tensor]:
    return {
        "packed_qkv": (
            torch.randn((batch, PACKED_WIDTH), generator=generator)
            * (0.07 + 0.005 * step)
        ).to(torch.bfloat16),
        "a": (torch.randn((batch, H_V), generator=generator) * 0.35).to(
            torch.bfloat16
        ),
        "b": (torch.randn((batch, H_V), generator=generator) * 0.5).to(
            torch.bfloat16
        ),
        "state_indices": (torch.arange(batch, dtype=torch.int32) + step) % slots,
    }


def copy_inputs(
    cpu_inputs: dict[str, torch.Tensor],
    groups: list[dict[str, torch.Tensor]],
) -> None:
    for group in groups:
        for name, value in cpu_inputs.items():
            group[name].copy_(value)


def run_queue_ordering_stress(report: dict[str, Any], save: Any) -> None:
    """Prove predecessor and successor ordering without host synchronization."""
    batch = 16
    slots = batch + 3
    generator = torch.Generator().manual_seed(20260921)
    base_state = (
        torch.randn(
            (slots, H_V, HEAD_DIM, HEAD_DIM),
            generator=generator,
            dtype=torch.float32,
        )
        * 0.01
    )
    a_log = torch.log(torch.linspace(1.0, 16.0, H_V, dtype=torch.float32))
    dt_bias = torch.linspace(-0.5, 0.5, H_V, dtype=torch.float32).to(
        torch.bfloat16
    )
    source = allocate_group(batch, slots, base_state, a_log, dt_bias)
    candidate = allocate_group(batch, slots, base_state, a_log, dt_bias)
    native = allocate_group(batch, slots, base_state, a_log, dt_bias)
    case: dict[str, Any] = {
        "status": "running",
        "batch": batch,
        "iterations": QUEUE_ORDERING_ITERATIONS,
        "passed": False,
        "checks": [],
    }
    report["queue_ordering_stress"] = case
    save()

    copied_names = ("packed_qkv", "a", "b", "state_indices", "state")
    try:
        for iteration in range(QUEUE_ORDERING_ITERATIONS):
            cpu_inputs = make_step_inputs(batch, slots, iteration, generator)
            state_cpu = base_state * (1.0 + 0.01 * iteration)
            copy_inputs(cpu_inputs, [source])
            source["state"].copy_(state_cpu)
            torch.npu.synchronize()

            for group in (candidate, native):
                group["packed_qkv"].fill_(0)
                group["a"].fill_(0)
                group["b"].fill_(0)
                group["state_indices"].fill_(0)
                group["state"].fill_(0)
            torch.npu.synchronize()

            # Deliberately do not synchronize between the D2D predecessor,
            # candidate launch, and D2D successor.  A raw stream(false) launch
            # can read poison values or let the clones observe stale outputs.
            for name in copied_names:
                candidate[name].copy_(source[name])
            candidate_output = run_candidate(candidate)
            output_follower = candidate_output.clone()
            state_follower = candidate["state"].clone()

            for name in copied_names:
                native[name].copy_(source[name])
            native_output = run_native(native)
            torch.npu.synchronize()

            numeric = {
                "candidate_output_vs_native": error_metrics(
                    candidate_output, native_output, rtol=1e-2, atol=1e-2
                ),
                "candidate_state_vs_native": error_metrics(
                    candidate["state"], native["state"], rtol=1e-4, atol=2e-5
                ),
            }
            invariants = {
                "successor_output_exact": exact_bytes(
                    output_follower, candidate_output
                ),
                "successor_state_exact": exact_bytes(
                    state_follower, candidate["state"]
                ),
            }
            failed = [name for name, value in invariants.items() if not value]
            failed.extend(
                name for name, value in numeric.items() if not value["allclose"]
            )
            case["checks"].append(
                {
                    "iteration": iteration + 1,
                    "numeric": numeric,
                    "invariants": invariants,
                    "passed": not failed,
                    "failed_checks": failed,
                }
            )
            save()
            if failed:
                raise RuntimeError(
                    f"queue ordering iteration={iteration + 1} failed: {failed}"
                )
        case.update(status="passed", passed=True)
    except BaseException as error:
        case.update(
            status="failed",
            passed=False,
            error=repr(error),
            error_type=type(error).__name__,
        )
        raise
    finally:
        save()


def run_case(
    batch: int,
    case: dict[str, Any],
    save: Any,
) -> None:
    generator = torch.Generator().manual_seed(20260920 + batch)
    slots = batch + 3
    state_initial = (
        torch.randn(
            (slots, H_V, HEAD_DIM, HEAD_DIM),
            generator=generator,
            dtype=torch.float32,
        )
        * 0.01
    )
    a_log = torch.log(torch.linspace(1.0, 16.0, H_V, dtype=torch.float32))
    # The loaded Qwen3.6 checkpoint keeps dt_bias in model BF16.  Exercise the
    # exact service ABI rather than the earlier synthetic FP32 assumption.
    dt_bias = torch.linspace(-0.5, 0.5, H_V, dtype=torch.float32).to(torch.bfloat16)
    native = allocate_group(batch, slots, state_initial, a_log, dt_bias)
    eager = allocate_group(batch, slots, state_initial, a_log, dt_bias)
    graph_group = allocate_group(batch, slots, state_initial, a_log, dt_bias)
    graph: torch_npu.npu.NPUGraph | None = None

    case.update(
        status="running",
        slots=slots,
        steps=[],
        shapes={
            "packed_qkv": [batch, PACKED_WIDTH],
            "state": [slots, H_V, HEAD_DIM, HEAD_DIM],
            "output": [batch, H_V, HEAD_DIM],
        },
    )
    save()
    try:
        for warmup in range(3):
            copy_inputs(
                make_step_inputs(batch, slots, warmup, generator),
                [graph_group],
            )
            run_candidate(graph_group)
            torch.npu.synchronize()
        graph_group["state"].copy_(state_initial)
        torch.npu.synchronize()

        graph = torch.npu.NPUGraph()
        with torch.npu.graph(graph):
            graph_output = run_candidate(graph_group)
        torch.npu.synchronize()
        graph_group["state"].copy_(state_initial)
        torch.npu.synchronize()

        tracked = {
            **{f"eager.{name}": value for name, value in eager.items()},
            **{f"graph.{name}": value for name, value in graph_group.items()},
            "graph.output": graph_output,
        }
        metadata = {name: tensor_metadata(value) for name, value in tracked.items()}
        case["tracked_tensor_metadata"] = metadata
        save()

        for step in range(STEPS):
            cpu_inputs = make_step_inputs(batch, slots, step, generator)
            copy_inputs(cpu_inputs, [native, eager, graph_group])
            selected = cpu_inputs["state_indices"].tolist()
            native_before = native["state"].detach().cpu()
            eager_before = eager["state"].detach().cpu()
            graph_before = graph_group["state"].detach().cpu()

            native_output = run_native(native)
            eager_output = run_candidate(eager)
            graph.replay()
            torch.npu.synchronize()

            native_after = native["state"].detach().cpu()
            eager_after = eager["state"].detach().cpu()
            graph_after = graph_group["state"].detach().cpu()
            numeric = {
                "eager_output_vs_native": error_metrics(
                    eager_output, native_output, rtol=1e-2, atol=1e-2
                ),
                "graph_output_vs_native": error_metrics(
                    graph_output, native_output, rtol=1e-2, atol=1e-2
                ),
                "eager_state_vs_native": error_metrics(
                    eager_after, native_after, rtol=1e-4, atol=2e-5
                ),
                "graph_state_vs_native": error_metrics(
                    graph_after, native_after, rtol=1e-4, atol=2e-5
                ),
            }
            invariants = {
                "eager_graph_output_exact": exact_bytes(eager_output, graph_output),
                "eager_graph_state_exact": exact_bytes(eager_after, graph_after),
                "native_unselected_unchanged": unchanged_slots(
                    native_before, native_after, selected
                ),
                "eager_unselected_unchanged": unchanged_slots(
                    eager_before, eager_after, selected
                ),
                "graph_unselected_unchanged": unchanged_slots(
                    graph_before, graph_after, selected
                ),
                "tensor_metadata_unchanged": metadata
                == {name: tensor_metadata(value) for name, value in tracked.items()},
                "all_full_states_finite": bool(
                    torch.isfinite(native_after).all()
                    and torch.isfinite(eager_after).all()
                    and torch.isfinite(graph_after).all()
                ),
            }
            failed = [name for name, value in invariants.items() if not value]
            failed.extend(
                name for name, value in numeric.items() if not value["allclose"]
            )
            case["steps"].append(
                {
                    "step": step + 1,
                    "selected_slots": selected,
                    "numeric": numeric,
                    "invariants": invariants,
                    "passed": not failed,
                    "failed_checks": failed,
                }
            )
            save()
            print(
                json.dumps(
                    {
                        "batch": batch,
                        "step": step + 1,
                        "passed": not failed,
                        "failed_checks": failed,
                    }
                ),
                flush=True,
            )
            if failed:
                raise RuntimeError(
                    f"batch={batch} step={step + 1} failed: {failed}"
                )
        case.update(status="passed", passed=True)
    except BaseException as error:
        case.update(
            status="failed",
            passed=False,
            error=repr(error),
            error_type=type(error).__name__,
        )
        raise
    finally:
        if graph is not None:
            try:
                graph.reset()
            except BaseException as cleanup_error:
                case["graph_cleanup_error"] = repr(cleanup_error)
                if sys.exc_info()[1] is None:
                    case.update(status="failed", passed=False)
                    raise
        save()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    library = args.library.resolve()
    output_dir = args.output_dir.resolve()
    allowed_root = Path("/gdn-megaop-results")
    if allowed_root not in output_dir.parents or output_dir.exists():
        parser.error("a fresh directory below /gdn-megaop-results is required")
    if os.environ.get("ASCEND_RT_VISIBLE_DEVICES") != "0":
        parser.error("requires audited container logical NPU0 mapped to physical NPU4")
    if not library.is_file():
        parser.error(f"missing candidate library: {library}")

    source = Path("/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py")
    output_dir.mkdir(parents=True)
    report: dict[str, Any] = {
        "schema": "qwen36-gdn-decode-core-candidate-probe/v1",
        "status": "running",
        "created_unix_ns": time.time_ns(),
        "script_sha256": sha256(Path(__file__)),
        "candidate_library": str(library),
        "candidate_library_sha256": sha256(library),
        "device_contract": "container logical NPU0; externally audited physical NPU4",
        "limits": (
            "Fused post-convolution core correctness/state/graph gate only; "
            "not causal-convolution fusion, service performance, or task accuracy."
        ),
        "protocol": {
            "batches": list(BATCHES),
            "steps": STEPS,
            "queue_ordering_iterations": QUEUE_ORDERING_ITERATIONS,
            "eager_graph_parity": "finite logical tensor bytes exactly equal",
            "output_tolerance": {"rtol": 1e-2, "atol": 1e-2},
            "state_tolerance": {"rtol": 1e-4, "atol": 2e-5},
            "budget": "one batch1/batch16 matrix, no automatic retry",
        },
        "cases": [],
    }

    def save() -> None:
        (output_dir / "report.json").write_text(
            json.dumps(report, indent=2, allow_nan=False) + "\n"
        )

    save()
    try:
        if not source.is_file() or sha256(source) != ASCEND_GDN_SHA256:
            raise RuntimeError("vLLM-Ascend GDN source identity changed; re-audit required")

        from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton
        from vllm_ascend.utils import enable_custom_op

        torch_npu.npu.set_compile_mode(jit_compile=False)
        if not enable_custom_op():
            raise RuntimeError("vLLM-Ascend custom operators are unavailable")
        torch.npu.set_device(0)
        init_device_properties_triton()
        torch.ops.load_library(str(library))
        report.update(
            torch_version=torch.__version__,
            torch_npu_version=torch_npu.__version__,
            custom_opp_path=os.environ.get("ASCEND_CUSTOM_OPP_PATH"),
            candidate_schema=str(torch.ops.qwen36_gdn.decode_core.default._schema),
            recurrent_schema=str(
                torch.ops._C_ascend.npu_recurrent_gated_delta_rule.default._schema
            ),
        )
        save()

        run_queue_ordering_stress(report, save)
        for batch in BATCHES:
            case = {"batch": batch, "status": "pending", "passed": False}
            report["cases"].append(case)
            save()
            run_case(batch, case, save)
        report["status"] = "candidate_post_conv_gdn_core_gate_pass"
    except BaseException as error:
        report.update(status="failed", error=repr(error), error_type=type(error).__name__)
        raise
    finally:
        report["completed_unix_ns"] = time.time_ns()
        save()

    if report["status"] != "candidate_post_conv_gdn_core_gate_pass":
        raise RuntimeError("candidate evidence is incomplete")
    print(json.dumps({"status": report["status"], "report": str(output_dir / "report.json")}))


if __name__ == "__main__":
    main()

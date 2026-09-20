#!/usr/bin/env python3
"""Real-NPU golden probe for the Qwen3.6 TP4 GDN decode chain.

This is a numerical and state-mutation gate.  It is not an operator benchmark,
service benchmark, cache-manager integration test, or model-quality result.
The unmodified vLLM-Ascend v0.23 native chain is compared with an independent
PyTorch formulation and with its own NPUGraph replay over multiple decode
steps and changing state indices.
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
import torch.nn.functional as F
import torch_npu


H_QK = 4
H_V = 12
HEAD_DIM = 128
PACKED_WIDTH = 2 * H_QK * HEAD_DIM + H_V * HEAD_DIM
CONV_WIDTH = 4
CONV_STATE_LEN = CONV_WIDTH - 1
STEPS = 8
BATCHES = (1, 16)
SCALE = HEAD_DIM**-0.5
EPS = 1e-6
PAD_SLOT_ID = -1
ASCEND_GDN_SHA256 = "d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_bytes(left: torch.Tensor, right: torch.Tensor) -> bool:
    if left.shape != right.shape or left.dtype != right.dtype:
        return False
    left_cpu = left.detach().cpu().contiguous()
    right_cpu = right.detach().cpu().contiguous()
    if not bool(torch.isfinite(left_cpu).all() and torch.isfinite(right_cpu).all()):
        return False
    return bool(torch.equal(left_cpu.view(torch.uint8), right_cpu.view(torch.uint8)))


def error_metrics(actual: torch.Tensor, expected: torch.Tensor) -> dict[str, Any]:
    if actual.shape != expected.shape:
        return {
            "shape_match": False,
            "actual_shape": list(actual.shape),
            "expected_shape": list(expected.shape),
            "finite": False,
            "allclose": False,
        }
    actual_cpu = actual.detach().float().cpu()
    expected_cpu = expected.detach().float().cpu()
    delta = actual_cpu - expected_cpu
    expected_l2_sq = float(expected_cpu.square().sum(dtype=torch.float64))
    expected_max = float(expected_cpu.abs().max())
    metrics = {
        "shape_match": True,
        "actual_dtype": str(actual.dtype),
        "expected_dtype": str(expected.dtype),
        "finite": bool(torch.isfinite(actual_cpu).all() and torch.isfinite(expected_cpu).all()),
        "max_abs": float(delta.abs().max()),
        "relative_l2": math.sqrt(
            float(delta.square().sum(dtype=torch.float64)) / max(expected_l2_sq, 1e-30)
        ),
        "normalized_max_abs": float(delta.abs().max()) / max(expected_max, 1e-30),
    }
    metrics["allclose"] = bool(
        metrics["finite"]
        and torch.allclose(actual_cpu, expected_cpu, rtol=1e-2, atol=1e-2)
    )
    return metrics


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
    unselected = [index for index in range(before.shape[0]) if index not in set(selected)]
    return exact_bytes(before[unselected], after[unselected])


def cpu_l2norm(value: torch.Tensor) -> torch.Tensor:
    value_fp32 = value.float()
    return (value_fp32 / torch.sqrt(value_fp32.square().sum(dim=-1, keepdim=True) + EPS)).to(
        value.dtype
    )


def cpu_reference_step(
    mixed_qkv: torch.Tensor,
    conv_weight_t: torch.Tensor,
    conv_bias: torch.Tensor,
    conv_state: torch.Tensor,
    a_log: torch.Tensor,
    a: torch.Tensor,
    b: torch.Tensor,
    dt_bias: torch.Tensor,
    recurrent_state: torch.Tensor,
    state_indices: torch.Tensor,
) -> dict[str, torch.Tensor]:
    """Independent one-token-per-sequence CPU formulation of the native chain."""
    indices = state_indices.tolist()
    conv_rows: list[torch.Tensor] = []
    for token, slot in enumerate(indices):
        window = torch.cat((conv_state[slot], mixed_qkv[token].unsqueeze(0)), dim=0)
        conv_state[slot].copy_(window[1:])
        accumulated = (window.float() * conv_weight_t.float()).sum(dim=0)
        conv_rows.append(F.silu(accumulated + conv_bias.float()).to(torch.bfloat16))
    conv_output = torch.stack(conv_rows, dim=0)

    q_width = H_QK * HEAD_DIM
    query, key, value = torch.split(
        conv_output,
        [q_width, q_width, H_V * HEAD_DIM],
        dim=-1,
    )
    query = cpu_l2norm(query.view(len(indices), H_QK, HEAD_DIM))
    key = cpu_l2norm(key.view(len(indices), H_QK, HEAD_DIM))
    value = value.view(len(indices), H_V, HEAD_DIM)

    softplus = F.softplus(a.float() + dt_bias.float())
    g = -torch.exp(a_log.float()) * softplus
    beta = torch.sigmoid(b.float()).to(b.dtype)

    query = query.repeat_interleave(H_V // H_QK, dim=1).float() * SCALE
    key = key.repeat_interleave(H_V // H_QK, dim=1).float()
    selected_state = recurrent_state[indices]
    selected_state = selected_state * torch.exp(g.float())[:, :, None, None]
    prediction = (selected_state * key[:, :, None, :]).sum(dim=-1)
    delta = (value.float() - prediction) * beta.float()[:, :, None]
    selected_state = selected_state + delta[:, :, :, None] * key[:, :, None, :]
    output = (selected_state * query[:, :, None, :]).sum(dim=-1).to(torch.bfloat16)
    recurrent_state[indices] = selected_state
    return {
        "output": output,
        "conv_output": conv_output,
        "query": query.to(torch.bfloat16),
        "key": key.to(torch.bfloat16),
        "value": value,
        "g": g,
        "beta": beta,
    }


def native_chain(
    mixed_qkv: torch.Tensor,
    conv_weight_t: torch.Tensor,
    conv_bias: torch.Tensor,
    conv_state: torch.Tensor,
    a_log: torch.Tensor,
    a: torch.Tensor,
    b: torch.Tensor,
    dt_bias: torch.Tensor,
    recurrent_state: torch.Tensor,
    query_start_loc: torch.Tensor,
    actual_seq_lengths: torch.Tensor,
    state_indices: torch.Tensor,
) -> dict[str, torch.Tensor]:
    from vllm.model_executor.layers.fla.ops.l2norm import l2norm_fwd
    from vllm_ascend.device.device_op import DeviceOperator

    conv_output = torch.empty_like(mixed_qkv)
    torch.ops._C_ascend.npu_causal_conv1d_custom(
        conv_output,
        mixed_qkv,
        conv_weight_t,
        conv_state=conv_state,
        bias_opt=conv_bias,
        query_start_loc_opt=query_start_loc,
        cache_indices_opt=state_indices,
        initial_state_mode_opt=None,
        num_accepted_tokens_opt=None,
        activation_mode=1,
        pad_slot_id=PAD_SLOT_ID,
        run_mode=1,
    )

    q_width = H_QK * HEAD_DIM
    query, key, value = torch.split(
        conv_output,
        [q_width, q_width, H_V * HEAD_DIM],
        dim=-1,
    )
    query = query.reshape(1, mixed_qkv.shape[0], H_QK, HEAD_DIM).contiguous()
    key = key.reshape(1, mixed_qkv.shape[0], H_QK, HEAD_DIM).contiguous()
    value = value.reshape(1, mixed_qkv.shape[0], H_V, HEAD_DIM).contiguous()
    g, beta = DeviceOperator.fused_gdn_gating(a_log, a, b, dt_bias)
    query = l2norm_fwd(query)
    key = l2norm_fwd(key)
    output = torch.ops._C_ascend.npu_recurrent_gated_delta_rule(
        query=query.squeeze(0),
        key=key.squeeze(0),
        value=value.squeeze(0),
        g=g.squeeze(0),
        beta=beta.squeeze(0),
        state=recurrent_state,
        scale=SCALE,
        actual_seq_lengths=actual_seq_lengths,
        ssm_state_indices=state_indices,
    )
    return {
        "output": output,
        "conv_output": conv_output,
        "query": query.squeeze(0),
        "key": key.squeeze(0),
        "value": value.squeeze(0),
        "g": g.squeeze(0),
        "beta": beta.squeeze(0),
    }


def make_case_inputs(batch: int) -> dict[str, Any]:
    generator = torch.Generator().manual_seed(20260920 + batch)
    slots = batch + 3
    cpu = {
        "conv_weight_t": (
            torch.randn((CONV_WIDTH, PACKED_WIDTH), generator=generator) / math.sqrt(CONV_WIDTH)
        ).to(torch.bfloat16),
        "conv_bias": (torch.randn((PACKED_WIDTH,), generator=generator) * 0.02).to(torch.bfloat16),
        "conv_state_initial": (
            torch.randn((slots, CONV_STATE_LEN, PACKED_WIDTH), generator=generator) * 0.05
        ).to(torch.bfloat16),
        "a_log": torch.log(torch.linspace(1.0, 16.0, H_V, dtype=torch.float32)),
        "dt_bias": torch.linspace(-0.5, 0.5, H_V, dtype=torch.float32),
        "recurrent_state_initial": torch.randn(
            (slots, H_V, HEAD_DIM, HEAD_DIM), generator=generator, dtype=torch.float32
        )
        * 0.01,
        "generator": generator,
    }
    return {"slots": slots, "cpu": cpu}


def copy_step_inputs(
    batch: int,
    slots: int,
    step: int,
    generator: torch.Generator,
    npu_groups: list[dict[str, torch.Tensor]],
) -> dict[str, torch.Tensor]:
    cpu = {
        "mixed_qkv": (
            torch.randn((batch, PACKED_WIDTH), generator=generator) * (0.07 + 0.005 * step)
        ).to(torch.bfloat16),
        "a": (torch.randn((batch, H_V), generator=generator) * 0.35).to(torch.bfloat16),
        "b": (torch.randn((batch, H_V), generator=generator) * 0.5).to(torch.bfloat16),
        "state_indices": ((torch.arange(batch, dtype=torch.int32) + step) % slots),
    }
    for group in npu_groups:
        for name, value in cpu.items():
            group[name].copy_(value)
    return cpu


def allocate_npu_group(batch: int, cpu: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    group = {
        "mixed_qkv": torch.zeros((batch, PACKED_WIDTH), dtype=torch.bfloat16, device="npu:0"),
        "a": torch.zeros((batch, H_V), dtype=torch.bfloat16, device="npu:0"),
        "b": torch.zeros((batch, H_V), dtype=torch.bfloat16, device="npu:0"),
        "state_indices": torch.zeros((batch,), dtype=torch.int32, device="npu:0"),
        "conv_weight_t": cpu["conv_weight_t"].to("npu:0"),
        "conv_bias": cpu["conv_bias"].to("npu:0"),
        "conv_state": cpu["conv_state_initial"].to("npu:0"),
        "a_log": cpu["a_log"].to("npu:0"),
        "dt_bias": cpu["dt_bias"].to("npu:0"),
        "recurrent_state": cpu["recurrent_state_initial"].to("npu:0"),
        "query_start_loc": torch.arange(batch + 1, dtype=torch.int32, device="npu:0"),
        "actual_seq_lengths": torch.cat(
            (torch.zeros(1, dtype=torch.int32), torch.ones(batch, dtype=torch.int32))
        ).to("npu:0"),
    }
    return group


def run_native(group: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    return native_chain(
        mixed_qkv=group["mixed_qkv"],
        conv_weight_t=group["conv_weight_t"],
        conv_bias=group["conv_bias"],
        conv_state=group["conv_state"],
        a_log=group["a_log"],
        a=group["a"],
        b=group["b"],
        dt_bias=group["dt_bias"],
        recurrent_state=group["recurrent_state"],
        query_start_loc=group["query_start_loc"],
        actual_seq_lengths=group["actual_seq_lengths"],
        state_indices=group["state_indices"],
    )


def run_case(batch: int, report_case: dict[str, Any], save: Any) -> None:
    setup = make_case_inputs(batch)
    slots = setup["slots"]
    cpu = setup["cpu"]
    eager = allocate_npu_group(batch, cpu)
    graph_group = allocate_npu_group(batch, cpu)
    reference_conv_state = cpu["conv_state_initial"].clone()
    reference_recurrent_state = cpu["recurrent_state_initial"].clone()
    graph: torch_npu.npu.NPUGraph | None = None

    report_case.update(
        status="running",
        batch=batch,
        slots=slots,
        steps=[],
        shapes={
            "mixed_qkv": [batch, PACKED_WIDTH],
            "conv_state": [slots, CONV_STATE_LEN, PACKED_WIDTH],
            "recurrent_state": [slots, H_V, HEAD_DIM, HEAD_DIM],
            "output": [batch, H_V, HEAD_DIM],
        },
    )
    save()
    try:
        # Compile and allocate every kernel before graph capture.
        for warmup in range(3):
            copy_step_inputs(batch, slots, warmup, cpu["generator"], [graph_group])
            run_native(graph_group)
            torch.npu.synchronize()
        graph_group["conv_state"].copy_(cpu["conv_state_initial"])
        graph_group["recurrent_state"].copy_(cpu["recurrent_state_initial"])
        torch.npu.synchronize()

        graph = torch.npu.NPUGraph()
        with torch.npu.graph(graph):
            graph_outputs = run_native(graph_group)
        torch.npu.synchronize()
        graph_group["conv_state"].copy_(cpu["conv_state_initial"])
        graph_group["recurrent_state"].copy_(cpu["recurrent_state_initial"])
        torch.npu.synchronize()

        tracked = {
            **{f"eager.{name}": value for name, value in eager.items()},
            **{f"graph.{name}": value for name, value in graph_group.items()},
            **{f"graph.output.{name}": value for name, value in graph_outputs.items()},
        }
        metadata = {name: tensor_metadata(value) for name, value in tracked.items()}
        report_case["tracked_tensor_metadata"] = metadata
        save()

        for step in range(STEPS):
            step_cpu = copy_step_inputs(
                batch,
                slots,
                step,
                cpu["generator"],
                [eager, graph_group],
            )
            selected = step_cpu["state_indices"].tolist()
            eager_conv_before = eager["conv_state"].detach().cpu()
            graph_conv_before = graph_group["conv_state"].detach().cpu()
            eager_recurrent_before = eager["recurrent_state"].detach().cpu()
            graph_recurrent_before = graph_group["recurrent_state"].detach().cpu()

            expected = cpu_reference_step(
                mixed_qkv=step_cpu["mixed_qkv"],
                conv_weight_t=cpu["conv_weight_t"],
                conv_bias=cpu["conv_bias"],
                conv_state=reference_conv_state,
                a_log=cpu["a_log"],
                a=step_cpu["a"],
                b=step_cpu["b"],
                dt_bias=cpu["dt_bias"],
                recurrent_state=reference_recurrent_state,
                state_indices=step_cpu["state_indices"],
            )
            eager_outputs = run_native(eager)
            graph.replay()
            torch.npu.synchronize()

            eager_conv_after = eager["conv_state"].detach().cpu()
            graph_conv_after = graph_group["conv_state"].detach().cpu()
            eager_recurrent_after = eager["recurrent_state"].detach().cpu()
            graph_recurrent_after = graph_group["recurrent_state"].detach().cpu()
            observed_metadata = {name: tensor_metadata(value) for name, value in tracked.items()}

            checks = {
                "eager_output_vs_cpu": error_metrics(eager_outputs["output"], expected["output"]),
                "graph_output_vs_cpu": error_metrics(graph_outputs["output"], expected["output"]),
                "eager_conv_output_vs_cpu": error_metrics(
                    eager_outputs["conv_output"], expected["conv_output"]
                ),
                "graph_conv_output_vs_cpu": error_metrics(
                    graph_outputs["conv_output"], expected["conv_output"]
                ),
                "eager_recurrent_state_vs_cpu": error_metrics(
                    eager_recurrent_after, reference_recurrent_state
                ),
                "graph_recurrent_state_vs_cpu": error_metrics(
                    graph_recurrent_after, reference_recurrent_state
                ),
            }
            booleans = {
                "eager_graph_output_exact": exact_bytes(
                    eager_outputs["output"], graph_outputs["output"]
                ),
                "eager_graph_conv_output_exact": exact_bytes(
                    eager_outputs["conv_output"], graph_outputs["conv_output"]
                ),
                "eager_graph_conv_state_exact": exact_bytes(
                    eager_conv_after, graph_conv_after
                ),
                "eager_graph_recurrent_state_exact": exact_bytes(
                    eager_recurrent_after, graph_recurrent_after
                ),
                "eager_conv_state_vs_cpu_exact": exact_bytes(
                    eager_conv_after, reference_conv_state
                ),
                "graph_conv_state_vs_cpu_exact": exact_bytes(
                    graph_conv_after, reference_conv_state
                ),
                "eager_conv_unselected_unchanged": unchanged_slots(
                    eager_conv_before, eager_conv_after, selected
                ),
                "graph_conv_unselected_unchanged": unchanged_slots(
                    graph_conv_before, graph_conv_after, selected
                ),
                "eager_recurrent_unselected_unchanged": unchanged_slots(
                    eager_recurrent_before, eager_recurrent_after, selected
                ),
                "graph_recurrent_unselected_unchanged": unchanged_slots(
                    graph_recurrent_before, graph_recurrent_after, selected
                ),
                "tensor_metadata_unchanged": metadata == observed_metadata,
                "all_full_states_finite": bool(
                    torch.isfinite(eager_conv_after).all()
                    and torch.isfinite(graph_conv_after).all()
                    and torch.isfinite(eager_recurrent_after).all()
                    and torch.isfinite(graph_recurrent_after).all()
                ),
            }
            failed = [name for name, value in booleans.items() if not value]
            failed.extend(name for name, value in checks.items() if not value.get("allclose", False))
            step_record = {
                "step": step + 1,
                "selected_slots": selected,
                "numeric": checks,
                "invariants": booleans,
                "passed": not failed,
                "failed_checks": failed,
            }
            report_case["steps"].append(step_record)
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
                raise RuntimeError(f"batch={batch} step={step + 1} failed: {failed}")
        report_case.update(status="passed", passed=True)
    except BaseException as error:
        report_case.update(
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
                report_case["graph_cleanup_error"] = repr(cleanup_error)
                if sys.exc_info()[1] is None:
                    report_case.update(status="failed", passed=False)
                    raise
        save()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    allowed_root = Path("/gdn-megaop-results")
    if allowed_root not in output_dir.parents or output_dir.exists():
        parser.error("a fresh directory below /gdn-megaop-results is required")
    if os.environ.get("ASCEND_RT_VISIBLE_DEVICES") != "0":
        parser.error("requires audited container logical NPU0 mapped to physical NPU4")

    source = Path("/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py")
    output_dir.mkdir(parents=True)
    report: dict[str, Any] = {
        "schema": "qwen36-gdn-decode-golden-probe/v1",
        "status": "running",
        "created_unix_ns": time.time_ns(),
        "script_sha256": sha256(Path(__file__)),
        "device_contract": "container logical NPU0; externally audited physical NPU4",
        "limits": (
            "Native-chain numerical/state/graph oracle only; not a custom-operator, "
            "service-performance, cache-manager, or task-accuracy result."
        ),
        "protocol": {
            "batches": list(BATCHES),
            "steps": STEPS,
            "tp_local_shape": {
                "qk_heads": H_QK,
                "value_heads": H_V,
                "head_dim": HEAD_DIM,
                "packed_width": PACKED_WIDTH,
            },
            "activation_dtype": "bfloat16",
            "recurrent_state_dtype": "float32",
            "cpu_oracle_tolerance": {"rtol": 1e-2, "atol": 1e-2},
            "eager_graph_parity": "finite logical tensor bytes exactly equal",
            "state_indices": "unique cyclic slots changed every step",
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
        if not source.is_file():
            raise RuntimeError(f"missing runtime source: {source}")
        report["ascend_gdn_sha256"] = sha256(source)
        if report["ascend_gdn_sha256"] != ASCEND_GDN_SHA256:
            raise RuntimeError("vLLM-Ascend GDN source identity changed; re-audit before running")

        from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton
        from vllm_ascend.utils import enable_custom_op

        torch_npu.npu.set_compile_mode(jit_compile=False)
        if not enable_custom_op():
            raise RuntimeError("vLLM-Ascend custom operators are unavailable")
        torch.npu.set_device(0)
        init_device_properties_triton()
        report.update(
            torch_version=torch.__version__,
            torch_npu_version=torch_npu.__version__,
            custom_opp_path=os.environ.get("ASCEND_CUSTOM_OPP_PATH"),
            operator_schemas={
                "causal_conv": str(torch.ops._C_ascend.npu_causal_conv1d_custom.default._schema),
                "gating": str(torch.ops._C_ascend.npu_fused_gdn_gating.default._schema),
                "recurrent": str(
                    torch.ops._C_ascend.npu_recurrent_gated_delta_rule.default._schema
                ),
            },
        )
        save()
        for batch in BATCHES:
            case_record: dict[str, Any] = {"batch": batch, "status": "pending", "passed": False}
            report["cases"].append(case_record)
            save()
            run_case(batch, case_record, save)
        report["status"] = "native_gdn_decode_golden_gate_pass"
    except BaseException as error:
        report.update(status="failed", error=repr(error), error_type=type(error).__name__)
        raise
    finally:
        try:
            libraries = sorted(
                {
                    line.split()[-1]
                    for line in Path("/proc/self/maps").read_text().splitlines()
                    if "/" in line
                    and (
                        "/vllm_ascend/" in line
                        or "libcust_opapi" in line
                        or "libopapi" in line
                    )
                }
            )
            report["loaded_libraries"] = [
                {"path": path, "sha256": sha256(Path(path))}
                for path in libraries
                if Path(path).is_file()
            ]
        except BaseException as evidence_error:
            report["library_evidence_error"] = repr(evidence_error)
            report["status"] = "failed"
        report["completed_unix_ns"] = time.time_ns()
        save()
    if report["status"] != "native_gdn_decode_golden_gate_pass":
        raise RuntimeError("native GDN decode golden evidence is incomplete")
    print(
        json.dumps(
            {"status": report["status"], "report": str(output_dir / "report.json")}
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()

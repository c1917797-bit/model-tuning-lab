#!/usr/bin/env python3
"""Real-NPU equation gate for the DeltaLog Qwen3.6 GDN adaptation.

This intentionally uses ordinary torch/NPU tensor operations for the DeltaLog
side and the deployed vLLM-Ascend recurrent custom op as the oracle.  It proves
the paper equations and frozen numerical bounds before an AscendC kernel is
written.  It is not a performance candidate and must never be used as E2E
evidence: the reference implementation may materialize temporary logical
states and writes selected tensors through generic index_copy operations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import time
from typing import Any

import torch
import torch_npu


H_QK = 4
H_V = 12
D = 128
CAPACITY = 7
STEPS = 128
SCALE = D**-0.5
BATCHES = (1, 16)
OUTPUT_RELATIVE_LIMIT = 0.00303
STATE_RELATIVE_L2_LIMIT = 7.92e-7
ASCEND_GDN_SHA256 = "d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_max_error(actual: torch.Tensor, expected: torch.Tensor) -> float:
    actual_cpu = actual.detach().float().cpu()
    expected_cpu = expected.detach().float().cpu()
    return float((actual_cpu - expected_cpu).abs().max()) / max(
        float(expected_cpu.abs().max()), 1.0e-30
    )


def relative_l2(actual: torch.Tensor, expected: torch.Tensor) -> float:
    delta = (actual.detach().float() - expected.detach().float()).double().cpu()
    reference = expected.detach().float().double().cpu()
    return math.sqrt(
        float(delta.square().sum()) / max(float(reference.square().sum()), 1.0e-30)
    )


def finite(tensor: torch.Tensor) -> bool:
    return bool(torch.isfinite(tensor).all().cpu())


def make_inputs(batch: int, slots: int, step: int, generator: torch.Generator) -> dict[str, torch.Tensor]:
    query = torch.randn((batch, H_QK, D), generator=generator, dtype=torch.float32)
    key = torch.randn((batch, H_QK, D), generator=generator, dtype=torch.float32)
    query = torch.nn.functional.normalize(query, dim=-1).to(torch.bfloat16)
    key = torch.nn.functional.normalize(key, dim=-1).to(torch.bfloat16)
    value = (torch.randn((batch, H_V, D), generator=generator) * 0.2).to(torch.bfloat16)
    gate_seed = torch.rand((batch, H_V), generator=generator)
    g = -(0.002 + 0.18 * gate_seed).to(torch.float32)
    beta = torch.sigmoid(torch.randn((batch, H_V), generator=generator)).to(torch.bfloat16)
    indices = (torch.arange(batch, dtype=torch.int32) + step) % slots
    return {
        "query": query.to("npu:0"),
        "key": key.to("npu:0"),
        "value": value.to("npu:0"),
        "g": g.to("npu:0"),
        "beta": beta.to("npu:0"),
        "indices": indices.to("npu:0"),
    }


def materialize_selected(state: dict[str, torch.Tensor], indices64: torch.Tensor) -> torch.Tensor:
    base = state["base"].index_select(0, indices64)
    k_log = state["k_log"].index_select(0, indices64).float()
    u_log = state["u_log"].index_select(0, indices64)
    lambda_log = state["lambda_log"].index_select(0, indices64)
    decay = state["decay"].index_select(0, indices64)
    length = state["length"].index_select(0, indices64)
    live = (
        torch.arange(CAPACITY, dtype=torch.int32, device="npu:0").view(1, 1, CAPACITY)
        < length.view(-1, 1, 1)
    )
    coefficients = torch.exp(decay.unsqueeze(-1) - lambda_log) * live.float()
    contribution = torch.einsum("thl,thlv,thlk->thvk", coefficients, u_log, k_log)
    return torch.exp(decay).unsqueeze(-1).unsqueeze(-1) * base + contribution


def deltalog_step(
    state: dict[str, torch.Tensor], inputs: dict[str, torch.Tensor]
) -> tuple[torch.Tensor, torch.Tensor]:
    indices64 = inputs["indices"].long()
    logical_previous = materialize_selected(state, indices64)
    q_heads = torch.repeat_interleave(inputs["query"].float(), 3, dim=1) * SCALE
    k_heads = torch.repeat_interleave(inputs["key"].float(), 3, dim=1)
    decayed_previous = torch.exp(inputs["g"]).unsqueeze(-1).unsqueeze(-1) * logical_previous
    prediction = torch.einsum("thvk,thk->thv", decayed_previous, k_heads)
    update = inputs["beta"].float().unsqueeze(-1) * (inputs["value"].float() - prediction)
    logical_next = decayed_previous + update.unsqueeze(-1) * k_heads.unsqueeze(-2)
    output = torch.einsum("thvk,thk->thv", logical_next, q_heads).to(torch.bfloat16)

    selected_base = state["base"].index_select(0, indices64)
    selected_k = state["k_log"].index_select(0, indices64)
    selected_u = state["u_log"].index_select(0, indices64)
    selected_lambda = state["lambda_log"].index_select(0, indices64)
    selected_decay = state["decay"].index_select(0, indices64)
    selected_length = state["length"].index_select(0, indices64)
    append = selected_length < CAPACITY
    merge = torch.logical_not(append)
    position = torch.minimum(
        selected_length,
        torch.full_like(selected_length, CAPACITY - 1),
    )
    position4 = (
        torch.arange(CAPACITY, dtype=torch.int32, device="npu:0").view(1, 1, CAPACITY, 1)
        == position.view(-1, 1, 1, 1)
    )
    append4 = append.view(-1, 1, 1, 1)
    merge4 = merge.view(-1, 1, 1, 1)
    next_k = torch.where(position4 & append4, k_heads.unsqueeze(2).to(torch.bfloat16), selected_k)
    next_u = torch.where(position4 & append4, update.unsqueeze(2), selected_u)
    next_k = torch.where(merge4, torch.zeros_like(next_k), next_k)
    next_u = torch.where(merge4, torch.zeros_like(next_u), next_u)
    position3 = position4.squeeze(-1)
    append3 = append.view(-1, 1, 1)
    next_decay = selected_decay + inputs["g"]
    next_lambda = torch.where(position3 & append3, next_decay.unsqueeze(-1), selected_lambda)
    next_lambda = torch.where(merge.view(-1, 1, 1), torch.zeros_like(next_lambda), next_lambda)
    next_base = torch.where(merge4, logical_next, selected_base)
    next_cumulative = torch.where(merge.view(-1, 1), torch.zeros_like(next_decay), next_decay)
    next_length = torch.where(append, selected_length + 1, torch.zeros_like(selected_length))

    # Generic index_copy is used only by this equation oracle.  The AscendC
    # candidate must avoid writing base on append steps.
    state["base"].index_copy_(0, indices64, next_base)
    state["k_log"].index_copy_(0, indices64, next_k)
    state["u_log"].index_copy_(0, indices64, next_u)
    state["lambda_log"].index_copy_(0, indices64, next_lambda)
    state["decay"].index_copy_(0, indices64, next_cumulative)
    state["length"].index_copy_(0, indices64, next_length)
    return output, merge


def native_step(
    native_state: torch.Tensor,
    inputs: dict[str, torch.Tensor],
    actual_seq_lengths: torch.Tensor,
) -> torch.Tensor:
    return torch.ops._C_ascend.npu_recurrent_gated_delta_rule(
        query=inputs["query"],
        key=inputs["key"],
        value=inputs["value"],
        g=inputs["g"],
        beta=inputs["beta"],
        state=native_state,
        scale=SCALE,
        actual_seq_lengths=actual_seq_lengths,
        ssm_state_indices=inputs["indices"],
    )


def run_case(batch: int, report: dict[str, Any], save: Any) -> None:
    slots = batch + 3
    generator = torch.Generator().manual_seed(260815533 + batch)
    initial = (
        torch.randn((slots, H_V, D, D), generator=generator, dtype=torch.float32) * 0.005
    )
    native_state = initial.to("npu:0")
    delta_state = {
        "base": initial.to("npu:0"),
        "k_log": torch.zeros((slots, H_V, CAPACITY, D), dtype=torch.bfloat16, device="npu:0"),
        "u_log": torch.zeros((slots, H_V, CAPACITY, D), dtype=torch.float32, device="npu:0"),
        "lambda_log": torch.zeros((slots, H_V, CAPACITY), dtype=torch.float32, device="npu:0"),
        "decay": torch.zeros((slots, H_V), dtype=torch.float32, device="npu:0"),
        "length": torch.zeros((slots,), dtype=torch.int32, device="npu:0"),
    }
    actual_seq_lengths = torch.cat(
        (torch.zeros(1, dtype=torch.int32), torch.ones(batch, dtype=torch.int32))
    ).to("npu:0")
    case: dict[str, Any] = {
        "batch": batch,
        "slots": slots,
        "status": "running",
        "steps": [],
        "max_output_normalized_error": 0.0,
        "max_merge_state_relative_l2": 0.0,
        "merge_observations": 0,
    }
    report["cases"].append(case)
    save()
    try:
        for step in range(STEPS):
            inputs = make_inputs(batch, slots, step, generator)
            expected = native_step(native_state, inputs, actual_seq_lengths)
            actual, merge = deltalog_step(delta_state, inputs)
            torch.npu.synchronize()
            output_error = normalized_max_error(actual, expected)
            output_finite = finite(actual) and finite(expected)
            merged = bool(merge.any().cpu())
            state_error = None
            state_finite = True
            if merged:
                indices64 = inputs["indices"].long()
                logical = materialize_selected(delta_state, indices64)
                expected_state = native_state.index_select(0, indices64)
                state_error = relative_l2(logical, expected_state)
                state_finite = finite(logical) and finite(expected_state)
                case["merge_observations"] += 1
                case["max_merge_state_relative_l2"] = max(
                    case["max_merge_state_relative_l2"], state_error
                )
            case["max_output_normalized_error"] = max(
                case["max_output_normalized_error"], output_error
            )
            passed = (
                output_finite
                and state_finite
                and output_error <= OUTPUT_RELATIVE_LIMIT
                and (state_error is None or state_error <= STATE_RELATIVE_L2_LIMIT)
            )
            case["steps"].append(
                {
                    "step": step + 1,
                    "output_normalized_error": output_error,
                    "merge_observed": merged,
                    "merge_state_relative_l2": state_error,
                    "output_finite": output_finite,
                    "state_finite": state_finite,
                    "passed": passed,
                }
            )
            save()
            if not passed:
                raise RuntimeError(
                    f"batch={batch} step={step + 1} output_error={output_error} state_error={state_error}"
                )
        case["status"] = "passed"
        case["passed"] = True
    except BaseException as error:
        case.update(status="failed", passed=False, error=repr(error))
        raise
    finally:
        save()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    allowed_root = Path("/deltalog-results")
    if allowed_root not in output_dir.parents or output_dir.exists():
        parser.error("a fresh output directory below /deltalog-results is required")
    if os.environ.get("ASCEND_RT_VISIBLE_DEVICES") != "0":
        parser.error("requires container logical NPU0 mapped to physical NPU4")
    source = Path("/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py")
    output_dir.mkdir(parents=True)
    report: dict[str, Any] = {
        "schema": "qwen36-deltalog-equation-npu-probe/v1",
        "status": "running",
        "created_unix_ns": time.time_ns(),
        "script_sha256": sha256(Path(__file__)),
        "device_contract": "container logical NPU0 mapped to physical NPU4",
        "limits": "Equation-level real-NPU evidence only; generic torch/NPU reference is not a performance implementation.",
        "protocol": {
            "batches": list(BATCHES),
            "steps": STEPS,
            "merge_interval": CAPACITY + 1,
            "output_normalized_max_limit": OUTPUT_RELATIVE_LIMIT,
            "merge_state_relative_l2_limit": STATE_RELATIVE_L2_LIMIT,
            "retry_budget": "one run; preserve first failure",
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
        report.update(
            torch_version=torch.__version__,
            torch_npu_version=torch_npu.__version__,
            native_schema=str(torch.ops._C_ascend.npu_recurrent_gated_delta_rule.default._schema),
        )
        save()
        for batch in BATCHES:
            run_case(batch, report, save)
        report["status"] = "deltalog_equation_gate_pass"
    except BaseException as error:
        report.update(status="failed", error=repr(error), error_type=type(error).__name__)
        raise
    finally:
        report["completed_unix_ns"] = time.time_ns()
        save()
    print(json.dumps({"status": report["status"], "report": str(output_dir / "report.json")}))


if __name__ == "__main__":
    main()

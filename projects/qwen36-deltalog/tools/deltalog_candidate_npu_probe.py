#!/usr/bin/env python3
"""One-shot real-NPU eager gate for the direct-invoke DeltaLog AscendC op."""

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

H_QK, H_V, D, CAPACITY = 4, 12, 128, 7
SCALE = D**-0.5
STEPS = 128
BATCHES = (1, 16)
OUTPUT_LIMIT = 0.00303
STATE_LIMIT = 7.92e-7
ASCEND_GDN_SHA256 = "d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_max_error(actual: torch.Tensor, expected: torch.Tensor) -> float:
    a, e = actual.detach().float().cpu(), expected.detach().float().cpu()
    return float((a - e).abs().max()) / max(float(e.abs().max()), 1.0e-30)


def relative_l2(actual: torch.Tensor, expected: torch.Tensor) -> float:
    delta = (actual.detach().float() - expected.detach().float()).double().cpu()
    reference = expected.detach().float().double().cpu()
    return math.sqrt(float(delta.square().sum()) / max(float(reference.square().sum()), 1.0e-30))


def make_inputs(batch: int, slots: int, step: int, gen: torch.Generator) -> dict[str, torch.Tensor]:
    q = torch.nn.functional.normalize(torch.randn((batch, H_QK, D), generator=gen), dim=-1)
    k = torch.nn.functional.normalize(torch.randn((batch, H_QK, D), generator=gen), dim=-1)
    return {
        "query": q.to(torch.bfloat16).to("npu:0"),
        "key": k.to(torch.bfloat16).to("npu:0"),
        "value": (torch.randn((batch, H_V, D), generator=gen) * 0.2).to(torch.bfloat16).to("npu:0"),
        "g": (-(0.002 + 0.18 * torch.rand((batch, H_V), generator=gen))).to("npu:0"),
        "beta": torch.sigmoid(torch.randn((batch, H_V), generator=gen)).to(torch.bfloat16).to("npu:0"),
        "indices": ((torch.arange(batch, dtype=torch.int32) + step) % slots).to("npu:0"),
    }


def materialize_selected(state: dict[str, torch.Tensor], indices64: torch.Tensor) -> torch.Tensor:
    base = state["base"].index_select(0, indices64)
    k_log = state["k_log"].index_select(0, indices64).float()
    u_log = state["u_log"].index_select(0, indices64)
    lambda_log = state["lambda_log"].index_select(0, indices64)[:, :, :CAPACITY]
    decay = state["decay"].index_select(0, indices64)[:, :, 0]
    length = state["length"].index_select(0, indices64)[:, :, 0]
    live = torch.arange(CAPACITY, dtype=torch.int32, device="npu:0").view(1, 1, CAPACITY) < length.unsqueeze(-1)
    coeff = torch.exp(decay.unsqueeze(-1) - lambda_log) * live.float()
    contribution = torch.einsum("thl,thlv,thlk->thvk", coeff, u_log, k_log)
    return torch.exp(decay).unsqueeze(-1).unsqueeze(-1) * base + contribution


def native_step(state: torch.Tensor, inputs: dict[str, torch.Tensor], seq: torch.Tensor) -> torch.Tensor:
    return torch.ops._C_ascend.npu_recurrent_gated_delta_rule(
        query=inputs["query"], key=inputs["key"], value=inputs["value"],
        g=inputs["g"], beta=inputs["beta"], state=state, scale=SCALE,
        actual_seq_lengths=seq, ssm_state_indices=inputs["indices"])


def candidate_step(state: dict[str, torch.Tensor], inputs: dict[str, torch.Tensor], seq: torch.Tensor) -> torch.Tensor:
    return torch.ops.qwen36_deltalog.decode(
        inputs["query"], inputs["key"], inputs["value"], inputs["g"], inputs["beta"],
        state["base"], state["k_log"], state["u_log"], state["lambda_log"],
        state["decay"], state["length"], seq, inputs["indices"])


def run_case(batch: int, report: dict[str, Any], save: Any) -> None:
    slots = batch + 3
    gen = torch.Generator().manual_seed(260815533 + batch)
    initial = (torch.randn((slots, H_V, D, D), generator=gen) * 0.005).float()
    native = initial.to("npu:0")
    state = {
        "base": initial.to("npu:0"),
        "k_log": torch.zeros((slots, H_V, CAPACITY, D), dtype=torch.bfloat16, device="npu:0"),
        "u_log": torch.zeros((slots, H_V, CAPACITY, D), dtype=torch.float32, device="npu:0"),
        "lambda_log": torch.zeros((slots, H_V, 8), dtype=torch.float32, device="npu:0"),
        "decay": torch.zeros((slots, H_V, 8), dtype=torch.float32, device="npu:0"),
        "length": torch.zeros((slots, H_V, 8), dtype=torch.int32, device="npu:0"),
    }
    pointers = {name: tensor.untyped_storage().data_ptr() for name, tensor in state.items()}
    seq = torch.cat((torch.zeros(1, dtype=torch.int32), torch.ones(batch, dtype=torch.int32))).to("npu:0")
    case: dict[str, Any] = {"batch": batch, "slots": slots, "status": "running", "steps": [],
                            "max_output_normalized_error": 0.0, "max_state_relative_l2": 0.0,
                            "merge_observations": 0}
    report["cases"].append(case)
    save()
    try:
        for step in range(STEPS):
            inputs = make_inputs(batch, slots, step, gen)
            idx64 = inputs["indices"].long()
            length_before = state["length"].index_select(0, idx64)[:, :, 0].clone()
            base_before = state["base"].index_select(0, idx64).clone()
            expected = native_step(native, inputs, seq)
            actual = candidate_step(state, inputs, seq)
            torch.npu.synchronize()
            merge = length_before == CAPACITY
            append = torch.logical_not(merge)
            output_error = normalized_max_error(actual, expected)
            logical = materialize_selected(state, idx64)
            expected_state = native.index_select(0, idx64)
            state_error = relative_l2(logical, expected_state)
            base_after = state["base"].index_select(0, idx64)
            append_base_unchanged = bool(torch.equal(base_after[append[:, 0]], base_before[append[:, 0]]))
            length_after = state["length"].index_select(0, idx64)[:, :, 0]
            length_heads_equal = bool(torch.equal(length_after, length_after[:, :1].expand(-1, H_V)))
            pointers_stable = pointers == {name: tensor.untyped_storage().data_ptr() for name, tensor in state.items()}
            finite = bool(torch.isfinite(actual).all().cpu() and torch.isfinite(logical).all().cpu())
            merged = bool(merge.any().cpu())
            if merged:
                case["merge_observations"] += 1
            case["max_output_normalized_error"] = max(case["max_output_normalized_error"], output_error)
            case["max_state_relative_l2"] = max(case["max_state_relative_l2"], state_error)
            passed = (finite and output_error <= OUTPUT_LIMIT and state_error <= STATE_LIMIT
                      and append_base_unchanged and length_heads_equal and pointers_stable)
            diagnostics = None
            if not (finite and output_error <= OUTPUT_LIMIT and state_error <= STATE_LIMIT
                    and append_base_unchanged and length_heads_equal and pointers_stable):
                diagnostics = {
                    "length_after": length_after.cpu().tolist(),
                    "decay_after": state["decay"].index_select(0, idx64)[:, :, 0].cpu().tolist(),
                    "lambda0_after": state["lambda_log"].index_select(0, idx64)[:, :, 0].cpu().tolist(),
                    "k_log_abs_sum_per_head": state["k_log"].index_select(0, idx64)[:, :, 0].float().abs().sum(-1).cpu().tolist(),
                    "u_log_abs_sum_per_head": state["u_log"].index_select(0, idx64)[:, :, 0].abs().sum(-1).cpu().tolist(),
                }
            case["steps"].append({"step": step + 1, "output_normalized_error": output_error,
                                  "state_relative_l2": state_error, "merge_observed": merged,
                                  "append_base_unchanged": append_base_unchanged,
                                  "length_heads_equal": length_heads_equal,
                                  "pointers_stable": pointers_stable, "finite": finite,
                                  "diagnostics": diagnostics, "passed": passed})
            save()
            if not passed:
                raise RuntimeError(f"batch={batch} step={step + 1} output={output_error} state={state_error}")
        case.update(status="passed", passed=True)
    except BaseException as error:
        case.update(status="failed", passed=False, error=repr(error))
        raise
    finally:
        save()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--physical-device", required=True, type=int, choices=range(4, 8))
    args = parser.parse_args()
    library, output_dir = args.library.resolve(), args.output_dir.resolve()
    if Path("/deltalog-results") not in output_dir.parents or output_dir.exists():
        parser.error("a fresh output directory below /deltalog-results is required")
    if os.environ.get("ASCEND_RT_VISIBLE_DEVICES") != "0":
        parser.error("requires container logical NPU0; the launcher must map the declared physical NPU")
    if not library.is_file():
        parser.error("candidate library is missing")
    output_dir.mkdir(parents=True)
    report: dict[str, Any] = {
        "schema": "qwen36-deltalog-ascendc-eager-gate/v1", "status": "running",
        "created_unix_ns": time.time_ns(), "script_sha256": sha256(Path(__file__)),
        "library": str(library), "library_sha256": sha256(library),
        "device_contract": f"container logical NPU0 mapped to physical NPU{args.physical_device}",
        "protocol": {"batches": list(BATCHES), "steps": STEPS,
                     "output_limit": OUTPUT_LIMIT, "state_relative_l2_limit": STATE_LIMIT,
                     "retry_budget": "one run; preserve first failure"}, "cases": []}

    def save() -> None:
        (output_dir / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")

    save()
    try:
        source = Path("/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py")
        if not source.is_file() or sha256(source) != ASCEND_GDN_SHA256:
            raise RuntimeError("vLLM-Ascend source identity changed")
        from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton
        from vllm_ascend.utils import enable_custom_op
        torch_npu.npu.set_compile_mode(jit_compile=False)
        if not enable_custom_op():
            raise RuntimeError("custom operators unavailable")
        torch.npu.set_device(0)
        init_device_properties_triton()
        torch.ops.load_library(str(library))
        report["candidate_schema"] = str(torch.ops.qwen36_deltalog.decode.default._schema)
        save()
        for batch in BATCHES:
            run_case(batch, report, save)
        report["status"] = "ascendc_eager_gate_pass"
    except BaseException as error:
        report.update(status="failed", error=repr(error), error_type=type(error).__name__)
        raise
    finally:
        report["completed_unix_ns"] = time.time_ns()
        save()
    print(json.dumps({"status": report["status"], "report": str(output_dir / "report.json")}))


if __name__ == "__main__":
    main()

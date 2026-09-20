#!/usr/bin/env python3
"""One-shot eager diagnostic that isolates fused GDN decode-core stages."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import time

import torch
import torch_npu

from gdn_decode_core_candidate_probe import (
    HEAD_DIM,
    H_QK,
    H_V,
    PACKED_WIDTH,
    error_metrics,
    run_candidate,
    run_native,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_safe(value: object) -> object:
    if isinstance(value, float) and not math.isfinite(value):
        return {"nonfinite": repr(value)}
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    return value


def make_group(
    packed_qkv: torch.Tensor,
    a: torch.Tensor,
    b: torch.Tensor,
    state: torch.Tensor,
) -> dict[str, torch.Tensor]:
    return {
        "packed_qkv": packed_qkv.to("npu:0"),
        "a_log": torch.zeros(H_V, dtype=torch.float32, device="npu:0"),
        "a": a.to("npu:0"),
        "b": b.to("npu:0"),
        "dt_bias": torch.zeros(H_V, dtype=torch.bfloat16, device="npu:0"),
        "state": state.to("npu:0"),
        "actual_seq_lengths": torch.tensor(
            [0, 1], dtype=torch.int32, device="npu:0"
        ),
        "state_indices": torch.tensor([0], dtype=torch.int32, device="npu:0"),
    }


def summarize(tensor: torch.Tensor) -> dict[str, object]:
    value = tensor.detach().float().cpu()
    return {
        "finite": bool(torch.isfinite(value).all()),
        "min": float(value.min()),
        "max": float(value.max()),
        "l2": float(torch.linalg.vector_norm(value)),
        "first16": value.flatten()[:16].tolist(),
    }


def per_head_half_errors(
    actual: torch.Tensor, expected: torch.Tensor
) -> list[dict[str, object]]:
    actual_cpu = actual.detach().float().cpu()
    expected_cpu = expected.detach().float().cpu()
    if actual_cpu.ndim == 4 or (
        actual_cpu.ndim == 3 and actual_cpu.shape[0] == 1
    ):
        actual_cpu = actual_cpu[0]
        expected_cpu = expected_cpu[0]
    if actual_cpu.ndim not in (2, 3) or actual_cpu.shape[0] != H_V:
        raise ValueError(f"unexpected [head, value, ...] shape: {actual_cpu.shape}")
    value_extent = actual_cpu.shape[1]
    split = value_extent // 2
    result: list[dict[str, object]] = []
    for head in range(H_V):
        head_record: dict[str, object] = {"head": head, "halves": []}
        for half, (start, end) in enumerate(((0, split), (split, value_extent))):
            actual_slice = actual_cpu[head, start:end]
            expected_slice = expected_cpu[head, start:end]
            delta = actual_slice - expected_slice
            expected_l2 = float(torch.linalg.vector_norm(expected_slice))
            actual_l2 = float(torch.linalg.vector_norm(actual_slice))
            head_record["halves"].append(
                {
                    "half": half,
                    "max_abs": float(delta.abs().max()),
                    "actual_l2": actual_l2,
                    "expected_l2": expected_l2,
                    "l2_ratio": actual_l2 / expected_l2 if expected_l2 else None,
                }
            )
        result.append(head_record)
    return result


def run_case(
    name: str,
    packed: torch.Tensor,
    state: torch.Tensor,
    *,
    a: torch.Tensor | None = None,
    b: torch.Tensor | None = None,
) -> dict[str, object]:
    if a is None:
        a = torch.zeros((1, H_V), dtype=torch.bfloat16)
    if b is None:
        b = torch.zeros((1, H_V), dtype=torch.bfloat16)
    native = make_group(packed, a, b, state.clone())
    candidate = make_group(packed, a, b, state.clone())
    native_output = run_native(native)
    candidate_output = run_candidate(candidate)
    torch.npu.synchronize()
    native_state = native["state"].detach()
    candidate_state = candidate["state"].detach()
    return {
        "name": name,
        "output_error": error_metrics(
            candidate_output, native_output, rtol=1e-2, atol=1e-2
        ),
        "state_error": error_metrics(
            candidate_state, native_state, rtol=1e-4, atol=2e-5
        ),
        "native_output": summarize(native_output),
        "candidate_output": summarize(candidate_output),
        "native_selected_state": summarize(native_state[0]),
        "candidate_selected_state": summarize(candidate_state[0]),
        "output_per_head_half_errors": per_head_half_errors(
            candidate_output, native_output
        ),
        "state_per_head_half_errors": per_head_half_errors(
            candidate_state, native_state
        ),
    }


def queue_iteration3_packed() -> torch.Tensor:
    """Recreate the exact packed input that failed queue iteration 3.

    The queue stress generator first creates its base state, then draws one
    packed/a/b group per iteration.  Preserve that draw order so this
    diagnostic answers the observed failure rather than a nearby random case.
    """
    generator = torch.Generator().manual_seed(20260921)
    torch.randn(
        (19, H_V, HEAD_DIM, HEAD_DIM),
        generator=generator,
        dtype=torch.float32,
    )
    packed = torch.empty((1, PACKED_WIDTH), dtype=torch.bfloat16)
    for step in range(3):
        packed = (
            torch.randn((16, PACKED_WIDTH), generator=generator)
            * (0.07 + 0.005 * step)
        ).to(torch.bfloat16)
        torch.randn((16, H_V), generator=generator)
        torch.randn((16, H_V), generator=generator)
    return packed.clone()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    library = args.library.resolve()
    output_dir = args.output_dir.resolve()
    if Path("/gdn-megaop-results") not in output_dir.parents or output_dir.exists():
        parser.error("a fresh directory below /gdn-megaop-results is required")
    if os.environ.get("ASCEND_RT_VISIBLE_DEVICES") != "0":
        parser.error("requires audited container logical NPU0 mapped to physical NPU4")
    output_dir.mkdir(parents=True)

    report: dict[str, object] = {
        "schema": "qwen36-gdn-decode-core-stage-diagnostic/v1",
        "status": "running",
        "created_unix_ns": time.time_ns(),
        "candidate_library_sha256": sha256(library),
        "device_contract": "container logical NPU0; externally audited physical NPU4",
        "limits": "Diagnostic controlled eager cases only; not a correctness pass.",
        "cases": [],
    }

    def save() -> None:
        (output_dir / "report.json").write_text(
            json.dumps(json_safe(report), indent=2, allow_nan=False) + "\n"
        )

    save()
    try:
        from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton
        from vllm_ascend.utils import enable_custom_op

        torch_npu.npu.set_compile_mode(jit_compile=False)
        if not enable_custom_op():
            raise RuntimeError("vLLM-Ascend custom operators are unavailable")
        torch.npu.set_device(0)
        init_device_properties_triton()
        torch.ops.load_library(str(library))

        packed = torch.zeros((1, PACKED_WIDTH), dtype=torch.bfloat16)
        for head in range(H_QK):
            packed[0, head * HEAD_DIM] = 1
            packed[0, H_QK * HEAD_DIM + head * HEAD_DIM] = 1
        for head in range(H_V):
            packed[0, 2 * H_QK * HEAD_DIM + head * HEAD_DIM] = 0.25
        zero_state = torch.zeros(
            (4, H_V, HEAD_DIM, HEAD_DIM), dtype=torch.float32
        )
        report["cases"].append(
            run_case("basis_qk_constant_v_zero_state", packed, zero_state)
        )
        save()

        packed_dense = torch.zeros((1, PACKED_WIDTH), dtype=torch.bfloat16)
        dense_row = torch.linspace(-1.0, 1.0, HEAD_DIM).to(torch.bfloat16)
        for head in range(H_QK):
            packed_dense[
                0, head * HEAD_DIM : (head + 1) * HEAD_DIM
            ] = dense_row
            key_start = H_QK * HEAD_DIM + head * HEAD_DIM
            packed_dense[0, key_start : key_start + HEAD_DIM] = dense_row.flip(0)
        for head in range(H_V):
            value_start = 2 * H_QK * HEAD_DIM + head * HEAD_DIM
            packed_dense[0, value_start : value_start + HEAD_DIM] = 0.25
        report["cases"].append(
            run_case("dense_qk_constant_v_zero_state", packed_dense, zero_state)
        )
        save()

        packed_state = torch.zeros((1, PACKED_WIDTH), dtype=torch.bfloat16)
        for head in range(H_QK):
            packed_state[0, head * HEAD_DIM] = 1
        patterned_state = torch.zeros(
            (4, H_V, HEAD_DIM, HEAD_DIM), dtype=torch.float32
        )
        patterned_state[0, :, :, 0] = torch.linspace(
            -0.02, 0.02, HEAD_DIM
        ).reshape(1, HEAD_DIM)
        report["cases"].append(
            run_case("basis_q_zero_kv_patterned_state", packed_state, patterned_state)
        )
        save()

        packed_orthogonal = torch.zeros(
            (1, PACKED_WIDTH), dtype=torch.bfloat16
        )
        for head in range(H_QK):
            packed_orthogonal[0, head * HEAD_DIM] = 1
            packed_orthogonal[
                0, H_QK * HEAD_DIM + head * HEAD_DIM + 1
            ] = 1
        report["cases"].append(
            run_case(
                "orthogonal_qk_zero_v_patterned_state",
                packed_orthogonal,
                patterned_state,
            )
        )
        save()

        # Algebraic stage isolation on the exact first token from the queue
        # ordering iteration that failed.  With zero state, beta=0.5 and a
        # basis V vector, final_state[:, 0, :] is exactly 0.5 * normalized K;
        # no recurrent reduction contributes to that row.
        packed_failed = queue_iteration3_packed()
        for token in range(packed_failed.shape[0]):
            packed_k = packed_failed[token : token + 1].clone()
            packed_k[:, 2 * H_QK * HEAD_DIM :] = 0
            for head in range(H_V):
                value_start = 2 * H_QK * HEAD_DIM + head * HEAD_DIM
                packed_k[0, value_start] = 1
            key_case = run_case(
                f"queue_iteration3_key_isolation_token{token}",
                packed_k,
                zero_state,
            )
            report["cases"].append(key_case)
            save()
            if key_case["state_error"]["max_abs"] != 0.0:
                break
        save()

        # With identity state, g=1 and beta=0, the output rows expose
        # normalized Q through an identity matvec.  The -100 BF16 controls
        # make softplus and sigmoid round to zero on the deployed path.
        identity_state = torch.zeros(
            (4, H_V, HEAD_DIM, HEAD_DIM), dtype=torch.float32
        )
        identity_state[0] = torch.eye(HEAD_DIM).reshape(
            1, HEAD_DIM, HEAD_DIM
        ).expand(H_V, -1, -1)
        zero_gate = torch.full(
            (1, H_V), -100.0, dtype=torch.bfloat16
        )
        for token in range(packed_failed.shape[0]):
            packed_q = torch.zeros(
                (1, PACKED_WIDTH), dtype=torch.bfloat16
            )
            packed_q[:, : H_QK * HEAD_DIM] = packed_failed[
                token : token + 1, : H_QK * HEAD_DIM
            ]
            query_case = run_case(
                f"queue_iteration3_query_isolation_token{token}",
                packed_q,
                identity_state,
                a=zero_gate,
                b=zero_gate,
            )
            report["cases"].append(query_case)
            save()
            if query_case["output_error"]["max_abs"] != 0.0:
                break
        report["status"] = "diagnostic_complete"
    except BaseException as error:
        report.update(status="failed", error=repr(error), error_type=type(error).__name__)
        raise
    finally:
        report["completed_unix_ns"] = time.time_ns()
        save()

    print(json.dumps({"status": report["status"], "report": str(output_dir / "report.json")}))


if __name__ == "__main__":
    main()

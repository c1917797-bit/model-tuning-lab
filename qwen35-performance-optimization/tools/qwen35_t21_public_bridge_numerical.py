#!/usr/bin/env python3
"""Exact-shape BF16 numerical/stress gate for the public ACL bridge."""

from __future__ import annotations

import json
import math
import os

import torch
import torch_npu

import qwen35_t21_bridge


HIDDEN = 5120
LOCAL_INTERMEDIATE = 4352
LOCAL_GATE_UP = 2 * LOCAL_INTERMEDIATE
MAX_ABS_LIMIT = 0.125
RELATIVE_L2_LIMIT = 0.02


def metrics(actual: torch.Tensor, expected: torch.Tensor) -> tuple[float, float, bool]:
    actual_cpu = actual.float().cpu()
    expected_cpu = expected.float().cpu()
    difference = actual_cpu - expected_cpu
    max_abs = float(difference.abs().max())
    denominator = float(torch.linalg.vector_norm(expected_cpu))
    relative_l2 = float(torch.linalg.vector_norm(difference)) / max(denominator, 1e-12)
    bit_exact = bool(torch.equal(actual.cpu(), expected.cpu()))
    return max_abs, relative_l2, bit_exact


def reference(
    x: torch.Tensor,
    gate_up_weight: torch.Tensor,
    down_weight: torch.Tensor,
) -> torch.Tensor:
    gate_up = torch.matmul(x, gate_up_weight)
    activated = torch_npu.npu_swiglu(gate_up, dim=-1)
    return torch.matmul(activated, down_weight)


def one_case(
    rows: int,
    seed: int,
    gate_up_model_layout: torch.Tensor,
    down_model_layout: torch.Tensor,
) -> dict[str, object]:
    torch.manual_seed(seed * 1000 + rows)
    x = (torch.randn((rows, HIDDEN), device="npu", dtype=torch.bfloat16) * 0.02)
    gate_up_view = gate_up_model_layout.t()
    down_view = down_model_layout.t()
    assert tuple(gate_up_view.shape) == (HIDDEN, LOCAL_GATE_UP)
    assert tuple(gate_up_view.stride()) == (1, HIDDEN)
    assert tuple(down_view.shape) == (LOCAL_INTERMEDIATE, HIDDEN)
    assert tuple(down_view.stride()) == (1, LOCAL_INTERMEDIATE)
    assert qwen35_t21_bridge.supports_layout(gate_up_view)
    assert qwen35_t21_bridge.supports_layout(down_view)

    candidate_view = torch.ops.qwen35_t21.swiglu_gated_mlp(
        x, gate_up_view, down_view
    )
    candidate_contiguous = torch.ops.qwen35_t21.swiglu_gated_mlp(
        x, gate_up_view.contiguous(), down_view.contiguous()
    )
    expected = reference(x, gate_up_view, down_view)
    torch.npu.synchronize()

    view_max_abs, view_relative_l2, view_bit_exact = metrics(
        candidate_view, expected
    )
    layout_max_abs, layout_relative_l2, layout_bit_exact = metrics(
        candidate_view, candidate_contiguous
    )
    passed = (
        view_max_abs <= MAX_ABS_LIMIT
        and view_relative_l2 <= RELATIVE_L2_LIMIT
        and layout_max_abs == 0.0
        and layout_relative_l2 == 0.0
        and layout_bit_exact
    )
    return {
        "schema": "qwen35-t21-public-bridge-numerical/v1",
        "m": rows,
        "seed": seed,
        "view_vs_reference_max_abs": view_max_abs,
        "view_vs_reference_relative_l2": view_relative_l2,
        "view_vs_reference_bit_exact": view_bit_exact,
        "view_vs_contiguous_max_abs": layout_max_abs,
        "view_vs_contiguous_relative_l2": layout_relative_l2,
        "view_vs_contiguous_bit_exact": layout_bit_exact,
        "passed": passed,
    }


def main() -> None:
    rows_values = [int(item) for item in os.environ.get("M_VALUES", "1 5 8 16").split()]
    seeds = [int(item) for item in os.environ.get("SEEDS", "1 2 3").split()]
    stress_iterations = int(os.environ.get("STRESS_ITERATIONS", "100"))
    if not rows_values or any(item <= 0 for item in rows_values):
        raise SystemExit("M_VALUES must contain positive integers")
    if not seeds or any(item <= 0 for item in seeds):
        raise SystemExit("SEEDS must contain positive integers")
    if stress_iterations < 1:
        raise SystemExit("STRESS_ITERATIONS must be positive")

    all_passed = True
    for seed in seeds:
        torch.manual_seed(seed)
        gate_up_model_layout = (
            torch.randn(
                (LOCAL_GATE_UP, HIDDEN), device="npu", dtype=torch.bfloat16
            )
            * 0.02
        )
        down_model_layout = (
            torch.randn(
                (HIDDEN, LOCAL_INTERMEDIATE),
                device="npu",
                dtype=torch.bfloat16,
            )
            * 0.02
        )
        for rows in rows_values:
            result = one_case(
                rows, seed, gate_up_model_layout, down_model_layout
            )
            print(json.dumps(result, sort_keys=True), flush=True)
            all_passed = all_passed and bool(result["passed"])

    torch.manual_seed(8675309)
    x = torch.randn((1, HIDDEN), device="npu", dtype=torch.bfloat16) * 0.02
    gate_up_model_layout = torch.randn(
        (LOCAL_GATE_UP, HIDDEN), device="npu", dtype=torch.bfloat16
    ) * 0.02
    down_model_layout = torch.randn(
        (HIDDEN, LOCAL_INTERMEDIATE), device="npu", dtype=torch.bfloat16
    ) * 0.02
    gate_up_view = gate_up_model_layout.t()
    down_view = down_model_layout.t()
    checksum = 0.0
    for _ in range(stress_iterations):
        output = torch.ops.qwen35_t21.swiglu_gated_mlp(
            x, gate_up_view, down_view
        )
        checksum += float(output[0, 0].float().cpu())
    torch.npu.synchronize()
    stress_passed = math.isfinite(checksum)
    print(
        json.dumps(
            {
                "schema": "qwen35-t21-public-bridge-stress/v1",
                "iterations": stress_iterations,
                "finite_checksum": stress_passed,
                "passed": stress_passed,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    if not all_passed or not stress_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

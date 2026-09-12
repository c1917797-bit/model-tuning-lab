#!/usr/bin/env python3
"""Static fail-closed contract for the opt-in T21 runtime composition."""

from pathlib import Path


SOURCE = (
    Path(__file__).resolve().parents[1]
    / "runtime-monkeypatch"
    / "sitecustomize.py"
).read_text(encoding="utf-8")


def test_t21_hook_is_opt_in_and_exact_model_gated_without_dynamic_m_branch() -> None:
    assert 'QWEN35_ASCEND_T21_DENSE_MLP", "0"' in SOURCE
    for marker in (
        "tuple(gate_up_weight.shape) == (8704, 5120)",
        "tuple(down_weight.shape) == (5120, 4352)",
        '== "UnquantizedLinearMethod"',
        "gate_up_proj.tp_size == 4",
        "down_proj.tp_size == 4",
    ):
        assert marker in SOURCE
    assert "1 <= x.size(0) <= 16" not in SOURCE


def test_t21_hook_composes_upstream_and_existing_collective() -> None:
    assert "torch.ops.qwen35_t21.swiglu_gated_mlp" in SOURCE
    assert "tensor_model_parallel_all_reduce(output_parallel)" in SOURCE
    assert "gate_up_weight.t(), down_weight.t()" in SOURCE
    assert "return original(self, x)" in SOURCE


def test_t21_ineligible_path_has_state_free_failfast_diagnostics() -> None:
    assert "_diagnostics_enabled()" in SOURCE
    assert "T21_DIAG_FAIL=x_rows" not in SOURCE
    assert "T21_DIAG_FAIL=gate_shape" in SOURCE
    assert "_qwen35_t21_calls" not in SOURCE


if __name__ == "__main__":
    test_t21_hook_is_opt_in_and_exact_model_gated_without_dynamic_m_branch()
    test_t21_hook_composes_upstream_and_existing_collective()
    test_t21_ineligible_path_has_state_free_failfast_diagnostics()
    print("PASS: T21 runtime hook source contract")

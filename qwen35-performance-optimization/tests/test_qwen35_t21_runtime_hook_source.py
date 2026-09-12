#!/usr/bin/env python3
"""Static fail-closed contract for the opt-in T21 runtime composition."""

from pathlib import Path


SOURCE = (
    Path(__file__).resolve().parents[1]
    / "runtime-monkeypatch"
    / "sitecustomize.py"
).read_text(encoding="utf-8")


def test_t21_hook_has_only_static_module_admission_before_torch_op() -> None:
    assert 'QWEN35_ASCEND_T21_DENSE_MLP", "0"' in SOURCE
    for marker in (
        '== "UnquantizedLinearMethod"',
        "gate_up_proj.tp_size == 4",
        "down_proj.tp_size == 4",
    ):
        assert marker in SOURCE
    hook = SOURCE[SOURCE.index("def _patch_qwen2_moe"):SOURCE.index("def _patch_ascend_gdn")]
    for forbidden in (
        "x.dim()",
        "x.size(",
        "x.dtype",
        "x.is_contiguous()",
        "gate_up_weight.dtype",
        "gate_up_weight.device",
        "gate_up_weight.shape",
        "gate_up_weight.is_contiguous()",
        "gate_up_weight.storage_offset()",
        "down_weight.dtype",
        "down_weight.device",
        "down_weight.shape",
        "down_weight.is_contiguous()",
        "down_weight.storage_offset()",
    ):
        assert forbidden not in hook


def test_t21_hook_composes_upstream_and_existing_collective() -> None:
    assert "torch.ops.qwen35_t21.swiglu_gated_mlp" in SOURCE
    assert "tensor_model_parallel_all_reduce(output_parallel)" in SOURCE
    assert "gate_up_weight.t(), down_weight.t()" in SOURCE
    assert "return original(self, x)" in SOURCE


def test_t21_ineligible_path_has_state_free_failfast_diagnostics() -> None:
    assert "_diagnostics_enabled()" in SOURCE
    assert "T21_DIAG_FAIL=x_rows" not in SOURCE
    assert "T21_DIAG_FAIL=gate_tp" in SOURCE
    assert "_qwen35_t21_calls" not in SOURCE


if __name__ == "__main__":
    test_t21_hook_has_only_static_module_admission_before_torch_op()
    test_t21_hook_composes_upstream_and_existing_collective()
    test_t21_ineligible_path_has_state_free_failfast_diagnostics()
    print("PASS: T21 runtime hook source contract")

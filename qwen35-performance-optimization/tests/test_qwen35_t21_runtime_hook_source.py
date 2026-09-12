#!/usr/bin/env python3
"""Static fail-closed contract for the opt-in T21 runtime composition."""

from pathlib import Path


SOURCE = (
    Path(__file__).resolve().parents[1]
    / "runtime-monkeypatch"
    / "sitecustomize.py"
).read_text(encoding="utf-8")


def test_t21_hook_is_opt_in_and_exact_shape_gated() -> None:
    assert 'QWEN35_ASCEND_T21_DENSE_MLP", "0"' in SOURCE
    for marker in (
        "1 <= x.size(0) <= 16",
        "tuple(gate_up_weight.shape) == (8704, 5120)",
        "tuple(down_weight.shape) == (5120, 4352)",
        '== "UnquantizedLinearMethod"',
        "gate_up_proj.tp_size == 4",
        "down_proj.tp_size == 4",
    ):
        assert marker in SOURCE


def test_t21_hook_composes_upstream_and_existing_collective() -> None:
    assert "torch.ops.qwen35_t21.swiglu_gated_mlp" in SOURCE
    assert "tensor_model_parallel_all_reduce(output_parallel)" in SOURCE
    assert "gate_up_weight.t(), down_weight.t()" in SOURCE
    assert "return original(self, x)" in SOURCE


if __name__ == "__main__":
    test_t21_hook_is_opt_in_and_exact_shape_gated()
    test_t21_hook_composes_upstream_and_existing_collective()
    print("PASS: T21 runtime hook source contract")

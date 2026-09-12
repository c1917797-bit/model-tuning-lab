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
        "from vllm.model_executor.layers.linear import UnquantizedLinearMethod",
        "isinstance(",
        "gate_up_proj.quant_method, UnquantizedLinearMethod",
        "down_proj.quant_method, UnquantizedLinearMethod",
        "gate_up_proj.tp_size == 4",
        "down_proj.tp_size == 4",
    ):
        assert marker in SOURCE
    assert '== "UnquantizedLinearMethod"' not in SOURCE
    hook = SOURCE[
        SOURCE.index("def _patch_qwen2_moe"):
        SOURCE.index("def _patch_vllm_backends")
    ]
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


def test_t21_hook_overrides_only_fake_shape_propagation_symbolically() -> None:
    assert "def _register_t21_fake_kernel(torch_module)" in SOURCE
    assert '"qwen35_t21::swiglu_gated_mlp", allow_override=True' in SOURCE
    assert "return x.new_empty((x.shape[0], down_weight.shape[1]))" in SOURCE
    assert "_register_t21_fake_kernel(module.torch)" in SOURCE
    helper = SOURCE[
        SOURCE.index("def _register_t21_fake_kernel"):
        SOURCE.index("def _patch_qwen_gdn_linear_attn")
    ]
    assert "PrivateUse1" in helper
    assert "torch_module.library.register_fake" in helper
    assert "torch_module.library.Library" not in helper


def test_t21_ineligible_path_has_state_free_failfast_diagnostics() -> None:
    assert "_diagnostics_enabled()" in SOURCE
    assert "T21_DIAG_FAIL=x_rows" not in SOURCE
    assert "T21_DIAG_FAIL=gate_tp" in SOURCE
    assert "_qwen35_t21_calls" not in SOURCE


def test_t21_backports_upstream_size_dim_graph_split_guard() -> None:
    assert '"vllm.compilation.backends"' in SOURCE
    assert "def _patch_vllm_backends(module: ModuleType)" in SOURCE
    assert 'if len(node.args) > 1 or "dim" in node.kwargs:' in SOURCE
    assert '"vllm.compilation.backends._decompose_size_nodes"' in SOURCE
    assert "if not _t21_dense_mlp_enabled():" in SOURCE


def test_size_dim_backport_matches_official_vllm_source_once() -> None:
    official_path = Path("/vllm-workspace/vllm/vllm/compilation/backends.py")
    if not official_path.exists():
        return
    official_source = official_path.read_text(encoding="utf-8")
    old = """    for node in size_nodes:
        tensor_node = node.args[0]
"""
    assert official_source.count(old) == 1
    patched_source = official_source.replace(
        old,
        """    for node in size_nodes:
        if len(node.args) > 1 or "dim" in node.kwargs:
            continue
        tensor_node = node.args[0]
""",
    )
    assert patched_source.count(
        'if len(node.args) > 1 or "dim" in node.kwargs:'
    ) == 1


if __name__ == "__main__":
    test_t21_hook_has_only_static_module_admission_before_torch_op()
    test_t21_hook_composes_upstream_and_existing_collective()
    test_t21_hook_overrides_only_fake_shape_propagation_symbolically()
    test_t21_ineligible_path_has_state_free_failfast_diagnostics()
    test_t21_backports_upstream_size_dim_graph_split_guard()
    print("PASS: T21 runtime hook source contract")

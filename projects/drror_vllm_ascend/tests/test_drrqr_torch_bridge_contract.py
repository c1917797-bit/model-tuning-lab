"""Software-only checks for the isolated DRRQR PyTorch bridge."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRIDGE = (
    ROOT / "native" / "drrqr_recurrent_layout_control_v1"
    / "torch_bridge.cpp"
)
BUILDER = ROOT / "tools" / "build_drrqr_torch_bridge.py"


def test_bridge_is_explicit_and_does_not_replace_upstream_namespace():
    source = BRIDGE.read_text()
    assert "TORCH_LIBRARY(drrqr_ascend, m)" in source
    assert "TORCH_LIBRARY_IMPL(drrqr_ascend, PrivateUse1, m)" in source
    assert "TORCH_LIBRARY(_C_ascend" not in source
    assert "configure_exact_opapi" in source


def test_bridge_requires_exact_library_and_verifies_symbol_origin():
    source = BRIDGE.read_text()
    assert "path.front() == '/'" in source
    assert "RTLD_NOW | RTLD_LOCAL" in source
    assert "dladdr(address, &info)" in source
    assert "canonical_path(info.dli_fname) == expected_path" in source
    assert "aclnnDrrqrRecurrentLayoutControlV1GetWorkspaceSize" in source


def test_bridge_preserves_mutable_state_schema_and_runtime_limit():
    source = BRIDGE.read_text()
    builder = BUILDER.read_text()
    assert "Tensor(a!) state" in source
    assert "at::Tensor& state" in source
    assert "Build/load/schema evidence only; not NPU numerical" in builder
    assert "output directory must not exist" in builder


def test_bridge_manifest_does_not_claim_a_recursive_self_hash():
    builder = BUILDER.read_text()
    assert "path.is_file() and path != manifest_path" in builder

#!/usr/bin/env python3
"""Fail closed if the T21 bridge regresses to private or replacement code."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT
    / "runtime-monkeypatch"
    / "native"
    / "qwen35_t21_public_acl_bridge.cpp"
).read_text(encoding="utf-8")


def test_uses_only_public_tensor_and_stream_seams() -> None:
    assert "aclCreateTensor" in SOURCE
    assert "getCurrentNPUStream" in SOURCE
    assert "OpCommand::RunOpApiV2" in SOURCE
    assert "std::make_shared<PublicAclTensor>" in SOURCE
    assert "dlopen" in SOURCE and "dlsym" in SOURCE
    assert "aclnnSwigluGatedMlp" in SOURCE
    assert "TORCH_LIBRARY(qwen35_t21" in SOURCE
    assert "TORCH_LIBRARY_IMPL(qwen35_t21, PrivateUse1" in SOURCE
    assert "TORCH_LIBRARY_IMPL(qwen35_t21, Meta" in SOURCE
    assert "NPUBridge" not in SOURCE
    assert "NPUStorageImpl" not in SOURCE
    assert "op_api_common.h" not in SOURCE


def test_is_exact_model_shape_gated_without_artificial_m_ceiling() -> None:
    for marker in ("5120", "8704", "4352", "positive flattened row count"):
        assert marker in SOURCE
    assert "M in [1,16]" not in SOURCE


def test_meta_kernel_preserves_symbolic_flattened_rows() -> None:
    assert "x.new_empty_symint(" in SOURCE
    assert "{x.sym_size(0), down_weight.sym_size(1)}" in SOURCE
    meta = SOURCE[SOURCE.index("at::Tensor SwigluGatedMlpMeta"):]
    meta = meta[:meta.index("}  // namespace")]
    assert "at::empty({x.size(0)" not in meta


if __name__ == "__main__":
    test_uses_only_public_tensor_and_stream_seams()
    test_is_exact_model_shape_gated_without_artificial_m_ceiling()
    test_meta_kernel_preserves_symbolic_flattened_rows()
    print("PASS: T21 public ACL bridge source contract")

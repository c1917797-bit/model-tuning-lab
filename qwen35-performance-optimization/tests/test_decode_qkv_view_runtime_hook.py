from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import torch


def _load_patch():
    path = (
        Path(__file__).resolve().parents[1]
        / "runtime-monkeypatch"
        / "sitecustomize.py"
    )
    spec = importlib.util.spec_from_file_location("qwen35_decode_qkv_patch", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_m1_qkv_rearrange_uses_zero_copy_views(monkeypatch):
    monkeypatch.setenv("VLLM_ASCEND_FUSE_QWEN35_GDN_PROJECTIONS", "1")
    monkeypatch.setenv("QWEN35_ASCEND_DECODE_QKV_VIEW", "1")
    patch = _load_patch()
    fallback_calls = []

    class FakeAttention:
        def __init__(self):
            pass

        def rearrange_mixed_qkv(self, mixed_qkv):
            fallback_calls.append(mixed_qkv)
            return "fallback"

    fake_module = SimpleNamespace(
        QwenGatedDeltaNetAttention=FakeAttention,
        torch=torch,
        MergedColumnParallelLinear=object,
    )
    patch._patch_qwen_gdn_linear_attn(fake_module)

    layer = object.__new__(FakeAttention)
    layer.key_dim = 4
    layer.value_dim = 4
    layer.tp_size = 1
    layer.head_k_dim = 2
    layer.head_v_dim = 2
    packed = torch.arange(12, dtype=torch.bfloat16).reshape(1, 12)

    query, key, value = layer.rearrange_mixed_qkv(packed)

    assert fallback_calls == []
    assert query.shape == (1, 1, 2, 2)
    assert key.shape == (1, 1, 2, 2)
    assert value.shape == (1, 1, 2, 2)
    assert query.is_contiguous() and key.is_contiguous() and value.is_contiguous()
    assert query.untyped_storage().data_ptr() == packed.untyped_storage().data_ptr()
    assert key.untyped_storage().data_ptr() == packed.untyped_storage().data_ptr()
    assert value.untyped_storage().data_ptr() == packed.untyped_storage().data_ptr()
    torch.testing.assert_close(query.reshape(1, -1), packed[:, :4])
    torch.testing.assert_close(key.reshape(1, -1), packed[:, 4:8])
    torch.testing.assert_close(value.reshape(1, -1), packed[:, 8:])


def test_non_m1_qkv_rearrange_falls_back(monkeypatch):
    monkeypatch.setenv("VLLM_ASCEND_FUSE_QWEN35_GDN_PROJECTIONS", "1")
    monkeypatch.setenv("QWEN35_ASCEND_DECODE_QKV_VIEW", "1")
    patch = _load_patch()
    fallback_calls = []

    class FakeAttention:
        def __init__(self):
            pass

        def rearrange_mixed_qkv(self, mixed_qkv):
            fallback_calls.append(mixed_qkv)
            return "fallback"

    fake_module = SimpleNamespace(
        QwenGatedDeltaNetAttention=FakeAttention,
        torch=torch,
        MergedColumnParallelLinear=object,
    )
    patch._patch_qwen_gdn_linear_attn(fake_module)

    layer = object.__new__(FakeAttention)
    packed = torch.zeros((2, 12), dtype=torch.bfloat16)
    assert layer.rearrange_mixed_qkv(packed) == "fallback"
    assert fallback_calls == [packed]

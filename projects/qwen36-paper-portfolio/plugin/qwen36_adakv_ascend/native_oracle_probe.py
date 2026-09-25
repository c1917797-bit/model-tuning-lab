"""Read-only native FIA vs math oracle baseline on all full-attention layers.

This diagnostic leaves the serving output and dense cache unchanged. It
captures Q/K/V for one 4096-token request to measure the deployed backend's
own numerical envelope; it is not an Ada-KV performance implementation.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from .live_probe import EXPECTED_SOURCE_SHA256, _error, _event, _math_attention


def register() -> None:
    if os.environ.get("QWEN36_ADAKV_NATIVE_ORACLE_ENABLE") != "1":
        return
    import torch
    import torch_npu
    import vllm_ascend.ops  # noqa: F401 - required v0.23 plugin import order
    import vllm_ascend.attention.attention_v1 as attention

    source = Path(attention.__file__).resolve()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"attention source mismatch: {digest}")
    cls = attention.AscendAttentionBackendImpl
    if hasattr(cls, "_adakv_native_oracle_original_fia"):
        raise RuntimeError("Ada-KV native oracle already installed")
    original_forward = cls.forward
    original_fia = cls.forward_fused_infer_attention
    target_layers = frozenset(f"language_model.model.layers.{i}.self_attn.attn"
                              for i in range(3, 64, 4))

    def forward(self, *args, **kwargs):
        layer = args[0] if args else kwargs.get("layer")
        self._adakv_native_oracle_layer_name = getattr(layer, "layer_name", None)
        return original_forward(self, *args, **kwargs)

    def fia(self, query, key, value, attn_metadata, output, kv_cache=None):
        result = original_fia(self, query, key, value, attn_metadata, output, kv_cache)
        layer_name = getattr(self, "_adakv_native_oracle_layer_name", None)
        if layer_name not in target_layers or attention._EXTRA_CTX.capturing:
            return result
        state = attn_metadata.attn_state
        if (state == attention.AscendAttentionState.PrefillNoCache
                and query.ndim == 3 and query.shape[1:] == (6, 256)
                and key.shape == (query.shape[0], 1, 256)
                and value.shape == key.shape
                and query.shape[0] == 4096
                and len(attn_metadata.actual_seq_lengths_q) == 1):
            self._adakv_native_oracle_key = key.clone()
            self._adakv_native_oracle_value = value.clone()
            self._adakv_native_oracle_step = 0
            _event("native_oracle_prefill", layer_name=layer_name,
                   length=int(query.shape[0]), output_unchanged=True)
            return result
        if (state != attention.AscendAttentionState.DecodeOnly
                or query.shape != (1, 6, 256)
                or key.shape != (1, 1, 256) or value.shape != key.shape
                or len(attn_metadata.seq_lens_list) != 1
                or not hasattr(self, "_adakv_native_oracle_key")
                or self._adakv_native_oracle_step >= 3):
            return result
        self._adakv_native_oracle_key = torch.cat((self._adakv_native_oracle_key, key), dim=0)
        self._adakv_native_oracle_value = torch.cat((self._adakv_native_oracle_value, value), dim=0)
        full_k = self._adakv_native_oracle_key
        full_v = self._adakv_native_oracle_value
        length = int(full_k.shape[0])
        contiguous, _ = torch_npu.npu_fused_infer_attention_score(
            query=query, key=full_k, value=full_v, input_layout="TND",
            actual_seq_lengths=[1], actual_seq_lengths_kv=[length],
            num_key_value_heads=1, num_heads=6, scale=self.scale, sparse_mode=0)
        expected = _math_attention(query, full_k, full_v, self.scale)
        dense = result[0].reshape(6, 256)
        contiguous = contiguous[0].reshape(6, 256)
        self._adakv_native_oracle_step += 1
        _event("native_oracle_decode", layer_name=layer_name,
               decode_step=self._adakv_native_oracle_step, length=length,
               output_rms=float(expected.float().square().mean().sqrt().item()),
               paged_vs_contiguous=_error(dense, contiguous),
               paged_vs_math=_error(dense, expected),
               contiguous_vs_math=_error(contiguous, expected),
               paged_vs_rounded_math=_error(dense, expected.to(dense.dtype)),
               contiguous_vs_rounded_math=_error(contiguous, expected.to(contiguous.dtype)),
               output_unchanged=True)
        return result

    cls._adakv_native_oracle_original_forward = original_forward
    cls._adakv_native_oracle_original_fia = original_fia
    cls.forward = forward
    cls.forward_fused_infer_attention = fia
    _event("native_oracle_installed", source=str(source), source_sha256=digest,
           target_layers=sorted(target_layers), torch_npu=torch_npu.__version__)

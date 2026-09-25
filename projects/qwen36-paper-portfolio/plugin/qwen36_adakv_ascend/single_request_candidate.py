"""Fail-closed, single-request Ada-KV serving seam for NPU correctness only.

This intentionally does not advertise a production cache or memory gain.
vLLM still allocates its normal KV buffer, but the selected full-attention
layer does not write to it. The plugin owns a separate compact K/V arena and
calls the deployed native FIA on that arena. Only eager PrefillNoCache and
DecodeOnly with one active request are supported.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from .budget import allocate_global_head_budget
from .live_probe import EXPECTED_SOURCE_SHA256, TARGET_LAYER, WINDOW, _error, _event, _math_attention, _score


def register() -> None:
    if os.environ.get("QWEN36_ADAKV_CANDIDATE_ENABLE") != "1":
        return
    import torch
    import torch.distributed as dist
    import torch_npu
    import vllm_ascend.ops  # noqa: F401 - required v0.23 plugin import order
    import vllm_ascend.attention.attention_v1 as attention

    source = Path(attention.__file__).resolve()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"attention source mismatch: {digest}")
    capacity = int(os.environ.get("QWEN36_ADAKV_BASE_CAPACITY", "2048"))
    max_decode = int(os.environ.get("QWEN36_ADAKV_MAX_DECODE", "8"))
    all_full = os.environ.get("QWEN36_ADAKV_ALL_FULL_LAYERS") == "1"
    target_layers = (
        frozenset(f"language_model.model.layers.{i}.self_attn.attn"
                  for i in range(3, 64, 4))
        if all_full else frozenset((TARGET_LAYER,))
    )
    if capacity <= 0 or max_decode <= 0:
        raise RuntimeError("capacity and max_decode must be positive")

    cls = attention.AscendAttentionBackendImpl
    if hasattr(cls, "_adakv_candidate_original_forward"):
        raise RuntimeError("Ada-KV candidate already installed")
    original_forward = cls.forward
    original_reshape = cls.reshape_and_cache
    original_forward_impl = cls.forward_impl
    original_fia = cls.forward_fused_infer_attention

    def forward(self, *args, **kwargs):
        layer = args[0] if args else kwargs.get("layer")
        self._adakv_candidate_layer_name = getattr(layer, "layer_name", None)
        return original_forward(self, *args, **kwargs)

    def reshape_and_cache(self, query, key, value, kv_cache, attn_metadata, output):
        layer_name = getattr(self, "_adakv_candidate_layer_name", None)
        if layer_name not in target_layers:
            return original_reshape(self, query, key, value, kv_cache, attn_metadata, output)
        state = attn_metadata.attn_state
        if attention._EXTRA_CTX.capturing:
            raise RuntimeError("Ada-KV single-request candidate requires eager mode")
        if state not in (attention.AscendAttentionState.PrefillNoCache,
                         attention.AscendAttentionState.DecodeOnly):
            raise RuntimeError(f"unsupported Ada-KV attention state: {state}")
        if len(attn_metadata.actual_seq_lengths_q) != 1:
            raise RuntimeError("Ada-KV single-request candidate requires batch 1")
        # The normal native dense write is deliberately skipped. Any later
        # unsupported path must fail, because that cache is now uninitialized.
        _event("candidate_dense_write_skipped", layer_name=layer_name,
               state=str(state), tokens=int(attn_metadata.num_actual_tokens))
        return query, key, value, output

    def forward_impl(self, query, key, value, kv_cache, attn_metadata, output):
        if getattr(self, "_adakv_candidate_layer_name", None) not in target_layers:
            return original_forward_impl(self, query, key, value, kv_cache, attn_metadata, output)
        # Bypass the ordinary paged-attention dispatch as well as its dense
        # cache read. The candidate FIA consumes only the compact arena.
        return self.forward_fused_infer_attention(
            query, key, value, attn_metadata, output, kv_cache)

    def fia(self, query, key, value, attn_metadata, output, kv_cache=None):
        layer_name = getattr(self, "_adakv_candidate_layer_name", None)
        if layer_name not in target_layers:
            return original_fia(self, query, key, value, attn_metadata, output, kv_cache)
        state = attn_metadata.attn_state
        if attention._EXTRA_CTX.capturing:
            raise RuntimeError("Ada-KV single-request candidate requires eager mode")
        if state == attention.AscendAttentionState.PrefillNoCache:
            if not dist.is_initialized() or dist.get_world_size() != 4:
                raise RuntimeError("Ada-KV candidate requires initialized TP4 workers")
            if query.ndim != 3 or query.shape[1:] != (6, 256):
                raise RuntimeError(f"unexpected Ada-KV prefill query shape: {tuple(query.shape)}")
            if key.shape != (query.shape[0], 1, 256) or value.shape != key.shape:
                raise RuntimeError("unexpected Ada-KV prefill K/V geometry")
            if len(attn_metadata.actual_seq_lengths_q) != 1:
                raise RuntimeError("Ada-KV single-request prefill requires batch 1")
            length = int(query.shape[0])
            result = original_fia(self, query, key, value, attn_metadata, output, kv_cache)
            if length <= WINDOW + capacity:
                indices = torch.arange(length, device=key.device)
                counts = budgets = None
            else:
                score = _score(query, key, self.scale)
                if not bool(torch.isfinite(score).all().item()):
                    raise RuntimeError("nonfinite Ada-KV observation scores")
                local, budgets, counts = allocate_global_head_budget(
                    score[None], capacity, 0.5)
                selected = torch.argsort(score, descending=True, stable=True)[:int(local[0].item())]
                recent = torch.arange(length - WINDOW, length, device=key.device)
                indices = torch.cat((selected.sort().values, recent))
            selected_tokens = int(indices.numel())
            arena_tokens = selected_tokens + max_decode
            compact_k = torch.empty((arena_tokens, 1, 256), dtype=key.dtype, device=key.device)
            compact_v = torch.empty_like(compact_k)
            compact_k[:selected_tokens].copy_(key.index_select(0, indices))
            compact_v[:selected_tokens].copy_(value.index_select(0, indices))
            self._adakv_candidate_cache = (compact_k, compact_v)
            self._adakv_candidate_length = selected_tokens
            self._adakv_candidate_decode_count = 0
            _event("candidate_prefill_compact", layer_name=layer_name,
                   full_length=length, selected_tokens=selected_tokens,
                   arena_tokens=arena_tokens,
                   raw_counts=None if counts is None else counts[0].cpu().tolist(),
                   safeguarded_budgets=None if budgets is None else budgets[0].cpu().tolist(),
                   dense_write_skipped=True)
            return result
        if state != attention.AscendAttentionState.DecodeOnly:
            raise RuntimeError(f"unsupported Ada-KV attention state: {state}")
        if query.shape != (1, 6, 256) or key.shape != (1, 1, 256) or value.shape != key.shape:
            raise RuntimeError("Ada-KV single-request candidate requires one decode token")
        if len(attn_metadata.seq_lens_list) != 1:
            raise RuntimeError("Ada-KV single-request candidate requires batch 1")
        if not hasattr(self, "_adakv_candidate_cache"):
            raise RuntimeError("Ada-KV compact cache missing before decode")
        compact_k, compact_v = self._adakv_candidate_cache
        n = self._adakv_candidate_length
        if n >= compact_k.shape[0]:
            raise RuntimeError("Ada-KV compact cache exceeded configured max_decode")
        compact_k[n:n + 1].copy_(key)
        compact_v[n:n + 1].copy_(value)
        n += 1
        selected, _ = torch_npu.npu_fused_infer_attention_score(
            query=query, key=compact_k[:n], value=compact_v[:n],
            input_layout="TND", actual_seq_lengths=[1],
            actual_seq_lengths_kv=[n], num_key_value_heads=1,
            num_heads=6, scale=self.scale, sparse_mode=0)
        expected = _math_attention(query, compact_k[:n], compact_v[:n], self.scale)
        expected_rounded = expected.to(selected.dtype)
        raw_error = _error(selected[0], expected)
        error = _error(selected[0], expected_rounded)
        rounding_error = _error(expected_rounded, expected)
        expected_rms = float(expected.float().square().mean().sqrt().item())
        # Same-stack, uncompressed native-oracle baseline (192 TP rank/layer/
        # step points) reached 0.002819 relative RMS versus this rounded math
        # oracle. Freeze a 0.003 ceiling before the candidate full-layer run.
        allowed_rms = 0.003 * expected_rms
        # Native FIA emits BF16. Compare with the independently computed
        # oracle at the same output dtype; retain the FP32 comparison and the
        # oracle's own BF16 rounding loss as separate diagnostics. This gate
        # tests the native selected-support calculation only, not task quality.
        if (expected_rms <= 0 or error["rms"] > allowed_rms
                or not bool(torch.isfinite(selected).all().item())
                or not bool(torch.isfinite(expected).all().item())):
            _event("candidate_numeric_gate_failed", layer_name=layer_name,
                   decode_step=self._adakv_candidate_decode_count + 1,
                   selected_tokens=n, native_math_error=raw_error,
                   rounded_reference_error=error,
                   oracle_rounding_error=rounding_error,
                   allowed_rms=allowed_rms,
                   selected_rms=float(selected.float().square().mean().sqrt().item()),
                   expected_rms=expected_rms)
            raise RuntimeError(f"Ada-KV native selected-support numerical gate failed: {error}")
        output[:1] = selected[:1].view(1, 6, 256)
        self._adakv_candidate_length = n
        self._adakv_candidate_decode_count += 1
        _event("candidate_decode_compact", layer_name=layer_name,
               decode_step=self._adakv_candidate_decode_count,
               selected_tokens=n, native_math_error=raw_error,
               rounded_reference_error=error,
               oracle_rounding_error=rounding_error,
               allowed_rms=allowed_rms, expected_rms=expected_rms,
               dense_write_skipped=True, output_replaced=True)
        return output

    cls._adakv_candidate_original_forward = original_forward
    cls._adakv_candidate_original_reshape = original_reshape
    cls._adakv_candidate_original_forward_impl = original_forward_impl
    cls._adakv_candidate_original_fia = original_fia
    cls.forward = forward
    cls.reshape_and_cache = reshape_and_cache
    cls.forward_impl = forward_impl
    cls.forward_fused_infer_attention = fia
    _event("candidate_installed", target_layers=sorted(target_layers),
           source=str(source), source_sha256=digest, capacity=capacity,
           max_decode=max_decode, torch_npu=torch_npu.__version__)

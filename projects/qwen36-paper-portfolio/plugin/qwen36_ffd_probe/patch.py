"""Real-Q/K/V FFD selector investment probe; return native dense output.

This is an unpacked source-equation diagnostic, not an Ascend port or exact
FP16-arithmetic emulation of the author's fused CUDA kernel. It never alters
the model response or KV cache.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import threading
import time

EXPECTED_SOURCE_SHA256 = "80005aba42bcf61247cc0d91502a0f1338194a4b38dd82bc521f6d3c84958390"
ENABLE_ENV = "QWEN36_FFD_PROBE_ENABLE"
AUDIT_ENV = "QWEN36_FFD_PROBE_AUDIT"
_LOCK = threading.Lock()
_DONE_LAYERS: set[str] = set()
_TARGET_LAYERS = {
    "language_model.model.layers.3.self_attn.attn",
    "language_model.model.layers.31.self_attn.attn",
    "language_model.model.layers.63.self_attn.attn",
}


def _event(name: str, **fields: object) -> None:
    base = os.environ.get(AUDIT_ENV)
    if not base:
        raise RuntimeError(f"{AUDIT_ENV} is required")
    path = Path(f"{base}.{os.getpid()}.jsonl")
    payload = {"event": name, "pid": os.getpid(), "time_ns": time.time_ns(), **fields}
    with path.open("a", encoding="utf-8") as output:
        output.write(json.dumps(payload, sort_keys=True, allow_nan=False) + "\n")


def _scan_scores(q, approx_k, scale):
    """Return [query_head, block, token] scores, never token/block transposed."""
    import torch

    scores = torch.einsum("hd,btd->hbt", q, approx_k) * scale
    expected = (q.shape[0], approx_k.shape[0], approx_k.shape[1])
    if tuple(scores.shape) != expected:
        raise RuntimeError(f"FFD scan shape {tuple(scores.shape)} != {expected}")
    return scores


def _selection_masks(keep, selection_size: int, tail_len: int):
    """Expand subblock decisions and the author's KV-group OR to token masks."""
    import torch

    if keep.ndim != 2 or keep.dtype != torch.bool:
        raise RuntimeError("FFD keep decisions must be a [head, subblock] bool tensor")
    if selection_size <= 0 or tail_len < 0:
        raise RuntimeError("invalid FFD selection/tail geometry")
    union = keep.any(dim=0)
    per_head_tokens = keep.repeat_interleave(selection_size, dim=-1)
    union_tokens = union.repeat_interleave(selection_size)
    if tail_len:
        per_head_tokens = torch.cat(
            (per_head_tokens, torch.ones((keep.shape[0], tail_len),
                                         dtype=torch.bool, device=keep.device)),
            dim=-1,
        )
        union_tokens = torch.cat(
            (union_tokens, torch.ones((tail_len,),
                                       dtype=torch.bool, device=keep.device)),
            dim=-1,
        )
    return per_head_tokens, union, union_tokens


def _sample(self, query, result, attn_metadata) -> None:
    import torch

    length = int(attn_metadata.seq_lens_list[0])
    block_size = int(self.key_cache.shape[1])
    if block_size != 128:
        raise RuntimeError(f"FFD source block size is 128, live cache is {block_size}")
    full_count, tail_len = divmod(length, block_size)
    if full_count < 2:
        raise RuntimeError("FFD diagnostic requires at least two full blocks")
    num_pages = full_count + int(tail_len != 0)
    pages = attn_metadata.block_tables[0, :num_pages].long()
    if bool((pages < 0).any().item()):
        raise RuntimeError("invalid live block table")
    key_pages = self.key_cache.index_select(0, pages).reshape(
        num_pages, block_size, 256
    )
    value_pages = self.value_cache.index_select(0, pages).reshape(
        num_pages, block_size, 256
    )
    k_full = key_pages[:full_count]
    scale = (k_full.abs().amax(dim=1) / 1.5).clamp(min=1e-8)
    # Author quantize_symmetric_blocks: per-block/per-coordinate mid-rise Q2.
    codes = (k_full / scale[:, None, :] + 1.5).round().clamp(0, 3)
    approx_k = (codes.float() - 1.5) * scale.float()[:, None, :]
    q = query[0].float()
    approx = _scan_scores(q, approx_k, self.scale)
    exact_k = key_pages.float().reshape(-1, 256)[:length]
    exact_v = value_pages.float().reshape(-1, 256)[:length]
    exact_logits = (q @ exact_k.T) * self.scale
    exact_probs = torch.softmax(exact_logits, dim=-1)
    native_output_dtype = result[0].dtype
    native = result[0].float().reshape(6, 256)
    dense_math = exact_probs @ exact_v
    if not bool(torch.isfinite(approx).all().item()):
        raise RuntimeError("non-finite Q2 scan")
    if not bool(torch.isfinite(exact_logits).all().item()):
        raise RuntimeError("non-finite dense oracle")
    dense_oracle_error = dense_math.to(native_output_dtype).float() - native
    dense_oracle_relative_rms = (
        dense_oracle_error.square().mean().sqrt()
        / native.square().mean().sqrt().clamp(min=1e-8)
    ).item()
    if dense_oracle_relative_rms > 0.005:
        raise RuntimeError(
            f"full-support math/native relative RMS {dense_oracle_relative_rms:.6f} "
            "exceeds frozen 0.005 diagnostic ceiling"
        )

    # The released paged kernel uses first/last quantized full blocks for
    # its pseudo-max. It stores scores in log2 units and subtracts raw delta.
    pseudo_nat = torch.maximum(
        approx[:, 0, :].amax(dim=-1), approx[:, -1, :].amax(dim=-1)
    )
    exact_max = exact_logits.amax(dim=-1)
    cases = []
    # The released author wrapper defaults SBS=BS=128, but the kernel admits
    # finer subblocks. Keep Q2 quantization at the original 128-token block.
    # This is an author-supported algorithm-parameter sweep, not FP16 kernel
    # arithmetic parity or an enabled attention replacement.
    for selection_size in (16, 32, 64, 128):
        if block_size % selection_size:
            raise RuntimeError("FFD subblock must divide the quantized block")
        subblock_count = full_count * (block_size // selection_size)
        subblock_scores = approx.reshape(6, subblock_count, selection_size)
        exact_subblocks = exact_logits[:, : full_count * block_size].reshape(
            6, subblock_count, selection_size
        ).amax(dim=-1)
        for delta in (3.0, 4.0, 5.0):
            effective_delta = delta * math.log(2.0)
            threshold = pseudo_nat[:, None] - effective_delta
            keep = subblock_scores.amax(dim=-1) >= threshold
            keep_tokens, union, union_token_mask = _selection_masks(
                keep, selection_size, tail_len
            )
            if keep_tokens.shape != (6, length) or union_token_mask.shape != (length,):
                raise RuntimeError("FFD selection token-mask shape mismatch")
            ideal_keep = exact_subblocks >= (exact_max[:, None] - effective_delta)
            missed = (ideal_keep & ~keep).sum(dim=-1)
            mass = (exact_probs * keep_tokens).sum(dim=-1)
            union_mass = (exact_probs * union_token_mask[None, :]).sum(dim=-1)
            ideal_mask = ideal_keep.repeat_interleave(selection_size, dim=-1)
            if tail_len:
                ideal_mask = torch.cat(
                    (ideal_mask, torch.ones((6, tail_len), dtype=torch.bool, device=q.device)),
                    dim=-1,
                )
            ideal_mass = (exact_probs * ideal_mask).sum(dim=-1)
            ideal_union = ideal_keep.any(dim=0)
            selected_probs = torch.softmax(
                exact_logits.masked_fill(~keep_tokens, float("-inf")), dim=-1
            )
            selected = selected_probs @ exact_v
            union_probs = torch.softmax(
                exact_logits.masked_fill(~union_token_mask[None, :], float("-inf")),
                dim=-1,
            )
            union_selected = union_probs @ exact_v
            if not bool(torch.isfinite(selected).all().item()) or not bool(
                torch.isfinite(union_selected).all().item()
            ):
                raise RuntimeError("non-finite selected-support output")
            per_head_difference = selected.to(native_output_dtype).float() - native
            union_difference = union_selected.to(native_output_dtype).float() - native
            cases.append({
                "delta": delta,
                "units": "author_log2",
                "source_subblock_size": selection_size,
                "effective_natural_delta": effective_delta,
                "per_head_subblock_keep_fraction": keep.float().mean(dim=-1).tolist(),
                "union_subblock_keep_fraction": union.float().mean().item(),
                "union_k_residual_v_token_fraction": union_token_mask.float().mean().item(),
                "per_head_exact_dense_probability_mass": mass.tolist(),
                "union_exact_dense_probability_mass": union_mass.tolist(),
                "per_head_exact_logit_ideal_mass": ideal_mass.tolist(),
                "ideal_exact_logit_union_subblock_keep_fraction": ideal_union.float().mean().item(),
                "per_head_false_negative_subblocks_against_exact_global_delta": missed.tolist(),
                "per_head_selected_math_vs_native_rms": per_head_difference.square().mean().sqrt().item(),
                "union_selected_math_vs_native_max_abs": union_difference.abs().max().item(),
                "union_selected_math_vs_native_rms": union_difference.square().mean().sqrt().item(),
                "union_selected_math_vs_native_relative_rms": (
                    union_difference.square().mean().sqrt()
                    / native.square().mean().sqrt().clamp(min=1e-8)
                ).item(),
                "union_selected_vs_dense_math_rms": (
                    union_selected - dense_math
                ).square().mean().sqrt().item(),
            })
    torch.npu.synchronize()
    _event(
        "real_decode_sample",
        layer_name=self._ffd_probe_layer_name,
        tp_rank=torch.distributed.get_rank() if torch.distributed.is_initialized() else None,
        seq_len=length,
        block_size=block_size,
        full_quantized_blocks=full_count,
        unquantized_tail_tokens=tail_len,
        query_dtype=str(query.dtype),
        cache_dtype=str(self.key_cache.dtype),
        source_mode="author_paged_threshold_unpacked_equation_diagnostic_not_fp16_kernel_parity",
        source_keep_scope="kv_group_any_query_head",
        source_subblock_sizes_tested=[16, 32, 64, 128],
        pseudo_max_below_exact_max=(exact_max - pseudo_nat).tolist(),
        q2_scan_vs_exact_max_abs=(
            approx.reshape(6, -1) - exact_logits[:, : full_count * block_size]
        ).abs().max().item(),
        dense_math_vs_native_max_abs=dense_oracle_error.abs().max().item(),
        dense_math_vs_native_relative_rms=dense_oracle_relative_rms,
        cases=cases,
    )


def register() -> None:
    if os.environ.get(ENABLE_ENV) != "1":
        return
    import torch
    import torch_npu
    import vllm_ascend.ops  # Initialize Ascend custom ops before attention import.
    import vllm_ascend.attention.attention_v1 as attention

    source = Path(attention.__file__).resolve()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"attention source mismatch: {digest}")
    cls = attention.AscendAttentionBackendImpl
    if hasattr(cls, "_ffd_probe_original"):
        raise RuntimeError("FFD probe already installed")
    original = cls.forward_fused_infer_attention
    original_forward = cls.forward
    _event("probe_installed", source=str(source), source_sha256=digest,
           torch=torch.__version__, torch_npu=torch_npu.__version__)

    def observed(self, query, key, value, attn_metadata, output, kv_cache=None):
        result = original(self, query, key, value, attn_metadata, output, kv_cache)
        if (
            attn_metadata.attn_state != attention.AscendAttentionState.DecodeOnly
            or attention._EXTRA_CTX.capturing
            or query.ndim != 3
            or query.shape[1:] != (6, 256)
            or int(attn_metadata.actual_seq_lengths_q[-1]) != 1
            or self.num_kv_heads != 1
            or self.key_cache is None
            or self.value_cache is None
            or getattr(self, "_ffd_probe_layer_name", None) not in _TARGET_LAYERS
            or len(attn_metadata.seq_lens_list) != 1
            or int(attn_metadata.seq_lens_list[0]) < 2048
        ):
            return result
        with _LOCK:
            layer_name = self._ffd_probe_layer_name
            if layer_name in _DONE_LAYERS:
                return result
            _DONE_LAYERS.add(layer_name)
        try:
            _sample(self, query, result, attn_metadata)
        except BaseException as exc:
            _event("real_decode_sample_failed", layer_name=layer_name,
                   error=f"{type(exc).__name__}: {exc}")
            raise
        return result

    def observed_forward(self, *args, **kwargs):
        layer = args[0] if args else kwargs.get("layer")
        self._ffd_probe_layer_name = getattr(layer, "layer_name", None)
        return original_forward(self, *args, **kwargs)

    cls._ffd_probe_original = original
    cls._ffd_probe_original_forward = original_forward
    cls.forward = observed_forward
    cls.forward_fused_infer_attention = observed

"""Output-preserving, real-Q/K/V KIVI-4 investment probe on Ascend.

The author-equation arm is unpacked and deliberately untimed. The second arm
uses static per-channel K and whole-channel per-token V scales, corresponding
to the native FIA antiquant modes rather than to faithful KIVI.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import threading
import time

EXPECTED_SOURCE_SHA256 = "80005aba42bcf61247cc0d91502a0f1338194a4b38dd82bc521f6d3c84958390"
_LOCK = threading.Lock()
_DONE: set[str] = set()
_LAYERS = {
    "language_model.model.layers.3.self_attn.attn",
    "language_model.model.layers.31.self_attn.attn",
    "language_model.model.layers.63.self_attn.attn",
}


def _event(name: str, **fields: object) -> None:
    base = os.environ.get("QWEN36_KIVI_PROBE_AUDIT")
    if not base:
        raise RuntimeError("QWEN36_KIVI_PROBE_AUDIT is required")
    path = Path(f"{base}.{os.getpid()}.jsonl")
    payload = {"event": name, "pid": os.getpid(), "time_ns": time.time_ns(), **fields}
    with path.open("a", encoding="utf-8") as output:
        output.write(json.dumps(payload, sort_keys=True, allow_nan=False) + "\n")


def _quant_dequant(groups, bits: int = 4):
    """Official asymmetric min/max equation along the final group axis."""
    import torch

    if bits != 4 or groups.ndim < 2:
        raise ValueError("probe requires 4-bit groups")
    work = groups.float()
    mn = work.amin(dim=-1, keepdim=True)
    mx = work.amax(dim=-1, keepdim=True)
    width = mx - mn
    zero_width = width == 0
    scale = torch.where(zero_width, torch.ones_like(width), width / 15.0)
    codes = ((work - mn) / scale).clamp(0, 15).round()
    restored = codes * scale + mn
    if restored.shape != groups.shape or not bool(torch.isfinite(restored).all().item()):
        raise RuntimeError("non-finite or wrong-shape dequantized groups")
    return restored, int(zero_width.sum().item())


def _kivi_k(x, group_size: int = 32, residual_length: int = 128):
    """Per-channel, per-token-group K; author key tail is modulo R."""
    import torch

    length, width = x.shape
    quant_length = length - (length % residual_length)
    if quant_length % group_size:
        raise RuntimeError("K quantized length not group-aligned")
    if quant_length == 0:
        return x.float(), 0, 0
    groups = x[:quant_length].T.contiguous().reshape(width, -1, group_size)
    restored, zero_width = _quant_dequant(groups)
    full = torch.cat((restored.reshape(width, quant_length).T,
                      x[quant_length:].float()), dim=0)
    return full, quant_length, zero_width


def _kivi_v(x, group_size: int = 32, residual_length: int = 128):
    """Per-token, per-channel-group V with an R-token full-precision tail."""
    import torch

    length, width = x.shape
    quant_length = max(0, length - residual_length)
    if width % group_size:
        raise RuntimeError("V head width not group-aligned")
    if quant_length == 0:
        return x.float(), 0, 0
    groups = x[:quant_length].contiguous().reshape(quant_length, width // group_size, group_size)
    restored, zero_width = _quant_dequant(groups)
    full = torch.cat((restored.reshape(quant_length, width),
                      x[quant_length:].float()), dim=0)
    return full, quant_length, zero_width


def _native_compatible_k(x, quant_length: int):
    """One static scale/offset per K channel, not KIVI's token groups."""
    import torch

    if quant_length == 0:
        return x.float(), 0
    restored, zero_width = _quant_dequant(x[:quant_length].T.contiguous())
    return torch.cat((restored.T, x[quant_length:].float()), dim=0), zero_width


def _native_compatible_v(x, quant_length: int):
    """One scale/offset over the entire head per token, not KIVI's D-groups."""
    import torch

    if quant_length == 0:
        return x.float(), 0
    restored, zero_width = _quant_dequant(x[:quant_length].contiguous())
    return torch.cat((restored, x[quant_length:].float()), dim=0), zero_width


def _sample(self, query, result, attn_metadata) -> None:
    import torch

    length = int(attn_metadata.seq_lens_list[0])
    block_size = int(self.key_cache.shape[1])
    page_count = (length + block_size - 1) // block_size
    pages = attn_metadata.block_tables[0, :page_count].long()
    if bool((pages < 0).any().item()):
        raise RuntimeError("invalid live block table")
    key = self.key_cache.index_select(0, pages).reshape(-1, 256)[:length]
    value = self.value_cache.index_select(0, pages).reshape(-1, 256)[:length]
    if query.shape != (1, 6, 256) or key.shape != (length, 256) or value.shape != (length, 256):
        raise RuntimeError("unexpected Q/K/V shape")
    q = query[0].float()
    native = result[0].float().reshape(6, 256)
    logits = (q @ key.float().T) * self.scale
    dense_math = torch.softmax(logits, dim=-1) @ value.float()
    base_difference = dense_math.to(result[0].dtype).float() - native
    base_relative_rms = (
        base_difference.square().mean().sqrt()
        / native.square().mean().sqrt().clamp(min=1e-8)
    ).item()
    if not bool(torch.isfinite(dense_math).all().item()) or base_relative_rms > 0.005:
        raise RuntimeError(f"dense math/native oracle failed: {base_relative_rms:.6f}")

    k_author, k_quant_length, k_zero = _kivi_k(key)
    v_author, v_quant_length, v_zero = _kivi_v(value)
    k_native, k_native_zero = _native_compatible_k(key, k_quant_length)
    v_native, v_native_zero = _native_compatible_v(value, v_quant_length)
    cases = []
    for label, k_input, v_input, faithful in (
        ("kivi4_group32_equation", k_author, v_author, True),
        ("fia_mode0_mode1_static_derivative", k_native, v_native, False),
    ):
        output = torch.softmax((q @ k_input.T) * self.scale, dim=-1) @ v_input
        if not bool(torch.isfinite(output).all().item()):
            raise RuntimeError(f"non-finite {label} output")
        difference = output.to(result[0].dtype).float() - native
        cases.append({
            "name": label,
            "paper_equation": faithful,
            "output_vs_native_relative_rms": (
                difference.square().mean().sqrt()
                / native.square().mean().sqrt().clamp(min=1e-8)
            ).item(),
            "output_vs_native_max_abs": difference.abs().max().item(),
            "output_vs_dense_math_rms": (output - dense_math).square().mean().sqrt().item(),
            "k_vs_original_relative_rms": ((k_input - key.float()).square().mean().sqrt()
                                          / key.float().square().mean().sqrt().clamp(min=1e-8)).item(),
            "v_vs_original_relative_rms": ((v_input - value.float()).square().mean().sqrt()
                                          / value.float().square().mean().sqrt().clamp(min=1e-8)).item(),
        })
    torch.npu.synchronize()
    _event(
        "real_decode_sample",
        layer_name=self._kivi_probe_layer_name,
        tp_rank=torch.distributed.get_rank() if torch.distributed.is_initialized() else None,
        seq_len=length,
        block_size=block_size,
        head_geometry=[6, 1, 256],
        key_quantized_tokens=k_quant_length,
        value_quantized_tokens=v_quant_length,
        group_size=32,
        residual_length=128,
        zero_width_groups={"kivi_k": k_zero, "kivi_v": v_zero,
                           "native_k": k_native_zero, "native_v": v_native_zero},
        dense_math_vs_native_relative_rms=base_relative_rms,
        cases=cases,
        scope="unpacked_equation_investment_probe_not_native_int4_or_service_performance",
    )


def register() -> None:
    if os.environ.get("QWEN36_KIVI_PROBE_ENABLE") != "1":
        return
    import torch
    import torch_npu
    import vllm_ascend.ops  # Bootstrap custom operators before attention import.
    import vllm_ascend.attention.attention_v1 as attention

    source = Path(attention.__file__).resolve()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"attention source mismatch: {digest}")
    cls = attention.AscendAttentionBackendImpl
    if hasattr(cls, "_kivi_probe_original"):
        raise RuntimeError("KIVI probe already installed")
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
            or getattr(self, "_kivi_probe_layer_name", None) not in _LAYERS
            or len(attn_metadata.seq_lens_list) != 1
            or int(attn_metadata.seq_lens_list[0]) < 2048
        ):
            return result
        with _LOCK:
            layer_name = self._kivi_probe_layer_name
            if layer_name in _DONE:
                return result
            _DONE.add(layer_name)
        try:
            _sample(self, query, result, attn_metadata)
        except BaseException as exc:
            _event("real_decode_sample_failed", layer_name=layer_name,
                   error=f"{type(exc).__name__}: {exc}")
            raise
        return result

    def observed_forward(self, *args, **kwargs):
        layer = args[0] if args else kwargs.get("layer")
        self._kivi_probe_layer_name = getattr(layer, "layer_name", None)
        return original_forward(self, *args, **kwargs)

    cls._kivi_probe_original = original
    cls._kivi_probe_original_forward = original_forward
    cls.forward = observed_forward
    cls.forward_fused_infer_attention = observed

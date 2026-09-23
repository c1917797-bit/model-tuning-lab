"""Equation-derived Self-Indexing Attention selector on live Ascend decode Q/K/V.

This is not an author-code port or a production sparse-attention operator.
The original vLLM-Ascend dense output is returned unchanged. Timings are
diagnostic wall times, not a performance benchmark.
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
ENABLE_ENV = "QWEN36_SIA_PROBE_ENABLE"
AUDIT_ENV = "QWEN36_SIA_PROBE_AUDIT"
_LOCK = threading.Lock()
_DONE_LAYERS: set[str] = set()
_TARGET_LAYERS = {3, 31, 63}


def _event(name: str, **fields: object) -> None:
    path = os.environ.get(AUDIT_ENV)
    if not path:
        raise RuntimeError(f"{AUDIT_ENV} is required")
    payload = {"event": name, "pid": os.getpid(),
               "time_ns": time.time_ns(), **fields}
    with open(path, "a", encoding="utf-8") as output:
        output.write(json.dumps(payload, sort_keys=True, allow_nan=False) + "\n")


def _fwht(x):
    """Sylvester Walsh-Hadamard transform on the trailing power-of-two axis."""
    import torch

    width = x.shape[-1]
    if width < 2 or width & (width - 1):
        raise ValueError(f"Hadamard width must be a power of two: {width}")
    out = x
    stride = 1
    while stride < width:
        blocks = out.reshape(*out.shape[:-1], width // (2 * stride), 2, stride)
        left, right = blocks.unbind(dim=-2)
        out = torch.stack((left + right, left - right), dim=-2)
        out = out.reshape(*x.shape)
        stride *= 2
    return out / math.sqrt(width)


def _rotation_sign(layer_index: int, global_kv_head: int, device):
    import torch

    # The paper fixes seed 42 but does not release an exact sign-stream layout.
    # This deterministic per-layer/KV-head stream implements its D*H equation;
    # do not label its individual top-k set as author-code identical.
    generator = torch.Generator(device="cpu")
    generator.manual_seed(42 + layer_index * 4099 + global_kv_head * 131071)
    signs = torch.randint(0, 2, (256,), generator=generator, dtype=torch.int8)
    return (signs.to(device=device, dtype=torch.float32) * 2 - 1)


def _select_indices(scores, length: int, budget: int):
    import torch

    if budget < 128 or budget > length:
        raise ValueError(f"invalid sparse budget {budget} for {length}")
    positions = torch.arange(length, device=scores.device)
    forced = (positions < 64) | (positions >= length - 64)
    candidates = scores.masked_fill(forced, float("-inf"))
    middle = torch.topk(candidates, budget - 128, sorted=False).indices
    return torch.cat((positions[forced], middle)).sort().values


def register() -> None:
    if os.environ.get(ENABLE_ENV) != "1":
        return
    import torch
    import torch_npu
    import vllm_ascend.ops
    import vllm_ascend.attention.attention_v1 as attention

    path = Path(attention.__file__).resolve()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"attention source mismatch: {digest}")
    cls = attention.AscendAttentionBackendImpl
    if hasattr(cls, "_sia_probe_original"):
        raise RuntimeError("Self-Indexing Attention probe is already installed")
    original = cls.forward_fused_infer_attention
    original_forward = cls.forward
    _event("probe_installed", source=str(path), source_sha256=digest,
           torch=torch.__version__, torch_npu=torch_npu.__version__)

    def observed(self, query, key, value, attn_metadata, output, kv_cache=None):
        result = original(self, query, key, value, attn_metadata, output, kv_cache)
        layer_name = getattr(self, "_sia_probe_layer_name", None)
        layer_index = int(layer_name.split(".layers.")[1].split(".")[0]) \
            if layer_name and ".layers." in layer_name else -1
        if (
            attn_metadata.attn_state != attention.AscendAttentionState.DecodeOnly
            or attention._EXTRA_CTX.capturing
            or query.ndim != 3
            or query.shape[1:] != (6, 256)
            or self.num_kv_heads != 1
            or self.key_cache is None
            or layer_index not in _TARGET_LAYERS
            or attn_metadata.actual_seq_lengths_q[-1] != 1
        ):
            return result
        lengths = attn_metadata.seq_lens_list
        if len(lengths) != 1 or int(lengths[0]) < 2048:
            return result
        with _LOCK:
            if layer_name in _DONE_LAYERS:
                return result
            _DONE_LAYERS.add(layer_name)
        try:
            length = int(lengths[0])
            block_size = int(self.key_cache.shape[1])
            num_pages = math.ceil(length / block_size)
            pages = attn_metadata.block_tables[0, :num_pages].long()
            if bool((pages < 0).any().item()):
                raise RuntimeError("invalid live page table")
            q = query[0].float()
            k = self.key_cache.index_select(0, pages).float().reshape(-1, 256)[:length]
            v = self.value_cache.index_select(0, pages).float().reshape(-1, 256)[:length]
            dense = result[0].float().reshape(6, 256)
            if not all(bool(torch.isfinite(t).all().item()) for t in (q, k, v, dense)):
                raise RuntimeError("non-finite live attention tensor")
            rank = torch.distributed.get_rank() if torch.distributed.is_initialized() else 0
            sign = _rotation_sign(layer_index, rank, q.device)

            start = time.perf_counter_ns()
            q_rot = _fwht(q * sign)
            k_rot = _fwht(k * sign)
            torch.npu.synchronize()
            rotation_wall_ms = (time.perf_counter_ns() - start) / 1e6
            dot_error = ((q @ k[:256].T) - (q_rot @ k_rot[:256].T)).abs().max().item()
            if dot_error > 0.01:
                raise RuntimeError(f"live Hadamard dot-product identity failed: {dot_error}")

            full_probs = torch.softmax((q @ k.T) * self.scale, dim=-1)
            full_math = full_probs @ v
            full_math_error = (full_math - dense).abs().max().item()
            if full_math_error > 0.1:
                raise RuntimeError(f"full-support math/native mismatch: {full_math_error}")

            start = time.perf_counter_ns()
            absmax_head = q_rot.abs().argmax(dim=0, keepdim=True)
            pooled = q_rot.gather(0, absmax_head).squeeze(0)
            query_sign = pooled >= 0
            key_sign = k_rot >= 0
            matches = (key_sign == query_sign[None, :]).sum(dim=-1).float()
            scores = (matches - 128).clamp_min(0) * k_rot.norm(dim=-1)
            torch.npu.synchronize()
            score_wall_ms = (time.perf_counter_ns() - start) / 1e6
            cases = []
            for fraction in (0.05, 0.10, 0.25):
                budget = min(length, max(math.ceil(fraction * length), 768))
                start = time.perf_counter_ns()
                selected = _select_indices(scores, length, budget)
                torch.npu.synchronize()
                selection_wall_ms = (time.perf_counter_ns() - start) / 1e6
                mass = full_probs.index_select(1, selected).sum(dim=-1)
                selected_k = k.index_select(0, selected)
                selected_v = v.index_select(0, selected)
                sparse_probs = torch.softmax((q @ selected_k.T) * self.scale, dim=-1)
                sparse_math = sparse_probs @ selected_v
                difference = sparse_math - dense
                cases.append({
                    "fraction": fraction, "budget": budget,
                    "selected_mass_per_head": mass.tolist(),
                    "mass_min": mass.min().item(), "mass_mean": mass.mean().item(),
                    "math_output_max_abs": difference.abs().max().item(),
                    "math_output_rms": difference.square().mean().sqrt().item(),
                    "selection_wall_ms": selection_wall_ms,
                })
            _event("real_decode_sample", layer_name=layer_name,
                   tp_rank=rank, seq_len=length, block_size=block_size,
                   num_pages=num_pages, global_kv_head=rank,
                   rotation_seed_base=42,
                   dot_product_max_abs=dot_error,
                   full_math_vs_dense_max_abs=full_math_error,
                   rotation_wall_ms=rotation_wall_ms,
                   sign_score_wall_ms=score_wall_ms,
                   cases=cases)
        except BaseException as exc:
            _event("real_decode_sample_failed", layer_name=layer_name,
                   error=f"{type(exc).__name__}: {exc}")
            raise
        return result

    def observed_forward(self, *args, **kwargs):
        layer = args[0] if args else kwargs.get("layer")
        self._sia_probe_layer_name = getattr(layer, "layer_name", None)
        return original_forward(self, *args, **kwargs)

    cls._sia_probe_original = original
    cls._sia_probe_original_forward = original_forward
    cls.forward = observed_forward
    cls.forward_fused_infer_attention = observed

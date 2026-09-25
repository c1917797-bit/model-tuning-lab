"""One-shot real-model Ada-KV selection diagnostic, no serving cache mutation."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import threading
import time

EXPECTED_SOURCE_SHA256 = "80005aba42bcf61247cc0d91502a0f1338194a4b38dd82bc521f6d3c84958390"
TARGET_LAYER = "language_model.model.layers.3.self_attn.attn"
WINDOW = 32
POOL = 7
BASE_CAPACITY = 256
FLOOR_RATIO = 0.5
_LOCK = threading.Lock()
_DONE = False
_SEEN = False
_DECODE_STEPS = 4
_CAPACITIES = (256, 512, 1024, 2048)


def _event(name: str, **fields: object) -> None:
    import torch.distributed as dist

    root = os.environ.get("QWEN36_ADAKV_PROBE_AUDIT_DIR")
    if not root:
        raise RuntimeError("QWEN36_ADAKV_PROBE_AUDIT_DIR is required")
    rank = dist.get_rank() if dist.is_initialized() else -1
    payload = {"event": name, "rank": rank, "pid": os.getpid(),
               "time_ns": time.time_ns(), **fields}
    with open(Path(root) / f"audit-rank{rank}.jsonl", "a", encoding="utf-8") as out:
        out.write(json.dumps(payload, sort_keys=True, allow_nan=False) + "\n")


def _score(query, key, scale: float):
    import torch
    import torch.nn.functional as functional

    # Single full-prompt prefill only: TND query [L,6,D], key [L,1,D].
    length = query.shape[0]
    q = query[-WINDOW:].permute(1, 0, 2)
    k = key[:, 0]
    logits = torch.matmul(q, k.T) * scale
    recent = logits[..., -WINDOW:]
    causal = torch.triu(torch.ones((WINDOW, WINDOW), device=query.device,
                                   dtype=torch.bool), diagonal=1)
    recent.masked_fill_(causal, torch.finfo(logits.dtype).min)
    # Match official calcul_attn_sore: BF16 QK, FP32 softmax, then cast
    # probabilities back to the query dtype *before* window/GQA pooling.
    weights = torch.softmax(logits, dim=-1, dtype=torch.float32).to(query.dtype)
    old = weights[..., :length - WINDOW].mean(dim=1).mean(dim=0)
    return functional.max_pool1d(old[None, None], kernel_size=POOL,
                                 stride=1, padding=POOL // 2).reshape(-1)


def _math_attention(query, key, value, scale: float):
    import torch

    logits = query[0].float() @ key[:, 0].float().T * scale
    return torch.softmax(logits, dim=-1) @ value[:, 0].float()


def _error(actual, reference):
    import torch.nn.functional as functional

    diff = actual.float() - reference.float()
    return {"max_abs": float(diff.abs().max().item()),
            "rms": float(diff.square().mean().sqrt().item()),
            "cosine": float(functional.cosine_similarity(
                actual.float().reshape(-1), reference.float().reshape(-1), dim=0).item())}


def register() -> None:
    if os.environ.get("QWEN36_ADAKV_PROBE_ENABLE") != "1":
        return
    import torch
    import torch.distributed as dist
    import torch_npu
    import vllm_ascend.ops  # noqa: F401 - required early plugin import order
    import vllm_ascend.attention.attention_v1 as attention

    source = Path(attention.__file__).resolve()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"attention source mismatch: {digest}")
    cls = attention.AscendAttentionBackendImpl
    if hasattr(cls, "_adakv_live_original"):
        raise RuntimeError("Ada-KV live probe already installed")
    original = cls.forward_fused_infer_attention
    original_forward = cls.forward
    _event("probe_installed", source=str(source), source_sha256=digest,
           torch=torch.__version__, torch_npu=torch_npu.__version__)

    def observed(self, query, key, value, attn_metadata, output, kv_cache=None):
        global _DONE, _SEEN
        result = original(self, query, key, value, attn_metadata, output, kv_cache)
        if getattr(self, "_adakv_probe_layer_name", None) == TARGET_LAYER:
            with _LOCK:
                first = not _SEEN
                _SEEN = True
            if first:
                _event("real_forward_geometry", layer_name=TARGET_LAYER,
                       state=str(attn_metadata.attn_state),
                       query_shape=list(query.shape), key_shape=list(key.shape),
                       query_lengths=list(attn_metadata.actual_seq_lengths_q),
                       capturing=bool(attention._EXTRA_CTX.capturing))
        if (getattr(self, "_adakv_probe_layer_name", None) == TARGET_LAYER
                and getattr(self, "_adakv_probe_compact", None) is not None
                and attn_metadata.attn_state == attention.AscendAttentionState.DecodeOnly
                and not attention._EXTRA_CTX.capturing
                and query.shape == (1, 6, 256)
                and key.shape == (1, 1, 256)
                and value.shape == (1, 1, 256)
                and len(attn_metadata.seq_lens_list) == 1
                and self._adakv_probe_step < _DECODE_STEPS):
            try:
                self._adakv_probe_step += 1
                dense = result[0].float().reshape(6, 256)
                self._adakv_probe_full_key = torch.cat((self._adakv_probe_full_key, key), dim=0)
                self._adakv_probe_full_value = torch.cat((self._adakv_probe_full_value, value), dim=0)
                exact_full = _math_attention(query, self._adakv_probe_full_key,
                                             self._adakv_probe_full_value, self.scale)
                cases = []
                for capacity in _CAPACITIES:
                    old_k, old_v = self._adakv_probe_compact[capacity]
                    compact_k = torch.cat((old_k, key), dim=0).contiguous()
                    compact_v = torch.cat((old_v, value), dim=0).contiguous()
                    selected, _ = torch_npu.npu_fused_infer_attention_score(
                        query=query, key=compact_k, value=compact_v,
                        input_layout="TND", actual_seq_lengths=[1],
                        actual_seq_lengths_kv=[compact_k.shape[0]],
                        num_key_value_heads=1, num_heads=6,
                        scale=self.scale, sparse_mode=0)
                    selected_math = _math_attention(query, compact_k, compact_v, self.scale)
                    cases.append({"base_capacity": capacity,
                                  "selected_tokens": int(compact_k.shape[0]),
                                  "native_vs_dense": _error(selected[0], dense),
                                  "selected_math_vs_native": _error(selected_math, selected[0])})
                    self._adakv_probe_compact[capacity] = (compact_k, compact_v)
                _event("real_decode_selected_support", step=self._adakv_probe_step,
                       full_length=int(self._adakv_probe_full_key.shape[0]),
                       full_math_vs_native=_error(exact_full, dense),
                       cases=cases, output_unchanged=True)
            except BaseException as exc:
                _event("real_decode_selected_support_failed",
                       step=getattr(self, "_adakv_probe_step", -1),
                       error=f"{type(exc).__name__}: {exc}")
                raise
            return result
        if (getattr(self, "_adakv_probe_layer_name", None) != TARGET_LAYER
                or attention._EXTRA_CTX.capturing
                or attn_metadata.attn_state != attention.AscendAttentionState.PrefillNoCache
                or query.ndim != 3 or key.ndim != 3
                or query.shape[1] != 6 or key.shape[1] != 1
                or query.shape[-1] != key.shape[-1]
                or query.shape[0] != key.shape[0]
                or query.shape[0] < 2048
                or len(attn_metadata.actual_seq_lengths_q) != 1):
            return result
        with _LOCK:
            if _DONE:
                return result
            _DONE = True
        try:
            if not dist.is_initialized() or dist.get_world_size() != 4:
                raise RuntimeError("expected one TP4 process group")
            length = int(query.shape[0])
            score = _score(query, key, self.scale)
            if not bool(torch.isfinite(score).all().item()):
                raise RuntimeError("nonfinite live Ada-KV scores")
            from .budget import allocate_global_head_budget
            cases = []
            compact = {}
            old_end = length - WINDOW
            recent = torch.arange(old_end, length, device=key.device)
            for capacity in _CAPACITIES:
                local, budgets, counts = allocate_global_head_budget(
                    score[None], capacity, FLOOR_RATIO)
                selected = torch.argsort(score, descending=True, stable=True)[:int(local[0].item())]
                indices = torch.cat((selected.sort().values, recent))
                compact[capacity] = (key.index_select(0, indices).contiguous(),
                                     value.index_select(0, indices).contiguous())
                cases.append({"base_capacity": capacity,
                              "selected_total": int(counts.sum().item()),
                              "raw_counts": counts[0].cpu().tolist(),
                              "safeguarded_budgets": budgets[0].cpu().tolist(),
                              "local_budget": int(local[0].item()),
                              "local_selected_tokens": int(indices.numel())})
            self._adakv_probe_compact = compact
            self._adakv_probe_full_key = key.clone()
            self._adakv_probe_full_value = value.clone()
            self._adakv_probe_step = 0
            _event("real_prefill_budget", layer_name=TARGET_LAYER,
                   length=length, dtype=str(query.dtype), scale=float(self.scale),
                   scores=length - WINDOW, world=dist.get_world_size(), cases=cases,
                   output_unchanged=True)
        except BaseException as exc:
            _event("real_prefill_budget_failed", error=f"{type(exc).__name__}: {exc}")
            raise
        return result

    def observed_forward(self, *args, **kwargs):
        layer = args[0] if args else kwargs.get("layer")
        self._adakv_probe_layer_name = getattr(layer, "layer_name", None)
        return original_forward(self, *args, **kwargs)

    cls._adakv_live_original = original
    cls._adakv_live_original_forward = original_forward
    cls.forward = observed_forward
    cls.forward_fused_infer_attention = observed

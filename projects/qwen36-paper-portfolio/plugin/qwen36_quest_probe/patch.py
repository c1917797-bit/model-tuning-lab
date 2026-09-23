"""Observe one real decode call; keep native dense output unchanged.

Quest's released cache metadata is page-min/max. For this *diagnostic* the
summaries are recomputed once from live K, then the online selector is timed
separately. A serving candidate must maintain summaries incrementally and
revalidate graph, slot and prefix-cache lifecycles.
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
ENABLE_ENV = "QWEN36_QUEST_PROBE_ENABLE"
AUDIT_ENV = "QWEN36_QUEST_PROBE_AUDIT"
_LOCK = threading.Lock()
_DONE = False


def _event(name: str, **fields: object) -> None:
    path = os.environ.get(AUDIT_ENV)
    if not path:
        raise RuntimeError(f"{AUDIT_ENV} is required")
    payload = {"event": name, "pid": os.getpid(),
               "time_ns": time.time_ns(), **fields}
    with open(path, "a", encoding="utf-8") as output:
        output.write(json.dumps(payload, sort_keys=True, allow_nan=False) + "\n")


def _page_score(query, page_min, page_max):
    """Quest's coordinate-wise min/max upper-bound; [G,P,D] -> [G,P]."""
    import torch

    low = query[:, None, :] * page_min[None, :, :]
    high = query[:, None, :] * page_max[None, :, :]
    return torch.maximum(low, high).sum(dim=-1)


def register() -> None:
    if os.environ.get(ENABLE_ENV) != "1":
        return
    import torch
    import torch_npu
    # Initialize Ascend ops before its attention module during early plugin
    # discovery; see the recorded SparQ v1 import-cycle failure.
    import vllm_ascend.ops
    import vllm_ascend.attention.attention_v1 as attention

    path = Path(attention.__file__).resolve()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"attention source mismatch: {digest}")
    cls = attention.AscendAttentionBackendImpl
    if hasattr(cls, "_quest_probe_original"):
        raise RuntimeError("Quest probe is already installed")
    original = cls.forward_fused_infer_attention
    original_forward = cls.forward
    _event("probe_installed", source=str(path), source_sha256=digest,
           torch=torch.__version__, torch_npu=torch_npu.__version__)

    def observed(self, query, key, value, attn_metadata, output, kv_cache=None):
        global _DONE
        result = original(self, query, key, value, attn_metadata, output, kv_cache)
        actual_tokens = attn_metadata.actual_seq_lengths_q[-1]
        if (
            attn_metadata.attn_state != attention.AscendAttentionState.DecodeOnly
            or attention._EXTRA_CTX.capturing
            or query.ndim != 3
            or actual_tokens != 1
            or query.shape[1:] != (6, 256)
            or self.num_kv_heads != 1
            or self.key_cache is None
            or getattr(self, "_quest_probe_layer_name", None)
            != "language_model.model.layers.3.self_attn.attn"
        ):
            return result
        lengths = attn_metadata.seq_lens_list
        if len(lengths) != 1 or int(lengths[0]) < 2048:
            return result
        with _LOCK:
            if _DONE:
                return result
            _DONE = True
        try:
            length = int(lengths[0])
            block_size = int(self.key_cache.shape[1])
            num_pages = math.ceil(length / block_size)
            pages = attn_metadata.block_tables[0, :num_pages].long()
            if bool((pages < 0).any().item()):
                raise RuntimeError("invalid live page table")
            start = time.perf_counter_ns()
            key_pages = self.key_cache.index_select(0, pages).float().reshape(
                num_pages, block_size, 256
            )
            page_min = key_pages.amin(dim=1)
            page_max = key_pages.amax(dim=1)
            last_length = length - (num_pages - 1) * block_size
            if last_length != block_size:
                page_min[-1] = key_pages[-1, :last_length].amin(dim=0)
                page_max[-1] = key_pages[-1, :last_length].amax(dim=0)
            torch.npu.synchronize()
            summary_build_ms = (time.perf_counter_ns() - start) / 1e6

            q = query[0].float()
            start = time.perf_counter_ns()
            head_scores = _page_score(q, page_min, page_max)
            shared_scores = head_scores.max(dim=0).values
            torch.npu.synchronize()
            score_ms = (time.perf_counter_ns() - start) / 1e6
            dense = result[0].float().reshape(6, 256)
            cache_key = self.key_cache.view(self.key_cache.shape[0], block_size, -1)
            cache_value = self.value_cache.view(self.value_cache.shape[0], block_size, -1)
            cases = []
            for fraction in (0.25, 0.5):
                budget = max(2, math.ceil(num_pages * fraction))
                start = time.perf_counter_ns()
                chosen_other = torch.topk(
                    shared_scores[:-1], budget - 1, sorted=False
                ).indices
                latest = shared_scores[-1:].to(torch.long) * 0 + (num_pages - 1)
                chosen = torch.cat((chosen_other, latest)).sort().values
                selected_pages = pages.index_select(0, chosen).int()
                torch.npu.synchronize()
                selection_ms = (time.perf_counter_ns() - start) / 1e6

                selected_length = (budget - 1) * block_size + last_length
                start = time.perf_counter_ns()
                sparse, _ = torch_npu.npu_fused_infer_attention_score(
                    query=query[:1], key=cache_key, value=cache_value,
                    block_table=selected_pages.view(1, -1),
                    input_layout="TND", block_size=block_size,
                    actual_seq_lengths=[1],
                    actual_seq_lengths_kv=[selected_length],
                    num_key_value_heads=1, num_heads=6, scale=self.scale,
                    sparse_mode=0,
                )
                torch.npu.synchronize()
                sparse_ms = (time.perf_counter_ns() - start) / 1e6
                approximation = sparse[0].float().reshape(6, 256)
                difference = approximation - dense
                each_other = torch.topk(
                    head_scores[:, :-1], budget - 1, dim=-1,
                    sorted=False
                ).indices
                page_recall = (
                    each_other[:, :, None] == chosen[None, None, :]
                ).any(dim=-1).float().mean(dim=-1)
                # Exact selected probability mass is diagnostic only. It
                # reads full K *after* the online selector has been timed.
                full_keys = key_pages.reshape(-1, 256)[:length]
                full_probs = torch.softmax(
                    (q @ full_keys.T) * self.scale, dim=-1
                )
                logical_positions = torch.arange(length, device=q.device)
                selected_mask = (
                    logical_positions[:, None] // block_size
                    == chosen[None, :]
                ).any(dim=-1)
                selected_mass = full_probs[:, selected_mask].sum(dim=-1)
                cases.append({
                    "fraction": fraction, "page_budget": budget,
                    "selected_tokens": selected_length,
                    "selection_wall_ms": selection_ms,
                    "sparse_fia_wall_ms": sparse_ms,
                    "per_head_quest_page_recall": page_recall.tolist(),
                    "per_head_exact_attention_mass": selected_mass.tolist(),
                    "output_max_abs": difference.abs().max().item(),
                    "output_rms": difference.square().mean().sqrt().item(),
                    "output_cosine": torch.nn.functional.cosine_similarity(
                        approximation.flatten(), dense.flatten(), dim=0
                    ).item(),
                })
            _event("real_decode_sample", tp_rank=torch.distributed.get_rank()
                   if torch.distributed.is_initialized() else None,
                   seq_len=length, block_size=block_size,
                   num_pages=num_pages, summary_build_ms=summary_build_ms,
                   score_wall_ms=score_ms, cases=cases)
        except BaseException as exc:
            _event("real_decode_sample_failed", error=f"{type(exc).__name__}: {exc}")
            raise
        return result

    def observed_forward(self, *args, **kwargs):
        layer = args[0] if args else kwargs.get("layer")
        self._quest_probe_layer_name = getattr(layer, "layer_name", None)
        return original_forward(self, *args, **kwargs)

    cls._quest_probe_original = original
    cls._quest_probe_original_forward = original_forward
    cls.forward = observed_forward
    cls.forward_fused_infer_attention = observed

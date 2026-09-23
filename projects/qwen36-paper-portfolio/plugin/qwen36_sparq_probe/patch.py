"""One-shot eager decode observation; never changes the model's dense output."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import threading
import time

EXPECTED_SOURCE_SHA256 = "80005aba42bcf61247cc0d91502a0f1338194a4b38dd82bc521f6d3c84958390"
ENABLE_ENV = "QWEN36_SPARQ_PROBE_ENABLE"
AUDIT_ENV = "QWEN36_SPARQ_PROBE_AUDIT"
_LOCK = threading.Lock()
_DONE = False
_SEEN_CALLS: set[tuple[int, str]] = set()


def _event(name: str, **fields: object) -> None:
    path = os.environ.get(AUDIT_ENV)
    if not path:
        raise RuntimeError(f"{AUDIT_ENV} is required")
    payload = {"event": name, "pid": os.getpid(), "rank": os.environ.get("RANK"),
               "time_ns": time.time_ns(), **fields}
    line = json.dumps(payload, sort_keys=True, allow_nan=False) + "\n"
    with open(path, "a", encoding="utf-8") as output:
        output.write(line)


def register() -> None:
    if os.environ.get(ENABLE_ENV) != "1":
        return
    import torch
    import torch_npu
    # v0.23's device_op imports ops.triton while ops.__init__ imports
    # fused_moe.experts_selector back through DeviceOperator. During early
    # general-plugin discovery, initialize ops first to avoid that cycle.
    import vllm_ascend.ops
    import vllm_ascend.attention.attention_v1 as attention

    path = Path(attention.__file__).resolve()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"attention source mismatch: {digest}")
    cls = attention.AscendAttentionBackendImpl
    if hasattr(cls, "_sparq_probe_original"):
        raise RuntimeError("SparQ probe is already installed")
    original = cls.forward_fused_infer_attention
    original_forward = cls.forward
    _event("probe_installed", source=str(path), source_sha256=digest,
           torch=torch.__version__, torch_npu=torch_npu.__version__)

    def observed(self, query, key, value, attn_metadata, output, kv_cache=None):
        global _DONE
        result = original(self, query, key, value, attn_metadata, output, kv_cache)
        state_name = getattr(attn_metadata.attn_state, "name", str(attn_metadata.attn_state))
        identity = (self.layerIndex, state_name)
        if self.layerIndex in (0, 3, 4) and identity not in _SEEN_CALLS:
            _SEEN_CALLS.add(identity)
            _event(
                "attention_call_shape",
                runtime_layer_index_field=self.layerIndex,
                model_layer_name=getattr(self, "_sparq_probe_layer_name", None),
                state=state_name,
                query_shape=list(query.shape),
                num_actual_tokens=int(attn_metadata.actual_seq_lengths_q[-1]),
                seq_lens=[int(length) for length in attn_metadata.seq_lens_list],
                local_kv_heads=int(self.num_kv_heads),
                block_size=None if self.key_cache is None else int(self.key_cache.shape[1]),
            )
        actual_tokens = attn_metadata.actual_seq_lengths_q[-1]
        if (
            attn_metadata.attn_state != attention.AscendAttentionState.DecodeOnly
            or attention._EXTRA_CTX.capturing
            or query.ndim != 3
            or actual_tokens != 1
            or query.shape[1:] != (6, 256)
            or self.num_kv_heads != 1
            or self.key_cache is None
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
            from sparq_page_selection import select_sparq_pages

            length = int(lengths[0])
            block_size = int(self.key_cache.shape[1])
            num_pages = math.ceil(length / block_size)
            pages = attn_metadata.block_tables[0, :num_pages].long()
            if bool((pages < 0).any().item()):
                raise RuntimeError("invalid live page table")
            keys = self.key_cache.index_select(0, pages).reshape(-1, 256)[:length]
            values = self.value_cache.index_select(0, pages).reshape(-1, 256)[:length]
            mean_value = values.float().mean(dim=0)
            cache_key = self.key_cache.view(self.key_cache.shape[0], block_size, -1)
            cache_value = self.value_cache.view(self.value_cache.shape[0], block_size, -1)
            dense = result[0].float().reshape(6, 256)
            cases = []
            for fraction in (0.25, 0.5):
                page_budget = max(2, math.ceil(num_pages * fraction))
                start = time.perf_counter_ns()
                selected = select_sparq_pages(
                    query[0], keys, pages,
                    block_size=block_size, rank=32, token_budget=128,
                    page_budget=page_budget, recent_tokens=1,
                )
                torch.npu.synchronize()
                selection_ms = (time.perf_counter_ns() - start) / 1e6
                start = time.perf_counter_ns()
                sparse, _ = torch_npu.npu_fused_infer_attention_score(
                    query=query[:1], key=cache_key, value=cache_value,
                    block_table=selected["selected_physical_pages"].view(1, -1).int(),
                    input_layout="TND", block_size=block_size,
                    actual_seq_lengths=[1],
                    actual_seq_lengths_kv=[selected["selected_length"]],
                    num_key_value_heads=1, num_heads=6, scale=self.scale,
                    sparse_mode=0,
                )
                torch.npu.synchronize()
                sparse_ms = (time.perf_counter_ns() - start) / 1e6
                approximation = sparse[0].float().reshape(6, 256)
                difference = approximation - dense
                # Paper Eq. 10 reallocates the omitted approximate probability
                # mass to a running mean V. This one-shot diagnostic computes
                # the exact historical mean from the live cache; it is not a
                # serving implementation of the running-mean lifecycle.
                q_full = query[0].float()
                dimensions = selected["top_r_dimensions"]
                q_short = q_full.index_select(-1, dimensions)
                k_short = keys.index_select(-1, dimensions).float()
                coverage = q_short.abs().sum(-1) / q_full.abs().sum(-1).clamp_min(1e-12)
                temperature = torch.sqrt(256 * coverage.clamp_min(1e-12))
                approximate = torch.softmax(
                    (q_short @ k_short.T) / temperature[:, None], dim=-1
                )
                logical_positions = torch.arange(length, device=query.device)
                selected_mask = (
                    logical_positions[:, None] // block_size
                    == selected["selected_logical_pages"][None, :]
                ).any(dim=-1)
                alpha = approximate[:, selected_mask].sum(dim=-1)
                corrected = alpha[:, None] * approximation + (1 - alpha[:, None]) * mean_value
                corrected_difference = corrected - dense
                cases.append({
                    "fraction": fraction,
                    "page_budget": page_budget,
                    "selected_tokens": selected["selected_length"],
                    "paper_topk_page_recall": (
                        selected["retained_paper_top_k_tokens"].float() / 128
                    ).item(),
                    "selection_wall_ms": selection_ms,
                    "sparse_fia_wall_ms": sparse_ms,
                    "output_max_abs": difference.abs().max().item(),
                    "output_rms": difference.square().mean().sqrt().item(),
                    "output_cosine": torch.nn.functional.cosine_similarity(
                        approximation.flatten(), dense.flatten(), dim=0
                    ).item(),
                    "mean_reallocation_alpha_range": [alpha.min().item(), alpha.max().item()],
                    "mean_reallocated_max_abs": corrected_difference.abs().max().item(),
                    "mean_reallocated_rms": corrected_difference.square().mean().sqrt().item(),
                    "mean_reallocated_cosine": torch.nn.functional.cosine_similarity(
                        corrected.flatten(), dense.flatten(), dim=0
                    ).item(),
                })
            _event("real_decode_sample",
                   model_layer_name=getattr(self, "_sparq_probe_layer_name", None),
                   tp_rank=torch.distributed.get_rank()
                   if torch.distributed.is_initialized() else None,
                   seq_len=length,
                   block_size=block_size, num_pages=num_pages, cases=cases)
        except BaseException as exc:
            _event("real_decode_sample_failed", error=f"{type(exc).__name__}: {exc}")
            raise
        return result

    def observed_forward(self, *args, **kwargs):
        layer = args[0] if args else kwargs.get("layer")
        self._sparq_probe_layer_name = getattr(layer, "layer_name", None)
        return original_forward(self, *args, **kwargs)

    cls._sparq_probe_original = original
    cls._sparq_probe_original_forward = original_forward
    cls.forward = observed_forward
    cls.forward_fused_infer_attention = observed

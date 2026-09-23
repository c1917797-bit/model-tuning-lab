"""Official-mechanism-derived Kascade diagnostic on live Ascend Q/K/V.

This imports no CUDA/TileLang kernel, never changes the native dense output,
and is not a deployable sparse-attention implementation or E2E benchmark.
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
ENABLE_ENV = "QWEN36_KASCADE_PROBE_ENABLE"
AUDIT_ENV = "QWEN36_KASCADE_PROBE_AUDIT"
_LOCK = threading.Lock()
_DONE_LAYERS: set[str] = set()
_TARGET_LAYERS = set(range(3, 64, 4))
_ANCHORS: dict[int, dict] = {}


def _event(name: str, **fields: object) -> None:
    path = os.environ.get(AUDIT_ENV)
    if not path:
        raise RuntimeError(f"{AUDIT_ENV} is required")
    payload = {"event": name, "pid": os.getpid(), "time_ns": time.time_ns(), **fields}
    with open(path, "a", encoding="utf-8") as output:
        output.write(json.dumps(payload, sort_keys=True, allow_nan=False) + "\n")


def _budget(length: int, percent: int) -> int:
    # The author's paged decode kernel rounds the requested Top-K up to a
    # block_N=128 tile; the minimum is 128 and the live length caps it.
    return min(length, max(128, math.ceil(length * percent / 100 / 128) * 128))


def _summary(probabilities, selected, query, key, value, dense, scale):
    import torch

    mass = probabilities.index_select(1, selected).sum(dim=-1)
    selected_key = key.index_select(0, selected)
    selected_value = value.index_select(0, selected)
    weights = torch.softmax((query @ selected_key.T) * scale, dim=-1)
    sparse_math = weights @ selected_value
    difference = sparse_math - dense
    return {
        "mass_per_q_head": mass.tolist(),
        "mass_min": mass.min().item(),
        "mass_mean": mass.mean().item(),
        "output_max_abs_vs_native_dense": difference.abs().max().item(),
        "output_rms_vs_native_dense": difference.square().mean().sqrt().item(),
    }


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
    if hasattr(cls, "_kascade_probe_original"):
        raise RuntimeError("Kascade probe is already installed")
    original = cls.forward_fused_infer_attention
    original_forward = cls.forward
    _event("probe_installed", source=str(path), source_sha256=digest,
           torch=torch.__version__, torch_npu=torch_npu.__version__)

    def observed(self, query, key, value, attn_metadata, output, kv_cache=None):
        result = original(self, query, key, value, attn_metadata, output, kv_cache)
        layer_name = getattr(self, "_kascade_probe_layer_name", None)
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
            full_prob = torch.softmax((q @ k.T) * self.scale, dim=-1)
            full_math = full_prob @ v
            full_error = (full_math - dense).abs().max().item()
            rank = torch.distributed.get_rank() if torch.distributed.is_initialized() else 0
            if full_error > 0.1:
                _event("full_support_gate_failed", layer_name=layer_name,
                       tp_rank=rank, layer_index=layer_index, seq_len=length,
                       full_math_vs_dense_max_abs=full_error,
                       predeclared_max_abs_gate=0.1)
                return result
            previous_layer = layer_index - 4 if layer_index > 3 else None
            anchors = {index: item for index, item in _ANCHORS.items()
                       if index < layer_index and item["length"] == length}
            pooled = full_prob.sum(dim=0)
            cases = []
            selected_by_percent = {}
            for percent in (10, 20, 30):
                budget = _budget(length, percent)
                same_layer = torch.topk(pooled, budget, sorted=False).indices
                per_head = torch.topk(full_prob, budget, dim=-1, sorted=False).indices
                per_head_mass = full_prob.gather(1, per_head).sum(dim=-1)
                selected_by_percent[percent] = same_layer
                case = {
                    "requested_percent": percent, "selected_tokens": budget,
                    "same_layer_kv_pooled": _summary(
                        full_prob, same_layer, q, k, v, dense, self.scale),
                    "same_layer_per_q_head_exact_mass_min": per_head_mass.min().item(),
                    "same_layer_per_q_head_exact_mass_mean": per_head_mass.mean().item(),
                }
                if anchors:
                    candidates = []
                    for index, item in sorted(anchors.items()):
                        selected = item["indices"][percent]
                        masses = full_prob.index_select(1, selected).sum(dim=-1)
                        candidates.append((index, masses.min().item(),
                                           masses.mean().item()))
                    best_min = max(candidates, key=lambda x: (x[1], -x[0]))
                    best_mean = max(candidates, key=lambda x: (x[2], -x[0]))
                    case["best_earlier_anchor_by_min"] = {
                        "layer": best_min[0],
                        **_summary(full_prob, anchors[best_min[0]]["indices"][percent],
                                   q, k, v, dense, self.scale),
                    }
                    case["best_earlier_anchor_by_mean"] = {
                        "layer": best_mean[0],
                        **_summary(full_prob, anchors[best_mean[0]]["indices"][percent],
                                   q, k, v, dense, self.scale),
                    }
                    case["earlier_anchor_candidates"] = [
                        {"layer": index, "mass_min": minimum, "mass_mean": mean}
                        for index, minimum, mean in candidates
                    ]
                cases.append(case)
            _ANCHORS[layer_index] = {
                "length": length,
                "indices": selected_by_percent,
            }
            _event("real_decode_sample", layer_name=layer_name,
                   tp_rank=rank, layer_index=layer_index,
                   previous_layer=previous_layer,
                   eligible_earlier_anchor_layers=sorted(anchors),
                   seq_len=length, block_size=block_size, num_pages=num_pages,
                   local_q_heads=6, local_kv_heads=1,
                   full_math_vs_dense_max_abs=full_error, cases=cases)
        except BaseException as exc:
            _event("real_decode_sample_failed", layer_name=layer_name,
                   error=f"{type(exc).__name__}: {exc}")
            raise
        return result

    def observed_forward(self, *args, **kwargs):
        layer = args[0] if args else kwargs.get("layer")
        self._kascade_probe_layer_name = getattr(layer, "layer_name", None)
        return original_forward(self, *args, **kwargs)

    cls._kascade_probe_original = original
    cls._kascade_probe_original_forward = original_forward
    cls.forward = observed_forward
    cls.forward_fused_infer_attention = observed

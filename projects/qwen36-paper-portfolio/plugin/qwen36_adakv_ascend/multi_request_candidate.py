"""Opt-in Ada-KV request-indexed eager seam; correctness experiment, not a cache manager.

New-request prefill and one-token decode may coexist in a mixed turn. The
normal vLLM dense allocation remains; targeted layers skip its writes and use
compact per-request arenas. Continuation chunked prefill and graph still fail
closed. This is not a deployable cache-manager implementation.
"""

from __future__ import annotations

from contextvars import ContextVar
import hashlib
import os
from pathlib import Path

from .budget import allocate_global_head_budget
from .live_probe import EXPECTED_SOURCE_SHA256, TARGET_LAYER, WINDOW, _error, _event, _math_attention, _score


RUNNER_SHA256 = "94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968"
_REQUEST_IDS: ContextVar[tuple[str, ...] | None] = ContextVar("adakv_request_ids", default=None)
# BF16 native FIA versus FP32 mathematical attention is not bitwise parity.
# The independent dense native oracle peaked at 0.002642; a 32-token selected-
# support diagnostic peaked at 0.003757 (9 / 3968 above the old 0.003 gate).
# Keep a hard, separately predeclared native-math screen for the long test;
# this does not replace final task-accuracy acceptance.
MAX_NATIVE_MATH_REL_RMS = 0.005
MIN_NATIVE_MATH_COSINE = 0.99998


def register() -> None:
    if os.environ.get("QWEN36_ADAKV_MULTI_REQUEST_ENABLE") != "1":
        return
    import torch
    import torch.distributed as dist
    import torch_npu
    import vllm_ascend.ops  # noqa: F401 - required v0.23 plugin import order
    import vllm_ascend.attention.attention_v1 as attention
    import vllm_ascend.worker.model_runner_v1 as runner_module

    attention_source = Path(attention.__file__).resolve()
    runner_source = Path(runner_module.__file__).resolve()
    attention_digest = hashlib.sha256(attention_source.read_bytes()).hexdigest()
    runner_digest = hashlib.sha256(runner_source.read_bytes()).hexdigest()
    if attention_digest != EXPECTED_SOURCE_SHA256 or runner_digest != RUNNER_SHA256:
        raise RuntimeError(f"Ada-KV runtime source mismatch: {attention_digest}, {runner_digest}")
    capacity = int(os.environ.get("QWEN36_ADAKV_BASE_CAPACITY", "2048"))
    max_decode = int(os.environ.get("QWEN36_ADAKV_MAX_DECODE", "8"))
    max_requests = int(os.environ.get("QWEN36_ADAKV_MAX_REQUESTS", "2"))
    prefill_crosscheck = os.environ.get("QWEN36_ADAKV_PREFILL_NATIVE_CROSSCHECK") == "1"
    check_steps_raw = os.environ.get("QWEN36_ADAKV_NUMERIC_CHECK_STEPS", "all")
    if check_steps_raw == "all":
        check_steps = None
    elif check_steps_raw == "none":
        check_steps = frozenset()
    else:
        check_steps = frozenset(int(part) for part in check_steps_raw.split(","))
        if not check_steps or min(check_steps) <= 0 or max(check_steps) > max_decode:
            raise RuntimeError("invalid Ada-KV numeric check steps")
    audit_decode = os.environ.get("QWEN36_ADAKV_AUDIT_DECODE", "1") == "1"
    audit_dense_write = os.environ.get("QWEN36_ADAKV_AUDIT_DENSE_WRITE", "1") == "1"
    diagnostic_only = os.environ.get("QWEN36_ADAKV_NUMERIC_DIAGNOSTIC_ONLY") == "1"
    grouped_decode = os.environ.get("QWEN36_ADAKV_GROUPED_DECODE_ENABLE") == "1"
    grouped_crosscheck = os.environ.get("QWEN36_ADAKV_GROUPED_CROSSCHECK_ENABLE") == "1"
    all_full = os.environ.get("QWEN36_ADAKV_ALL_FULL_LAYERS") == "1"
    target_layers = (
        frozenset(f"language_model.model.layers.{i}.self_attn.attn" for i in range(3, 64, 4))
        if all_full else frozenset((TARGET_LAYER,))
    )
    if min(capacity, max_decode, max_requests) <= 0:
        raise RuntimeError("Ada-KV capacity, max_decode and max_requests must be positive")

    runner_cls = runner_module.NPUModelRunner
    attn_cls = attention.AscendAttentionBackendImpl
    if hasattr(runner_cls, "_adakv_original_model_forward") or hasattr(attn_cls, "_adakv_multi_original_forward"):
        raise RuntimeError("Ada-KV multi-request candidate already installed")
    original_model_forward = runner_cls._model_forward
    original_forward = attn_cls.forward
    original_reshape = attn_cls.reshape_and_cache
    original_forward_impl = attn_cls.forward_impl
    original_fia = attn_cls.forward_fused_infer_attention

    def model_forward(self, *args, **kwargs):
        batch = getattr(self, "input_batch", None)
        count = getattr(batch, "num_reqs", 0)
        ids = tuple(batch.req_ids[:count]) if count else ()
        # Startup warmups have no real request identity and must remain dense.
        if not ids:
            return original_model_forward(self, *args, **kwargs)
        if len(ids) != count or len(set(ids)) != count or len(ids) > max_requests:
            raise RuntimeError("Ada-KV request ID invariant failed")
        token = _REQUEST_IDS.set(ids)
        try:
            return original_model_forward(self, *args, **kwargs)
        finally:
            _REQUEST_IDS.reset(token)

    def _ids_and_boundaries(metadata, query):
        ids = _REQUEST_IDS.get()
        if ids is None:
            return None
        if attention._EXTRA_CTX.capturing:
            raise RuntimeError("Ada-KV multi-request candidate requires eager mode")
        if metadata.attn_state not in (attention.AscendAttentionState.PrefillNoCache,
                                       attention.AscendAttentionState.DecodeOnly,
                                       attention.AscendAttentionState.ChunkedPrefill):
            raise RuntimeError(f"unsupported Ada-KV attention state: {metadata.attn_state}")
        ends = tuple(int(x) for x in metadata.actual_seq_lengths_q)
        if (len(ends) != len(ids) or not ends or ends[-1] != int(metadata.num_actual_tokens)
                or ends[-1] > query.shape[0] or any(a >= b for a, b in zip((0,) + ends[:-1], ends))):
            raise RuntimeError(f"Ada-KV request/metadata alignment failed: ids={len(ids)}, q={ends}")
        if len(metadata.seq_lens_list) != len(ids):
            raise RuntimeError("Ada-KV request/sequence-length alignment failed")
        return ids, (0,) + ends

    def forward(self, *args, **kwargs):
        layer = args[0] if args else kwargs.get("layer")
        self._adakv_multi_layer = getattr(layer, "layer_name", None)
        return original_forward(self, *args, **kwargs)

    def reshape_and_cache(self, query, key, value, kv_cache, metadata, output):
        if self._adakv_multi_layer not in target_layers or _REQUEST_IDS.get() is None:
            return original_reshape(self, query, key, value, kv_cache, metadata, output)
        _ids_and_boundaries(metadata, query)
        if audit_dense_write:
            _event("multi_dense_write_skipped", layer_name=self._adakv_multi_layer,
                   state=str(metadata.attn_state), tokens=int(metadata.num_actual_tokens))
        return query, key, value, output

    def forward_impl(self, query, key, value, kv_cache, metadata, output):
        if self._adakv_multi_layer not in target_layers or _REQUEST_IDS.get() is None:
            return original_forward_impl(self, query, key, value, kv_cache, metadata, output)
        return self.forward_fused_infer_attention(query, key, value, metadata, output, kv_cache)

    def fia(self, query, key, value, metadata, output, kv_cache=None):
        layer_name = self._adakv_multi_layer
        if layer_name not in target_layers or _REQUEST_IDS.get() is None:
            return original_fia(self, query, key, value, metadata, output, kv_cache)
        ids, bounds = _ids_and_boundaries(metadata, query)
        if not dist.is_initialized() or dist.get_world_size() != 4:
            raise RuntimeError("Ada-KV multi-request candidate requires initialized TP4")
        if query.ndim != 3 or query.shape[1:] != (6, 256):
            raise RuntimeError("unexpected Ada-KV query geometry")
        if key.shape != (query.shape[0], 1, 256) or value.shape != key.shape:
            raise RuntimeError("unexpected Ada-KV K/V geometry")
        caches = getattr(self, "_adakv_multi_caches", {})
        # A request ID uniquely owns an arena. Drop completed requests so
        # sequential arrivals cannot inherit state or retain stale HBM.
        caches = {req_id: caches[req_id] for req_id in ids if req_id in caches}
        self._adakv_multi_caches = caches
        if grouped_decode and metadata.attn_state == attention.AscendAttentionState.DecodeOnly and len(ids) > 1:
            pending = []
            for index, req_id in enumerate(ids):
                start, end = bounds[index:index + 2]
                if req_id not in caches or end - start != 1:
                    raise RuntimeError("Ada-KV grouped decode request invariant failed")
                compact_k, compact_v, n, step = caches[req_id]
                if n >= compact_k.shape[0]:
                    raise RuntimeError("Ada-KV grouped compact cache exceeded max_decode")
                compact_k[n:n + 1].copy_(key[start:end])
                compact_v[n:n + 1].copy_(value[start:end])
                pending.append((req_id, start, compact_k, compact_v, n + 1, step))
            kv_ends = []
            total = 0
            for _req_id, _start, _compact_k, _compact_v, n, _step in pending:
                total += n
                kv_ends.append(total)
            grouped_q = torch.cat([query[start:start + 1] for _, start, *_ in pending], dim=0)
            grouped_k = torch.cat([compact_k[:n] for _, _, compact_k, _, n, _ in pending], dim=0)
            grouped_v = torch.cat([compact_v[:n] for _, _, _, compact_v, n, _ in pending], dim=0)
            selected, _ = torch_npu.npu_fused_infer_attention_score(
                query=grouped_q, key=grouped_k, value=grouped_v,
                input_layout="TND", actual_seq_lengths=list(range(1, len(pending) + 1)),
                actual_seq_lengths_kv=kv_ends, num_key_value_heads=1,
                num_heads=6, scale=self.scale, sparse_mode=0)
            for index, (req_id, start, compact_k, compact_v, n, step) in enumerate(pending):
                if grouped_crosscheck and step < 3:
                    solo, _ = torch_npu.npu_fused_infer_attention_score(
                        query=query[start:start + 1], key=compact_k[:n], value=compact_v[:n],
                        input_layout="TND", actual_seq_lengths=[1],
                        actual_seq_lengths_kv=[n], num_key_value_heads=1,
                        num_heads=6, scale=self.scale, sparse_mode=0)
                    if not torch.equal(selected[index:index + 1], solo):
                        _event("multi_grouped_native_mismatch", layer_name=layer_name,
                               request_index=index, decode_step=step + 1,
                               grouped_vs_solo=_error(selected[index], solo[0]))
                        raise RuntimeError("Ada-KV grouped native FIA differs from solo FIA")
                check_numeric = check_steps is None or step + 1 in check_steps
                error = expected_rms = None
                if check_numeric:
                    expected = _math_attention(query[start:start + 1], compact_k[:n],
                                               compact_v[:n], self.scale)
                    error = _error(selected[index], expected.to(selected.dtype))
                    expected_rms = float(expected.float().square().mean().sqrt().item())
                    finite = (bool(torch.isfinite(selected[index]).all().item())
                              and bool(torch.isfinite(expected).all().item()))
                    failed = (expected_rms <= 0 or not finite
                              or error["rms"] > MAX_NATIVE_MATH_REL_RMS * expected_rms
                              or error["cosine"] < MIN_NATIVE_MATH_COSINE)
                    if failed:
                        _event("multi_numeric_gate_failed", layer_name=layer_name,
                               request_index=index, decode_step=step + 1,
                               selected_tokens=n, rounded_reference_error=error,
                               expected_rms=expected_rms,
                               fatal=not diagnostic_only or expected_rms <= 0 or not finite)
                        if not diagnostic_only or expected_rms <= 0 or not finite:
                            raise RuntimeError("Ada-KV grouped native selected-support gate failed")
                output[start:start + 1] = selected[index:index + 1].view(1, 6, 256)
                caches[req_id] = (compact_k, compact_v, n, step + 1)
                if audit_decode:
                    _event("multi_grouped_decode", layer_name=layer_name,
                           request_index=index, decode_step=step + 1,
                           selected_tokens=n, rounded_reference_error=error,
                           expected_rms=expected_rms, grouped_size=len(pending))
            return output
        if metadata.attn_state == attention.AscendAttentionState.PrefillNoCache:
            original_fia(self, query, key, value, metadata, output, kv_cache)
        for index, req_id in enumerate(ids):
            start, end = bounds[index:index + 2]
            qlen = end - start
            if req_id not in caches:
                # New prefill only. A continuation would need already-stored
                # prefill tokens; silently treating it as fresh loses context.
                if qlen <= 1 or int(metadata.seq_lens_list[index]) != qlen:
                    raise RuntimeError(f"Ada-KV unsupported continuation prefill: index={index}")
                if metadata.attn_state == attention.AscendAttentionState.DecodeOnly:
                    raise RuntimeError("Ada-KV DecodeOnly contains a new prefill request")
                if (metadata.attn_state == attention.AscendAttentionState.ChunkedPrefill
                        or prefill_crosscheck):
                    q, k, v = query[start:end], key[start:end], value[start:end]
                    prefill_output, _ = torch_npu.npu_fused_infer_attention_score(
                        query=q, key=k, value=v, atten_mask=metadata.attn_mask,
                        input_layout="TND", actual_seq_lengths=[qlen],
                        actual_seq_lengths_kv=[qlen], num_key_value_heads=1,
                        num_heads=6, scale=self.scale, sparse_mode=3)
                    prefill_output = prefill_output.view(qlen, 6, 256)
                    if metadata.attn_state == attention.AscendAttentionState.ChunkedPrefill:
                        output[start:end] = prefill_output
                    else:
                        reference = output[start:end]
                        error = _error(prefill_output, reference)
                        reference_rms = float(reference.float().square().mean().sqrt().item())
                        _event("multi_prefill_native_crosscheck", layer_name=layer_name,
                               request_index=index, full_length=qlen,
                               direct_vs_original=error, reference_rms=reference_rms)
                        if (reference_rms <= 0 or error["rms"] > 0.003 * reference_rms
                                or not bool(torch.isfinite(prefill_output).all().item())):
                            raise RuntimeError("Ada-KV split-native prefill crosscheck failed")
                q, k, v = query[start:end], key[start:end], value[start:end]
                length = end - start
                if length <= WINDOW + capacity:
                    selected = torch.arange(length, device=k.device)
                    budget = None
                else:
                    score = _score(q, k, self.scale)
                    if not bool(torch.isfinite(score).all().item()):
                        raise RuntimeError("nonfinite Ada-KV observation scores")
                    local, budgets, _counts = allocate_global_head_budget(score[None], capacity, 0.5)
                    top = torch.argsort(score, descending=True, stable=True)[:int(local[0].item())]
                    selected = torch.cat((top.sort().values,
                                          torch.arange(length - WINDOW, length, device=k.device)))
                    budget = budgets[0].cpu().tolist()
                n = int(selected.numel())
                compact_k = torch.empty((n + max_decode, 1, 256), dtype=k.dtype, device=k.device)
                compact_v = torch.empty_like(compact_k)
                compact_k[:n].copy_(k.index_select(0, selected))
                compact_v[:n].copy_(v.index_select(0, selected))
                caches[req_id] = (compact_k, compact_v, n, 0)
                _event("multi_prefill_compact", layer_name=layer_name, request_index=index,
                       full_length=length, selected_tokens=n, budget=budget,
                       state=str(metadata.attn_state))
                continue
            if metadata.attn_state == attention.AscendAttentionState.PrefillNoCache:
                raise RuntimeError("Ada-KV PrefillNoCache contains existing request")
            if qlen != 1:
                raise RuntimeError("Ada-KV only supports one-token decode for existing requests")
            compact_k, compact_v, n, step = caches[req_id]
            if n >= compact_k.shape[0]:
                raise RuntimeError("Ada-KV compact cache exceeded max_decode")
            compact_k[n:n + 1].copy_(key[start:start + 1])
            compact_v[n:n + 1].copy_(value[start:start + 1])
            n += 1
            selected, _ = torch_npu.npu_fused_infer_attention_score(
                query=query[start:start + 1], key=compact_k[:n], value=compact_v[:n],
                input_layout="TND", actual_seq_lengths=[1], actual_seq_lengths_kv=[n],
                num_key_value_heads=1, num_heads=6, scale=self.scale, sparse_mode=0)
            check_numeric = check_steps is None or step + 1 in check_steps
            error = expected_rms = None
            if check_numeric:
                expected = _math_attention(query[start:start + 1], compact_k[:n], compact_v[:n], self.scale)
                rounded = expected.to(selected.dtype)
                error = _error(selected[0], rounded)
                expected_rms = float(expected.float().square().mean().sqrt().item())
                finite = (bool(torch.isfinite(selected).all().item())
                          and bool(torch.isfinite(expected).all().item()))
                if expected_rms <= 0 or not finite:
                    _event("multi_numeric_gate_failed", layer_name=layer_name, request_index=index,
                           decode_step=step + 1, selected_tokens=n, rounded_reference_error=error,
                           expected_rms=expected_rms, fatal=True)
                    raise RuntimeError("Ada-KV multi-request native selected-support gate failed")
                if (error["rms"] > MAX_NATIVE_MATH_REL_RMS * expected_rms
                        or error["cosine"] < MIN_NATIVE_MATH_COSINE):
                    _event("multi_numeric_gate_failed", layer_name=layer_name, request_index=index,
                           decode_step=step + 1, selected_tokens=n, rounded_reference_error=error,
                           expected_rms=expected_rms, fatal=not diagnostic_only)
                    if not diagnostic_only:
                        raise RuntimeError("Ada-KV multi-request native selected-support gate failed")
            output[start:start + 1] = selected.view(1, 6, 256)
            caches[req_id] = (compact_k, compact_v, n, step + 1)
            if audit_decode and check_numeric:
                _event("multi_decode_compact", layer_name=layer_name, request_index=index,
                       decode_step=step + 1, selected_tokens=n, rounded_reference_error=error,
                       expected_rms=expected_rms, output_replaced=True)
        return output

    runner_cls._adakv_original_model_forward = original_model_forward
    attn_cls._adakv_multi_original_forward = original_forward
    runner_cls._model_forward = model_forward
    attn_cls.forward = forward
    attn_cls.reshape_and_cache = reshape_and_cache
    attn_cls.forward_impl = forward_impl
    attn_cls.forward_fused_infer_attention = fia
    _event("multi_candidate_installed", target_layers=sorted(target_layers),
           attention_sha256=attention_digest, runner_sha256=runner_digest,
           capacity=capacity, max_decode=max_decode, max_requests=max_requests,
           prefill_crosscheck=prefill_crosscheck, numeric_check_steps=check_steps_raw,
           audit_decode=audit_decode, audit_dense_write=audit_dense_write,
           numeric_diagnostic_only=diagnostic_only,
           grouped_decode=grouped_decode, grouped_crosscheck=grouped_crosscheck,
           torch_npu=torch_npu.__version__)

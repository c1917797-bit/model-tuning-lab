"""Fail-closed vLLM-Ascend v0.23 adapter for Qwen3.6 DeltaLog."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
import threading
import time
from typing import Any
from .layout_controls import check_layout, identity_same


LOGGER = logging.getLogger(__name__)
PATCH_VERSION = "0.2.2"
ENABLE_ENV = "QWEN36_DELTALOG_ENABLE"
LIBRARY_ENV = "QWEN36_DELTALOG_LIBRARY"
AUDIT_ENV = "QWEN36_DELTALOG_AUDIT"
EXPECTED_GDN_SHA256 = "d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816"
PACKED_WIDTH = 2560
KEY_HEADS = 4
VALUE_HEADS = 12
HEAD_DIM = 128
CAPACITY = 7
META_STRIDE = 16
_LOCK = threading.Lock()
_SEEN: set[tuple[int, str, str]] = set()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _audit(event: str, **fields: Any) -> None:
    path_value = os.environ.get(AUDIT_ENV)
    if not path_value:
        return
    payload = {
        "event": event,
        "patch_version": PATCH_VERSION,
        "pid": os.getpid(),
        "rank": os.environ.get("RANK"),
        "local_rank": os.environ.get("LOCAL_RANK"),
        "time_ns": time.time_ns(),
        **fields,
    }
    data = (json.dumps(payload, sort_keys=True, allow_nan=False) + "\n").encode()
    path = Path(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)


def _audit_once(event: str, key: str, **fields: Any) -> None:
    identity = (os.getpid(), event, key)
    with _LOCK:
        if identity in _SEEN:
            return
        _SEEN.add(identity)
    _audit(event, key=key, **fields)


def _valid_base(torch: Any, self: Any) -> Any | None:
    if len(getattr(self, "kv_cache", ())) < 2:
        return None
    base = self.kv_cache[1]
    if not isinstance(base, torch.Tensor):
        return None
    if base.device.type != "npu" or base.dtype != torch.float32 or base.ndim != 4:
        return None
    if list(base.shape[1:]) != [VALUE_HEADS, HEAD_DIM, HEAD_DIM]:
        return None
    return base


def _ensure_aux(torch: Any, self: Any) -> dict[str, Any] | None:
    base = _valid_base(torch, self)
    if base is None:
        return None
    existing = getattr(self, "_qwen36_deltalog_aux", None)
    base_ptr = base.untyped_storage().data_ptr()
    base_identity = check_layout(base)
    if existing is not None:
        if identity_same(existing["base_identity"], base_identity):
            return existing
        if bool(torch.any(existing["length"][:, :, 0] != 0).item()):
            raise RuntimeError(
                "DeltaLog base-state storage changed while auxiliary entries were live"
            )
        _audit(
            "aux_reallocated_for_base_change",
            prefix=getattr(self, "prefix", None),
            old_base_ptr=existing["base_ptr"],
            new_base_ptr=base_ptr,
        )
    slots = int(base.shape[0])
    options = {"device": base.device}
    aux = {
        "base_ptr": base_ptr,
        "base_identity": base_identity,
        "slots": slots,
        "k_log": torch.zeros((slots, KEY_HEADS, CAPACITY, HEAD_DIM),
                             dtype=torch.bfloat16, **options),
        "u_log": torch.zeros((slots, VALUE_HEADS, CAPACITY, HEAD_DIM),
                             dtype=torch.float32, **options),
        "lambda_log": torch.zeros((slots, VALUE_HEADS, META_STRIDE),
                                  dtype=torch.float32, **options),
        "decay": torch.zeros((slots, VALUE_HEADS, META_STRIDE),
                             dtype=torch.float32, **options),
        "length": torch.zeros((slots, VALUE_HEADS, META_STRIDE),
                              dtype=torch.int32, **options),
    }
    self._qwen36_deltalog_aux = aux
    bytes_allocated = sum(
        tensor.numel() * tensor.element_size()
        for tensor in aux.values()
        if isinstance(tensor, torch.Tensor)
    )
    _audit(
        "aux_allocated",
        prefix=getattr(self, "prefix", None),
        slots=slots,
        bytes=bytes_allocated,
        base_ptr=base_ptr,
    )
    return aux


def _reset_selected(aux: dict[str, Any], indices: Any) -> None:
    if indices is None or indices.numel() == 0:
        return
    selected = indices.flatten().long()
    for name in ("k_log", "u_log", "lambda_log", "decay", "length"):
        aux[name].index_fill_(0, selected, 0)


def _flush_slots(
    torch: Any, self: Any, aux: dict[str, Any], indices: Any, reason: str,
    selection: str = "batch",
) -> None:
    if indices.numel() == 0:
        return
    base = self.kv_cache[1]
    if indices.device != base.device or indices.dtype not in (torch.int32, torch.int64):
        raise RuntimeError("DeltaLog fallback slot indices must be NPU int32/int64")
    selected = indices.reshape(-1).long()
    selected_base = base.index_select(0, selected)
    k_log = (
        aux["k_log"]
        .index_select(0, selected)
        .float()
        .repeat_interleave(VALUE_HEADS // KEY_HEADS, dim=1)
    )
    u_log = aux["u_log"].index_select(0, selected)
    lambda_log = aux["lambda_log"].index_select(0, selected)[:, :, :CAPACITY]
    decay = aux["decay"].index_select(0, selected)[:, :, 0]
    length = aux["length"].index_select(0, selected)[:, :, 0]
    live = (
        torch.arange(CAPACITY, dtype=torch.int32, device=base.device)
        .view(1, 1, CAPACITY)
        < length.unsqueeze(-1)
    )
    # Dead entries retain stale payload after a selected-slot flush. Mask the
    # exponent *before* exp: multiplying an overflowed exp by zero is NaN.
    safe_lambda = torch.where(live, lambda_log, decay.unsqueeze(-1))
    coeff = torch.exp(decay.unsqueeze(-1) - safe_lambda) * live.float()
    # Dead payloads are outside the logical state. Zero them BEFORE arithmetic:
    # a zero coefficient does not make 0 * NaN/Inf safe.
    live_payload = live.unsqueeze(-1)
    safe_u_log = torch.where(live_payload, u_log, torch.zeros_like(u_log))
    safe_k_log = torch.where(live_payload, k_log, torch.zeros_like(k_log))
    contribution = torch.einsum("shl,shlv,shlk->shvk", coeff, safe_u_log, safe_k_log)
    logical = (
        torch.exp(decay).unsqueeze(-1).unsqueeze(-1) * selected_base
        + contribution
    )
    # Diagnostic bridge fail-closed gate, BEFORE any selected state mutation.
    # This host synchronization is explicit and is NOT a formal timing path.
    if not bool(torch.isfinite(logical).all().item()):
        raise RuntimeError("DeltaLog selected logical state is non-finite; live payload/base/decay invalid")
    base.index_copy_(0, selected, logical)
    # A zero length makes K/U/lambda payloads invisible. Clearing those large
    # tensors on every mixed batch would undo the deferred-write saving; the
    # next append overwrites entry zero before it becomes live again.
    aux["decay"].index_fill_(0, selected, 0)
    aux["length"].index_fill_(0, selected, 0)
    _audit(
        "aux_materialized_for_fallback",
        prefix=getattr(self, "prefix", None),
        reason=reason,
        selection=selection,
        selected_slots=int(selected.numel()),
    )


def _flush_all(torch: Any, self: Any, aux: dict[str, Any], reason: str) -> None:
    lengths = aux["length"][:, :, 0]
    if not bool(torch.any(lengths != 0).item()):
        return
    active = torch.nonzero(lengths[:, 0] != 0, as_tuple=False).flatten()
    _flush_slots(torch, self, aux, active, reason, selection="all_live")


def _reset_prefill(aux: dict[str, Any], metadata: Any) -> None:
    if getattr(metadata, "num_prefills", 0) <= 0:
        return
    _reset_selected(aux, getattr(metadata, "prefill_state_indices", None))


def _fallback(
    torch: Any,
    original: Any,
    reason: str,
    self: Any,
    aux: dict[str, Any] | None,
    metadata: Any,
    mixed_qkv: Any,
    b: Any,
    a: Any,
    core_attn_out: Any,
) -> Any:
    if aux is not None:
        if (
            reason == "not_pure_decode"
            and metadata is not None
            and metadata.num_decodes > 0
            and metadata.num_prefills > 0
            and isinstance(metadata.non_spec_state_indices_tensor, torch.Tensor)
            and isinstance(metadata.prefill_state_indices, torch.Tensor)
            and metadata.non_spec_state_indices_tensor.device == aux["length"].device
            and metadata.prefill_state_indices.device == aux["length"].device
            and metadata.non_spec_state_indices_tensor.dtype in (torch.int32, torch.int64)
            and metadata.prefill_state_indices.dtype in (torch.int32, torch.int64)
        ):
            # The native mixed path reads decode slots, then initializes the
            # prefill slots. Materialize only those slots without a host-side
            # nonzero/item synchronization on every GDN layer and TP rank.
            selected = torch.cat(
                (
                    metadata.non_spec_state_indices_tensor[: metadata.num_decodes],
                    metadata.prefill_state_indices,
                )
            )
            _flush_slots(torch, self, aux, selected, reason)
        else:
            _flush_all(torch, self, aux, reason)
    result = original(self, mixed_qkv, b, a, core_attn_out)
    if aux is not None and metadata is not None:
        _reset_prefill(aux, metadata)
    _audit_once("native_fallback", reason, prefix=getattr(self, "prefix", None))
    return result


def _eligibility_reason(
    torch: Any,
    self: Any,
    metadata: Any,
    aux: dict[str, Any] | None,
    mixed_qkv: Any,
    b: Any,
    a: Any,
    core: Any,
) -> str | None:
    if aux is None:
        return "aux_unavailable"
    if metadata.spec_sequence_masks is not None:
        return "speculative_or_multi_query"
    if metadata.num_prefills != 0 or metadata.num_decodes <= 0:
        return "not_pure_decode"
    tokens = int(metadata.num_actual_tokens)
    if tokens != int(metadata.num_decodes) or tokens != int(metadata.num_decode_tokens):
        return "decode_token_count_mismatch"
    if tokens < 1 or tokens > 16:
        return "decode_token_count_unsupported"
    tensors = (mixed_qkv, b, a, core)
    if any(not isinstance(t, torch.Tensor) or t.device.type != "npu" for t in tensors):
        return "non_npu_tensor"
    if mixed_qkv.dtype != torch.bfloat16 or list(mixed_qkv.shape) != [tokens, PACKED_WIDTH]:
        return "packed_qkv_contract"
    if b.dtype != torch.bfloat16 or a.dtype != torch.bfloat16:
        return "gating_dtype"
    if list(b.shape) != [tokens, VALUE_HEADS] or list(a.shape) != [tokens, VALUE_HEADS]:
        return "gating_shape"
    if core.dtype != torch.bfloat16 or list(core.shape[1:]) != [VALUE_HEADS, HEAD_DIM]:
        return "output_contract"
    if getattr(self, "tp_size", None) != 4:
        return "tp_size"
    if getattr(self, "head_k_dim", None) != HEAD_DIM or getattr(self, "head_v_dim", None) != HEAD_DIM:
        return "head_dim"
    if getattr(self, "num_k_heads", None) // self.tp_size != KEY_HEADS:
        return "local_key_heads"
    if getattr(self, "num_v_heads", None) // self.tp_size != VALUE_HEADS:
        return "local_value_heads"
    indices = metadata.non_spec_state_indices_tensor
    if indices is None or indices.device.type != "npu" or indices.dtype != torch.int32:
        return "state_indices_contract"
    if indices.numel() != tokens:
        return "state_indices_shape"
    decode = metadata.non_spec_decode_metadata
    if decode is None or decode.causal_conv1d is None:
        return "decode_metadata"
    seq = decode.actual_seq_lengths
    if seq is None or seq.device.type != "npu" or seq.dtype != torch.int32:
        return "actual_seq_lengths_contract"
    if seq.numel() != tokens + 1:
        return "actual_seq_lengths_shape"
    return None

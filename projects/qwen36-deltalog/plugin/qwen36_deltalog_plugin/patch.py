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


LOGGER = logging.getLogger(__name__)
PATCH_VERSION = "0.2.0"
ENABLE_ENV = "QWEN36_DELTALOG_ENABLE"
LIBRARY_ENV = "QWEN36_DELTALOG_LIBRARY"
AUDIT_ENV = "QWEN36_DELTALOG_AUDIT"
EXPECTED_GDN_SHA256 = "d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816"
EXPECTED_LIBRARY_SHA256 = "a3698261d9e6de185b49aba5dd5aee1dc676cbb457e3e172aec826475bb57513"
EXPECTED_SCHEMA = (
    "qwen36_deltalog::decode(Tensor query, Tensor key, Tensor value, Tensor g, "
    "Tensor beta, Tensor(a!) base_state, Tensor(b!) k_log, Tensor(c!) u_log, "
    "Tensor(d!) lambda_log, Tensor(e!) cumulative_decay, Tensor(f!) log_length, "
    "Tensor actual_seq_lengths, Tensor state_indices) -> Tensor"
)
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
    if existing is not None:
        if existing["base_ptr"] == base_ptr and existing["slots"] == int(base.shape[0]):
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


def _flush_all(torch: Any, self: Any, aux: dict[str, Any], reason: str) -> None:
    lengths = aux["length"][:, :, 0]
    if not bool(torch.any(lengths != 0).item()):
        return
    active = torch.nonzero(lengths[:, 0] != 0, as_tuple=False).flatten()
    base = self.kv_cache[1]
    selected_base = base.index_select(0, active)
    k_log = (
        aux["k_log"]
        .index_select(0, active)
        .float()
        .repeat_interleave(VALUE_HEADS // KEY_HEADS, dim=1)
    )
    u_log = aux["u_log"].index_select(0, active)
    lambda_log = aux["lambda_log"].index_select(0, active)[:, :, :CAPACITY]
    decay = aux["decay"].index_select(0, active)[:, :, 0]
    length = aux["length"].index_select(0, active)[:, :, 0]
    live = (
        torch.arange(CAPACITY, dtype=torch.int32, device=base.device)
        .view(1, 1, CAPACITY)
        < length.unsqueeze(-1)
    )
    coeff = torch.exp(decay.unsqueeze(-1) - lambda_log) * live.float()
    contribution = torch.einsum("shl,shlv,shlk->shvk", coeff, u_log, k_log)
    logical = (
        torch.exp(decay).unsqueeze(-1).unsqueeze(-1) * selected_base
        + contribution
    )
    base.index_copy_(0, active, logical)
    _reset_selected(aux, active)
    _audit(
        "aux_materialized_for_fallback",
        prefix=getattr(self, "prefix", None),
        reason=reason,
        active_slots=int(active.numel()),
    )


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


def register() -> None:
    """Install the adapter only when explicitly enabled."""
    if os.environ.get(ENABLE_ENV) != "1":
        return

    import torch

    library_value = os.environ.get(LIBRARY_ENV)
    if not library_value:
        raise RuntimeError(f"{LIBRARY_ENV} is required when {ENABLE_ENV}=1")
    library = Path(library_value).resolve()
    if not library.is_file():
        raise RuntimeError(f"candidate library not found: {library}")
    library_sha256 = _sha256(library)
    if library_sha256 != EXPECTED_LIBRARY_SHA256:
        raise RuntimeError(
            f"candidate library identity changed: {library_sha256}; "
            f"expected {EXPECTED_LIBRARY_SHA256}"
        )

    from vllm_ascend.utils import enable_custom_op

    if not enable_custom_op():
        raise RuntimeError("vLLM-Ascend custom operators are unavailable")
    torch.ops.load_library(str(library))
    schema = str(torch.ops.qwen36_deltalog.decode.default._schema)
    if schema != EXPECTED_SCHEMA:
        raise RuntimeError(f"candidate schema changed: {schema}")

    import vllm_ascend.ops.gdn as gdn
    from vllm.model_executor.layers.fla.ops.l2norm import l2norm_fwd
    from vllm_ascend.device.device_op import DeviceOperator

    source = Path(gdn.__file__).resolve()
    source_sha256 = _sha256(source)
    if source_sha256 != EXPECTED_GDN_SHA256:
        raise RuntimeError(
            f"vLLM-Ascend GDN source changed: {source_sha256}; re-audit required"
        )

    cls = gdn.AscendGatedDeltaNetAttention
    if getattr(cls, "_qwen36_deltalog_patch_version", None) == PATCH_VERSION:
        return
    if hasattr(cls, "_qwen36_deltalog_original_forward_core"):
        raise RuntimeError("another DeltaLog patch is already installed")
    if hasattr(cls, "_qwen36_decode_core_patch_version"):
        raise RuntimeError("the incompatible GDN decode-core patch is installed")

    original = cls._forward_core

    def patched_forward_core(
        self: Any,
        mixed_qkv: Any,
        b: Any,
        a: Any,
        core_attn_out: Any,
    ) -> Any:
        aux = _ensure_aux(torch, self)
        forward_context = gdn.get_forward_context()
        metadata_map = forward_context.attn_metadata
        if metadata_map is None:
            return _fallback(
                torch, original, "profile_run", self, aux, None,
                mixed_qkv, b, a, core_attn_out
            )
        if not isinstance(metadata_map, dict) or self.prefix not in metadata_map:
            return _fallback(
                torch, original, "metadata_map", self, aux, None,
                mixed_qkv, b, a, core_attn_out
            )
        metadata = metadata_map[self.prefix]
        if not isinstance(metadata, gdn.GDNAttentionMetadata):
            return _fallback(
                torch, original, "metadata_type", self, aux, None,
                mixed_qkv, b, a, core_attn_out
            )
        reason = _eligibility_reason(
            torch, self, metadata, aux, mixed_qkv, b, a, core_attn_out
        )
        if reason is not None:
            return _fallback(
                torch, original, reason, self, aux, metadata,
                mixed_qkv, b, a, core_attn_out
            )

        tokens = int(metadata.num_actual_tokens)
        packed = mixed_qkv[:tokens]
        a_decode = a[:tokens]
        b_decode = b[:tokens]
        conv_weights = self.conv1d.weight.view(
            self.conv1d.weight.size(0), self.conv1d.weight.size(2)
        )
        conv_metadata = metadata.non_spec_decode_metadata.causal_conv1d
        post_conv = torch.empty_like(packed)
        torch.ops._C_ascend.npu_causal_conv1d_custom(
            post_conv,
            packed,
            conv_weights.transpose(0, 1),
            conv_state=self.kv_cache[0],
            bias_opt=self.conv1d.bias,
            query_start_loc_opt=conv_metadata.query_start_loc,
            cache_indices_opt=conv_metadata.cache_indices,
            initial_state_mode_opt=None,
            num_accepted_tokens_opt=None,
            activation_mode=1 if self.activation else 0,
            pad_slot_id=gdn.PAD_SLOT_ID,
            run_mode=1,
        )
        try:
            query, key, value = self.rearrange_mixed_qkv(post_conv)
            query = l2norm_fwd(query).squeeze(0).contiguous()
            key = l2norm_fwd(key).squeeze(0).contiguous()
            value = value.squeeze(0).contiguous()
            gating, beta = DeviceOperator.fused_gdn_gating(
                self.A_log, a_decode, b_decode, self.dt_bias
            )
            result = torch.ops.qwen36_deltalog.decode(
                query,
                key,
                value,
                gating.squeeze(0).contiguous(),
                beta.squeeze(0).contiguous(),
                self.kv_cache[1],
                aux["k_log"],
                aux["u_log"],
                aux["lambda_log"],
                aux["decay"],
                aux["length"],
                metadata.non_spec_decode_metadata.actual_seq_lengths,
                metadata.non_spec_state_indices_tensor,
            )
            core_attn_out[:tokens].copy_(result)
        except BaseException:
            _audit(
                "candidate_dispatch_failed",
                prefix=self.prefix,
                num_tokens=tokens,
                library_sha256=library_sha256,
            )
            raise

        _audit_once(
            "candidate_dispatch",
            str(self.prefix),
            prefix=self.prefix,
            num_tokens=tokens,
            library_sha256=library_sha256,
        )
        return None

    cls._qwen36_deltalog_original_forward_core = original
    cls._forward_core = patched_forward_core
    cls._qwen36_deltalog_patch_version = PATCH_VERSION
    _audit(
        "plugin_installed",
        library=str(library),
        library_sha256=library_sha256,
        source=str(source),
        source_sha256=source_sha256,
        schema=schema,
    )
    LOGGER.warning(
        "Installed Qwen3.6 DeltaLog plugin %s with library %s",
        PATCH_VERSION,
        library,
    )

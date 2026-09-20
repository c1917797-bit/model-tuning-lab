"""Fail-closed vLLM-Ascend v0.23 adapter for the fused GDN decode core.

The plugin keeps causal convolution and the deployed Q/K normalization on the
audited upstream path and replaces only gating plus recurrent update for the
exact Qwen3.6-27B TP4 non-speculative decode ABI.
"""

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
PATCH_VERSION = "0.1.0"
ENABLE_ENV = "QWEN36_GDN_DECODE_CORE_ENABLE"
LIBRARY_ENV = "QWEN36_GDN_DECODE_CORE_LIBRARY"
AUDIT_ENV = "QWEN36_GDN_DECODE_CORE_AUDIT"
EXPECTED_GDN_SHA256 = "d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816"
EXPECTED_LIBRARY_SHA256 = "feaf6a4297dc2b688dc41cc5c49851188c7de8d156b2aa9583f4b4b38e38ed69"
EXPECTED_SCHEMA = (
    "qwen36_gdn::decode_core(Tensor query, Tensor key, Tensor value, "
    "Tensor a_log, Tensor a, Tensor b, Tensor dt_bias, Tensor(a!) state, Tensor actual_seq_lengths, "
    "Tensor state_indices) -> Tensor"
)
PACKED_WIDTH = 2560
VALUE_HEADS = 12
HEAD_DIM = 128
_LOCK = threading.Lock()
_DISPATCH_LOGGED: set[tuple[int, str]] = set()
_FALLBACK_LOGGED: set[tuple[int, str]] = set()


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
    seen = _DISPATCH_LOGGED if event == "candidate_dispatch" else _FALLBACK_LOGGED
    identity = (os.getpid(), key)
    with _LOCK:
        if identity in seen:
            return
        seen.add(identity)
    _audit(event, key=key, **fields)


def _fallback(
    original: Any,
    reason: str,
    self: Any,
    mixed_qkv: Any,
    b: Any,
    a: Any,
    core_attn_out: Any,
) -> Any:
    _audit_once("native_fallback", reason, prefix=getattr(self, "prefix", None))
    return original(self, mixed_qkv, b, a, core_attn_out)


def _eligibility_reason(torch: Any, self: Any, metadata: Any, mixed_qkv: Any, b: Any, a: Any, core: Any) -> str | None:
    if metadata.spec_sequence_masks is not None:
        return "speculative_or_multi_query"
    if metadata.num_prefills != 0 or metadata.num_decodes <= 0:
        return "not_decode_only"
    num_tokens = int(metadata.num_actual_tokens)
    if num_tokens != int(metadata.num_decodes) or num_tokens != int(metadata.num_decode_tokens):
        return "decode_token_count_mismatch"
    tensors = (mixed_qkv, b, a, core)
    if any(not isinstance(tensor, torch.Tensor) for tensor in tensors):
        return "non_tensor_input"
    if any(tensor.device.type != "npu" for tensor in tensors):
        return "non_npu_input"
    if mixed_qkv.dtype != torch.bfloat16 or mixed_qkv.ndim != 2:
        return "packed_qkv_dtype_or_rank"
    if list(mixed_qkv.shape) != [num_tokens, PACKED_WIDTH]:
        return "packed_qkv_shape"
    if b.dtype != torch.bfloat16 or a.dtype != torch.bfloat16:
        return "gating_dtype"
    if list(b.shape) != [num_tokens, VALUE_HEADS] or list(a.shape) != [num_tokens, VALUE_HEADS]:
        return "gating_shape"
    if core.dtype != torch.bfloat16 or core.ndim != 3:
        return "output_dtype_or_rank"
    if list(core.shape[1:]) != [VALUE_HEADS, HEAD_DIM] or core.shape[0] < num_tokens:
        return "output_shape"
    if getattr(self, "tp_size", None) != 4:
        return "tp_size"
    if getattr(self, "head_k_dim", None) != HEAD_DIM or getattr(self, "head_v_dim", None) != HEAD_DIM:
        return "head_dim"
    if getattr(self, "num_k_heads", None) // self.tp_size != 4:
        return "local_key_heads"
    if getattr(self, "num_v_heads", None) // self.tp_size != VALUE_HEADS:
        return "local_value_heads"
    if len(getattr(self, "kv_cache", ())) < 2:
        return "missing_kv_cache"
    state = self.kv_cache[1]
    if state.device.type != "npu" or state.dtype != torch.float32 or state.ndim != 4:
        return "state_dtype_or_rank"
    if list(state.shape[1:]) != [VALUE_HEADS, HEAD_DIM, HEAD_DIM]:
        return "state_shape"
    if self.A_log.device.type != "npu" or self.A_log.dtype != torch.float32:
        return "a_log_dtype_or_device"
    if self.dt_bias.device.type != "npu" or self.dt_bias.dtype != torch.bfloat16:
        return "dt_bias_dtype_or_device"
    if list(self.A_log.shape) != [VALUE_HEADS] or list(self.dt_bias.shape) != [VALUE_HEADS]:
        return "gating_parameter_shape"
    state_indices = metadata.non_spec_state_indices_tensor
    if state_indices is None or state_indices.device.type != "npu" or state_indices.dtype != torch.int32:
        return "state_indices_dtype_or_device"
    if state_indices.numel() != num_tokens:
        return "state_indices_shape"
    decode_metadata = metadata.non_spec_decode_metadata
    if decode_metadata is None or decode_metadata.causal_conv1d is None:
        return "missing_decode_metadata"
    actual_seq_lengths = decode_metadata.actual_seq_lengths
    if actual_seq_lengths is None or actual_seq_lengths.device.type != "npu":
        return "actual_seq_lengths_device"
    if actual_seq_lengths.dtype != torch.int32 or actual_seq_lengths.numel() != num_tokens + 1:
        return "actual_seq_lengths_shape_or_dtype"
    return None


def register() -> None:
    """Install the monkeypatch only when the explicit opt-in is enabled."""
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
            f"candidate library identity changed: {library_sha256}; expected {EXPECTED_LIBRARY_SHA256}"
        )

    from vllm_ascend.utils import enable_custom_op

    if not enable_custom_op():
        raise RuntimeError("vLLM-Ascend custom operators are unavailable")
    torch.ops.load_library(str(library))
    schema = str(torch.ops.qwen36_gdn.decode_core.default._schema)
    if schema != EXPECTED_SCHEMA:
        raise RuntimeError(f"candidate schema changed: {schema}")

    import vllm_ascend.ops.gdn as gdn
    from vllm.model_executor.layers.fla.ops.l2norm import l2norm_fwd

    source = Path(gdn.__file__).resolve()
    source_sha256 = _sha256(source)
    if source_sha256 != EXPECTED_GDN_SHA256:
        raise RuntimeError(
            f"vLLM-Ascend GDN source changed: {source_sha256}; re-audit required"
        )

    cls = gdn.AscendGatedDeltaNetAttention
    if getattr(cls, "_qwen36_decode_core_patch_version", None) == PATCH_VERSION:
        return
    if hasattr(cls, "_qwen36_decode_core_original_forward_core"):
        raise RuntimeError("another Qwen3.6 GDN decode-core patch is already installed")

    original = cls._forward_core

    def patched_forward_core(
        self: Any,
        mixed_qkv: Any,
        b: Any,
        a: Any,
        core_attn_out: Any,
    ) -> Any:
        forward_context = gdn.get_forward_context()
        metadata_map = forward_context.attn_metadata
        if metadata_map is None:
            return _fallback(original, "profile_run", self, mixed_qkv, b, a, core_attn_out)
        if not isinstance(metadata_map, dict) or self.prefix not in metadata_map:
            return _fallback(original, "metadata_map", self, mixed_qkv, b, a, core_attn_out)
        metadata = metadata_map[self.prefix]
        if not isinstance(metadata, gdn.GDNAttentionMetadata):
            return _fallback(original, "metadata_type", self, mixed_qkv, b, a, core_attn_out)
        reason = _eligibility_reason(torch, self, metadata, mixed_qkv, b, a, core_attn_out)
        if reason is not None:
            return _fallback(original, reason, self, mixed_qkv, b, a, core_attn_out)

        num_tokens = int(metadata.num_actual_tokens)
        packed = mixed_qkv[:num_tokens]
        a_decode = a[:num_tokens]
        b_decode = b[:num_tokens]
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
            query, key, value = torch.split(
                post_conv,
                [4 * HEAD_DIM, 4 * HEAD_DIM, VALUE_HEADS * HEAD_DIM],
                dim=-1,
            )
            query = l2norm_fwd(
                query.reshape(1, num_tokens, 4, HEAD_DIM).contiguous()
            ).squeeze(0)
            key = l2norm_fwd(
                key.reshape(1, num_tokens, 4, HEAD_DIM).contiguous()
            ).squeeze(0)
            value = value.reshape(
                num_tokens, VALUE_HEADS, HEAD_DIM
            ).contiguous()
            result = torch.ops.qwen36_gdn.decode_core(
                query,
                key,
                value,
                self.A_log,
                a_decode,
                b_decode,
                self.dt_bias,
                self.kv_cache[1],
                metadata.non_spec_decode_metadata.actual_seq_lengths,
                metadata.non_spec_state_indices_tensor,
            )
            core_attn_out[:num_tokens].copy_(result)
        except BaseException:
            _audit(
                "candidate_dispatch_failed",
                prefix=self.prefix,
                num_tokens=num_tokens,
                library_sha256=library_sha256,
            )
            raise

        _audit_once(
            "candidate_dispatch",
            str(self.prefix),
            prefix=self.prefix,
            num_tokens=num_tokens,
            library_sha256=library_sha256,
        )
        return None

    cls._qwen36_decode_core_original_forward_core = original
    cls._forward_core = patched_forward_core
    cls._qwen36_decode_core_patch_version = PATCH_VERSION
    _audit(
        "plugin_installed",
        library=str(library),
        library_sha256=library_sha256,
        source=str(source),
        source_sha256=source_sha256,
        schema=schema,
    )
    LOGGER.warning(
        "Installed Qwen3.6 GDN decode-core plugin %s with library %s",
        PATCH_VERSION,
        library,
    )

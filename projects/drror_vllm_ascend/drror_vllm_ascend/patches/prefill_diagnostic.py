"""Opt-in production-length finite-value tracing for the Ascend GDN prefill."""

from __future__ import annotations

import contextvars
import functools
import inspect
import math
import threading

from ..diagnostics import emit_evidence
from ..envs import DrrqrConfig

SCHEMA = "drrqr-prefill-finite-trace/v1"
_PREFILL_TRACE_LIMIT = 16
_MIXED_TRACE_LIMIT = 64
_STAGE_ORDER = (
    "raw.q",
    "raw.k",
    "raw.v",
    "raw.g",
    "raw.beta",
    "raw.initial_state",
    "normalized.q",
    "normalized.k",
    "chunk.output",
    "chunk.final_state",
    "gdn.output",
)
_MIXED_STAGE_ORDER = (
    "core.mixed_qkv",
    "core.b",
    "core.a",
    "state.conv.before",
    "state.ssm.before",
    "core.output",
    "state.conv.after",
    "state.ssm.after",
)


def tensor_stats(tensor) -> dict:
    """Return JSON-safe full-tensor finite counts and a scale-safe RMS."""
    values = tensor.detach().float()
    finite = values.isfinite()
    finite_count = int(finite.sum().item())
    total = int(values.numel())
    nonfinite_count = total - finite_count
    nan_count = int(values.isnan().sum().item())
    inf_count = int(values.isinf().sum().item())
    safe = values.where(finite, values.new_zeros(()))
    max_abs = float(safe.abs().max().item()) if total else 0.0
    if finite_count and max_abs:
        scaled = safe / max_abs
        rms = float((scaled.square().sum() / finite_count).sqrt().item()) * max_abs
    else:
        rms = 0.0
    if not math.isfinite(max_abs) or not math.isfinite(rms):
        raise RuntimeError("DRRQR: diagnostic produced a non-JSON numeric statistic")
    return {
        "shape": list(tensor.shape),
        "dtype": str(tensor.dtype),
        "numel": total,
        "finite_count": finite_count,
        "nonfinite_count": nonfinite_count,
        "nan_count": nan_count,
        "inf_count": inf_count,
        "max_abs": max_abs,
        "rms": rms,
    }


def _first_nonfinite(stats: dict[str, dict]) -> str | None:
    order = _MIXED_STAGE_ORDER if "core.output" in stats else _STAGE_ORDER
    for name in order:
        item = stats.get(name)
        if item is not None and item["nonfinite_count"]:
            return name
    return None


def _storage_identity(tensor) -> dict:
    return {
        "data_ptr": int(tensor.untyped_storage().data_ptr()),
        "storage_offset": int(tensor.storage_offset()),
        "shape": list(tensor.shape),
        "stride": list(tensor.stride()),
        "dtype": str(tensor.dtype),
    }


def _indices(value) -> list[int]:
    if value is None:
        return []
    return [int(item) for item in value.detach().reshape(-1).cpu().tolist()]


def install_prefill_diagnostic(gdn_cls, gdn_module, chunk_module, config: DrrqrConfig) -> None:
    """Trace one exact production token count without changing tensor values."""
    if not config.prefill_diagnostic:
        return
    identity = (config.plan_path, config.plan_sha256, config.prefill_diagnostic_tokens)
    original_core = gdn_cls._forward_core
    if getattr(original_core, "_drror_prefill_diagnostic_config", None) is not None:
        if original_core._drror_prefill_diagnostic_config != identity:
            raise RuntimeError("DRRQR: prefill diagnostic already bound to another identity")
        return

    original_public = gdn_module.chunk_gated_delta_rule
    original_inner = chunk_module.chunk_gated_delta_rule_fwd
    public_signature = inspect.signature(original_public)
    inner_signature = inspect.signature(original_inner)
    active = contextvars.ContextVar("drrqr_prefill_diagnostic", default=None)
    lock = threading.Lock()
    prefill_counts: dict[str, int] = {}
    mixed_counts: dict[str, int] = {}
    mixed_armed = False
    stopped_after_nonfinite = False

    def record(observation: dict, prefix: str, tensor) -> None:
        if prefix not in observation["stats"]:
            observation["stats"][prefix] = tensor_stats(tensor)

    @functools.wraps(original_public)
    def public(*args, **kwargs):
        observation = active.get()
        if observation is None:
            return original_public(*args, **kwargs)
        bound = public_signature.bind(*args, **kwargs)
        bound.apply_defaults()
        values = bound.arguments
        for name in ("q", "k", "v", "g", "beta", "initial_state"):
            tensor = values.get(name)
            if tensor is not None:
                record(observation, "raw." + name, tensor)
        return original_public(*args, **kwargs)

    @functools.wraps(original_inner)
    def inner(*args, **kwargs):
        observation = active.get()
        if observation is None:
            return original_inner(*args, **kwargs)
        bound = inner_signature.bind(*args, **kwargs)
        bound.apply_defaults()
        values = bound.arguments
        record(observation, "normalized.q", values["q"])
        record(observation, "normalized.k", values["k"])
        result = original_inner(*args, **kwargs)
        record(observation, "chunk.output", result[1])
        record(observation, "chunk.final_state", result[3])
        return result

    @functools.wraps(original_core)
    def core(self, mixed_qkv, b, a, core_attn_out):
        nonlocal mixed_armed, stopped_after_nonfinite
        metadata = getattr(gdn_module.get_forward_context(), "attn_metadata", None)
        candidate = metadata.get(self.prefix) if isinstance(metadata, dict) else metadata
        prefix = str(self.prefix)
        num_prefills = int(getattr(candidate, "num_prefills", 0) or 0)
        num_decodes = int(getattr(candidate, "num_decodes", 0) or 0)
        num_decode_tokens = int(getattr(candidate, "num_decode_tokens", 0) or 0)
        num_actual_tokens = int(getattr(candidate, "num_actual_tokens", 0) or 0)
        prefill_tokens = max(0, num_actual_tokens - num_decode_tokens)
        long_prefill = (
            candidate is not None
            and num_prefills > 0
            and prefill_tokens == config.prefill_diagnostic_tokens
        )
        if long_prefill:
            mixed_armed = True
        prefill_call_index = prefill_counts.get(prefix, 0)
        mixed_call_index = mixed_counts.get(prefix, 0)
        prefill_eligible = (
            not stopped_after_nonfinite
            and long_prefill
            and prefill_call_index < _PREFILL_TRACE_LIMIT
            and getattr(candidate, "spec_sequence_masks", None) is None
        )
        mixed_eligible = (
            not stopped_after_nonfinite
            and mixed_armed
            and candidate is not None
            and (num_prefills > 0 or num_decodes > 0)
            and mixed_call_index < _MIXED_TRACE_LIMIT
            and getattr(candidate, "spec_sequence_masks", None) is None
        )
        if not prefill_eligible and not mixed_eligible:
            return original_core(self, mixed_qkv, b, a, core_attn_out)

        prefill_observation = {"stats": {}}
        token = active.set(prefill_observation) if prefill_eligible else None
        prefill_indices = _indices(getattr(candidate, "prefill_state_indices", None))
        non_spec_indices = _indices(
            getattr(candidate, "non_spec_state_indices_tensor", None)
        )
        decode_indices = non_spec_indices[:num_decodes]
        selected_indices = sorted(set(prefill_indices + decode_indices))
        cache = getattr(self, "kv_cache", None)
        conv_state = cache[0] if cache is not None and len(cache) > 0 else None
        ssm_state = cache[1] if cache is not None and len(cache) > 1 else None
        state_limit = int(ssm_state.shape[0]) if ssm_state is not None else 0
        valid_indices = [
            index for index in selected_indices if 0 <= index < state_limit
        ]
        invalid_indices = [
            index for index in selected_indices if index not in valid_indices
        ]
        mixed_stats = {}
        if mixed_eligible:
            for name, tensor in (
                ("core.mixed_qkv", mixed_qkv),
                ("core.b", b),
                ("core.a", a),
            ):
                if tensor is not None:
                    mixed_stats[name] = tensor_stats(
                        tensor[:num_actual_tokens]
                    )
            if valid_indices:
                if conv_state is not None:
                    mixed_stats["state.conv.before"] = tensor_stats(
                        conv_state[valid_indices]
                    )
                if ssm_state is not None:
                    mixed_stats["state.ssm.before"] = tensor_stats(
                        ssm_state[valid_indices]
                    )
        try:
            result = original_core(self, mixed_qkv, b, a, core_attn_out)
            if prefill_eligible:
                record(
                    prefill_observation,
                    "gdn.output",
                    core_attn_out[:num_actual_tokens],
                )
        finally:
            if token is not None:
                active.reset(token)
        if mixed_eligible:
            mixed_stats["core.output"] = tensor_stats(
                core_attn_out[:num_actual_tokens]
            )
            if valid_indices:
                if conv_state is not None:
                    mixed_stats["state.conv.after"] = tensor_stats(
                        conv_state[valid_indices]
                    )
                if ssm_state is not None:
                    mixed_stats["state.ssm.after"] = tensor_stats(
                        ssm_state[valid_indices]
                    )
        prefill_first = (
            _first_nonfinite(prefill_observation["stats"])
            if prefill_eligible
            else None
        )
        mixed_first = _first_nonfinite(mixed_stats) if mixed_eligible else None
        with lock:
            if prefill_eligible:
                prefill_counts[prefix] = prefill_call_index + 1
            if mixed_eligible:
                mixed_counts[prefix] = mixed_call_index + 1
            if prefill_first is not None or mixed_first is not None:
                stopped_after_nonfinite = True
        phase = (
            "mixed"
            if num_prefills > 0 and num_decodes > 0
            else ("prefill" if num_prefills > 0 else "decode")
        )
        if prefill_eligible:
            emit_evidence(
                config,
                "prefill_finite_trace",
                component="gdn-diagnostic",
                diagnostic_schema=SCHEMA,
                plan_sha256=config.plan_sha256,
                prefix=prefix,
                phase=phase,
                call_index=prefill_call_index,
                token_count=prefill_tokens,
                first_nonfinite_stage=prefill_first,
                all_observed_finite=prefill_first is None,
                stats=prefill_observation["stats"],
                arithmetic_changed=False,
            )
        if mixed_eligible:
            emit_evidence(
                config,
                "mixed_state_finite_trace",
                component="gdn-diagnostic",
                diagnostic_schema="drrqr-mixed-state-finite-trace/v1",
                plan_sha256=config.plan_sha256,
                prefix=prefix,
                phase=phase,
                call_index=mixed_call_index,
                num_prefills=num_prefills,
                num_decodes=num_decodes,
                num_decode_tokens=num_decode_tokens,
                num_actual_tokens=num_actual_tokens,
                prefill_tokens=prefill_tokens,
                prefill_state_indices=prefill_indices,
                decode_state_indices=decode_indices,
                selected_state_indices=selected_indices,
                invalid_state_indices=invalid_indices,
                selected_indices_unique=(
                    len(prefill_indices + decode_indices)
                    == len(set(prefill_indices + decode_indices))
                ),
                prefill_decode_index_overlap=sorted(
                    set(prefill_indices).intersection(decode_indices)
                ),
                conv_storage=(
                    _storage_identity(conv_state)
                    if conv_state is not None
                    else None
                ),
                ssm_storage=(
                    _storage_identity(ssm_state)
                    if ssm_state is not None
                    else None
                ),
                first_nonfinite_stage=mixed_first,
                all_observed_finite=mixed_first is None,
                stats=mixed_stats,
                arithmetic_changed=False,
            )
        return result

    public._drror_prefill_diagnostic_config = identity
    inner._drror_prefill_diagnostic_config = identity
    core._drror_prefill_diagnostic_config = identity
    core._drror_core_original = getattr(original_core, "_drror_core_original", original_core)
    gdn_module.chunk_gated_delta_rule = public
    chunk_module.chunk_gated_delta_rule_fwd = inner
    gdn_cls._forward_core = core

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
    for name in _STAGE_ORDER:
        item = stats.get(name)
        if item is not None and item["nonfinite_count"]:
            return name
    return None


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
    completed_prefixes: set[str] = set()
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
        nonlocal stopped_after_nonfinite
        metadata = getattr(gdn_module.get_forward_context(), "attn_metadata", None)
        candidate = metadata.get(self.prefix) if isinstance(metadata, dict) else metadata
        prefix = str(self.prefix)
        eligible = (
            not stopped_after_nonfinite
            and prefix not in completed_prefixes
            and candidate is not None
            and getattr(candidate, "num_prefills", 0) > 0
            and getattr(candidate, "num_decodes", 0) == 0
            and getattr(candidate, "spec_sequence_masks", None) is None
            and getattr(candidate, "num_actual_tokens", None) == config.prefill_diagnostic_tokens
        )
        if not eligible:
            return original_core(self, mixed_qkv, b, a, core_attn_out)
        observation = {"stats": {}}
        token = active.set(observation)
        try:
            result = original_core(self, mixed_qkv, b, a, core_attn_out)
            record(
                observation,
                "gdn.output",
                core_attn_out[: config.prefill_diagnostic_tokens],
            )
        finally:
            active.reset(token)
        first = _first_nonfinite(observation["stats"])
        with lock:
            completed_prefixes.add(prefix)
            if first is not None:
                stopped_after_nonfinite = True
        emit_evidence(
            config,
            "prefill_finite_trace",
            component="gdn-diagnostic",
            diagnostic_schema=SCHEMA,
            plan_sha256=config.plan_sha256,
            prefix=prefix,
            token_count=config.prefill_diagnostic_tokens,
            first_nonfinite_stage=first,
            all_observed_finite=first is None,
            stats=observation["stats"],
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

"""Read-only Tail-Replay recurrence oracle on the live Ascend GDN path."""

from __future__ import annotations

from contextvars import ContextVar
from functools import wraps
import hashlib
import inspect
from pathlib import Path
import sys
import threading
from types import ModuleType
from typing import Any, Callable

import torch

from .config import TailReplayConfig
from .diagnostics import emit_event
from .import_hook import PostImportFinder


_TARGET_MODULE = "vllm_ascend.ops.gdn"
_CURRENT_LAYER_PREFIX: ContextVar[str | None] = ContextVar(
    "mst_tail_replay_current_layer_prefix", default=None
)
_SEEN_LAYER_PREFIXES: set[str] = set()
_SEEN_LOCK = threading.Lock()
_CHUNK_ARGUMENTS = (
    "q",
    "k",
    "v",
    "g",
    "beta",
    "scale",
    "initial_state",
    "output_final_state",
    "cu_seqlens",
    "prebuilt_meta",
    "head_first",
    "use_qk_l2norm_in_kernel",
)


def _distributed_rank() -> int | None:
    try:
        import torch.distributed as dist

        if dist.is_available() and dist.is_initialized():
            return int(dist.get_rank())
    except Exception:
        return None
    return None


def _source_identity(callable_obj: Callable) -> tuple[str | None, str | None]:
    try:
        path = Path(inspect.getsourcefile(callable_obj) or "").resolve()
        return str(path), hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, TypeError, ValueError):
        return None, None


def _argument(name: str, args: tuple[Any, ...], kwargs: dict[str, Any], default=None):
    if name in kwargs:
        return kwargs[name]
    index = _CHUNK_ARGUMENTS.index(name)
    return args[index] if index < len(args) else default


def _tail_tokens(total_tokens: int, ratio: float) -> int:
    return max(1, min(total_tokens, int(total_tokens * ratio + 0.999999999)))


def _state_metrics(reference: torch.Tensor, candidate: torch.Tensor) -> dict[str, Any]:
    reference_fp32 = reference.float()
    candidate_fp32 = candidate.float()
    difference = candidate_fp32 - reference_fp32
    reference_flat = reference_fp32.reshape(-1)
    candidate_flat = candidate_fp32.reshape(-1)
    difference_flat = difference.reshape(-1)
    reference_norm = torch.linalg.vector_norm(reference_flat)
    candidate_norm = torch.linalg.vector_norm(candidate_flat)
    difference_norm = torch.linalg.vector_norm(difference_flat)
    tiny = torch.finfo(torch.float32).tiny
    cosine = torch.dot(reference_flat, candidate_flat) / (
        reference_norm.clamp_min(tiny) * candidate_norm.clamp_min(tiny)
    )

    head_reference = reference_fp32.reshape(-1, *reference_fp32.shape[-2:])
    head_candidate = candidate_fp32.reshape(-1, *candidate_fp32.shape[-2:])
    head_difference = head_candidate - head_reference
    head_reference_norm = torch.linalg.vector_norm(head_reference, dim=(-2, -1))
    head_candidate_norm = torch.linalg.vector_norm(head_candidate, dim=(-2, -1))
    head_difference_norm = torch.linalg.vector_norm(head_difference, dim=(-2, -1))
    head_relative_l2 = head_difference_norm / head_reference_norm.clamp_min(tiny)
    head_cosine = (head_reference * head_candidate).sum(dim=(-2, -1)) / (
        head_reference_norm.clamp_min(tiny) * head_candidate_norm.clamp_min(tiny)
    )

    return {
        "all_finite": bool(
            torch.isfinite(reference_fp32).all().item()
            and torch.isfinite(candidate_fp32).all().item()
        ),
        "reference_norm": float(reference_norm.item()),
        "candidate_norm": float(candidate_norm.item()),
        "difference_norm": float(difference_norm.item()),
        "relative_l2": float((difference_norm / reference_norm.clamp_min(tiny)).item()),
        "cosine": float(cosine.item()),
        "max_abs_error": float(difference.abs().max().item()),
        "head_relative_l2_min": float(head_relative_l2.min().item()),
        "head_relative_l2_mean": float(head_relative_l2.mean().item()),
        "head_relative_l2_max": float(head_relative_l2.max().item()),
        "head_cosine_min": float(head_cosine.min().item()),
        "head_cosine_mean": float(head_cosine.mean().item()),
        "head_cosine_max": float(head_cosine.max().item()),
    }


def _invoke_chunk(
    original: Callable,
    values: dict[str, Any],
    *,
    start: int,
    end: int,
    initial_state: torch.Tensor,
):
    cu_seqlens = values["cu_seqlens"].new_tensor([0, end - start])
    return original(
        q=values["q"][:, start:end],
        k=values["k"][:, start:end],
        v=values["v"][:, start:end],
        g=values["g"][:, start:end],
        beta=values["beta"][:, start:end],
        scale=values["scale"],
        initial_state=initial_state,
        output_final_state=True,
        cu_seqlens=cu_seqlens,
        prebuilt_meta=None,
        head_first=False,
        use_qk_l2norm_in_kernel=values["use_qk_l2norm_in_kernel"],
    )


def _make_chunk_wrapper(original: Callable, config: TailReplayConfig) -> Callable:
    @wraps(original)
    def chunk_with_recurrence_oracle(*args, **kwargs):
        result = original(*args, **kwargs)
        layer_prefix = _CURRENT_LAYER_PREFIX.get()
        if layer_prefix is None:
            return result

        values = {
            name: _argument(name, args, kwargs)
            for name in _CHUNK_ARGUMENTS
        }
        q = values["q"]
        initial_state = values["initial_state"]
        cu_seqlens = values["cu_seqlens"]
        full_state = result[1] if isinstance(result, tuple) and len(result) == 2 else None
        if (
            q is None
            or initial_state is None
            or cu_seqlens is None
            or full_state is None
            or bool(values["head_first"])
            or not bool(values["output_final_state"])
            or q.ndim != 4
            or int(q.shape[0]) != 1
            or int(cu_seqlens.shape[0]) != 2
        ):
            return result

        total_tokens = int(q.shape[1])
        if not (config.min_prefill_tokens <= total_tokens <= config.max_prefill_tokens):
            return result
        with _SEEN_LOCK:
            if layer_prefix in _SEEN_LAYER_PREFIXES:
                return result
            _SEEN_LAYER_PREFIXES.add(layer_prefix)

        initial_max_abs = float(initial_state.float().abs().max().item())
        if initial_max_abs != 0.0:
            emit_event(
                "recurrence_oracle_rejected_nonzero_initial_state",
                layer_prefix=layer_prefix,
                distributed_rank=_distributed_rank(),
                total_tokens=total_tokens,
                initial_state_max_abs=initial_max_abs,
            )
            raise RuntimeError(
                "Tail-Replay recurrence oracle requires a fresh zero-state prefill"
            )

        zero_state = torch.zeros_like(initial_state)
        for ratio in config.replay_ratios:
            tail_tokens = _tail_tokens(total_tokens, ratio)
            head_tokens = total_tokens - tail_tokens
            _, zero_tail_state = _invoke_chunk(
                original,
                values,
                start=head_tokens,
                end=total_tokens,
                initial_state=zero_state.clone(),
            )
            if head_tokens:
                _, head_state = _invoke_chunk(
                    original,
                    values,
                    start=0,
                    end=head_tokens,
                    initial_state=zero_state.clone(),
                )
                _, exact_split_state = _invoke_chunk(
                    original,
                    values,
                    start=head_tokens,
                    end=total_tokens,
                    initial_state=head_state,
                )
            else:
                exact_split_state = zero_tail_state

            exact_metrics = _state_metrics(full_state, exact_split_state)
            replay_metrics = _state_metrics(full_state, zero_tail_state)
            passed = bool(
                exact_metrics["all_finite"]
                and replay_metrics["all_finite"]
                and exact_metrics["relative_l2"]
                <= config.exact_split_relative_l2_max
            )
            emit_event(
                "recurrence_oracle_result",
                layer_prefix=layer_prefix,
                distributed_rank=_distributed_rank(),
                total_tokens=total_tokens,
                replay_ratio=ratio,
                tail_tokens=tail_tokens,
                head_tokens=head_tokens,
                q_shape=list(q.shape),
                state_shape=list(full_state.shape),
                state_dtype=str(full_state.dtype),
                state_device=str(full_state.device),
                initial_state_max_abs=initial_max_abs,
                exact_split=exact_metrics,
                zero_tail=replay_metrics,
                exact_split_relative_l2_max=config.exact_split_relative_l2_max,
                harness_passed=passed,
            )
            if not passed:
                raise RuntimeError(
                    "Tail-Replay recurrence oracle exact-split harness failed"
                )
        return result

    return chunk_with_recurrence_oracle


def _make_core_wrapper(original: Callable) -> Callable:
    @wraps(original)
    def core_with_layer_identity(self, *args, **kwargs):
        token = _CURRENT_LAYER_PREFIX.set(str(getattr(self, "prefix", "unknown")))
        try:
            return original(self, *args, **kwargs)
        finally:
            _CURRENT_LAYER_PREFIX.reset(token)

    core_with_layer_identity._mst_tail_replay_context_wrapper = True
    return core_with_layer_identity


def _apply_gdn_patch(module: ModuleType, config: TailReplayConfig) -> None:
    original_chunk = getattr(module, "chunk_gated_delta_rule", None)
    ascend_class = getattr(module, "AscendGatedDeltaNetAttention", None)
    if original_chunk is None or ascend_class is None:
        if config.require_runtime_hooks:
            raise RuntimeError("Tail-Replay canary could not resolve the Ascend GDN path")
        return
    if getattr(original_chunk, "_mst_tail_replay_oracle_wrapper", False):
        return

    original_core = ascend_class._forward_core
    core_wrapper = _make_core_wrapper(original_core)
    ascend_class._forward_core = core_wrapper
    try:
        from vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn import (
            QwenGatedDeltaNetAttention,
        )

        QwenGatedDeltaNetAttention._forward_core = core_wrapper
    except ImportError:
        if config.require_runtime_hooks:
            raise

    chunk_wrapper = _make_chunk_wrapper(original_chunk, config)
    chunk_wrapper._mst_tail_replay_oracle_wrapper = True
    module.chunk_gated_delta_rule = chunk_wrapper
    core_path, core_hash = _source_identity(original_core)
    chunk_path, chunk_hash = _source_identity(original_chunk)
    emit_event(
        "recurrence_oracle_patch_installed",
        target_module=module.__name__,
        distributed_rank=_distributed_rank(),
        core_source_path=core_path,
        core_source_sha256=core_hash,
        chunk_source_path=chunk_path,
        chunk_source_sha256=chunk_hash,
        replay_ratios=list(config.replay_ratios),
    )


def install_runtime_patch(config: TailReplayConfig) -> None:
    module = sys.modules.get(_TARGET_MODULE)
    if module is not None:
        _apply_gdn_patch(module, config)
        return

    def callback(imported_module: ModuleType) -> None:
        _apply_gdn_patch(imported_module, config)

    PostImportFinder(_TARGET_MODULE, callback).install()
    emit_event("recurrence_oracle_patch_deferred", target_module=_TARGET_MODULE)

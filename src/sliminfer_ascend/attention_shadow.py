"""Identity-preserving SlimInfer selection hook for the final Ascend Qwen path."""

from __future__ import annotations

from contextlib import contextmanager
from functools import wraps
from hashlib import sha256
import inspect
import json
from pathlib import Path
import re
import sys
import threading
from types import ModuleType
from typing import Any, Iterator

from .config import SlimInferConfig
from .diagnostics import emit_event
from .import_hook import PostImportFinder
from .planner import selection_digest, select_active_blocks
from .shadow_score import remap_compact_block_scores, semantic_block_scores


_TARGET_MODULE = "vllm_ascend.patch.worker.patch_qwen3_5"
_TARGET_CLASS = "Qwen3NextAttention"
_LAYER_PATTERN = re.compile(r"(?:^|\.)layers\.(\d+)\.")
_BOUNDARY_KEEP_TOKENS = {19: 12 * 1024, 39: 6 * 1024, 59: 4 * 1024}
_BLOCK_SIZE = 64
_UNIT_SIZE = 8
_QUERY_WINDOW = 4
_state = threading.local()
_serial_lock = threading.Lock()
_next_serial = 0


def _source_identity(obj: Any) -> tuple[str | None, str | None]:
    path = inspect.getsourcefile(obj)
    if path is None:
        return None, None
    try:
        digest = sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        digest = None
    return path, digest


@contextmanager
def selection_forward_scope(
    *, prompt_tokens: int | None = None, semantic_compact: bool = False
) -> Iterator[int]:
    """Create request-local staged-selection state around one model forward."""

    global _next_serial
    if getattr(_state, "value", None) is not None:
        raise RuntimeError("nested SlimInfer selection forward scopes are unsupported")
    with _serial_lock:
        serial = _next_serial
        _next_serial += 1
    if semantic_compact and prompt_tokens is None:
        raise ValueError("semantic compact scope requires prompt_tokens")
    active = {}
    if prompt_tokens is not None:
        active[0] = tuple(range((prompt_tokens + _BLOCK_SIZE - 1) // _BLOCK_SIZE))
    _state.value = {
        "serial": serial,
        "active": active,
        "plans": {},
        "selection_inputs": {},
        "prompt_tokens": prompt_tokens,
        "semantic_compact": semantic_compact,
    }
    try:
        yield serial
    finally:
        del _state.value


def _selection_state() -> dict[str, Any]:
    value = getattr(_state, "value", None)
    if value is None:
        raise RuntimeError("SlimInfer attention hook ran outside the model forward scope")
    return value


def semantic_layer_transition(
    layer_index: int | None,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    state = _selection_state()
    if not state["semantic_compact"]:
        raise RuntimeError("semantic layer transition requires compact mode")
    if layer_index is None:
        active = state["active"].get(0)
        if active is None:
            raise RuntimeError("semantic active set is unavailable")
        return active, active
    before = state["selection_inputs"].get(0, {}).get(layer_index)
    selected = state["plans"].get(0, {}).get(layer_index)
    if before is None or selected is None:
        raise RuntimeError(f"semantic selection missing after layer {layer_index}")
    return before, selected


def _layer_index(layer_name: str) -> int:
    match = _LAYER_PATTERN.search(layer_name)
    if match is None:
        raise ValueError(f"cannot extract layer index from {layer_name!r}")
    return int(match.group(1))


def _to_int_list(value: Any) -> list[int]:
    if isinstance(value, (list, tuple)):
        return [int(item) for item in value]
    detach = getattr(value, "detach", None)
    if callable(detach):
        value = detach()
    cpu = getattr(value, "cpu", None)
    if callable(cpu):
        value = cpu()
    tolist = getattr(value, "tolist", None)
    if not callable(tolist):
        raise TypeError("sequence lengths must be a sequence or tensor-like value")
    rendered = tolist()
    if not isinstance(rendered, list):
        raise TypeError("sequence lengths must render as a list")
    return [int(item) for item in rendered]


def _whole_prompt_start_locs(metadata: Any, token_count: int) -> tuple[int, ...] | None:
    num_prefills = int(getattr(metadata, "num_prefills", 0))
    num_decodes = int(getattr(metadata, "num_decode_tokens", 0))
    if num_prefills == 0:
        return None
    if num_decodes != 0:
        raise RuntimeError("selection-shadow requires a prefill-only forward")
    state_name = getattr(getattr(metadata, "attn_state", None), "name", None)
    if state_name != "PrefillNoCache":
        raise RuntimeError(
            "selection-shadow requires whole-prompt PrefillNoCache attention"
        )
    starts = _to_int_list(getattr(metadata, "query_start_loc", None))
    if len(starts) != num_prefills + 1:
        raise RuntimeError("invalid query_start_loc size for selection-shadow")
    if starts[0] != 0 or starts[-1] != token_count:
        raise RuntimeError("selection-shadow rejects padded or partial prompt rows")
    if any(left >= right for left, right in zip(starts, starts[1:])):
        raise RuntimeError("query_start_loc must be strictly increasing")
    if int(getattr(metadata, "num_actual_tokens", token_count)) != token_count:
        raise RuntimeError("metadata token count differs from live Q/K rows")
    return tuple(starts)


def _attention_metadata(layer_name: str) -> Any | None:
    from vllm.forward_context import get_forward_context

    mapping = get_forward_context().attn_metadata
    if mapping is None:
        return None
    if not isinstance(mapping, dict):
        raise RuntimeError(
            "attention metadata must be a per-layer mapping when present"
        )
    if layer_name not in mapping:
        raise RuntimeError(f"missing attention metadata for {layer_name}")
    return mapping[layer_name]


def _projected_qkv(value: Any) -> Any:
    """Extract the live fused projection tensor from the Ascend layer output."""

    if isinstance(value, tuple):
        if not value:
            raise RuntimeError("QKV projection returned an empty tuple")
        value = value[0]
    if getattr(value, "shape", None) is None:
        raise RuntimeError("QKV projection did not return a tensor-like value")
    return value


def _split_projected_qk(self: Any, positions: Any, qkv: Any) -> tuple[Any, Any]:
    """Apply the real Ascend split/norm/RoPE op to an already projected QKV."""

    import torch

    cos_sin = self.rotary_emb.cos_sin_cache[positions]
    if cos_sin.device != qkv.device:
        cos_sin = cos_sin.to(qkv.device)
    if cos_sin.dtype != qkv.dtype:
        cos_sin = cos_sin.to(qkv.dtype)
    q, k, _, _ = torch.ops.vllm.triton_split_qkv_rmsnorm_mrope(
        qkv=qkv,
        q_weight=1.0 + self.q_norm.weight,
        k_weight=1.0 + self.k_norm.weight,
        cos_sin=cos_sin,
        num_q_heads=self.num_heads,
        num_kv_heads=self.num_kv_heads,
        head_size=self.head_dim,
        eps=self.config.rms_norm_eps,
        mrope_section=self.rotary_emb.mrope_section,
        is_interleaved=self.rotary_emb.mrope_interleaved,
        rope_dim=self.rotary_emb.rotary_dim,
        has_gate=self.attn_output_gate,
    )
    return (
        q.reshape(-1, self.num_heads, self.head_dim),
        k.reshape(-1, self.num_kv_heads, self.head_dim),
    )


def _tp_reduce_sum(value: Any) -> Any:
    from vllm.distributed.parallel_state import get_tp_group

    group = get_tp_group()
    reduced = group.all_reduce(value)
    return group.broadcast(reduced, src=0)


def _distributed_rank() -> int | None:
    try:
        import torch.distributed as dist

        if dist.is_available() and dist.is_initialized():
            return int(dist.get_rank())
    except Exception:
        return None
    return None


def _score_digest(block_scores: dict[int, float]) -> str:
    payload = [[int(block), float(score)] for block, score in sorted(block_scores.items())]
    encoded = json.dumps(payload, separators=(",", ":"), allow_nan=False).encode()
    return sha256(encoded).hexdigest()


def _request_token_counts(
    state: dict[str, Any], current_active_tokens: int
) -> tuple[int, int]:
    if current_active_tokens <= 0:
        raise ValueError("current active token count must be positive")
    if state["semantic_compact"]:
        original_tokens = state.get("prompt_tokens")
        if not isinstance(original_tokens, int) or original_tokens <= 0:
            raise RuntimeError("semantic prompt token identity is unavailable")
    else:
        original_tokens = current_active_tokens
    return original_tokens, current_active_tokens


def _record_selection(
    self: Any,
    *,
    positions: Any,
    projected_qkv: Any,
    start_locs: tuple[int, ...],
    config: SlimInferConfig,
    layer_index: int,
    layer_name: str,
) -> None:
    q, k = _split_projected_qk(self, positions, projected_qkv)
    results = semantic_block_scores(
        q,
        k,
        start_locs,
        block_size=_BLOCK_SIZE,
        unit_size=_UNIT_SIZE,
        query_window=_QUERY_WINDOW,
        reduce_sum=_tp_reduce_sum,
        global_query_heads=int(self.total_num_heads),
    )
    state = _selection_state()
    for result in results:
        request_index = result.request_index
        if state["semantic_compact"] and request_index != 0:
            raise RuntimeError("semantic-prefill currently supports one request")
        if state["semantic_compact"]:
            active = state["active"].get(request_index)
            if active is None:
                raise RuntimeError("semantic active block identity is missing")
            block_scores = remap_compact_block_scores(
                result.block_scores,
                active,
                prompt_tokens=int(state["prompt_tokens"]),
                compact_tokens=result.token_end - result.token_start,
                block_size=_BLOCK_SIZE,
            )
        else:
            block_scores = result.block_scores
        all_blocks = tuple(sorted(block_scores))
        active = state["active"].get(request_index, all_blocks)
        selected = select_active_blocks(
            active,
            block_scores,
            keep_tokens=_BOUNDARY_KEEP_TOKENS[layer_index],
            block_size=_BLOCK_SIZE,
            keep_sink=True,
            keep_recent=True,
        )
        state["active"][request_index] = selected
        plan = state["plans"].setdefault(request_index, {})
        state["selection_inputs"].setdefault(request_index, {})[layer_index] = active
        plan[layer_index] = selected
        digest = selection_digest(
            f"forward-{state['serial']}-request-{request_index}", plan
        )
        request_tokens, active_tokens = _request_token_counts(
            state, result.token_end - result.token_start
        )
        emit_event(
            "selection_shadow_layer",
            component="attention",
            mode=config.mode,
            distributed_rank=_distributed_rank(),
            forward_serial=state["serial"],
            request_index=request_index,
            layer_index=layer_index,
            layer_name=layer_name,
            request_tokens=request_tokens,
            active_tokens=active_tokens,
            input_block_count=len(active),
            selected_block_count=len(selected),
            selected_blocks=list(selected),
            score_sha256=_score_digest(block_scores),
            selection_sha256=digest,
            local_query_heads=int(self.num_heads),
            local_kv_heads=int(self.num_kv_heads),
            global_query_heads=int(self.total_num_heads),
            block_size=_BLOCK_SIZE,
            unit_size=_UNIT_SIZE,
            query_window=_QUERY_WINDOW,
            keep_sink_block=True,
            keep_recent_block=True,
            tp_score_canonicalization="sum-all-reduce-then-rank0-broadcast",
            score_block_identity=(
                "compact-remapped-to-absolute"
                if state["semantic_compact"]
                else "dense-original"
            ),
            compact_block_remap_applied=bool(state["semantic_compact"]),
            staged_compact_semantics_proven=bool(state["semantic_compact"]),
            duplicate_projection_for_diagnostics=False,
            projection_reused_from_live_forward=True,
            runtime_mutation=False,
        )


def _patch_attention_class(cls: type, config: SlimInferConfig) -> bool:
    if cls.__dict__.get("_mst_sliminfer_selection_shadow_installed", False):
        return False
    original_forward = cls.forward
    source_path, source_digest = _source_identity(original_forward)

    @wraps(original_forward)
    def forward_with_selection_shadow(
        self, positions: Any, output: Any, hidden_states: Any
    ):
        layer_name = getattr(getattr(self, "attn", None), "layer_name", None)
        if not isinstance(layer_name, str):
            raise RuntimeError("SlimInfer requires the live attention layer_name")
        layer_index = _layer_index(layer_name)
        if layer_index not in _BOUNDARY_KEEP_TOKENS:
            return original_forward(self, positions, output, hidden_states)

        metadata = _attention_metadata(layer_name)
        if metadata is None:
            scope = getattr(_state, "value", None)
            emit_event(
                "selection_shadow_metadata_unavailable",
                component="attention",
                mode=config.mode,
                distributed_rank=_distributed_rank(),
                forward_serial=(
                    scope.get("serial") if isinstance(scope, dict) else None
                ),
                layer_index=layer_index,
                layer_name=layer_name,
                reason="forward-context-attn-metadata-is-none",
                runtime_mutation=False,
            )
            return original_forward(self, positions, output, hidden_states)

        start_locs = _whole_prompt_start_locs(metadata, int(hidden_states.shape[0]))
        if start_locs is None:
            return original_forward(self, positions, output, hidden_states)

        observed_projection_count = 0

        def reuse_live_projection(_module: Any, _args: Any, value: Any) -> None:
            nonlocal observed_projection_count
            observed_projection_count += 1
            if observed_projection_count != 1:
                raise RuntimeError("attention forward executed QKV projection more than once")
            _record_selection(
                self,
                positions=positions,
                projected_qkv=_projected_qkv(value),
                start_locs=start_locs,
                config=config,
                layer_index=layer_index,
                layer_name=layer_name,
            )

        handle = self.qkv_proj.register_forward_hook(reuse_live_projection)
        try:
            result = original_forward(self, positions, output, hidden_states)
        finally:
            handle.remove()
        if observed_projection_count != 1:
            raise RuntimeError("attention forward did not execute the expected QKV projection")
        return result

    cls.forward = forward_with_selection_shadow
    cls._mst_sliminfer_selection_shadow_installed = True
    emit_event(
        "selection_shadow_patch_installed",
        component="attention",
        mode=config.mode,
        target_module=cls.__module__,
        target_class=cls.__name__,
        original_forward_module=original_forward.__module__,
        original_forward_qualname=original_forward.__qualname__,
        source_path=source_path,
        source_sha256=source_digest,
        distributed_rank=_distributed_rank(),
        boundaries=sorted(_BOUNDARY_KEEP_TOKENS),
    )
    return True


def _apply_attention_patch(module: ModuleType, config: SlimInferConfig) -> None:
    cls = getattr(module, _TARGET_CLASS, None)
    if cls is None:
        if config.require_runtime_hooks:
            raise RuntimeError(
                f"SlimInfer attention target {_TARGET_MODULE}.{_TARGET_CLASS} was not found"
            )
        return
    _patch_attention_class(cls, config)


def install_attention_patch(config: SlimInferConfig) -> None:
    """Patch only after vLLM-Ascend installs its final Qwen3.5 forward."""

    module = sys.modules.get(_TARGET_MODULE)
    if module is not None:
        _apply_attention_patch(module, config)
        return

    def callback(imported_module: ModuleType) -> None:
        _apply_attention_patch(imported_module, config)

    PostImportFinder(_TARGET_MODULE, callback).install()
    emit_event(
        "selection_shadow_patch_deferred",
        component="attention",
        mode=config.mode,
        target_module=_TARGET_MODULE,
        target_class=_TARGET_CLASS,
    )

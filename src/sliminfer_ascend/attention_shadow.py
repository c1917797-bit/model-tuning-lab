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
from .shadow_score import semantic_block_scores


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
def selection_forward_scope() -> Iterator[int]:
    """Create request-local staged-selection state around one model forward."""

    global _next_serial
    if getattr(_state, "value", None) is not None:
        raise RuntimeError("nested SlimInfer selection forward scopes are unsupported")
    with _serial_lock:
        serial = _next_serial
        _next_serial += 1
    _state.value = {"serial": serial, "active": {}, "plans": {}}
    try:
        yield serial
    finally:
        del _state.value


def _selection_state() -> dict[str, Any]:
    value = getattr(_state, "value", None)
    if value is None:
        raise RuntimeError("SlimInfer attention hook ran outside the model forward scope")
    return value


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


def _attention_metadata(layer_name: str) -> Any:
    from vllm.forward_context import get_forward_context

    mapping = get_forward_context().attn_metadata
    if not isinstance(mapping, dict) or layer_name not in mapping:
        raise RuntimeError(f"missing attention metadata for {layer_name}")
    return mapping[layer_name]


def _compute_live_qk(self: Any, positions: Any, hidden_states: Any) -> tuple[Any, Any]:
    """Duplicate the final Ascend projection/split only for a shadow canary."""

    import torch

    qkv, _ = self.qkv_proj(hidden_states)
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
    from vllm.distributed.communication_op import tensor_model_parallel_all_reduce

    return tensor_model_parallel_all_reduce(value)


def _score_digest(block_scores: dict[int, float]) -> str:
    payload = [[int(block), float(score)] for block, score in sorted(block_scores.items())]
    encoded = json.dumps(payload, separators=(",", ":"), allow_nan=False).encode()
    return sha256(encoded).hexdigest()


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
        if layer_index in _BOUNDARY_KEEP_TOKENS:
            metadata = _attention_metadata(layer_name)
            start_locs = _whole_prompt_start_locs(metadata, int(hidden_states.shape[0]))
            if start_locs is not None:
                q, k = _compute_live_qk(self, positions, hidden_states)
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
                    all_blocks = tuple(sorted(result.block_scores))
                    active = state["active"].get(request_index, all_blocks)
                    selected = select_active_blocks(
                        active,
                        result.block_scores,
                        keep_tokens=_BOUNDARY_KEEP_TOKENS[layer_index],
                        block_size=_BLOCK_SIZE,
                    )
                    state["active"][request_index] = selected
                    plan = state["plans"].setdefault(request_index, {})
                    plan[layer_index] = selected
                    digest = selection_digest(
                        f"forward-{state['serial']}-request-{request_index}", plan
                    )
                    emit_event(
                        "selection_shadow_layer",
                        component="attention",
                        mode=config.mode,
                        forward_serial=state["serial"],
                        request_index=request_index,
                        layer_index=layer_index,
                        layer_name=layer_name,
                        request_tokens=result.token_end - result.token_start,
                        input_block_count=len(active),
                        selected_block_count=len(selected),
                        selected_blocks=list(selected),
                        score_sha256=_score_digest(result.block_scores),
                        selection_sha256=digest,
                        local_query_heads=int(self.num_heads),
                        local_kv_heads=int(self.num_kv_heads),
                        global_query_heads=int(self.total_num_heads),
                        block_size=_BLOCK_SIZE,
                        unit_size=_UNIT_SIZE,
                        query_window=_QUERY_WINDOW,
                        duplicate_projection_for_diagnostics=True,
                        runtime_mutation=False,
                    )
        return original_forward(self, positions, output, hidden_states)

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

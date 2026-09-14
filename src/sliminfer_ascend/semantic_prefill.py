"""Fail-closed single-request SlimInfer semantic-prefill canary.

This is deliberately narrower than a serving implementation: it supports one
whole-prompt eager prefill and returns the first-token hidden state in the
original flattened shape. Decode, chunked prefill, PP and continuous batching
remain rejected until their layer-local cache contracts are implemented.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import fields, is_dataclass, replace
import os
from types import SimpleNamespace
from typing import Any, Iterator, Mapping, Sequence

from .diagnostics import emit_event
from .stream_contract import RequestPruningState


def _cache_pruned_fused_residual_blocks(
    hidden_states: Any,
    residual: Any,
    *,
    current_active_blocks: Sequence[int],
    selected_active_blocks: Sequence[int],
    prompt_tokens: int,
    layer_index: int,
) -> dict[tuple[int, int], Any]:
    """Cache complete pruned blocks from the vLLM fused-residual stream."""

    import torch

    from .request_runtime import HiddenStateBlock

    if residual is None:
        raise RuntimeError("semantic-stream requires the fused residual tensor")
    selected = set(int(block) for block in selected_active_blocks)
    current_state = RequestPruningState(
        prompt_tokens=prompt_tokens,
        active_blocks=tuple(int(block) for block in current_active_blocks),
    )
    row_by_token = {
        token_id: row
        for row, token_id in enumerate(current_state.active_prompt_token_ids)
    }
    result: dict[tuple[int, int], HiddenStateBlock] = {}
    for block in current_state.active_blocks:
        if block in selected:
            continue
        start = block * current_state.pruning_block_size
        stop = min(start + current_state.pruning_block_size, prompt_tokens)
        rows = tuple(row_by_token[token_id] for token_id in range(start, stop))
        index = torch.tensor(rows, dtype=torch.long, device=hidden_states.device)
        result[(layer_index, block)] = HiddenStateBlock(
            hidden_states=torch.index_select(hidden_states, 0, index).detach(),
            residual=torch.index_select(residual, 0, index).detach(),
        )
    return result


def position_token_axis(positions: Any) -> int:
    """Return the token axis for supported text and multimodal RoPE layouts."""

    ndim = int(getattr(positions, "ndim", -1))
    if ndim == 1:
        return 0
    if ndim == 2:
        return 1
    raise RuntimeError(
        "semantic-prefill requires positions shaped [tokens] or [channels, tokens]"
    )


def compact_positions(
    positions: Any,
    index: Any,
    *,
    expected_tokens: int,
) -> Any:
    """Gather token positions while preserving any leading RoPE channels."""

    axis = position_token_axis(positions)
    if int(positions.shape[axis]) != int(expected_tokens):
        raise RuntimeError("position token count differs from hidden-state rows")
    return positions.index_select(axis, index)


def compact_gather_indices(
    current_active_blocks: Sequence[int],
    selected_active_blocks: Sequence[int],
    *,
    prompt_tokens: int,
    block_size: int = 64,
) -> tuple[int, ...]:
    """Return row indices that compact current whole blocks to a subset."""

    current = RequestPruningState(
        prompt_tokens=prompt_tokens,
        active_blocks=tuple(int(block) for block in current_active_blocks),
        pruning_block_size=block_size,
    )
    selected = RequestPruningState(
        prompt_tokens=prompt_tokens,
        active_blocks=tuple(int(block) for block in selected_active_blocks),
        pruning_block_size=block_size,
    )
    if not set(selected.active_blocks).issubset(current.active_blocks):
        raise ValueError("selected blocks must be a subset of current active blocks")
    relative = {
        absolute_id: row
        for row, absolute_id in enumerate(current.active_prompt_token_ids)
    }
    return tuple(relative[token] for token in selected.active_prompt_token_ids)


def _new_int_tensor(reference: Any, values: Sequence[int]) -> Any:
    new_tensor = getattr(reference, "new_tensor", None)
    if not callable(new_tensor):
        raise TypeError("metadata sequence tensor does not support new_tensor")
    return new_tensor(tuple(int(value) for value in values))


def _replace_preserving_dynamic(value: Any, **changes: Any) -> Any:
    if not is_dataclass(value):
        raise TypeError("attention metadata must be a dataclass instance")
    replaced = replace(value, **changes)
    declared = {field.name for field in fields(value)}
    for name, item in vars(value).items():
        if name not in declared and name not in changes:
            setattr(replaced, name, item)
    return replaced


def _validate_single_prefill_counts(metadata: Any, compact_tokens: int) -> None:
    if compact_tokens <= 0:
        raise ValueError("compact_tokens must be positive")
    if int(getattr(metadata, "num_prefills", -1)) != 1:
        raise RuntimeError("semantic-prefill requires exactly one prefill request")
    if int(getattr(metadata, "num_decodes", 0)) != 0:
        raise RuntimeError("semantic-prefill rejects mixed decode batches")
    if int(getattr(metadata, "num_decode_tokens", 0)) != 0:
        raise RuntimeError("semantic-prefill rejects decode tokens")
    original_tokens = int(getattr(metadata, "num_actual_tokens", -1))
    if compact_tokens > original_tokens:
        raise RuntimeError("compact token count exceeds original metadata rows")


def compact_full_attention_metadata(metadata: Any, compact_tokens: int) -> Any:
    """Clone one full-attention prefill metadata object for compact rows."""

    _validate_single_prefill_counts(metadata, compact_tokens)
    state_name = getattr(getattr(metadata, "attn_state", None), "name", None)
    if state_name != "PrefillNoCache":
        raise RuntimeError("semantic-prefill requires full-attention PrefillNoCache")
    query_start_loc = _new_int_tensor(metadata.query_start_loc, (0, compact_tokens))
    seq_lens = _new_int_tensor(metadata.seq_lens, (compact_tokens,))
    seq_lens_cpu = _new_int_tensor(metadata.seq_lens_cpu, (compact_tokens,))
    if metadata.slot_mapping is None or int(metadata.slot_mapping.shape[0]) < compact_tokens:
        raise RuntimeError("full-attention slot mapping is shorter than compact rows")
    return _replace_preserving_dynamic(
        metadata,
        num_actual_tokens_pcp_padded=compact_tokens,
        num_actual_tokens=compact_tokens,
        num_prefills=1,
        num_decodes=0,
        num_decode_tokens=0,
        seq_lens=seq_lens,
        seq_lens_cpu=seq_lens_cpu,
        seq_lens_list=[compact_tokens],
        actual_seq_lengths_q=[compact_tokens],
        query_start_loc=query_start_loc,
        max_query_len=compact_tokens,
        slot_mapping=metadata.slot_mapping[:compact_tokens],
    )


def compact_gdn_metadata(
    metadata: Any,
    compact_tokens: int,
    *,
    linear_num_value_heads: int,
    tp_size: int,
) -> Any:
    """Clone one Ascend GDN metadata object and rebuild compact chunk state."""

    _validate_single_prefill_counts(metadata, compact_tokens)
    if linear_num_value_heads <= 0 or tp_size <= 0:
        raise ValueError("GDN head count and TP size must be positive")
    start_reference = getattr(metadata, "non_spec_query_start_loc", None)
    if start_reference is None:
        raise RuntimeError("GDN metadata lacks non-spec prefill boundaries")
    query_start_loc = _new_int_tensor(start_reference, (0, compact_tokens))

    from vllm_ascend.ops.gdn_attn_builder import (
        _build_non_spec_chunked_prefill_metadata,
    )

    builder = SimpleNamespace(
        vllm_config=SimpleNamespace(
            model_config=SimpleNamespace(
                hf_text_config=SimpleNamespace(
                    linear_num_value_heads=linear_num_value_heads
                )
            ),
            parallel_config=SimpleNamespace(tensor_parallel_size=tp_size),
        )
    )
    chunk = _build_non_spec_chunked_prefill_metadata(
        builder, query_start_loc.cpu(), query_start_loc.device
    )
    nested = getattr(metadata, "non_spec_prefill_metadata", None)
    if nested is None:
        raise RuntimeError("GDN metadata lacks native non-spec prefill metadata")
    causal = getattr(nested, "causal_conv1d", None)
    if causal is None:
        raise RuntimeError("GDN metadata lacks native causal-conv metadata")
    compact_causal = _replace_preserving_dynamic(
        causal, query_start_loc=query_start_loc
    )
    compact_nested = _replace_preserving_dynamic(
        nested, causal_conv1d=compact_causal, chunk=chunk
    )
    result = _replace_preserving_dynamic(
        metadata,
        num_prefills=1,
        num_prefill_tokens=compact_tokens,
        num_decodes=0,
        num_decode_tokens=0,
        num_spec_decodes=0,
        num_spec_decode_tokens=0,
        num_actual_tokens=compact_tokens,
        non_spec_query_start_loc=query_start_loc,
        prefill_query_start_loc=query_start_loc,
        chunk_indices=chunk.chunk_indices_chunk64,
        chunk_offsets=chunk.chunk_offsets_chunk64,
    )
    result.non_spec_prefill_metadata = compact_nested
    return result


def compact_layer_metadata(
    metadata: Any,
    compact_tokens: int,
    *,
    layer: Any,
) -> Any:
    if hasattr(metadata, "attn_state"):
        return compact_full_attention_metadata(metadata, compact_tokens)
    linear_attn = getattr(layer, "linear_attn", None)
    if linear_attn is None:
        raise TypeError("unrecognized attention metadata type")
    return compact_gdn_metadata(
        metadata,
        compact_tokens,
        linear_num_value_heads=int(linear_attn.num_v_heads),
        tp_size=int(linear_attn.tp_size),
    )


def layer_metadata_key(layer: Any) -> str:
    if getattr(layer, "layer_type", None) == "full_attention":
        name = getattr(getattr(getattr(layer, "self_attn", None), "attn", None), "layer_name", None)
    elif getattr(layer, "layer_type", None) == "linear_attention":
        name = getattr(getattr(layer, "linear_attn", None), "prefix", None)
    else:
        raise RuntimeError("semantic-prefill found an unsupported layer type")
    if not isinstance(name, str) or not name:
        raise RuntimeError("semantic-prefill cannot resolve the live layer metadata key")
    return name


def validate_model_contract(model: Any) -> None:
    """Reject model features whose output/cache contracts are not implemented."""

    layers = getattr(model, "layers", None)
    if layers is None:
        raise RuntimeError("semantic-prefill model has no decoder layers")
    layer_count = len(layers)
    if (
        int(getattr(model, "start_layer", -1)) != 0
        or int(getattr(model, "end_layer", -1)) != layer_count
    ):
        raise RuntimeError(
            "semantic-prefill requires the complete decoder layer range on one PP rank"
        )
    if tuple(getattr(model, "aux_hidden_state_layers", ())):
        raise RuntimeError(
            "semantic-prefill rejects auxiliary hidden-state consumers"
        )


@contextmanager
def swapped_layer_metadata(
    mapping: dict[str, Any], layer_name: str, replacement: Any
) -> Iterator[None]:
    if layer_name not in mapping:
        raise RuntimeError(f"missing attention metadata for {layer_name}")
    original = mapping[layer_name]
    mapping[layer_name] = replacement
    try:
        yield
    finally:
        mapping[layer_name] = original


def semantic_prefill_forward(
    model: Any,
    input_ids: Any,
    positions: Any,
    intermediate_tensors: Any = None,
    inputs_embeds: Any = None,
) -> Any:
    """Run the bounded whole-prompt semantic prefill canary."""

    import torch
    from vllm.distributed.parallel_state import get_pp_group
    from vllm.forward_context import get_forward_context

    pp_group = get_pp_group()
    if not pp_group.is_first_rank or not pp_group.is_last_rank:
        raise RuntimeError("semantic-prefill currently rejects pipeline parallelism")
    if intermediate_tensors is not None:
        raise RuntimeError("semantic-prefill rejects intermediate PP tensors")
    validate_model_contract(model)
    if inputs_embeds is None:
        if input_ids is None:
            raise ValueError("semantic-prefill requires input_ids or inputs_embeds")
        hidden_states = model.embed_input_ids(input_ids)
    elif input_ids is not None:
        raise ValueError("semantic-prefill accepts only one input representation")
    else:
        hidden_states = inputs_embeds
    if hidden_states.ndim != 2:
        raise RuntimeError("semantic-prefill requires flattened 2D hidden states")
    prompt_tokens = int(hidden_states.shape[0])
    position_axis = position_token_axis(positions)
    if int(positions.shape[position_axis]) != prompt_tokens:
        raise RuntimeError("position token count differs from hidden-state rows")

    context = get_forward_context()
    mapping = context.attn_metadata
    if not isinstance(mapping, dict):
        raise RuntimeError("semantic-prefill requires per-layer attention metadata")

    from .attention_shadow import (
        _BOUNDARY_KEEP_TOKENS,
        _distributed_rank,
        semantic_layer_transition,
        selection_forward_scope,
    )

    original_rows = prompt_tokens
    residual = None
    current_positions = positions
    persistent_state = None
    if os.environ.get("MST_SLIMINFER_MODE") == "semantic-stream":
        from .request_runtime import (
            PersistentRequestState,
            current_runner_forward_identity,
        )

        runner_identity = current_runner_forward_identity()
        if len(runner_identity.requests) != 1:
            raise RuntimeError("semantic-stream requires exactly one runner request")
        request_identity = runner_identity.requests[0]
        if request_identity.num_computed_tokens != 0:
            raise RuntimeError("semantic-stream decode is not implemented yet")
        if request_identity.prompt_tokens != prompt_tokens:
            raise RuntimeError("runner and model prompt lengths differ")
        persistent_state = PersistentRequestState(
            req_id=request_identity.req_id,
            prompt_tokens=prompt_tokens,
            block_tables=request_identity.block_tables,
            kv_block_sizes=request_identity.kv_block_sizes,
        )
    with selection_forward_scope(
        prompt_tokens=prompt_tokens, semantic_compact=True
    ):
        for layer_index, layer in enumerate(model.layers):
            layer_name = layer_metadata_key(layer)
            metadata = mapping.get(layer_name)
            if metadata is None:
                raise RuntimeError(f"missing attention metadata for {layer_name}")
            if int(hidden_states.shape[0]) == original_rows:
                replacement = metadata
            else:
                replacement = compact_layer_metadata(
                    metadata, int(hidden_states.shape[0]), layer=layer
                )
            with swapped_layer_metadata(mapping, layer_name, replacement):
                hidden_states, residual = layer(
                    positions=current_positions,
                    hidden_states=hidden_states,
                    residual=residual,
                )
            if layer_index in _BOUNDARY_KEEP_TOKENS:
                before, selected = semantic_layer_transition(layer_index)
                if persistent_state is not None:
                    persistent_state.hidden_state_cache.update(
                        _cache_pruned_fused_residual_blocks(
                            hidden_states,
                            residual,
                            current_active_blocks=before,
                            selected_active_blocks=selected,
                            prompt_tokens=prompt_tokens,
                            layer_index=layer_index,
                        )
                    )
                    persistent_state.active_blocks_after_layer[layer_index] = selected
                gather = compact_gather_indices(
                    before,
                    selected,
                    prompt_tokens=prompt_tokens,
                )
                index = torch.tensor(
                    gather, dtype=torch.long, device=hidden_states.device
                )
                input_rows = int(hidden_states.shape[0])
                current_positions = compact_positions(
                    current_positions,
                    index,
                    expected_tokens=input_rows,
                )
                hidden_states = torch.index_select(hidden_states, 0, index)
                residual = torch.index_select(residual, 0, index)
                emit_event(
                    "semantic_prefill_compacted",
                    component="model",
                    mode="semantic-prefill",
                    layer_index=layer_index,
                    distributed_rank=_distributed_rank(),
                    input_rows=input_rows,
                    output_rows=int(hidden_states.shape[0]),
                    runtime_mutation=True,
                )

        hidden_states, _ = model.norm(hidden_states, residual)
        active_blocks = semantic_layer_transition(None)[1]
        active_state = RequestPruningState(
            prompt_tokens=prompt_tokens,
            active_blocks=active_blocks,
        )
        active_ids = active_state.active_prompt_token_ids
        if prompt_tokens - 1 not in active_ids:
            raise RuntimeError("final input token was pruned before logits")
        restored = torch.zeros(
            (original_rows, int(hidden_states.shape[1])),
            dtype=hidden_states.dtype,
            device=hidden_states.device,
        )
        scatter = torch.tensor(active_ids, dtype=torch.long, device=hidden_states.device)
        restored.index_copy_(0, scatter, hidden_states)
        emit_event(
            "semantic_prefill_complete",
            component="model",
            mode="semantic-prefill",
            distributed_rank=_distributed_rank(),
            original_rows=original_rows,
            final_active_rows=len(active_ids),
            output_rows=int(restored.shape[0]),
            runtime_mutation=True,
        )
        if persistent_state is not None:
            from .request_runtime import put_request_state

            put_request_state(persistent_state)
            emit_event(
                "semantic_stream_prefill_state_committed",
                component="model",
                mode="semantic-stream",
                distributed_rank=_distributed_rank(),
                prompt_tokens=prompt_tokens,
                boundary_layers=sorted(persistent_state.active_blocks_after_layer),
                hidden_state_block_count=len(persistent_state.hidden_state_cache),
                kv_group_count=len(persistent_state.block_tables),
                runtime_mutation=True,
            )
        return restored

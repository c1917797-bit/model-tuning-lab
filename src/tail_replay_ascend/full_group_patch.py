"""Non-mutating full-GDN-group Tail-Replay oracle for Qwen3.6 on Ascend."""

from __future__ import annotations

from contextvars import ContextVar
from functools import wraps
import inspect
from pathlib import Path
import hashlib
import sys
import threading
from types import ModuleType
from typing import Any, Callable

from .config import TailReplayConfig
from .diagnostics import emit_event
from .import_hook import PostImportFinder


_TARGET_MODULE = "vllm.model_executor.models.qwen3_5"
_ASCEND_PATCH_MODULE = "vllm_ascend.patch.worker.patch_qwen3_5"
_ACTIVE_CAPTURE: ContextVar[dict[str, Any] | None] = ContextVar(
    "mst_tail_replay_group_capture", default=None
)
_ACTIVE_DECODE_CAPTURE: ContextVar[dict[str, Any] | None] = ContextVar(
    "mst_tail_replay_group_decode_capture", default=None
)
_SEEN_GROUPS: set[tuple[int | None, int]] = set()
_SEEN_DECODE_GROUPS: set[tuple[int | None, int]] = set()
_REPLAY_STATES: dict[tuple[float, int], tuple[Any, Any]] = {}
_SEEN_LOCK = threading.Lock()


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
        path = Path(inspect.getsourcefile(inspect.unwrap(callable_obj)) or "").resolve()
        return str(path), hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, TypeError, ValueError):
        return None, None


def _tail_tokens(total_tokens: int, ratio: float) -> int:
    return max(1, min(total_tokens, int(total_tokens * ratio + 0.999999999)))


def _tensor_metrics(reference, candidate) -> dict[str, Any]:
    import torch

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
    return {
        "all_finite": bool(
            torch.isfinite(reference_fp32).all().item()
            and torch.isfinite(candidate_fp32).all().item()
        ),
        "reference_norm": float(reference_norm.item()),
        "candidate_norm": float(candidate_norm.item()),
        "difference_norm": float(difference_norm.item()),
        "relative_l2": float(
            (difference_norm / reference_norm.clamp_min(tiny)).item()
        ),
        "cosine": float(cosine.item()),
        "max_abs_error": float(difference.abs().max().item()),
    }


def _materialize(hidden_states, residual):
    return hidden_states if residual is None else hidden_states + residual


def _is_group_start(layer_idx: int, layer_type: str) -> bool:
    return layer_type == "linear_attention" and layer_idx % 4 == 0


def _is_group_end(layer_idx: int, layer_type: str) -> bool:
    return layer_type == "linear_attention" and layer_idx % 4 == 2


def _prefill_metadata(attn):
    from vllm.forward_context import get_forward_context

    all_metadata = get_forward_context().attn_metadata
    if not isinstance(all_metadata, dict):
        raise RuntimeError("Tail-Replay group oracle requires per-layer metadata")
    metadata = all_metadata.get(attn.prefix)
    if metadata is None:
        raise RuntimeError(
            f"Tail-Replay group oracle could not resolve metadata for {attn.prefix}"
        )
    if int(metadata.num_prefills) != 1 or int(metadata.num_decodes) != 0:
        raise RuntimeError(
            "Tail-Replay group oracle requires one fresh prefill and no decodes"
        )
    has_initial = metadata.prefill_has_initial_state
    if has_initial is None or bool(has_initial.any().item()):
        raise RuntimeError(
            "Tail-Replay group oracle requires zero initial recurrent state"
        )
    return metadata


def _decode_metadata(attn):
    from vllm.forward_context import get_forward_context

    all_metadata = get_forward_context().attn_metadata
    if not isinstance(all_metadata, dict):
        raise RuntimeError("Tail-Replay decode oracle requires per-layer metadata")
    metadata = all_metadata.get(attn.prefix)
    if metadata is None:
        raise RuntimeError(
            f"Tail-Replay decode oracle could not resolve metadata for {attn.prefix}"
        )
    if (
        int(metadata.num_prefills) != 0
        or int(metadata.num_decodes) != 1
        or int(metadata.num_decode_tokens) != 1
    ):
        raise RuntimeError(
            "Tail-Replay decode oracle requires one non-spec decode token"
        )
    if metadata.non_spec_decode_metadata is None:
        raise RuntimeError(
            "Tail-Replay decode oracle requires non-spec decode metadata"
        )
    return metadata


def _build_chunk_metadata(q, v, token_count: int):
    import torch
    from vllm_ascend.ops.gdn_attn_builder import GDNChunkedPrefillMetadata
    from vllm_ascend.ops.triton.fla.utils import (
        prepare_chunk_indices,
        prepare_chunk_offsets,
        prepare_final_chunk_indices,
        prepare_update_chunk_offsets,
    )

    chunk_size = 64
    solve_tril_large_block_size = 608 * 2
    cumsum_working_set = 2**18
    value_heads = int(v.shape[2])
    cumsum_chunks = max(1, cumsum_working_set // (value_heads * chunk_size))
    cumsum_chunk_size = (
        1 if cumsum_chunks <= 1 else 1 << (cumsum_chunks - 1).bit_length()
    )
    cu_seqlens_cpu = torch.tensor([0, token_count], dtype=torch.int32)
    chunk_indices = prepare_chunk_indices(cu_seqlens_cpu, chunk_size)
    chunk_offsets = prepare_chunk_offsets(cu_seqlens_cpu, chunk_size)
    update_chunk_offsets = prepare_update_chunk_offsets(
        cu_seqlens_cpu, chunk_size
    )
    final_chunk_indices = prepare_final_chunk_indices(
        cu_seqlens_cpu, chunk_size
    )
    large_block_indices = prepare_chunk_indices(
        cu_seqlens_cpu, solve_tril_large_block_size
    )
    cumsum_block_indices = prepare_chunk_indices(
        cu_seqlens_cpu, cumsum_chunk_size
    )
    device = q.device
    return GDNChunkedPrefillMetadata(
        cu_seqlens_host=(0, token_count),
        chunk_indices_chunk64_host=tuple(
            chunk_indices.to(torch.int64).reshape(-1).tolist()
        ),
        chunk_indices_chunk64=chunk_indices.to(device=device, non_blocking=True),
        chunk_offsets_chunk64=chunk_offsets.to(device=device, non_blocking=True),
        update_chunk_offsets_chunk64=update_chunk_offsets.to(
            device=device, non_blocking=True
        ),
        final_chunk_indices_chunk64=final_chunk_indices.to(
            device=device, non_blocking=True
        ),
        chunk_indices_large_block=large_block_indices.to(
            device=device, non_blocking=True
        ),
        block_indices_cumsum=cumsum_block_indices.to(
            device=device, non_blocking=True
        ),
        num_decodes=int(token_count == 1),
        cu_seqlens_kern=None,
        keep_meta=None,
    )


def _split_qkvzba(attn, hidden_states):
    if hasattr(attn, "in_proj_qkv"):
        mixed_qkv, _ = attn.in_proj_qkv(hidden_states)
        ba, _ = attn.in_proj_ba(hidden_states)
        z, _ = attn.in_proj_z(hidden_states)
        z = z.reshape(z.size(0), -1, attn.head_v_dim)
        b, a = (
            attn._split_ba_for_tp(ba)
            if hasattr(attn, "_split_ba_for_tp")
            else ba.chunk(2, dim=-1)
        )
        return mixed_qkv, z, b.contiguous(), a.contiguous()

    mixed_qkvz, _ = attn.in_proj_qkvz(hidden_states)
    if bool(getattr(attn, "gqa_interleaved_layout", False)):
        projected_ba, _ = attn.in_proj_ba(hidden_states)
        from vllm_ascend.ops.triton.fla.fused_qkvzba_split_reshape import (
            fused_qkvzba_split_reshape_cat,
        )
        from vllm.triton_utils import triton

        return fused_qkvzba_split_reshape_cat(
            mixed_qkvz,
            projected_ba,
            triton.cdiv(attn.num_k_heads, attn.tp_size),
            triton.cdiv(attn.num_v_heads, attn.tp_size),
            attn.head_k_dim,
            attn.head_v_dim,
        )

    qkv_size = (attn.key_dim * 2 + attn.value_dim) // attn.tp_size
    z_size = attn.value_dim // attn.tp_size
    mixed_qkv, z = mixed_qkvz.split([qkv_size, z_size], dim=-1)
    z = z.reshape(z.size(0), -1, attn.head_v_dim)
    ba, _ = attn.in_proj_ba(hidden_states)
    b, a = (
        attn._split_ba_for_tp(ba)
        if hasattr(attn, "_split_ba_for_tp")
        else ba.chunk(2, dim=-1)
    )
    return mixed_qkv, z, b.contiguous(), a.contiguous()


def _functional_gdn(attn, hidden_states, metadata):
    import torch
    from vllm.v1.attention.backends.utils import PAD_SLOT_ID
    from vllm_ascend.device.device_op import DeviceOperator
    from vllm_ascend.ops.gdn import chunk_gated_delta_rule

    token_count = int(hidden_states.shape[0])
    mixed_qkv, z, b, a = _split_qkvzba(attn, hidden_states)

    conv_template = metadata.non_spec_prefill_metadata.causal_conv1d
    query_start_loc = conv_template.query_start_loc.new_tensor([0, token_count])
    cache_indices = conv_template.cache_indices[:1].new_zeros((1,))
    if conv_template.initial_state_mode is None:
        initial_state_mode = torch.zeros(
            (1,), dtype=torch.bool, device=hidden_states.device
        )
    else:
        initial_state_mode = conv_template.initial_state_mode[:1].new_zeros((1,))
    conv_state = torch.zeros_like(attn.kv_cache[0][:1])
    conv_weights = attn.conv1d.weight.view(
        attn.conv1d.weight.size(0), attn.conv1d.weight.size(2)
    )
    conv_output = torch.empty_like(mixed_qkv)
    torch.ops._C_ascend.npu_causal_conv1d_custom(
        conv_output,
        mixed_qkv,
        conv_weights.transpose(0, 1),
        conv_state=conv_state,
        bias_opt=attn.conv1d.bias,
        query_start_loc_opt=query_start_loc,
        cache_indices_opt=cache_indices,
        initial_state_mode_opt=initial_state_mode,
        num_accepted_tokens_opt=None,
        activation_mode=1 if attn.activation else 0,
        pad_slot_id=PAD_SLOT_ID,
        run_mode=0,
    )

    query, key, value = attn.rearrange_mixed_qkv(conv_output)
    g, beta = DeviceOperator.fused_gdn_gating(
        attn.A_log, a, b, attn.dt_bias
    )
    initial_state = torch.zeros_like(attn.kv_cache[1][:1]).transpose(
        -1, -2
    ).contiguous()
    chunk_metadata = _build_chunk_metadata(query, value, token_count)
    core_output, final_state = chunk_gated_delta_rule(
        q=query,
        k=key,
        v=value,
        g=g,
        beta=beta,
        initial_state=initial_state,
        output_final_state=True,
        cu_seqlens=query_start_loc,
        prebuilt_meta=chunk_metadata,
        head_first=False,
        use_qk_l2norm_in_kernel=True,
    )
    z_shape = z.shape
    core_output = core_output.reshape(-1, core_output.shape[-1])
    z_flat = z.reshape(-1, z.shape[-1])
    core_output = attn.norm(core_output, z_flat).reshape(z_shape)
    projected, _ = attn.out_proj(core_output.reshape(token_count, -1))
    recurrent_state = final_state.transpose(-1, -2).contiguous()
    return projected, conv_state, recurrent_state


def _functional_decoder_layer(layer, hidden_states, residual, metadata):
    if residual is None:
        next_residual = hidden_states
        normalized = layer.input_layernorm(hidden_states)
    else:
        normalized, next_residual = layer.input_layernorm(
            hidden_states, residual
        )
    attention_output, conv_state, recurrent_state = _functional_gdn(
        layer.linear_attn, normalized, metadata
    )
    if bool(getattr(layer, "layer_scale", False)):
        attention_output = attention_output * (
            layer.attn_layer_scale.to(attention_output.dtype)[0] + 1
        )
    normalized, next_residual = layer.post_attention_layernorm(
        attention_output, next_residual
    )
    output = layer.mlp(normalized)
    if bool(getattr(layer, "layer_scale", False)):
        output = output * (
            layer.ffn_layer_scale.to(output.dtype)[0] + 1
        )
    return output, next_residual, conv_state, recurrent_state


def _functional_gdn_decode(
    attn,
    hidden_states,
    metadata,
    conv_state,
    recurrent_state,
):
    import torch
    from vllm.v1.attention.backends.utils import PAD_SLOT_ID
    from vllm_ascend.device.device_op import DeviceOperator
    from vllm_ascend.ops.triton.fla.l2norm import l2norm_fwd

    mixed_qkv, z, b, a = _split_qkvzba(attn, hidden_states)
    decode_metadata = metadata.non_spec_decode_metadata
    conv_metadata = decode_metadata.causal_conv1d
    local_conv_state = conv_state.clone()
    local_recurrent_state = recurrent_state.clone()
    conv_weights = attn.conv1d.weight.view(
        attn.conv1d.weight.size(0), attn.conv1d.weight.size(2)
    )
    conv_output = torch.empty_like(mixed_qkv)
    local_conv_index = conv_metadata.cache_indices[:1].new_zeros((1,))
    torch.ops._C_ascend.npu_causal_conv1d_custom(
        conv_output,
        mixed_qkv,
        conv_weights.transpose(0, 1),
        conv_state=local_conv_state,
        bias_opt=attn.conv1d.bias,
        query_start_loc_opt=conv_metadata.query_start_loc,
        cache_indices_opt=local_conv_index,
        initial_state_mode_opt=None,
        num_accepted_tokens_opt=None,
        activation_mode=1 if attn.activation else 0,
        pad_slot_id=PAD_SLOT_ID,
        run_mode=1,
    )

    query, key, value = attn.rearrange_mixed_qkv(conv_output)
    g, beta = DeviceOperator.fused_gdn_gating(
        attn.A_log, a, b, attn.dt_bias
    )
    query = l2norm_fwd(query)
    key = l2norm_fwd(key)
    live_state_indices = metadata.non_spec_state_indices_tensor
    if live_state_indices is None or int(live_state_indices.numel()) != 1:
        raise RuntimeError(
            "Tail-Replay decode oracle requires one recurrent state index"
        )
    local_state_index = live_state_indices[:1].new_zeros((1,))
    core_output = torch.ops._C_ascend.npu_recurrent_gated_delta_rule(
        query=query.squeeze(0),
        key=key.squeeze(0),
        value=value.squeeze(0),
        g=g.squeeze(0),
        beta=beta.squeeze(0),
        state=local_recurrent_state,
        scale=key.shape[-1] ** -0.5,
        actual_seq_lengths=decode_metadata.actual_seq_lengths,
        ssm_state_indices=local_state_index,
    ).unsqueeze(0)
    z_shape = z.shape
    core_output = core_output.reshape(-1, core_output.shape[-1])
    z_flat = z.reshape(-1, z.shape[-1])
    core_output = attn.norm(core_output, z_flat).reshape(z_shape)
    projected, _ = attn.out_proj(core_output.reshape(hidden_states.shape[0], -1))
    return projected, local_conv_state, local_recurrent_state


def _functional_decoder_layer_decode(
    layer,
    hidden_states,
    residual,
    metadata,
    conv_state,
    recurrent_state,
):
    if residual is None:
        next_residual = hidden_states
        normalized = layer.input_layernorm(hidden_states)
    else:
        normalized, next_residual = layer.input_layernorm(
            hidden_states, residual
        )
    attention_output, next_conv, next_recurrent = _functional_gdn_decode(
        layer.linear_attn,
        normalized,
        metadata,
        conv_state,
        recurrent_state,
    )
    if bool(getattr(layer, "layer_scale", False)):
        attention_output = attention_output * (
            layer.attn_layer_scale.to(attention_output.dtype)[0] + 1
        )
    normalized, next_residual = layer.post_attention_layernorm(
        attention_output, next_residual
    )
    output = layer.mlp(normalized)
    if bool(getattr(layer, "layer_scale", False)):
        output = output * (
            layer.ffn_layer_scale.to(output.dtype)[0] + 1
        )
    return output, next_residual, next_conv, next_recurrent


def _dense_states(layer, metadata):
    state_indices = metadata.prefill_state_indices
    if state_indices is None or int(state_indices.numel()) != 1:
        raise RuntimeError(
            "Tail-Replay group oracle requires one recurrent cache index"
        )
    state_index = int(state_indices.reshape(-1)[0].item())
    conv_indices = metadata.non_spec_prefill_metadata.causal_conv1d.cache_indices
    if int(conv_indices.numel()) != 1:
        raise RuntimeError(
            "Tail-Replay group oracle requires one convolution cache index"
        )
    conv_index = int(conv_indices.reshape(-1)[0].item())
    return (
        layer.linear_attn.kv_cache[0][conv_index : conv_index + 1].clone(),
        layer.linear_attn.kv_cache[1][state_index : state_index + 1].clone(),
    )


def _run_replay(layers, hidden_states, residual):
    states = []
    current_hidden = hidden_states
    current_residual = residual
    for layer in layers:
        metadata = _prefill_metadata(layer.linear_attn)
        (
            current_hidden,
            current_residual,
            conv_state,
            recurrent_state,
        ) = _functional_decoder_layer(
            layer, current_hidden, current_residual, metadata
        )
        states.append((conv_state, recurrent_state))
    return current_hidden, current_residual, states


def _run_group_oracle(
    *,
    start_layer: int,
    layers: list[Any],
    input_hidden,
    input_residual,
    reference_hidden,
    reference_residual,
    config: TailReplayConfig,
) -> None:
    import torch

    total_tokens = int(input_hidden.shape[0])
    gdn_path, gdn_hash = _source_identity(layers[0].linear_attn.forward)
    emit_event(
        "group_oracle_attempt",
        distributed_rank=_distributed_rank(),
        start_layer=start_layer,
        end_layer=start_layer + 2,
        total_tokens=total_tokens,
        input_hidden_shape=list(input_hidden.shape),
        input_residual_shape=(
            None if input_residual is None else list(input_residual.shape)
        ),
        gdn_forward_source_path=gdn_path,
        gdn_forward_source_sha256=gdn_hash,
        conv_cache_shapes=[
            list(layer.linear_attn.kv_cache[0].shape) for layer in layers
        ],
        recurrent_cache_shapes=[
            list(layer.linear_attn.kv_cache[1].shape) for layer in layers
        ],
    )
    metadata_by_layer = [
        _prefill_metadata(layer.linear_attn) for layer in layers
    ]
    dense_state_snapshots = [
        _dense_states(layer, metadata)
        for layer, metadata in zip(layers, metadata_by_layer)
    ]
    exact_hidden, exact_residual, exact_states = _run_replay(
        layers, input_hidden.clone(),
        None if input_residual is None else input_residual.clone()
    )
    reference_materialized = _materialize(reference_hidden, reference_residual)
    exact_materialized = _materialize(exact_hidden, exact_residual)
    exact_output_metrics = _tensor_metrics(
        reference_materialized, exact_materialized
    )
    exact_state_metrics = []
    for layer, (conv_state, recurrent_state), dense_states in zip(
        layers, exact_states, dense_state_snapshots
    ):
        dense_conv, dense_recurrent = dense_states
        exact_state_metrics.append(
            {
                "layer_idx": int(layer.layer_idx),
                "conv": _tensor_metrics(dense_conv, conv_state),
                "recurrent": _tensor_metrics(dense_recurrent, recurrent_state),
            }
        )
    exact_passed = bool(
        exact_output_metrics["all_finite"]
        and exact_output_metrics["relative_l2"]
        <= config.exact_split_relative_l2_max
        and all(
            item[kind]["all_finite"]
            and item[kind]["relative_l2"]
            <= config.exact_split_relative_l2_max
            for item in exact_state_metrics
            for kind in ("conv", "recurrent")
        )
    )
    emit_event(
        "group_oracle_exact_result",
        distributed_rank=_distributed_rank(),
        start_layer=start_layer,
        end_layer=start_layer + 2,
        total_tokens=total_tokens,
        output=exact_output_metrics,
        states=exact_state_metrics,
        relative_l2_max=config.exact_split_relative_l2_max,
        harness_passed=exact_passed,
    )
    if not exact_passed:
        raise RuntimeError(
            f"Tail-Replay exact full-group harness failed at layer {start_layer}"
        )

    for ratio in config.replay_ratios:
        tail_tokens = _tail_tokens(total_tokens, ratio)
        tail_start = total_tokens - tail_tokens
        emit_event(
            "group_oracle_tail_attempt",
            distributed_rank=_distributed_rank(),
            start_layer=start_layer,
            end_layer=start_layer + 2,
            total_tokens=total_tokens,
            replay_ratio=ratio,
            head_tokens=tail_start,
            tail_tokens=tail_tokens,
        )
        tail_hidden = input_hidden[tail_start:].clone()
        tail_residual = (
            None
            if input_residual is None
            else input_residual[tail_start:].clone()
        )
        replay_hidden, replay_residual, replay_states = _run_replay(
            layers, tail_hidden, tail_residual
        )
        for layer, replay_state in zip(layers, replay_states):
            _REPLAY_STATES[(float(ratio), int(layer.layer_idx))] = (
                replay_state[0].clone(),
                replay_state[1].clone(),
            )
        output_metrics = _tensor_metrics(
            reference_materialized[tail_start:],
            _materialize(replay_hidden, replay_residual),
        )
        state_metrics = []
        for layer, (conv_state, recurrent_state), dense_states in zip(
            layers, replay_states, dense_state_snapshots
        ):
            dense_conv, dense_recurrent = dense_states
            state_metrics.append(
                {
                    "layer_idx": int(layer.layer_idx),
                    "conv": _tensor_metrics(dense_conv, conv_state),
                    "recurrent": _tensor_metrics(
                        dense_recurrent, recurrent_state
                    ),
                }
            )
        emit_event(
            "group_oracle_tail_result",
            distributed_rank=_distributed_rank(),
            start_layer=start_layer,
            end_layer=start_layer + 2,
            total_tokens=total_tokens,
            replay_ratio=ratio,
            head_tokens=tail_start,
            tail_tokens=tail_tokens,
            output=output_metrics,
            states=state_metrics,
        )
    cache_preservation = []
    cache_preserved = True
    for layer, metadata, snapshot in zip(
        layers, metadata_by_layer, dense_state_snapshots
    ):
        current_conv, current_recurrent = _dense_states(layer, metadata)
        conv_equal = bool(torch.equal(current_conv, snapshot[0]))
        recurrent_equal = bool(torch.equal(current_recurrent, snapshot[1]))
        cache_preserved = cache_preserved and conv_equal and recurrent_equal
        cache_preservation.append(
            {
                "layer_idx": int(layer.layer_idx),
                "conv_bitwise_equal": conv_equal,
                "recurrent_bitwise_equal": recurrent_equal,
            }
        )
    emit_event(
        "group_oracle_live_cache_preservation",
        distributed_rank=_distributed_rank(),
        start_layer=start_layer,
        end_layer=start_layer + 2,
        cache_preserved=cache_preserved,
        layers=cache_preservation,
    )
    if not cache_preserved:
        raise RuntimeError(
            f"Tail-Replay group oracle mutated live cache at layer {start_layer}"
        )
    if input_hidden.device.type == "npu":
        torch.npu.synchronize()


def _dense_decode_states(layer, metadata):
    conv_indices = metadata.non_spec_decode_metadata.causal_conv1d.cache_indices
    state_indices = metadata.non_spec_state_indices_tensor
    if conv_indices is None or state_indices is None:
        raise RuntimeError(
            "Tail-Replay decode oracle requires convolution and recurrent indices"
        )
    if int(conv_indices.numel()) != 1 or int(state_indices.numel()) != 1:
        raise RuntimeError(
            "Tail-Replay decode oracle requires one cache index per state kind"
        )
    conv_index = int(conv_indices.reshape(-1)[0].item())
    state_index = int(state_indices.reshape(-1)[0].item())
    return (
        layer.linear_attn.kv_cache[0][conv_index : conv_index + 1].clone(),
        layer.linear_attn.kv_cache[1][state_index : state_index + 1].clone(),
    )


def _run_first_decode_oracle(
    *,
    start_layer: int,
    layers: list[Any],
    input_hidden,
    input_residual,
    reference_hidden,
    reference_residual,
    dense_initial_states,
    config: TailReplayConfig,
) -> None:
    import torch

    reference_materialized = _materialize(reference_hidden, reference_residual)
    metadata_by_layer = [
        _decode_metadata(layer.linear_attn) for layer in layers
    ]
    dense_state_snapshots = [
        _dense_decode_states(layer, metadata)
        for layer, metadata in zip(layers, metadata_by_layer)
    ]
    exact_hidden = input_hidden.clone()
    exact_residual = (
        None if input_residual is None else input_residual.clone()
    )
    exact_states = []
    for layer, metadata, initial_state in zip(
        layers, metadata_by_layer, dense_initial_states
    ):
        (
            exact_hidden,
            exact_residual,
            exact_conv,
            exact_recurrent,
        ) = _functional_decoder_layer_decode(
            layer,
            exact_hidden,
            exact_residual,
            metadata,
            initial_state[0],
            initial_state[1],
        )
        exact_states.append((exact_conv, exact_recurrent))
    exact_state_metrics = []
    for layer, exact, dense in zip(
        layers, exact_states, dense_state_snapshots
    ):
        exact_state_metrics.append(
            {
                "layer_idx": int(layer.layer_idx),
                "conv": _tensor_metrics(dense[0], exact[0]),
                "recurrent": _tensor_metrics(dense[1], exact[1]),
            }
        )
    exact_output_metrics = _tensor_metrics(
        reference_materialized,
        _materialize(exact_hidden, exact_residual),
    )
    exact_passed = bool(
        exact_output_metrics["all_finite"]
        and exact_output_metrics["relative_l2"]
        <= config.exact_split_relative_l2_max
        and all(
            item[kind]["all_finite"]
            and item[kind]["relative_l2"]
            <= config.exact_split_relative_l2_max
            for item in exact_state_metrics
            for kind in ("conv", "recurrent")
        )
    )
    emit_event(
        "group_oracle_first_decode_exact_result",
        distributed_rank=_distributed_rank(),
        start_layer=start_layer,
        end_layer=start_layer + 2,
        output=exact_output_metrics,
        states=exact_state_metrics,
        relative_l2_max=config.exact_split_relative_l2_max,
        harness_passed=exact_passed,
    )
    if not exact_passed:
        raise RuntimeError(
            f"Tail-Replay exact first-decode harness failed at {start_layer}"
        )
    for ratio in config.replay_ratios:
        current_hidden = input_hidden.clone()
        current_residual = (
            None if input_residual is None else input_residual.clone()
        )
        candidate_states = []
        for layer, metadata in zip(layers, metadata_by_layer):
            state_key = (float(ratio), int(layer.layer_idx))
            if state_key not in _REPLAY_STATES:
                raise RuntimeError(
                    f"Tail-Replay missing reconstructed state {state_key}"
                )
            conv_state, recurrent_state = _REPLAY_STATES[state_key]
            (
                current_hidden,
                current_residual,
                next_conv,
                next_recurrent,
            ) = _functional_decoder_layer_decode(
                layer,
                current_hidden,
                current_residual,
                metadata,
                conv_state,
                recurrent_state,
            )
            candidate_states.append((next_conv, next_recurrent))
        state_metrics = []
        for layer, candidate, dense in zip(
            layers, candidate_states, dense_state_snapshots
        ):
            state_metrics.append(
                {
                    "layer_idx": int(layer.layer_idx),
                    "conv": _tensor_metrics(dense[0], candidate[0]),
                    "recurrent": _tensor_metrics(dense[1], candidate[1]),
                }
            )
        emit_event(
            "group_oracle_first_decode_result",
            distributed_rank=_distributed_rank(),
            start_layer=start_layer,
            end_layer=start_layer + 2,
            replay_ratio=ratio,
            output=_tensor_metrics(
                reference_materialized,
                _materialize(current_hidden, current_residual),
            ),
            states=state_metrics,
        )

    preserved = True
    preservation = []
    for layer, metadata, snapshot in zip(
        layers, metadata_by_layer, dense_state_snapshots
    ):
        current = _dense_decode_states(layer, metadata)
        conv_equal = bool(torch.equal(current[0], snapshot[0]))
        recurrent_equal = bool(torch.equal(current[1], snapshot[1]))
        preserved = preserved and conv_equal and recurrent_equal
        preservation.append(
            {
                "layer_idx": int(layer.layer_idx),
                "conv_bitwise_equal": conv_equal,
                "recurrent_bitwise_equal": recurrent_equal,
            }
        )
    emit_event(
        "group_oracle_first_decode_cache_preservation",
        distributed_rank=_distributed_rank(),
        start_layer=start_layer,
        end_layer=start_layer + 2,
        cache_preserved=preserved,
        layers=preservation,
    )
    if not preserved:
        raise RuntimeError(
            f"Tail-Replay first-decode oracle mutated live cache at {start_layer}"
        )
    if input_hidden.device.type == "npu":
        torch.npu.synchronize()


def _make_decoder_wrapper(original: Callable, config: TailReplayConfig) -> Callable:
    @wraps(original)
    def decoder_with_group_oracle(self, hidden_states, residual, *args, **kwargs):
        layer_idx = int(getattr(self, "layer_idx", -1))
        layer_type = str(getattr(self, "layer_type", ""))
        capture = _ACTIVE_CAPTURE.get()
        decode_capture = _ACTIVE_DECODE_CAPTURE.get()
        if layer_idx >= 0 and layer_idx % 4 == 0:
            token_count = int(hidden_states.shape[0])
            emit_event(
                "group_oracle_group_start_seen",
                distributed_rank=_distributed_rank(),
                layer_idx=layer_idx,
                layer_type=layer_type,
                token_count=token_count,
                capture_eligible=bool(
                    _is_group_start(layer_idx, layer_type)
                    and config.min_prefill_tokens
                    <= token_count
                    <= config.max_prefill_tokens
                ),
                decoder_class_module=type(self).__module__,
                decoder_class_name=type(self).__qualname__,
            )
        if _is_group_start(layer_idx, layer_type):
            token_count = int(hidden_states.shape[0])
            key = (_distributed_rank(), layer_idx)
            should_capture = (
                config.min_prefill_tokens <= token_count <= config.max_prefill_tokens
            )
            with _SEEN_LOCK:
                if key in _SEEN_GROUPS:
                    should_capture = False
                elif should_capture:
                    _SEEN_GROUPS.add(key)
            if should_capture:
                _prefill_metadata(self.linear_attn)
                capture = {
                    "start_layer": layer_idx,
                    "layers": [],
                    "input_hidden": hidden_states.clone(),
                    "input_residual": (
                        None if residual is None else residual.clone()
                    ),
                }
                _ACTIVE_CAPTURE.set(capture)

            decode_key = (_distributed_rank(), layer_idx)
            reconstructed_ready = all(
                (float(ratio), candidate_layer) in _REPLAY_STATES
                for ratio in config.replay_ratios
                for candidate_layer in range(layer_idx, layer_idx + 3)
            )
            should_decode_capture = (
                token_count == 1
                and reconstructed_ready
                and decode_key not in _SEEN_DECODE_GROUPS
            )
            if should_decode_capture:
                _decode_metadata(self.linear_attn)
                with _SEEN_LOCK:
                    if decode_key in _SEEN_DECODE_GROUPS:
                        should_decode_capture = False
                    else:
                        _SEEN_DECODE_GROUPS.add(decode_key)
            if should_decode_capture:
                decode_capture = {
                    "start_layer": layer_idx,
                    "layers": [],
                    "dense_initial_states": [],
                    "input_hidden": hidden_states.clone(),
                    "input_residual": (
                        None if residual is None else residual.clone()
                    ),
                }
                _ACTIVE_DECODE_CAPTURE.set(decode_capture)

        if capture is not None:
            expected_idx = int(capture["start_layer"]) + len(capture["layers"])
            if layer_idx == expected_idx and layer_type == "linear_attention":
                capture["layers"].append(self)
        if decode_capture is not None:
            expected_idx = (
                int(decode_capture["start_layer"])
                + len(decode_capture["layers"])
            )
            if layer_idx == expected_idx and layer_type == "linear_attention":
                decode_capture["layers"].append(self)
                decode_capture["dense_initial_states"].append(
                    _dense_decode_states(
                        self, _decode_metadata(self.linear_attn)
                    )
                )

        result = original(self, hidden_states, residual, *args, **kwargs)
        if (
            capture is not None
            and _is_group_end(layer_idx, layer_type)
            and len(capture["layers"]) == 3
        ):
            _run_group_oracle(
                start_layer=int(capture["start_layer"]),
                layers=capture["layers"],
                input_hidden=capture["input_hidden"],
                input_residual=capture["input_residual"],
                reference_hidden=result[0],
                reference_residual=result[1],
                config=config,
            )
            _ACTIVE_CAPTURE.set(None)
        if (
            decode_capture is not None
            and _is_group_end(layer_idx, layer_type)
            and len(decode_capture["layers"]) == 3
        ):
            _run_first_decode_oracle(
                start_layer=int(decode_capture["start_layer"]),
                layers=decode_capture["layers"],
                input_hidden=decode_capture["input_hidden"],
                input_residual=decode_capture["input_residual"],
                reference_hidden=result[0],
                reference_residual=result[1],
                dense_initial_states=decode_capture[
                    "dense_initial_states"
                ],
                config=config,
            )
            _ACTIVE_DECODE_CAPTURE.set(None)
        return result

    decoder_with_group_oracle._mst_tail_replay_group_wrapper = True
    return decoder_with_group_oracle


def _apply_full_group_patch(module: ModuleType, config: TailReplayConfig) -> None:
    decoder_class = getattr(module, "Qwen3_5DecoderLayer", None)
    if decoder_class is None:
        if config.require_runtime_hooks:
            raise RuntimeError(
                "Tail-Replay group oracle could not resolve Qwen3_5DecoderLayer"
            )
        return
    original = decoder_class.forward
    if getattr(original, "_mst_tail_replay_group_wrapper", False):
        return
    decoder_class.forward = _make_decoder_wrapper(original, config)
    path, source_hash = _source_identity(original)
    emit_event(
        "group_oracle_patch_installed",
        distributed_rank=_distributed_rank(),
        target_module=module.__name__,
        decoder_source_path=path,
        decoder_source_sha256=source_hash,
        replay_ratios=list(config.replay_ratios),
        applied_after_ascend_patch=True,
    )


def _apply_after_ascend_patch(
    ascend_patch_module: ModuleType, config: TailReplayConfig
) -> None:
    target_module = sys.modules.get(_TARGET_MODULE)
    if target_module is None:
        if config.require_runtime_hooks:
            raise RuntimeError(
                "Tail-Replay group oracle saw the Ascend Qwen3.5 patch "
                "without the target model module"
            )
        return
    _apply_full_group_patch(target_module, config)
    emit_event(
        "group_oracle_ascend_patch_order_verified",
        distributed_rank=_distributed_rank(),
        ascend_patch_module=ascend_patch_module.__name__,
        target_module=_TARGET_MODULE,
    )


def install_full_group_patch(config: TailReplayConfig) -> None:
    ascend_patch_module = sys.modules.get(_ASCEND_PATCH_MODULE)
    if ascend_patch_module is not None:
        _apply_after_ascend_patch(ascend_patch_module, config)
        return

    def callback(imported_module: ModuleType) -> None:
        _apply_after_ascend_patch(imported_module, config)

    PostImportFinder(_ASCEND_PATCH_MODULE, callback).install()
    emit_event(
        "group_oracle_patch_deferred",
        target_module=_TARGET_MODULE,
        wait_for_module=_ASCEND_PATCH_MODULE,
    )

"""One-kernel packed QKV rearrangement with exact-boundary Q/K L2 norm."""

from __future__ import annotations

import torch

from vllm.triton_utils import tl, triton


@triton.jit
def _packed_qkv_l2_kernel(
    mixed,
    output,
    tokens,
    eps,
    H_QK: tl.constexpr,
    H_V: tl.constexpr,
    D_K: tl.constexpr,
    D_V: tl.constexpr,
    V_BLOCK: tl.constexpr,
):
    pid = tl.program_id(0)
    norm_rows_per_token: tl.constexpr = 2 * H_QK
    v_blocks_per_token: tl.constexpr = tl.cdiv(H_V * D_V, V_BLOCK)
    norm_programs = tokens * norm_rows_per_token
    q_width: tl.constexpr = H_QK * D_K
    k_width: tl.constexpr = H_QK * D_K
    v_width: tl.constexpr = H_V * D_V
    packed_width: tl.constexpr = q_width + k_width + v_width

    if pid < norm_programs:
        token = pid // norm_rows_per_token
        row = pid % norm_rows_per_token
        is_key = row >= H_QK
        head = row - tl.where(is_key, H_QK, 0)
        cols = tl.arange(0, D_K)
        input_base = token * packed_width + head * D_K
        input_base += tl.where(is_key, q_width, 0)
        values = tl.load(mixed + input_base + cols).to(tl.float32)
        inv_norm = tl.rsqrt(tl.sum(values * values, axis=0) + eps)
        output_base = token * q_width + head * D_K
        output_base += tl.where(is_key, tokens * q_width, 0)
        tl.store(
            output + output_base + cols,
            (values * inv_norm).to(tl.bfloat16),
        )
    else:
        value_pid = pid - norm_programs
        token = value_pid // v_blocks_per_token
        block = value_pid % v_blocks_per_token
        cols = tl.arange(0, V_BLOCK)
        value_offset = block * V_BLOCK + cols
        mask = value_offset < v_width
        input_base = token * packed_width + q_width + k_width
        output_base = tokens * (q_width + k_width) + token * v_width
        values = tl.load(mixed + input_base + value_offset, mask=mask)
        tl.store(output + output_base + value_offset, values, mask=mask)


def packed_qkv_l2(
    mixed_qkv: torch.Tensor,
    *,
    h_qk: int = 4,
    h_v: int = 12,
    d_k: int = 64,
    d_v: int = 128,
    eps: float = 1e-6,
):
    """Return contiguous Q/K/V views matching rearrange then l2norm_fwd.

    This first implementation deliberately supports only the admitted TP4
    energy-Dk64 decode layout. Callers must retain the unfused path as fallback.
    """
    if mixed_qkv.ndim != 2 or mixed_qkv.dtype != torch.bfloat16:
        raise RuntimeError("DRRQR packed QKV requires a rank-2 BF16 tensor")
    if (h_qk, h_v, d_k, d_v) != (4, 12, 64, 128):
        raise RuntimeError("DRRQR packed QKV supports only TP4 Dk64 layout")
    tokens = mixed_qkv.shape[0]
    packed_width = 2 * h_qk * d_k + h_v * d_v
    if mixed_qkv.shape[1] != packed_width or not mixed_qkv.is_contiguous():
        raise RuntimeError("DRRQR packed QKV width/stride contract failed")
    output = torch.empty(
        (tokens * packed_width,), dtype=mixed_qkv.dtype,
        device=mixed_qkv.device,
    )
    v_block = 256
    programs = tokens * (
        2 * h_qk + triton.cdiv(h_v * d_v, v_block)
    )
    _packed_qkv_l2_kernel[(programs,)](
        mixed_qkv, output, tokens, eps,
        H_QK=h_qk, H_V=h_v, D_K=d_k, D_V=d_v, V_BLOCK=v_block,
    )
    q_size = tokens * h_qk * d_k
    k_size = q_size
    query = output[:q_size].view(1, tokens, h_qk, d_k)
    key = output[q_size:q_size + k_size].view(1, tokens, h_qk, d_k)
    value = output[q_size + k_size:].view(1, tokens, h_v, d_v)
    return query, key, value

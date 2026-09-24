"""One-tile KVarN compressed attention feasibility kernel for Ascend.

This intentionally tests only the author's K4/V2 dequant-plus-attention
mechanism. It does not implement the sink/tail pool, paging or vLLM serving.
"""

from __future__ import annotations

import math

import torch
import triton
import triton.language as tl

from .tile_dequant_split import GROUP, HEAD_DIM


@triton.jit
def _one_tile_attention(
    q_ptr, kq_ptr, kcol_ptr, kzp_ptr, krow_ptr,
    vq_ptr, vcol_ptr, vrow_ptr, vzp_ptr, out_ptr,
    SCALE: tl.constexpr, D: tl.constexpr, G: tl.constexpr,
    H: tl.constexpr, HPAD: tl.constexpr, BN: tl.constexpr,
):
    tile = tl.program_id(0)
    d = tl.arange(0, D)
    heads = tl.arange(0, HPAD)
    q = tl.load(q_ptr + tile * H * D + heads[:, None] * D + d[None, :],
                mask=(heads < H)[:, None], other=0).to(tl.float16)
    kc = tl.load(kcol_ptr + tile * D + d).to(tl.float32)
    kz = tl.load(kzp_ptr + tile * D + d).to(tl.float32)
    vc = tl.load(vcol_ptr + tile * D + d).to(tl.float32)
    maximum = tl.full((HPAD,), -float("inf"), tl.float32)
    denominator = tl.zeros((HPAD,), tl.float32)
    numerator = tl.zeros((HPAD, D), tl.float32)
    for start in range(0, G, BN):
        token = start + tl.arange(0, BN)
        kr = tl.load(krow_ptr + tile * G + token).to(tl.float32)
        vr = tl.load(vrow_ptr + tile * G + token).to(tl.float32)
        vz = tl.load(vzp_ptr + tile * G + token).to(tl.float32)
        k_offset = tile * (D * G // 2) + d[:, None] * (G // 2) + (token // 2)[None, :]
        kb = tl.load(kq_ptr + k_offset).to(tl.int32)
        k_quant = ((kb >> ((token % 2) * 4)[None, :]) & 15).to(tl.float32)
        key = ((k_quant * kc[:, None] + kz[:, None]) * kr[None, :]).to(tl.float16)
        v_offset = tile * (G * D // 4) + token[:, None] * (D // 4) + (d // 4)[None, :]
        vb = tl.load(vq_ptr + v_offset).to(tl.int32)
        v_quant = ((vb >> ((d % 4) * 2)[None, :]) & 3).to(tl.float32)
        value = ((v_quant * vr[:, None] + vz[:, None]) * vc[None, :]).to(tl.float16)
        logits = tl.dot(q, key).to(tl.float32) * SCALE
        new_max = tl.maximum(maximum, tl.max(logits, 1))
        probability = tl.exp(logits - new_max[:, None])
        alpha = tl.exp(maximum - new_max)
        denominator = denominator * alpha + tl.sum(probability, 1)
        numerator = numerator * alpha[:, None] + tl.dot(probability.to(tl.float16), value)
        maximum = new_max
    result = (numerator / denominator[:, None]).to(tl.float16)
    tl.store(out_ptr + tile * H * D + heads[:, None] * D + d[None, :],
             result, mask=(heads < H)[:, None])


def one_tile_attention_split(
    q: torch.Tensor, k_packed: torch.Tensor, k_col: torch.Tensor,
    k_zp: torch.Tensor, k_row: torch.Tensor, v_packed: torch.Tensor,
    v_col: torch.Tensor, v_row: torch.Tensor, v_zp: torch.Tensor,
) -> torch.Tensor:
    """Decode one query per tile, six local Q heads per KV head."""
    tiles = k_packed.shape[0]
    if q.shape != (tiles, 6, HEAD_DIM) or q.dtype != torch.float16 or q.device.type != "npu":
        raise ValueError("q must be contiguous NPU FP16 [tiles,6,256]")
    if not q.is_contiguous():
        raise ValueError("q must be contiguous")
    out = torch.empty_like(q)
    _one_tile_attention[(tiles,)](
        q, k_packed, k_col, k_zp, k_row,
        v_packed, v_col, v_row, v_zp, out,
        SCALE=1.0 / math.sqrt(HEAD_DIM), D=HEAD_DIM, G=GROUP,
        H=6, HPAD=16, BN=32,
    )
    return out

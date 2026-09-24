"""KVarN split-metadata mixed-cache decode feasibility kernel.

This is a paper-specific NPU numerical prototype, not a vLLM cache manager.
Block-table indirection and a FP16 sink/tail pool match the author's decode
mechanism; the split metadata is an Ascend compiler adaptation.
"""

from __future__ import annotations

import math

import torch
import triton
import triton.language as tl

from .tile_dequant_split import GROUP, HEAD_DIM


@triton.jit
def _mixed_decode(
    q_ptr, table_ptr, length_ptr, slot_ptr,
    kq_ptr, kc_ptr, kz_ptr, kr_ptr, vq_ptr, vc_ptr, vr_ptr, vz_ptr,
    pool_k_ptr, pool_v_ptr, out_ptr,
    SCALE: tl.constexpr, D: tl.constexpr, G: tl.constexpr,
    H: tl.constexpr, HPAD: tl.constexpr, BN: tl.constexpr,
    MAX_BLOCKS: tl.constexpr,
):
    b = tl.program_id(0)
    length = tl.load(length_ptr + b)
    d = tl.arange(0, D)
    heads = tl.arange(0, HPAD)
    q = tl.load(q_ptr + b * H * D + heads[:, None] * D + d[None, :],
                mask=(heads < H)[:, None], other=0).to(tl.float16)
    maximum = tl.full((HPAD,), -float("inf"), tl.float32)
    denominator = tl.zeros((HPAD,), tl.float32)
    numerator = tl.zeros((HPAD, D), tl.float32)
    for block in range(MAX_BLOCKS):
        valid = tl.minimum(tl.maximum(length - block * G, 0), G)
        block_id = tl.maximum(tl.load(table_ptr + b * MAX_BLOCKS + block), 0)
        pool_slot = tl.load(slot_ptr + block_id)
        for start in range(0, G, BN):
            token = start + tl.arange(0, BN)
            mask = token < valid
            safe_slot = tl.maximum(pool_slot, 0)
            offset = safe_slot * G * D + token[:, None] * D + d[None, :]
            pool_key = tl.load(pool_k_ptr + offset, mask=mask[:, None], other=0).to(tl.float16)
            pool_value = tl.load(pool_v_ptr + offset, mask=mask[:, None], other=0).to(tl.float16)
            kc = tl.load(kc_ptr + block_id * D + d).to(tl.float32)
            kz = tl.load(kz_ptr + block_id * D + d).to(tl.float32)
            vc = tl.load(vc_ptr + block_id * D + d).to(tl.float32)
            kr = tl.load(kr_ptr + block_id * G + token).to(tl.float32)
            vr = tl.load(vr_ptr + block_id * G + token).to(tl.float32)
            vz = tl.load(vz_ptr + block_id * G + token).to(tl.float32)
            ko = block_id * (D * G // 2) + d[:, None] * (G // 2) + (token // 2)[None, :]
            kb = tl.load(kq_ptr + ko).to(tl.int32)
            kquant = ((kb >> ((token % 2) * 4)[None, :]) & 15).to(tl.float32)
            compressed_key = ((kquant * kc[:, None] + kz[:, None]) * kr[None, :]).to(tl.float16)
            vo = block_id * (G * D // 4) + token[:, None] * (D // 4) + (d // 4)[None, :]
            vb = tl.load(vq_ptr + vo).to(tl.int32)
            vquant = ((vb >> ((d % 4) * 2)[None, :]) & 3).to(tl.float32)
            compressed_value = ((vquant * vr[:, None] + vz[:, None]) * vc[None, :]).to(tl.float16)
            key_dg = tl.where(pool_slot >= 0, tl.trans(pool_key), compressed_key)
            value = tl.where(pool_slot >= 0, pool_value, compressed_value)
            logits = tl.dot(q, key_dg).to(tl.float32) * SCALE
            logits = tl.where(mask[None, :], logits, -1.0e9)
            new_max = tl.maximum(maximum, tl.max(logits, 1))
            probability = tl.exp(logits - new_max[:, None])
            alpha = tl.exp(maximum - new_max)
            denominator = denominator * alpha + tl.sum(probability, 1)
            numerator = numerator * alpha[:, None] + tl.dot(probability.to(tl.float16), value)
            maximum = new_max
    result = tl.where(length > 0, numerator / denominator[:, None], 0).to(tl.float16)
    tl.store(out_ptr + b * H * D + heads[:, None] * D + d[None, :],
             result, mask=(heads < H)[:, None])


def mixed_decode_split(
    q: torch.Tensor, block_table: torch.Tensor, seq_lens: torch.Tensor,
    block_to_pool_slot: torch.Tensor, k_packed: torch.Tensor,
    k_col: torch.Tensor, k_zp: torch.Tensor, k_row: torch.Tensor,
    v_packed: torch.Tensor, v_col: torch.Tensor, v_row: torch.Tensor,
    v_zp: torch.Tensor, pool_k: torch.Tensor, pool_v: torch.Tensor,
) -> torch.Tensor:
    """Return `[B,6,256]` rotated-space attention for mixed 128-token blocks."""
    batch = q.shape[0]
    if q.shape != (batch, 6, HEAD_DIM) or q.dtype != torch.float16:
        raise ValueError("q must be FP16 [B,6,256]")
    if block_table.ndim != 2 or block_table.shape[0] != batch:
        raise ValueError("block_table must be [B,max_blocks]")
    if seq_lens.shape != (batch,) or block_to_pool_slot.shape != (k_packed.shape[0],):
        raise ValueError("invalid sequence length or block map")
    if block_table.dtype != torch.int32 or seq_lens.dtype != torch.int32 or block_to_pool_slot.dtype != torch.int32:
        raise ValueError("metadata must be int32")
    if pool_k.shape != pool_v.shape or pool_k.ndim != 3 or pool_k.shape[1:] != (GROUP, HEAD_DIM):
        raise ValueError("pool must be [slots,128,256]")
    fields = (q, block_table, seq_lens, block_to_pool_slot, k_packed, k_col,
              k_zp, k_row, v_packed, v_col, v_row, v_zp, pool_k, pool_v)
    if any(t.device != q.device or t.device.type != "npu" or not t.is_contiguous() for t in fields):
        raise ValueError("all fields must be contiguous on one NPU")
    out = torch.empty_like(q)
    _mixed_decode[(batch,)](
        q, block_table, seq_lens, block_to_pool_slot,
        k_packed, k_col, k_zp, k_row, v_packed, v_col, v_row, v_zp,
        pool_k, pool_v, out,
        SCALE=1.0 / math.sqrt(HEAD_DIM), D=HEAD_DIM, G=GROUP,
        H=6, HPAD=16, BN=32, MAX_BLOCKS=block_table.shape[1],
    )
    return out

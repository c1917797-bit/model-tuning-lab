"""Opt-in KVarN FP16 staging-pool scatter for Ascend.

This is the author algorithm's slot-mapping store seam: tokens are rotated
before entry, and completed non-sink blocks are sealed separately. No dense
BF16 KV cache is allocated by this module.
"""

from __future__ import annotations

import torch
import triton
import triton.language as tl

from .tile_dequant_split import GROUP, HEAD_DIM


@triton.jit
def _scatter_pool(
    k_ptr, v_ptr, slot_mapping_ptr, block_to_slot_ptr, pool_k_ptr, pool_v_ptr,
    STRIDE_IN_N: tl.constexpr, STRIDE_IN_H: tl.constexpr,
    STRIDE_POOL_B: tl.constexpr, STRIDE_POOL_T: tl.constexpr,
    STRIDE_POOL_H: tl.constexpr, NUM_BLOCKS: tl.constexpr,
    POOL_SIZE: tl.constexpr, G: tl.constexpr, D: tl.constexpr,
):
    token = tl.program_id(0)
    head = tl.program_id(1)
    sm = tl.load(slot_mapping_ptr + token)
    block = sm // G
    valid_block = (sm >= 0) & (block < NUM_BLOCKS)
    safe_block = tl.minimum(tl.maximum(block, 0), NUM_BLOCKS - 1)
    slot = tl.load(block_to_slot_ptr + safe_block, mask=valid_block, other=-1)
    valid_slot = valid_block & (slot >= 0) & (slot < POOL_SIZE)
    safe_slot = tl.maximum(slot, 0)
    position = tl.maximum(sm % G, 0)
    d = tl.arange(0, D)
    src = token * STRIDE_IN_N + head * STRIDE_IN_H + d
    k = tl.load(k_ptr + src)
    v = tl.load(v_ptr + src)
    dst = (safe_slot.to(tl.int64) * STRIDE_POOL_B
           + position.to(tl.int64) * STRIDE_POOL_T
           + head * STRIDE_POOL_H + d)
    tl.store(pool_k_ptr + dst, k, mask=valid_slot)
    tl.store(pool_v_ptr + dst, v, mask=valid_slot)


def scatter_pool(
    k: torch.Tensor,
    v: torch.Tensor,
    slot_mapping: torch.Tensor,
    block_to_slot: torch.Tensor,
    pool_k: torch.Tensor,
    pool_v: torch.Tensor,
) -> None:
    """Scatter rotated `[N,Hk,256]` tokens to `[slots,128,Hk,256]`."""
    if k.ndim != 3 or v.shape != k.shape or k.shape[-1] != HEAD_DIM:
        raise ValueError("K/V must share shape [tokens, kv_heads, 256]")
    if k.dtype != torch.float16 or v.dtype != torch.float16:
        raise ValueError("rotated K/V must be FP16")
    if slot_mapping.shape != (k.shape[0],) or slot_mapping.dtype != torch.int32:
        raise ValueError("slot_mapping must be int32 [tokens]")
    if block_to_slot.ndim != 1 or block_to_slot.dtype != torch.int32:
        raise ValueError("block_to_slot must be int32 [num_blocks]")
    if block_to_slot.numel() == 0:
        raise ValueError("block_to_slot must not be empty")
    if pool_k.shape != pool_v.shape or pool_k.ndim != 4:
        raise ValueError("pool K/V must share shape [slots,128,kv_heads,256]")
    if pool_k.shape[1:] != (GROUP, k.shape[1], HEAD_DIM):
        raise ValueError("pool geometry does not match K/V")
    if pool_k.dtype != torch.float16 or pool_v.dtype != torch.float16:
        raise ValueError("pool K/V must be FP16")
    tensors = (k, v, slot_mapping, block_to_slot, pool_k, pool_v)
    if any(t.device != k.device or t.device.type != "npu" or not t.is_contiguous()
           for t in tensors):
        raise ValueError("all inputs must be contiguous on one NPU")
    _scatter_pool[(k.shape[0], k.shape[1])](
        k, v, slot_mapping, block_to_slot, pool_k, pool_v,
        STRIDE_IN_N=k.stride(0), STRIDE_IN_H=k.stride(1),
        STRIDE_POOL_B=pool_k.stride(0), STRIDE_POOL_T=pool_k.stride(1),
        STRIDE_POOL_H=pool_k.stride(2),
        NUM_BLOCKS=block_to_slot.numel(), POOL_SIZE=pool_k.shape[0],
        G=GROUP, D=HEAD_DIM,
    )

"""Partitioned KVarN compressed/pool attention prototype for Ascend.

Separate kernels avoid the CANN 9.1 mixed-source dynamic-branch lowering
failure. Each returns a normalized partial output plus log-sum-exp so the
partials can be combined without materializing the full KV history.
"""

from __future__ import annotations

import math

import torch
import triton
import triton.language as tl

from .tile_dequant_split import GROUP, HEAD_DIM


@triton.jit
def _compressed_partial(
    q_ptr, block_ids_ptr,
    kq_ptr, kc_ptr, kz_ptr, kr_ptr, vq_ptr, vc_ptr, vr_ptr, vz_ptr,
    out_ptr, lse_ptr,
    SCALE: tl.constexpr, D: tl.constexpr, G: tl.constexpr,
    H: tl.constexpr, HPAD: tl.constexpr, BN: tl.constexpr,
):
    task = tl.program_id(0)
    block = tl.load(block_ids_ptr + task)
    d = tl.arange(0, D)
    heads = tl.arange(0, HPAD)
    q = tl.load(q_ptr + task * H * D + heads[:, None] * D + d[None, :],
                mask=(heads < H)[:, None], other=0).to(tl.float16)
    kc = tl.load(kc_ptr + block * D + d).to(tl.float32)
    kz = tl.load(kz_ptr + block * D + d).to(tl.float32)
    vc = tl.load(vc_ptr + block * D + d).to(tl.float32)
    maximum = tl.full((HPAD,), -float("inf"), tl.float32)
    denominator = tl.zeros((HPAD,), tl.float32)
    numerator = tl.zeros((HPAD, D), tl.float32)
    for start in range(0, G, BN):
        token = start + tl.arange(0, BN)
        kr = tl.load(kr_ptr + block * G + token).to(tl.float32)
        vr = tl.load(vr_ptr + block * G + token).to(tl.float32)
        vz = tl.load(vz_ptr + block * G + token).to(tl.float32)
        ko = block * (D * G // 2) + d[:, None] * (G // 2) + (token // 2)[None, :]
        kb = tl.load(kq_ptr + ko).to(tl.int32)
        kquant = ((kb >> ((token % 2) * 4)[None, :]) & 15).to(tl.float32)
        key = ((kquant * kc[:, None] + kz[:, None]) * kr[None, :]).to(tl.float16)
        vo = block * (G * D // 4) + token[:, None] * (D // 4) + (d // 4)[None, :]
        vb = tl.load(vq_ptr + vo).to(tl.int32)
        vquant = ((vb >> ((d % 4) * 2)[None, :]) & 3).to(tl.float32)
        value = ((vquant * vr[:, None] + vz[:, None]) * vc[None, :]).to(tl.float16)
        logits = tl.dot(q, key).to(tl.float32) * SCALE
        new_max = tl.maximum(maximum, tl.max(logits, 1))
        probability = tl.exp(logits - new_max[:, None])
        alpha = tl.exp(maximum - new_max)
        denominator = denominator * alpha + tl.sum(probability, 1)
        numerator = numerator * alpha[:, None] + tl.dot(probability.to(tl.float16), value)
        maximum = new_max
    output = (numerator / denominator[:, None]).to(tl.float16)
    lse = maximum + tl.log(denominator)
    tl.store(out_ptr + task * H * D + heads[:, None] * D + d[None, :],
             output, mask=(heads < H)[:, None])
    tl.store(lse_ptr + task * H + heads, lse, mask=heads < H)


@triton.jit
def _pool_partial(
    q_ptr, slot_ids_ptr, valid_ptr, pool_k_ptr, pool_v_ptr,
    out_ptr, lse_ptr,
    SCALE: tl.constexpr, D: tl.constexpr, G: tl.constexpr,
    H: tl.constexpr, HPAD: tl.constexpr, BN: tl.constexpr,
):
    task = tl.program_id(0)
    slot = tl.load(slot_ids_ptr + task)
    valid = tl.load(valid_ptr + task)
    d = tl.arange(0, D)
    heads = tl.arange(0, HPAD)
    q = tl.load(q_ptr + task * H * D + heads[:, None] * D + d[None, :],
                mask=(heads < H)[:, None], other=0).to(tl.float16)
    maximum = tl.full((HPAD,), -float("inf"), tl.float32)
    denominator = tl.zeros((HPAD,), tl.float32)
    numerator = tl.zeros((HPAD, D), tl.float32)
    for start in range(0, G, BN):
        token = start + tl.arange(0, BN)
        mask = token < valid
        offset = slot * G * D + token[:, None] * D + d[None, :]
        key = tl.load(pool_k_ptr + offset, mask=mask[:, None], other=0).to(tl.float16)
        value = tl.load(pool_v_ptr + offset, mask=mask[:, None], other=0).to(tl.float16)
        logits = tl.dot(q, tl.trans(key)).to(tl.float32) * SCALE
        logits = tl.where(mask[None, :], logits, -1.0e9)
        new_max = tl.maximum(maximum, tl.max(logits, 1))
        probability = tl.exp(logits - new_max[:, None])
        alpha = tl.exp(maximum - new_max)
        denominator = denominator * alpha + tl.sum(probability, 1)
        numerator = numerator * alpha[:, None] + tl.dot(probability.to(tl.float16), value)
        maximum = new_max
    output = (numerator / denominator[:, None]).to(tl.float16)
    lse = maximum + tl.log(denominator)
    tl.store(out_ptr + task * H * D + heads[:, None] * D + d[None, :],
             output, mask=(heads < H)[:, None])
    tl.store(lse_ptr + task * H + heads, lse, mask=heads < H)


def compressed_partial(q: torch.Tensor, block_ids: torch.Tensor, fields: tuple[torch.Tensor, ...]):
    if q.ndim != 3 or q.shape[1:] != (6, HEAD_DIM) or q.dtype != torch.float16:
        raise ValueError("q must be FP16 [tasks,6,256]")
    if block_ids.shape != (q.shape[0],) or block_ids.dtype != torch.int32 or len(fields) != 8:
        raise ValueError("invalid compressed task inputs")
    if any(t.device != q.device or t.device.type != "npu" or not t.is_contiguous()
           for t in (q, block_ids, *fields)):
        raise ValueError("all compressed inputs must be contiguous on one NPU")
    out = torch.empty_like(q)
    lse = torch.empty(q.shape[:2], dtype=torch.float32, device=q.device)
    _compressed_partial[(q.shape[0],)](
        q, block_ids, *fields, out, lse,
        SCALE=1.0 / math.sqrt(HEAD_DIM), D=HEAD_DIM, G=GROUP,
        H=6, HPAD=16, BN=32,
    )
    return out, lse


def pool_partial(q: torch.Tensor, slots: torch.Tensor, valid: torch.Tensor,
                 pool_k: torch.Tensor, pool_v: torch.Tensor):
    if q.ndim != 3 or q.shape[1:] != (6, HEAD_DIM) or q.dtype != torch.float16:
        raise ValueError("q must be FP16 [tasks,6,256]")
    if slots.shape != (q.shape[0],) or valid.shape != slots.shape:
        raise ValueError("invalid pool task arrays")
    if slots.dtype != torch.int32 or valid.dtype != torch.int32:
        raise ValueError("pool task arrays must be int32")
    if pool_k.shape != pool_v.shape or pool_k.ndim != 3 or pool_k.shape[1:] != (GROUP, HEAD_DIM):
        raise ValueError("invalid pool shape")
    if any(t.device != q.device or t.device.type != "npu" or not t.is_contiguous()
           for t in (q, slots, valid, pool_k, pool_v)):
        raise ValueError("all pool inputs must be contiguous on one NPU")
    out = torch.empty_like(q)
    lse = torch.empty(q.shape[:2], dtype=torch.float32, device=q.device)
    _pool_partial[(q.shape[0],)](
        q, slots, valid, pool_k, pool_v, out, lse,
        SCALE=1.0 / math.sqrt(HEAD_DIM), D=HEAD_DIM, G=GROUP,
        H=6, HPAD=16, BN=32,
    )
    return out, lse


def combine_partials(outputs: torch.Tensor, lses: torch.Tensor) -> torch.Tensor:
    """Combine `[B, parts, 6, D]` normalized partials via log-sum-exp."""
    maximum = lses.max(1, keepdim=True).values
    weights = torch.exp(lses - maximum)
    result = (outputs.float() * weights[..., None]).sum(1) / weights.sum(1)[..., None]
    return result.half()

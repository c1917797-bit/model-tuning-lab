"""Typed-metadata KVarN K4/V2 dequantization on Ascend Triton.

The author tile equations are retained; typed FP16 metadata is stored apart
from the packed uint8 payload to avoid a CANN 9.1 mixed-pointer compiler
failure. This is not a complete cache manager or fused attention kernel.
"""

from __future__ import annotations

import torch
import triton
import triton.language as tl


HEAD_DIM = 256
GROUP = 128


@triton.jit
def _dequant_split_chunk(
    kq_ptr, kcol_ptr, kzp_ptr, krow_ptr,
    vq_ptr, vcol_ptr, vrow_ptr, vzp_ptr,
    kout_ptr, vout_ptr,
    D: tl.constexpr, G: tl.constexpr, BN: tl.constexpr,
):
    tile = tl.program_id(0)
    chunk = tl.program_id(1)
    d = tl.arange(0, D)
    g = chunk * BN + tl.arange(0, BN)

    k_col = tl.load(kcol_ptr + tile * D + d).to(tl.float32)
    k_zp = tl.load(kzp_ptr + tile * D + d).to(tl.float32)
    k_row = tl.load(krow_ptr + tile * G + g).to(tl.float32)
    k_addr = tile * (D * G // 2) + d[:, None] * (G // 2) + (g // 2)[None, :]
    k_byte = tl.load(kq_ptr + k_addr).to(tl.int32)
    k_quant = ((k_byte >> ((g % 2) * 4)[None, :]) & 15).to(tl.float32)
    k_value = (k_quant * k_col[:, None] + k_zp[:, None]) * k_row[None, :]

    v_col = tl.load(vcol_ptr + tile * D + d).to(tl.float32)
    v_row = tl.load(vrow_ptr + tile * G + g).to(tl.float32)
    v_zp = tl.load(vzp_ptr + tile * G + g).to(tl.float32)
    v_addr = tile * (G * D // 4) + g[:, None] * (D // 4) + (d // 4)[None, :]
    v_byte = tl.load(vq_ptr + v_addr).to(tl.int32)
    v_quant = ((v_byte >> ((d % 4) * 2)[None, :]) & 3).to(tl.float32)
    v_value = (v_quant * v_row[:, None] + v_zp[:, None]) * v_col[None, :]

    dst = tile * G * D + g[:, None] * D + d[None, :]
    tl.store(kout_ptr + dst, tl.trans(k_value).to(tl.float16))
    tl.store(vout_ptr + dst, v_value.to(tl.float16))


def dequantize_split_tiles(
    k_packed: torch.Tensor, k_col: torch.Tensor, k_zp: torch.Tensor,
    k_row: torch.Tensor, v_packed: torch.Tensor, v_col: torch.Tensor,
    v_row: torch.Tensor, v_zp: torch.Tensor, *, block_n: int = 16,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Dequantize author-equivalent fields for `[tiles,128,256]` output."""
    tiles = k_packed.shape[0]
    expected = (
        ((tiles, HEAD_DIM, GROUP // 2), torch.uint8),
        ((tiles, HEAD_DIM), torch.float16),
        ((tiles, HEAD_DIM), torch.float16),
        ((tiles, GROUP), torch.float16),
        ((tiles, GROUP, HEAD_DIM // 4), torch.uint8),
        ((tiles, HEAD_DIM), torch.float16),
        ((tiles, GROUP), torch.float16),
        ((tiles, GROUP), torch.float16),
    )
    fields = (k_packed, k_col, k_zp, k_row, v_packed, v_col, v_row, v_zp)
    for field, (shape, dtype) in zip(fields, expected):
        if field.device != k_packed.device or field.device.type != "npu":
            raise ValueError("all fields must be on one NPU")
        if tuple(field.shape) != shape or field.dtype != dtype or not field.is_contiguous():
            raise ValueError(f"invalid field shape/dtype/layout: {tuple(field.shape)}, {field.dtype}")
    if block_n not in (8, 16, 32):
        raise ValueError("block_n must be 8, 16, or 32")
    k = torch.empty((tiles, GROUP, HEAD_DIM), dtype=torch.float16, device=k_packed.device)
    v = torch.empty_like(k)
    _dequant_split_chunk[(tiles, GROUP // block_n)](
        *fields, k, v, D=HEAD_DIM, G=GROUP, BN=block_n,
    )
    return k, v

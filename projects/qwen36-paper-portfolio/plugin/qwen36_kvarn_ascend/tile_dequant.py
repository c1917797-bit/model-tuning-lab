"""KVarN K4/V2 tile dequantization for Ascend Triton.

This primitive only converts packed history tiles into rotated FP16 K/V. It
does not implement the fused attention, sink/tail lifecycle, or vLLM cache.
The byte layout follows huawei-csl/KVarN commit
7586257f1c632e63187bfacbbe21ccb51540f7b3 for D=256, group=128.
"""

from __future__ import annotations

import torch
import triton
import triton.language as tl


GROUP = 128
HEAD_DIM = 256
TILE_BYTES = 32768
K_PACKED_OFFSET = 0
K_S_COL_OFFSET = 16384
K_ZP_OFFSET = 16896
K_S_ROW_OFFSET = 17408
V_PACKED_OFFSET = 17664
V_S_COL_OFFSET = 25856
V_S_ROW_OFFSET = 26368
V_ZP_OFFSET = 26624


@triton.jit
def _dequantize_tile_chunk(
    packed_ptr, k_out_ptr, v_out_ptr,
    tile_stride, out_tile_stride,
    D: tl.constexpr, G: tl.constexpr, BN: tl.constexpr,
    K_PACKED_OFFSET: tl.constexpr, K_S_COL_OFFSET: tl.constexpr,
    K_ZP_OFFSET: tl.constexpr, K_S_ROW_OFFSET: tl.constexpr,
    V_PACKED_OFFSET: tl.constexpr, V_S_COL_OFFSET: tl.constexpr,
    V_S_ROW_OFFSET: tl.constexpr, V_ZP_OFFSET: tl.constexpr,
):
    tile = tl.program_id(0)
    chunk = tl.program_id(1)
    d = tl.arange(0, D)
    g = chunk * BN + tl.arange(0, BN)
    tile_base = tile * tile_stride
    k_col_lo = tl.load(packed_ptr + tile_base + K_S_COL_OFFSET + 2 * d).to(tl.uint16)
    k_col_hi = tl.load(packed_ptr + tile_base + K_S_COL_OFFSET + 2 * d + 1).to(tl.uint16)
    k_col = (k_col_lo | (k_col_hi << 8)).to(tl.float16, bitcast=True).to(tl.float32)
    k_zp_lo = tl.load(packed_ptr + tile_base + K_ZP_OFFSET + 2 * d).to(tl.uint16)
    k_zp_hi = tl.load(packed_ptr + tile_base + K_ZP_OFFSET + 2 * d + 1).to(tl.uint16)
    k_zp = (k_zp_lo | (k_zp_hi << 8)).to(tl.float16, bitcast=True).to(tl.float32)
    k_row_lo = tl.load(packed_ptr + tile_base + K_S_ROW_OFFSET + 2 * g).to(tl.uint16)
    k_row_hi = tl.load(packed_ptr + tile_base + K_S_ROW_OFFSET + 2 * g + 1).to(tl.uint16)
    k_row = (k_row_lo | (k_row_hi << 8)).to(tl.float16, bitcast=True).to(tl.float32)
    k_addr = tile_base + K_PACKED_OFFSET + d[:, None] * (G // 2) + (g // 2)[None, :]
    k_byte = tl.load(packed_ptr + k_addr).to(tl.uint32)
    k_quant = ((k_byte >> ((g % 2) * 4)[None, :]) & 15).to(tl.float32)
    k_value = (k_quant * k_col[:, None] + k_zp[:, None]) * k_row[None, :]

    v_col_lo = tl.load(packed_ptr + tile_base + V_S_COL_OFFSET + 2 * d).to(tl.uint16)
    v_col_hi = tl.load(packed_ptr + tile_base + V_S_COL_OFFSET + 2 * d + 1).to(tl.uint16)
    v_col = (v_col_lo | (v_col_hi << 8)).to(tl.float16, bitcast=True).to(tl.float32)
    v_row_lo = tl.load(packed_ptr + tile_base + V_S_ROW_OFFSET + 2 * g).to(tl.uint16)
    v_row_hi = tl.load(packed_ptr + tile_base + V_S_ROW_OFFSET + 2 * g + 1).to(tl.uint16)
    v_row = (v_row_lo | (v_row_hi << 8)).to(tl.float16, bitcast=True).to(tl.float32)
    v_zp_lo = tl.load(packed_ptr + tile_base + V_ZP_OFFSET + 2 * g).to(tl.uint16)
    v_zp_hi = tl.load(packed_ptr + tile_base + V_ZP_OFFSET + 2 * g + 1).to(tl.uint16)
    v_zp = (v_zp_lo | (v_zp_hi << 8)).to(tl.float16, bitcast=True).to(tl.float32)
    v_addr = tile_base + V_PACKED_OFFSET + g[:, None] * (D // 4) + (d // 4)[None, :]
    v_byte = tl.load(packed_ptr + v_addr).to(tl.uint32)
    v_quant = ((v_byte >> ((d % 4) * 2)[None, :]) & 3).to(tl.float32)
    v_value = (v_quant * v_row[:, None] + v_zp[:, None]) * v_col[None, :]

    dst = tile * out_tile_stride + g[:, None] * D + d[None, :]
    tl.store(k_out_ptr + dst, tl.trans(k_value).to(tl.float16))
    tl.store(v_out_ptr + dst, v_value.to(tl.float16))


def dequantize_packed_tiles(packed: torch.Tensor, *, block_n: int = 16) -> tuple[torch.Tensor, torch.Tensor]:
    """Dequantize contiguous ``[tiles, 32768]`` uint8 KVarN cache records."""
    if packed.device.type != "npu" or packed.dtype != torch.uint8:
        raise TypeError("packed must be an NPU uint8 tensor")
    if packed.ndim != 2 or packed.shape[1] != TILE_BYTES or not packed.is_contiguous():
        raise ValueError("packed must be contiguous [tiles, 32768]")
    if block_n not in (8, 16, 32):
        raise ValueError("block_n must be 8, 16, or 32")
    shape = (packed.shape[0], GROUP, HEAD_DIM)
    k = torch.empty(shape, dtype=torch.float16, device=packed.device)
    v = torch.empty_like(k)
    _dequantize_tile_chunk[(packed.shape[0], GROUP // block_n)](
        packed, k, v, packed.stride(0), GROUP * HEAD_DIM,
        D=HEAD_DIM, G=GROUP, BN=block_n,
        K_PACKED_OFFSET=K_PACKED_OFFSET, K_S_COL_OFFSET=K_S_COL_OFFSET,
        K_ZP_OFFSET=K_ZP_OFFSET, K_S_ROW_OFFSET=K_S_ROW_OFFSET,
        V_PACKED_OFFSET=V_PACKED_OFFSET, V_S_COL_OFFSET=V_S_COL_OFFSET,
        V_S_ROW_OFFSET=V_S_ROW_OFFSET, V_ZP_OFFSET=V_ZP_OFFSET,
    )
    return k, v

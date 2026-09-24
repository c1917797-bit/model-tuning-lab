"""Opt-in Ascend primitives for the pinned KVarN K4/V2 experiment."""

from .tile_dequant import dequantize_packed_tiles

__all__ = ["dequantize_packed_tiles"]

"""Qwen3.8 ModelOpt mixed-precision adapters for Ascend."""

from .adapter import QUANTIZATION_NAME, register

__all__ = ["QUANTIZATION_NAME", "register"]


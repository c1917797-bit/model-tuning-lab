"""Reusable paper-to-Ascend reference components."""

from .dynamic_moe import dynamic_top_p_select, fixed_top_k_select

__all__ = ["dynamic_top_p_select", "fixed_top_k_select"]

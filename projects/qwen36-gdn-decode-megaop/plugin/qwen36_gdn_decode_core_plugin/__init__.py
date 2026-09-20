"""Opt-in vLLM plugin for the Qwen3.6 Ascend GDN decode core."""

from .patch import register

__all__ = ["register"]

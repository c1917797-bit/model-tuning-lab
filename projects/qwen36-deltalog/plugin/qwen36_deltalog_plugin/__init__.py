"""Explicit opt-in DeltaLog adapter for Qwen3.6 on vLLM-Ascend."""

from .patch import register

__all__ = ["register"]

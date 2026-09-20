"""vLLM general-plugin entry point for the SSM TP Ascend workstream."""

from .runtime import register

__all__ = ["register"]
__version__ = "0.1.0"

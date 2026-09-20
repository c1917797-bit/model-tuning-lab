"""vLLM general-plugin entry point for sparse prefix placement."""

from .runtime import register

__all__ = ["register"]
__version__ = "0.1.0"

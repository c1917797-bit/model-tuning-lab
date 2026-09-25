"""Opt-in Ada-KV Ascend adaptation; no runtime patch is installed by import."""

from .live_probe import register

__all__ = ["register"]

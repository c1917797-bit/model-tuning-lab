"""MXR plugin entry point."""

from __future__ import annotations

from .config import MxrConfig


def register() -> None:
    config = MxrConfig.from_env()
    if not config.enabled:
        return
    from .runtime import install

    install(config)


__all__ = ["register"]

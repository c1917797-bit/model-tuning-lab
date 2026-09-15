"""DASC plugin entry point."""

from __future__ import annotations

from .config import DascConfig


def register() -> None:
    config = DascConfig.from_env()
    if not config.enabled:
        return
    from .monkeypatch import install

    install(config)


__all__ = ["register"]

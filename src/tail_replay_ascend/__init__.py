"""Opt-in Tail-Replay research plugin for the pinned Ascend runtime."""

from __future__ import annotations

import logging

from .config import TailReplayConfig, get_config


__version__ = "0.1.0"
logger = logging.getLogger(__name__)


def register() -> None:
    config = get_config()
    if not config.enable:
        return
    from .diagnostics import emit_event
    from .runtime_patch import install_runtime_patch

    emit_event(
        "plugin_build_active",
        component="plugin",
        version=__version__,
        module=__file__,
        mode=config.mode,
    )
    install_runtime_patch(config)
    logger.info(
        "Tail-Replay Ascend plugin active: version=%s mode=%s module=%s",
        __version__,
        config.mode,
        __file__,
    )


__all__ = ["TailReplayConfig", "get_config", "register"]

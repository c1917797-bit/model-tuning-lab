"""SlimInfer Ascend planning primitives and opt-in vLLM plugin entry point."""

from __future__ import annotations

import logging

from .config import SlimInferConfig, get_config
from .planner import (
    LayerPruningSpec,
    aggregate_rank_scores,
    build_layer_plan,
    prompt_block_ids,
    selection_digest,
    select_active_blocks,
)

__version__ = "0.1.0"

logger = logging.getLogger(__name__)


def register() -> None:
    """Install the disabled-by-default runtime canary through vLLM's plugin API."""

    config = get_config()
    if not config.enable:
        return

    from .diagnostics import emit_event
    from .runtime_patch import install_model_patch

    emit_event(
        "plugin_build_active",
        component="plugin",
        version=__version__,
        module=__file__,
        mode=config.mode,
    )
    install_model_patch(config)
    logger.info(
        "SlimInfer Ascend plugin active: version=%s mode=%s module=%s",
        __version__,
        config.mode,
        __file__,
    )


__all__ = [
    "LayerPruningSpec",
    "SlimInferConfig",
    "aggregate_rank_scores",
    "build_layer_plan",
    "get_config",
    "prompt_block_ids",
    "register",
    "selection_digest",
    "select_active_blocks",
]

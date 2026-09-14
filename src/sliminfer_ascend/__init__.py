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
from .stream_contract import (
    CompactPrefillLayout,
    HiddenStateRestorationPlan,
    RequestPruningState,
    build_hidden_state_restoration_plan,
    build_whole_prompt_layout,
    decode_full_attention_slots,
    full_attention_physical_slot,
    prefill_full_attention_slots,
)
from .shadow_score import (
    SemanticRequestScores,
    remap_compact_block_scores,
    semantic_block_scores,
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
    if config.mode in {"selection-shadow", "semantic-prefill"}:
        from .attention_shadow import install_attention_patch

        install_attention_patch(config)
    logger.info(
        "SlimInfer Ascend plugin active: version=%s mode=%s module=%s",
        __version__,
        config.mode,
        __file__,
    )


__all__ = [
    "LayerPruningSpec",
    "CompactPrefillLayout",
    "HiddenStateRestorationPlan",
    "RequestPruningState",
    "SlimInferConfig",
    "SemanticRequestScores",
    "aggregate_rank_scores",
    "build_layer_plan",
    "build_hidden_state_restoration_plan",
    "build_whole_prompt_layout",
    "decode_full_attention_slots",
    "full_attention_physical_slot",
    "get_config",
    "prompt_block_ids",
    "prefill_full_attention_slots",
    "register",
    "remap_compact_block_scores",
    "selection_digest",
    "semantic_block_scores",
    "select_active_blocks",
]

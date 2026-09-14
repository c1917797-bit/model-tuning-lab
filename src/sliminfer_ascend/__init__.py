"""Portable planning primitives for the SlimInfer Ascend workstream."""

from .planner import (
    LayerPruningSpec,
    aggregate_rank_scores,
    build_layer_plan,
    prompt_block_ids,
    selection_digest,
    select_active_blocks,
)

__all__ = [
    "LayerPruningSpec",
    "aggregate_rank_scores",
    "build_layer_plan",
    "prompt_block_ids",
    "selection_digest",
    "select_active_blocks",
]

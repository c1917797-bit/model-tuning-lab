"""Fail-closed runtime adapter that changes only HYPIC prefix placement."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from .planner import PlacementPlan

logger = logging.getLogger(__name__)
_INSTALLED = False


def _enabled() -> bool:
    return os.environ.get("VLLM_ASCEND_SPARSE_PREFIX_ENABLE", "0") == "1"


def _load_plan(path: str) -> PlacementPlan:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema") != "sparse-prefix-placement/v1":
        raise RuntimeError("unsupported sparse-prefix placement schema")
    plan = PlacementPlan(
        positions=tuple(int(value) for value in payload["positions"]),
        checkpoint_budget=int(payload["checkpoint_budget"]),
        block_size=int(payload["block_size"]),
        max_length=int(payload["max_length"]),
    )
    plan.validate()
    return plan


def register() -> None:
    global _INSTALLED
    if not _enabled() or _INSTALLED:
        return
    if os.environ.get("VLLM_ASCEND_HYPIC_ENABLE", "0") != "1":
        raise RuntimeError(
            "Sparse Prefix Ascend requires the validated HYPIC state/KV runtime"
        )
    path = os.environ.get("VLLM_ASCEND_SPARSE_PREFIX_PLAN")
    if not path or not Path(path).is_absolute():
        raise RuntimeError(
            "VLLM_ASCEND_SPARSE_PREFIX_PLAN must be an absolute plan path"
        )
    plan = _load_plan(path)

    from hypic_vllm_ascend.patches import scheduler as hypic_scheduler

    original = hypic_scheduler._candidate_prefix_ends_for_request
    if getattr(original, "_sparse_prefix_ascend_wrapped", False):
        _INSTALLED = True
        return

    def candidate_prefix_ends(
        request,
        token_ids,
        config,
        *,
        block_size: int,
        segments=None,
    ):
        # Retain HYPIC's eligibility and upper-bound semantics, then replace
        # only the placement policy with the frozen paper/control plan.
        eligible = original(
            request,
            token_ids,
            config,
            block_size=block_size,
            segments=segments,
        )
        if not eligible:
            return ()
        if block_size != plan.block_size:
            raise RuntimeError(
                "sparse-prefix plan/runtime block-size mismatch: "
                f"plan={plan.block_size}, runtime={block_size}"
            )
        upper = max(int(value) for value in eligible)
        minimum = int(getattr(config, "min_rewrite_tokens", 0) or 0)
        selected = tuple(
            position
            for position in reversed(plan.positions)
            if minimum <= position <= upper and position < len(token_ids)
        )
        return selected

    candidate_prefix_ends._sparse_prefix_ascend_wrapped = True
    candidate_prefix_ends._sparse_prefix_original = original
    hypic_scheduler._candidate_prefix_ends_for_request = candidate_prefix_ends
    _INSTALLED = True
    logger.info(
        "Sparse Prefix Ascend placement active: positions=%s budget=%d block=%d",
        plan.positions,
        plan.checkpoint_budget,
        plan.block_size,
    )

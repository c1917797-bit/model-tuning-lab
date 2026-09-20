"""Fail-closed runtime adapter that changes only HYPIC prefix placement."""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

from .planner import PlacementPlan

logger = logging.getLogger(__name__)
_INSTALLED = False


def _emit_evidence(event: str, **fields) -> None:
    path = os.environ.get(
        "VLLM_ASCEND_SPARSE_PREFIX_EVIDENCE_FILE",
        os.environ.get("VLLM_ASCEND_HYPIC_EVIDENCE_FILE", ""),
    )
    if not path:
        return
    payload = {
        "schema": 1,
        "event": event,
        "component": "sparse_prefix_ascend",
        "pid": os.getpid(),
        "ppid": os.getppid(),
        "time_ns": time.time_ns(),
        **fields,
    }
    encoded = (
        json.dumps(payload, ensure_ascii=True, sort_keys=True) + "\n"
    ).encode("utf-8")
    descriptor = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, encoded)
    finally:
        os.close(descriptor)


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
    _emit_evidence(
        "sparse_prefix_plan_loaded",
        positions=list(plan.positions),
        checkpoint_budget=plan.checkpoint_budget,
        block_size=plan.block_size,
        max_length=plan.max_length,
    )

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
        _emit_evidence(
            "sparse_prefix_candidates_selected",
            request_id=getattr(request, "request_id", None),
            prompt_tokens=len(token_ids),
            runtime_block_size=block_size,
            original_candidates=list(eligible),
            original_upper=upper,
            selected=list(selected),
            minimum_rewrite_tokens=minimum,
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

"""Deterministic, device-independent SlimInfer block planning.

This module deliberately contains no framework or device integration.  It
defines the request-local selection contract that a later vLLM-Ascend hook must
implement and prove on NPU.  CPU tests are preconditions, not NPU evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True, order=True)
class LayerPruningSpec:
    """One zero-based pruning boundary and its target prompt-token budget."""

    layer_index: int
    keep_tokens: int

    def __post_init__(self) -> None:
        if self.layer_index < 0:
            raise ValueError("layer_index must be non-negative")
        if self.keep_tokens <= 0:
            raise ValueError("keep_tokens must be positive")


def prompt_block_ids(prompt_tokens: int, block_size: int = 64) -> tuple[int, ...]:
    """Return stable absolute block IDs covering a prompt."""

    if prompt_tokens <= 0:
        raise ValueError("prompt_tokens must be positive")
    if block_size <= 0:
        raise ValueError("block_size must be positive")
    return tuple(range(math.ceil(prompt_tokens / block_size)))


def aggregate_rank_scores(
    rank_scores: Sequence[Mapping[int, float]],
) -> dict[int, float]:
    """Mean-reduce TP-local block scores with a fail-closed identity check.

    A real NPU implementation must use a collective over the score vector
    before top-k.  Selecting independently on sharded heads is invalid even
    when every rank uses the same source code.
    """

    if not rank_scores:
        raise ValueError("at least one rank score map is required")
    expected = set(rank_scores[0])
    if not expected:
        raise ValueError("score maps must not be empty")
    for rank, scores in enumerate(rank_scores[1:], start=1):
        if set(scores) != expected:
            raise ValueError(f"rank {rank} block IDs differ from rank 0")
    return {
        block_id: math.fsum(float(scores[block_id]) for scores in rank_scores)
        / len(rank_scores)
        for block_id in sorted(expected)
    }


def select_active_blocks(
    current_active_blocks: Iterable[int],
    block_scores: Mapping[int, float],
    *,
    keep_tokens: int,
    block_size: int = 64,
    keep_sink_and_recent: bool = True,
) -> tuple[int, ...]:
    """Select a deterministic subset of the currently active prompt blocks."""

    if keep_tokens <= 0:
        raise ValueError("keep_tokens must be positive")
    if block_size <= 0:
        raise ValueError("block_size must be positive")
    active = tuple(sorted(set(current_active_blocks)))
    if not active:
        raise ValueError("current_active_blocks must not be empty")
    missing = [block_id for block_id in active if block_id not in block_scores]
    if missing:
        raise ValueError(f"missing scores for active blocks: {missing[:8]}")
    non_finite = [
        block_id
        for block_id in active
        if not math.isfinite(float(block_scores[block_id]))
    ]
    if non_finite:
        raise ValueError(f"non-finite scores for active blocks: {non_finite[:8]}")

    keep_count = min(len(active), math.ceil(keep_tokens / block_size))
    if keep_count == len(active):
        return active

    # Score descending, absolute block ID ascending for deterministic ties.
    ranked = sorted(active, key=lambda block_id: (-float(block_scores[block_id]), block_id))
    mandatory = {active[0], active[-1]} if keep_sink_and_recent else set()
    if len(mandatory) >= keep_count:
        return tuple(sorted(mandatory))

    selected = set(mandatory)
    for block_id in ranked:
        selected.add(block_id)
        if len(selected) == keep_count:
            break
    return tuple(sorted(selected))


def build_layer_plan(
    prompt_tokens: int,
    layer_specs: Sequence[LayerPruningSpec],
    scores_by_layer: Mapping[int, Mapping[int, float]],
    *,
    block_size: int = 64,
) -> dict[int, tuple[int, ...]]:
    """Build monotonically shrinking active sets at the declared boundaries."""

    if tuple(layer_specs) != tuple(sorted(layer_specs)):
        raise ValueError("layer_specs must be strictly ordered")
    if len({spec.layer_index for spec in layer_specs}) != len(layer_specs):
        raise ValueError("layer_specs contain duplicate layer indices")
    active = prompt_block_ids(prompt_tokens, block_size)
    result: dict[int, tuple[int, ...]] = {}
    for spec in layer_specs:
        if spec.layer_index not in scores_by_layer:
            raise ValueError(f"missing scores for layer {spec.layer_index}")
        active = select_active_blocks(
            active,
            scores_by_layer[spec.layer_index],
            keep_tokens=spec.keep_tokens,
            block_size=block_size,
        )
        result[spec.layer_index] = active
    return result


def selection_digest(
    request_id: str,
    layer_active_blocks: Mapping[int, Sequence[int]],
) -> str:
    """Canonical digest used to prove TP-rank agreement."""

    payload = {
        "request_id": request_id,
        "layers": [
            {"layer": int(layer), "blocks": sorted({int(block) for block in blocks})}
            for layer, blocks in sorted(layer_active_blocks.items())
        ],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(canonical).hexdigest()

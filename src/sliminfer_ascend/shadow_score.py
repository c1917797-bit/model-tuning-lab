"""Faithful, read-only SlimInfer semantic block scoring.

This module implements the paper's selection score without changing model
outputs or KV-cache state. It is intended for the first Ascend shadow canary,
not for performance measurement: a runtime hook may temporarily duplicate Q/K
work to obtain the tensors consumed here.

The important distributed invariant is that tensor-parallel head sums are
reduced for every semantic unit before taking the maximum unit score inside a
block. Max-reducing rank-local block scores is not equivalent and can select a
different active set.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Callable, Mapping, Sequence


ReduceSum = Callable[[Any], Any | None]


@dataclass(frozen=True)
class SemanticRequestScores:
    """Request-local semantic-unit and block scores."""

    request_index: int
    token_start: int
    token_end: int
    unit_scores: tuple[float, ...]
    block_scores: dict[int, float]


def remap_compact_block_scores(
    compact_block_scores: Mapping[int, float],
    active_absolute_blocks: Sequence[int],
    *,
    prompt_tokens: int,
    compact_tokens: int,
    block_size: int = 64,
) -> dict[int, float]:
    """Map compact score ordinals back to stable prompt block identities.

    A semantic pruning stage concatenates complete active prompt blocks.  The
    scorer necessarily labels those rows with compact ordinals 0..N-1, while
    the planner must continue using the original prompt's absolute block IDs.
    Validate both identities and the exact compact row count before remapping.
    """

    if prompt_tokens <= 0:
        raise ValueError("prompt_tokens must be positive")
    if compact_tokens <= 0:
        raise ValueError("compact_tokens must be positive")
    if block_size <= 0:
        raise ValueError("block_size must be positive")

    absolute = tuple(int(block) for block in active_absolute_blocks)
    if not absolute:
        raise ValueError("active_absolute_blocks must not be empty")
    if absolute != tuple(sorted(set(absolute))):
        raise ValueError(
            "active_absolute_blocks must be strictly increasing and unique"
        )

    total_blocks = math.ceil(prompt_tokens / block_size)
    invalid = [block for block in absolute if block < 0 or block >= total_blocks]
    if invalid:
        raise ValueError(f"absolute block IDs are outside the prompt: {invalid[:8]}")

    expected_compact_tokens = sum(
        min(block_size, prompt_tokens - block * block_size) for block in absolute
    )
    if compact_tokens != expected_compact_tokens:
        raise ValueError(
            "compact token rows do not exactly cover the declared active blocks: "
            f"expected {expected_compact_tokens}, got {compact_tokens}"
        )

    compact_ids = set(int(block) for block in compact_block_scores)
    expected_ids = set(range(len(absolute)))
    if compact_ids != expected_ids:
        raise ValueError(
            "compact score block IDs must be contiguous ordinals 0..N-1"
        )
    non_finite = [
        block
        for block, score in compact_block_scores.items()
        if not math.isfinite(float(score))
    ]
    if non_finite:
        raise ValueError(f"compact block scores must be finite: {non_finite[:8]}")

    return {
        absolute[compact_id]: float(compact_block_scores[compact_id])
        for compact_id in range(len(absolute))
    }


def _validate_start_locs(start_locs: Sequence[int], token_count: int) -> tuple[int, ...]:
    starts = tuple(int(value) for value in start_locs)
    if len(starts) < 2:
        raise ValueError("request_start_locs must contain at least start and end")
    if starts[0] != 0 or starts[-1] != token_count:
        raise ValueError(
            "request_start_locs must start at 0 and end at the Q/K token count"
        )
    if any(left >= right for left, right in zip(starts, starts[1:])):
        raise ValueError("request_start_locs must be strictly increasing")
    return starts


def semantic_block_scores(
    q: Any,
    k: Any,
    request_start_locs: Sequence[int],
    *,
    block_size: int = 64,
    unit_size: int = 8,
    query_window: int = 4,
    reduce_sum: ReduceSum | None = None,
    global_query_heads: int | None = None,
) -> tuple[SemanticRequestScores, ...]:
    """Compute SlimInfer scores for flattened whole-prompt Q/K tensors.

    q and k have shapes [T, Hq_local, D] and [T, Hkv_local, D].
    request_start_locs contains cumulative request boundaries including 0 and T.
    reduce_sum receives one flat vector of per-unit local head sums and may
    return the reduced tensor or reduce its input in-place and return None.

    This first scorer intentionally accepts only complete, compact whole-prompt
    rows. Later pruning stages must provide an explicit absolute-block mapping
    rather than pretending compact row ordinals are original block identities.
    """

    try:
        import torch
    except ImportError as exc:  # pragma: no cover - target runtime owns torch
        raise RuntimeError("semantic_block_scores requires PyTorch") from exc

    if block_size <= 0 or unit_size <= 0 or query_window <= 0:
        raise ValueError("block_size, unit_size, and query_window must be positive")
    if not isinstance(q, torch.Tensor) or not isinstance(k, torch.Tensor):
        raise TypeError("q and k must be torch.Tensor instances")
    if q.ndim != 3 or k.ndim != 3:
        raise ValueError("q and k must have shape [tokens, heads, head_dim]")
    if q.shape[0] != k.shape[0] or q.shape[2] != k.shape[2]:
        raise ValueError("q and k token counts and head dimensions must match")
    if q.device != k.device:
        raise ValueError("q and k must be on the same device")
    if not q.is_floating_point() or not k.is_floating_point():
        raise ValueError("q and k must use floating-point dtypes")

    token_count, local_query_heads, _ = (int(value) for value in q.shape)
    local_kv_heads = int(k.shape[1])
    if local_query_heads <= 0 or local_kv_heads <= 0:
        raise ValueError("q and k must contain at least one head")
    if local_query_heads % local_kv_heads:
        raise ValueError("local query heads must be divisible by local KV heads")
    starts = _validate_start_locs(request_start_locs, token_count)

    if global_query_heads is None:
        if reduce_sum is not None:
            raise ValueError("global_query_heads is required with reduce_sum")
        global_query_heads = local_query_heads
    if global_query_heads <= 0:
        raise ValueError("global_query_heads must be positive")
    if reduce_sum is None and global_query_heads != local_query_heads:
        raise ValueError(
            "global_query_heads must equal local query heads without reduce_sum"
        )
    if global_query_heads < local_query_heads:
        raise ValueError("global_query_heads cannot be smaller than local query heads")

    # This synchronization is intentional in the correctness-only shadow path:
    # non-finite inputs must fail closed before emitting a selection digest.
    if not bool(torch.isfinite(q).all().item()) or not bool(torch.isfinite(k).all().item()):
        raise ValueError("q and k must contain only finite values")

    repeat_factor = local_query_heads // local_kv_heads
    local_unit_sums: list[Any] = []
    unit_locations: list[tuple[int, int]] = []
    request_unit_counts: list[int] = []

    for request_index, (start, end) in enumerate(zip(starts, starts[1:])):
        query_start = max(start, end - query_window)
        query = q[query_start:end].float().mean(dim=0)
        unit_count = 0
        for block_start in range(start, end, block_size):
            block_end = min(end, block_start + block_size)
            block_id = (block_start - start) // block_size
            for unit_start in range(block_start, block_end, unit_size):
                unit_end = min(block_end, unit_start + unit_size)
                representative_key = k[unit_start:unit_end].float().mean(dim=0)
                if repeat_factor != 1:
                    representative_key = representative_key.repeat_interleave(
                        repeat_factor, dim=0
                    )
                local_unit_sums.append((query * representative_key).sum())
                unit_locations.append((request_index, block_id))
                unit_count += 1
        request_unit_counts.append(unit_count)

    local_scores = torch.stack(local_unit_sums)
    if reduce_sum is not None:
        reduced = reduce_sum(local_scores)
        if reduced is not None:
            local_scores = reduced
    if not isinstance(local_scores, torch.Tensor):
        raise TypeError("reduce_sum must return a torch.Tensor or None")
    if tuple(local_scores.shape) != (len(unit_locations),):
        raise ValueError("reduce_sum changed the semantic-unit score vector shape")
    if not bool(torch.isfinite(local_scores).all().item()):
        raise ValueError("reduced semantic-unit scores must be finite")

    unit_scores = (local_scores / float(global_query_heads)).detach().cpu().tolist()
    results: list[SemanticRequestScores] = []
    cursor = 0
    for request_index, ((start, end), unit_count) in enumerate(
        zip(zip(starts, starts[1:]), request_unit_counts)
    ):
        request_scores = tuple(
            float(value) for value in unit_scores[cursor : cursor + unit_count]
        )
        block_scores: dict[int, float] = {}
        for offset, score in enumerate(request_scores):
            _, block_id = unit_locations[cursor + offset]
            block_scores[block_id] = max(block_scores.get(block_id, -math.inf), score)
        results.append(
            SemanticRequestScores(
                request_index=request_index,
                token_start=start,
                token_end=end,
                unit_scores=request_scores,
                block_scores=block_scores,
            )
        )
        cursor += unit_count
    return tuple(results)

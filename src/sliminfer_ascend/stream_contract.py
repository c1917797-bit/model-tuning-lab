"""Device-independent contract for a compact SlimInfer token stream.

The functions here describe identities that a later vLLM-Ascend runtime patch
must preserve. They do not execute pruning on NPU and are not performance or
correctness evidence for the model.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import math
from typing import Sequence


@dataclass(frozen=True)
class RequestPruningState:
    """Per-request prompt and compact-cache identity.

    active_blocks use SlimInfer's pruning block size. Full-attention KV cache
    blocks may use a different size and are handled separately.
    """

    prompt_tokens: int
    active_blocks: tuple[int, ...]
    pruning_block_size: int = 64
    generated_tokens: int = 0

    def __post_init__(self) -> None:
        if self.prompt_tokens <= 0:
            raise ValueError("prompt_tokens must be positive")
        if self.pruning_block_size <= 0:
            raise ValueError("pruning_block_size must be positive")
        if self.generated_tokens < 0:
            raise ValueError("generated_tokens must be non-negative")
        blocks = tuple(sorted(set(self.active_blocks)))
        if blocks != self.active_blocks:
            raise ValueError("active_blocks must be sorted and unique")
        if not blocks:
            raise ValueError("active_blocks must not be empty")
        max_block = math.ceil(self.prompt_tokens / self.pruning_block_size) - 1
        if blocks[0] != 0:
            raise ValueError("the sink block must remain active")
        if any(block < 0 or block > max_block for block in blocks):
            raise ValueError("active_blocks contain an out-of-range block")

    @property
    def active_prompt_token_ids(self) -> tuple[int, ...]:
        token_ids: list[int] = []
        for block in self.active_blocks:
            start = block * self.pruning_block_size
            stop = min(start + self.pruning_block_size, self.prompt_tokens)
            token_ids.extend(range(start, stop))
        return tuple(token_ids)

    @property
    def active_prompt_tokens(self) -> int:
        return len(self.active_prompt_token_ids)

    @property
    def next_decode_absolute_position(self) -> int:
        """RoPE/model position of the next response token."""

        return self.prompt_tokens + self.generated_tokens

    @property
    def next_decode_compact_cache_position(self) -> int:
        """Logical full-attention KV position of the next response token."""

        return self.active_prompt_tokens + self.generated_tokens

    def advance_decode(self, count: int = 1) -> "RequestPruningState":
        if count <= 0:
            raise ValueError("count must be positive")
        return replace(self, generated_tokens=self.generated_tokens + count)


@dataclass(frozen=True)
class CompactPrefillLayout:
    """Flattened prefill identities for an eager whole-prompt canary."""

    gather_indices: tuple[int, ...]
    absolute_positions: tuple[int, ...]
    query_start_loc: tuple[int, ...]
    request_indices: tuple[int, ...]
    compact_cache_positions: tuple[int, ...]


def build_whole_prompt_layout(
    states: Sequence[RequestPruningState],
    dense_query_start_loc: Sequence[int],
    computed_tokens: Sequence[int],
) -> CompactPrefillLayout:
    """Build compact rows while rejecting partial/chunked prompt prefills.

    A first semantic canary must see each complete prompt in one model forward.
    Otherwise earlier chunks have already crossed later layers before a
    full-prompt pruning decision exists.
    """

    if not states:
        raise ValueError("at least one request state is required")
    if len(dense_query_start_loc) != len(states) + 1:
        raise ValueError("dense_query_start_loc must have one sentinel per batch")
    if len(computed_tokens) != len(states):
        raise ValueError("computed_tokens must match the request count")
    starts = tuple(int(value) for value in dense_query_start_loc)
    if starts[0] != 0 or any(
        right <= left for left, right in zip(starts, starts[1:])
    ):
        raise ValueError("dense_query_start_loc must start at zero and increase")

    gather: list[int] = []
    positions: list[int] = []
    request_indices: list[int] = []
    compact_positions: list[int] = []
    compact_starts = [0]
    for request_index, state in enumerate(states):
        scheduled = starts[request_index + 1] - starts[request_index]
        if int(computed_tokens[request_index]) != 0 or scheduled != state.prompt_tokens:
            raise RuntimeError(
                "SlimInfer whole-prompt canary rejects partial or resumed prefill"
            )
        token_ids = state.active_prompt_token_ids
        gather.extend(starts[request_index] + token_id for token_id in token_ids)
        positions.extend(token_ids)
        request_indices.extend([request_index] * len(token_ids))
        compact_positions.extend(range(len(token_ids)))
        compact_starts.append(len(gather))

    return CompactPrefillLayout(
        gather_indices=tuple(gather),
        absolute_positions=tuple(positions),
        query_start_loc=tuple(compact_starts),
        request_indices=tuple(request_indices),
        compact_cache_positions=tuple(compact_positions),
    )


def full_attention_physical_slot(
    block_table: Sequence[int],
    *,
    kv_block_size: int,
    compact_cache_position: int,
) -> int:
    """Map a compact logical KV position into an allocated physical slot."""

    if kv_block_size <= 0:
        raise ValueError("kv_block_size must be positive")
    if compact_cache_position < 0:
        raise ValueError("compact_cache_position must be non-negative")
    block_offset, within_block = divmod(compact_cache_position, kv_block_size)
    if block_offset >= len(block_table):
        raise ValueError("block table is too short for compact cache position")
    physical_block = int(block_table[block_offset])
    if physical_block < 0:
        raise ValueError("block table contains an invalid physical block")
    return physical_block * kv_block_size + within_block


def prefill_full_attention_slots(
    states: Sequence[RequestPruningState],
    block_tables: Sequence[Sequence[int]],
    *,
    kv_block_size: int,
) -> tuple[int, ...]:
    """Return physical KV slots for compact prompt rows in flattened order."""

    if len(states) != len(block_tables):
        raise ValueError("block_tables must match the request count")
    return tuple(
        full_attention_physical_slot(
            block_table,
            kv_block_size=kv_block_size,
            compact_cache_position=compact_position,
        )
        for state, block_table in zip(states, block_tables)
        for compact_position in range(state.active_prompt_tokens)
    )


def decode_full_attention_slots(
    states: Sequence[RequestPruningState],
    block_tables: Sequence[Sequence[int]],
    *,
    kv_block_size: int,
) -> tuple[int, ...]:
    """Return each request's physical slot for its next response token."""

    if len(states) != len(block_tables):
        raise ValueError("block_tables must match the request count")
    return tuple(
        full_attention_physical_slot(
            block_table,
            kv_block_size=kv_block_size,
            compact_cache_position=state.next_decode_compact_cache_position,
        )
        for state, block_table in zip(states, block_tables)
    )

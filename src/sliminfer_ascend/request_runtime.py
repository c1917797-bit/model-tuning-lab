"""Request identity and persistent state for the bounded SlimInfer stream port.

The official implementation keeps hidden-state and KV identities across
generation steps.  vLLM-Ascend owns those identities in the model runner, so
the plugin captures them without modifying the framework source.  This module
is intentionally fail-closed and currently permits one request per forward.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
import threading
from typing import Any, Iterator


@dataclass(frozen=True)
class RunnerRequestIdentity:
    req_id: str
    prompt_tokens: int
    num_computed_tokens: int
    scheduled_tokens: int
    block_tables: tuple[tuple[int, ...], ...]
    kv_block_sizes: tuple[int, ...]


@dataclass(frozen=True)
class RunnerForwardIdentity:
    requests: tuple[RunnerRequestIdentity, ...]


@dataclass
class HiddenStateBlock:
    """The two tensors required to resume one vLLM fused-residual layer."""

    hidden_states: Any
    residual: Any


@dataclass
class PersistentRequestState:
    req_id: str
    prompt_tokens: int
    block_tables: tuple[tuple[int, ...], ...]
    kv_block_sizes: tuple[int, ...]
    active_blocks_after_layer: dict[int, tuple[int, ...]] = field(
        default_factory=dict
    )
    hidden_state_cache: dict[tuple[int, int], HiddenStateBlock] = field(
        default_factory=dict
    )
    generated_tokens: int = 0


_forward_local = threading.local()
_registry_lock = threading.Lock()
_request_registry: dict[str, PersistentRequestState] = {}


def _position_token_count(positions: Any) -> int:
    shape = getattr(positions, "shape", None)
    if shape is None:
        raise RuntimeError("runner positions are unavailable")
    if len(shape) == 1:
        return int(shape[0])
    if len(shape) == 2:
        return int(shape[1])
    raise RuntimeError("runner positions must be [tokens] or [channels, tokens]")


def _capture_block_tables(input_batch: Any, request_index: int):
    multi = getattr(input_batch, "block_table", None)
    tables = getattr(multi, "block_tables", None)
    if not isinstance(tables, list) or not tables:
        raise RuntimeError("runner block-table groups are unavailable")
    rows: list[tuple[int, ...]] = []
    sizes: list[int] = []
    for table in tables:
        counts = getattr(table, "num_blocks_per_row", None)
        get_array = getattr(table, "get_numpy_array", None)
        if counts is None or not callable(get_array):
            raise RuntimeError("runner block-table group has an unknown layout")
        count = int(counts[request_index])
        if count <= 0:
            raise RuntimeError("runner request has no allocated KV blocks")
        array = get_array()
        rows.append(tuple(int(value) for value in array[request_index, :count]))
        block_size = int(getattr(table, "block_size", 0))
        if block_size <= 0:
            raise RuntimeError("runner KV block size is invalid")
        sizes.append(block_size)
    return tuple(rows), tuple(sizes)


def capture_runner_forward_identity(
    runner: Any, positions: Any
) -> RunnerForwardIdentity:
    input_batch = getattr(runner, "input_batch", None)
    requests = getattr(runner, "requests", None)
    if input_batch is None or not isinstance(requests, dict):
        raise RuntimeError("NPUModelRunner request state is unavailable")
    req_ids = tuple(getattr(input_batch, "req_ids", ()))
    if len(req_ids) != 1:
        raise RuntimeError("SlimInfer semantic-stream currently requires one request")
    req_id = req_ids[0]
    request = requests.get(req_id)
    if request is None:
        raise RuntimeError("runner request identity is missing")
    prompt_tokens = int(getattr(request, "num_prompt_tokens", 0))
    if prompt_tokens <= 0:
        raise RuntimeError("runner prompt length is invalid")
    computed = getattr(input_batch, "num_computed_tokens_cpu", None)
    if computed is None:
        raise RuntimeError("runner computed-token state is unavailable")
    block_tables, block_sizes = _capture_block_tables(input_batch, 0)
    return RunnerForwardIdentity(
        requests=(
            RunnerRequestIdentity(
                req_id=str(req_id),
                prompt_tokens=prompt_tokens,
                num_computed_tokens=int(computed[0]),
                scheduled_tokens=_position_token_count(positions),
                block_tables=block_tables,
                kv_block_sizes=block_sizes,
            ),
        )
    )


@contextmanager
def runner_forward_scope(
    runner: Any, positions: Any
) -> Iterator[RunnerForwardIdentity]:
    if getattr(_forward_local, "identity", None) is not None:
        raise RuntimeError("nested SlimInfer runner scopes are unsupported")
    identity = capture_runner_forward_identity(runner, positions)
    _forward_local.identity = identity
    try:
        yield identity
    finally:
        del _forward_local.identity


def current_runner_forward_identity() -> RunnerForwardIdentity:
    identity = getattr(_forward_local, "identity", None)
    if identity is None:
        raise RuntimeError("SlimInfer model forward ran outside its runner scope")
    return identity


def put_request_state(state: PersistentRequestState) -> None:
    with _registry_lock:
        _request_registry[state.req_id] = state


def get_request_state(req_id: str) -> PersistentRequestState:
    with _registry_lock:
        state = _request_registry.get(req_id)
    if state is None:
        raise RuntimeError(f"SlimInfer state is missing for request {req_id!r}")
    return state


def discard_request_state(req_id: str) -> None:
    with _registry_lock:
        _request_registry.pop(req_id, None)


def clear_request_registry_for_test() -> None:
    with _registry_lock:
        _request_registry.clear()

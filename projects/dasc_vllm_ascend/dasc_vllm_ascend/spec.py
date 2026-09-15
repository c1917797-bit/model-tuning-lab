"""DASC transformation of vLLM Mamba cache specifications."""

from __future__ import annotations

from dataclasses import replace
from math import prod
from typing import Any


class CompactSpecError(ValueError):
    pass


def compact_mamba_spec(
    spec: Any,
    *,
    state_index: int,
    head_axis: int,
    retained_heads: int,
) -> Any:
    """Return a per-layer spec that owns only physically retained heads.

    page_size_padded must be cleared: leaving the dense global padding in
    place would make the new shape accounting cosmetic rather than physical.
    The native operator is not allowed to consume the resulting cache tensor
    directly; the runtime bridge expands it into a dense active workspace.
    """
    shapes = tuple(tuple(shape) for shape in spec.shapes)
    if not 0 <= state_index < len(shapes):
        raise CompactSpecError("state_index is outside Mamba spec shapes")
    state_shape = shapes[state_index]
    if not 0 <= head_axis < len(state_shape):
        raise CompactSpecError("head_axis is outside selected state shape")
    total_heads = state_shape[head_axis]
    if not 0 < retained_heads <= total_heads:
        raise CompactSpecError("retained_heads must be in (0, total_heads]")
    if len(spec.dtypes) != len(shapes):
        raise CompactSpecError("Mamba shapes and dtypes have different lengths")

    compact_state = list(state_shape)
    compact_state[head_axis] = retained_heads
    compact_shapes = list(shapes)
    compact_shapes[state_index] = tuple(compact_state)
    compact = replace(
        spec,
        shapes=tuple(compact_shapes),
        page_size_padded=None,
    )
    if compact.page_size_bytes >= spec.page_size_bytes and retained_heads < total_heads:
        raise CompactSpecError("compact Mamba spec did not reduce physical page bytes")
    return compact


def state_payload_elements(spec: Any) -> int:
    """Return unpadded state elements for audit reporting."""
    return sum(prod(shape) for shape in spec.shapes)

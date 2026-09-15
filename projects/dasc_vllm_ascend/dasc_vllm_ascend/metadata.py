"""Fail-closed Ascend GDN metadata remapping for dense active slots."""

from __future__ import annotations

from dataclasses import fields, is_dataclass, replace
from typing import Any

from .compact import ActiveSlotPlan, build_active_slot_plan


ASCEND_GDN_STATE_INDEX_PATHS = (
    ("non_spec_state_indices_tensor",),
    ("spec_state_indices_tensor",),
    ("prefill_state_indices",),
    ("non_spec_prefill_metadata", "causal_conv1d", "cache_indices"),
    ("non_spec_decode_metadata", "causal_conv1d", "cache_indices"),
    ("spec_decode_metadata", "spec_causal_conv1d", "cache_indices"),
)


def _get_path(root: Any, path: tuple[str, ...]) -> Any | None:
    current = root
    for name in path:
        if current is None or not hasattr(current, name):
            return None
        current = getattr(current, name)
    return current


def _replace_path(root: Any, path: tuple[str, ...], value: Any) -> Any:
    if not is_dataclass(root):
        raise TypeError(f"metadata node for {'.'.join(path)} is not a dataclass")
    if len(path) == 1:
        return replace(root, **{path[0]: value})
    child = getattr(root, path[0])
    if child is None:
        raise ValueError(f"metadata path {'.'.join(path)} disappeared")
    return replace(root, **{path[0]: _replace_path(child, path[1:], value)})


def _discover_index_paths(root: Any, prefix: tuple[str, ...] = ()) -> set[tuple[str, ...]]:
    if root is None or not is_dataclass(root):
        return set()
    found: set[tuple[str, ...]] = set()
    for field in fields(root):
        value = getattr(root, field.name)
        path = (*prefix, field.name)
        if field.name in {
            "non_spec_state_indices_tensor",
            "spec_state_indices_tensor",
            "prefill_state_indices",
            "cache_indices",
        } and value is not None:
            found.add(path)
        if is_dataclass(value):
            found.update(_discover_index_paths(value, path))
    return found


def remap_ascend_gdn_metadata(
    metadata: Any, *, pad_slot_id: int = -1
) -> tuple[Any, ActiveSlotPlan]:
    """Return a copied metadata tree whose state references use active slots.

    The function refuses unknown state/cache-index fields so an upstream
    metadata change cannot silently route conv and temporal states differently.
    """
    discovered = _discover_index_paths(metadata)
    allowed = set(ASCEND_GDN_STATE_INDEX_PATHS)
    unknown = discovered - allowed
    if unknown:
        names = ", ".join(".".join(path) for path in sorted(unknown))
        raise ValueError(f"unhandled Ascend GDN state-index metadata: {names}")

    present_paths = []
    tensors = []
    for path in ASCEND_GDN_STATE_INDEX_PATHS:
        value = _get_path(metadata, path)
        if value is not None:
            present_paths.append(path)
            tensors.append(value)
    if not tensors:
        raise ValueError("Ascend GDN metadata contains no state-index tensors")

    plan = build_active_slot_plan(*tensors, pad_slot_id=pad_slot_id)
    remapped = metadata
    for path, tensor in zip(present_paths, plan.remapped_indices):
        remapped = _replace_path(remapped, path, tensor)
    return remapped, plan

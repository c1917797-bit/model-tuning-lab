#!/usr/bin/env python3
"""Bounded numerical snapshot comparison, not a device/quality acceptance gate.

The future capture adapter must bind these snapshots to independently audited
worker/request receipts. This module cannot establish that an NPU executed.
"""
from __future__ import annotations
import math

COMPONENTS = frozenset({"kv_key", "kv_value", "gdn_conv", "gdn_state",
                        "gdn_transition", "positions"})
IDENTITY = ("request_id", "rank", "layer", "step", "component", "segment_hash",
            "generation", "coordinates", "shape", "dtype", "comparison")


def compare(reference: dict, observed: dict) -> dict:
    """Compare like-for-like coordinates; never infer causality from a delta."""
    for key in IDENTITY:
        if key not in reference or reference[key] != observed.get(key):
            raise ValueError("snapshot identity mismatch: " + key)
    component = reference["component"]
    if component not in COMPONENTS:
        raise ValueError("unknown component")
    shape = reference["shape"]
    if not isinstance(shape, list) or not shape or any(
            type(n) is not int or n <= 0 for n in shape):
        raise ValueError("invalid shape")
    coordinates = reference["coordinates"]
    if not isinstance(coordinates, list) or not 1 <= len(coordinates) <= 4096:
        raise ValueError("bounded coordinates required")
    if len({tuple(c) for c in coordinates}) != len(coordinates):
        raise ValueError("duplicate coordinates")
    for c in coordinates:
        if not isinstance(c, list) or len(c) != len(shape) or any(
                type(i) is not int or i < 0 or i >= dim
                for i, dim in zip(c, shape)):
            raise ValueError("coordinate outside shape")
    left, right = reference.get("values"), observed.get("values")
    if not isinstance(left, list) or not isinstance(right, list) or not (
            len(left) == len(right) == len(coordinates)):
        raise ValueError("value coverage mismatch")
    for values in (left, right):
        if any(type(v) not in (int, float) or not math.isfinite(v) for v in values):
            raise ValueError("nonfinite or nonnumeric value")
        if component == "positions" and any(type(v) is not int for v in values):
            raise ValueError("position indices must be exact integers")
    delta = [float(b) - float(a) for a, b in zip(left, right)]
    rms = math.sqrt(math.fsum(d*d for d in delta) / len(delta))
    reference_rms = math.sqrt(math.fsum(float(v)**2 for v in left) / len(left))
    result = {key: reference[key] for key in IDENTITY}
    result.update(
        coordinates_compared=len(delta),
        full_tensor_coverage=len(delta) == math.prod(shape),
        different_coordinates=sum(a != b for a, b in zip(left, right)),
        max_abs_error=max(abs(d) for d in delta),
        rms_error=rms,
        relative_rms_error=None if reference_rms == 0 else rms/reference_rms,
        reference_rms=reference_rms,
        numerical_acceptance="not-decided",
        device_execution_proven=False,
        quality_or_causality_proven=False,
    )
    return result

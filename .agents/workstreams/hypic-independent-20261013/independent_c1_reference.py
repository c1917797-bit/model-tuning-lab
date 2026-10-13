"""Independent C1 mathematical reference, derived from paper equations 2/6.

State orientation is [value_heads, key_dim, value_dim]. This module imports
ordinary Torch only. It is not a serving hook or performance candidate.
"""
from dataclasses import dataclass
import torch

@dataclass(frozen=True)
class SegmentAffine:
    transition: torch.Tensor
    zero_state: torch.Tensor

def _inputs(keys, values, beta, decay):
    if keys.ndim != 3 or values.ndim != 3:
        raise ValueError("expected [tokens, heads, dimension]")
    length, key_heads, key_dim = keys.shape
    if length != values.shape[0] or key_heads <= 0:
        raise ValueError("token/head mismatch")
    value_heads = values.shape[1]
    if value_heads <= 0 or value_heads % key_heads:
        raise ValueError("value heads must be an integer multiple of key heads")
    if beta.shape != (length, value_heads) or decay.shape != beta.shape:
        raise ValueError("gate shape mismatch")
    if not all(t.device == keys.device and t.dtype == keys.dtype
               for t in (values, beta, decay)):
        raise ValueError("input device/dtype mismatch")
    if not keys.is_floating_point():
        raise ValueError("floating inputs required")
    dtype = torch.float64 if keys.dtype == torch.float64 else torch.float32
    expanded = keys.repeat_interleave(value_heads // key_heads, dim=1).to(dtype)
    return expanded, values.to(dtype), beta.to(dtype), decay.to(dtype)

def accumulate_segment(keys, values, beta, decay):
    """Accumulate T and zero-start S using low-rank updates, not dense A."""
    keys, values, beta, decay = _inputs(keys, values, beta, decay)
    heads, dk, dv = keys.shape[1], keys.shape[2], values.shape[2]
    transition = torch.eye(dk, dtype=keys.dtype, device=keys.device).expand(heads, dk, dk).clone()
    state = torch.zeros(heads, dk, dv, dtype=keys.dtype, device=keys.device)
    for k, v, b, g in zip(keys, values, beta, decay):
        k_col = k.unsqueeze(-1)
        k_row = k.unsqueeze(-2)
        b = b[:, None, None]
        g = g[:, None, None]
        transition = g * (transition - b * k_col * (k_row @ transition))
        state = g * (state - b * k_col * (k_row @ state)) + b * k_col * v.unsqueeze(-2)
    return SegmentAffine(transition, state)

def apply_segment(segment, incoming_state):
    if incoming_state.shape != segment.zero_state.shape:
        raise ValueError("incoming state shape mismatch")
    return segment.transition @ incoming_state.to(segment.transition.dtype) + segment.zero_state

def compose_segments(first, second):
    """Return the affine map for first followed by second; order matters."""
    if first.transition.shape != second.transition.shape or first.zero_state.shape != second.zero_state.shape:
        raise ValueError("segment shapes differ")
    return SegmentAffine(second.transition @ first.transition,
                         second.transition @ first.zero_state + second.zero_state)

def serial_dense_oracle(keys, values, beta, decay, initial_state):
    """Independent direct recurrence: construct each dense token transition."""
    keys, values, beta, decay = _inputs(keys, values, beta, decay)
    heads, dk = keys.shape[1:3]
    identity = torch.eye(dk, dtype=keys.dtype, device=keys.device).expand(heads, dk, dk)
    state = initial_state.to(keys.dtype).clone()
    for k, v, b, g in zip(keys, values, beta, decay):
        token_transition = g[:, None, None] * (
            identity - b[:, None, None] * (k.unsqueeze(-1) @ k.unsqueeze(-2)))
        token_write = b[:, None, None] * (k.unsqueeze(-1) @ v.unsqueeze(-2))
        state = token_transition @ state + token_write
    return state

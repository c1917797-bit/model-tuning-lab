"""Independent CPU oracle for DAMP; no imports from candidate reference/kernel.

Equation-derived, training-free numerical preparation only. The Ascend ABI
is value-major, not the key-major storage used by the earlier PyTorch probe.
"""
from dataclasses import dataclass
from fractions import Fraction
import math
import struct
import torch

RECIPROCAL_BITS = 0x3C010204
RECIPROCAL = struct.unpack("<f", struct.pack("<I", RECIPROCAL_BITS))[0]


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def f32_bits(value):
    return struct.unpack("<I", struct.pack("<f", value))[0]


def round_rational_f32(value):
    """Exact nearest-even FP32 for finite, FP32-range rational boundary tests.

    A binary64 approximation locates the three neighboring FP32 numbers;
    Fraction distances, not that approximation, decide the rounding.
    """
    guess = f32(float(value))
    bits = f32_bits(guess)
    candidates = []
    for candidate_bits in (bits - 1, bits, bits + 1):
        if not 0 <= candidate_bits <= 0xFFFFFFFF:
            continue
        candidate = struct.unpack("<f", struct.pack("<I", candidate_bits))[0]
        if math.isfinite(candidate):
            candidates.append((abs(Fraction.from_float(candidate) - value),
                               candidate_bits & 1, candidate))
    return min(candidates, key=lambda item: (item[0], item[1]))[2]


def scalar_div_f32(numerator, denominator):
    if denominator == 0:
        raise ValueError("zero denominator")
    return round_rational_f32(Fraction.from_float(f32(numerator)) /
                              Fraction.from_float(f32(denominator)))


def scalar_scale_f32(maximum):
    return round_rational_f32(Fraction.from_float(f32(maximum)) *
                              Fraction.from_float(RECIPROCAL))


def _cpu_float(x, name):
    if x.device.type != "cpu":
        raise ValueError(name + " must be CPU for the independent oracle")
    result = x.detach().float()
    if not bool(torch.isfinite(result).all()):
        raise ValueError(name + " contains nonfinite values")
    return result


@dataclass(frozen=True)
class OracleLayout:
    c: torch.Tensor              # [Hv,Dv], original-coordinate positive scale
    pv: torch.Tensor             # [Hv,Dv], reordered -> original
    pk: torch.Tensor             # [Hv,Dk], reordered -> original
    khi: int = 16
    group: int = 32


@dataclass
class ValueMajorPacked:
    high: torch.Tensor           # FP16 [S,Hv,Dv,khi]
    low: torch.Tensor            # INT8 [S,Hv,Dv,Dk-khi]
    scales: torch.Tensor         # FP32 [S,Hv,Dv/group,Dk-khi]

    def clone(self):
        return ValueMajorPacked(self.high.clone(), self.low.clone(),
                                self.scales.clone())


def validate_layout(layout, hv, dv, dk):
    c = _cpu_float(layout.c, "c")
    if c.shape != (hv, dv) or not bool((c > 0).all()):
        raise ValueError("c must be positive [Hv,Dv]")
    if not (0 < layout.khi < dk) or dv % layout.group:
        raise ValueError("invalid khi/group")
    for name, permutation, dimension in (("pv", layout.pv, dv),
                                          ("pk", layout.pk, dk)):
        if permutation.device.type != "cpu" or permutation.shape != (hv, dimension):
            raise ValueError(name + " shape/device mismatch")
        if permutation.dtype not in (torch.int64, torch.int32, torch.uint8):
            raise ValueError(name + " requires integer indices")
        expected = torch.arange(dimension, dtype=torch.int64)
        for head in range(hv):
            if not torch.equal(permutation[head].long().sort().values, expected):
                raise ValueError(name + " is not a bijection")


def transform_state(original, layout):
    original = _cpu_float(original, "original")
    if original.ndim != 4:
        raise ValueError("state axes must be [S,Hv,Dv,Dk]")
    _, hv, dv, dk = original.shape
    validate_layout(layout, hv, dv, dk)
    transformed = torch.empty_like(original)
    for head in range(hv):
        scaled = original[:, head] / layout.c[head, :, None].float()
        transformed[:, head] = scaled.index_select(1, layout.pv[head].long()).index_select(
            2, layout.pk[head].long())
    return transformed


def restore_state(transformed, layout):
    transformed = _cpu_float(transformed, "transformed")
    _, hv, dv, dk = transformed.shape
    validate_layout(layout, hv, dv, dk)
    restored = torch.empty_like(transformed)
    for head in range(hv):
        value_inverse = layout.pv[head].long().argsort()
        key_inverse = layout.pk[head].long().argsort()
        restored[:, head] = transformed[:, head].index_select(
            1, value_inverse).index_select(2, key_inverse) * layout.c[head, :, None]
    return restored


def pack_value_major(transformed, layout):
    """Explicit group loop along reordered Dv; independent of candidate pack."""
    transformed = _cpu_float(transformed, "transformed")
    slots, hv, dv, dk = transformed.shape
    validate_layout(layout, hv, dv, dk)
    high = transformed[..., :layout.khi].half().contiguous()
    if not bool(torch.isfinite(high).all()):
        raise ValueError("high region overflows FP16")
    low_fp32 = transformed[..., layout.khi:]
    low = torch.empty_like(low_fp32, dtype=torch.int8)
    scales = torch.empty((slots, hv, dv // layout.group, dk-layout.khi),
                         dtype=torch.float32)
    reciprocal = torch.tensor(RECIPROCAL, dtype=torch.float32)
    for group_id in range(dv // layout.group):
        start, end = group_id*layout.group, (group_id+1)*layout.group
        values = low_fp32[:, :, start:end, :]
        maximum = values.abs().max(dim=2).values
        scale = maximum * reciprocal
        if bool(((maximum != 0) & (scale == 0)).any()):
            raise ValueError("positive group maximum underflows FP32 scale")
        scale = torch.where(maximum == 0, torch.ones_like(maximum), scale)
        if not bool(torch.isfinite(scale).all()) or not bool((scale > 0).all()):
            raise ValueError("invalid scale")
        quotient = values / scale[:, :, None, :]
        low[:, :, start:end, :] = quotient.round().clamp(-127, 127).to(torch.int8)
        scales[:, :, group_id, :] = scale
    return ValueMajorPacked(high, low.contiguous(), scales.contiguous())


def unpack_value_major(packed, layout):
    """Independent explicit dequantization group loop, without candidate unpack."""
    if packed.high.device.type != "cpu" or packed.low.device.type != "cpu":
        raise ValueError("packed oracle inputs must be CPU")
    slots, hv, dv, kl = packed.low.shape
    dk = kl + layout.khi
    validate_layout(layout, hv, dv, dk)
    if packed.high.shape != (slots, hv, dv, layout.khi):
        raise ValueError("high shape mismatch")
    if packed.scales.shape != (slots, hv, dv//layout.group, kl):
        raise ValueError("scales shape mismatch")
    if (packed.high.dtype != torch.float16 or packed.low.dtype != torch.int8 or
            packed.scales.dtype != torch.float32):
        raise ValueError("packed dtype mismatch")
    if not bool(torch.isfinite(packed.high).all()) or not bool(
            torch.isfinite(packed.scales).all()) or not bool((packed.scales > 0).all()):
        raise ValueError("nonfinite/nonpositive packed region")
    if bool((packed.low == -128).any()):
        raise ValueError("symmetric INT8 contract forbids code -128")
    transformed = torch.empty((slots, hv, dv, dk), dtype=torch.float32)
    transformed[..., :layout.khi] = packed.high.float()
    for group_id in range(dv//layout.group):
        start, end = group_id*layout.group, (group_id+1)*layout.group
        transformed[:, :, start:end, layout.khi:] = (
            packed.low[:, :, start:end, :].float() *
            packed.scales[:, :, group_id, None, :])
    return transformed


def _validate_turn(q, k, v, g, beta, indices, slots, hv, dv, dk):
    q, k, v, g, beta = [_cpu_float(x, name) for x, name in
                        zip((q, k, v, g, beta), ("q", "k", "v", "g", "beta"))]
    batch, hq, _ = q.shape
    if k.shape != q.shape or q.shape[-1] != dk or hv % hq:
        raise ValueError("Q/K geometry or GQA ratio mismatch")
    if v.shape != (batch, hv, dv) or g.shape != (batch, hv) or beta.shape != g.shape:
        raise ValueError("V/g/beta geometry mismatch")
    if indices.device.type != "cpu" or indices.shape != (batch,):
        raise ValueError("state_indices must be CPU [batch]")
    if indices.dtype not in (torch.int32, torch.int64):
        raise ValueError("state_indices must be INT32/INT64")
    ids = indices.long()
    if int(ids.min()) < 0 or int(ids.max()) >= slots or len(set(ids.tolist())) != batch:
        raise ValueError("duplicate/out-of-range slots")
    if bool((g > 0).any()) or bool(((beta < 0) | (beta > 1)).any()):
        raise ValueError("require nonpositive log decay and beta in [0,1]")
    return q, k, v, g, beta, ids, hv//hq


def uncompressed_step(original, q, k, v, g, beta, indices):
    """Native-coordinate CPU GDN; FP32 mv reduction, no candidate gdn_step."""
    original = _cpu_float(original, "state")
    slots, hv, dv, dk = original.shape
    q, k, v, g, beta, ids, ratio = _validate_turn(
        q, k, v, g, beta, indices, slots, hv, dv, dk)
    updated = original.clone()
    output = torch.empty_like(v)
    for row, slot in enumerate(ids.tolist()):
        for head in range(hv):
            qh, kh = q[row, head//ratio], k[row, head//ratio]
            decayed = original[slot, head] * g[row, head].exp()
            residual = v[row, head] - torch.mv(decayed, kh)
            state = decayed + torch.outer(beta[row, head]*residual, kh)
            updated[slot, head] = state
            output[row, head] = torch.mv(state, qh) * (dk**-0.5)
    return updated, output


def compressed_step(packed, layout, q, k, v, g, beta, indices):
    """Decompress -> update -> original-coordinate FP32 readout -> repack.

    Returned output is deliberately taken BEFORE repacking updated state.
    Only selected slots change; distinct requests require distinct slot IDs.
    """
    transformed = unpack_value_major(packed, layout)
    slots, hv, dv, dk = transformed.shape
    q, k, v, g, beta, ids, ratio = _validate_turn(
        q, k, v, g, beta, indices, slots, hv, dv, dk)
    updated = transformed.clone()
    output = torch.empty_like(v)
    for row, slot in enumerate(ids.tolist()):
        for head in range(hv):
            pv, pk = layout.pv[head].long(), layout.pk[head].long()
            qh = q[row, head//ratio].index_select(0, pk)
            kh = k[row, head//ratio].index_select(0, pk)
            vh = (v[row, head] / layout.c[head]).index_select(0, pv)
            decayed = transformed[slot, head] * g[row, head].exp()
            residual = vh - torch.mv(decayed, kh)
            state = decayed + torch.outer(beta[row, head]*residual, kh)
            updated[slot, head] = state
            reordered_output = torch.mv(state, qh) * (dk**-0.5)
            output[row, head] = (reordered_output * layout.c[head].index_select(
                0, pv)).index_select(0, pv.argsort())
    selected = pack_value_major(updated.index_select(0, ids), layout)
    result = packed.clone()
    result.high.index_copy_(0, ids, selected.high)
    result.low.index_copy_(0, ids, selected.low)
    result.scales.index_copy_(0, ids, selected.scales)
    return result, output, updated


def errors(actual, expected):
    """Finite JSON-ready metrics, without diluting selected slots into untouched."""
    a, e = actual.detach().float().cpu().double(), expected.detach().float().cpu().double()
    if a.shape != e.shape:
        raise ValueError("metric shape mismatch")
    if not bool(torch.isfinite(a).all()) or not bool(torch.isfinite(e).all()):
        return {"finite": False, "relative_l2": None, "max_head_relative_l2": None,
                "max_absolute": None, "expected_norm": None}
    difference = a-e
    # Leading [selected slot/request, head] axes remain separate.
    dims = tuple(range(2, a.ndim))
    per_numerator = difference.square().sum(dims)
    per_denominator = e.square().sum(dims).clamp_min(1e-30)
    return {"finite": True,
            "relative_l2": math.sqrt(float(difference.square().sum()) /
                                     max(float(e.square().sum()), 1e-30)),
            "max_head_relative_l2": float((per_numerator/per_denominator).sqrt().max()),
            "max_absolute": float(difference.abs().max()),
            "expected_norm": float(e.square().sum().sqrt())}


def original_coordinate_errors(packed, layout, expected_original, indices=None):
    actual = restore_state(unpack_value_major(packed, layout), layout)
    if indices is not None:
        actual = actual.index_select(0, indices.long())
        expected_original = expected_original.index_select(0, indices.long())
    return errors(actual, expected_original)


"""Independent CPU KIVI A16 group32 equations, for reference preparation only.

No candidate kernel/producer/codec import. Caller supplies qualified NumPy.
The API accepts exactly one complete original 128x256 A16 tile, keeping peak
workspace bounded. Returned payload/scales/minima are compared byte-for-byte.
This module is not wired into frozen raw023, model018, or mixed008.
"""
import math

SCALAR_REFERENCE_SHA = "45ccb0c2fff417e518cb591aaf5ba201645551a1aeafc9d8bdc3c97ce6a8fd49"
TOKENS = 128
DIM = 256
GROUP = 32


def _require(value, message):
    if not value:
        raise ValueError(message)


def _round_a16(values, dtype, np):
    """Each operation uses float64 then the original explicit A16 boundary."""
    values = np.asarray(values, dtype=np.float64)
    _require(bool(np.isfinite(values).all()), "nonfinite input")
    with np.errstate(over="ignore", invalid="ignore"):
        if dtype == "float16":
            result = values.astype("<f2")
            # struct.pack("<e", finite overflow) raises, rather than returns inf.
            if not bool(np.isfinite(result).all()):
                raise OverflowError("float16 struct-pack range")
            return result.astype(np.float64)
        _require(dtype == "bfloat16", "only float16/bfloat16")
        f32 = values.astype("<f4")
        # Preserve struct.pack("<f") overflow independently of BF16 rounding.
        if not bool(np.isfinite(f32).all()):
            raise OverflowError("float32 struct-pack range")
        word = f32.view("<u4")
        word = (word + np.uint32(0x7fff) +
                ((word >> np.uint32(16)) & np.uint32(1))) & np.uint32(0xffff0000)
        # Rounding finite float32 may yield BF16 infinity, as does scalar cast.
        # Its next scalar operation rejects nonfinite input; do not clamp it.
        return word.view("<f4").astype(np.float64)


def _decode(raw, dtype, np):
    if dtype == "float16":
        return np.frombuffer(raw, dtype="<f2").astype(np.float64)
    _require(dtype == "bfloat16", "bad dtype")
    word = np.frombuffer(raw, dtype="<u2").astype("<u4") << np.uint32(16)
    return word.view("<f4").astype(np.float64)


def _encode(values, dtype, np):
    value = _round_a16(values, dtype, np)
    if dtype == "float16":
        return value.astype("<f2").tobytes(order="C")
    return (value.astype("<f4").view("<u4") >> np.uint32(16)).astype("<u2").tobytes(order="C")


def _groups(values, bits, dtype, np):
    value = _round_a16(values, dtype, np)
    # Python min/max retain the first equal operand, including signed zero.
    # np.min/max can select a later equal zero, changing minima bytes.
    low = np.take_along_axis(value, np.argmin(value, axis=-1)[..., None], axis=-1)[..., 0]
    high = np.take_along_axis(value, np.argmax(value, axis=-1)[..., None], axis=-1)[..., 0]
    with np.errstate(over="ignore", invalid="ignore"):
        width = _round_a16(high - low, dtype, np)
    maximum = (1 << bits) - 1
    scale = np.ones_like(width)
    active = width != 0
    scale[active] = _round_a16(width[active] / maximum, dtype, np)
    _require(not bool((scale == 0).any()), "nonconstant group scale underflow")
    numerator = _round_a16(value - low[..., None], dtype, np)
    ratio = _round_a16(numerator / scale[..., None], dtype, np)
    # Python round and np.rint are both nearest-even after the A16 cast.
    codes = np.rint(np.clip(ratio, 0, maximum)).astype(np.uint32)
    return codes, scale, low


def pack_tile(raw, axis, bits, dtype, np):
    """Return all three planes for one full tile; never skips data or groups."""
    _require(type(raw) is bytes and len(raw) == TOKENS * DIM * 2,
             "one complete original128x256 A16 tile")
    _require(type(bits) is int and bits in (2, 4), "KIVI2/4bit")
    _require(axis in ("K", "V"), "unknown axis")
    rows = _decode(raw, dtype, np).reshape(TOKENS, DIM)
    if axis == "K":
        value = rows.reshape(TOKENS // GROUP, GROUP, DIM).transpose(0, 2, 1)
        codes, scales, minima = _groups(value, bits, dtype, np)
        codes = codes.transpose(0, 2, 1).reshape(TOKENS, DIM)
        n = 32 // bits
        fields = codes.reshape(TOKENS // n, n, DIM)
        words = np.zeros((TOKENS // n, DIM), dtype="<u4")
        for j in range(n):
            words |= fields[:, j, :] << np.uint32(bits * j)
    else:
        value = rows.reshape(TOKENS, DIM // GROUP, GROUP)
        codes, scales, minima = _groups(value, bits, dtype, np)
        n = 32 // bits
        fields = codes.reshape(TOKENS, DIM // n, n)
        words = np.zeros((TOKENS, DIM // n), dtype="<u4")
        for j in range(n):
            words |= fields[:, :, j] << np.uint32(bits * j)
    return dict(axis=axis, tokens=TOKENS, dim=DIM, bits=bits, dtype=dtype,
                payload=words.tobytes(order="C"), scales=_encode(scales, dtype, np),
                minima=_encode(minima, dtype, np))

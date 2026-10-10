"""Independent packed KV oracle; vectorized decode, unchanged scalar sums.

No Torch, Triton, model or candidate import. NumPy does only exact integer
unpacking and elementwise FP64 products; math.fsum/math.exp retain the prior
scalar oracle's arithmetic order/boundaries. Software qualification is not NPU
or CUDA parity. This is a new reference source, never an old PASS replacement.
"""
import math
import struct

import numpy as np


def cast(x, dtype):
    if dtype == "float16":
        return struct.unpack("<e", struct.pack("<e", x))[0]
    if dtype == "bfloat16":
        bits = struct.unpack("<I", struct.pack("<f", x))[0]
        if (bits & 0x7f800000) == 0x7f800000:
            if bits & 0x007fffff:
                bits |= 0x00400000
        else:
            bits += 0x7fff + ((bits >> 16) & 1)
        return struct.unpack("<f", struct.pack("<I", bits & 0xffff0000))[0]
    raise ValueError("A16 dtype required")


def scalar(raw, index, dtype):
    if len(raw) % 2 or type(index) is not int or not 0 <= index < len(raw) // 2:
        raise ValueError("actual A16 byte extent")
    bits = struct.unpack_from("<H", raw, index * 2)[0]
    if dtype == "float16":
        return struct.unpack("<e", struct.pack("<H", bits))[0]
    if dtype == "bfloat16":
        return struct.unpack("<f", struct.pack("<I", bits << 16))[0]
    raise ValueError("A16 dtype required")


def _a16(raw, dtype):
    if len(raw) % 2:
        raise ValueError("actual A16 byte extent")
    if dtype == "float16":
        return np.frombuffer(raw, dtype="<f2").astype(np.float64)
    if dtype == "bfloat16":
        words = np.frombuffer(raw, dtype="<u2").astype("<u4") << np.uint32(16)
        return words.view("<f4").astype(np.float64)
    raise ValueError("A16 dtype required")


def _cast_array(values, dtype):
    values = np.asarray(values, dtype=np.float64)
    if not np.isfinite(values).all():
        raise ValueError("finite reference intermediate")
    with np.errstate(over="raise", invalid="raise"):
        if dtype == "float16":
            result = values.astype("<f2").astype(np.float64)
        elif dtype == "bfloat16":
            words = values.astype("<f4").view("<u4")
            words = words + np.uint32(0x7fff) + ((words >> np.uint32(16)) & np.uint32(1))
            result = (words & np.uint32(0xffff0000)).view("<f4").astype(np.float64)
        else:
            raise ValueError("A16 dtype required")
    if not np.isfinite(result).all():
        raise ValueError("finite A16 reference result")
    return result


def decode(pool, row, axis, bits, dtype, chunk=1024):
    """Decode one full logical K or V; physical maps need not be contiguous."""
    if bits not in (2, 4) or axis not in ("K", "V") or not 1 <= chunk <= 1024:
        raise ValueError("qualified bits/axis/bounded decode chunk")
    length, kp, vp, slot = row["controls"]
    if any(type(x) is not int for x in (length, kp, vp, slot)) or not (
        1 <= length <= 33792 and 0 <= kp < length and kp % 128 == 0
        and 0 <= vp < length and 1 <= length - kp <= 128
        and 1 <= length - vp <= 129 and slot >= 0
    ):
        raise ValueError("actual pending K128/V129 controls")
    lanes, prefix = 32 // bits, kp if axis == "K" else vp
    name = "key" if axis == "K" else "value"
    mapping = row["kp"] if axis == "K" else row["vp"]
    if len(mapping) != (kp // 128 if axis == "K" else vp) or any(
        type(x) is not int or x < 0 for x in mapping
    ):
        raise ValueError("complete nonnegative physical remap")
    codes = np.frombuffer(pool[name + "_codes"], dtype="<u4")
    scales = _a16(pool[name + "_scales"], dtype)
    minima = _a16(pool[name + "_minima"], dtype)
    residual = _a16(pool[name + "_residual"], dtype)
    indices = np.asarray(mapping, dtype=np.int64)
    channels = np.arange(256, dtype=np.int64)[None, :]
    result = np.empty((length, 256), dtype=np.float64)
    for start in range(0, prefix, chunk):
        tokens = np.arange(start, min(prefix, start + chunk), dtype=np.int64)
        if axis == "K":
            physical, local = indices[tokens // 128, None], tokens[:, None] % 128
            wi = physical * (128 // lanes * 256) + local // lanes * 256 + channels
            mi = physical * 1024 + local // 32 * 256 + channels
            shift = (local % lanes * bits).astype(np.uint32)
        else:
            physical = indices[tokens, None]
            wi = physical * (256 // lanes) + channels // lanes
            mi = physical * 8 + channels // 32
            shift = (channels % lanes * bits).astype(np.uint32)
        unpacked = ((codes[wi] >> shift) & np.uint32((1 << bits) - 1)).astype(np.float64)
        # Both distinct A16 casts are part of the original reference contract.
        result[start:start + len(tokens)] = _cast_array(
            _cast_array(unpacked * scales[mi], dtype) + minima[mi], dtype
        )
    capacity = 128 if axis == "K" else 129
    first, count = slot * capacity * 256, (length - prefix) * 256
    tail = residual[first:first + count]
    if tail.size != count:
        raise ValueError("whole physical residual slot")
    result[prefix:] = tail.reshape(-1, 256)
    if not np.isfinite(result).all():
        raise ValueError("finite full decoded state")
    return result


def attention(pool_bytes, row, query, bits, dtype):
    if len(query) != 6 or any(len(q) != 256 for q in query):
        raise ValueError("Qwen TP4 actual Q6/KV1/D256")
    qarray = np.asarray(query, dtype=np.float64)
    if not np.isfinite(qarray).all():
        raise ValueError("finite actual query")
    keys = decode(pool_bytes, row, "K", bits, dtype)
    values = decode(pool_bytes, row, "V", bits, dtype)
    length, _, vp, _ = row["controls"]
    outputs, splits = [], []
    for q in qarray:
        dots = np.empty(length, dtype=np.float64)
        for start in range(0, length, 1024):
            products = keys[start:start + 1024] * q
            dots[start:start + len(products)] = np.fromiter(
                (math.fsum(line) for line in products), dtype=np.float64, count=len(products)
            )
        scores = _cast_array(_cast_array(dots, dtype) * 0.0625, dtype)
        peak = float(scores.max())
        # Do not substitute np.exp/reduce: retain scalar libm and fsum.
        exps = [math.exp(float(s) - peak) for s in scores]
        total = math.fsum(exps)
        probs = _cast_array([x / total for x in exps], dtype)
        out, split = [], []
        for d in range(256):
            terms = probs * values[:, d]
            out.append(cast(math.fsum(terms), dtype))
            split.append(cast(cast(math.fsum(terms[:vp]), dtype)
                              + cast(math.fsum(terms[vp:]), dtype), dtype))
        outputs.append(out)
        splits.append(split)
    return {"scalar_a16_boundary_output": outputs,
            "official_python_split_boundary_output": splits,
            "released_cuda_parity": False, "native_or_model_pass": False,
            "reference_algorithm": "independent-vectorized-unpack-scalar-fsum-exp/v1"}


def compare(actual, expected):
    if len(actual) != len(expected) or not actual or not all(
        math.isfinite(x) for x in tuple(actual) + tuple(expected)
    ):
        raise ValueError("whole finite output")
    rms = math.sqrt(math.fsum(x * x for x in expected) / len(expected))
    error = math.sqrt(math.fsum((a - b) ** 2 for a, b in zip(actual, expected)) / len(expected))
    measured = {"relative_rms": error / max(rms, 1e-8),
                "max_abs": max(abs(a - b) for a, b in zip(actual, expected)), "threshold": 0.005}
    if measured["relative_rms"] > 0.005:
        raise ValueError("unchanged .005 relative RMS ceiling: " + repr(measured))
    return measured

"""Independent stdlib unpack and attention boundaries; never imports candidate kernel.
Released CUDA execution parity is pending. Constant-group policy is the donor adaptation.
"""
import math
import struct

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
    if len(raw) % 2 or type(index) is not int or index < 0 or index >= len(raw) // 2:
        raise ValueError("actual A16 byte extent")
    bits = struct.unpack_from("<H", raw, index * 2)[0]
    if dtype == "float16":
        return struct.unpack("<e", struct.pack("<H", bits))[0]
    if dtype == "bfloat16":
        return struct.unpack("<f", struct.pack("<I", bits << 16))[0]
    raise ValueError("A16 dtype required")

def word(raw, index):
    if len(raw) % 4 or type(index) is not int or index < 0 or index >= len(raw) // 4:
        raise ValueError("actual int32 byte extent")
    return struct.unpack_from("<I", raw, index * 4)[0]

def affine(code, scale, minimum, dtype):
    return cast(cast(code * scale, dtype) + minimum, dtype)

def decoded(pool_bytes, row, axis, token, channel, bits, dtype):
    length, kprefix, vprefix, slot = row["controls"]
    if bits not in (2, 4) or type(token) is not int or not (0 <= token < length) or not (0 <= channel < 256):
        raise ValueError("KIVI bits/token/channel")
    lanes = 32 // bits
    if axis == "K" and token < kprefix:
        page = row["kp"][token // 128]
        local = token % 128
        wi = page * (128 // lanes * 256) + local // lanes * 256 + channel
        mi = page * 1024 + local // 32 * 256 + channel
        code = (word(pool_bytes["key_codes"], wi) >> (local % lanes * bits)) & ((1 << bits) - 1)
        return affine(code, scalar(pool_bytes["key_scales"], mi, dtype),
                      scalar(pool_bytes["key_minima"], mi, dtype), dtype)
    if axis == "V" and token < vprefix:
        record = row["vp"][token]
        wi = record * (256 // lanes) + channel // lanes
        mi = record * 8 + channel // 32
        code = (word(pool_bytes["value_codes"], wi) >> (channel % lanes * bits)) & ((1 << bits) - 1)
        return affine(code, scalar(pool_bytes["value_scales"], mi, dtype),
                      scalar(pool_bytes["value_minima"], mi, dtype), dtype)
    if axis not in ("K", "V"):
        raise ValueError("K or V")
    prefix, tail_capacity, name = (kprefix, 128, "key_residual") if axis == "K" else (vprefix, 129, "value_residual")
    return scalar(pool_bytes[name], slot * tail_capacity * 256 + (token - prefix) * 256 + channel, dtype)

def attention(pool_bytes, row, query, bits, dtype):
    length, _, vprefix, _ = row["controls"]
    if len(query) != 6 or any(len(q) != 256 for q in query):
        raise ValueError("Qwen TP4 actual Q6/KV1/D256")
    outputs, author_boundary_outputs = [], []
    for q in query:
        # FP64 scalar oracle, A16 dot and scale/prob boundaries explicit.
        scores = [cast(cast(math.fsum(q[d] * decoded(pool_bytes, row, "K", token, d, bits, dtype)
                    for d in range(256)), dtype) * 0.0625, dtype) for token in range(length)]
        peak = max(scores)
        exps = [math.exp(s - peak) for s in scores]
        total = math.fsum(exps)
        probs = [cast(x / total, dtype) for x in exps]
        out, split = [], []
        for d in range(256):
            terms = [probs[token] * decoded(pool_bytes, row, "V", token, d, bits, dtype) for token in range(length)]
            # Candidate follows donor named full-token FP32 AV accumulation (not CUDA bitwise).
            out.append(cast(math.fsum(terms), dtype))
            # Official Python splits quant prefix and FP residual then adds A16 partials.
            split.append(cast(cast(math.fsum(terms[:vprefix]), dtype) +
                              cast(math.fsum(terms[vprefix:]), dtype), dtype))
        outputs.append(out); author_boundary_outputs.append(split)
    return {"scalar_a16_boundary_output": outputs, "official_python_split_boundary_output": author_boundary_outputs,
            "released_cuda_parity": False, "native_or_model_pass": False}

def compare(actual, expected):
    if len(actual) != len(expected) or not actual or not all(math.isfinite(x) for x in tuple(actual) + tuple(expected)):
        raise ValueError("whole finite output")
    rms = math.sqrt(math.fsum(x * x for x in expected) / len(expected))
    error = math.sqrt(math.fsum((a - b) ** 2 for a, b in zip(actual, expected)) / len(expected))
    measured = {"relative_rms": error / max(rms, 1e-8), "max_abs": max(abs(a - b) for a, b in zip(actual, expected)),
                "threshold": 0.005}
    if measured["relative_rms"] > 0.005:
        raise ValueError("unchanged .005 relative RMS ceiling: " + repr(measured))
    return measured

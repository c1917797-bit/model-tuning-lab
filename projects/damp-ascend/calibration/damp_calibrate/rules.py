"""Deterministic selection rules without Torch."""
import math
import struct

PAPER = "https://arxiv.org/html/2608.27513v2"
ALPHAS = (0.0, 0.25, 0.5, 0.75, 1.0)
RECIPROCAL = struct.unpack("<f", struct.pack("<I", 0x3C010204))[0]

def require(condition, message):
    if not condition: raise ValueError(message)

def f32(value):
    try: return struct.unpack("<f", struct.pack("<f", value))[0]
    except OverflowError: return float("inf")

def retention(rows):
    require(bool(rows) and bool(rows[0]), "empty future")
    logs = [0.0] * len(rows[0]); terms = [[1.0] for _ in logs]
    for row in rows:
        require(len(row) == len(logs), "ragged future")
        for head, value in enumerate(row):
            require(math.isfinite(value) and value <= 1e-6, "invalid future log decay")
            logs[head] += 2.0 * value
            terms[head].append(math.exp(logs[head]))
    return [math.fsum(values) for values in terms]

def joint_risk(errors, weights):
    require(bool(errors) and len(errors) == len(weights), "anchor risk mismatch")
    width = len(errors[0]); require(width > 0, "empty channel errors")
    require(all(len(e) == width and all(math.isfinite(x) and x >= 0 for x in e)
                for e in errors) and all(math.isfinite(w) and w >= 1 for w in weights),
            "invalid joint errors/retention")
    return [math.fsum(e[k] * w for e, w in zip(errors, weights)) / len(errors)
            for k in range(width)]

def protected(risk, count):
    require(0 < count < len(risk) and all(math.isfinite(x) and x >= 0 for x in risk),
            "bad protected risk/count")
    high = sorted(sorted(range(len(risk)), key=lambda key: (-risk[key], key))[:count])
    return high, high + [key for key in range(len(risk)) if key not in set(high)]

def choose(scores):
    valid = [(score, index) for index, score in enumerate(scores)
             if score is not None and math.isfinite(score) and score >= 0]
    require(bool(valid), "no finite SR candidate")
    return min(valid)[1]

def sr_from_rms(rms, alpha):
    require(alpha in ALPHAS and bool(rms) and
            all(math.isfinite(x) and x >= 0 for x in rms), "invalid RMS/grid")
    sr = [f32(x ** alpha) if x > 0 else 1.0 for x in rms]
    require(all(math.isfinite(x) and x > 0 for x in sr), "candidate SR over/underflow")
    pv = sorted(range(len(rms)), key=lambda value: (rms[value] / sr[value], value))
    return sr, pv

def partition_rows(rows):
    from collections import Counter
    require(len(rows) == 36 and Counter((r["split"], r["domain"]) for r in rows) ==
            Counter({(s, d): 4 for s in ("fit", "tune", "validation")
                     for d in ("math", "code", "general")}), "36 balanced partitions required")
    ids = [r["id"] for r in rows]
    require(len(set(ids)) == 36, "duplicate request identity")
    return {split: sorted((r for r in rows if r["split"] == split), key=lambda r: r["id"])
            for split in ("fit", "tune", "validation")}

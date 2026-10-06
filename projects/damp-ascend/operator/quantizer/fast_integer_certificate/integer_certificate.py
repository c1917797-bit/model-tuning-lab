# SPDX-License-Identifier: Apache-2.0
"""Integer-only model of the NEW conservative certificate; not an NPU result."""
MAX_FINITE = 0x7f7fffff
MIN_NORMAL = 0x00800000

def coefficient(j):
    if not 0 <= j <= 126:
        raise ValueError("half transition index must be 0..126")
    k = 2*j+1
    f = k.bit_length()-2
    c = (k << (23-f)) + (-1 if j & 1 else 1)
    assert 1 << 24 <= c < 1 << 25
    return c, f

def tables():
    # Slot 127 is a safe unused placeholder. n0/n127 are clamped BEFORE gather.
    rows = [coefficient(j) for j in range(127)]
    return rows+[rows[-1]]

def floor_endpoint(scale_bits, j):
    """Return (normal-domain, exact positive FP32 floor bits).
    Arithmetic matches the proposed SIMD limb sequence, not float multiply.
    An invalid scale still produces safe bounded intermediates; no certificate.
    """
    a = scale_bits & 0x7fffffff
    se = a >> 23
    ms = (a - (se << 23)) + (1 << 23)
    c, f = coefficient(j)
    m1, m0 = ms >> 12, ms & 4095
    c1, c0 = (c >> 12)-4096, c & 4095
    p00 = m0*c0
    u1 = (p00 >> 12) + m0*c1 + m1*c0
    u2 = (u1 >> 12) + m1*c1 + m0
    u3 = (u2 >> 12) + m1
    d2 = u2 & 4095
    b = u3 >> 12
    assert 0 <= b <= 1
    assert 0 <= p00 < 1 << 24
    assert 0 <= u1 < 1 << 25 and 0 <= u2 < 1 << 25
    assert 2048 <= u3 < 8192
    mant48 = (u3 << 12)+d2
    mant49 = (u3 << 11)+(d2 >> 1)
    mant = mant48+b*(mant49-mant48)
    eraw = se+f+b
    valid = not(scale_bits >> 31) and 1 <= se <= 254 and 1 <= eraw <= 254
    safe_e = min(254, max(1, eraw))  # clamp BEFORE shift; invalid placeholder
    bits = (safe_e << 23)+(mant-(1 << 23))
    assert MIN_NORMAL <= bits <= MAX_FINITE
    return valid, bits

def certificate(x_bits, scale_bits, magnitude):
    """Any proposed n0..127 is permitted; Div accuracy/sign is NOT trusted."""
    if not 0 <= magnitude <= 127:
        raise ValueError("candidate magnitude must be 0..127 before any gather")
    a = x_bits & 0x7fffffff
    if a > MAX_FINITE or not 0 < scale_bits <= MAX_FINITE:
        return False
    lv, lower = floor_endpoint(scale_bits, max(magnitude-1, 0))
    uv, upper = floor_endpoint(scale_bits, min(magnitude, 126))
    # Strict interior is safe regardless of boundary inclusion/parity.
    return ((magnitude == 0 or (lv and a > lower)) and
            (magnitude == 127 or (uv and a < upper)) and
            (scale_bits & 0x7fffffff) >= MIN_NORMAL)

def restore_sign(x_bits, magnitude):
    return -magnitude if x_bits >> 31 else magnitude

def limb_boundaries(scale_mant, c):
    """Expose P limbs independently reconstructable by a host test."""
    m0, m1 = scale_mant & 4095, scale_mant >> 12
    c0, c1 = c & 4095, (c >> 12)-4096
    p00 = m0*c0
    u1 = (p00 >> 12)+m0*c1+m1*c0
    u2 = (u1 >> 12)+m1*c1+m0
    u3 = (u2 >> 12)+m1
    return (p00 & 4095, u1 & 4095, u2 & 4095, u3)


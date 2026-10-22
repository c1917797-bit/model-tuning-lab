"""Independent exact BF16 reduction diagnostics; no NPU or acceptance authority.

A finite BF16 value is an integer multiple of 2**-133. Keep that integer exact,
then round once with nearest/ties-to-even. This avoids an FP64 -> FP32 -> BF16
double rounding path. Tree results describe possible BF16 intermediate adds;
membership is diagnostic and never replaces the registered numerical gate.
"""
from functools import lru_cache

INF = 0x7F80
NAN = 0x7FC0


def is_finite(bits):
    if type(bits) is not int or not 0 <= bits <= 0xFFFF:
        raise ValueError("one unsigned BF16 word required")
    return (bits & 0x7F80) != 0x7F80


def scaled_integer(bits):
    """Return exact value * 2**133; reject infinity and NaN."""
    if not is_finite(bits):
        raise ValueError("finite BF16 operand required")
    exponent, fraction = (bits >> 7) & 255, bits & 127
    magnitude = fraction if exponent == 0 else (128 + fraction) << (exponent - 1)
    return -magnitude if bits & 0x8000 else magnitude


def round_scaled(value):
    """Nearest/ties-to-even BF16 from exact integer * 2**-133."""
    if type(value) is not int:
        raise ValueError("exact integer required")
    sign, magnitude = (0x8000, -value) if value < 0 else (0, value)
    if magnitude < 128:
        return sign | magnitude
    shift = magnitude.bit_length() - 8
    significand = magnitude >> shift
    if shift:
        remainder = magnitude - (significand << shift)
        halfway = 1 << (shift - 1)
        if remainder > halfway or (remainder == halfway and significand & 1):
            significand += 1
    if significand == 256:
        significand = 128
        shift += 1
    exponent = shift + 1
    if exponent >= 255:
        return sign | INF
    return sign | (exponent << 7) | (significand - 128)


def add_bf16(left, right):
    """Diagnostic IEEE-style add with a BF16 rounding boundary after the add."""
    for value in (left, right):
        if type(value) is not int or not 0 <= value <= 0xFFFF:
            raise ValueError("BF16 words required")
    nonfinite = [x for x in (left, right) if not is_finite(x)]
    if any(x & 127 for x in nonfinite):
        return NAN
    if nonfinite:
        if len(nonfinite) == 2 and (left ^ right) & 0x8000:
            return NAN
        return nonfinite[0]
    exact = scaled_integer(left) + scaled_integer(right)
    if exact == 0 and left == right == 0x8000:
        return 0x8000
    return round_scaled(exact)


def exact_sum(words):
    """One final BF16 rounding of the exact real sum of finite operands."""
    return round_scaled(sum(scaled_integer(x) for x in words))


def bf16_tree_results(words):
    """Every binary parenthesization/permutation, rounded at each BF16 add."""
    values = tuple(words)
    if not 1 <= len(values) <= 4 or not all(is_finite(x) for x in values):
        raise ValueError("one to four finite BF16 operands required")

    @lru_cache(None)
    def visit(mask):
        if mask & (mask - 1) == 0:
            return frozenset((values[mask.bit_length() - 1],))
        result = set()
        first = mask & -mask
        subset = (mask - 1) & mask
        while subset:
            other = mask ^ subset
            if other and subset & first:
                result.update(add_bf16(a, b) for a in visit(subset) for b in visit(other))
            subset = (subset - 1) & mask
        return frozenset(result)

    return visit((1 << len(values)) - 1)


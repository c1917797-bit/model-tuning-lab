"""Independent exact Fraction decision, binary64 used ONLY to locate FP32."""
from fractions import Fraction
import math
import struct

MAX = 0x7f7fffff
OVERFLOW_MIDPOINT = Fraction((1<<25)-1)*(1<<103)

def value(bits):
    e, m = (bits>>23)&255, bits&0x7fffff
    if e == 0: return Fraction(m,1<<149)
    if e == 255: raise ValueError("nonfinite")
    return Fraction((1<<23)|m)*Fraction(2)**(e-150)

def divide(x_bits,c_bits):
    sign, x, c = x_bits&0x80000000, x_bits&0x7fffffff, c_bits&0x7fffffff
    if x >= 0x7f800000 or c_bits&0x80000000 or c == 0 or c >= 0x7f800000:
        return False,False,0
    if x == 0: return True,True,sign
    target = value(x)/value(c)
    if target >= OVERFLOW_MIDPOINT: return True,False,sign|0x7f800000
    try:
        guess = struct.unpack("<I",struct.pack("<f",float(target)))[0]
    except OverflowError:
        guess = MAX
    guess = min(MAX,guess)
    candidates = [b for b in (guess-1,guess,guess+1) if 0 <= b <= MAX]
    winner = min(candidates,key=lambda b:(abs(value(b)-target),b&1))
    return True,True,sign|winner

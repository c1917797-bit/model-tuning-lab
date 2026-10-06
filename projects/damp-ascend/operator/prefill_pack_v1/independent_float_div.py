"""Independent exact Fraction golden; no candidate helper imports or float division."""
from fractions import Fraction
MAX=0x7f7fffff
INF=0x7f800000
def power(e):
    return Fraction(1<<e) if e>=0 else Fraction(1,1<<(-e))
def value(bits):
    if not 0<=bits<=MAX:raise ValueError("finite positive magnitude required")
    exponent=bits>>23
    if exponent:return Fraction(0x800000+(bits&0x7fffff))*power(exponent-150)
    return Fraction(bits&0x7fffff)*power(-149)
OVERFLOW_MIDPOINT=Fraction((1<<25)-1)*power(103)
def rounded_fraction(y):
    if y<0:raise ValueError("positive magnitude only")
    if y>=OVERFLOW_MIDPOINT:return INF
    lo,hi=0,MAX
    while lo<hi:
        mid=(lo+hi+1)//2
        if value(mid)<=y:lo=mid
        else:hi=mid-1
    if lo==MAX:return MAX
    next_bits=lo+1
    below=y-value(lo);above=value(next_bits)-y
    if above<below:return next_bits
    if above>below:return lo
    return lo if not lo&1 else next_bits
def oracle(x,c):
    mag=x&0x7fffffff;sign=x&0x80000000
    if mag>=INF or not 0<c<INF:return False,False,0
    q=rounded_fraction(value(mag)/value(c))
    return True,q<INF,sign|q
def midpoint(q,upper):
    if q==0:
        if not upper:return Fraction(0)
        return value(1)/2
    if upper and q==MAX:return OVERFLOW_MIDPOINT
    return (value(q)+value(q+1 if upper else q-1))/2
def oracle_certificate(x,c,q):
    if x&0x7fffffff>=INF or not 0<c<INF or not 0<=q<INF:return False
    return (oracle(x,c)[2]&0x7fffffff)==q

"""Source-mapped integer model, not the independent golden or NPU execution."""
MASK=0x7fffffff
INF=0x7f800000
def decode(bits):
    raw=bits>>23
    return ((bits&0x7fffff)|(0x800000 if raw else 0),raw-150 if raw else -149)
def normalize(bits):
    m,e=decode(bits);shift=24-m.bit_length()
    return m<<shift,e-shift
def rounded_ratio(n,d):
    q=0
    for bit in range(24,-1,-1):
        unit=d<<bit
        if n>=unit:n-=unit;q|=1<<bit
    assert n<d
    return q+int(n*2>d or (n*2==d and q&1))
def exact_div(x,c):
    mag=x&MASK;sign=x&0x80000000
    if mag>=INF or not 0<c<INF:return False,False,0
    if not mag:return True,True,sign
    mx,ex=normalize(mag);mc,ec=normalize(c);d=ex-ec
    e=d-int(mx<mc)
    if e>127:return True,False,sign|INF
    if e>=-126:
        q=rounded_ratio(mx<<(d-e+23),mc)
        if q==0x1000000:q>>=1;e+=1
        if e>127:return True,False,sign|INF
        return True,True,sign|((e+127)<<23)|(q-0x800000)
    if d<=-151:return True,True,sign
    shift=d+149
    q=rounded_ratio(mx,mc<<1) if shift==-1 else rounded_ratio(mx<<shift,mc)
    return True,True,sign|q
def compare(a,ea,b,eb):
    if not a or not b:return 0 if a==b else -1 if not a else 1
    la,lb=a.bit_length(),b.bit_length();ta,tb=ea+la,eb+lb
    if ta!=tb:return -1 if ta<tb else 1
    if la<lb:a<<=lb-la
    elif lb<la:b<<=la-lb
    return (a>b)-(a<b)
def midpoint_compare(x,c,k,e):
    mx,ex=decode(x);mc,ec=decode(c)
    return compare(mx,ex,k*mc,e+ec)
def certifies(x,c,q):
    mag=x&MASK
    if mag>=INF or not 0<c<INF or not 0<=q<INF:return False
    even=not q&1
    if q==0:return midpoint_compare(mag,c,1,-150)<=0
    m,e=decode(q);k=2*m-1;le=e-1
    if q>>23>1 and not q&0x7fffff:k=4*m-1;le=e-2
    lo=midpoint_compare(mag,c,k,le)
    if lo<0 or (lo==0 and not even):return False
    hi=midpoint_compare(mag,c,2*m+1,e-1)
    return hi<0 or (hi==0 and even)

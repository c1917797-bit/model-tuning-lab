"""Independent Fraction-derived raw-bit fixtures; no torch/device imports."""
import importlib.util
from pathlib import Path
import random
BASE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("damp_prefill_float_independent",BASE/"independent_float_div.py")
gold=importlib.util.module_from_spec(spec);spec.loader.exec_module(gold)
GUARDS=(0x13579bdf,0x2468ace0,0x10293847,0x31415926)
INPUT_GUARDS=(0x11223344,0x22334455,0x33445566)
def signed(bits):
    return bits if bits<0x80000000 else bits-0x100000000
def rows():
    raw=[]
    xs=[0,1,2,0x003fffff,0x007fffff,0x00800000,0x00800001,0x00ffffff,
        0x3eaaaaab,0x3f000000,0x3f7fffff,0x3f800000,0x3f800001,
        0x40000000,0x7e800000,0x7f000000,gold.MAX]
    cs=[1,2,0x007fffff,0x00800000,0x00800001,0x3f000000,0x3f7fffff,
        0x3f800000,0x3f800001,0x3f8ccccd,0x40000000,gold.MAX]
    for x in xs:
        for c in cs:
            for sign in (0,0x80000000):raw.append((x|sign,c,"extreme-cross"))
    qs=[0,1,2,0x007ffffe,0x007fffff,0x00800000,0x00800001,0x01000000,
        0x3effffff,0x3f000000,0x3f7fffff,0x3f800000,0x3f800001,
        0x40000000,gold.MAX-1,gold.MAX]
    for q in qs:
        for c in (1,2,0x007fffff,0x00800000,0x00800001,0x3f800000,0x3f8ccccd,gold.MAX):
            for upper in (False,True):
                if not q and not upper:continue
                seed=gold.rounded_fraction(gold.midpoint(q,upper)*gold.value(c))
                if seed==gold.INF:seed=gold.MAX
                for x in (seed-1,seed,seed+1):
                    if 0<=x<=gold.MAX:
                        for sign in (0,0x80000000):
                            raw.append((x|sign,c,"midpoint-preimage-neighbor"))
    rng=random.Random(20261007)
    for _ in range(6000):
        raw.append((rng.randrange(gold.MAX+1)|(rng.randrange(2)<<31),
                    rng.randrange(1,gold.MAX+1),"random"))
    for x,c in ((gold.INF,0x3f800000),(0xff800000,1),(0x7fc00001,1),(0,0),
                (1,0x80000000),(1,0xbf800000),(1,gold.INF),(1,0x7fc00000)):
        raw.append((x,c,"invalid"))
    result=[]
    for i,(x,c,label) in enumerate(raw):
        valid,finite,bits=gold.oracle(x,c);q=bits&0x7fffffff
        proposals=(q,max(0,q-1),min(gold.INF,q+1),gold.INF,0x80000000)
        proposal=proposals[i%len(proposals)]
        accepted=gold.oracle_certificate(x,c,proposal)
        result.append(dict(x=x,c=c,proposal=proposal,valid=int(valid),finite=int(finite),
                           bits=bits,accepted=int(accepted),label=label))
    return result
def matrix_chunks(n):
    data=rows()
    for index,start in enumerate(range(0,len(data),n)):
        chunk=data[start:start+n]
        chunk+=data[:n-len(chunk)]
        yield "matrix-%d-%d"%(n,index),chunk
def changing_rows(n,turn):
    rng=random.Random(93247+turn+n)
    out=[]
    for i in range(n):
        x=rng.randrange(gold.MAX+1)|(rng.randrange(2)<<31)
        c=(1,0x007fffff,0x00800000,0x3f8ccccd,gold.MAX)[(i+turn)%5]
        valid,finite,bits=gold.oracle(x,c);q=bits&0x7fffffff
        proposal=q if i%3 else max(0,q-1)
        out.append(dict(x=x,c=c,proposal=proposal,valid=int(valid),finite=int(finite),
                        bits=bits,accepted=int(gold.oracle_certificate(x,c,proposal)),
                        label="changing-%d"%turn))
    return out

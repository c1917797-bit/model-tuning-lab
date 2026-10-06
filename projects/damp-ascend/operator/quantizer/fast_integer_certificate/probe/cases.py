# SPDX-License-Identifier: Apache-2.0
"""Diagnostic fixture stream. Independent Fraction oracle is frozen/read-only."""
import hashlib
import struct
import sys
from pathlib import Path
CERT=Path(__file__).resolve().parent.parent
QUANT=CERT.parent
sys.path.insert(0,str(QUANT)); sys.path.insert(0,str(CERT))
from integer_certificate import tables, certificate, floor_endpoint
from test_integer_certificate import threshold_independent, normal_floor_fraction
from test_exact_quantizer import exact_fraction, oracle
from probe_fixtures import build_fixtures, fixture_sha
GUARDS=(0x13579bdf,0x2468ace0,0x10293847,0x31415926,0x27182818,0x456789ab,0x56789abc)
NAMES=("accepted","lowerFloor","upperFloor","lowerDomain","upperDomain","finalSignedCode","finalValid")
MANTISSAS=(0,1,2,4094,4095,4096,4097,0x3ffffe,0x3fffff,0x7ffffd,0x7ffffe,0x7fffff)
LUT_HASHES=("7c6e8dbfe3ea2a3dcaf62ab2ef14936d2d9252a36738eb6b78ba4b1d37c7c708",
            "2df58f09be50ce6051418c229acf641a37c9596f1826884ee02d7a02b1581a83",
            "c58fdd435e302b9209203dcbdd38b7e456bed8f0d425d9f7339ca5b46e3582c8")
def lut_hashes():
    t=tables()
    c=b"".join(struct.pack("<i",r[0]) for r in t)
    f=b"".join(struct.pack("<i",r[1]) for r in t)
    return tuple(hashlib.sha256(b).hexdigest() for b in (c,f,c+f))
def signed(bits):
    return bits if bits<(1<<31) else bits-(1<<32)
def golden(row):
    x,s,n=row["x_bits"],row["scale_bits"],row["proposal"]
    if not 0<=n<=127: raise ValueError("proposal outside0..127")
    lv,lo=floor_endpoint(s,max(n-1,0))
    uv,up=floor_endpoint(s,min(n,126))
    # Independent product floor verifies every valid endpoint. Invalid floor is
    # only a safe, clamped synthetic placeholder, never a transition authority.
    if 0x00800000<=s<=0x7f7fffff:
        independent_lo=normal_floor_fraction(exact_fraction(s)*threshold_independent(max(n-1,0)))
        independent_up=normal_floor_fraction(exact_fraction(s)*threshold_independent(min(n,126)))
        assert lv==(independent_lo is not None) and uv==(independent_up is not None)
        if lv: assert lo==independent_lo
        if uv: assert up==independent_up
    else:
        assert not lv and not uv
    accepted=certificate(x,s,n)
    valid,code=oracle(x,s)
    if accepted: assert valid and (-n if x>>31 else n)==code
    return (int(accepted),lo,up,int(lv),int(uv),code,int(valid))
def labeled_fixtures():
    rows=build_fixtures(2048)
    assert len(rows)==40316 and fixture_sha(rows)=="1c10a0a47fd9edd1c862d05bb55e39ae2dc06526c4cdbbf70f415b58e6d80e32"
    return rows
def endpoint_rows():
    # proposal j+1 exposes all127 transitions in lowerFloor. x0 lets fallback
    # return early; this is limb/domain correctness, not a performance workload.
    for e in range(1,255):
        for m in MANTISSAS:
            for j in range(127):
                yield {"label":f"endpoint_e{e}_m{m}_j{j}","x_bits":0,
                       "scale_bits":(e<<23)+m,"proposal":j+1}
def proposal_rows(rows):
    for row in rows:
        k=abs(row["code"])
        # Keep all5 labels even when clamp produces duplicate magnitudes.
        for label,n in (("zero",0),("clip",127),("minus",max(0,k-1)),
                        ("correct",k),("plus",min(127,k+1))):
            yield {**row,"label":row["label"]+"_"+label,"proposal":n}
    for i,row in enumerate(rows):
        if i%257==0:
            for n in range(128):
                yield {**row,"label":row["label"]+f"_arbitrary{n}","proposal":n}
def chunks(stream,name,count=896):
    chunk=[]; begin=0
    for row in stream:
        chunk.append(row)
        if len(chunk)==count:
            yield f"{name}_{begin}",chunk,count
            begin+=count; chunk=[]
    if chunk:
        useful=len(chunk)
        chunk+= [{"label":"padding_saved_step45","x_bits":0xbd05a10e,
                  "scale_bits":0x39919209,"proposal":118}]*(count-useful)
        yield f"{name}_{begin}",chunk,useful
def lifecycle_rows(rows,count,repeat):
    # Deliberately changed inputs, sign/domain/pointer/lane boundary coverage.
    result=[]
    invalid=[r for r in rows if not r["valid"]]
    for i in range(count):
        r=rows[(repeat*997+i*127)%len(rows)]
        if i<len(invalid): r=invalid[i]
        if i in (0,count-1,63,64): r=rows[0]
        k=abs(r["code"])
        n=(k, max(0,k-1),min(127,k+1),0,127)[(i+repeat)%5]
        result.append({**r,"proposal":n,"label":r["label"]+f"_lifecycle{repeat}_{i}"})
    return result


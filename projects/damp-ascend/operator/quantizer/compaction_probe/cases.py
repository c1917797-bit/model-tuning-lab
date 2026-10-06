# SPDX-License-Identifier: Apache-2.0
"""Independent Fraction RN32->RNE fixture oracle; never imports candidate bits helper."""
import hashlib
import importlib.util
import random
from pathlib import Path

ORACLE_SHA="b1c9d10bf9e24e095fe048235693e426f5437be27a9e21b39503bd7825a50c3d"
EXACT_SHA="f5d380534d34d6e4148d94fcfec35b294ca8ca38d09316d98b11e7f645ff6169"
GUARDS=(0x13579BDF,0x2468ACE0,0x31415926,0x12345678)
INPUT_GUARDS=(0x10203040,0x20304050,0x30405060,0x40506070)
INDEX_FILL,COUNT_FILL=-777777,-888888
SAVED45=(0xBD05A10E,0x39919209)

def math_oracle():
    p=Path(__file__).resolve().parent.parent/"test_exact_quantizer.py"
    if hashlib.sha256(p.read_bytes()).hexdigest()!=ORACLE_SHA:
        raise RuntimeError("independent Fraction oracle source changed")
    spec=importlib.util.spec_from_file_location("damp_compaction_fraction_oracle",p)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def unsigned_to_i32(x):
    return x if x < (1<<31) else x-(1<<32)

def pool():
    o=math_oracle()
    rows=[SAVED45,(0,1),(0x80000000,1),(0x7f7fffff,1),(1,0x7f7fffff),
          (1,1),(0x007fffff,0x00800000),(0x00800000,0x007fffff)]
    # All parity half boundaries +/-1ULP, both signs, and non-power-of-two scales.
    for j in range(127):
        for scale in (0x3f800000,0x3f8ccccd,0x39919209):
            xb=o.mul_f32_bits(o.half_bits(j),scale)
            for d in (-1,0,1):
                if 0<=xb+d<=0x7f7fffff:
                    rows.extend(((xb+d,scale),((xb+d)|0x80000000,scale)))
    return rows

def masks(n):
    yield "none_rejected",[1]*n
    yield "all_rejected",[0]*n
    yield "none_after_all",[1]*n
    for lane in sorted({0,31,32,63,64,n-1}):
        if lane<n:
            a=[1]*n;a[lane]=0
            yield "single_"+str(lane),a
    yield "even_rejected",[i%2 for i in range(n)]
    yield "odd_rejected",[(i+1)%2 for i in range(n)]
    rng=random.Random(0xC0A02026+n)
    for percent in (1,10,50,90):
        yield "random_"+str(percent),[int(rng.randrange(100)>=percent) for _ in range(n)]
    yield "invalid_domain_all_rejected",[0]*n
    yield "none_after_invalid",[1]*n

def fixtures():
    o=math_oracle(); rows=pool()
    invalids=[(0x7f800000,0x3f800000),(0x7fc00000,0x3f800000),
              (0xff800000,0x3f800000),(1,0),(1,0x80000000),(1,0xbf800000),
              (1,0x7f800000),(1,0x7fc00000)]
    for n in (64,448,896):
        for turn,(name,a) in enumerate(masks(n)):
            offset=(turn*137+n)%len(rows)
            chosen=[rows[(offset+i*37)%len(rows)] for i in range(n)]
            chosen[0]=SAVED45  # stable real failure row, every mask generation
            if name.startswith("invalid_"):
                for i,row in enumerate(invalids): chosen[i]=row
            expected=[o.oracle(x,s) for x,s in chosen]
            # Accepted flags/proposals here are pre-certified mathematical inputs.
            # Deliberately wrong rejected proposals prove sparse scatter overwrite.
            proposal=[abs(code) if flag else (abs(code)+17)%128
                      for flag,(valid,code) in zip(a,expected)]
            if any(flag and not valid for flag,(valid,code) in zip(a,expected)):
                raise AssertionError("invalid accepted fixture")
            reject=[i for i,v in enumerate(a) if not v]
            raw=[a,[unsigned_to_i32(x) for x,s in chosen],
                 [unsigned_to_i32(s) for x,s in chosen],proposal]
            interiors=[[code for valid,code in expected],
                       reject+[INDEX_FILL]*(n-len(reject)),
                       [len(reject)]+[COUNT_FILL]*(n-1),
                       [int(valid) for valid,code in expected]]
            outputs=[[GUARDS[j]]*8+v+[GUARDS[j]]*8 for j,v in enumerate(interiors)]
            roots=[[INPUT_GUARDS[j]]*8+v+[INPUT_GUARDS[j]]*8
                   for j,v in enumerate(raw)]
            yield {"n":n,"turn":turn,"name":name,"inputs":raw,"roots":roots,
                   "outputs":outputs,"rejected":reject}

def software_gate():
    cases=list(fixtures())
    counts={str(n):0 for n in (64,448,896)}
    for c in cases:
        n=c["n"]; counts[str(n)]+=1
        r=c["rejected"]
        assert r==sorted(set(r)) and all(0<=i<n for i in r)
        assert c["outputs"][2][8]==len(r)
        assert all(len(v)==n+16 for v in c["roots"]+c["outputs"])
        for i in r:
            assert c["outputs"][0][8+i] != (
                -c["inputs"][3][i] if c["inputs"][1][i]<0 else c["inputs"][3][i])
    assert math_oracle().oracle(*SAVED45)==(True,-118)
    digest=hashlib.sha256(repr(cases).encode()).hexdigest()
    return {"status":"pass","cases":len(cases),"cases_by_n":counts,
            "fixture_sha256":digest,"scope":"stdlib fixtures ONLY",
            "npu_executed":False,"graph_executed":False,"performance_measured":False}

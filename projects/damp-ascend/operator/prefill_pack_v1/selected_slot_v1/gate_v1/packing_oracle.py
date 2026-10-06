"""Independent CPU packing; no production float/INT8 helper imports."""
from functools import lru_cache
import struct
from fraction_locator import divide

@lru_cache(maxsize=65536)
def exact_divide(x,c):
    return divide(x,c)

def transform(torch,dense,sr,pv,pk):
    if dense.device.type!="cpu" or sr.device.type!="cpu": raise ValueError("CPU oracle inputs")
    # Original-coordinate x/c rounded by Fraction distances, not vector Div.
    raw=dense.contiguous().view(torch.int32)
    c_raw=sr.contiguous().view(torch.int32)
    out=torch.empty_like(raw)
    for head in range(12):
        for ov in range(128):
            cb=int(c_raw[head,ov])&0xffffffff
            values=raw[:,head,ov].reshape(-1).tolist()
            words=[]
            for value in values:
                valid,finite,bits=exact_divide(int(value)&0xffffffff,cb)
                if not valid or not finite: raise ValueError("nonfinite/invalid exact transform")
                words.append(bits if bits<0x80000000 else bits-0x100000000)
            out[:,head,ov]=torch.tensor(words,dtype=torch.int32).view(dense.shape[0],128)
    scaled=out.view(torch.float32)
    reordered=torch.empty_like(scaled)
    for head in range(12):
        reordered[:,head]=scaled[:,head].index_select(1,pv[head].long()).index_select(2,pk[head].long())
    return reordered

def pack(torch,independent,dense,layout):
    transformed=transform(torch,dense,layout.c,layout.pv,layout.pk)
    return independent.pack_value_major(transformed,layout)

def fixture(torch,p,turn):
    generator=torch.Generator(device="cpu").manual_seed(260627513+p*4099+turn)
    result=torch.randint(-256,257,(p,12,128,128),generator=generator).float()*(2**-10)
    # Original source words include signed zero and normal/subnormal neighbors.
    words=result.view(torch.int32)
    edges=[0,0x80000000,1,0x80000001,0x007fffff,0x807fffff,
           0x00800000,0x80800000,0x3f800000,0xbf800000,0x3f800001,0x3f7fffff]
    for i,b in enumerate(edges):
        words.view(-1)[i]=b if b<0x80000000 else b-0x100000000
    return result

def layout(torch,independent,general=True):
    generator=torch.Generator(device="cpu").manual_seed(260627513)
    pk=torch.stack([torch.randperm(128,generator=generator) for _ in range(12)]).int()
    pv=torch.stack([torch.randperm(128,generator=generator) for _ in range(12)]).int()
    if general:
        palette=torch.tensor([.7,1.0,1.1,1.3,1.7,2.3,3.1],dtype=torch.float32)
        sr=palette[(torch.arange(12)[:,None]*19+torch.arange(128)[None,:])%7].contiguous()
    else: sr=torch.ones(12,128,dtype=torch.float32)
    return independent.OracleLayout(sr,pv,pk)

def seed(torch,independent,slots,plan):
    generator=torch.Generator(device="cpu").manual_seed(260627513+slots)
    transformed=torch.randint(-128,129,(slots,12,128,128),generator=generator).float()*(2**-11)
    return independent.pack_value_major(transformed,plan)

def selected_update(golden,packed,indices):
    for name in ("high","low","scales"):
        getattr(golden,name).index_copy_(0,indices.long(),getattr(packed,name))

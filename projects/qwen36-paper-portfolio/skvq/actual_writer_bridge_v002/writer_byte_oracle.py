"""Independent SKVQ byte equations. Never imports/calls candidate pack/quantize/writer.
Scalar baseline and NumPy vectorization both apply EACH declared A16 rounding.
NumPy reductions are min/max only; no candidate labels/score/reference sharing.
"""
import math,struct
def require(v,m):
    if not v:raise ValueError(m)
def scalar(x,kind):
    require(math.isfinite(x),"finite affine scalar")
    if kind=="float16":return struct.unpack("<e",struct.pack("<e",x))[0]
    require(kind=="bfloat16","original A16 kind")
    u=struct.unpack("<I",struct.pack("<f",x))[0];u=(u+32767+((u>>16)&1))&0xffff0000
    return struct.unpack("<f",struct.pack("<I",u))[0]
def scalar_bytes(values,kind):
    if kind=="float16":return b"".join(struct.pack("<e",x)for x in values)
    require(kind=="bfloat16","A16 kind")
    return b"".join(struct.pack("<H",struct.unpack("<I",struct.pack("<f",x))[0]>>16)for x in values)
def values(raw,kind):
    require(len(raw)%2==0,"whole A16 bytes")
    if kind=="float16":return [x[0]for x in struct.iter_unpack("<e",raw)]
    require(kind=="bfloat16","A16 kind")
    return [struct.unpack("<f",struct.pack("<I",x[0]<<16))[0]for x in struct.iter_unpack("<H",raw)]
def geometry(layout,bits):
    p=layout["permutation"];s=layout["starts"];n=8//bits if type(bits)is int and bits in(2,4)else 0
    require(n and len(p)>0 and all(type(x)is int for x in p)and sorted(p)==list(range(len(p)))and
      len(s)>=2 and s[0]==0 and s[-1]==len(p)and all(type(x)is int for x in s)and
      all(a<b for a,b in zip(s,s[1:]))and len(layout["smooth"])==len(p)and
      all(type(x)in(int,float)and math.isfinite(x)and x>0 for x in layout["smooth"])and
      type(layout["clip"])in(int,float)and .91<=layout["clip"]<=.97,"complete independent byte geometry")
    return n,[(b-a+n-1)//n for a,b in zip(s,s[1:])]
def encode_scalar(raw,layout,bits,kind):
    n,widths=geometry(layout,bits);data=values(raw,kind);dim=len(layout["permutation"])
    require(len(data)%dim==0 and data,"whole nonempty row input")
    payload=bytearray();ss=[];zz=[];rd=lambda x:scalar(x,kind);maximum=(1<<bits)-1
    for begin in range(0,len(data),dim):
        row=data[begin:begin+dim]
        arranged=[rd(rd(row[i])*rd(layout["smooth"][i]))for i in layout["permutation"]]
        for (a,b),width in zip(zip(layout["starts"],layout["starts"][1:]),widths):
            group=arranged[a:b];low=rd(min(group)*rd(layout["clip"]));high=rd(max(group)*rd(layout["clip"]))
            scale=max(rd(rd(high-low)/maximum),rd(1e-5))
            codes=[int(round(min(max(rd(rd(x-low)/scale),0),maximum)))for x in group]
            codes += [0]*(width*n-len(codes))
            for j in range(width):payload.append(sum(codes[j*n+k]<<(bits*(n-1-k))for k in range(n)))
            ss.append(scale);zz.append(low)
    return dict(payload=bytes(payload),scales=scalar_bytes(ss,kind),zero_points=scalar_bytes(zz,kind))
def encode_numpy(raw,layout,bits,kind,np):
    """Vectorized independent direct equations; actual np qualification belongs to caller."""
    n,widths=geometry(layout,bits);dim=len(layout["permutation"])
    require(raw and len(raw)%(dim*2)==0,"whole original A16 rows")
    def rd(x):
        a=np.asarray(x,dtype=np.float64)
        require(bool(np.isfinite(a).all()),"finite independent vector")
        if kind=="float16":return a.astype("<f2").astype(np.float64)
        require(kind=="bfloat16","original A16 kind")
        u=a.astype("<f4").view("<u4")
        u=(u+np.uint32(32767)+((u>>np.uint32(16))&np.uint32(1)))&np.uint32(0xffff0000)
        return u.view("<f4").astype(np.float64)
    def encode(x):
        if kind=="float16":return np.asarray(x,dtype="<f2").tobytes(order="C")
        u=np.asarray(x,dtype="<f4").view("<u4")
        return (u>>np.uint32(16)).astype("<u2").tobytes(order="C")
    if kind=="float16":data=np.frombuffer(raw,dtype="<f2").astype(np.float64)
    else:
        require(kind=="bfloat16","original A16 kind")
        data=(np.frombuffer(raw,dtype="<u2").astype("<u4")<<np.uint32(16)).view("<f4").astype(np.float64)
    data=data.reshape(-1,dim);arranged=rd(rd(data)*rd(layout["smooth"]))[:,layout["permutation"]]
    maximum=(1<<bits)-1;packed=[];scales=[];zeros=[]
    for (a,b),width in zip(zip(layout["starts"],layout["starts"][1:]),widths):
        v=arranged[:,a:b];low=rd(np.min(v,axis=1)*rd(layout["clip"]))
        high=rd(np.max(v,axis=1)*rd(layout["clip"]))
        scale=np.maximum(rd(rd(high-low)/maximum),rd(1e-5))
        codes=np.rint(np.clip(rd(rd(v-low[:,None])/scale[:,None]),0,maximum)).astype(np.uint8)
        codes=np.pad(codes,((0,0),(0,width*n-(b-a))),mode="constant").reshape(len(data),width,n)
        field=np.zeros((len(data),width),dtype=np.uint8)
        for j in range(n):field|=codes[:,:,j]<<(bits*(n-1-j))
        packed.append(field);scales.append(scale);zeros.append(low)
    return dict(payload=np.concatenate(packed,axis=1).tobytes(order="C"),
      scales=encode(np.stack(scales,axis=1)),zero_points=encode(np.stack(zeros,axis=1)))
def check_axis(observation,input_bytes,layout,bits,kind,read,*,vector=None):
    """All published before/after planes checked independently; untouched rows and input."""
    n,widths=geometry(layout,bits);stride=sum(widths);groups=len(widths)
    total=observation["tokens"];start,stop=observation["middle"]
    require(type(total)is int and type(start)is int and type(stop)is int and 0<start<stop<total,
      "explicit sink/middle/recent domain")
    dim=len(layout["permutation"])
    require(len(input_bytes)==total*dim*2 and observation["shape"]==[total,dim]and
      observation["returned_bytes"]==(stop-start)*(stride+4*groups),"original full row extent/actual writer bytes")
    require(read(observation["input_after_ref"])==input_bytes,"all original inputs unchanged after actual writer")
    chunk=input_bytes[start*dim*2:stop*dim*2]
    expected=encode_scalar(chunk,layout,bits,kind)if vector is None else encode_numpy(chunk,layout,bits,kind,vector)
    for name,width,unit in(("payload",stride,1),("scales",groups,2),("zero_points",groups,2)):
        row_bytes=width*unit;before=read(observation["before"][name]);after=read(observation["after"][name])
        require(len(before)==len(after)==total*row_bytes,"complete plane byte domain")
        require(before[:start*row_bytes]==after[:start*row_bytes]and before[stop*row_bytes:]==after[stop*row_bytes:],
          "complete untouched sink/recent guard rows")
        require(after[start*row_bytes:stop*row_bytes]==expected[name],"exact original affine/round/pack plane "+name)
    return dict(tokens=total,middle_tokens=stop-start,stride=stride,groups=groups,
      full_input_unchanged=True,full_sink_recent_guard_unchanged=True,
      exact_payload_scales_zero_points=True,independent_candidate_math_not_called=True)

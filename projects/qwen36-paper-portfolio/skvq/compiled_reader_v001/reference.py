"""Independent original-byte SKVQ equations; no candidate map/pack/kernel import.
A16 affine mul/add, original channel permutation, QK/scale/prob/output rounding.
FP64 fsum/exp is the adjudication reference; device FP32 reductions must meet .005.
"""
import math,struct
def require(value,message):
    if not value:raise ValueError(message)
def scalar(value,kind):
    require(math.isfinite(value),"finite reference scalar")
    if kind=="float16":return struct.unpack("<e",struct.pack("<e",value))[0]
    require(kind=="bfloat16","A16 kind")
    u=struct.unpack("<I",struct.pack("<f",value))[0]
    u=(u+32767+((u>>16)&1))&0xffff0000
    return struct.unpack("<f",struct.pack("<I",u))[0]
def values(raw,kind):
    require(type(raw)is bytes and len(raw)%2==0,"complete A16 bytes")
    if kind=="float16":return [x[0]for x in struct.iter_unpack("<e",raw)]
    require(kind=="bfloat16","A16 kind")
    return [struct.unpack("<f",struct.pack("<I",x[0]<<16))[0]for x in struct.iter_unpack("<H",raw)]
def bytes_a16(items,kind):
    x=[scalar(v,kind)for v in items]
    if kind=="float16":return b"".join(struct.pack("<e",v)for v in x)
    return b"".join(struct.pack("<H",struct.unpack("<I",struct.pack("<f",v))[0]>>16)for v in x)
def geometry(layout,bits):
    p=layout["permutation"];s=layout["starts"]
    require(type(bits)is int and bits in(2,4)and len(p)==256 and sorted(p)==list(range(256))and
      all(type(x)is int for x in p+s)and len(s)==5 and s[0]==0 and s[-1]==256 and
      all(a<b for a,b in zip(s,s[1:]))and layout["smooth"]==[1.]*256 and layout["clip"]==.95,"independent complete local-group geometry")
    n=8//bits
    return n,[(b-a+n-1)//n for a,b in zip(s,s[1:])]
def decode_axis(payload,scales,zeros,original,layout,bits,kind,length):
    n,widths=geometry(layout,bits);stride=sum(widths);ss=values(scales,kind);zz=values(zeros,kind);dense=values(original,kind)
    require(type(length)is int and 1<=length<=33792 and len(dense)==length*256 and
      len(payload)==length*stride and len(ss)==len(zz)==length*4,"whole packed/dense original byte extents")
    start=min(5,length);stop=max(start,length-128);result=[]
    for t in range(length):
        row=dense[t*256:(t+1)*256]
        if start<=t<stop:
            offset=t*stride
            for g,(a,b)in enumerate(zip(layout["starts"],layout["starts"][1:])):
                for j in range(b-a):
                    byte=payload[offset+j//n]
                    code=(byte>>(bits*(n-1-j%n)))&((1<<bits)-1)
                    original_channel=layout["permutation"][a+j]
                    # Never use the candidate's address table, padding or decoded values.
                    row[original_channel]=scalar(scalar(code*ss[t*4+g],kind)+zz[t*4+g],kind)
                offset+=widths[g]
        require(all(math.isfinite(x)for x in row),"complete decoded row finite")
        result.append(row)
    return result
def attention(query,key,value,kind):
    require(len(query)==6 and len(key)==len(value)>0 and all(len(x)==256 for x in query+key+value),"complete Q6/KV1/D256")
    scores=[];probs=[];output=[]
    for head in query:
        score=[scalar(scalar(math.fsum(x*y for x,y in zip(head,row)),kind)*.0625,kind)for row in key]
        maximum=max(score);exp=[math.exp(x-maximum)for x in score];denom=math.fsum(exp)
        prob=[scalar(x/denom,kind)for x in exp]
        out=[scalar(math.fsum(p*row[c]for p,row in zip(prob,value)),kind)for c in range(256)]
        scores.extend(score);probs.extend(prob);output.extend(out)
    return dict(output=bytes_a16(output,kind),scores=bytes_a16(scores,kind),probabilities=bytes_a16(probs,kind))
def compare(actual,expected,kind):
    a=values(actual,kind);e=values(expected,kind)
    require(len(a)==len(e)>0 and all(math.isfinite(x)for x in a+e),"every actual output checked/finite")
    n=math.fsum(x*x for x in e);d=math.fsum((x-y)**2 for x,y in zip(a,e))
    rms=math.sqrt(d/max(n,1e-30));require(rms<=.005,"unchanged relative RMS .005")
    return dict(relative_rms=rms,threshold_relative_rms=.005,elements=len(a),all_finite=True)
def decode_numpy(payload,scales,zeros,original,layout,bits,kind,length,np):
    """Same independent equations vectorized; no candidate mapping table."""
    n,widths=geometry(layout,bits);stride=sum(widths)
    def vals(raw):
        if kind=="float16":return np.frombuffer(raw,dtype="<f2").astype(np.float64)
        return (np.frombuffer(raw,dtype="<u2").astype("<u4")<<np.uint32(16)).view("<f4").astype(np.float64)
    def rd(a):
        a=np.asarray(a,dtype=np.float64);require(bool(np.isfinite(a).all()),"finite independent vector")
        if kind=="float16":return a.astype("<f2").astype(np.float64)
        u=a.astype("<f4").view("<u4");u=(u+np.uint32(32767)+((u>>np.uint32(16))&np.uint32(1)))&np.uint32(0xffff0000)
        return u.view("<f4").astype(np.float64)
    require(1<=length<=33792 and len(payload)==length*stride and len(scales)==len(zeros)==length*8 and
      len(original)==length*512,"independent complete physical plane byte extents")
    result=vals(original).reshape(length,256).copy();ss=vals(scales).reshape(length,4);zz=vals(zeros).reshape(length,4)
    codes=np.frombuffer(payload,dtype=np.uint8).reshape(length,stride);start=min(5,length);stop=max(start,length-128)
    offset=0
    for g,(a,b)in enumerate(zip(layout["starts"],layout["starts"][1:])):
        for j in range(b-a):
            field=(codes[start:stop,offset+j//n]>>np.uint8(bits*(n-1-j%n)))&np.uint8((1<<bits)-1)
            result[start:stop,layout["permutation"][a+j]]=rd(rd(field.astype(np.float64)*ss[start:stop,g])+zz[start:stop,g])
        offset+=widths[g]
    require(bool(np.isfinite(result).all()),"all decoded keys/values finite")
    return result
def attention_numpy(query,key,value,kind,np):
    """Vectorize multiplication only; fsum/exp and A16 rounding remain scalar baseline."""
    query=np.asarray(query,dtype=np.float64);key=np.asarray(key,dtype=np.float64);value=np.asarray(value,dtype=np.float64)
    require(query.shape==(6,256)and key.shape==value.shape and len(key.shape)==2 and key.shape[1]==256 and
      bool(np.isfinite(query).all())and bool(np.isfinite(key).all())and bool(np.isfinite(value).all()),"true Q6/KV1/D256 reference")
    score=[];prob=[];output=[]
    for q in query:
        products=key*q[None,:]
        s=[scalar(scalar(math.fsum(row),kind)*.0625,kind)for row in products]
        maximum=max(s);ex=[math.exp(x-maximum)for x in s];denominator=math.fsum(ex)
        p=[scalar(x/denominator,kind)for x in ex]
        weighted=value*np.asarray(p,dtype=np.float64)[:,None]
        o=[scalar(math.fsum(weighted[:,c]),kind)for c in range(256)]
        score.extend(s);prob.extend(p);output.extend(o)
    return dict(output=bytes_a16(output,kind),scores=bytes_a16(score,kind),probabilities=bytes_a16(prob,kind))

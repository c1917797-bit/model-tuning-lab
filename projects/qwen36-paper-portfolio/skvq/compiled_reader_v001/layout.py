"""SKVQ-specific address map; no Torch, Triton or candidate quantization import."""
def need(value,message):
    if not value:raise ValueError(message)
def validate(layout):
    need(type(layout)is dict and set(layout)=={"permutation","starts","smooth","clip"},"exact layout fields")
    p=layout["permutation"];s=layout["starts"]
    need(type(p)is list and len(p)==256 and all(type(i)is int for i in p)and sorted(p)==list(range(256)),"local256 bijection")
    need(type(s)is list and len(s)==5 and all(type(i)is int for i in s)and s[0]==0 and s[-1]==256 and
      all(a<b for a,b in zip(s,s[1:])),"four nonempty TP-local groups")
    need(layout["smooth"]==[1.]*256 and layout["clip"]==.95,"named smoothOFF/clip.95 adaptation")
    return layout
def addresses(layout,bits):
    validate(layout);need(type(bits)is int and bits in(2,4),"Q2/Q4 only")
    pack=8//bits;rows=[None]*256;offset=0
    for g,(start,end)in enumerate(zip(layout["starts"],layout["starts"][1:])):
        for j in range(end-start):
            original=layout["permutation"][start+j]
            rows[original]=[offset+j//pack,bits*(pack-1-j%pack),g]
        offset+=(end-start+pack-1)//pack
    need(all(x is not None for x in rows),"every original output channel assigned")
    return rows,offset
def interval(length):
    need(type(length)is int and 1<=length<=33792,"actual context capacity")
    start=min(5,length);stop=max(start,length-128)
    return start,stop
def edge_index(token,length):
    start,stop=interval(length);need(type(token)is int and 0<=token<length,"actual token")
    need(not start<=token<stop,"middle has no unquantized edge alias")
    return token if token<start else start+token-stop

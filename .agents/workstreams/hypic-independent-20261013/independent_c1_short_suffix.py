"""Default-off caller-owned correction of short live suffix execution.

Uses the independently derived token recurrence on raw post-convolution Q/K/V.
No native state slots, cached-body recomputation, loader or device launch.
"""
from independent_recurrent_boundary import recurrent_boundary

def align_short_suffixes(layout,q,k,v,g,beta,seeds,output,terminals):
    if seeds.ndim!=4 or terminals.shape!=seeds.shape or len(layout.windows)!=seeds.shape[0]:
        raise ValueError("complete private per-window seed/terminal ABI required")
    if q.ndim!=4 or q.shape!=k.shape or q.shape[0]!=1 or v.shape[:2]!=q.shape[:2]:
        raise ValueError("raw packed grouped Q/K/V required")
    if (output.shape!=(1,q.shape[1],v.shape[2],v.shape[3])
            or seeds.shape[1:]!=(v.shape[2],q.shape[3],v.shape[3])
            or g.shape!=v.shape[:3] or beta.shape!=g.shape):
        raise ValueError("complete output/state/gate ABI required")
    if any(x.device!=q.device for x in(k,v,g,beta,seeds,output,terminals)):
        raise ValueError("single private device required")
    jobs=[];seen=set()
    for rid,chain in zip(layout.request_ids,layout.chains):
        if len(chain)!=3:continue
        if tuple(kind for kind,key in chain)!=("live","cached","live"):
            raise ValueError("explicit prefix/body/suffix chain required")
        j=chain[-1][1]
        if type(j)is not int or not 0<=j<len(layout.windows) or j in seen:
            raise ValueError("unique valid suffix window required")
        seen.add(j);w=layout.windows[j];n=w.packed_end-w.packed_start
        if (w.request_id!=rid or not 0<=w.packed_start<w.packed_end<=q.shape[1]
                or n!=w.source_end-w.source_start):
            raise ValueError("exact source/packed suffix geometry required")
        jobs.append((rid,j,w,n))
    # Work only on private clones: an exception cannot partially alter caller buffers.
    y=output.clone();h=terminals.clone();routes=[]
    for rid,j,w,n in jobs:
        if n>64:continue
        span=slice(w.packed_start,w.packed_end)
        value,state=recurrent_boundary(q[:,span],k[:,span],v[:,span],
                                       g[:,span],beta[:,span],seeds[j:j+1])
        y[:,span].copy_(value.to(y.dtype));h[j].copy_(state[0].to(h.dtype))
        routes.append(dict(request_id=rid,job=j,window="suffix",rows=n,
            source_start=w.source_start,source_end=w.source_end,
            packed_start=w.packed_start,packed_end=w.packed_end,
            branch="independent_recurrent_le64",output_and_terminal=True))
    return y,h,routes

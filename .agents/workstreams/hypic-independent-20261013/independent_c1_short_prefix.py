"""Own canonical short-prefix terminal intervention; no runtime activation."""
from independent_recurrent_boundary import recurrent_boundary

def align_short_prefix_terminals(layout,q,k,v,g,beta,initial,terminals,*,input_observer=None):
    if terminals.shape!=initial.shape or terminals.ndim!=4:
        raise ValueError("one private terminal/initial state per actual window required")
    if q.shape!=k.shape or q.ndim!=4 or q.shape[0]!=1 or v.shape[:2]!=q.shape[:2]:
        raise ValueError("actual raw grouped query/key/value inputs required")
    jobs=[]
    for rid,chain in zip(layout.request_ids,layout.chains):
        if not chain or chain[0][0]!="live":continue
        live=[j for kind,j in chain if kind=="live"]
        if not live:continue
        j=live[0];w=layout.windows[j];n=w.packed_end-w.packed_start
        if (w.request_id!=rid or not 1<=n or n!=w.source_end-w.source_start
                or not 0<=w.packed_start<w.packed_end<=q.shape[1]):
            raise ValueError("actual prefix source/packed coverage mismatch")
        jobs.append((rid,j,w,n))
    # Preserve all existing long-prefix and suffix terminals. Mutate private clone only.
    result=terminals.clone();routes=[]
    for rid,j,w,n in jobs:
        branch="official_chunk64"
        if n<=64:
            span=slice(w.packed_start,w.packed_end)
            observe=None if input_observer is None else lambda **values:input_observer(j,**values)
            _,state=recurrent_boundary(q[:,span],k[:,span],v[:,span],g[:,span],beta[:,span],
                                      initial[j:j+1],input_observer=observe)
            result[j].copy_(state[0].to(result.dtype))
            branch="independent_recurrent_le64"
        routes.append(dict(request_id=rid,job=j,window="prefix",source_start=w.source_start,
            source_end=w.source_end,packed_start=w.packed_start,packed_end=w.packed_end,
            rows=n,branch=branch,policy="canonical_recurrent_le64"))
    return result,routes

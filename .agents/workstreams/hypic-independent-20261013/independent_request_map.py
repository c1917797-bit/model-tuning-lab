"""Immutable pre-forward request identity snapshot for future runtime attachment."""
from dataclasses import dataclass
@dataclass(frozen=True)
class RequestSlice:
    request_id: str
    rank: int
    step: int
    computed_tokens: int
    scheduled_tokens: int
    row: int
    token_start: int
    token_end: int
def freeze_request_slices(req_ids,computed,scheduled,query_start,*,rank,step):
    ids=tuple(req_ids);counts=tuple(int(x) for x in computed);sched=tuple(int(x) for x in scheduled)
    starts=tuple(int(x) for x in query_start)
    n=len(ids)
    if len(set(ids))!=n or len(counts)!=n or len(sched)!=n or len(starts)!=n+1:
        raise ValueError("request identity/count coverage mismatch")
    if rank<0 or step<0 or starts[0]!=0 or any(x<0 for x in counts+sched):
        raise ValueError("invalid request snapshot")
    rows=[]
    for i,rid in enumerate(ids):
        if not isinstance(rid,str) or not rid or starts[i+1]-starts[i]!=sched[i]:
            raise ValueError("request/token boundary mismatch")
        rows.append(RequestSlice(rid,rank,step,counts[i],sched[i],i,starts[i],starts[i+1]))
    return tuple(rows)

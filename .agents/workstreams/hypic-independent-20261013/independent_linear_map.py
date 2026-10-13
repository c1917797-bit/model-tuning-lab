"""Non-spec pure-prefill linear-state association before hybrid reuse."""
from dataclasses import dataclass
@dataclass(frozen=True)
class LinearSlice:
    request_id: str
    rank: int
    step: int
    row: int
    state_slot: int
    token_start: int
    token_end: int
    has_initial_state: bool

def freeze_prefill_linear_slices(requests,query_start,state_indices,has_initial,
                                 *,state_capacity,speculative=False,num_decodes=0):
    requests=tuple(requests)
    starts=tuple(int(x) for x in query_start)
    indices=tuple(int(x) for x in state_indices)
    initial=tuple(bool(x) for x in has_initial)
    n=len(requests)
    if speculative or num_decodes:
        raise ValueError("mixed/decode/spec state association requires separate mapping")
    if len(starts)!=n+1 or len(indices)!=n or len(initial)!=n:
        raise ValueError("linear metadata coverage mismatch")
    if len(set(indices))!=n or any(x<0 or x>=state_capacity for x in indices):
        raise ValueError("invalid or aliased linear state slots")
    if not starts or starts[0]!=0:
        raise ValueError("invalid linear token start")
    output=[]
    for row,r in enumerate(requests):
        if r.row!=row or (r.token_start,r.token_end)!=(starts[row],starts[row+1]):
            raise ValueError("linear sequence order differs from request batch")
        if initial[row]!=(r.computed_tokens>0):
            raise ValueError("initial-state flag inconsistent with computed prefix")
        output.append(LinearSlice(r.request_id,r.rank,r.step,row,indices[row],
                                  r.token_start,r.token_end,initial[row]))
    return tuple(output)

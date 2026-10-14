"""Freeze source-observed non-spec decode-first hybrid state associations."""
from independent_linear_map import LinearSlice

def freeze_mixed_linear_slices(requests,query_start,state_indices,has_initial,
        *,state_capacity,num_decodes,num_prefills,num_decode_tokens,
        prefill_query_start=(),prefill_state_indices=(),prefill_has_initial=(),
        speculative=False):
    requests=tuple(requests);n=len(requests)
    if speculative: raise ValueError('speculative mixed state mapping unsupported')
    if any(type(x) is not int or x<0 for x in
           (state_capacity,num_decodes,num_prefills,num_decode_tokens)):
        raise ValueError('invalid mixed state counts')
    if not n or num_decodes+num_prefills!=n or num_decode_tokens!=num_decodes:
        raise ValueError('mixed sequence count drift')
    starts=tuple(int(x) for x in query_start)
    slots=tuple(int(x) for x in state_indices)
    initial=tuple(bool(x) for x in has_initial)
    if len(starts)!=n+1 or starts[0]!=0 or len(slots)!=n or len(initial)!=n:
        raise ValueError('mixed state coverage mismatch')
    if len(set(slots))!=n or any(x<0 or x>=state_capacity for x in slots):
        raise ValueError('mixed state alias/out-of-range')
    identity=(requests[0].rank,requests[0].step);seen=set();out=[]
    for row,r in enumerate(requests):
        if (not r.request_id or r.request_id in seen or r.row!=row or
            (r.rank,r.step)!=identity or
            (r.token_start,r.token_end)!=(starts[row],starts[row+1]) or
            r.scheduled_tokens!=starts[row+1]-starts[row] or
            (r.scheduled_tokens==1)!=(row<num_decodes) or
            r.scheduled_tokens<1 or initial[row]!=(r.computed_tokens>0)):
            raise ValueError('decode-first request/state identity drift')
        seen.add(r.request_id)
        out.append(LinearSlice(r.request_id,r.rank,r.step,row,slots[row],
                               r.token_start,r.token_end,initial[row]))
    if num_prefills:
        expected=tuple(x-num_decode_tokens for x in starts[num_decodes:])
        if (tuple(int(x) for x in prefill_query_start)!=expected or
            tuple(int(x) for x in prefill_state_indices)!=slots[num_decodes:] or
            tuple(bool(x) for x in prefill_has_initial)!=initial[num_decodes:]):
            raise ValueError('prefill-tail rebase/state association drift')
    elif prefill_query_start or prefill_state_indices or prefill_has_initial:
        raise ValueError('unexpected prefill-tail metadata')
    return tuple(out)

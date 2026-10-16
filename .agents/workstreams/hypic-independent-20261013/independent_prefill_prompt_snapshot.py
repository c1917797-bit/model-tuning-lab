"""Unactivated opt-in helper: no full-prompt copy for verified pure decode rows."""
from types import MappingProxyType
from independent_prompt_snapshot import freeze_prompt_tokens

def freeze_prefill_prompt_tokens(request_ids,states,*,computed_tokens=(),
                                 scheduled_tokens=(),enabled=False):
    if type(enabled)is not bool:raise ValueError("explicit phase snapshot switch required")
    ids=tuple(request_ids)
    if not enabled:return freeze_prompt_tokens(ids,states)
    computed=tuple(computed_tokens);scheduled=tuple(scheduled_tokens)
    if (len(ids)!=len(computed) or len(ids)!=len(scheduled)
            or len(set(ids))!=len(ids)
            or any(not isinstance(r,str) or not r.strip() for r in ids)):
        raise ValueError("complete unique current request identities/counts required")
    if (any(type(x)is not int or x<0 for x in computed)
            or any(type(x)is not int or x<=0 for x in scheduled)):
        raise ValueError("integer current computed/scheduled counts required")
    eligible=[];native=set()
    for rid,done,count in zip(ids,computed,scheduled):
        state=states[rid];tokens=state.prompt_token_ids
        if tokens is None or state.mm_features:
            native.add(rid);continue
        if not len(tokens):raise ValueError("invalid runtime prompt tokens")
        # A last prompt-token/chunked producer is NOT complete and must retain
        # the exact original prompt snapshot. No memoization/generation state.
        if count==1 and done>=len(tokens):native.add(rid)
        else:eligible.append(rid)
    frozen=freeze_prompt_tokens(eligible,states)
    return MappingProxyType({rid:None if rid in native else frozen[rid] for rid in ids})

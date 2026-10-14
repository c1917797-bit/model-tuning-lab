"""Pure heterogeneous-segment query plan; runtime leases are NOT supplied here."""
from dataclasses import replace
from independent_mixed_query_plan import plan_mixed_queries

def plan_catalog_batch(requests,prompts,catalog,ready_digests):
    requests=tuple(requests);ready_digests=frozenset(ready_digests)
    if not ready_digests.issubset(catalog.entries):
        raise ValueError("material readiness outside frozen catalog")
    selections={};lengths={};ready=[]
    for r in requests:
        tokens=prompts.get(r.request_id)
        if tokens is None:continue
        try:s=catalog.select_one(tokens)
        except ValueError:continue
        if s.start==0:s=replace(s,public=True)
        selections[r.request_id]=s;lengths[r.request_id]=s.end-s.start
        if s.tokens_sha256 in ready_digests:ready.append(r.request_id)
    return plan_mixed_queries(requests,selections,ready,
        seam_tokens=catalog.boundary,public_length=0,public_lengths=lengths)

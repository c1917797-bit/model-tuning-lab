"""Per-request mixed-batch row plan; not yet a runtime admission switch.

Native entries retain every scheduled row. Only complete, ready private PIC
entries use C2 pruning. Handlers must dispatch native entries without applying
public state/KV material. Cold/partial/decode entries are never counted as hot.
"""
from dataclasses import dataclass
from independent_c2_query_plan import plan_c2_queries, QueryWindow


@dataclass(frozen=True)
class NativeQueryPlan:
    request_id: str
    rank: int
    step: int
    token_start: int
    computed_tokens: int
    scheduled_tokens: int
    reason: str

    @property
    def retained_offsets(self): return tuple(range(self.scheduled_tokens))
    @property
    def skipped_tokens(self): return 0
    @property
    def body_start(self): return 0
    @property
    def body_end(self): return 0
    @property
    def windows(self):
        return (QueryWindow(0,self.scheduled_tokens,
                self.computed_tokens+self.scheduled_tokens,0,self.scheduled_tokens),)
    def packed_rows(self):
        return tuple(range(self.token_start,self.token_start+self.scheduled_tokens))
    def absolute_positions(self):
        return tuple(range(self.computed_tokens,self.computed_tokens+self.scheduled_tokens))


def plan_mixed_queries(requests,selections,ready_ids,*,seam_tokens,public_length,
                       public_lengths=None):
    """Selections are previously token-validated; readiness is all-layer pinned.

    This planner does not acquire pins or mutate caches. Caller must hold the
    readiness generation through execution. Invalid batch identity fails closed,
    while valid unsupported request shapes stay native within the same batch.
    """
    requests=tuple(requests);ready=frozenset(ready_ids);lengths=dict(public_lengths or {})
    if not requests: raise ValueError('empty mixed batch')
    rank=requests[0].rank;step=requests[0].step
    ids=set();cursor=0;plans=[]
    for req in requests:
        coords=(req.rank,req.step,req.row,req.token_start,req.token_end,
                req.computed_tokens,req.scheduled_tokens)
        if any(type(x) is not int or x<0 for x in coords):
            raise ValueError('invalid mixed coordinates')
        if (not req.request_id or req.request_id in ids or
            (req.rank,req.step)!=(rank,step) or req.row!=len(plans) or
            req.token_start!=cursor or req.scheduled_tokens<1 or
            req.token_end!=cursor+req.scheduled_tokens):
            raise ValueError('mixed request identity/order/coverage drift')
        ids.add(req.request_id);cursor=req.token_end
        selection=selections.get(req.request_id)
        reason='no-private-segment'
        if req.scheduled_tokens==1: reason='decode'
        elif selection is not None and selection.public: reason='public-producer'
        elif selection is not None and req.request_id not in ready: reason='cold-material'
        elif selection is not None:
            if req.computed_tokens>selection.start: reason='pdc-overlap'
            elif req.computed_tokens+req.scheduled_tokens<selection.end:
                reason='partial-body'
            else:
                plans.append(plan_c2_queries(req,selection,
                    seam_tokens=seam_tokens,public_length=lengths.get(req.request_id,public_length)))
                continue
        plans.append(NativeQueryPlan(req.request_id,req.rank,req.step,
                     req.token_start,req.computed_tokens,req.scheduled_tokens,reason))
    if not ready.issubset(ids) or not set(selections).issubset(ids) or not set(lengths).issubset(ids):
        raise ValueError('selection/readiness outside current batch')
    return tuple(plans)

"""Bind C2 retained queries to an observed cache map and explicit write lease.

Association is not ownership. Callers must separately supply scheduler-proven
writable slots; this module never derives a lease from a block table.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class BoundQueryWindow:
    compact_start: int
    compact_end: int
    logical_positions: tuple
    write_slots: tuple
    kv_end: int
    block_ids: tuple


@dataclass(frozen=True)
class C2CacheBinding:
    request_id: str
    rank: int
    step: int
    group: int
    body_slots: tuple
    windows: tuple


def bind_c2_cache(plan, cache, *, writable_slots):
    if (plan.request_id,plan.rank,plan.step)!=(cache.request_id,cache.rank,cache.step):
        raise ValueError("request/rank/step cache identity mismatch")
    if len(cache.slots)!=plan.scheduled_tokens:
        raise ValueError("scheduled slot coverage mismatch")
    if cache.block_size<=0 or cache.group<0:
        raise ValueError("invalid cache group/block size")
    lease=frozenset(writable_slots)
    if any(type(x) is not int or x<0 for x in lease):
        raise ValueError("invalid explicit write lease")
    # Validate the observed map anew; future callers may construct CacheSlice
    # without going through the diagnostic map freezer.
    scheduled=[]
    for i,slot in enumerate(cache.slots):
        pos=plan.computed_tokens+i
        block,offset=divmod(pos,cache.block_size)
        if block>=len(cache.block_ids) or cache.block_ids[block]<0:
            raise ValueError("logical KV coverage incomplete")
        expected=cache.block_ids[block]*cache.block_size+offset
        if type(slot) is not int or slot!=expected or slot not in lease:
            raise ValueError("invalid or unleased scheduled write slot")
        scheduled.append(slot)
    if len(set(scheduled))!=len(scheduled):
        raise ValueError("scheduled cache writes alias")
    # A shared PDC prefix must never alias any new request write, even when a
    # malformed lease lists it. Check entire allocated computed-prefix blocks.
    prefix_slots=set()
    for logical in range(plan.computed_tokens):
        b,o=divmod(logical,cache.block_size)
        prefix_slots.add(cache.block_ids[b]*cache.block_size+o)
    if prefix_slots.intersection(scheduled):
        raise ValueError("write aliases computed prefix")
    windows=[]
    for w in plan.windows:
        n=w.query_end-w.query_start
        if n<=0 or w.compact_end-w.compact_start!=n:
            raise ValueError("invalid query window coverage")
        if w.kv_end-n!=plan.computed_tokens+w.query_start:
            raise ValueError("causal query endpoint drift")
        count=(w.kv_end+cache.block_size-1)//cache.block_size
        ids=cache.block_ids[:count]
        if len(ids)!=count:
            raise ValueError("query window beyond allocated cache")
        windows.append(BoundQueryWindow(w.compact_start,w.compact_end,
            tuple(range(plan.computed_tokens+w.query_start,
                        plan.computed_tokens+w.query_end)),
            tuple(scheduled[w.query_start:w.query_end]),w.kv_end,ids))
    return C2CacheBinding(plan.request_id,plan.rank,plan.step,cache.group,
        tuple(scheduled[plan.body_start:plan.body_end]),tuple(windows))

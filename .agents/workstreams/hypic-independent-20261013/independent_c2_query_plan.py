"""Causal retained-query plan for model-layer PIC pruning.

Logical KV positions remain unchanged. A hole in query positions requires two
causal windows: prefix/seam and suffix. One compact causal call would align
the first window to the wrong KV endpoint and expose future tokens.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class QueryWindow:
    query_start: int
    query_end: int
    kv_end: int
    compact_start: int
    compact_end: int


@dataclass(frozen=True)
class C2QueryPlan:
    request_id: str
    rank: int
    step: int
    token_start: int
    computed_tokens: int
    scheduled_tokens: int
    body_start: int
    body_end: int
    retained_offsets: tuple
    windows: tuple

    @property
    def skipped_tokens(self):
        return self.body_end - self.body_start

    def absolute_positions(self):
        return tuple(self.computed_tokens + i for i in self.retained_offsets)

    def packed_rows(self):
        return tuple(self.token_start + i for i in self.retained_offsets)


def plan_c2_queries(request, selection, *, seam_tokens, public_length):
    """Pure plan; does not change scheduler, cache slots or runtime metadata.

    computed prefix/PDC is supported only when it ends before the selected
    segment. The complete selected body must be scheduled. A later chunk may
    carry its suffix normally; mid-body partial chunks need another contract.
    """
    ints=(request.rank, request.step, request.token_start,
          request.computed_tokens, request.scheduled_tokens,
          request.token_end, selection.start, selection.end,
          seam_tokens, public_length)
    if any(type(x) is not int for x in ints):
        raise ValueError("integer request/segment coordinates required")
    if not request.request_id or any(x < 0 for x in ints):
        raise ValueError("invalid request identity/coordinates")
    if request.token_end-request.token_start != request.scheduled_tokens:
        raise ValueError("packed request rows disagree with scheduled count")
    if selection.public or selection.end-selection.start != public_length:
        raise ValueError("private exact-length segment required")
    if not 0 < seam_tokens < public_length:
        raise ValueError("nonempty seam and reusable body required")
    computed=request.computed_tokens
    if computed > selection.start:
        raise ValueError("computed prefix overlaps selected segment")
    if computed+request.scheduled_tokens < selection.end:
        raise ValueError("scheduled chunk does not cover reusable body")
    body_start=selection.start+seam_tokens-computed
    body_end=selection.end-computed
    retained=tuple(range(body_start))+tuple(range(body_end,request.scheduled_tokens))
    windows=[QueryWindow(0,body_start,computed+body_start,0,body_start)]
    if body_end < request.scheduled_tokens:
        n=request.scheduled_tokens-body_end
        windows.append(QueryWindow(body_end,request.scheduled_tokens,
                                   computed+request.scheduled_tokens,
                                   body_start,body_start+n))
    # For each window a bottom-right causal mask now maps every query to its
    # original logical endpoint, despite the omitted public body queries.
    for w in windows:
        if w.kv_end-(w.query_end-w.query_start) != computed+w.query_start:
            raise ValueError("causal endpoint mismatch")
    return C2QueryPlan(request.request_id,request.rank,request.step,
                       request.token_start,computed,request.scheduled_tokens,
                       body_start,body_end,retained,tuple(windows))

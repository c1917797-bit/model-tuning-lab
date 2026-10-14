"""Deterministic full-denominator LongBench token/segment freezing."""
from independent_segment_selection import token_digest

def unique_public_segments(segments):
    entries={}
    for segment in segments:
        digest=token_digest(segment)
        entries.setdefault(digest,list(segment))
    return list(entries.values())

def context_segment(token_ids,offsets,context_start,context_end,*,max_tokens=16384):
    if len(token_ids)!=len(offsets) or not 0<=context_start<context_end:
        raise ValueError("exact token offsets/context span required")
    rows=[i for i,(a,b) in enumerate(offsets)
          if context_start<=a<b<=context_end]
    if not rows or rows!=list(range(rows[0],rows[-1]+1)):
        raise ValueError("contiguous context token span required")
    count=min(max_tokens,len(rows))
    count=count//16*16
    if count<=8:raise ValueError("context has no reusable segment body")
    start=rows[0];end=start+count
    segment=tuple(token_ids[start:end])
    return {"start":start,"end":end,"tokens_sha256":token_digest(segment)},segment

def quality_generation(enable_thinking=False):
    if type(enable_thinking) is not bool:raise ValueError("explicit thinking boolean required")
    return {"max_tokens":2048 if enable_thinking else 1024,"temperature":0,
            "seed":0,"ignore_eos":False,"enable_thinking":enable_thinking}

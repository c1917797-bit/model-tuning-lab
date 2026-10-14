"""Prospective PIC-aware chunk cap; not installed in runtime scheduler."""
def cap_pic_chunk(*,computed,proposed,prompt_tokens,segment_start,segment_end,ready,block_size=1):
    values=(computed,proposed,prompt_tokens,segment_start,segment_end)
    if any(type(x) is not int or x<0 for x in values) or not segment_start<segment_end<prompt_tokens or computed>prompt_tokens:
        raise ValueError("exact private prompt/PIC coordinates required")
    if type(ready) is not bool:raise ValueError("explicit complete-material readiness required")
    if type(block_size) is not int or block_size<1:raise ValueError("source-derived native block size required")
    n=min(proposed,prompt_tokens-computed)
    if not ready:return n
    if computed>segment_start:
        if computed<segment_end:
            raise ValueError("PIC body already partially computed; cannot retroactively skip")
        return n
    if computed+n>=segment_end+1:return n
    safe_end=(segment_start//block_size)*block_size
    return max(0,min(n,safe_end-computed))

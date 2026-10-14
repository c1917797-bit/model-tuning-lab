"""Gather model hidden/residual/position rows without changing logical KV positions."""
import torch


def compact_decoder_rows(hidden,residual,positions,plans):
    plans=tuple(plans)
    if not plans or hidden.ndim!=2:
        raise ValueError("nonempty decoder request batch required")
    if residual is not None and (residual.shape!=hidden.shape or residual.device!=hidden.device):
        raise ValueError("residual row/device mismatch")
    if positions.ndim not in (1,2) or positions.shape[-1]!=hidden.shape[0]:
        raise ValueError("positions do not cover original model rows")
    seen=set();rows=[];cursor=0;compact_spans=[]
    rank=plans[0].rank;step=plans[0].step
    for p in plans:
        if p.request_id in seen or (p.rank,p.step)!=(rank,step) or p.token_start!=cursor:
            raise ValueError("batch identity or packed request order mismatch")
        seen.add(p.request_id)
        start=len(rows);rows.extend(p.packed_rows());compact_spans.append((start,len(rows)))
        logical=positions[...,p.token_start:p.token_start+p.scheduled_tokens]
        # This target contract is text only. Identical MRoPE position planes
        # are accepted; multimodal planes require another relocation contract.
        expected=torch.arange(p.computed_tokens,p.computed_tokens+p.scheduled_tokens,
                              dtype=positions.dtype,device=positions.device)
        if not torch.equal(logical,expected.expand_as(logical)):
            raise ValueError("nontext or drifted logical positions")
        cursor+=p.scheduled_tokens
    if cursor!=hidden.shape[0] or len(set(rows))!=len(rows):
        raise ValueError("batch rows incomplete or aliased")
    index=torch.tensor(rows,dtype=torch.int64,device=hidden.device)
    pos_index=index.to(positions.device)
    return (hidden.index_select(0,index),
            None if residual is None else residual.index_select(0,index),
            positions.index_select(-1,pos_index),tuple(compact_spans))

"""Experimental C1 partitioned state/render schedule; never installs runtime hooks.

Reuses prepared per-window WY, computes each live window's state/output once.
This changes kernel batching, so CPU equivalence is not NPU acceptance.
"""
from dataclasses import dataclass
import torch
from independent_c1_shared_wy import SharedWY
from independent_c1_prefix_seeds import prefix_initial_seeds,suffix_seeds_from_terminals

@dataclass
class PartitionedRender:
    output: object
    terminal: object
    prefix_terminals: object
    seeds: object
    state_window_visits: int
    state_token_visits: int

def _select(shared,jobs,metadata_cache,*,total_value_heads,tp_size):
    starts=[0]; tokens=[]
    for j in jobs:
        lo,hi=shared.starts[j:j+2]
        tokens.extend(range(lo,hi));starts.append(starts[-1]+hi-lo)
    meta=metadata_cache.get(tuple(starts),total_value_heads=total_value_heads,
                            tp_size=tp_size,device=shared.k.device)
    if tuple(meta.cu_seqlens_host)!=tuple(starts) or meta.chunk_indices_chunk64_host is None:
        raise ValueError("partition metadata mismatch")
    index=torch.tensor(tokens,dtype=torch.long,device=shared.k.device)
    values=[]
    for name in ("q","k","w","u","g"):
        value=getattr(shared,name)
        if value.ndim not in (3,4) or value.shape[0]!=1 or value.shape[2]!=shared.starts[-1]:
            raise ValueError("complete head-major prepared tensor required")
        if value.device!=shared.k.device:
            raise ValueError("one private prepared device required")
        values.append(value.index_select(2,index).contiguous())
    return SharedWY(*values,tuple(starts),tuple(meta.chunk_indices_chunk64_host),
                    shared.state_op,shared.output_op,shared.scale),index

def render_partitioned(shared,layout,initial_states,cached_maps,*,metadata_cache,
                       total_value_heads,tp_size,align_prefix=None):
    """Private results only. Optional alignment runs before suffix composition.

    Caller remains responsible for finiteness, ownership, completion, and commit.
    No activation/config defaults or production source bindings are changed here.
    """
    initial=prefix_initial_seeds(layout,initial_states)
    n=len(layout.windows)
    if (len(shared.starts)!=n+1 or shared.starts[0]!=0
            or shared.starts[-1]!=layout.packed_tokens
            or any((w.packed_start,w.packed_end)!=tuple(shared.starts[j:j+2])
                   for j,w in enumerate(layout.windows))):
        raise ValueError("exact complete packed window geometry required")
    prefix=tuple(chain[0][1] for chain in layout.chains if chain)
    suffix=tuple(chain[2][1] for chain in layout.chains if len(chain)==3)
    if len(set(prefix+suffix))!=n or set(prefix+suffix)!=set(range(n)):
        raise ValueError("each live window exactly once required")
    terminal=initial.clone();prefix_terms=initial.clone()
    output=None;visits=0;token_visits=0
    def render(jobs,seeds):
        nonlocal output,visits,token_visits
        if not jobs:return
        selected,index=_select(shared,jobs,metadata_cache,
            total_value_heads=total_value_heads,tp_size=tp_size)
        ji=torch.tensor(jobs,dtype=torch.long,device=initial.device)
        y,h=selected.render(seeds.index_select(0,ji).clone())
        if y.shape!=(1,index.numel(),initial.shape[1],initial.shape[-1]) or h.shape!=(len(jobs),*initial.shape[1:]):
            raise ValueError("complete private partition result required")
        if output is None:
            output=y.new_empty((1,layout.packed_tokens,*y.shape[2:]))
        output.index_copy_(1,index,y)
        terminal.index_copy_(0,ji,h)
        visits+=len(jobs);token_visits+=index.numel()
    render(prefix,initial)
    pi=torch.tensor(prefix,dtype=torch.long,device=initial.device)
    prefix_terms.index_copy_(0,pi,terminal.index_select(0,pi))
    if align_prefix is not None:
        aligned=align_prefix(initial.clone(),prefix_terms.clone())
        if (aligned.shape!=prefix_terms.shape or aligned.dtype!=prefix_terms.dtype
                or aligned.device!=prefix_terms.device):
            raise ValueError("aligned prefix ABI mismatch")
        # Alignment can only change the actual prefix terminal, never suffix slots.
        if suffix:
            si=torch.tensor(suffix,dtype=torch.long,device=initial.device)
            if not torch.equal(aligned.index_select(0,si),prefix_terms.index_select(0,si)):
                raise ValueError("prefix alignment changed suffix slots")
        prefix_terms=aligned
    seeds=suffix_seeds_from_terminals(layout,initial,prefix_terms,cached_maps)
    render(suffix,seeds)
    if output is None or visits!=n or token_visits!=layout.packed_tokens:
        raise ValueError("complete single-visit private execution required")
    # Match existing canonical short-prefix terminal carry (output remains chunked).
    if align_prefix is not None:
        for chain in layout.chains:
            if not chain:continue
            live=[j for kind,j in chain if kind=="live"]
            j=live[0]
            if len(live)==1 and shared.starts[j+1]-shared.starts[j]<=64:
                terminal[j].copy_(prefix_terms[j])
    return PartitionedRender(output,terminal,prefix_terms,seeds,visits,token_visits)

"""Private one-token native decode packing; no runtime hook or device launch."""
from dataclasses import dataclass
import torch

@dataclass(frozen=True)
class DecodeRow:
    request_id: str
    projected_offset: int
    state_slot: int
    has_initial_state: bool

@dataclass(frozen=True)
class PackedDecode:
    rows: tuple
    projected: object
    b: object
    a: object
    conv: object
    # Official recurrent primitive expects VALUE-major private state.
    state: object
    conv_starts: object
    actual_seq_lengths: object

def pack_native_decode(rows, projected, b, a, conv_cache, state_cache):
    rows=tuple(rows)
    if not rows or any(not isinstance(r,DecodeRow) for r in rows):
        raise ValueError("nonempty explicit decode rows required")
    if any(not isinstance(r.request_id,str) or not r.request_id for r in rows):
        raise ValueError("request identity required")
    if len({r.request_id for r in rows})!=len(rows):
        raise ValueError("duplicate request")
    for field in ("projected_offset","state_slot"):
        values=[getattr(r,field) for r in rows]
        if any(type(v) is not int or v<0 for v in values) or len(set(values))!=len(values):
            raise ValueError("invalid or duplicate "+field)
    if any(type(r.has_initial_state) is not bool for r in rows):
        raise ValueError("initial-state flag must be bool")
    if projected.ndim!=2 or b.ndim!=2 or a.ndim!=2:
        raise ValueError("projected and gates must be row matrices")
    if b.shape[0]!=projected.shape[0] or a.shape[0]!=projected.shape[0]:
        raise ValueError("gate row coverage")
    if conv_cache.ndim!=3 or conv_cache.shape[1:]!=(3,projected.shape[1]):
        raise ValueError("conv cache layout")
    if state_cache.ndim!=4 or state_cache.shape[0]!=conv_cache.shape[0]:
        raise ValueError("value-major state cache layout")
    if any(x.device!=projected.device for x in (b,a,conv_cache,state_cache)):
        raise ValueError("mixed devices")
    if max(r.projected_offset for r in rows)>=projected.shape[0] or max(r.state_slot for r in rows)>=state_cache.shape[0]:
        raise ValueError("decode row outside input/cache")
    offsets=torch.tensor([r.projected_offset for r in rows],dtype=torch.long,device=projected.device)
    slots=torch.tensor([r.state_slot for r in rows],dtype=torch.long,device=projected.device)
    # index_select owns its storage; kernels may mutate these, NEVER real caches.
    conv=conv_cache.index_select(0,slots).to(projected.dtype).contiguous()
    state=state_cache.index_select(0,slots).contiguous()
    for i,r in enumerate(rows):
        if not r.has_initial_state:
            conv[i].zero_()
            state[i].zero_()
    n=len(rows)
    starts=torch.arange(n+1,dtype=torch.int32,device=projected.device)
    lengths=torch.ones(n+1,dtype=torch.int32,device=projected.device)
    lengths[0]=0
    return PackedDecode(rows,projected.index_select(0,offsets),
        b.index_select(0,offsets),a.index_select(0,offsets),
        conv,state,starts,lengths)

def unpack_native_decode(packed, output, value_major_state, conv, *, finite_check=None):
    if finite_check is not None and not callable(finite_check):raise ValueError('finite callback required')
    n=len(packed.rows)
    if output.ndim!=3 or output.shape[0]!=n:
        raise ValueError("decode output layout")
    if value_major_state.shape!=packed.state.shape or conv.shape!=packed.conv.shape:
        raise ValueError("private decode final layout")
    if output.shape[1]!=value_major_state.shape[1] or output.shape[2]!=value_major_state.shape[2]:
        raise ValueError("value dimensions mismatch")
    if any(x.device!=packed.projected.device for x in (output,value_major_state,conv)):
        raise ValueError("final devices mismatch")
    if finite_check is None:
        if not all(bool(torch.isfinite(x).all()) for x in (output,value_major_state,conv)):
            raise ValueError("nonfinite private decode")
    else:finite_check(output,value_major_state,conv)
    return {row.request_id:(output[i].clone(),
            value_major_state[i].transpose(-1,-2).contiguous().clone(),
            conv[i].clone()) for i,row in enumerate(packed.rows)}

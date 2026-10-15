"""Independent affine dependency engine for packed live C1 windows.

No old HYPIC imports, runtime hooks, real cache writes or device launch.
Official packed preparation/state/output callbacks are supplied separately.
"""
from dataclasses import dataclass
import torch
from independent_mixed_query_plan import NativeQueryPlan
from independent_linear_map import validate_linear_plan_associations


@dataclass(frozen=True)
class LiveWindow:
    request_row: int
    request_id: str
    source_start: int
    source_end: int
    packed_start: int
    packed_end: int


@dataclass(frozen=True)
class C1WaveLayout:
    request_ids: tuple
    state_slots: tuple
    has_initial: tuple
    rank: int
    step: int
    windows: tuple
    chains: tuple
    native_one_rows: tuple

    @property
    def packed_tokens(self):
        return self.windows[-1].packed_end if self.windows else 0


def build_wave_layout(plans,associations,*,separate_native_one=True):
    if type(separate_native_one) is not bool:
        raise ValueError("explicit native1 route required")
    plans=tuple(plans)
    if not 1<=len(plans)<=32:raise ValueError("bounded nonempty layer batch required")
    associations=validate_linear_plan_associations(plans,associations)
    if len({p.request_id for p in plans})!=len(plans) or len({(p.rank,p.step) for p in plans})!=1:
        raise ValueError("duplicate request or changed rank/step")
    jobs=[];chains=[];native=[];source_offset=0;packed_offset=0
    for row,(plan,assoc) in enumerate(zip(plans,associations)):
        if separate_native_one and isinstance(plan,NativeQueryPlan) and plan.scheduled_tokens==1:
            native.append(row);chains.append(())
            source_offset+=len(plan.retained_offsets);continue
        hot=not isinstance(plan,NativeQueryPlan)
        if not 1<=len(plan.windows)<=2 or (not hot and len(plan.windows)!=1):
            raise ValueError("live window geometry required")
        if hot and (not isinstance(plan.tokens_sha256,str) or not plan.tokens_sha256 or plan.skipped_tokens<=0):
            raise ValueError("exact cached body identity required")
        chain=[];local_cursor=0
        for index,window in enumerate(plan.windows):
            lo,hi=window.compact_start,window.compact_end
            if type(lo) is not int or type(hi) is not int or lo!=local_cursor or hi<=lo:
                raise ValueError("noncontiguous or empty retained window")
            length=hi-lo;number=len(jobs)
            jobs.append(LiveWindow(row,plan.request_id,source_offset+lo,source_offset+hi,
                                   packed_offset,packed_offset+length))
            chain.append(("live",number));packed_offset+=length;local_cursor=hi
            if hot and index==0:chain.append(("cached",plan.tokens_sha256))
        if local_cursor!=len(plan.retained_offsets):
            raise ValueError("live windows do not cover retained rows")
        chains.append(tuple(chain));source_offset+=local_cursor
    return C1WaveLayout(tuple(p.request_id for p in plans),
        tuple(a.state_slot for a in associations),tuple(a.has_initial_state for a in associations),
        plans[0].rank,plans[0].step,tuple(jobs),tuple(chains),tuple(native))


def propagate_window_seeds(layout,initial_states,live_maps,cached_maps):
    """Solve affine chains by dependency depth with batched matrix products.

    All live-window maps are already available. Their expensive independent
    derivation does not wait for the actual incoming prefix state.
    """
    n=len(layout.request_ids)
    if initial_states.ndim!=4 or initial_states.shape[0]!=n or initial_states.dtype not in (torch.float32,torch.float64):
        raise ValueError("private key-major [request,head,key,value] state required")
    if not layout.windows:raise ValueError("no packed prefill windows; use native1 route")
    live_maps=tuple(live_maps)
    needed={key for chain in layout.chains for kind,key in chain if kind=="cached"}
    if len(live_maps)!=len(layout.windows) or set(cached_maps)!=needed:
        raise ValueError("complete exact live/cached map coverage required")
    state_shape=tuple(initial_states.shape[1:])
    transition_shape=state_shape[:-1]+(state_shape[-2],)
    for item in (*live_maps,*cached_maps.values()):
        if tuple(item.transition.shape)!=transition_shape or tuple(item.zero_state.shape)!=state_shape:
            raise ValueError("affine layout mismatch")
        if any(t.device!=initial_states.device or t.dtype!=initial_states.dtype
               for t in (item.transition,item.zero_state)):
            raise ValueError("affine dtype/device mismatch")
    state=initial_states.clone()
    for row,present in enumerate(layout.has_initial):
        if not present:state[row].zero_()
    seeds=state.new_empty((len(layout.windows),*state_shape))
    for depth in range(max(map(len,layout.chains))):
        live_rows=[];live_jobs=[];cached_groups={}
        for row,chain in enumerate(layout.chains):
            if depth>=len(chain):continue
            kind,key=chain[depth]
            if kind=="live":live_rows.append(row);live_jobs.append(key)
            elif kind=="cached":cached_groups.setdefault(key,[]).append(row)
            else:raise ValueError("unknown affine chain action")
        if live_rows:
            indices=torch.tensor(live_rows,dtype=torch.long,device=state.device)
            job_indices=torch.tensor(live_jobs,dtype=torch.long,device=state.device)
            incoming=state.index_select(0,indices)
            seeds.index_copy_(0,job_indices,incoming)
            transitions=torch.stack([live_maps[j].transition for j in live_jobs])
            zeros=torch.stack([live_maps[j].zero_state for j in live_jobs])
            state.index_copy_(0,indices,torch.matmul(transitions,incoming)+zeros)
        for key,rows in cached_groups.items():
            indices=torch.tensor(rows,dtype=torch.long,device=state.device)
            material=cached_maps[key]
            # One immutable cached T/S broadcasts to every matching request.
            updated=torch.matmul(material.transition.unsqueeze(0),state.index_select(0,indices))
            state.index_copy_(0,indices,updated+material.zero_state.unsqueeze(0))
    finals={rid:state[row].clone() for row,rid in enumerate(layout.request_ids) if layout.chains[row]}
    return seeds,finals


def execute_packed_c1(layout,initial_states,cached_maps,*,prepare,derive,render):
    """One packed preparation, one all-window map stage, one output stage.

    prepare returns backend-private buffers (including independently seeded
    convolution windows). derive obtains all live T/S maps. render consumes
    solved incoming states for every live window. Caller must validate all
    terminal state/output/conv tensors before touching actual native slots.
    """
    if not all(callable(x) for x in (prepare,derive,render)):
        raise ValueError("explicit packed backend callbacks required")
    if not layout.windows:raise ValueError("delegate native1-only layer")
    prepared=prepare(layout)
    maps=derive(prepared)
    seeds,finals=propagate_window_seeds(layout,initial_states,maps,cached_maps)
    output=render(prepared,seeds)
    wanted=(layout.packed_tokens,initial_states.shape[1],initial_states.shape[-1])
    if tuple(output.shape)!=wanted or output.device!=initial_states.device:
        raise ValueError("complete packed output coverage required")
    pieces={}
    for window in layout.windows:
        pieces.setdefault(window.request_id,[]).append(output[window.packed_start:window.packed_end])
    return {rid:(torch.cat(parts,dim=0),finals[rid]) for rid,parts in pieces.items()}

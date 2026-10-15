"""Actual-prefix dependency seeds for one cached body and up to two live windows."""
import torch

def _chains(layout):
    found=set()
    for row,chain in enumerate(layout.chains):
        if not chain:continue
        if (len(chain)not in (1,2,3) or chain[0][0]!='live'
                or len(chain)>1 and chain[1][0]!='cached'
                or len(chain)==3 and chain[2][0]!='live'):
            raise ValueError("one cached body/prefix/suffix geometry required")
        for kind,job in chain:
            if kind!='live':continue
            if (type(job)is not int or not 0<=job<len(layout.windows) or job in found
                    or layout.windows[job].request_row!=row):
                raise ValueError("exact unique request/window ownership required")
            found.add(job)
    if found!=set(range(len(layout.windows))):raise ValueError("complete live window coverage required")

def prefix_initial_seeds(layout,initial_states):
    if (initial_states.ndim!=4 or initial_states.shape[0]!=len(layout.request_ids)
            or initial_states.dtype not in (torch.float32,torch.float64)
            or any(d<1 for d in initial_states.shape)
            or len(layout.has_initial)!=len(layout.request_ids)
            or any(type(x)is not bool for x in layout.has_initial)):
        raise ValueError("private nonempty key-major state and explicit initial flags required")
    _chains(layout)
    seeds=initial_states.new_zeros((len(layout.windows),*initial_states.shape[1:]))
    rows=[];jobs=[]
    for row,chain in enumerate(layout.chains):
        if chain and layout.has_initial[row]:rows.append(row);jobs.append(chain[0][1])
    if rows:
        ri=torch.tensor(rows,dtype=torch.long,device=seeds.device)
        ji=torch.tensor(jobs,dtype=torch.long,device=seeds.device)
        seeds.index_copy_(0,ji,initial_states.index_select(0,ri))
    return seeds

def suffix_seeds_from_terminals(layout,initial_seeds,prefix_terminals,cached_maps):
    _chains(layout)
    if (initial_seeds.ndim!=4 or initial_seeds.shape[0]!=len(layout.windows)
            or prefix_terminals.shape!=initial_seeds.shape
            or prefix_terminals.device!=initial_seeds.device
            or prefix_terminals.dtype!=initial_seeds.dtype):
        raise ValueError("complete same-device actual prefix terminal states required")
    needed={chain[1][1] for chain in layout.chains if len(chain)>1}
    if set(cached_maps)!=needed:raise ValueError("exact cached body maps required")
    state_shape=tuple(initial_seeds.shape[1:])
    for item in cached_maps.values():
        if (item.transition.shape!=(*state_shape[:-1],state_shape[-2])
                or item.zero_state.shape!=state_shape or any(
                t.device!=initial_seeds.device or t.dtype!=initial_seeds.dtype
                for t in (item.transition,item.zero_state))):
            raise ValueError("cached T/S state layout/dtype/device mismatch")
    seeds=initial_seeds.clone();groups={}
    for chain in layout.chains:
        if len(chain)==3:groups.setdefault(chain[1][1],[]).append((chain[0][1],chain[2][1]))
    for key,pairs in groups.items():
        pi=torch.tensor([p for p,s in pairs],dtype=torch.long,device=seeds.device)
        si=torch.tensor([s for p,s in pairs],dtype=torch.long,device=seeds.device)
        material=cached_maps[key]
        states=material.transition.unsqueeze(0)@prefix_terminals.index_select(0,pi)
        seeds.index_copy_(0,si,states+material.zero_state.unsqueeze(0))
    return seeds

"""Paper-derived tree gather around the unchanged native single-token conv.
No global hook is installed. Logical tails are oldest-to-newest raw projections.
"""
from dataclasses import dataclass

def need(v,message):
    if not v:raise ValueError(message)

@dataclass(frozen=True)
class Owner:
    request_id:str
    generation:int
    slot:int
    committed_length:int
    version:int

@dataclass
class Trial:
    tree:object
    owners:tuple
    initial:object
    inputs:object
    histories:object
    after:object
    arena_identity:tuple
    closed:bool=False

def identity(x):
    return (x.untyped_storage().data_ptr(),x.data_ptr(),x.storage_offset(),tuple(x.shape),tuple(x.stride()),str(x.dtype),str(x.device))

def check_owners(tree,owners):
    need(len(owners)==len(tree.request_ids),'all request owners')
    need(len({o.slot for o in owners})==len(owners),'distinct committed slots')
    for r,o in enumerate(owners):
        need(type(o)is Owner and o.request_id==tree.request_ids[r]and o.generation==tree.generations[r]and o.slot==tree.committed_slots[r]and o.committed_length==tree.committed_lengths[r]and type(o.version)is int and o.version>=0,'exact scheduler owner/generation/length/version')

def prepare(t,tree,owners,arena,inputs,*,width,node_budget=4096):
    tree.validate(node_budget=node_budget,max_depth=8,topk=4);check_owners(tree,owners)
    need(type(width)is int and width>=2,'explicit kernel width>=2')
    n=len(tree.tokens);b=len(owners)
    need(arena.ndim==3 and arena.shape[1]==width-1 and inputs.ndim==2 and inputs.shape==(n,arena.shape[2]),'logical [slot,width-1,channel] and [node,channel]')
    need(arena.stride(2)==1 and arena.stride(1)==arena.shape[2]and arena.stride(0)>=arena.shape[1]*arena.shape[2],'nonoverlapping SD slots; page padding allowed, DS/overlap refused')
    need(arena.dtype==inputs.dtype and arena.device==inputs.device,'actual matching projection/cache dtype/device')
    need(all(0<=o.slot<arena.shape[0]for o in owners),'actual committed slot range')
    slots=t.tensor([o.slot for o in owners],dtype=t.long,device=arena.device)
    initial=arena.index_select(0,slots).clone();raw=inputs.clone()
    source=t.cat((initial.reshape(b*(width-1),-1),raw),dim=0)
    before=[];after=[]
    # Metadata-only topology loop. All tensor node histories are one gather;
    # there is no per-node convolution or per-node device recurrence here.
    for r in range(b):
        for node in range(tree.offsets[r],tree.offsets[r+1]):
            prefix=list(range(r*(width-1),(r+1)*(width-1)))
            path=[b*(width-1)+j for j in tree.path(node)]
            before.append((prefix+path[:-1])[-(width-1):]);after.append((prefix+path)[-(width-1):])
    def gather(indices):
        index=t.tensor(indices,dtype=t.long,device=arena.device)
        return source.index_select(0,index.reshape(-1)).reshape(n,width-1,arena.shape[2]).contiguous()
    return Trial(tree,tuple(owners),initial,raw,gather(before),gather(after),identity(arena))

def native_one_call(t,trial,weight,bias,*,native_op,layout_receipt_ref,calibration_owner_ref,expected_source_ref,activation=False):
    """Component seam only; unknown native physical layout is a hard refusal.

    Receipt must be produced by a separately reviewed real native ABI/layout
    calibration, not by this source-preparation package or a software fixture.
    """
    import json,source118 as S
    S.source(expected_source_ref)
    r=json.loads(S.checked(layout_receipt_ref).read_bytes());owner=json.loads(S.checked(calibration_owner_ref).read_bytes())
    need(owner.get('source')==expected_source_ref and owner.get('primary')is None and owner.get('secondary')==[]and owner.get('stopped_retained')is True and owner.get('physical')==[4],'actual released same-source singleton calibration owner')
    stage=json.loads(S.checked(owner['result']).read_bytes())
    need(stage.get('source')==expected_source_ref and stage.get('NPU')is True and stage.get('primary')is None and stage.get('result')==layout_receipt_ref,'actual owner-stage-layout Ref chain')
    schema=getattr(native_op,'_schema',None)
    need(schema is not None and schema.name=='_C_ascend::npu_causal_conv1d_custom'and str(schema)==r.get('actual_schema'),'exact actual registered native callable, not a supplied Python backend')
    need(type(r)is dict and r.get('schema')=='bole.actual-native-conv-layout/v118'and r.get('source')==expected_source_ref and r.get('NPU')is True and r.get('pass_gate')is True,'actual source-bound native layout receipt required')
    need(r.get('layout')=='slot,width,channel'and r.get('cache_width')==trial.histories.shape[1]and r.get('kernel_width')==weight.shape[1]and weight.shape==(trial.inputs.shape[1],trial.histories.shape[1]+1),'proven native no-spec cache geometry')
    need(r.get('query_start_dtype')=='torch.int32'and r.get('indices_dtype')=='torch.int32'and r.get('run_mode')==1 and r.get('num_accepted_tokens')is None,'actual one-token native ABI calibration')
    need(not trial.closed,'live verification trial');n=trial.inputs.shape[0]
    scratch=trial.histories.clone();output=t.empty_like(trial.inputs)
    native_op(output,trial.inputs,weight.transpose(0,1),conv_state=scratch,bias_opt=bias,query_start_loc_opt=t.arange(n+1,dtype=t.int32,device=trial.inputs.device),cache_indices_opt=t.arange(n,dtype=t.int32,device=trial.inputs.device),initial_state_mode_opt=None,num_accepted_tokens_opt=None,activation_mode=1 if activation else 0,pad_slot_id=-1,run_mode=1)
    return output,scratch

def commit(t,trial,arena,current_owners,selected_nodes):
    """Only accepted root-to-node raw-input tail is committed, never siblings.
    Caller must retain the scheduler's exclusive commit window/stream order.
    """
    need(not trial.closed and identity(arena)==trial.arena_identity,'fresh trial and same explicit arena view')
    check_owners(trial.tree,current_owners);need(tuple(current_owners)==trial.owners,'slot recycled or request progressed during verification')
    current_index=t.tensor([o.slot for o in current_owners],dtype=t.long,device=arena.device)
    need(t.equal(arena.index_select(0,current_index).contiguous().view(t.uint8),trial.initial.contiguous().view(t.uint8)),'committed tail bytes changed since verification snapshot')
    need(len(selected_nodes)==len(current_owners),'one terminal or None per request')
    rows=[];slots=[];new=[]
    for r,(owner,node)in enumerate(zip(current_owners,selected_nodes)):
        path=trial.tree.commit_path(r,node,actual_generation=owner.generation,actual_slot=owner.slot)
        if path:rows.append(trial.after[node]);slots.append(owner.slot)
        new.append(Owner(owner.request_id,owner.generation,owner.slot,owner.committed_length+len(path),owner.version+(1 if path else 0)))
    # Validate every request before any mutation. Source buffers are cloned,
    # so source/destination overlap and within-batch slot permutations are safe.
    trial.closed=True
    if rows:
        values=t.stack(rows).clone();index=t.tensor(slots,dtype=t.long,device=arena.device)
        arena.index_copy_(0,index,values)
    return tuple(new)

def model_enable(*,enabled=False,tree112_ref=None,fia116_ref=None,mtp114_ref=None,treeconv118_qualification_ref=None):
    if not enabled:return dict(enabled=False,model_ready=False)
    need(all(v is not None for v in(tree112_ref,fia116_ref,mtp114_ref,treeconv118_qualification_ref)),'actual112/116/114 and independent treeconv qualification required')
    # This package provides no unified model installer or acceptance transaction.
    # Component booleans cannot authorize global monkeypatch installation.
    raise ValueError('component-only: unified GDN/conv/FA/KV/sampler commit and actual model qualification are not implemented by this module')

"""Real worker callback composition, diagnostic cache writeback then restoration.

No actor/controller/device is created. Existing owned HTTP/native-MTP runner
must load this callback inside its actual four workers. Missing predecessors
or source/runtime interfaces fail before any candidate model invocation.
"""
import inspect,os,traceback
from pathlib import Path
from types import SimpleNamespace
import model_entry as E
import worker_entry as W
import cache_registry as R
import prefill_tail as T
import mtp_entry as M
import tp_consensus as TP
import diagnostic_export as X
import core112,adapter,treeconv118,tree_metadata111,predecessor118t
import component_gate,registration118,acceptance
import native_logits


POLICY=dict(temperature=0,top_p=1,min_p=0,repetition_penalty=1,
 frequency_penalty=0,presence_penalty=0,grammar=False,custom_logits_processors=False)


def context_payload(ctx):
 # Explicitly omit private mutable ar_caches and ALL live model/arena objects.
 return dict(owner=ctx.owner,tokens=ctx.tokens,positions=ctx.positions,
             mode=ctx.mode,captures=ctx.captures,order=ctx.order,phase=ctx.phase,
             first_fault=ctx.first_fault,secondary_faults=ctx.secondary_faults)


def install(worker,torch,torch_npu,C,*,source_ref,component_refs,
            get_forward_context,get_attention_context,enter_context,
            native_get_tp_group,publish):
 m=C.obj(source_ref);refs=m['runtime_sources'];own_ref=C.ref(__file__)
 for fn in(enter_context,publish):E.code_source(C,fn,m['files'][Path(inspect.getsourcefile(fn)).name])
 group=native_get_tp_group()
 E.need(group.world_size==4 and 0<=group.rank_in_group<4,'real native TP4 worker group')
 inner=worker._bole_model_objects['inner'];outer=worker._bole_model_objects['outer']
 runner=worker.model_runner;drafter=runner.drafter
 E.need(drafter is not None and drafter.runner is runner and drafter.method=='mtp',
        'actual loaded native MTP drafter belongs to this worker runner')
 state=SimpleNamespace(prefill=None,completed=False,bridge=None)
 native_proposer=inspect.getmodule(drafter._propose.__func__)
 vocab_size=outer.config.vocab_size
 E.need(drafter.model.config.vocab_size==vocab_size,'actual target/MTP same vocabulary')
 def canonical_logits(value):
  return native_logits.canonical(torch,C,native_proposer,group,value,
             proposer_ref=refs['proposer'],vocab_size=vocab_size)
 restore_tail=T.install_capture(worker,torch,C,get_forward_context=get_forward_context,
                               gdn_ref=refs['gdn'],context_ref=refs['forward_context'])

 def after_prefill(**kw):
  if state.completed:return # Native retirement-barrier request is not a second tree trial.
  E.need(state.prefill is None and not state.completed,'one real request only, no silent reuse')
  ids=kw['input_ids'];positions=kw['positions']
  E.need(ids.dtype==torch.int64 and tuple(ids.shape)==(131,), 'exact real131token native prefill')
  axes=positions.ndim
  expected=list(range(131)) if axes==1 else [list(range(131))]*3
  E.need((axes==1 or tuple(positions.shape)==(3,131))and positions.cpu().tolist()==expected,
         'actual source text RoPE coordinates, no vision delta inference')
  restore_tail() # All48 actual native callbacks completed; restore real source.
  bindings,window=R.register(torch,C,worker,inner,request_id=kw['request_id'],
       request=kw['request'],metadata=kw['metadata'],forward_context=kw['forward_context'],
       get_attention_context=get_attention_context,refs=refs,length=131)
  root_hidden=kw['hidden'][0]if type(kw['hidden'])is tuple else kw['hidden']
  E.need(tuple(root_hidden.shape)==(131,5120),'actual native target final hidden')
  state.prefill=dict(window=window,bindings=bindings,context=kw['forward_context'],
    input_ids=ids.clone(),positions=positions.clone(),hidden=root_hidden.clone(),axes=axes)
  convabi=C.obj(m['actual118c']['capture'])['actual_device_abi_ref']
  prerequisite=component_gate.consume(C,component_refs,gdn_math=C.ref(core112.__file__),paged_math=C.ref(adapter.__file__))
  fia=prerequisite['components']['paged']['actual_fia_abi']
  state.bridge=E.Bridge(torch,C,inner,bindings,qwen_next_ref=refs['qwen_next'],gdn_ref=refs['gdn'],
    actual118c=m['actual118c'],conv_seam=__import__('native_seams'),treeconv=treeconv118,
    tree_metadata=tree_metadata111,core112=core112,paged=adapter,torch_npu=torch_npu,
    actual_fia_abi=fia,actual_conv_abi=convabi,calibration_reader=predecessor118t,
    arm_verified=True,component_refs=component_refs,component_gate=component_gate,
    native_registration=registration118,own_source_ref=source_ref,position_axes=1 if axes==1 else 3,
    prefill_window=window).install()
  owner=E.Owner(window['request_id'],1,window['slot'],131,0)
  state.prefill['native_anchors']=state.bridge._anchors(owner)

 def receive(*,proposer,record):
  if state.completed:return # Original native HTTP generation continues untouched.
  E.need(state.prefill is not None and proposer is drafter,'actual native prefill before genuine first MTP proposal')
  p=state.prefill;b=state.bridge;w=p['window'];request=w['request']
  owner=E.Owner(w['request_id'],1,w['slot'],131,0) # First observed request generation, NOT a scheduler-native counter.
  def current_owner():
   actual=[x for x in runner.input_batch.req_ids if x is not None]
   E.need(actual==[owner.request]and runner.requests[owner.request]is request and
          runner.input_batch.req_id_to_index[owner.request]==0,'same live actual request object/row')
   groups={binding['group']:binding['allocated_table']for binding in p['bindings']}
   for gid,expected in groups.items():
    block=runner.input_batch.block_table[gid];allocated=int(block.num_blocks_per_row[0])
    E.need(tuple(block.get_cpu_tensor()[0,:allocated].tolist())==expected,
           'same actual allocated physical pages/slots throughout diagnostic window')
   return owner
  E.need(torch.equal(record['target_token_ids'],p['input_ids'])and
         torch.equal(record['target_positions'],p['positions'])and
         torch.equal(record['target_hidden_states'],p['hidden']),
         'native MTP actually consumed this same target prefill IDs/positions/hidden')
  tokens=tuple(int(x)for x in torch.cat((record['root'].reshape(-1),record['children'].reshape(-1))).cpu().tolist())
  E.need(len(tokens)==3 and tokens[1]!=tokens[2],'one genuine root plus two distinct actual MTP vocabulary candidates')
  device=p['input_ids'].device;plan=None;raw={}
  try:
   native_anchors=p['native_anchors'];b._unchanged(native_anchors)
   agreement=TP.agree(torch,group,owner,tokens,None,device=device,phase=0)
   anchors=[]
   gdn_anchors=[]
   for binding in p['bindings']:
    if binding['kind']=='fa':
     ids=binding['table'][:2];index=torch.tensor(ids,dtype=torch.long,device=device)
     anchors.append(dict(layer=binding['index'],physical_pages=ids,
       key=binding['key'].index_select(0,index).clone(),value=binding['value'].index_select(0,index).clone()))
    else:
     observation=binding['layer'].linear_attn._bole_pure_prefill_observation
     gdn_anchors.append(dict(layer=binding['index'],initial_native_state=binding['state'][owner.slot].clone(),
       full_conv_slot=binding['tail'].selected_before.clone(),native_prefill_raw_last3=observation['raw_last3'].clone(),
       native_extra_before=observation['extra_before'].clone(),native_gdn_source=observation['native_gdn_source']))
   compute_logits=W.actual_logits_head(C,outer,inner,refs['qwen35'])
   with enter_context(p['context'],num_tokens=1,source_ref=source_ref):
    root_logits=canonical_logits(compute_logits(p['hidden'][-1:]))
    E.need(root_logits.dtype==torch.float32 and bool(torch.isfinite(root_logits).all())and
           int(root_logits.argmax(-1).item())==tokens[0],'genuine root agrees with original neutral greedy target sampling')
   with enter_context(p['context'],num_tokens=3,source_ref=source_ref):
    ids=torch.tensor(tokens,dtype=torch.int64,device=device)
    pos=torch.tensor([131,132,132],dtype=torch.int64,device=device)
    if p['axes']==2:pos=pos.unsqueeze(0).repeat(3,1)
    hidden,ctx=b.forward(owner,tokens,input_ids=ids,positions=pos,current_owner=current_owner)
    plan=b.greedy_proposal(hidden,ctx,compute_logits=compute_logits,acceptance=acceptance,
                           policy=POLICY,current_owner=current_owner,canonical_logits=canonical_logits)
   # Native AR has one real token per call; a separate correct Ascend context
   # must be entered, not the three-token context or stale draft metadata.
   with enter_context(p['context'],num_tokens=1,source_ref=source_ref):
    native=b.sequential_native_paths(owner,tokens,current_owner=current_owner)
    for path in native:
     for step in path['steps']:
      h=step['hidden'][0]if type(step['hidden'])is tuple else step['hidden']
      step['logits']=canonical_logits(compute_logits(h))
   transaction=TP.temporary_writeback(torch,b,plan,group=group,tokens=tokens,current_owner=current_owner)
   b._unchanged(native_anchors) # Includes complete selected wide conv slots and real FA pages.
   final_gdn=[];final_fa=[]
   for binding in p['bindings']:
    if binding['kind']=='gdn':
     final_gdn.append(dict(layer=binding['index'],full_conv_slot=binding['conv_arena'][owner.slot:owner.slot+1].clone(),
        native_state=binding['state'][owner.slot].clone()))
    else:
     index=torch.tensor(binding['table'][:2],dtype=torch.long,device=device)
     final_fa.append(dict(layer=binding['index'],key=binding['key'].index_select(0,index).clone(),value=binding['value'].index_select(0,index).clone()))
   raw=dict(schema='bole.actual-three-node-model-capture/v1',source=source_ref,
      rank=group.rank_in_group,request=owner,actual_native_prefill_ids=p['input_ids'],
      actual_native_prefill_positions=p['positions'],actual_native_prefill_hidden=p['hidden'],actual_root_logits=root_logits,
      actual_native_initial_GDN=gdn_anchors,
      actual_native_final_GDN=final_gdn,actual_native_final_FA=final_fa,
      native_logits_policy=dict(reduce_sample=native_proposer.get_ascend_config().enable_reduce_sample,
          lmhead_tp=False,vocab_size=vocab_size,proposer_source=refs['proposer']),
      genuine_MTP={k:v for k,v in record.items()if k not in('common_attn_metadata','scheduler_output')},
      initial_FA_pages=anchors,tree_hidden=hidden,tree_context=context_payload(ctx),
      staged=X.export_staged(torch,plan,cap_bytes=2**30)['payload'],transaction=transaction,
      native=[dict(child=path['child'],steps=[dict(node=s['node'],hidden=s['hidden'],logits=s['logits'],context=context_payload(s['context']))for s in path['steps']])for path in native],
      initial_agreement=agreement,scheduler_committed=False,model_ready=False)
   payload=X.export(torch,raw,cap_bytes=2**30)
   publish(source_ref=source_ref,rank=group.rank_in_group,payload=payload,primary=None)
   state.completed=True;b.restore()
  except BaseException as error:
   # Preserve the ORIGINAL traceback plus available bounded operands. No failed
   # component or partial cache restoration is converted into native fallback.
   failed=dict(schema='bole.actual-three-node-model-first-fault/v1',source=source_ref,
       rank=group.rank_in_group,primary=repr(error),traceback=traceback.format_exc(),
       tree=None if not hasattr(b,'last_context')else context_payload(b.last_context),
       native=None if not hasattr(b,'last_native_context')else context_payload(b.last_native_context),
       scheduler_committed=False,model_ready=False)
   publish(source_ref=source_ref,rank=group.rank_in_group,payload=X.export(torch,failed,cap_bytes=2**30),primary=repr(error))
   raise

 W.install_after_native_prefill(worker,C,qwen_next_ref=refs['qwen_next'],
     get_forward_context=get_forward_context,context_source_ref=refs['forward_context'],
     callback=after_prefill,callback_source_ref=own_ref)
 M.install(drafter,torch,C,proposer_ref=refs['proposer'],mtp_ref=refs['mtp'],
           receive=receive,receiver_ref=own_ref,canonical_logits=canonical_logits)
 return state

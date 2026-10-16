"""Source-pinned eager/no-PDC CPU mirror hooks. OFF by default.

No model algorithm installation and no permission to run a performance test.
The caller must independently qualify and source-bind its new runtime consumer.
"""
import contextvars,functools,hashlib,inspect,os
from pathlib import Path
from .cpu_metadata import check_cpu,tensor_identity,require_same_native_view,need

PINS={
 'vllm_ascend.worker.model_runner_v1':'94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968',
 'vllm_ascend.ops.gdn_attn_builder':'42cc0284b57193112b8a8ad19704aa3401f02294f0c36333c307d748f462fe16',
 'vllm_ascend.worker.npu_input_batch':'a4dc08a9918f07797622f8d0915785e8c7b6899e0d10d92603e1dddec218acc3',
 'vllm_ascend.worker.block_table':'8f77809c12af3bd9d56974edbbe5c792995f2620aadfe62411806f2e68d2ef0a',
 'vllm.v1.attention.backends.utils':'f4f2f106ad84aa77cdf0b09d6948878f4e74c56568309312ec47bd190cc710cd',
 'vllm.v1.attention.backend':'01e2068470081d2dcf3b676d454ed73d4728798fced35e76ebfa8f0fe4e5dad7',
 'vllm_ascend.worker.utils':'e75651c8742650f1bac7dddb5f39b9a636f289b4785864c984837ec12dcdae75'}
_PREP=contextvars.ContextVar('deltalog018_prepare',default=None)
_BUILD=contextvars.ContextVar('deltalog018_build',default=None)
_DUMMY=contextvars.ContextVar('deltalog018_dummy',default=False)

def cpu_values(t):
 need(t.device.type=='cpu','already-native CPU source only')
 return tuple(t.reshape(-1).tolist())

def guard(r):
 need(not r.use_async_scheduling and not r.use_async_spec_decode and r.speculative_config is None,'synchronous nonspec scheduler only')
 need(r.model_config.enforce_eager and r.pcp_size==1 and not r.use_cp,'eager PCP1, no transformed/padded PCP table')
 need(r.cache_config.mamba_cache_mode=='none'and not r.cache_config.enable_prefix_caching,'native none; no prefix-copy qualification')

def request_keys(r,n):
 ids=tuple(r.input_batch.req_ids)
 need(len(ids)==n and all(type(x)is str for x in ids)and len(set(ids))==n,'exact actual persistent request rows')
 need(all(r.input_batch.req_id_to_index[x]==i for i,x in enumerate(ids)),'post-reorder request index map')
 return tuple((x,r.requests[x])for x in ids) # retain strong request-generation objects

def lifecycle(previous,keys,slots,nd):
 need(len(keys)==len(slots),'request/slot count')
 out=dict(previous)
 for i,(key,slot)in enumerate(zip(keys,slots)):
  # New generation or moved slot may not silently consume stale deferred logs.
  if i<nd:need(same_key(out.get(slot),key),'decode requires same admitted request generation and temporal slot')
  else:out[slot]=key
 return out

def same_key(a,b):
 return a is not None and a[0]==b[0]and a[1]is b[1]

def same_keys(a,b):
 return len(a)==len(b)and all(same_key(x,y)for x,y in zip(a,b))

def new_state():
 return dict(epoch=0,owners={},current=None,layers={},query_serial=0)

def invalidate(state,reason):
 if state is not None:
  state['epoch']+=1;state['current']=None;state['invalidated_by']=reason

def invalidate_for_dummy(r):
 state=getattr(r,'_deltalog018_state',None)
 invalidate(state,'actual_dummy_run_before_buffer_writes')
 # Even a fresh future prepare cannot undo a dummy's mutation of live deferred
 # state. Native-only warmup is startup-only, never a live-session fallback.
 need(state is None or not any(state['owners'].values()),'native dummy after live request ownership forbidden')

def arena_identity(base):
 return (id(base),tensor_identity(base),base.untyped_storage().data_ptr())

def register_layers(r,rows,actual_target):
 """Provider passes actual (layer,KVgroup) objects, not fabricated layer IDs."""
 guard(r);state=getattr(r,'_deltalog018_state',None)
 if state is None:state=new_state();r._deltalog018_state=state
 need(state['current']is None and not state['layers'],'register once before real scheduler work')
 expected={name for gid,table in enumerate(r.input_batch.block_table.block_tables)if table.is_mamba_group for name in r.kv_cache_config.kv_cache_groups[gid].layer_names}
 need(len(expected)==48 and len(rows)==48,'actual config has48 GDN layer names')
 found={};arena_ranges=[]
 for layer,gid in rows:
  need(isinstance(layer,actual_target)and layer.prefix in expected and layer.prefix not in found,'actual target object and unique registered prefix')
  need(layer.prefix in r.kv_cache_config.kv_cache_groups[gid].layer_names and r.input_batch.block_table[gid].is_mamba_group,'native layer-to-KVgroup binding')
  base=layer.kv_cache[1]
  need(base.device.type=='npu'and str(base.dtype)=='torch.float32'and list(base.shape[1:])==[12,128,128]and list(base.stride())==[196608,16384,128,1]and base.is_contiguous(),'reviewed actual native arena')
  start,end=base.data_ptr(),base.data_ptr()+base.numel()*base.element_size()
  need(all(end<=lo or start>=hi for lo,hi in arena_ranges),'registered actual layer arenas must not overlap')
  arena_ranges.append((start,end))
  found[layer.prefix]=dict(layer=layer,group=gid,base=base,identity=arena_identity(base))
 need(set(found)==expected,'all actual48 config names registered; no inferred fake mapping')
 state['layers']=found
 return dict(registered_prefixes=tuple(sorted(found)),NPU_qualified=False)

def finish_step(r):
 state=r._deltalog018_state;step=state['current'];need(step is not None,'real step remains valid')
 for prefix,row in state['layers'].items():
  gid=row['group'];need(gid in step['metadata'],'all registered groups built')
  meta=step['metadata'][gid];seen=meta._deltalog018_cpu_receipt['seen']
  need((prefix,'core')in seen,'actual layer core receipt consumed once')
  if meta.num_decodes:need((prefix,'decode')in seen,'actual layer decode receipt consumed once')
 return True

def read_receipt(r,layer,meta,base,ids,sequence,forward_context,phase):
 """Mandatory real reader identities; no D2H and no pointer-as-content claim."""
 need(not _DUMMY.get()and phase in ('core','decode'),'real execution phase only')
 v=getattr(meta,'_deltalog018_cpu_receipt',None)
 need(v is not None,'no genuine source-bound scheduler/builder receipt; refuse dummy or unknown path')
 state=r._deltalog018_state
 need(v['state']is state and v['epoch']==state['epoch']and state['current']is v['step'],'stale or superseded metadata epoch')
 need(meta is v['metadata']and forward_context.attn_metadata[layer.prefix]is meta and forward_context.no_compile_layers[layer.prefix]is layer,'actual current forward metadata and layer')
 reg=state['layers'].get(layer.prefix)
 need(reg is not None and reg['layer']is layer and reg['group']==v['group'],'registered actual layer/KVgroup')
 need(base is layer.kv_cache[1]and base is reg['base']and arena_identity(base)==reg['identity'],'actual per-layer arena object/storage/view')
 need(base.shape[0]>max(v['cpu'].decode+v['cpu'].prefill,default=-1),'actual arena slot bounds')
 need(tensor_identity(meta.non_spec_state_indices_tensor)==v['index_identity'],'device index object/view drift')
 require_same_native_view(ids,meta.non_spec_state_indices_tensor,len(v['cpu'].decode))
 if meta.num_decodes:
  need(meta.non_spec_decode_metadata is not None and sequence is meta.non_spec_decode_metadata.actual_seq_lengths,'same native individual-length tensor')
 else:
  need(phase=='core'and sequence is None,'pure-prefill core has no decode sequence input')
 key=(layer.prefix,phase);need(key not in v['seen'],'duplicate layer/phase read')
 if phase=='decode':need(meta.num_decodes>0 and(layer.prefix,'core')in v['seen'],'decode follows same real layer core')
 v['seen'].add(key)
 return v['cpu']

def install():
 if os.environ.get('QWEN36_DELTALOG_CPU_MIRROR018_REV2_ENABLE')!='1':return {'installed':False,'default_OFF':True}
 import importlib
 mods={n:importlib.import_module(n)for n in PINS}
 for n,m in mods.items():
  p=Path(inspect.getsourcefile(m)).resolve();need(hashlib.sha256(p.read_bytes()).hexdigest()==PINS[n],'actual source pin '+n)
 R=mods['vllm_ascend.worker.model_runner_v1'].NPUModelRunner
 BT=mods['vllm_ascend.worker.block_table'].BlockTable
 G=mods['vllm_ascend.ops.gdn_attn_builder'].AscendGDNAttentionMetadataBuilder
 need(not getattr(R,'_deltalog018_installed',False),'no duplicate hook installation')
 original_prepare,original_meta,original_commit,original_build,original_dummy=R._prepare_inputs,R._build_attention_metadata,BT.commit_block_table,G.build,R._dummy_run
 U=mods['vllm_ascend.worker.utils'];original_snapshot=U.copy_snapshot_to_gpu
 need(mods['vllm_ascend.worker.model_runner_v1'].copy_snapshot_to_gpu is original_snapshot,'actual runner copy helper import binding')

 @functools.wraps(original_commit)
 def commit(table,n):
  step=_PREP.get()
  if step is None:return original_commit(table,n) # actual dummy path is NOT a real request receipt
  r=step['runner'];need(n==step['n'],'commit row count is real scheduler count')
  groups=r.input_batch.block_table.block_tables
  found=[i for i,x in enumerate(groups)if x is table];need(len(found)==1,'real runner-owned KV table')
  gid=found[0]
  if not table.is_mamba_group:return original_commit(table,n)
  need(table.pcp_world_size==table.dcp_world_size==1 and not table.use_hybrid_blocks,'untransformed native Mamba rows')
  cpu=table.get_cpu_tensor();need(cpu.device.type=='cpu'and table.max_num_blocks_per_req==1 and cpu.shape[1]==1,'none nonspec one block per request')
  values=cpu_values(cpu[:n,0]);need(all(int(x)==x for x in values),'native int slot IDs');values=tuple(int(x)for x in values)
  need(gid not in step['tables'],'one actual commit per group in real prepare')
  result=original_commit(table,n)
  # Actual original commit clones/pins the same CPU source before asynchronous
  # H2D. CPU buffer changes during the call invalidate this mirror.
  need(values==tuple(int(x)for x in cpu_values(cpu[:n,0])),'CPU table changed during source snapshot/copy')
  step['tables'][gid]=dict(table=table,values=values,device=tensor_identity(table.get_device_tensor()[:n]))
  return result

 @functools.wraps(original_prepare)
 def prepare(r,*a,**kw):
  guard(r);need(_PREP.get()is None,'no nested/reentrant scheduler prepare')
  n=r.input_batch.num_reqs;need(1<=n<=16,'reviewed actual request count');keys=request_keys(r,n)
  state=getattr(r,'_deltalog018_state',None)
  if state is None:state=new_state();r._deltalog018_state=state
  need(len(state['layers'])==48,'provider must register actual48 layer/arenas first')
  if state['current']is not None:finish_step(r)
  state['epoch']+=1;state['current']=None
  step=dict(runner=r,n=n,keys=keys,tables={},epoch=state['epoch'],state=state,query=None,metadata={})
  tok=_PREP.set(step)
  try:result=original_prepare(r,*a,**kw)
  finally:_PREP.reset(tok)
  need(same_keys(request_keys(r,n),keys),'request generation/reorder changed during prepare')
  need(bool(step['tables'])and step['query']is not None,'actual GDN table and query snapshot committed')
  computed=cpu_values(r.input_batch.num_computed_tokens_cpu_tensor[:n]);seq=cpu_values(r.optimistic_seq_lens_cpu[:n]);q=step['query']['values']
  need(tuple(c+(q[i+1]-q[i])for i,c in enumerate(computed))==seq,'actual sync CPU seq_lens=computed+query')
  step['computed']=computed
  state['current']=step
  return result

 @functools.wraps(original_meta)
 def metadata(r,*a,**kw):
  guard(r)
  # Dummy warmup has no genuine current scheduler receipt; leave metadata
  # unannotated. The runtime reader MUST refuse it (or separately qualified
  # native-before-any-live-state warmup), never fabricate request identities.
  state=getattr(r,'_deltalog018_state',None);step=None if state is None or _DUMMY.get() else state['current']
  need(not kw.get('for_cudagraph_capture',False)and not kw.get('use_spec_decode',False)and kw.get('ubatch_slices')is None,'no graph/spec/ubatch')
  token=_BUILD.set(step)
  try:return original_meta(r,*a,**kw)
  finally:_BUILD.reset(token)

 @functools.wraps(original_build)
 def build(builder,*a,**kw):
  step=_BUILD.get()
  if step is None:return original_build(builder,*a,**kw)
  r=step['runner'];guard(r);need(same_keys(request_keys(r,step['n']),step['keys']),'actual request generation still current')
  common=kw.get('common_attn_metadata',a[1]if len(a)>1 else None);need(common is not None,'actual Common metadata argument')
  need(common.num_reqs==step['n']and not builder.use_full_cuda_graph and not builder.use_spec_decode,'no padded graph/spec shape')
  need(tensor_identity(common.query_start_loc_cpu)==tensor_identity(r.gdn_query_start_loc.cpu[:step['n']+1])and tensor_identity(common.query_start_loc)==tensor_identity(r.gdn_query_start_loc.gpu[:step['n']+1]),'source-native GDN CPU/device query buffer views')
  need(tensor_identity(common.query_start_loc_cpu)==step['query']['CPU']and tensor_identity(common.query_start_loc)==step['query']['device'],'same CPU/device buffers as original helper snapshot window')
  matches=[(gid,t)for gid,t in step['tables'].items()if tensor_identity(common.block_table_tensor)==t['device']]
  need(len(matches)==1,'actual Common device table belongs to one committed GDN group')
  gid,t=matches[0];need(tuple(int(x)for x in cpu_values(t['table'].get_cpu_tensor()[:step['n'],0]))==t['values'],'CPU rows changed since commit')
  need(gid not in step['metadata'],'reviewed one GDN metadata object per KVgroup; no silent overwrite')
  q=cpu_values(common.query_start_loc_cpu);need(q==step['query']['values'],'same actual query snapshot values')
  need(q[0]==0 and len(q)==step['n']+1 and all(y>x for x,y in zip(q,q[1:])),'real nonempty CPU query rows')
  meta=original_build(builder,*a,**kw)
  need(cpu_values(common.query_start_loc_cpu)==q,'CPU query boundaries changed during builder')
  nd,np=meta.num_decodes,meta.num_prefills;need(nd+np==step['n']and meta.num_decode_tokens==nd and meta.spec_sequence_masks is None,'exact native nonspec partition')
  need(all(q[i+1]-q[i]==1 for i in range(nd)),'all true decode lengths one')
  computed=cpu_values(r.input_batch.num_computed_tokens_cpu_tensor[:step['n']]);need(computed==step['computed'],'CPU computed-state lineage unchanged')
  c=check_cpu(list(t['values'][:nd]),list(t['values'][nd:]),[0]+[1]*nd,[x>0 for x in computed[nd:]],max(t['values'],default=-1)+1)
  owners=lifecycle(step['state']['owners'].get(gid,{}),step['keys'],t['values'],nd);step['state']['owners'][gid]=owners
  receipt=dict(cpu=c,metadata=meta,state=step['state'],step=step,epoch=step['epoch'],group=gid,index_identity=tensor_identity(meta.non_spec_state_indices_tensor),seen=set())
  meta._deltalog018_cpu_receipt=receipt;step['metadata'][gid]=meta
  return meta

 @functools.wraps(original_dummy)
 def dummy(r,*a,**kw):
  invalidate_for_dummy(r)
  token=_DUMMY.set(True)
  try:return original_dummy(r,*a,**kw)
  finally:_DUMMY.reset(token)

 @functools.wraps(original_snapshot)
 def snapshot(buffer):
  step=_PREP.get()
  if step is None:return original_snapshot(buffer)
  r=step['runner']
  if buffer is not r.gdn_query_start_loc:return original_snapshot(buffer)
  need(step['query']is None,'one native GDN query snapshot per real prepare')
  values=cpu_values(buffer.cpu[:step['n']+1]);result=original_snapshot(buffer)
  need(values==cpu_values(buffer.cpu[:step['n']+1]),'CPU query changed during native clone/copy')
  step['query']=dict(values=values,CPU=tensor_identity(buffer.cpu[:step['n']+1]),device=tensor_identity(buffer.gpu[:step['n']+1]))
  return result

 mods['vllm_ascend.worker.model_runner_v1'].copy_snapshot_to_gpu=snapshot
 BT.commit_block_table=commit;R._prepare_inputs=prepare;R._build_attention_metadata=metadata;R._dummy_run=dummy;G.build=build;R._deltalog018_installed=True
 return dict(installed=True,source_pins=PINS,performance_qualified=False,NPU_qualified=False)

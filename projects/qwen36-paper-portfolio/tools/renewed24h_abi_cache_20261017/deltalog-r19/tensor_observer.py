"""Selected three real GDN layers; diagnostic D2H, never a timing path."""
import contextvars,functools,hashlib,json,os
from pathlib import Path
FIELDS=('k_log','u_log','lambda_log','decay','length')
CURRENT=contextvars.ContextVar('dl026_actual_core',default=None)
OP_CAPTURE=contextvars.ContextVar('dl045_selected_actual_op',default=None)

def dispatch_for(production):
 def dispatch(*args):
  capture=OP_CAPTURE.get()
  return production(*args)if capture is None else capture(*args)
 return dispatch
def install(R,W,M,sr,m):
 if os.environ.get('QWEN36_DELTALOG_TENSOR026_ENABLE')!='1':raise ValueError('tensor diagnostic explicitly ON only')
 import torch
 import vllm_ascend.ops.gdn as G
 H=R.H;L=R.L;original_route=R._route;original_core=H.execute_mixed_core;original_chunk=G.chunk_gated_delta_rule
 selected=None;selection=None;count=0;native_states={};store=None
 root=Path(os.environ['QWEN36_DELTALOG_SERVICE023_AUDIT'])/'tensor026'/('worker-%d'%os.getpid())
 def write(name,value):
  raw=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode()
  with(root/name).open('xb')as f:f.write(raw)
 def select(layer):
  nonlocal selected,selection,store
  r=W.runner_for(layer);state=r._deltalog018_state
  if selected is None:
   root.mkdir(parents=True,exist_ok=False)
   import raw_codec
   store=raw_codec.Store(torch,root,m['tensor_budget']['per_worker_bytes'])
   rows=sorted((v['layer'].layer_idx,p)for p,v in state['layers'].items())
   if len(rows)!=48 or len({i for i,p in rows})!=48:raise ValueError('actual48 numeric layer identities')
   selected={rows[i][1]for i in(0,24,47)}
   from vllm.distributed import parallel_state as ps
   selection=dict(schema='deltalog.actual-selected-GDN/v026',source=sr,plugin_source=R._SOURCE or m['plugin_source'],pid=os.getpid(),rank=ps.get_tensor_model_parallel_rank(),all48=rows,selected=sorted(selected),diagnostic_D2H=True,NPU=True,model_qualified=False)
   write('SELECTION.json',selection)
  return r if layer.prefix in selected else None
 def context(layer,r):
  step=r._deltalog018_state['current'];meta=G.get_forward_context().attn_metadata[layer.prefix];receipt=meta._deltalog018_cpu_receipt
  if (layer.prefix,'core')not in receipt['seen']or len(step['keys'])!=1:raise ValueError('actual B1 core receipt before capture')
  return dict(source=sr,prefix=layer.prefix,layer_idx=layer.layer_idx,pid=os.getpid(),rank=selection['rank'],epoch=step['epoch'],engine_request_id=step['keys'][0][0],meta=meta,runner=r,layer=layer,chunks=[])
 def cpu(t):
  if not isinstance(t,torch.Tensor):return t
  return t.detach().cpu().clone()
 def snap(layer,ids):
  if layer.kv_cache[1].device.type!='npu' or ids.device.type!='npu':raise ValueError('actual NPU tensors required')
  aux=H._bind(torch,L,layer);index=ids.flatten().long()
  return dict(base=cpu(layer.kv_cache[1].index_select(0,index)),**{n:cpu(aux[n].index_select(0,index))for n in FIELDS})
 def save(kind,c,data):
  nonlocal count
  p=root/('row-%06d.pt'%count)
  raw=store.write(p,data)
  row={k:c[k]for k in('source','prefix','layer_idx','pid','rank','epoch','engine_request_id')};row.update(kind=kind,raw=raw)
  with(root/'ROWS.jsonl').open('a')as f:f.write(json.dumps(row,sort_keys=True)+'\n')
  count+=1
 def route(T,layer,**kw):
  r=select(layer)
  if r is None:return original_route(T,layer,**kw)
  c=CURRENT.get()
  if c is None or c['layer']is not layer:raise ValueError('actual same core route context')
  ids=kw['ssm_state_indices'];actual_ids=cpu(ids).flatten().tolist()
  expected=list(c['meta']._deltalog018_cpu_receipt['cpu'].decode)
  if actual_ids!=expected or len(actual_ids)!=1:raise ValueError('actual selected slot-to-CPU receipt')
  inputs={n:cpu(kw[n])for n in('query','key','value','g','beta')};before=snap(layer,ids);pointers={n:kw[n].data_ptr()for n in inputs}
  key=(layer.prefix,c['engine_request_id'])
  if key not in native_states:raise ValueError('native prefill boundary must precede selected decode')
  ghost=native_states[key];native_before=cpu(ghost)
  if ghost.untyped_storage().data_ptr()==layer.kv_cache[1].untyped_storage().data_ptr():raise ValueError('native diagnostic state must be isolated')
  import sidecar_capture
  capture=sidecar_capture.Capture(torch,actual_op[0],debug_op[0])
  capture.sink=lambda name,value:store.write(root/('sidecar-%06d.pt'%count),dict(value,model_identity={k:c[k]for k in('source','prefix','layer_idx','pid','rank','epoch','engine_request_id')},production_library=m['library_ref'],debug_library=m['debug_library']))
  token=OP_CAPTURE.set(capture)
  try:out=original_route(T,layer,**kw)
  finally:OP_CAPTURE.reset(token)
  sidecar_ref=capture.take()
  if len(capture.records)!=1:raise ValueError('one real selected B010 dispatch per decode')
  native_out=torch.ops._C_ascend.npu_recurrent_gated_delta_rule(query=kw['query'].contiguous(),key=kw['key'].contiguous(),value=kw['value'].contiguous(),g=kw['g'].contiguous(),beta=kw['beta'].contiguous(),state=ghost,scale=kw['scale'],actual_seq_lengths=kw['actual_seq_lengths'].contiguous(),ssm_state_indices=torch.zeros_like(ids).contiguous())
  data=dict(before=before,after=snap(layer,ids),actual_ids=actual_ids,inputs=inputs,input_after={n:cpu(kw[n])for n in inputs},output=cpu(out),native_before=native_before,native_after=cpu(ghost),native_output=cpu(native_out),scale=kw['scale'],pointer_before=pointers,pointer_after={n:kw[n].data_ptr()for n in inputs},actual_NPU=True,actual_sidecar045=sidecar_ref)
  save('decode',c,data);return out
 def chunk(*a,**kw):
  c=CURRENT.get()
  if c is None:return original_chunk(*a,**kw)
  names=('q','k','v','g','beta','initial_state','cu_seqlens','use_qk_l2norm_in_kernel','scale')
  inputs={n:cpu(kw[n])for n in names if n in kw};value=original_chunk(*a,**kw)
  native_states[(c['prefix'],c['engine_request_id'])]=value[1].transpose(-1,-2).contiguous().clone()
  c['chunks'].append(dict(inputs=inputs,output=cpu(value[0]),final_state=cpu(value[1])));return value
 @functools.wraps(original_core)
 def core(T,legacy,gdn,specialized,native,self,mixed_qkv,b,a,core,emit=None):
  r=select(self)
  if r is None:return original_core(T,legacy,gdn,specialized,native,self,mixed_qkv,b,a,core,emit=emit)
  c=context(self,r);meta=c['meta'];prefill=meta.num_prefills
  if prefill:
   ids=meta.prefill_state_indices;actual_ids=cpu(ids).flatten().tolist()
   if actual_ids!=list(meta._deltalog018_cpu_receipt['cpu'].prefill)or len(actual_ids)!=1:raise ValueError('actual B1 prefill selection')
   before=snap(self,ids);has_initial=cpu(meta.prefill_has_initial_state).flatten().tolist()
  token=CURRENT.set(c)
  try:result=original_core(T,legacy,gdn,specialized,native,self,mixed_qkv,b,a,core,emit=emit)
  finally:CURRENT.reset(token)
  if prefill:save('prefill',c,dict(before=before,after=snap(self,ids),actual_ids=actual_ids,has_initial=has_initial,chunks=c['chunks'],core_output=cpu(core),actual_NPU=True))
  return result
 R._route=route;H.execute_mixed_core=core;G.chunk_gated_delta_rule=chunk
 actual_op=[];debug_op=[]
 def activate():
  if actual_op or R._OP is None:raise ValueError('activate once after real023 registration')
  import owner_overlay as O
  for key in('debug_library','debug_build_ref','debug_kernel_source_ref'):O.obj_file(m[key])
  torch.ops.load_library(m['debug_library']['path'])
  namespace='qwen36_deltalog_split_scale_sidecar_v051'
  if not torch._C._dispatch_has_kernel_for_dispatch_key(namespace+'::decode','PrivateUse1'):raise ValueError('actual015 PrivateUse1 sidecar')
  if not any(m['debug_library']['path']in s for s in Path('/proc/self/maps').read_text().splitlines()):raise ValueError('actual015 DSO map')
  actual_op.append(R._OP);debug_op.append(getattr(torch.ops,namespace).decode)
  R._OP=dispatch_for(actual_op[0])
 return activate

"""Untimed actual004 once-candidate capture. Default OFF; no native shadow replay."""
import contextvars,functools,hashlib,importlib.util,inspect,json,os,sys
from pathlib import Path
P=Path(__file__).resolve().parent
_installed_bridge=None

def read_arm(root,run_id):
 p=root/'ARM-LONG.json'
 if not p.exists():return None
 need(p.is_file()and not p.is_symlink()and p.stat().st_size<=4096,'bounded long ARM')
 v=json.loads(p.read_bytes());need(v==dict(schema='mxr.long.arm/v1',run_id=run_id,lengths=[32768,40960]),'exact long source-qualified ARM')
 return v

def need(v,s):
 if not v:raise ValueError(s)
def ref(p):
 b=Path(p).read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def checked(r):
 p=Path(r['path']);b=p.read_bytes();need(len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'],'actual full source Ref3');return b
def fingerprint(torch,t):
 c=t.detach().cpu().contiguous();b=c.view(torch.uint8).numpy().tobytes();return dict(dtype=str(t.dtype),shape=list(t.shape),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def install():
 global _installed_bridge
 if _installed_bridge is not None:return _installed_bridge
 if os.environ.get('MXR_ONCE_CORRECTNESS_ENABLE')!='1':return None
 sr=json.loads(os.environ['MXR_ONCE_CORRECTNESS_SOURCE_REF']);m=json.loads(checked(sr))
 need(m['schema']=='mxr.diag16.full-gdn-frame-bridge-source/v1'and m['stage']=='long-both'and m['default_enabled']is False,'explicit bounded new diagnostic stage')
 from admission047 import consume
 consume(m['new_prerequisites'])
 for r in m['files'].values():checked(r)
 plugin=m['plugin_source'];mf=json.loads(checked(plugin))
 for r in mf['files'].values():checked(r)
 plugin_root=Path(mf['root']);sys.path.insert(0,str(plugin_root))
 import observerless_install as I
 need(Path(I.__file__).resolve()==plugin_root/'observerless_install.py','genuine004 module not sibling shadow')
 q=json.loads(checked(json.loads(os.environ['MXR_OBSERVERLESS_QUALIFICATION_REF'])))
 need(q['mode']=='correctness'and q['plugin_source_ref']==plugin and {32768,40960}<=set(q['lengths']),'actual004 correctness only; notperformance receipt')
 runtime=I.install();need(runtime is not None and runtime['mode']=='correctness','actual004 installed')
 import torch,block_refine
 common=__import__('common_precision');precision=common.apply(torch)
 from vllm_ascend.ops import gdn
 root=Path(os.environ['MST_MXR_SOLVE_EVIDENCE_ROOT']);need(root.is_absolute()and root.is_dir(),'soleowned output')
 raw_root=Path(os.environ['MXR_LONG_RAW_ROOT']);need(str(raw_root)==m['raw_storage']['root']and raw_root.is_dir()and raw_root.stat().st_dev==root.stat().st_dev and m['raw_storage']['one_shared_reserve']is True,'actual sameopt raw/control with one registered combined ledger')
 spec=importlib.util.spec_from_file_location('_lossless011',P/'lossless_raw.py');codec=importlib.util.module_from_spec(spec);spec.loader.exec_module(codec)
 run_id=os.environ['MST_MXR_MODEL_RUN_ID'];need(run_id==m['runtime_identity']['run_id'],'same MAIN owned run')
 wr=root/('worker-'+str(os.getpid()));wr.mkdir(exist_ok=False)
 raw_wr=raw_root/('worker-'+str(os.getpid()));raw_wr.mkdir(exist_ok=False)
 pending={};phase={};decode_counts={}
 with(wr/'RUNTIME.json').open('x')as h:json.dump(dict(schema='mxr.observerless-once-runtime/v1',source=sr,plugin_source=plugin,pid=os.getpid(),run_id=run_id,mode='correctness',performance_ready=False),h,sort_keys=True)
 captured=set();warmup={};scope=contextvars.ContextVar('actual_once_frame',default=None);prefix=contextvars.ContextVar('actual_once_prefix',default=None);charged=0
 original_eager=block_refine.eager
 need(Path(block_refine.__file__).resolve()==plugin_root/'block_refine.py','actual044 eager seam, not old safe_eager')
 @functools.wraps(original_eager)
 def observed(solver,A,cu,chunks,dtype,pool,backend,boundaries):
  frame=scope.get()
  if frame is None:return original_eager(solver,A,cu,chunks,dtype,pool,backend,boundaries)
  before=A.detach().cpu().clone();cb=cu.detach().cpu().clone()
  need(tuple(boundaries)==tuple(cb.tolist()),'actual044 immutable host boundaries match captured cu')
  need(pool.max_bytes==512*1024**2 and pool.max_entries==2,'unchanged actual044512MiB/2entries')
  out=original_eager(solver,A,cu,chunks,dtype,pool,backend,boundaries);torch.npu.synchronize()
  need(frame.get('solve')is None,'one candidate solve per captured real chunk')
  frame['solve']=dict(A=before,cu=cb,A_after=fingerprint(torch,A),cu_after=fingerprint(torch,cu),output=out.detach().cpu())
  frame['FP32_policy']=dict(precision,common_to_all_arms=True);frame['block044']=dict(boundaries=list(boundaries),chunks=chunks,source=plugin,pool_bytes=pool.max_bytes,pool_entries=pool.max_entries)
  return out
 block_refine.eager=observed
 from vllm_ascend.ops.triton.fla import chunk as chunk_module
 original_fwd=chunk_module.chunk_gated_delta_rule_fwd;fwd_signature=inspect.signature(original_fwd)
 @functools.wraps(original_fwd)
 def normalized_boundary(*a,**kw):
  frame=scope.get()
  if frame is not None:
   need('normalized_inputs'not in frame,'one actual normalized chunk boundary')
   bound=fwd_signature.bind(*a,**kw);bound.apply_defaults();v=bound.arguments
   frame['normalized_inputs']={k:t.detach().cpu().clone()for k,t in v.items()if torch.is_tensor(t)}
   frame['normalized_inputs']['scale']=v['scale'];frame['normalized_inputs']['already_normalized']=True
  out=original_fwd(*a,**kw)
  if frame is not None:frame['normalized_inputs_after']={k:fingerprint(torch,t)for k,t in v.items()if torch.is_tensor(t)}
  return out
 chunk_module.chunk_gated_delta_rule_fwd=normalized_boundary
 def after_core(self,layer,result):
  if layer in pending:
   frame,returned=pending.pop(layer)
   from vllm.forward_context import get_forward_context
   meta=get_forward_context().attn_metadata[layer];idx=meta.prefill_state_indices
   need(idx is not None,'actual prefill physical state indices')
   physical=self.kv_cache[1].index_select(0,idx.long()).detach().cpu()
   with(frame/'PHYSICAL.pt').open('xb')as h:torch.save(dict(indices=idx.detach().cpu(),physical_after=physical,returned=returned,prefill_has_initial_state=meta.prefill_has_initial_state.detach().cpu()),h)
   with(frame/'PHYSICAL.json').open('x')as h:json.dump(ref(frame/'PHYSICAL.pt'),h)
 binding_ref=m['actual_core_binding_ref'];checked(binding_ref)
 spec=importlib.util.spec_from_file_location('_long012_actual_qwen_binding',binding_ref['path']);binding_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(binding_module)
 actual_binding=binding_module.actual(gdn,runtime,prefix,wr,sr,run_id,after=after_core)
 native_recurrent=torch.ops._C_ascend.npu_recurrent_gated_delta_rule
 @functools.wraps(native_recurrent)
 def recurrent(*a,**kw):
  layer=prefix.get();T=phase.get(layer);key=(T,layer);number=decode_counts.get(key,0)
  if a or T is None or number>=2:return native_recurrent(*a,**kw)
  need(read_arm(root,run_id)is not None and kw.get('num_accepted_tokens')is None,'non-spec actual long decode only')
  idx=kw['ssm_state_indices'].flatten().long();state=kw['state'];lens=kw['actual_seq_lengths'].detach().cpu()
  need(idx.numel()==lens.numel()-1 and lens[0].item()==0 and sum(lens[1:].tolist())==kw['query'].shape[0],'actual builder lengths, NOT cumulative reinterpretation')
  data={k:v.detach().cpu().clone()for k,v in kw.items()if torch.is_tensor(v)and k!='state'}
  data.update(initial_state=state.index_select(0,idx).detach().cpu().clone(),scale=kw['scale'])
  out=native_recurrent(*a,**kw);torch.npu.synchronize();data.update(output=out.detach().cpu(),final_state=state.index_select(0,idx).detach().cpu())
  path=raw_wr/('decode-%d-%s-%d.pt'%(T,hashlib.sha256(layer.encode()).hexdigest()[:16],number))
  codec.write(torch,path,data)
  with(wr/path.with_suffix('.json').name).open('x')as h:json.dump(dict(schema='mxr.long-native-decode/v1',source=sr,plugin_source=plugin,run_id=run_id,pid=os.getpid(),prefix=layer,prefill_tokens=T,step=number,raw=ref(path)),h,sort_keys=True)
  decode_counts[key]=number+1;return out
 torch.ops._C_ascend.npu_recurrent_gated_delta_rule=recurrent
 original_chunk=gdn.chunk_gated_delta_rule;signature=inspect.signature(original_chunk)
 @functools.wraps(original_chunk)
 def capture(*args,**kwargs):
  nonlocal charged
  layer=prefix.get();need(type(layer)is str,'real GDNcore prefix')
  armed=read_arm(root,run_id)is not None
  x=signature.bind(*args,**kwargs);x.apply_defaults();tokens=x.arguments['q'].shape[1]
  if not armed:
   out=original_chunk(*args,**kwargs);warmup[layer]=True;return out
  expected_count=96
  key=(tokens,layer)
  if key in captured or len(captured)>=expected_count:return original_chunk(*args,**kwargs)
  need(len(warmup)==48 and tokens in(32768,40960)and not torch.npu.is_current_stream_capturing(),'actual48 native warmup and exact packed stage')
  v=x.arguments;needed=sum(t.numel()*t.element_size()for t in v.values()if torch.is_tensor(t))+v['v'].numel()*v['v'].element_size()+v['initial_state'].numel()*v['initial_state'].element_size()+tokens*12*64*6+1024**2
  need(v['head_first']is False and v['use_qk_l2norm_in_kernel']is True and v['output_final_state']is True,'actual native GDN reference contract')
  needed+=sum(t.numel()*t.element_size()for t in v.values()if torch.is_tensor(t))
  need(needed<=768*1024**2 and charged+needed<=64*1024**3,'explicit long perframe768MiB/perworker64GiB raw guard');charged+=needed
  frame=wr/('frame-%03d'%len(captured));frame.mkdir()
  data={'inputs':{k:t.detach().cpu().clone()for k,t in v.items()if torch.is_tensor(t)}}
  data['inputs']['scale']=v['scale'] if v['scale']is not None else v['q'].shape[-1]**-.5
  token=scope.set(data);before=runtime['counts']['candidate']
  try:out,state=original_chunk(*args,**kwargs);torch.npu.synchronize()
  finally:scope.reset(token)
  need(runtime['counts']['candidate']-before==1 and state is not None and data.get('solve')is not None,'real004 admission/hit, no allfallback or duplicatecertificate')
  data['inputs_after']={k:fingerprint(torch,t)for k,t in v.items()if torch.is_tensor(t)};data['inputs_after']['scale']=data['inputs']['scale'];data['output']=out.detach().cpu();data['final_state']=state.detach().cpu()
  raw_frame=raw_wr/frame.name;raw_frame.mkdir()
  target=raw_frame/'RAW.pt'
  codec.write(torch,target,data)
  ordinal=actual_binding['associations'][layer]['ordinal']
  note=dict(schema='mxr.observerless-once-frame/v1',source=sr,plugin_source=plugin,pid=os.getpid(),run_id=run_id,prefix=layer,stage='long'+str(tokens),tokens=tokens,candidate_delta=1,graph=False,raw=ref(target),capture_cost_not_performance=True,core_binding=ref(wr/'CORE_BINDING.json'),instance_binding=ref(wr/('core-binding-%03d.json'%ordinal)))
  with(frame/'FRAME.json').open('x')as f:json.dump(note,f,sort_keys=True)
  pending[layer]=(raw_frame,state.detach().cpu().clone());phase[layer]=tokens
  captured.add(key);return out,state
 gdn.chunk_gated_delta_rule=capture
 _installed_bridge=dict(actual004_installed=True,observer_binding_file=__file__,captured=captured,multistep_qualified=False,performance=False)
 return _installed_bridge
def register():return install()

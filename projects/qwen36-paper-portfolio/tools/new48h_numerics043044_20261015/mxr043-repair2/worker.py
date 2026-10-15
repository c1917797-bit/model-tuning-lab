"""Untimed actual004 once-candidate capture. Default OFF; no native shadow replay."""
import contextvars,functools,hashlib,importlib.util,inspect,json,os,sys
from pathlib import Path
P=Path(__file__).resolve().parent
_installed_bridge=None

def read_arm(root,run_id):
 p=root/'ARM.json'
 if not p.exists():return None
 need(p.is_file()and not p.is_symlink()and p.stat().st_size<=4096,'bounded actual ARM')
 value=json.loads(p.read_bytes());need(value==dict(schema='mxr.capture.arm/v1',run_id=run_id),'actual original003 ARM exact schema/run_id; not existence')
 return value
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
 need(m['schema']=='mxr.diag16.full-gdn-frame-bridge-source/v1'and m['stage']in('short129','long32768','long40960')and m['default_enabled']is False,'explicit bounded new diagnostic stage')
 for r in m['files'].values():checked(r)
 spec=importlib.util.spec_from_file_location('_043_admit',m['files']['admit042.py']['path']);admit=importlib.util.module_from_spec(spec);exec(compile(checked(m['files']['admit042.py']),m['files']['admit042.py']['path'],'exec'),admit.__dict__);admit.gate(m['actual042_owner_ref'])
 plugin=m['plugin_source'];mf=json.loads(checked(plugin))
 for r in mf['files'].values():checked(r)
 plugin_root=Path(mf['root']);sys.path.insert(0,str(plugin_root))
 import observerless_install as I
 need(Path(I.__file__).resolve()==plugin_root/'observerless_install.py','genuine004 module not sibling shadow')
 q=json.loads(checked(json.loads(os.environ['MXR_OBSERVERLESS_QUALIFICATION_REF'])))
 need(q['mode']=='correctness'and q['plugin_source_ref']==plugin and m['tokens']in q['lengths'],'actual004 correctness only; notperformance receipt')
 runtime=I.install();need(runtime is not None and runtime['mode']=='correctness','actual004 installed')
 import torch,safe_eager
 spec=importlib.util.spec_from_file_location('_043_actual_refiner',m['files']['refine.py']['path']);refiner=importlib.util.module_from_spec(spec);exec(compile(checked(m['files']['refine.py']),m['files']['refine.py']['path'],'exec'),refiner.__dict__)
 spec=importlib.util.spec_from_file_location('_043_common_precision',m['files']['common_precision.py']['path']);policy=importlib.util.module_from_spec(spec);exec(compile(checked(m['files']['common_precision.py']),m['files']['common_precision.py']['path'],'exec'),policy.__dict__)
 precision=policy.apply(torch,refiner)
 from vllm_ascend.ops import gdn
 root=Path(os.environ['MST_MXR_SOLVE_EVIDENCE_ROOT']);need(root.is_absolute()and root.is_dir(),'soleowned output')
 run_id=os.environ['MST_MXR_MODEL_RUN_ID'];need(run_id==m['runtime_identity']['run_id'],'same MAIN owned run')
 wr=root/('worker-'+str(os.getpid()));wr.mkdir(exist_ok=False)
 with(wr/'RUNTIME.json').open('x')as h:json.dump(dict(schema='mxr.observerless-once-runtime/v1',source=sr,plugin_source=plugin,pid=os.getpid(),run_id=run_id,mode='correctness',performance_ready=False),h,sort_keys=True)
 captured=set();warmup={};scope=contextvars.ContextVar('actual_once_frame',default=None);prefix=contextvars.ContextVar('actual_once_prefix',default=None);charged=0
 original_eager=safe_eager.eager
 @functools.wraps(original_eager)
 def observed(solver,A,cu,chunks,dtype,pool,backend):
  frame=scope.get()
  if frame is None:return original_eager(solver,A,cu,chunks,dtype,pool,backend)
  before=A.detach().cpu().clone();cb=cu.detach().cpu().clone()
  trace={};out=refiner.eager(solver,A,cu,chunks,dtype,pool,backend,cb.tolist(),trace=trace);torch.npu.synchronize()
  frame['refinement']={k:t.detach().cpu().clone()for k,t in trace.items()};frame['FP32_policy']=precision
  need(frame.get('solve')is None,'one candidate solve per captured real chunk')
  frame['solve']=dict(A=before,cu=cb,A_after=fingerprint(torch,A),cu_after=fingerprint(torch,cu),output=out.detach().cpu())
  return out
 safe_eager.eager=observed
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
 from prefix_binding import actual as bind_actual_core
 binding=bind_actual_core(gdn,runtime,prefix,wr,sr,run_id)
 original_chunk=gdn.chunk_gated_delta_rule;signature=inspect.signature(original_chunk)
 @functools.wraps(original_chunk)
 def capture(*args,**kwargs):
  nonlocal charged
  layer=prefix.get();need(type(layer)is str,'real GDNcore prefix')
  armed=read_arm(root,run_id)is not None
  x=signature.bind(*args,**kwargs);x.apply_defaults();tokens=x.arguments['q'].shape[1]
  if not armed:
   out=original_chunk(*args,**kwargs);warmup[layer]=True;return out
  expected_count=48 if m['stage']=='short129'else 1
  if layer in captured or len(captured)>=expected_count:return original_chunk(*args,**kwargs)
  need(len(warmup)==48 and tokens==m['tokens']and not torch.npu.is_current_stream_capturing(),'actual48 native warmup and exact packed stage')
  v=x.arguments;needed=sum(t.numel()*t.element_size()for t in v.values()if torch.is_tensor(t))+v['v'].numel()*v['v'].element_size()+v['initial_state'].numel()*v['initial_state'].element_size()+tokens*12*64*8
  need(v['head_first']is False and v['use_qk_l2norm_in_kernel']is True and v['output_final_state']is True,'actual native GDN reference contract')
  needed+=sum(t.numel()*t.element_size()for t in v.values()if torch.is_tensor(t))
  # Exact retained042 trace: four packed FP32 matrices and two full FP32 outputs.
  # This is charged to the unchanged768MiB worker evidence guard, not a new budget.
  needed+=((tokens+63)//64)*12*64*64*4*4+tokens*12*64*4*2
  need(charged+needed<=768*1024**2,'unchanged perworker768MiB complete raw guard');charged+=needed
  frame=wr/('frame-%03d'%len(captured));frame.mkdir()
  data={'inputs':{k:t.detach().cpu().clone()for k,t in v.items()if torch.is_tensor(t)}}
  data['inputs']['scale']=v['scale'] if v['scale']is not None else v['q'].shape[-1]**-.5
  token=scope.set(data);before=runtime['counts']['candidate']
  try:out,state=original_chunk(*args,**kwargs);torch.npu.synchronize()
  finally:scope.reset(token)
  need(runtime['counts']['candidate']-before==1 and state is not None and data.get('solve')is not None,'real004 admission/hit, no allfallback or duplicatecertificate')
  data['inputs_after']={k:fingerprint(torch,t)for k,t in v.items()if torch.is_tensor(t)};data['inputs_after']['scale']=data['inputs']['scale'];data['output']=out.detach().cpu();data['final_state']=state.detach().cpu()
  target=frame/'RAW.pt'
  with target.open('xb')as f:torch.save(data,f)
  association=binding['associations'][layer]
  note=dict(schema='mxr.observerless-once-frame/v1',source=sr,plugin_source=plugin,pid=os.getpid(),run_id=run_id,prefix=layer,stage=m['stage'],candidate_delta=1,graph=False,raw=ref(target),core_binding=ref(wr/'CORE_BINDING.json'),instance_binding=ref(wr/('core-binding-%03d.json'%association['ordinal'])),capture_cost_not_performance=True)
  with(frame/'FRAME.json').open('x')as f:json.dump(note,f,sort_keys=True)
  captured.add(layer);return out,state
 gdn.chunk_gated_delta_rule=capture
 _installed_bridge=dict(actual004_installed=True,observer_binding_file=__file__,captured=captured,bound_core=binding,multistep_qualified=False,performance=False)
 return _installed_bridge
def register():return install()

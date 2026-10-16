"""General-plugin registration is not actual model execution or a worker lease."""
import functools,hashlib,importlib,inspect,json,os
from pathlib import Path
PINS={'vllm_ascend.ops.gdn':'d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816','vllm_ascend.patch.worker.patch_qwen3_5':'21fc9a2064f9b490ffcf3d61bacc8ddb67806a4c7490895a33128e65438838d3','vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn':'885c56f5e3584ab60bb4ce4b42cf8259e5e92c86ba13aa6128e6ed7a2a20d2b0'}
def need(v,m):
 if not v:raise ValueError(m)
def ref(p):
 b=Path(p).read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
class Registration:
 def __init__(self,target,native,get_context,install,ensure,source,run_id,root,sources):
  self.target=target;self.native=native;self.install=install;self.ensure=ensure;self.source=source;self.run_id=run_id;self.root=Path(root);self.sources=sources;self.installed=False;self.failure=None;self.pid=os.getpid();self.bound=None
  prior=target._forward_core;need(inspect.unwrap(prior)is native,'real copied Qwen target prior native origin')
  @functools.wraps(native)
  def first(instance,*a,**kw):
   if self.failure is not None:raise RuntimeError('first-core install already failed; no deterministic retry')from self.failure
   if self.installed:raise ValueError('stale bootstrap invoked after actual binding')
   layer=instance.prefix
   need(os.getpid()==self.pid and isinstance(instance,target)and target._forward_core is first and type(layer)is str and layer and get_context().no_compile_layers.get(layer)is instance,'actual first Qwen self/MRO/no_compile instance before install')
   try:
    operator=self.ensure() # Real worker custom-op registration, never fake torch.ops.
    target._forward_core=prior
    self.install() # The whole original065 install body runs only HERE.
    current=target._forward_core;need(current is not first and inspect.unwrap(current)is native,'actual installer replaced real copied target preserving native origin')
    self.bound=current;self.installed=True
    wr=self.root/('worker-'+str(os.getpid()));need((wr/'RUNTIME.json').is_file()and (wr/'CORE_BINDING.json').is_file(),'actual worker evidence exists only after true install')
    value=dict(schema='mxr.actual-first-core-install/v067',source=source,run_id=run_id,pid=os.getpid(),first_prefix=layer,first_instance_id=id(instance),before_first_actual_core=True,official_operator=operator,actual_worker_install=True,registry_registration_is_not_worker=True,source_pins=sources)
    with(wr/'FIRST_CORE_INSTALL.json').open('x')as f:json.dump(value,f,sort_keys=True,allow_nan=False);f.write('\n')
    return current(instance,*a,**kw)
   except BaseException as exc:self.failure=exc;raise
  self.first=first;target._forward_core=first
 def verify(self):
  need(os.getpid()==self.pid and self.target._forward_core is(self.bound if self.installed else self.first),'same process and actual bootstrap/core still bound, no late patch overwrite')
 def receipt(self):
  self.verify();return dict(schema='mxr.registration-only-no-worker/v067',source=self.source,pid=self.pid,run_id=self.run_id,registered=True,pending_actual_first_core=not self.installed,actual_worker_installed=self.installed,model_instance_count=0 if not self.installed else None,source_pins=self.sources,bootstrap_bound=not self.installed,worker_numeric_proved=False)
def official_operator():
 import torch
 try:op=torch.ops._C_ascend.npu_recurrent_gated_delta_rule
 except AttributeError as exc:raise ValueError('actual first GDN core requires official recurrent custom-op registration')from exc
 qualified='_C_ascend::npu_recurrent_gated_delta_rule'
 need(isinstance(op,torch._ops.OpOverloadPacket)and getattr(op,'_qualified_op_name',None)==qualified,'genuine registered recurrent OpOverloadPacket required')
 schemas={k:str(v)for k,v in op._schemas.items()};need(schemas and any(qualified in v and 'query'in v and 'state'in v for v in schemas.values()),'real official operator schemas')
 return dict(qualified_name=qualified,OpOverloadPacket=True,schemas=schemas,object_id=id(op),before_actual_first_core=True)
def register(install,source_root):
 sr=json.loads(os.environ['MXR_ONCE_CORRECTNESS_SOURCE_REF']);need(ref(sr['path'])==sr,'exact current source whole bytes')
 m=json.loads(Path(sr['path']).read_bytes());need(m['root']==str(source_root)and m['schema']=='mxr.diag16.full-gdn-frame-bridge-source/v1'and m['default_enabled']is False,'same frozen caller defaultOFF source')
 for n,r in m['files'].items():need(Path(r['path'])==source_root/n and ref(r['path'])==r,'exact current registration closure')
 modules={};sources={}
 for name,digest in PINS.items():
  module=importlib.import_module(name);path=Path(inspect.getsourcefile(module)).resolve();r=ref(path);need(r['sha256']==digest,'real framework registration source '+name);modules[name]=module;sources[name]=r
 gdn=modules['vllm_ascend.ops.gdn'];target=modules['vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn'].QwenGatedDeltaNetAttention
 need(modules['vllm_ascend.patch.worker.patch_qwen3_5']._GDN_PATCH_TARGET is target,'actual copied-method target alias')
 native=gdn.AscendGatedDeltaNetAttention._forward_core;need(inspect.unwrap(native)is native,'no algorithm install during architecture registration')
 return Registration(target,native,gdn.get_forward_context,install,official_operator,sr,m['runtime_identity']['run_id'],Path(os.environ['MST_MXR_SOLVE_EVIDENCE_ROOT']),sources)
def software_controls():
 """Source/MRO bootstrap lifecycle control only; no fake native operator."""
 import types
 events=[]
 class Target:
  def _forward_core(self,*a,**kw):events.append('native');return 'source-only-return'
 native=Target._forward_core;instance=Target();instance.prefix='L';context=lambda:types.SimpleNamespace(no_compile_layers={'L':instance})
 def missing():events.append('official-check');raise ValueError('software missing-operator negative')
 reg=Registration(Target,native,context,lambda:events.append('install'),missing,{},'software',Path('.'),{})
 need(not events and reg.receipt()['pending_actual_first_core']is True,'registration must not touch operator/install/files')
 try:instance._forward_core()
 except ValueError:pass
 else:raise ValueError('actual first forward missing op must fail')
 need(events==['official-check']and not reg.installed,'no worker install on missing op')
 try:instance._forward_core()
 except RuntimeError:pass
 else:raise ValueError('must not retry deterministic first-core failure')
 need(events==['official-check'],'no repeat official lookup/install after failure')
 Target._forward_core=native
 return dict(registry_no_install=True,no_fake_ops=True,first_core_missing_hardfail=True,no_retry=True,NPU=False)

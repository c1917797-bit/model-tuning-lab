"""Fresh006 KDMA namespace provider; defaultOFF; no oldbinary aliases."""
import functools,hashlib,json,os,time
from pathlib import Path
from . import contract as C,primitives as L,runtime_helpers as H
from .transform import clone_core
_OP=None
_DISPATCH={}
_ADMISSION=None
def _ref(path):
 p=Path(path);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def _obj(r):
 p=Path(r['path'])
 if set(r)!={'path','bytes','sha256'}or not p.is_absolute()or p.is_symlink()or _ref(p)!=r:raise RuntimeError('exact actual Ref3')
 return json.loads(p.read_bytes())
def source_admission(source_ref,lifecycle_ref):
 m=_obj(source_ref)
 if m['schema']!='deltalog.deadpayload-native-bridge-source/v024'or m['root']!=str(Path(__file__).resolve().parent.parent)or m['default_enabled']is not False or m['window']!={'start':1791962297,'cutoff':1792135097}or not 1791962297<=time.time()<1792135097:raise RuntimeError('new exact source identity/defaultOFF/fixedwindow')
 for r in m['files'].values():
  if Path(r['path']).is_symlink()or _ref(r['path'])!=r:raise RuntimeError('sourcefile digest drift')
 if m.get('prepared_only',True):raise RuntimeError('actual022 composite binding pending')
 api=m['composite_api_ref'];p=Path(api['path'])
 if _ref(p)!=api:raise RuntimeError('actual022 API digest')
 import importlib.util
 s=importlib.util.spec_from_file_location('_bridge024_actual022',p);v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
 if lifecycle_ref!=m['composite_cpu_owner_ref']:raise RuntimeError('exact actual022 owned CPU receipt')
 life=v.admit_receipt(m['composite_source_ref'],lifecycle_ref)
 if life['library']!=m['library_ref'] or life['model_ready']is not False:raise RuntimeError('same production B010 component-only source')
 return m,life
def configure(source_ref,lifecycle_ref,*,explicit=False):
 global _OP,_ADMISSION
 if not explicit:raise RuntimeError('explicit fixture/model admission required')
 m,life=source_admission(source_ref,lifecycle_ref)
 import torch
 from vllm_ascend.utils import enable_custom_op
 if not enable_custom_op():raise RuntimeError('actual Ascendnative ops unavailable')
 lib=m['library_ref'];C.require_digest(lib['path'],C.LIBRARY_SHA)
 if _ref(lib['path'])!=lib:raise RuntimeError('library Refdrift')
 torch.ops.load_library(lib['path']);op=getattr(torch.ops,C.NAMESPACE).decode
 signature=C.NAMESPACE+'::decode(Tensor query, Tensor key, Tensor value, Tensor g, Tensor beta, Tensor(a!) base_state, Tensor(b!) k_log, Tensor(c!) u_log, Tensor(d!) lambda_log, Tensor(e!) cumulative_decay, Tensor(f!) log_length, Tensor actual_seq_lengths, Tensor state_indices) -> Tensor'
 if str(op.default._schema)!=signature or not torch._C._dispatch_has_kernel_for_dispatch_key(C.NAMESPACE+'::decode','PrivateUse1'):raise RuntimeError('actual freshnamespace/schema/dispatch ABI')
 if not any(lib['path']in line for line in Path('/proc/self/maps').read_text().splitlines()):raise RuntimeError('actual mapped freshlib required')
 _OP=op;_ADMISSION=dict(source=source_ref,lifecycle=lifecycle_ref,library=lib,namespace=C.NAMESPACE)
 return dict(_ADMISSION,schema=signature)
def _route(torch,legacy,layer,*,query,key,value,g,beta,state,scale,actual_seq_lengths,ssm_state_indices,**extra):
 if _OP is None or extra:raise RuntimeError('freshprovider unconfigured/unsupported nativekwargs')
 aux=H._bind(torch,legacy,layer);tokens=query.shape[0]
 if state.data_ptr()!=layer.kv_cache[1].data_ptr()or not 1<=tokens<=16 or ssm_state_indices.numel()!=tokens or actual_seq_lengths.numel()!=tokens+1:raise RuntimeError('ownedstate/tokens/sequenceABI')
 if abs(float(scale)-128**-.5)>1e-12:raise RuntimeError('native scaleABI')
 specs=((query,torch.bfloat16,[tokens,4,128]),(key,torch.bfloat16,[tokens,4,128]),(value,torch.bfloat16,[tokens,12,128]),(g,torch.float32,[tokens,12]),(beta,torch.bfloat16,[tokens,12]))
 if any(t.device.type!='npu'or t.dtype!=d or list(t.shape)!=shape for t,d,shape in specs):raise RuntimeError('actual fresh kernel geometry/dtype')
 if actual_seq_lengths.dtype!=torch.int32 or ssm_state_indices.dtype!=torch.int32:raise RuntimeError('native indicesdtype')
 out=_OP(query.contiguous(),key.contiguous(),value.contiguous(),g.contiguous(),beta.contiguous(),state,aux['k_log'],aux['u_log'],aux['lambda_log'],aux['decay'],aux['length'],actual_seq_lengths.contiguous(),ssm_state_indices.contiguous())
 _DISPATCH[layer.prefix]=_DISPATCH.get(layer.prefix,0)+1
 return out
def install_fixture(torch,gdn,mu,emit):
 C.require_digest(gdn.__file__,C.GDN_SHA);C.require_digest(mu.__file__,C.MAMBA_SHA)
 if _OP is None:raise RuntimeError('fresh configured operator required')
 H._event=emit;H.install_copy_bridge(torch,L,mu)
 return functools.partial(_route,torch,L)
def register():
 if os.environ.get('QWEN36_DELTALOG_FRESH_ENABLE')!='1':return
 if os.environ.get('QWEN36_DELTALOG_ENABLE')=='1'or os.environ.get('QWEN36_DELTALOG_MIXED_ENABLE')=='1':raise RuntimeError('oldproviders cannot coexist')
 sr=json.loads(os.environ['QWEN36_DELTALOG_FRESH_SOURCE_REF']);lr=json.loads(os.environ['QWEN36_DELTALOG_FRESH_LIFECYCLE_REF']);br=json.loads(os.environ['QWEN36_DELTALOG_FRESH_BRIDGE_REF']);m,life=source_admission(sr,lr);bridge=_obj(br)
 # Model hook is not authorized by a component-only kernel PASS.
 if bridge['schema']!='deltalog.fresh-bridge-consumption/v1'or bridge['source']!=sr or bridge['pass_gate']is not True or bridge['actual_prefill_CPU64_qualified']is not True or bridge['actual_native_copy_qualified']is not True:raise RuntimeError('fullmixed/copy independent bridge qualification pending')
 configure(sr,lr,explicit=True)
 import torch,vllm_ascend.ops.gdn as gdn
 from vllm.v1.worker import mamba_utils as mu
 from vllm_ascend.worker import model_runner_v1 as runner
 C.require_digest(gdn.__file__,C.GDN_SHA);C.require_digest(mu.__file__,C.MAMBA_SHA);C.require_digest(runner.__file__,C.RUNNER_SHA)
 if getattr(runner,'mamba_utils',None)is not mu:raise RuntimeError('realrunner copy module identity')
 cls=gdn.AscendGatedDeltaNetAttention
 if getattr(cls,'_qwen36_deltalog_fresh_version',None)=='1':
  if getattr(cls,'_qwen36_deltalog_fresh_source_sha',None)!=sr['sha256']:raise RuntimeError('differentfresh patch/source alreadyinstalled')
  return
 if hasattr(cls,'_qwen36_deltalog_original_forward_core')or getattr(cls,'_qwen36_deltalog_mixed_version',None):raise RuntimeError('unreviewed duplicatepatch')
 original=cls._forward_core;specialized=clone_core(Path(gdn.__file__).read_text(),vars(gdn),functools.partial(_route,torch,L))
 def event(name,**fields):
  # Actual worker rank stays sourced from initialized TP, never guest deviceID.
  H._event_original(name,**fields)
 H._event_original=H._event;H._event=event
 @functools.wraps(original)
 def core(self,mixed_qkv,b,a,out):return H.execute_mixed_core(torch,L,gdn,specialized,original,self,mixed_qkv,b,a,out,event)
 original_init=runner.NPUModelRunner.__init__
 @functools.wraps(original_init)
 def init(self,*args,**kwargs):
  original_init(self,*args,**kwargs)
  if self.vllm_config.speculative_config is not None or self.use_async_scheduling or not self.vllm_config.model_config.enforce_eager:raise RuntimeError('reviewed eager non-spec synchronousprovider only')
  mode=self.cache_config.mamba_cache_mode;pdc=bool(self.cache_config.enable_prefix_caching)
  if(mode,pdc)not in(('none',False),('align',True)):raise RuntimeError('actualcache reader lifecycle not qualified')
 H.install_copy_bridge(torch,L,mu);runner.NPUModelRunner.__init__=init;cls._forward_core=core;cls._qwen36_deltalog_fresh_version='1';cls._qwen36_deltalog_fresh_source_sha=sr['sha256']
 event('plugin_installed',gdn_sha256=C.GDN_SHA,mamba_sha256=C.MAMBA_SHA,model_runner_sha256=C.RUNNER_SHA,library_sha256=C.LIBRARY_SHA,namespace=C.NAMESPACE,source=sr,bridge=br)

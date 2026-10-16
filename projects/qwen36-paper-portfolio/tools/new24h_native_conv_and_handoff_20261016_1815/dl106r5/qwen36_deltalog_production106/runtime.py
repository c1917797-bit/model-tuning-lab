"""Default-OFF DL production SCREEN, sync/eager/noPDC, no final acceptance."""
import functools,json,os
from pathlib import Path
from . import admission as A,contract as C,primitives as L,runtime_helpers as H,binding as B
from .transform import clone_core
from . import layout_controls as LC,builder_mirror as M,integration as W,health
_STATE={};_INSTANCES={};_COUNTS={};_NATIVE={};_FLUSH={}
_OP=_ADMISSION=_SOURCE=_CORE=_LIB=_FRAMEWORK=_GDN=_TARGET=_NATIVE_CORE=None

def enabled():return os.environ.get('QWEN36_DELTALOG_PRODUCTION106_ENABLE')=='1'
def emit(*unused,**ignored):return None

def _route(torch,layer,*,query,key,value,g,beta,state,scale,actual_seq_lengths,ssm_state_indices,**extra):
 A.need(not extra and _OP is not None,'configured exact recurrent ABI')
 ctx=_GDN.get_forward_context();A.need(ctx.no_compile_layers.get(layer.prefix)is layer,'actual recurrent self')
 meta=ctx.attn_metadata[layer.prefix];A.need(meta.spec_sequence_masks is None and meta.num_decode_tokens==meta.num_decodes,'actual non-spec metadata')
 n=query.shape[0];ids=ssm_state_indices;B.indices(meta,ids,actual_seq_lengths,n)
 A.need(state is layer.kv_cache[1],'actual native state object');aux=H._bind(torch,L,layer)
 A.need(n==1 and n==meta.num_decodes and ids.numel()==n and actual_seq_lengths.numel()==n+1,'real decode shape/sequence')
 A.need(abs(float(scale)-128**-.5)<1e-12,'native scale')
 specs=((query,torch.bfloat16,[n,4,128]),(key,torch.bfloat16,[n,4,128]),(value,torch.bfloat16,[n,12,128]),(g,torch.float32,[n,12]),(beta,torch.bfloat16,[n,12]))
 A.need(all(x.device.type=='npu'and x.dtype==d and list(x.shape)==shape for x,d,shape in specs),'same B010 dtype/shape')
 A.need(ids.dtype==torch.int32 and actual_seq_lengths.dtype==torch.int32,'actual int32 metadata')
 M.read_receipt(W.runner_for(layer),layer,meta,state,ids,actual_seq_lengths,ctx,'decode')
 result=_OP(query.contiguous(),key.contiguous(),value.contiguous(),g.contiguous(),beta.contiguous(),state,aux['k_log'],aux['u_log'],aux['lambda_log'],aux['decay'],aux['length'],actual_seq_lengths.contiguous(),ids.contiguous())
 health.observe(torch,result);_COUNTS[layer.prefix]=_COUNTS.get(layer.prefix,0)+1
 return result

def guard_runner(r):
 A.need(r.vllm_config.speculative_config is None and not r.use_async_scheduling and r.vllm_config.model_config.enforce_eager,'screen sync/eager/nonspec only')
 A.need(r.cache_config.mamba_cache_mode=='none'and not r.cache_config.enable_prefix_caching,'none/PDCoff only')
def forbidden_copy(*unused,**ignored):raise RuntimeError('screen033 forbids native copy/PDC')

def worker_snapshot():
 import torch
 A.need(_SOURCE is not None and len(_INSTANCES)==48 and _CORE is not None,'actual48 bound instances')
 A.need(B.method_owner(_TARGET)[1]is _CORE and _GDN.AscendGatedDeltaNetAttention._forward_core is _NATIVE_CORE,'actual copied-Qwen target intact/native class preserved')
 rows={}
 for prefix,layer in _INSTANCES.items():
  A.need(B.method_owner(type(layer))[1]is _CORE,'actual instance override/MRO')
  meta=W.snapshot(layer);A.need(meta['last_forward_complete']and len(meta['registered_prefixes'])==48,'actual terminal forward all48 receipts')
  rows[prefix]=dict(self_id=id(layer),arena=LC.check_layout(layer.kv_cache[1]),core_id=id(_CORE),candidate=_COUNTS.get(prefix,0),native=_NATIVE.get(prefix,0),materialized_slots=_FLUSH.get(prefix,0),finished_steps=meta['finished_steps'])
 A.need(A.ref(_LIB['path'])==_LIB,'actual production library bytes')
 maps=[x for x in Path('/proc/self/maps').read_text().splitlines()if _LIB['path']in x];A.need(bool(maps),'actual mapped production library')
 return dict(mode='bounded-production',actual_common_precision=dict(matmul_allow_hf32=torch.npu.matmul.allow_hf32,conv_allow_hf32=torch.npu.conv.allow_hf32),source_ref=_SOURCE,qualification_ref=_ADMISSION['qualification_ref'],prefixes=rows,actual_core_id=id(_CORE),actual_target=_TARGET.__module__+'.'+_TARGET.__qualname__,framework_sources=_FRAMEWORK,library=_LIB,mapped_rows=maps,health=health.snapshot(torch,outside_timing=True),graph=False,async_scheduling=False,PDC=False,tensor_capture=False,native_peer=False)

def register():
 global _OP,_SOURCE,_ADMISSION,_CORE,_LIB,_FRAMEWORK,_GDN,_TARGET,_NATIVE_CORE
 if not enabled():return
 A.need(os.environ.get('QWEN36_DELTALOG_PRODUCTION106_MODE')=='production-bounded','explicit screen mode')
 A.need(all(not os.environ.get(k)for k in('MXR_CAPTURE_ENABLE','MXR_CAPTURE_SOURCE_REF','MXR_CAPTURE_ROOT','QWEN36_DELTALOG_TENSOR026_ENABLE','QWEN36_DELTALOG_TRACE025_ENABLE')),'no tensor/nativepeer/trajectory')
 A.need(all(os.environ.get(k)!='1'for k in('QWEN36_DELTALOG_ENABLE','QWEN36_DELTALOG_MIXED_ENABLE','QWEN36_DELTALOG_FRESH_ENABLE','QWEN36_DELTALOG_SERVICE003_ENABLE','QWEN36_DELTALOG_SERVICE023_ENABLE','QWEN36_DELTALOG_SCREEN033_ENABLE')),'no old aliases/providers')
 A.need(not any(k.startswith(('VLLM_PROFILER','VLLM_TORCH_PROFILER','TORCH_PROFILER'))for k in os.environ),'profiling OFF')
 sr=json.loads(os.environ['QWEN36_DELTALOG_PRODUCTION106_SOURCE_REF'])
 from qualification106 import qualify
 qref=json.loads(os.environ['QWEN36_DELTALOG_PRODUCTION106_QUALIFICATION_REF']);q=qualify(qref,sr)
 ad,m=A.consume(sr,qref)
 import torch
 from vllm_ascend.utils import enable_custom_op
 import vllm_ascend.ops.gdn as gdn
 from vllm.v1.worker import mamba_utils as mu
 from vllm_ascend.worker import model_runner_v1 as runner
 A.need(enable_custom_op()and getattr(runner,'mamba_utils',None)is mu,'actual native/custom modules')
 C.require_digest(runner.__file__,C.RUNNER_SHA);C.require_digest(mu.__file__,C.MAMBA_SHA)
 target,native,sources=B.resolve(gdn);lib=m['library_ref'];A.need(A.ref(lib['path'])==lib,'true B010 production DSO')
 torch.ops.load_library(lib['path']);op=getattr(torch.ops,C.NAMESPACE).decode
 A.need(str(op.default._schema)==m['operator_schema']and torch._C._dispatch_has_kernel_for_dispatch_key(C.NAMESPACE+'::decode','PrivateUse1'),'real registered schema')
 A.need(os.environ.get('QWEN36_DELTALOG_CPU_MIRROR018_REV2_ENABLE')=='1'and M.install()['installed'],'actual CPU metadata hooks')
 _OP=op;_SOURCE=sr;_ADMISSION=dict(ad,qualification_ref=qref);_LIB=lib;_FRAMEWORK=sources;_GDN=gdn;_TARGET=target;_NATIVE_CORE=native
 W.install(runner.NPUModelRunner,target,emit)
 specialized=clone_core(Path(gdn.__file__).read_text(),vars(gdn),functools.partial(_route,torch))
 def algorithm(self,mixed_qkv,b,a,core_attn_out):
  if M._DUMMY.get():
   _NATIVE[self.prefix]=_NATIVE.get(self.prefix,0)+1;return native(self,mixed_qkv,b,a,core_attn_out)
  metadata=gdn.get_forward_context().attn_metadata
  if metadata is None:
   r=W._RUNNERS.get(id(self));A.need(r is None or not any(r._deltalog018_state['owners'].values()),'no bypass with live state')
   _NATIVE[self.prefix]=_NATIVE.get(self.prefix,0)+1;return native(self,mixed_qkv,b,a,core_attn_out)
  meta=metadata[self.prefix];base=self.kv_cache[1];LC.check_layout(base)
  from common106 import request_geometry
  request_geometry(meta,W.runner_for(self)._deltalog018_state['current'])
  ids=meta.non_spec_state_indices_tensor[:meta.num_decodes];seq=None if not meta.num_decodes else meta.non_spec_decode_metadata.actual_seq_lengths
  cpu=M.read_receipt(W.runner_for(self),self,meta,base,ids,seq,gdn.get_forward_context(),'core')
  LC.metadata(list(cpu.decode),list(cpu.prefill),list(cpu.individual_decode_lengths),base.shape[0])
  result=H.execute_mixed_core(torch,L,gdn,specialized,native,self,mixed_qkv,b,a,core_attn_out,emit=None)
  _FLUSH[self.prefix]=_FLUSH.get(self.prefix,0)+len(cpu.prefill);return result
 def before(instance,owner,core):
  A.need(torch.npu.matmul.allow_hf32 is False and torch.npu.conv.allow_hf32 is False,'caller common precision must apply equally dense and candidate')
  A.need(instance.tp_size==4 and gdn.get_pcp_group().world_size==1,'actual TP4 PCP1')
  if instance.prefix not in _STATE:
   A.need(len(_STATE)<48,'actual48 GDN prefixes');_STATE[instance.prefix]=id(instance);_INSTANCES[instance.prefix]=instance
  A.need(_STATE[instance.prefix]==id(instance),'same real prefix instance')
 oldinit=runner.NPUModelRunner.__init__
 @functools.wraps(oldinit)
 def init(self,*args,**kw):oldinit(self,*args,**kw);guard_runner(self)
 mu.collect_mamba_copy_meta=forbidden_copy;mu.do_mamba_copy_block=forbidden_copy;runner.NPUModelRunner.__init__=init
 _CORE=B.install(target,native,algorithm,gdn.get_forward_context,before)
 A.need(gdn.AscendGatedDeltaNetAttention._forward_core is native,'native class unchanged')
 from .worker_receipt106 import install
 install(worker_snapshot)

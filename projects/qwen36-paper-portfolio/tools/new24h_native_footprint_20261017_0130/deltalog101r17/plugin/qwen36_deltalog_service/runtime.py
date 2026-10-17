"""B010 real-model diagnostic adapter: eager/noPDC only; default OFF."""
import functools,json,os,time
from pathlib import Path
from . import admission as A,contract as C,primitives as L,runtime_helpers as H,binding as B
from .transform import clone_core
from . import layout_controls as LC
from . import builder_mirror as M,integration as W
_STATE={};_COUNTS={};_SEEN=set();_OP=None;_ADMISSION=None;_SOURCE=None
def enabled():return os.environ.get('QWEN36_DELTALOG_SERVICE023_ENABLE')=='1'
def emit(name,**fields):
 from vllm.distributed import parallel_state as ps
 root=Path(os.environ['QWEN36_DELTALOG_SERVICE023_AUDIT']);A.need(root.is_dir(),'MAIN-created immutable audit root')
 rank=ps.get_tensor_model_parallel_rank();A.need(rank in(0,1,2,3),'actual initialized TP rank')
 if name=='graph_static_abi':name='kernel_abi';fields['consumer']=C.NAMESPACE+'::decode'
 key=(rank,name,fields.get('prefix'))
 if key in _SEEN:return
 first=not _SEEN;_SEEN.add(key);v=dict(schema='deltalog.actual-service-bridge-event/v023',source=_SOURCE,component=_ADMISSION,pid=os.getpid(),rank=rank,event=name,time_ns=time.time_ns(),performance=False,graph=False,**fields)
 with(root/('worker-%d.jsonl'%os.getpid())).open('x'if first else'a',encoding='utf8')as f:f.write(json.dumps(v,sort_keys=True,allow_nan=False)+'\n')
def _route(torch,layer,*,query,key,value,g,beta,state,scale,actual_seq_lengths,ssm_state_indices,**extra):
 A.need(not extra and _OP is not None,'configured exact recurrent ABI')
 ctx=__import__('vllm_ascend.ops.gdn',fromlist=['get_forward_context']).get_forward_context()
 A.need(ctx.no_compile_layers.get(layer.prefix)is layer,'actual recurrent self from framework context')
 meta=ctx.attn_metadata[layer.prefix];A.need(meta.spec_sequence_masks is None and meta.num_decode_tokens==meta.num_decodes,'actual non-spec metadata')
 n=query.shape[0];ids=ssm_state_indices
 B.indices(meta,ids,actual_seq_lengths,n)
 A.need(state is layer.kv_cache[1],'actual native state object binding')
 aux=H._bind(torch,L,layer)
 A.need(1<=n<=16 and n==meta.num_decodes and ids.numel()==n and actual_seq_lengths.numel()==n+1,'real decode shape/sequence')
 A.need(abs(float(scale)-128**-.5)<1e-12,'native scale')
 specs=((query,torch.bfloat16,[n,4,128]),(key,torch.bfloat16,[n,4,128]),(value,torch.bfloat16,[n,12,128]),(g,torch.float32,[n,12]),(beta,torch.bfloat16,[n,12]))
 A.need(all(x.device.type=='npu'and x.dtype==d and list(x.shape)==shape for x,d,shape in specs),'same B010 actual dtype/shape')
 A.need(ids.dtype==torch.int32 and actual_seq_lengths.dtype==torch.int32,'real int32 metadata')
 cpu=M.read_receipt(W.runner_for(layer),layer,meta,state,ids,actual_seq_lengths,ctx,'decode')
 if layer.prefix not in _COUNTS:
  iv=list(cpu.decode);seq=list(cpu.individual_decode_lengths)
  A.need(len(set(iv))==n and all(0<=i<state.shape[0]for i in iv),'real distinct live slots, no pad/duplicate')
  emit('actual_decode_binding',prefix=layer.prefix,self_id=id(layer),state_id=id(state),state_pointer=state.data_ptr(),indices_object_id=id(ids),state_indices=iv,actual_seq_lengths=seq,
   state_shape=list(state.shape),state_stride=list(state.stride()),state_contiguous=state.is_contiguous(),aux_pointers={k:aux[k].data_ptr()for k in C.AUX_NAMES})
 result=_OP(query.contiguous(),key.contiguous(),value.contiguous(),g.contiguous(),beta.contiguous(),state,aux['k_log'],aux['u_log'],aux['lambda_log'],aux['decay'],aux['length'],actual_seq_lengths.contiguous(),ids.contiguous())
 _COUNTS[layer.prefix]=_COUNTS.get(layer.prefix,0)+1
 emit('candidate_decode_executed',prefix=layer.prefix,layer_idx=layer.layer_idx,self_id=id(layer),state_pointer=state.data_ptr(),count=_COUNTS[layer.prefix],namespace=C.NAMESPACE)
 return result
def guard_runner(instance):
 A.need(instance.vllm_config.speculative_config is None and not instance.use_async_scheduling and instance.vllm_config.model_config.enforce_eager,'diagnostic eager/sync/nonspec only')
 A.need(instance.cache_config.mamba_cache_mode=='none'and not instance.cache_config.enable_prefix_caching,'none/PDCoff only; no factory copy claim')
def forbidden_copy(*a,**kw):raise RuntimeError('unexpected native mamba copy in explicitly none/PDCoff service; no DeltaLog copy qualification')
def register():
 global _OP,_SOURCE,_ADMISSION
 if not enabled():return
 A.need(os.environ.get('QWEN36_DELTALOG_SERVICE023_MODE')=='diagnostic-bridge-only','not a performance/accuracy qualification')
 A.need(all(os.environ.get(k)!='1'for k in('QWEN36_DELTALOG_ENABLE','QWEN36_DELTALOG_MIXED_ENABLE','QWEN36_DELTALOG_FRESH_ENABLE','QWEN36_DELTALOG_SERVICE003_ENABLE')),'no old DeltaLog aliases/providers')
 sr=json.loads(os.environ['QWEN36_DELTALOG_SERVICE023_SOURCE_REF'])
 ad,m=A.consume(sr,json.loads(os.environ['QWEN36_DELTALOG_SERVICE023_COMPOSITE_SOURCE_REF']))
 import torch
 for precision_group in('matmul','conv'):
  precision=getattr(torch.npu,precision_group);A.need(type(precision.allow_hf32)is bool,'actual common HF32 property')
  precision.allow_hf32=False;A.need(precision.allow_hf32 is False,'model smoke shares explicit PF071 HF32 OFF')
 from vllm_ascend.utils import enable_custom_op
 import vllm_ascend.ops.gdn as gdn
 from vllm.v1.worker import mamba_utils as mu
 from vllm_ascend.worker import model_runner_v1 as runner
 A.need(enable_custom_op()and getattr(runner,'mamba_utils',None)is mu,'actual native/customop/runner module identity')
 C.require_digest(runner.__file__,C.RUNNER_SHA);C.require_digest(mu.__file__,C.MAMBA_SHA)
 target,native,sources=B.resolve(gdn);lib=m['library_ref'];A.need(A.ref(lib['path'])==lib,'same true B010 DSO')
 torch.ops.load_library(lib['path']);op=getattr(torch.ops,C.NAMESPACE).decode
 A.need(str(op.default._schema)==m['operator_schema']and torch._C._dispatch_has_kernel_for_dispatch_key(C.NAMESPACE+'::decode','PrivateUse1'),'real namespace/schema/native registration')
 maps=[x for x in Path('/proc/self/maps').read_text().splitlines()if lib['path']in x];A.need(bool(maps),'actual mapped new library')
 A.need(os.environ.get('QWEN36_DELTALOG_CPU_MIRROR018_REV2_ENABLE')=='1','explicit source-bound CPU metadata optin required')
 installed=M.install();A.need(installed['installed'],'actual CPU metadata hooks installed')
 _OP=op;_SOURCE=sr;_ADMISSION=ad
 W.install(runner.NPUModelRunner,target,emit)
 specialized=clone_core(Path(gdn.__file__).read_text(),vars(gdn),functools.partial(_route,torch))
 def algorithm(self,mixed_qkv,b,a,core_attn_out):
  if M._DUMMY.get():return native(self,mixed_qkv,b,a,core_attn_out) # startup-only; live dummy already refused before native body
  metadata=gdn.get_forward_context().attn_metadata
  if metadata is None:
   r=W._RUNNERS.get(id(self));A.need(r is None or not any(r._deltalog018_state['owners'].values()),'metadataNone cannot bypass live deferred state')
   return native(self,mixed_qkv,b,a,core_attn_out)
  if metadata is not None:
   meta=metadata[self.prefix];base=self.kv_cache[1];LC.check_layout(base)
   ids=meta.non_spec_state_indices_tensor[:meta.num_decodes]
   seq=None if not meta.num_decodes else meta.non_spec_decode_metadata.actual_seq_lengths
   cpu=M.read_receipt(W.runner_for(self),self,meta,base,ids,seq,gdn.get_forward_context(),'core')
   LC.metadata(list(cpu.decode),list(cpu.prefill),list(cpu.individual_decode_lengths),base.shape[0])
  return H.execute_mixed_core(torch,L,gdn,specialized,native,self,mixed_qkv,b,a,core_attn_out,emit=emit)
 def before(instance,owner,core):
  A.need(torch.npu.matmul.allow_hf32 is False and torch.npu.conv.allow_hf32 is False,'actual unchanged model common HF32 policy')
  emit('actual_common_precision_policy',matmul_allow_hf32=False,conv_allow_hf32=False,phase='first-real-layer-before-core')
  A.need(instance.tp_size==4 and gdn.get_pcp_group().world_size==1,'actual TP4 PCP1')
  if instance.prefix not in _STATE:
   A.need(len(_STATE)<48,'exactly at most actual48 GDN prefixes per rank')
   _STATE[instance.prefix]=id(instance)
   emit('actual_qwen_core',prefix=instance.prefix,layer_idx=instance.layer_idx,self_id=id(instance),class_name=type(instance).__module__+'.'+type(instance).__qualname__,MRO=[c.__module__+'.'+c.__qualname__ for c in type(instance).__mro__],resolved_owner=owner.__module__+'.'+owner.__qualname__,core_id=id(core),native_id=id(native),target=target.__module__+'.'+target.__qualname__,framework_sources=sources,library=lib,mapped_rows=maps)
  A.need(_STATE[instance.prefix]==id(instance),'same real prefix/instance')
  if gdn.get_forward_context().attn_metadata is not None:
   base=instance.kv_cache[1];emit('actual_arena',prefix=instance.prefix,layer_idx=instance.layer_idx,shape=list(base.shape),stride=list(base.stride()),dtype=str(base.dtype),device=str(base.device),contiguous=base.is_contiguous(),base_pointer=base.data_ptr(),base_id=id(base),aux_bytes_if_allocated=base.shape[0]*52480)
 oldinit=runner.NPUModelRunner.__init__
 @functools.wraps(oldinit)
 def init(self,*a,**kw):oldinit(self,*a,**kw);guard_runner(self)
 # Real source-pinned runner uses the SAME module object. None mode source
 # bypasses align preprocessing; if that assumption drifts, fail closed.
 mu.collect_mamba_copy_meta=forbidden_copy;mu.do_mamba_copy_block=forbidden_copy
 runner.NPUModelRunner.__init__=init
 B.install(target,native,algorithm,gdn.get_forward_context,before)
 A.need(gdn.AscendGatedDeltaNetAttention._forward_core is native,'native Ascend class not mutated')

"""Actual copied-Qwen method ownership, stdlib only."""
import functools,hashlib,importlib,inspect
from pathlib import Path
PINS={'vllm_ascend.ops.gdn':'d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816','vllm_ascend.patch.worker.patch_qwen3_5':'21fc9a2064f9b490ffcf3d61bacc8ddb67806a4c7490895a33128e65438838d3','vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn':'885c56f5e3584ab60bb4ce4b42cf8259e5e92c86ba13aa6128e6ed7a2a20d2b0'}
def need(v,m):
 if not v:raise RuntimeError(m)
def method_owner(cls):
 for c in cls.__mro__:
  if '_forward_core'in c.__dict__:return c,c.__dict__['_forward_core']
 raise RuntimeError('missing real core')
def indices(meta,actual,sequence,n):
 # Native mixed path creates a fresh prefix VIEW; object identity would
 # wrongly reject it. Prove exact underlying native slice/address/stride.
 base=meta.non_spec_state_indices_tensor;expected=base[:n]
 need(base.numel()>=n and actual.shape==expected.shape and actual.dtype==expected.dtype and actual.device==expected.device and actual.stride()==expected.stride()and actual.data_ptr()==expected.data_ptr()and actual.storage_offset()==expected.storage_offset(),'actual native first-num_decodes state-index view binding')
 need(sequence is meta.non_spec_decode_metadata.actual_seq_lengths,'actual native decode metadata sequence object')
 return True
def resolve(gdn):
 mods={};sources={}
 for n,d in PINS.items():
  m=importlib.import_module(n);p=Path(inspect.getsourcefile(m)).resolve();b=p.read_bytes();need(hashlib.sha256(b).hexdigest()==d,'actual framework source '+n);mods[n]=m;sources[n]=dict(path=str(p),bytes=len(b),sha256=d)
 t=mods['vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn'].QwenGatedDeltaNetAttention
 need(mods['vllm_ascend.patch.worker.patch_qwen3_5']._GDN_PATCH_TARGET is t,'real Qwen alias identity')
 o,native=method_owner(t);need(native is gdn.AscendGatedDeltaNetAttention._forward_core and native.__qualname__=='AscendGatedDeltaNetAttention._forward_core','real target copied native; no previous plugin')
 need(inspect.unwrap(native)is native and inspect.getsourcefile(native)==str(Path(gdn.__file__).resolve()),'genuine unwrapped source-pinned native function body')
 return t,native,sources
def install(target,native,algorithm,get_context,before):
 @functools.wraps(native)
 def core(self,*args,**kw):
  resolved,method=method_owner(type(self))
  need(isinstance(self,target)and method is core,'real self method MRO/override identity')
  need(type(self.prefix)is str and bool(self.prefix),'actual instance prefix')
  ctx=get_context();need(ctx.no_compile_layers.get(self.prefix)is self,'actual static context layer is self')
  before(self,resolved,core)
  return algorithm(self,*args,**kw)
 need(method_owner(target)[1]is native,'native target unchanged before patch');target._forward_core=core
 return core

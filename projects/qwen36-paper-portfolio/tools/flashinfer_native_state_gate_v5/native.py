"""Actual old-FIA/native-update binding, lazy Torch only in MAIN device entry.
Public v0.23 source proves the API family, not this deployment's support.
"""
from pathlib import Path
import hashlib,importlib.metadata
from contract import D,H,N,CHUNK,PARTS,require,sha
REQUIRED={"query","key","value","atten_mask","num_heads","num_key_value_heads","input_layout","scale","sparse_mode","inner_precise","softmax_lse_flag"}
OPS=(("npu_fused_infer_attention_score","default"),("npu_fused_infer_attention_score","out"),
 ("_npu_fused_infer_attention_score_get_max_workspace","default"),("npu_attention_update","default"))
def required_schema(name,overload):
 needed={"lse","local_out","update_type"} if name=="npu_attention_update" else REQUIRED
 return needed|{"out","workspace"} if overload=="out" else needed
def check_schema(name,overload,schema):
 names={a.name for a in schema.arguments}
 require(names>=required_schema(name,overload),"actual required Tensor[] out ABI mismatch: "+name+"."+overload)
 returns=[str(a.type) for a in schema.returns]
 require(returns==(["Tensor"] if name.startswith("_npu_fused") else ["Tensor","Tensor"]),"actual native return ABI")
 if overload=="out":
  out=next(a for a in schema.arguments if a.name=="out")
  require(str(out.type) in ("List[Tensor]","Tensor[]"),"actual out must be Tensor[]; named output kwargs forbidden")
 return {"schema":str(schema),"sha256":hashlib.sha256(str(schema).encode()).hexdigest(),
   "arguments":[a.name for a in schema.arguments],"return_types":returns}
def inspect_schemas(torch):
 return {name+"."+overload:check_schema(name,overload,getattr(getattr(torch.ops.npu,name),overload)._schema)
   for name,overload in OPS}
def uninitialized(torch_npu):
 check=getattr(torch_npu.npu,"is_initialized",None)
 require(callable(check) and check() is False,"actual no-device initialized-state API must explicitly be false")
def verify_preinit(torch,torch_npu,receipt):
 uninitialized(torch_npu)
 exports=inspect_schemas(torch)
 require(exports==receipt["actual_exports"],"same-process actual exports differ from bound no-device receipt")
 for r in receipt["actual_runtime_sources"].values():
  require(sha(r["path"])==r["sha256"],"actual pre-init source changed")
 uninitialized(torch_npu)
 return exports
def resolve(torch,torch_npu,launch):
 exports=inspect_schemas(torch)
 require(importlib.metadata.version("vllm-ascend")==launch["stack"]["vllm_ascend"],"actual vllm-Ascend version")
 require(torch_npu.__version__==launch["stack"]["torch_npu"],"explicit actual torch_npu version")
 mapped={}
 for line in Path("/proc/self/maps").read_text().splitlines():
  fields=line.split()
  if len(fields)>=6 and fields[-1].startswith("/") and ".so" in fields[-1] and any(x in fields[-1].lower() for x in ("torch_npu","opapi","cust_op","vllm")):
   p=Path(fields[-1])
   if p.is_file():mapped[str(p)]=sha(p)
 for pair in launch["stack_source_refs"].values():
  r=pair["runtime_ref"];require(sha(r["path"])==r["sha256"],"actual deployed runtime source changed")
 pinned=launch["stack_source_refs"]["torch_npu_library"]["runtime_ref"]
 require(mapped.get(pinned["path"])==pinned["sha256"],"actual mapped torch_npu native library")
 return exports,mapped
class Guarded:
 def __init__(self,torch,shape,dtype,device,fill=7.):
  self.torch=torch;self.shape=tuple(shape);self.count=1
  for n in shape:self.count*=n
  self.backing=torch.full((self.count+128,),fill,dtype=dtype,device=device)
  self.value=self.backing[64:-64].view(shape);self.fill=fill
  self.identity=(self.backing.data_ptr(),self.value.data_ptr(),self.value.untyped_storage().nbytes(),tuple(self.value.stride()))
 def intact(self):
  return bool(self.torch.all(self.backing[:64]==self.fill).item() and self.torch.all(self.backing[-64:]==self.fill).item())
 def pointer(self):
  return self.identity==(self.backing.data_ptr(),self.value.data_ptr(),self.value.untyped_storage().nbytes(),tuple(self.value.stride()))
class NativeStates:
 def __init__(self,torch,batch,qwidth,device):
  self.t=torch;self.batch=batch;self.qwidth=qwidth;self.device=device
  self.q=Guarded(torch,(batch,H,qwidth,D),torch.bfloat16,device)
  self.k=Guarded(torch,(batch,1,N,D),torch.bfloat16,device)
  self.v=Guarded(torch,(batch,1,N,D),torch.bfloat16,device)
  self.mask=Guarded(torch,(batch,1,qwidth,N),torch.bool,device,True)
  self.out=Guarded(torch,(batch,H,qwidth,D),torch.bfloat16,device)
  self.lse=Guarded(torch,(batch,H,qwidth,1),torch.float32,device)
  self.final_out=Guarded(torch,(batch,H,qwidth,D),torch.bfloat16,device)
  self.final_lse=Guarded(torch,(batch,H,qwidth),torch.float32,device)
  self.parts=[]
  self._all=[self.q,self.k,self.v,self.mask,self.out,self.lse,self.final_out,self.final_lse]
  for i in range(PARTS):
   kp=Guarded(torch,(batch,1,CHUNK,D),torch.bfloat16,device)
   vp=Guarded(torch,(batch,1,CHUNK,D),torch.bfloat16,device)
   mp=Guarded(torch,(batch,1,qwidth,CHUNK),torch.bool,device,True)
   op=Guarded(torch,(batch,H,qwidth,D),torch.bfloat16,device)
   lp=Guarded(torch,(batch,H,qwidth,1),torch.float32,device)
   self.parts.append((kp,vp,mp,op,lp));self._all.extend((kp,vp,mp,op,lp))
  self.workspace=[];self.merge_raw_lse=None;self.got=None;self.got_lse=None;self.sanitized=None
 def kwargs(self,mask):
  return dict(atten_mask=mask,num_heads=H,num_key_value_heads=1,input_layout="BNSD",
     scale=1/16.,sparse_mode=0,inner_precise=0 if self.qwidth==1 else 2,softmax_lse_flag=True)
 def warm_workspace(self):
  op=self.t.ops.npu._npu_fused_infer_attention_score_get_max_workspace.default
  self.workspace=[op(self.q.value,self.k.value,self.v.value,**self.kwargs(self.mask.value))]
  for k,v,m,_,_ in self.parts:
   self.workspace.append(op(self.q.value,k.value,v.value,**self.kwargs(m.value)))
  require(all(x.device.type=="npu" for x in self.workspace),"actual native max-workspace device")
  self.workspace_identity=[(x.data_ptr(),x.untyped_storage().nbytes(),tuple(x.shape)) for x in self.workspace]
 def populate(self,query,keys,values,visible):
  t=self.t;self.q.value.copy_(query);self.k.value.copy_(keys);self.v.value.copy_(values)
  lens=t.tensor(visible,dtype=t.int32,device=self.device)
  positions=t.arange(N,device=self.device)
  self.mask.value.copy_((positions[None,None,None,:]>=lens[:,None,:,None]))
  for i,(k,v,m,_,_) in enumerate(self.parts):
   start=i*CHUNK;end=start+CHUNK
   k.value.copy_(self.k.value[:,:,start:end]);v.value.copy_(self.v.value[:,:,start:end])
   m.value.copy_(self.mask.value[:,:,:,start:end])
 def run(self):
  t=self.t;op=t.ops.npu.npu_fused_infer_attention_score.out
  op(self.q.value,self.k.value,self.v.value,**self.kwargs(self.mask.value),
    workspace=self.workspace[0],out=[self.out.value,self.lse.value])
  clean_outputs=[];clean_lse=[];present=[]
  for i,(k,v,m,out,lse) in enumerate(self.parts):
   op(self.q.value,k.value,v.value,**self.kwargs(m.value),workspace=self.workspace[i+1],
      out=[out.value,lse.value])
   valid=(~m.value).any(-1).expand(self.batch,H,self.qwidth)
   # Clear undefined values BEFORE multiplication/native aggregation. Merely
   # assigning zero weights cannot suppress NaN/Inf in an inactive output.
   y=t.where(valid[...,None],out.value.float(),t.zeros_like(out.value,dtype=t.float32))
   l=t.where(valid,lse.value[...,0],t.full_like(lse.value[...,0],float("-inf")))
   clean_outputs.append(y);clean_lse.append(l);present.append(valid)
  any_live=t.stack(present).any(0)
  dummy_out=t.zeros_like(clean_outputs[0]);dummy_lse=t.where(any_live,t.full_like(clean_lse[0],float("-inf")),t.zeros_like(clean_lse[0]))
  # Add a zero normalized dummy only for wholly empty rows, preventing
  # native all-(-inf) normalization without changing any nonempty domain.
  ys=[x.reshape(-1,D).contiguous() for x in [*clean_outputs,dummy_out]]
  ls=[x.reshape(-1).contiguous() for x in [*clean_lse,dummy_lse]]
  merged,raw_lse=t.ops.npu.npu_attention_update.default(ls,ys,0)
  require(tuple(merged.shape)==(self.batch*H*self.qwidth,D),"actual native update output ABI")
  merged=merged.view(self.batch,H,self.qwidth,D)
  self.final_out.value.copy_(t.where(any_live[...,None],merged,t.zeros_like(merged)).to(t.bfloat16))
  self.got=self.final_out.value
  lse=t.logsumexp(t.stack([*clean_lse,dummy_lse]),0)
  self.final_lse.value.copy_(t.where(any_live,lse,t.full_like(lse,float("-inf"))))
  self.got_lse=self.final_lse.value
  self.merge_raw_lse=raw_lse;self.sanitized=(clean_outputs,clean_lse,present)
  return self.got,self.got_lse
 def guards(self):return all(x.intact() for x in self._all)
 def pointers(self):
  return all(x.pointer() for x in self._all) and self.workspace_identity==[(x.data_ptr(),x.untyped_storage().nbytes(),tuple(x.shape)) for x in self.workspace]
 def bytes(self):
  return sum(x.backing.untyped_storage().nbytes() for x in self._all)+sum(x.untyped_storage().nbytes() for x in self.workspace)

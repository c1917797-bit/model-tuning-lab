"""Registered finite-precision Ascend ANN adaptation, NOT literal BF16 parity.
Selector and Q/K logits retain original BF16 arithmetic and exact tie contract.
FP32 GQA SUM has explicitly registered per-request fixed-capacity layout.
Alpha/final softmax/V-MV/mean compensation are FP32; one final BF16 output cast.
Native writer/leases/graph buffers and full FP64 thresholds are unchanged.
No Torch or NPU initialization at import.
"""
import importlib.util,math
from contract import BASE,BASE_CORE_SHA,PROTOCOL,read_ref,require
def substrate():
 path=BASE/"sparq_token_v4/core.py";read_ref({"path":str(path),"sha256":BASE_CORE_SHA})
 spec=importlib.util.spec_from_file_location("frozen_ann_native_substrate",str(path))
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
class ANNWorkspace:
 def __init__(self,device,batch,max_pages,budget=128,rank=32,local=1):
  import torch
  base=substrate();self.base=base
  require(type(batch) is int and batch in range(1,17) and max_pages==18 and budget==128 and rank==32 and local==1,
   "exact independent full matrix shape/rank/budget/local-current")
  self.batch=batch;self.max_pages=max_pages;self.capacity=max_pages*128
  self.rank=rank;self.budget=budget;self.local=local;self.scratch_pages=1;self._guards=[]
  def alloc(shape,dtype,fill=0):
   g=base.Guarded(torch,shape,dtype,device,fill=True if dtype==torch.bool else 7)
   self._guards.append(g);g.value.fill_(fill);return g.value
  self.rows=alloc((batch,max_pages),torch.int64)
  self.lengths=alloc((batch,),torch.int32)
  self.logical=alloc((self.capacity,),torch.int64);self.logical.copy_(torch.arange(self.capacity,dtype=torch.int64,device=device))
  self.logical_page=alloc((batch,self.capacity),torch.int64);self.logical_page.copy_((self.logical//128)[None,:].expand(batch,-1))
  self.offset=alloc((self.capacity,),torch.int64);self.offset.copy_(self.logical.remainder(128))
  self.batch_index=alloc((batch,),torch.int64);self.batch_index.copy_(torch.arange(batch,dtype=torch.int64,device=device))
  self.pa_table=alloc((batch,1),torch.int32);self.pa_table.copy_(torch.arange(batch,dtype=torch.int32,device=device)[:,None])
  self.budget_tensor=alloc((batch,),torch.int32,128)
  self.key=alloc((batch+1,128,1,256),torch.bfloat16)
  self.value=alloc((batch+1,128,1,256),torch.bfloat16)
  self.output=alloc((batch,6,256),torch.float32)
  self.corrected=alloc((batch,6,256),torch.bfloat16)
  self.importance=alloc((batch,256),torch.bfloat16)
  self.channels=alloc((batch,32),torch.int64)
  self.scale=alloc((batch,6),torch.bfloat16)
  self.score=alloc((batch,6,self.capacity),torch.float32)
  self.ranking=alloc((batch,self.capacity),torch.float32)
  self.rank_input=alloc((batch,6,self.capacity),torch.float32)
  self.selected=alloc((batch,128),torch.int64)
  self.valid=alloc((batch,self.capacity),torch.bool)
  self.selected_valid=alloc((batch,128),torch.bool)
  self.alpha=alloc((batch,6),torch.float32)
  self.weights=alloc((batch,6,128),torch.float32)
  self.bytes=sum(g.bytes() for g in self._guards)
 def guards(self):return all(g.intact() for g in self._guards)
 def tensors(self):
  import torch
  return {n:t for n,t in vars(self).items() if isinstance(t,torch.Tensor)}
 def run(self,query,kc,vc,mean,reallocation=False):
  import torch
  b=self.batch
  require(query.shape==(b,6,256) and query.dtype==kc.dtype==vc.dtype==torch.bfloat16 and
    kc.shape==vc.shape and kc.shape[1:]==(128,1,256) and mean.shape==(b,256) and mean.dtype==torch.float32,"original BF16 native geometry/lease mean")
  # Matches original SparseQ: original-dtype abs/sum; sorted topk with no stable-ID policy.
  self.importance.copy_(query.abs().sum(dim=1))
  self.channels.copy_(self.importance.topk(k=32,dim=-1).indices)
  physical=self.rows.gather(1,self.logical_page)
  short=kc[physical[:,:,None],self.offset[None,:,None],0,self.channels[:,None,:]]
  qshort=query.gather(2,self.channels[:,None,:].expand(-1,6,-1))
  scale=qshort.abs().sum(-1)
  scale.div_(query.abs().sum(-1));scale.mul_(256);scale.pow_(.5)
  self.scale.copy_(scale)
  raw_score=torch.bmm(qshort.div(scale[:,:,None]),short.transpose(1,2))
  self.valid.copy_(self.logical[None,:]<self.lengths[:,None])
  # Zero/+(-Inf) BF16 mask BEFORE float() matches original author score staging.
  mask=torch.zeros_like(raw_score).masked_fill(~self.valid[:,None,:],float("-inf"))
  self.score.copy_((raw_score+mask).float())
  recent=self.valid & (self.logical[None,:]>=self.lengths[:,None]-1)
  # Registered fixed-capacity layout port: [6,2304] SUM(0) per request.
  # Persistent input/output; static B loop, no host live-length read/capture.
  self.rank_input.copy_(self.score)
  self.rank_input.masked_fill_(recent[:,None,:],torch.finfo(torch.float32).max)
  for i in range(b):
   torch.sum(self.rank_input[i],dim=0,out=self.ranking[i])
  # +Inf from six forced Float32.max values is an intentional author rank sentinel.
  self.selected.copy_(self.ranking.topk(k=128,dim=-1).indices)
  self.selected_valid.copy_(self.selected<self.lengths[:,None])
  sp=physical.gather(1,self.selected);offset=self.selected.remainder(128)
  nk=kc[sp,offset,0,:].masked_fill(~self.selected_valid[:,:,None],0)
  nv=vc[sp,offset,0,:].masked_fill(~self.selected_valid[:,:,None],0)
  sk=self.key[:b].view(b,128,256);sv=self.value[:b].view(b,128,256)
  sk.copy_(nk);sv.copy_(nv) # Extra full page is untouched, never reused as valid.
  if reallocation:
   self.alpha.copy_(torch.softmax(self.score,-1).gather(2,self.selected[:,None,:].expand(-1,6,-1)).sum(-1))
  else:self.alpha.fill_(1)
  # Original BF16 Q predivide/dot/mask is UNCHANGED.
  # Registered adaptation: no intermediate BF16 alpha, weights, V-MV or
  # compensation rounding; exactly one final BF16 output cast.
  # This is not literal output equivalence; literal deviation is reported.
  exact_scores=torch.bmm(query.div(math.sqrt(256)),sk.transpose(1,2))
  exact_scores.add_(torch.zeros_like(exact_scores).masked_fill(~self.selected_valid[:,None,:],float("-inf")))
  weights=torch.softmax(exact_scores,-1,dtype=torch.float32)
  weights*=self.alpha[:,:,None];self.weights.copy_(weights)
  self.output.copy_(torch.bmm(weights,sv.float()))
  self.corrected.copy_((self.output+(1-self.alpha[:,:,None])*mean[:,None,:]).to(vc.dtype))
  return self.corrected,self.selected,self.alpha,self.channels

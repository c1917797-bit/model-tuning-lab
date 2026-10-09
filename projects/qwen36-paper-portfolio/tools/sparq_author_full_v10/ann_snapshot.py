"""All16 actual ANN layer snapshots, shared maxB backing per layer/all buckets.
Observer copies are diagnostic ONLY. Formal capture allocates no samples.
No global device init; all buffers are original guarded ND source substrate.
"""
import hashlib
from pathlib import Path
import source_contract as c
FIELDS=("q","output","key","value","selected","alpha","channels","score","ranking","importance")
class Pool:
 def __init__(self,core,t,npu,pages,device):
  self.t=t;self.npu=npu;self.pages=pages;self.guards={};self.views={};self.last_counter=None
  def alloc(name,shape,dtype):
   g=core.Guarded(t,shape,dtype,device);g.value.zero_();self.guards[name]=g;return g.value
  self.q=alloc("q",(16,6,256),t.bfloat16);self.output=alloc("output",(16,6,256),t.bfloat16)
  self.key=alloc("key",(17,128,1,256),t.bfloat16);self.value=alloc("value",(17,128,1,256),t.bfloat16)
  self.selected=alloc("selected",(16,128),t.int64);self.alpha=alloc("alpha",(16,6),t.float32)
  self.channels=alloc("channels",(16,32),t.int64);self.importance=alloc("importance",(16,256),t.bfloat16)
  self.score=alloc("score",(16,6,pages*128),t.float32);self.ranking=alloc("ranking",(16,pages*128),t.float32)
  self.epoch=alloc("epoch",(1,),t.int64);self.saved_epoch=alloc("saved_epoch",(1,),t.int64)
  self.counter=alloc("counter",(1,),t.int64);self.expected_epoch=None
  self.pointers={n:g.value.data_ptr() for n,g in self.guards.items()}
 def bytes(self):return sum(g.bytes() for g in self.guards.values())
 def intact(self):
  return all(g.intact() for g in self.guards.values()) and self.pointers=={n:g.value.data_ptr() for n,g in self.guards.items()}
 def view(self,batch):
  c.require(type(batch) is int and batch in range(1,17),"true batch view of guarded perFA maxB16 owner")
  if batch not in self.views:self.views[batch]=View(self,batch)
  return self.views[batch]
class View:
 def __init__(self,owner,batch):
  self.owner=owner;self.batch=batch;self.candidate=True
  for n in FIELDS:setattr(self,n,getattr(owner,n)[:batch] if n not in ("key","value") else getattr(owner,n))
 def bytes(self):return 0 # Entire owner is counted exactly once in State.budget.
 def prepare(self,epoch):
  c.require(type(epoch) is int and 0<epoch<2**63-1,"actual known current host epoch")
  p=self.owner;p.last_counter=int(p.counter.detach().cpu().item())
  p.epoch.fill_(epoch);p.expected_epoch=epoch
 def before(self,q):self.q.copy_(q)
 def after(self,out,ws,selected,alpha,channels):
  p=self.owner;b=self.batch
  self.output.copy_(out);p.key[:b].copy_(ws.key[:b]);p.value[:b].copy_(ws.value[:b])
  p.key[16:17].copy_(ws.key[16:17]);p.value[16:17].copy_(ws.value[16:17])
  self.selected.copy_(selected);self.alpha.copy_(alpha);self.channels.copy_(channels)
  self.score.copy_(ws.score);self.ranking.copy_(ws.ranking);self.importance.copy_(ws.importance)
  p.saved_epoch.copy_(p.epoch);p.counter.add_(1)
 def device_observation(self,epoch):
  p=self.owner
  c.require(p.intact() and p.expected_epoch==epoch,"all layer owner redzones/pointers/current epoch")
  saved=int(p.saved_epoch.detach().cpu().item());count=int(p.counter.detach().cpu().item())
  c.require(saved==epoch and count==p.last_counter+1,"actual original ACL copied this layer once; not Python forward counts")
  c.require(all(g.value.is_contiguous() and p.npu.get_npu_format(g.value)==2 for g in p.guards.values()),
   "original get_npu_format semantic ND2; enum return valid")
  return dict(epoch=saved,counter_increment=count-p.last_counter,device_counter=count,guards=True,pointers=p.pointers)

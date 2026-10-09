"""Diagnostic observation of the ORIGINAL ACL call; no substitute NPUGraph.
Added snapshot copies are explicitly an observation graph, never formal timing.
No torch import and no monkeypatch by import.
"""
import os,secrets,hashlib,json
from pathlib import Path
def need(ok,why):
 if not ok:raise ValueError(why)
def atomic_bytes(path,data):
 need(type(data) is bytes and len(data)<=4*1024**2,"bounded complete diagnostic binary")
 final=Path(path);tmp=final.with_name("."+final.name+".pending-"+secrets.token_hex(16))
 try:
  with tmp.open("xb") as out:
   need(out.write(data)==len(data),"full temporary binary write");out.flush();os.fsync(out.fileno())
  os.link(tmp,final,follow_symlinks=False)
  fd=os.open(str(final.parent),os.O_RDONLY|os.O_DIRECTORY)
  try:os.fsync(fd);tmp.unlink();os.fsync(fd)
  finally:os.close(fd)
 except BaseException:
  print("SPARQ_BINARY_PUBLISH_FAILED "+json.dumps(dict(final=str(final),retained_temporary=str(tmp))),flush=True);raise
 return dict(path=str(final),sha256=hashlib.sha256(data).hexdigest(),size_bytes=len(data))
class Snapshots:
 def __init__(self,core,torch,npu,batch,device,candidate):
  self.t=torch;self.npu=npu;self.batch=batch;self.candidate=candidate;self.guards={}
  def alloc(name,shape,dtype):
   g=core.Guarded(torch,shape,dtype,device);g.value.zero_();self.guards[name]=g;return g.value
  self.q=alloc("q",(batch,6,256),torch.bfloat16)
  self.output=alloc("output",(batch,6,256),torch.bfloat16)
  self.epoch=alloc("epoch",(1,),torch.int64);self.saved_epoch=alloc("saved_epoch",(1,),torch.int64)
  self.counter=alloc("counter",(1,),torch.int64);self.last_counter=None;self.expected_epoch=None
  if candidate:
   self.key=alloc("key",(batch+1,128,1,256),torch.bfloat16)
   self.value=alloc("value",(batch+1,128,1,256),torch.bfloat16)
   self.selected=alloc("selected",(batch,128),torch.int64)
   self.alpha=alloc("alpha",(batch,6),torch.float32)
   self.channels=alloc("channels",(batch,32),torch.int64)
  self.pointers={n:g.value.data_ptr() for n,g in self.guards.items()}
 def bytes(self):return sum(g.bytes() for g in self.guards.values())
 def prepare(self,epoch):
  need(type(epoch) is int and 0<epoch<2**63-1,"known current host epoch")
  if self.last_counter is None:self.last_counter=int(self.counter.detach().cpu().item())
  self.epoch.fill_(epoch);self.expected_epoch=epoch
 def before(self,q):
  self.q.copy_(q)
 def after(self,out,workspace=None,selected=None,alpha=None,channels=None):
  self.output.copy_(out)
  if self.candidate:
   need(workspace is not None,"actual candidate scratch owner")
   self.key.copy_(workspace.key);self.value.copy_(workspace.value)
   self.selected.copy_(selected);self.alpha.copy_(alpha);self.channels.copy_(channels)
  self.saved_epoch.copy_(self.epoch);self.counter.add_(1)
 def observe(self,directory,rank,prefix,batch,frame,arm):
  # Caller synchronizes only AFTER original model_forward and POST native update.
  need(self.batch==batch and self.expected_epoch is not None,"one real observed epoch")
  need(all(g.intact() for g in self.guards.values()),"snapshot redzones intact")
  need(self.pointers=={n:g.value.data_ptr() for n,g in self.guards.items()},"persistent snapshot pointers")
  epoch=int(self.saved_epoch.detach().cpu().item());count=int(self.counter.detach().cpu().item())
  need(epoch==self.expected_epoch,"current graph executed snapshot nodes; no stale capture values")
  if self.last_counter is not None:need(count==self.last_counter+1,"exact one replay per actual model turn")
  self.last_counter=count
  # Original get_npu_format==2 semantics; enum Format.ND is valid.
  need(all(g.value.is_contiguous() and self.npu.get_npu_format(g.value)==2 for g in self.guards.values()),"actual snapshot ND/contiguous")
  refs={}
  for name,g in self.guards.items():
   if name in ("epoch","saved_epoch","counter"):continue
   cpu=g.value.detach().cpu().contiguous()
   data=cpu.view(self.t.uint8).numpy().tobytes()
   filename="rank%d-epoch%d-%s-%s.bin"%(rank,epoch,prefix.replace(".","_"),name)
   ref=atomic_bytes(Path(directory)/filename,data)
   refs[name]=dict(ref,shape=list(cpu.shape),dtype=str(cpu.dtype),byte_order="little",native_format=2)
  return dict(arm=arm,prefix=prefix,batch=batch,epoch=epoch,device_counter=count,frame=frame,
   snapshot_refs=refs,guards=True,pointers=self.pointers,
   observation_graph=True,formal_graph=False,weak_ref_values_not_assumed=True,
   q_before_PA=True,output_after_PA=True,independent_numeric_verified=False,
   full64_layer_numeric_verified=False,model_ready=False)
def wrap_original_acl(acl,get_context,state_for_call):
 original=acl.ACLGraphWrapper.__call__
 need(original.__module__==acl.__name__,"actual original ACL wrapper, not prior patch")
 def observed(wrapper,*args,**kwargs):
  ctx=get_context();state=state_for_call()
  if state is None:return original(wrapper,*args,**kwargs)
  descriptor=ctx.batch_descriptor;entry=wrapper.concrete_aclgraph_entries.get(descriptor)
  is_replay=(ctx.cudagraph_runtime_mode==state.Mode.FULL and wrapper.runtime_mode==state.Mode.FULL and
   entry is not None and entry.aclgraph is not None)
  graph=entry.aclgraph if is_replay else None
  if is_replay:
   need(not ctx.capturing,"real existing stock FULL replay branch, not capture")
   addresses=[x.data_ptr() for x in args if isinstance(x,state.t.Tensor)]
   need(addresses==entry.input_addresses,"actual original captured ACL input addresses")
  got=original(wrapper,*args,**kwargs) # ONLY original sync/replay path.
  if is_replay:
   need(wrapper.concrete_aclgraph_entries[descriptor] is entry and entry.aclgraph is graph and got is entry.output,
    "same actual stock ACL entry/graph/output")
   state.replay_calls.append(dict(wrapper=id(wrapper),entry=id(entry),graph=id(graph),
    descriptor=dict(num_tokens=descriptor.num_tokens,uniform=descriptor.uniform),
    input_addresses=addresses,original_call_returned=True))
  return got
 observed.__wrapped__=original
 acl.ACLGraphWrapper.__call__=observed
 return original

def observe_native_gather(torch,ws,native,observation,directory):
 """Diagnostic-only read from actual original native cache, outside capture.
 Not a selector rerun or new attention operator. Entire valid scratch domain.
 """
 kc,vc,table=native;batch=observation["batch"];frame=observation["frame"]
 ids=observation["_actual_selected_tensor"].detach().cpu().tolist()
 tables=table.detach().cpu().tolist()
 # Read one token vector per selected native position; <one row per D2H.
 kb=bytearray(batch*128*256*2);vb=bytearray(len(kb));rows=[]
 for b in range(batch):
  n=frame[b]["native_length"];count=min(n,128);mapping=[]
  for j,token in enumerate(ids[b][:count]):
   need(type(token) is int and 0<=token<n and token//128<len(tables[b]),"actual selected native full-cache domain")
   block=tables[b][token//128];offset=token%128
   need(type(block) is int and 0<=block<kc.shape[0],"actual original native block allocation")
   for cache,dest in ((kc,kb),(vc,vb)):
    data=cache[block,offset].detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()
    need(len(data)==512,"entire local1KVhead/256dim/BF16 native token")
    dest[(b*128+j)*512:(b*128+j+1)*512]=data
   mapping.append(dict(token=token,block=block,offset=offset))
  rows.append(dict(rid=frame[b]["rid"],generation=frame[b]["generation"],mapping=mapping,
   full_native_length=n,block_table=list(tables[b])))
 stem="original-gather-r%d-e%d-%s"%(int(os.environ["QWEN36_SPARQ_ACTUAL_RANK"]),
  observation["epoch"],observation["prefix"].replace(".","_"))
 return dict(key=atomic_bytes(Path(directory)/(stem+"-key.bin"),bytes(kb)),
  value=atomic_bytes(Path(directory)/(stem+"-value.bin"),bytes(vb)),rows=rows,
  native_identities=[dict(pointer=t.data_ptr(),storage_pointer=t.untyped_storage().data_ptr(),
   shape=list(t.shape),stride=list(t.stride()),dtype=str(t.dtype),device=str(t.device)) for t in (kc,vc,table)],
  actual_original_cache_not_selected_scratch=True,capture=False)

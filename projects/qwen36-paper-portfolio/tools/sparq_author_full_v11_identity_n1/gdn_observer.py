"""Actual native GDN allocator observer. OFF unless instantiated by admitted bridge.
No state math/call replacement. Complete inactive logical rows before/after the
unchanged original model. Diagnostic-only D2H outside GLOBAL capture.
"""
import hashlib,os,re,secrets
from pathlib import Path
import evidence as c
import gdn_metadata,gdn_state
def identity(t,npu):
 fmt=npu.get_npu_format(t)
 return dict(shape=list(t.shape),stride=list(t.stride()),dtype=str(t.dtype),device=str(t.device),
  pointer=t.data_ptr(),storage_pointer=t.untyped_storage().data_ptr(),storage_offset=t.storage_offset(),
  storage_bytes=t.untyped_storage().nbytes(),native_format_value=int(fmt),
  native_format_type=type(fmt).__module__+"."+type(fmt).__qualname__)
class Observer:
 def __init__(self,runner,torch,npu,pins,runtime_modules):
  self.runner=runner;self.t=torch;self.npu=npu;self.pins=pins;self.modules=runtime_modules;self.pending=None
  self.epochs=0;self.root=None;self.content_bytes=0;self.domain_bytes=0
 def validate_original(self,obj):
  ascend=self.modules["gdn"]
  c.require(obj.forward.__func__ is ascend.AscendGatedDeltaNetAttention.forward and
   obj._forward_core.__func__ is ascend.AscendGatedDeltaNetAttention._forward_core,
   "actual patch donor and receiver identity retained exactly")
  c.require(len(obj.kv_cache)==2,"actual native conv/recurrent allocation tuple")
 def blob(self,t):
  # One row at a time bounds ordinary RAM; padded outer page stride is not
  # serialized as a fictitious contiguous whole-state tensor.
  raw=t.detach().cpu().contiguous().view(self.t.uint8).numpy().tobytes()
  self.domain_bytes+=len(raw);digest=hashlib.sha256(raw).hexdigest();path=self.root/"state-blobs"/(digest+".bin")
  if path.exists():
   c.require(path.is_file() and not path.is_symlink() and path.stat().st_size==len(raw) and c.sha(path)==digest,
    "immutable dedup blob actual bytes, no overwritten evidence")
  else:
   c.require(self.content_bytes+len(raw)<=8*1024**3,"complete diagnostic state output bound; stop, never sample")
   tmp=path.with_name("."+path.name+".pending-"+secrets.token_hex(16))
   try:
    with tmp.open("xb") as f:
     c.require(f.write(raw)==len(raw),"complete actual state bytes");f.flush();os.fsync(f.fileno())
    os.link(tmp,path,follow_symlinks=False)
    fd=os.open(str(path.parent),os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd);tmp.unlink();os.fsync(fd)
    finally:os.close(fd)
   except BaseException:
    print("GDN_BLOB_PRIMARY_FAILURE "+str(tmp),flush=True);raise
   self.content_bytes+=len(raw)
  return dict(path=str(path),sha256=digest,size_bytes=len(raw))
 def begin(self,ctx,root,rank,epoch,request_ids):
  c.require(self.pending is None and not ctx.capturing,"snapshot outside real GLOBAL capture before unchanged original model")
  self.root=Path(root);c.require(self.root.is_absolute() and Path("/cache/cch") in self.root.parents,"owned trace root")
  (self.root/"state-blobs").mkdir(exist_ok=True);layers={};seen=set()
  for prefix,meta in ctx.attn_metadata.items():
   match=re.search(r"(?:^|\.)layers\.([0-9]+)(?:\.|$)",prefix)
   if not match or int(match.group(1)) not in gdn_state.GDN:continue
   layer=int(match.group(1));c.require(layer not in seen,"one actual GDN prefix per layer");seen.add(layer)
   obj=ctx.no_compile_layers[prefix];self.validate_original(obj)
   raw=gdn_metadata.observe(meta,self.runner)
   raw.update(prefix=prefix,epoch=epoch,rank=rank,device_snapshot_copied_outside_GLOBAL_capture=True,
    request_ids=list(request_ids),metadata_class=type(meta).__module__+"."+type(meta).__qualname__)
   states=list(obj.kv_cache);domain=gdn_metadata.plan(raw,states[0].shape[0],states[1].shape[0])
   c.require(len(request_ids)<=len(domain["query_lengths"]) and len(request_ids)==sum(n>0 for n in domain["query_lengths"]),
    "all real requests matched actual positive metadata segments, padded rows not requests")
   rawref=c.write(self.root/("gdn-meta-r%d-e%d-l%d.json"%(rank,epoch,layer)),raw)
   records=[]
   for name,t in zip(("conv","recurrent"),states):
    ident=identity(t,self.npu);gdn_state.identity(ident)
    inactive=set(range(t.shape[0]))-set(domain["written_slots"][name])
    records.append(dict(name=name,state_slot_axis=0,identity_before=ident,
     untouched_slots=[dict(slot=i,before=self.blob(t[i])) for i in sorted(inactive)]))
   layers[prefix]=dict(obj=obj,states=states,event=dict(layer=layer,prefix=prefix,rank=rank,epoch=epoch,
    actual_metadata_before=rawref,deployed_state_sources=self.pins,original_forward_unchanged=True,
    original_forward_core_unchanged=True,states=records))
  c.require(seen==set(gdn_state.GDN),"all48 actual GDN layers, not FA-only graph instrumentation")
  self.pending=layers
 def end(self,ctx):
  c.require(self.pending is not None and not ctx.capturing,"snapshot after actual unchanged model and PA POSTupdate")
  self.t.npu.current_stream().synchronize();events=[]
  for prefix,row in self.pending.items():
   obj=row["obj"];self.validate_original(obj);event=row["event"]
   for record,t in zip(event["states"],obj.kv_cache):
    record["identity_after"]=identity(t,self.npu)
    c.require(record["identity_after"]==record["identity_before"],"same actual native GDN backing pointers/stride")
    for item in record["untouched_slots"]:item["after"]=self.blob(t[item["slot"]])
   # This producer check is not the independent complete model consumer.
   check=gdn_state.consume(event,self.pins)
   event["producer_check"]=check
   events.append(event)
  self.pending=None;self.epochs+=1;return events

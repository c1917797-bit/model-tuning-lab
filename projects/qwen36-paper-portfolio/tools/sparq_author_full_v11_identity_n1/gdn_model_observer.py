"""Opt-in actual GDN full-row streaming observer. No state math replacement.
Original complete before bytes remain CPU-resident until unchanged model ends.
Independent checker receives every original after row, active and inactive.
Success dumps are NOT retained; first offending row is permanently retained.
Capture/profile is never admitted by this diagnostic observer.
"""
import hashlib,os,re,secrets,time
from pathlib import Path
import evidence as c,gdn_metadata,gdn_state,gdn_stream
def identity(t,npu):
 fmt=npu.get_npu_format(t)
 return dict(shape=list(t.shape),stride=list(t.stride()),dtype=str(t.dtype),device=str(t.device),
  pointer=t.data_ptr(),storage_pointer=t.untyped_storage().data_ptr(),storage_offset=t.storage_offset(),
  storage_bytes=t.untyped_storage().nbytes(),native_format_value=int(fmt),
  native_format_type=type(fmt).__module__+"."+type(fmt).__qualname__)
def memory():
 snapshot=gdn_stream.memory() # Default64; host still proves complete ancestors.
 root=Path(os.environ["QWEN36_SPARQ_MODEL_SERVICE_ROOT"])
 arm=c.obj(c.bound(root/"ARM.json",c.sha(root/"ARM.json")));ident=c.obj(arm["identity"])
 gdn_stream.consume_memory(snapshot,gdn_stream.GUEST,ident["container_id"])
 proof=root/"identity"/("memory-startup-%d.json"%os.getpid())
 return gdn_stream.memory_sample(snapshot,c.bound(proof,c.sha(proof)))
def raw_publish(path,data):
 path=Path(path);view=gdn_stream.view(data)
 c.require(path.is_absolute() and path.parent.resolve()==path.parent and not path.exists(),"exact new first-fault binary")
 temporary=path.with_name("."+path.name+".pending-"+secrets.token_hex(16))
 try:
  with temporary.open("xb") as f:
   c.require(f.write(view)==len(view),"complete original first-fault row bytes");f.flush();os.fsync(f.fileno())
  os.link(temporary,path,follow_symlinks=False)
  fd=os.open(str(path.parent),os.O_RDONLY|os.O_DIRECTORY)
  try:os.fsync(fd);temporary.unlink();os.fsync(fd)
  finally:os.close(fd)
 except BaseException:
  print("GDN_STREAM_RAW_PRIMARY "+str(temporary),flush=True);raise
 return dict(path=str(path),sha256=c.sha(path),size_bytes=len(view))
class Observer:
 def __init__(self,runner,torch,npu,pins,runtime_modules):
  self.runner=runner;self.t=torch;self.npu=npu;self.pins=pins;self.modules=runtime_modules;self.pending=None
  self.epochs=0;self.first_fault=None
  import source_contract as full
  self.source,self.files=full.source(os.environ["QWEN36_SPARQ_STOCK_FULL_SOURCE"],os.environ["QWEN36_SPARQ_STOCK_FULL_SOURCE_SHA"])
  self.checker=c.bound(Path(__file__).with_name("gdn_stream.py"),self.files["gdn_stream.py"])
  import numpy
  self.np=numpy
  self.numpy=dict(version=numpy.__version__,file=c.bound(Path(numpy.__file__).resolve(),c.sha(Path(numpy.__file__).resolve())))
 def validate_original(self,obj):
  ascend=self.modules["gdn"]
  c.require(obj.forward.__func__ is ascend.AscendGatedDeltaNetAttention.forward and
   obj._forward_core.__func__ is ascend.AscendGatedDeltaNetAttention._forward_core,
   "actual patch donor and receiver identity retained exactly")
  c.require(len(obj.kv_cache)==2,"actual native conv/recurrent allocation tuple")
 def cpu(self,t):
  # No bytes()/tobytes() duplicate of complete before storage. NumPy buffer is
  # a zero-copy alias of this independently allocated CPU logical-row tensor.
  x=t.detach().cpu().contiguous()
  c.require(x.device.type=="cpu" and x.is_contiguous(),"whole actual CPU state logical row")
  array=x.view(self.t.uint8).numpy()
  return x,gdn_stream.view(array)
 def space(self):
  x=memory();c.require(x["memory_current"]+gdn_stream.RESERVE<=gdn_stream.GUEST,
   "actual model cgroup ordinary headroom retained; no HugeTLB additive fiction")
  return x
 def joint(self,records,rank,epoch):
  row=dict(schema=gdn_stream.BUDGET,rank=rank,epoch=epoch,source=self.source,states=records,
   cgroup=memory(),max_model_len=self.runner.vllm_config.model_config.max_model_len,
   original_cpu_before_allocated=False,checker=self.checker,numpy=self.numpy)
  c.write(self.root/("GDN-PLAN-e%d-r%d.json"%(epoch,rank)),row)
  end=time.monotonic()+30;paths=[self.root/("GDN-PLAN-e%d-r%d.json"%(epoch,r)) for r in range(4)]
  while not all(p.exists() for p in paths):
   c.require(time.monotonic()<end,"bounded all4 real-shape preallocation rendezvous")
   time.sleep(.01)
  original=[c.obj(c.bound(p,c.sha(p))) for p in paths]
  c.require(all(r["checker"]==self.checker and r["numpy"]==self.numpy and r["original_cpu_before_allocated"] is False for r in original),
   "same actual independent checker/NumPy dependency; all rank plans before CPU before allocation")
  # All ranks share this one guest cgroup; every simultaneous rank reservation
  # is included. No rank may independently reserve the whole64GiB limit.
  proof=gdn_stream.plan(original,memory()["memory_current"],epoch,self.source,self.runner.vllm_config.model_config.max_model_len)
  final=self.root/("GDN-JOINT-e%d.json"%epoch)
  if rank==0:c.write(final,proof)
  while not final.exists():
   c.require(time.monotonic()<end,"bounded actual joint allocation publication");time.sleep(.01)
  ref=c.bound(final,c.sha(final));actual=c.obj(ref);gdn_stream.consume_budget(actual)
  c.require(actual["records"]==original,"same exact actual all4 preallocation plans")
  # Baseline can increase slightly while another rank loads the published JSON;
  # the explicit reserve covers it. Do not demand stale equal baseline samples.
  self.space();return ref,actual
 def first(self,event,state,slot,before,after,error):
  if self.first_fault is not None:return
  # Save raw before/after for the FIRST actually observed row exception only.
  # Unavailable after (e.g. device copy failed) is explicit, never synthesized.
  root=self.root/("GDN-FIRST-e%d-r%d-l%d-%s-s%d"%(event["epoch"],event["rank"],event["layer"],state["name"],slot))
  before_ref=raw_publish(root.with_suffix(".before.bin"),before)
  after_ref=None if after is None else raw_publish(root.with_suffix(".after.bin"),after)
  result=dict(schema="sparq.GDN-first-original-row-fault/v2",original_exception=repr(error),
   event={k:event[k] for k in ("layer","prefix","rank","epoch","actual_metadata_before")},
   state_name=state["name"],slot=slot,identity_before=state["identity_before"],
   before=before_ref,after=after_ref,after_unavailable=after is None,
   independent_checker=self.checker,joint_budget=self.budget_ref,ready=False)
  self.first_fault=c.write(root.with_suffix(".json"),result)
 def begin(self,ctx,root,rank,epoch,request_ids):
  c.require(self.pending is None and not ctx.capturing,"before unchanged original model, outside GLOBAL capture")
  self.root=Path(root);c.require(self.root.is_absolute() and self.root.resolve()==self.root and
   Path("/cache/cch") in self.root.parents and not self.root.is_symlink(),"owned exact trace root")
  layers={};seen=set();plans=[]
  for prefix,meta in ctx.attn_metadata.items():
   match=re.search(r"(?:^|\.)layers\.([0-9]+)(?:\.|$)",prefix)
   if not match or int(match.group(1)) not in gdn_state.GDN:continue
   layer=int(match.group(1));c.require(layer not in seen,"one actual GDN prefix per layer");seen.add(layer)
   obj=ctx.no_compile_layers[prefix];self.validate_original(obj)
   raw=gdn_metadata.observe(meta,self.runner)
   raw.update(prefix=prefix,epoch=epoch,rank=rank,device_snapshot_copied_outside_GLOBAL_capture=True,
    request_ids=list(request_ids),metadata_class=type(meta).__module__+"."+type(meta).__qualname__)
   states=list(obj.kv_cache);domain=gdn_metadata.plan(raw,states[0].shape[0],states[1].shape[0])
   c.require(len(request_ids)==sum(n>0 for n in domain["query_lengths"]),
    "all actual positive requests, zero-length padded rows remain inactive")
   records=[]
   for name,t in zip(("conv","recurrent"),states):
    ident=identity(t,self.npu);gdn_state.identity(ident)
    plans.append(dict(layer=layer,prefix=prefix,name=name,identity=ident))
    records.append(dict(name=name,state_slot_axis=0,identity_before=ident))
   rawref=c.write(self.root/("gdn-meta-r%d-e%d-l%d.json"%(rank,epoch,layer)),raw)
   layers[prefix]=dict(obj=obj,states=states,domain=domain,event=dict(schema=gdn_stream.PROTOCOL,layer=layer,prefix=prefix,rank=rank,epoch=epoch,
    actual_metadata_before=rawref,deployed_state_sources=self.pins,original_forward_unchanged=True,
    original_forward_core_unchanged=True,independent_checker=self.checker,states=records))
  c.require(seen==set(gdn_state.GDN),"all48 actual native GDN initialized layers")
  self.budget_ref,proof=self.joint(plans,rank,epoch)
  for row in layers.values():
   row["before"]=[]
   for record,t in zip(row["event"]["states"],row["states"]):
    copies=[]
    for slot in range(t.shape[0]):
     self.space();cpu,view=self.cpu(t[slot]);copies.append(cpu)
     c.require(len(view)==gdn_state.identity(record["identity_before"]),"complete original logical row saved CPU")
    row["before"].append(copies)
   row["event"]["joint_budget"]=self.budget_ref
  self.pending=layers
 def end(self,ctx):
  c.require(self.pending is not None and not ctx.capturing,"after unchanged model and actual POSTupdate outside capture")
  self.t.npu.current_stream().synchronize();events=[]
  for prefix,row in self.pending.items():
   obj=row["obj"];self.validate_original(obj);event=row["event"]
   for index,(record,t) in enumerate(zip(event["states"],obj.kv_cache)):
    record["identity_after"]=identity(t,self.npu)
    c.require(record["identity_after"]==record["identity_before"],"same whole native GDN allocation before/after")
    writer=row["domain"]["written_slots"][record["name"]]
    checker=gdn_stream.Checker(record["identity_before"],writer,self.np)
    for slot,old_cpu in enumerate(row["before"][index]):
     before=gdn_stream.view(old_cpu.view(self.t.uint8).numpy());after=None
     try:
      self.space();after_cpu,after=self.cpu(t[slot])
      checker.row(slot,before,after)
      # Actual row transient is discarded before next D2H; before storage remains.
      del after_cpu
     except BaseException as error:
      try:self.first(event,record,slot,before,after,error)
      except BaseException as secondary:print("GDN_ORIGINAL_FIRST_ERROR "+repr(error)+"; raw secondary="+repr(secondary),flush=True)
      raise
    record.update(live_check=checker.finish(),original_before_CPU_saved=True,
     after_all_rows_streamed_once=True,all_after_rows_finite=True,active_state_dense_equivalence_not_asserted=True)
    record["active_slots"]=[dict(slot=i,bitwise_changed=i in checker.active_changed,after_finite=True) for i in writer]
   # Independent implementation sees original bytes, not producer booleans.
   check=gdn_state.consume(event,self.pins,self.checker,self.source);event["producer_check"]=check
   events.append(event)
  self.pending=None;self.epochs+=1;return events
 def abort(self,error):
  # Original model/identity/sync exceptions do not identify a bad state row.
  # Retain real original before of first available row and explicitly mark
  # after unavailable; never fabricate a causal after or mask primary error.
  if self.pending is None or self.first_fault is not None:return
  row=next(iter(self.pending.values()));state=row["event"]["states"][0]
  old_cpu=row["before"][0][0];before=gdn_stream.view(old_cpu.view(self.t.uint8).numpy())
  self.first(row["event"],state,0,before,None,error)

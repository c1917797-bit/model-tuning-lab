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
  self.epochs=0;self.first_fault=None;self.ledger_ref=None;self.physical_context=gdn_state.PhysicalContext()
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

 def joint(self,records,fa,rank,epoch):
  row=dict(schema=gdn_stream.PHYSICAL_BUDGET,rank=rank,epoch=epoch,source=self.source,states=records,fa=fa,
   cgroup=memory(),max_model_len=self.runner.vllm_config.model_config.max_model_len,
   original_cpu_before_allocated=False,checker=self.checker,numpy=self.numpy)
  c.write(self.root/("GDN-PLAN-e%d-r%d.json"%(epoch,rank)),row)
  end=time.monotonic()+30;paths=[self.root/("GDN-PLAN-e%d-r%d.json"%(epoch,r)) for r in range(4)]
  def wait(paths,why):
   while not all(p.exists() for p in paths):
    c.require(time.monotonic()<end,why);time.sleep(.01)
  wait(paths,"bounded all4 source-bound physical preallocation plans")
  original=[c.obj(c.bound(p,c.sha(p))) for p in paths]
  c.require(all(r["checker"]==self.checker and r["numpy"]==self.numpy and r["original_cpu_before_allocated"] is False for r in original),
   "same actual independent checker and NumPy, before any physical copy")
  fresh=self.root/("GDN-BASELINE-e%d-r%d.json"%(epoch,rank))
  c.write(fresh,memory())
  baselines=[self.root/("GDN-BASELINE-e%d-r%d.json"%(epoch,r)) for r in range(4)]
  wait(baselines,"bounded all4 FRESH original memory baseline refs")
  refs=[c.bound(p,c.sha(p)) for p in baselines]
  proof=gdn_stream.physical_budget(original,refs,epoch,self.source,self.runner.vllm_config.model_config.max_model_len)
  # Persist every actual term and original fresh Ref BEFORE any budget reject.
  final=self.root/("GDN-JOINT-e%d.json"%epoch)
  if rank==0:c.write(final,proof)
  wait([final],"bounded complete actual budget publication BEFORE reject")
  ref=c.bound(final,c.sha(final));actual=c.obj(ref)
  c.require(actual==proof,"same original all4 budget detail and fresh refs")
  c.require(actual["budget_fits"],"same64GiB physical before+chunk+oracle+reserve; actual detail persisted")
  gdn_stream.consume_physical_budget(actual);self.space()
  return ref,actual
 def first_pool(self,pool,offset,before,after,error):
  if self.first_fault is not None:return
  root=self.root/("GDN-FIRST-POOL-e%d-r%d-o%s-b%d"%(self.epoch,self.rank,pool["before_owner"],offset))
  before_ref=raw_publish(root.with_suffix(".before.bin"),before)
  after_ref=None if after is None else raw_publish(root.with_suffix(".after.bin"),after)
  self.first_fault=c.write(root.with_suffix(".json"),dict(schema="sparq.GDN-first-physical-byte-fault/v1",
   source=self.source,rank=self.rank,epoch=self.epoch,original_exception=repr(error),
   pool_identity=pool["identity"],pool_members=pool["members"],chunk_offset=offset,
   before=before_ref,after=after_ref,after_unavailable=after is None,
   independent_checker=self.checker,joint_budget=self.budget_ref,ready=False))
 def slab(self,t):
  x=identity(t,self.npu);info=gdn_stream.physical_identity(x)
  result=t.as_strided((x["storage_bytes"]//info["width"],),(1,),storage_offset=0)
  c.require(result.data_ptr()==x["storage_pointer"] and result.untyped_storage().nbytes()==x["storage_bytes"] and
   result.storage_offset()==0 and result.is_contiguous(),"exact original WHOLE slab ND view including all padding")
  return result
 def begin(self,ctx,root,rank,epoch,request_ids,native_caches,native_impls,backend):
  c.require(self.pending is None and not ctx.capturing,"before unchanged original model, outside GLOBAL capture")
  self.root=Path(root);self.rank=rank;self.epoch=epoch
  c.require(self.root.is_absolute() and self.root.resolve()==self.root and Path("/cache/cch") in self.root.parents and
   not self.root.is_symlink(),"owned exact trace root")
  layers={};seen=set();plans=[];tensors={};fa=[]
  for prefix,meta in ctx.attn_metadata.items():
   match=re.search(r"(?:^|\.)layers\.([0-9]+)(?:\.|$)",prefix)
   if not match or int(match.group(1)) not in gdn_state.GDN:continue
   layer=int(match.group(1));c.require(layer not in seen,"one actual GDN prefix per layer");seen.add(layer)
   obj=ctx.no_compile_layers[prefix];self.validate_original(obj);raw=gdn_metadata.observe(meta,self.runner)
   raw.update(prefix=prefix,epoch=epoch,rank=rank,device_snapshot_copied_outside_GLOBAL_capture=True,
    request_ids=list(request_ids),metadata_class=type(meta).__module__+"."+type(meta).__qualname__)
   states=list(obj.kv_cache);domain=gdn_metadata.plan(raw,states[0].shape[0],states[1].shape[0])
   c.require(len(request_ids)==sum(n>0 for n in domain["query_lengths"]),
    "all actual positive requests, zero-length native padding remains protected")
   rawref=c.write(self.root/("gdn-meta-r%d-e%d-l%d.json"%(rank,epoch,layer)),raw);records=[]
   for name,t in zip(("conv","recurrent"),states):
    ident=identity(t,self.npu);gdn_state.identity(ident);gdn_stream.physical_identity(ident)
    plans.append(dict(layer=layer,prefix=prefix,name=name,rank=rank,epoch=epoch,identity=ident,metadata=rawref))
    records.append(dict(name=name,state_slot_axis=0,identity_before=ident))
    tensors[gdn_stream.slab_key(ident)]=t
   layers[prefix]=dict(obj=obj,event=dict(schema=gdn_stream.PHYSICAL_PROTOCOL,layer=layer,prefix=prefix,rank=rank,epoch=epoch,
    actual_metadata_before=rawref,deployed_state_sources=self.pins,original_forward_unchanged=True,
    original_forward_core_unchanged=True,independent_checker=self.checker,states=records))
  c.require(seen==set(gdn_state.GDN),"all48 actual original GDN layers retained")
  for prefix,meta in ctx.attn_metadata.items():
   match=re.search(r"(?:^|\.)layers\.([0-9]+)(?:\.|$)",prefix)
   if not match or int(match.group(1)) not in range(3,64,4):continue
   layer=int(match.group(1));known=[v for k,v in native_caches.items() if (k[0] if type(k) is tuple else k)==prefix]
   c.require(known and len({tuple(gdn_stream.exact_view_key(identity(t,self.npu)) for t in v[:2]) for v in known})==1,
    "all captured B native K/V backing is the same exact initialized view")
   key,value=known[0][:2];n=meta.num_actual_tokens;impl=native_impls[prefix]
   c.bound(Path(backend.__file__).resolve(),gdn_stream.ALLOCATOR_PINS["/vllm-workspace/vllm-ascend/vllm_ascend/attention/attention_v1.py"])
   c.require(type(impl) is backend.AscendAttentionBackendImpl and impl.attn_type==backend.AttentionType.DECODER and
    impl.enable_c8_quant is impl.enable_hamming_sparse is impl.is_kv_producer is False and
    impl.kv_sharing_target_layer_name is None and
    identity(impl.key_cache,self.npu)==identity(key,self.npu) and
    identity(impl.value_cache,self.npu)==identity(value,self.npu),
    "same captured original decoder BF16 FA implementation, no encoder/quant/shared writer branch")
   fields={"class":type(impl).__module__+"."+type(impl).__qualname__,"impl_id":id(impl),
    "attn_type":str(impl.attn_type),"decoder_value":str(backend.AttentionType.DECODER),
    "enable_c8_quant":impl.enable_c8_quant,"enable_hamming_sparse":impl.enable_hamming_sparse,
    "is_kv_producer":impl.is_kv_producer,"kv_sharing_target_layer_name":impl.kv_sharing_target_layer_name}
   c.require(type(n) is int and n>0 and meta.causal is True and self.runner.use_cp is False,
    "actual source-bound ordinary non-CP causal FA native real-token writer")
   slots=meta.slot_mapping
   c.require(str(slots.dtype) in ("torch.int32","torch.int64") and len(slots.shape)==1 and len(slots)>=n,
    "complete original FA slot_mapping token slice, no block ID inference")
   raw=dict(schema="sparq.actual-native-FA-writer-metadata/v1",layer=layer,prefix=prefix,rank=rank,epoch=epoch,
    num_actual_tokens=n,slot_mapping=slots[:n].detach().cpu().tolist(),slot_mapping_identity=identity(slots,self.npu),
    cache_write_scope="original-reshape-and-cache-real-token-slice",is_encoder_decoder=impl.attn_type==backend.AttentionType.ENCODER_DECODER,
    cache_sharing_target=impl.kv_sharing_target_layer_name,CP=self.runner.use_cp,quantized=impl.enable_c8_quant,
    actual_implementation=fields,allocator_source_pins=gdn_stream.ALLOCATOR_PINS,
    original_backend_scope_admitted_before_capture=True)
   ref=c.write(self.root/("fa-writer-meta-r%d-e%d-l%d.json"%(rank,epoch,layer)),raw)
   fa.append(dict(layer=layer,prefix=prefix,rank=rank,epoch=epoch,metadata=ref,cache=[identity(t,self.npu) for t in (key,value)]))
  self.budget_ref,proof=self.joint(plans,fa,rank,epoch)
  pools=next(r["pools"] for r in proof["pools"] if r["rank"]==rank)
  if epoch==1:
   previous=dict(schema="sparq.actual-pool-last-writer-types/v1",rank=rank,epoch=0,source=self.source,pools=[],
    allocator_retirement_not_claimed=True)
   previous_ref=c.write(self.root/("GDN-TYPE-SEED-r%d.json"%rank),previous)
  else:
   c.require(self.ledger_ref is not None,"exact previous actual model typed history")
   previous_ref=self.ledger_ref;previous=c.obj(previous_ref)
  ledger=gdn_stream.typed_ledger(pools,previous,rank,epoch,self.source)
  ledger["previous"]=previous_ref;ledger["joint_budget"]=self.budget_ref
  self.t.npu.current_stream().synchronize()
  owners=[]
  for pool in pools:
   key=(pool["identity"]["device"],pool["identity"]["storage_pointer"],pool["identity"]["storage_bytes"],
    pool["identity"]["native_format_value"],pool["identity"]["native_format_type"])
   self.space();slab=self.slab(tensors[key]);cpu,raw=self.cpu(slab)
   c.require(len(raw)==pool["all_physical_bytes"],"ONE complete before copy per exact slab including padding")
   owners.append(dict(pool=pool,slab=slab,cpu=cpu))
  self.pending=dict(layers=layers,owners=owners,ledger=ledger,plans=plans,fa=fa)
 def end(self,ctx):
  c.require(self.pending is not None and not ctx.capturing,"after unchanged model, outside capture")
  self.t.npu.current_stream().synchronize();pending=self.pending;refs=[]
  # Every logical view retains identity, but no repeated physical copy/hash.
  for prefix,row in pending["layers"].items():
   self.validate_original(row["obj"])
   for record,t in zip(row["event"]["states"],row["obj"].kv_cache):
    record["identity_after"]=identity(t,self.npu)
    c.require(record["identity_after"]==record["identity_before"],"all96 original logical view identities unchanged")
  for owner in pending["owners"]:
   pool=owner["pool"];slab=owner["slab"];before=gdn_stream.view(owner["cpu"].view(self.t.uint8).numpy())
   current=next(p for p in pending["ledger"]["pools"] if p["before_owner"]==pool["before_owner"])
   check=gdn_stream.PhysicalChecker(pool,current["segments"],self.np)
   width=slab.element_size()
   for offset in range(0,pool["all_physical_bytes"],gdn_stream.CHUNK):
    number=min(gdn_stream.CHUNK,pool["all_physical_bytes"]-offset);after=None
    try:
     self.space();after_cpu,after=self.cpu(slab[offset//width:(offset+number)//width])
     check.chunk(offset,before[offset:offset+number],after);del after_cpu,after
    except BaseException as error:
     try:self.first_pool(pool,offset,before[offset:offset+number],after,error)
     except BaseException as secondary:print("GDN_PHYSICAL_PRIMARY "+repr(error)+"; retention secondary="+repr(secondary),flush=True)
     raise
   summary=check.finish()
   refs.append(c.write(self.root/("GDN-POOL-e%d-r%d-o%s.json"%(self.epoch,self.rank,pool["before_owner"])),summary))
  ledger_ref=c.write(self.root/("GDN-TYPE-e%d-r%d.json"%(self.epoch,self.rank)),pending["ledger"])
  complete=c.write(self.root/("GDN-PHYSICAL-e%d-r%d.json"%(self.epoch,self.rank)),dict(
   schema=gdn_stream.PHYSICAL_PROTOCOL,rank=self.rank,epoch=self.epoch,source=self.source,joint_budget=self.budget_ref,
   ledger=ledger_ref,pool_summaries=refs,original_full_before_copy_count=len(refs),
   independent_checker=self.checker,all64_actual_writer_metadata=True,postmortem_success_bytes_replay_claimed=False))
  events=[]
  for prefix,row in pending["layers"].items():
   event=row["event"];event["physical_epoch"]=complete;event["joint_budget"]=self.budget_ref
   event["producer_check"]=gdn_state.consume(event,self.pins,self.checker,self.source,self.physical_context);events.append(event)
  self.ledger_ref=ledger_ref;self.pending=None;self.epochs+=1;return events
 def abort(self,error):
  if self.pending is None or self.first_fault is not None:return
  owner=self.pending["owners"][0];before=gdn_stream.view(owner["cpu"].view(self.t.uint8).numpy())
  self.first_pool(owner["pool"],0,before[:gdn_stream.CHUNK],None,error)

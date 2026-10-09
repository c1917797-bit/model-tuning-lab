"""Opt-in actual source-bound FULL thin bridge; import is OFF/stdlib.
No change to original writer/core math/ACL replay or default post-update order.
Kernel/model authority is mandatory; this bridge does NOT manufacture readiness.
"""
from __future__ import annotations
import functools,os,re,threading
from pathlib import Path
import common
import workspace_budget as budget
from lifecycle import RequestLedger
import full_graph_pa as pa
import actual_replay as replay
import gdn_model_observer as gdn_observer,gdn_source
_LOCAL=threading.local()
_PATCHED=False
FA=tuple(range(3,64,4))
def require(v,m):common.require(v,m)
def tensor_identity(t):
 return (t.data_ptr(),t.untyped_storage().data_ptr(),t.storage_offset(),
  t.untyped_storage().nbytes(),tuple(t.shape),tuple(t.stride()),str(t.dtype),str(t.device))
def layer_number(prefix):
 m=re.search(r"(?:^|\.)layers\.([0-9]+)(?:\.|$)",prefix)
 require(m is not None and int(m.group(1)) in FA,"actual FA layer prefix in original64 architecture")
 return int(m.group(1))
class StockState:
 def __init__(self,runner,core,torch,npu,attention,acl,weak,Mode,ascend,diagnostic,emit):
  self.runner=runner;self.core=core;self.t=torch;self.npu=npu;self.a=attention;self.acl=acl;self.weak=weak
  self.Mode=Mode;self.ascend=ascend;self.diagnostic=diagnostic;self.emit=emit
  self.ledger=RequestLedger(16);self.bindings={};self.registry=None;self.workspaces={}
  self.arm=os.environ.get("QWEN36_SPARQ_MODEL_ARM","candidate");require(self.arm in ("dense","candidate"),"actual explicit arm")
  self.snapshots={};self.replay_calls=[]
  self.model_entries=0;self.post_updates=0;self.dummy_depth=0;self.dummy_batches=set();self.capture_batches=set()
  self.current=None;self.baseline_allocated=None;self.baseline_peak=None;self.capture_inputs={}
  self.gdn_observer=gdn_observer.Observer(runner,torch,npu,gdn_source.sources(),gdn_source.runtime()) if diagnostic else None
  self.actual_epoch=0;self.mixed_fa={};self.pending_scheduler=None;self.native_caches={};self.native_impls={}
  self.last_ctx=None;self.formal_turns=0;self.formal_full_turns=0;self.formal_replays=0;self.formal_post_updates=0
  self.formal_batches={};self.formal_requests={};self.tensor_identity=tensor_identity
  self.gdn_runtime=gdn_source.runtime() if not diagnostic else None
 def admit(self):return common.validate_runner(self.runner,self.Mode,self.ascend())
 def bind(self,impl,prefix):
  n=layer_number(prefix);old=self.bindings.get(prefix)
  row=dict(layer=n,impl_id=id(impl))
  require(old is None or old==row,"same actual prefix/backend identity, no monkeypatch ABA")
  require(all(v["layer"]!=n or k==prefix for k,v in self.bindings.items()),"one actual prefix per FA")
  self.bindings[prefix]=row;self.native_impls[prefix]=impl
 def ensure_registry(self):
  if self.registry is None:
   require({r["layer"] for r in self.bindings.values()}==set(FA),"actual sixteen FA bindings before FULL capture")
   self.registry=pa.CaptureRegistry(dict(self.bindings))
  return self.registry
 def budget(self):
  # Actual cumulative allocator includes every owned capture bucket/graph pool
  # and current transient allocations, not a numeric18page projection.
  require(self.baseline_allocated is not None,"actual native-cache-backed warmup aux baseline, not profile/model load")
  actual=self.t.npu.memory_allocated();reserved=self.t.npu.memory_reserved();peak=self.t.npu.max_memory_allocated()
  owned=sum(ws.bytes+ws.native_pa.context.bytes() for ws in self.workspaces.values())+sum(x.bytes() for x in self.snapshots.values())
  require(owned<=common.AUX_CEILING and actual-self.baseline_allocated<=common.AUX_CEILING and peak-self.baseline_allocated<=common.AUX_CEILING,
   "actual cumulative all-batch candidate aux+capture/transient <=2GiB, no memory saving claim")
  return dict(owned_guarded_bytes=owned,actual_current_allocated_bytes=actual,actual_current_reserved_bytes=reserved,
   actual_delta_allocated_bytes=actual-self.baseline_allocated,actual_peak_bytes=peak,
   actual_peak_upper_delta_bytes=peak-self.baseline_allocated,baseline_observation=self.baseline_peak,
   baseline_point="first-original-native-cache-backed-noncapture-dummy-selected-FA",
   aux_ceiling_bytes=common.AUX_CEILING,
   full_native_KV_GDN_not_removed=True,peak_graph_aux_within_conservative_ceiling=True,model_numeric_verified=False)
 def stockify(self):
  registry=self.ensure_registry()
  if self.arm=="dense":return
  for (prefix,batch,pages),ws in self.workspaces.items():
   if not hasattr(ws.native_pa,"update_stock"):
    previous=list(ws.native_pa.values)
    host=pa.make_stock_pa(self.core,self.t,self.npu,self.acl,self.weak,self.a._EXTRA_CTX,
     registry,prefix,self.bindings[prefix]["impl_id"],batch,ws.capacity)
    host.set_lengths(previous);ws.native_pa=host
 def begin(self,ctx,batch):
  self.admit();require(self.current is None,"single synchronous model turn, no overlapping graph updates")
  if self.dummy_depth:
   self.current=dict(dummy=True,batch=batch,runtime=ctx.cudagraph_runtime_mode);return
  if ctx.cudagraph_runtime_mode==self.Mode.FULL:
   require(batch in common.BATCHES and self.runner.input_batch.num_reqs==batch and not ctx.capturing and
    ctx.batch_descriptor.uniform and ctx.batch_descriptor.num_tokens==batch,
    "true B1..16 uniform one-token decode: reject virtual rows/new real-request capture")
   require(self.registry is not None and batch in self.capture_batches,"actual warmup/capture mandatory before real replay")
   topology={}
   for prefix in self.registry.bindings:
    require(prefix in ctx.attn_metadata,"actual keyed FA metadata, never zip64 dict")
    meta=ctx.attn_metadata[prefix];lengths=list(meta.seq_lens_list)
    require(self.capture_inputs.get((prefix,batch))==(tensor_identity(meta.block_tables),tensor_identity(self.runner.seq_lens[:batch])),
     "real replay native metadata pointers/stride/layout match original captured device inputs")
    require(meta.num_prefills==0 and meta.num_actual_tokens==batch and len(lengths)==batch,"real native decode CPU domain")
    self.ledger.decode(lengths);topology[prefix]=lengths
   frame=self.ledger.decode(next(iter(topology.values())))
   epoch=self.registry.queue(batch,self.acl.get_graph_params(),topology,frame)
   self.current=dict(dummy=False,batch=batch,runtime=ctx.cudagraph_runtime_mode,epoch=epoch,frame=frame,full_topology=topology,updated=False)
   self.replay_calls=[]
   for (prefix,b),sample in self.snapshots.items():
    if b==batch:sample.prepare(epoch)
  else:
   require(ctx.cudagraph_runtime_mode==self.Mode.NONE,"mixed/prefill same stock NONE path for both arms")
   self.current=dict(dummy=False,batch=batch,runtime=ctx.cudagraph_runtime_mode,updated=False)
  if self.diagnostic:
   self.actual_epoch+=1;self.mixed_fa={}
   ids=list(self.runner.input_batch.req_ids[:self.runner.input_batch.num_reqs])
   self.current["actual_epoch"]=self.actual_epoch;self.current["request_ids"]=ids
   self.gdn_observer.begin(ctx,os.environ["QWEN36_SPARQ_MODEL_TRACE_ROOT"],
    int(os.environ["QWEN36_SPARQ_ACTUAL_RANK"]),self.actual_epoch,ids,self.native_caches,self.native_impls,self.a)
 def post(self,ctx,batch,stream):
  require(self.current is not None and self.current["batch"]==batch,"actual post-run_model callback within one current turn")
  if self.current["dummy"]:
   # Stock warmup NONE has no pending PA task. Capture FULL records only.
   require(ctx.capturing or ctx.cudagraph_runtime_mode==self.Mode.NONE,"dummy FULL replay needs explicit lifecycle, not request authority")
   return
  if ctx.cudagraph_runtime_mode==self.Mode.FULL:
   require(not self.current["updated"] and not ctx.capturing,"exactly one POST-enqueue update, not pre-replay")
   record=pa.update_candidate_graph(self.t,self.acl,self.registry,stream,ctx,batch)
   self.current["updated"]=True;self.post_updates+=1
   if self.diagnostic:self.emit("actual-full-post-update",dict(record,actual_16_FA_events=True,native_PA_update_invoked=True,async_numerical_pass=False,model_ready=False))
 def end(self,ctx):
  require(self.current is not None,"actual current model turn")
  fa_refs={}
  if not self.current["dummy"] and ctx.cudagraph_runtime_mode==self.Mode.FULL:
   require(self.current["updated"] and self.registry.queued is None,"real FULL all16 fresh updates complete")
   if self.diagnostic:
    self.t.npu.current_stream().synchronize() # diagnostic only; formal keeps stock sync
    for (prefix,ws_batch,pages),ws in self.workspaces.items():
     require(ws.guards(),"actual persistent guarded selector/scratch/CPU metadata")
     if ws_batch==self.current["batch"]:
      host=self.current["full_topology"][prefix]
      require(ws.lengths.detach().cpu().tolist()==host and ws.native_pa.values==tuple(min(n,128) for n in host),
       "diagnostic actual replay full selector length/host scratch clamp, not only source shape")
    require(len(self.replay_calls)==1,"one actual original stock FULL ACL replay per model turn")
    for prefix in self.registry.bindings:
     sample=self.snapshots[(prefix,self.current["batch"])]
     observed=sample.observe(os.environ["QWEN36_SPARQ_MODEL_TRACE_ROOT"],int(os.environ["QWEN36_SPARQ_ACTUAL_RANK"]),prefix,self.current["batch"],self.current["frame"],self.arm)
     observed["model_epoch"]=self.current["actual_epoch"]
     if self.arm=="candidate":
      ws=next(ws for (p,bb,pp),ws in self.workspaces.items() if p==prefix and bb==self.current["batch"])
      observed["_actual_selected_tensor"]=sample.selected
      observed["original_native_selected_gather"]=replay.observe_native_gather(
       self.t,ws,self.native_caches[prefix],observed,os.environ["QWEN36_SPARQ_MODEL_TRACE_ROOT"])
     observed.pop("_actual_selected_tensor",None)
     fa_refs[str(self.bindings[prefix]["layer"])]=self.emit("actual-full-PA-snapshot",observed)
    self.emit("actual-full-turn",dict(self.budget(),frame=self.current["frame"],ACL_replays=self.replay_calls,arm=self.arm,completed=True,full64_layer_numeric_verified=False,model_ready=False))
  if not self.current["dummy"] and self.diagnostic:
   events=self.gdn_observer.end(ctx);gdn_refs={}
   for event in events:gdn_refs[str(event["layer"])]=self.emit("actual-GDN-state".lower(),event)
   self.emit("actual-model-boundary",dict(epoch=self.current["actual_epoch"],batch=self.runner.input_batch.num_reqs,
    runtime="FULL" if ctx.cudagraph_runtime_mode==self.Mode.FULL else "NONE",
    request_ids=self.current["request_ids"],gdn=gdn_refs,mixed_FA_records=self.mixed_fa,
    native_request_rows=self.pending_scheduler,fa=fa_refs,original_PA_post_update_finished=True,
    all_active_GDN_dense_equivalence_not_claimed=True,model_ready=False))
  if not self.current["dummy"] and not self.diagnostic:
   self.formal_turns+=1;self.last_ctx=ctx
   if ctx.cudagraph_runtime_mode==self.Mode.FULL:
    require(len(self.replay_calls)==1,"one actual existing ACL FULL replay; formal counter not a predicted call")
    self.formal_full_turns+=1;self.formal_replays+=len(self.replay_calls);self.formal_post_updates=self.post_updates
    key=str(self.current["batch"]);self.formal_batches[key]=self.formal_batches.get(key,0)+1
  self.model_entries+=1;self.current=None
 def selected_forward(self,impl,prefix,query,kc,vc,metadata,output):
  if self.diagnostic:self.native_caches[prefix]=(kc,vc,metadata.block_tables)
  batch=int(query.shape[0]);pages=int(metadata.block_tables.shape[1]);capturing=self.a._EXTRA_CTX.capturing
  require(common.SCREEN_PAGES<=pages<=320 and kc.shape[0]>=16*common.SCREEN_PAGES,
   "actual native allocator/max_pages covers true C16 fixed32768+1024; no numeric18page borrowing")
  require(batch in common.BATCHES and tuple(query.shape[1:])==(6,256) and
   query.dtype==kc.dtype==vc.dtype==self.t.bfloat16 and kc.shape==vc.shape and tuple(kc.shape[1:])==(128,1,256) and
   metadata.num_actual_tokens==batch and metadata.num_prefills==0 and metadata.causal is True,
   "actual local6Q/1KV BF16 full native cache and true decode only")
  key=(prefix,batch,pages);ws=self.workspaces.get(key)
  if ws is None:
   require(self.dummy_depth>0 and not capturing,"source-supported warmup allocation ONLY; never guard initialization in graph")
   if self.baseline_allocated is None:
    self.baseline_allocated=self.t.npu.memory_allocated()
    self.baseline_peak=self.t.npu.max_memory_allocated()
   existing=sum(x.bytes for x in self.workspaces.values())+sum(x.bytes() for x in self.snapshots.values())
   budget.admission(existing,batch,pages,self.t.npu.memory_allocated(),
    self.baseline_allocated,self.t.npu.max_memory_allocated())
   ws=self.core.GraphTokenWorkspace(kc.device,batch,pages,128,32,1)
   require(ws.bytes==budget.guarded_bytes(batch,pages),"actual original guarded allocation shape bytes")
   self.workspaces[key]=ws
  if capturing:require(self.registry is not None and hasattr(ws.native_pa,"update_stock"),"preallocated stock PA owner before capture")
  lengths=list(metadata.seq_lens_list)
  require(len(lengths)==batch and all(type(n) is int and 0<n<=ws.capacity for n in lengths),"actual nonempty host full topology within model max_pages")
  if capturing:
   require(ws.native_pa.values==tuple(min(n,128) for n in lengths),
    "CPU PA context prepared BEFORE GLOBAL graph capture, not initialized in graph")
   identity=(tensor_identity(metadata.block_tables),tensor_identity(self.runner.seq_lens[:batch]))
   require((prefix,batch) not in self.capture_inputs,"one actual captured native topology identity")
   self.capture_inputs[(prefix,batch)]=identity
  else:ws.native_pa.set_lengths(lengths) # Known CPU topology outside capture, no captured H2D
  # metadata.seq_lens is CPU in this deployed PA backend. Original runner.seq_lens
  # is persistent NPU int32 and must remain FULL native lengths for selector.
  pa.record_selector_topology(self.t,ws,self.runner.seq_lens[:batch],metadata.block_tables)
  self.a.record_attention_compute_start()
  sample=self.snapshot(prefix,batch,query.device) if self.diagnostic else None
  if sample is not None:sample.before(query)
  got,selected,alpha,channels=ws.run(query,kc,vc,None,reallocation=False,variant="paper-gqa-probability")
  output[:batch].copy_(got)
  if sample is not None:sample.after(got,ws,selected,alpha,channels)
  return output
 def snapshot(self,prefix,batch,device):
  key=(prefix,batch);sample=self.snapshots.get(key)
  if sample is None:
   require(self.dummy_depth>0 and not self.a._EXTRA_CTX.capturing,"snapshot allocation only in original noncapture warmup")
   if self.baseline_allocated is None:
    self.baseline_allocated=self.t.npu.memory_allocated();self.baseline_peak=self.t.npu.max_memory_allocated()
   sample=replay.Snapshots(self.core,self.t,self.npu,batch,device,self.arm=="candidate")
   self.snapshots[key]=sample;self.budget()
  return sample
 def dense_forward(self,impl,prefix,query,key,value,cache,metadata,output,original_impl):
  if self.diagnostic:self.native_caches[prefix]=(cache[0],cache[1],metadata.block_tables)
  batch=int(query.shape[0]);sample=self.snapshot(prefix,batch,query.device) if self.diagnostic else None
  capturing=self.a._EXTRA_CTX.capturing
  if capturing:
   require(self.registry is not None,"all16 dense original warmup bindings")
   identity=(tensor_identity(metadata.block_tables),tensor_identity(self.runner.seq_lens[:batch]))
   require((prefix,batch) not in self.capture_inputs,"one actual original dense capture")
   self.capture_inputs[(prefix,batch)]=identity
   params=self.acl.get_graph_params();ordinal=len(params.attn_params[batch])
  if sample is not None:sample.before(query)
  result=original_impl(impl,query,key,value,cache,metadata,output)
  if sample is not None:sample.after(output[:batch])
  if capturing:
   params=self.acl.get_graph_params()
   require(len(params.attn_params[batch])==len(params.handles[batch])==len(params.events[batch])==ordinal+1,
    "one native stock PA task captured for actual dense FA")
   self.registry.adopt_existing(batch,prefix,id(impl),params,ordinal)
  return result
 def dense_post(self,ctx,batch):
  require(self.current is not None and self.current["batch"]==batch,"actual original dense POST-update scope")
  if self.current["dummy"]:return
  if ctx.cudagraph_runtime_mode==self.Mode.FULL:
   require(not self.current["updated"] and not ctx.capturing,"one original dense POST-update")
   params=self.acl.get_graph_params();records=self.registry.complete(batch,params);epoch=self.current["epoch"]
   for prefix,row in records.items():
    query,key,value,nkv,nheads,scale,table,lens,out=row["param"]
    require(lens.device.type=="cpu" and lens.dtype==self.t.int32 and tuple(lens.shape)==(batch,) and
     lens.tolist()==self.current["full_topology"][prefix],"original dense PA full CPU context, not scratch clamp")
    self.registry.mark(prefix,epoch)
   record=self.registry.finish(params);self.current["updated"]=True;self.post_updates+=1
   if self.diagnostic:self.emit("actual-full-post-update",dict(record,arm="dense",native_PA_update_original=True,model_ready=False))
def install_from_env():
 global _PATCHED
 if os.environ.get("QWEN36_SPARQ_STOCK_FULL_ENABLED")!="1":
  return dict(default_enabled=False,model_executed=False,model_ready=False)
 require(not _PATCHED,"single explicit full bridge install; no chain")
 import source_contract as c
 source,files=c.source(os.environ.get("QWEN36_SPARQ_STOCK_FULL_SOURCE",""),os.environ.get("QWEN36_SPARQ_STOCK_FULL_SOURCE_SHA",""))
 # Strict replay of full original component consumer, not witness16 permission.
 authority=c.actual_component(os.environ.get("QWEN36_SPARQ_NUMERIC_AUTHORITY",""),os.environ.get("QWEN36_SPARQ_NUMERIC_AUTHORITY_SHA",""))
 mode=os.environ.get("QWEN36_SPARQ_MODEL_MODE","diagnostic");require(mode in ("diagnostic","formal"),"explicit instrumentation mode")
 if mode=="formal":
  from consume_model import consume_authority
  consume_authority(c.bound(os.environ.get("QWEN36_SPARQ_FULL_MODEL_AUTHORITY",""),
   os.environ.get("QWEN36_SPARQ_FULL_MODEL_AUTHORITY_SHA","")),source,
   c.bound(os.environ["QWEN36_SPARQ_NUMERIC_AUTHORITY"],os.environ["QWEN36_SPARQ_NUMERIC_AUTHORITY_SHA"]),replay=True)
 import identity_bridge
 startup_memory=identity_bridge.startup_memory_gate(source,files)
 import vllm_ascend.ops # actual v0.23 bootstrap before attention/device_op
 import torch,torch_npu
 import vllm_ascend.attention.attention_v1 as a
 import vllm_ascend.worker.model_runner_v1 as r
 import vllm_ascend.compilation.acl_graph as acl
 from vllm.config.compilation import CUDAGraphMode as Mode
 from vllm.forward_context import get_forward_context
 from vllm_ascend.ascend_config import get_ascend_config
 from vllm.distributed import get_tensor_model_parallel_rank,get_tensor_model_parallel_world_size
 from sparq_token_v4 import core
 c.runtime_sources(a,r,acl)
 originals={name:getattr(r.NPUModelRunner,name) for name in ("_prepare_inputs","_update_states","_dummy_run","_model_forward")}
 original_outer=a.AscendAttentionBackendImpl.forward;original_impl=a.AscendAttentionBackendImpl.forward_impl
 original_backend_update=a.AscendAttentionBackendImpl.update_graph_params
 require(all(fn.__module__==r.__name__ for fn in originals.values()) and
  original_outer.__module__==original_impl.__module__==a.__name__,"unknown prior model/backend monkeypatch")
 states={}
 def emit(kind,value):
  return c.event(os.environ.get("QWEN36_SPARQ_MODEL_TRACE_ROOT",""),get_tensor_model_parallel_rank(),kind,value,source,authority)
 def state(runner):
  require(get_tensor_model_parallel_world_size()==4,"actual TP4")
  os.environ["QWEN36_SPARQ_ACTUAL_RANK"]=str(get_tensor_model_parallel_rank())
  if id(runner) not in states:
   from ann_model_state import ANNState
   State=StockState if os.environ["QWEN36_SPARQ_MODEL_ARM"]=="dense" else ANNState
   states[id(runner)]=State(runner,core,torch,torch_npu,a,acl,acl.weak_ref_tensors,Mode,get_ascend_config,mode=="diagnostic",emit)
   states[id(runner)].original_backend_update=original_backend_update
   states[id(runner)].startup_memory_ref=startup_memory
   if mode=="formal":
    import formal_stats
    formal_stats.start(states[id(runner)],get_tensor_model_parallel_rank(),source,files,dict(path=os.environ["QWEN36_SPARQ_NUMERIC_AUTHORITY"],sha256=os.environ["QWEN36_SPARQ_NUMERIC_AUTHORITY_SHA"]))
   if mode=="diagnostic":
    import sys,hashlib
    emit("actual-rank-worker",dict(rank=get_tensor_model_parallel_rank(),world_size=get_tensor_model_parallel_world_size(),
     pre_weight_memory=startup_memory,namespace_pid=os.getpid(),logical_device=torch.npu.current_device(),common_identity_flag=__import__("identity_bridge").flag(),actual_proc_stat=Path("/proc/self/stat").read_text(),
     actual_proc_cgroup=Path("/proc/self/cgroup").read_text(),actual_proc_cmdline_sha256=hashlib.sha256(Path("/proc/self/cmdline").read_bytes()).hexdigest(),
     actual_proc_argv=Path("/proc/self/cmdline").read_bytes().decode().rstrip("\0").split("\0"),
     model_core_algorithm_source_unchanged=True,original_GDN_donor_receiver_unchanged=True,ready=False))
  return states[id(runner)]
 @functools.wraps(originals["_update_states"])
 def update(runner,scheduler):
  got=originals["_update_states"](runner,scheduler);s=state(runner);s.ledger.finish(list(scheduler.finished_req_ids))
  s.actual_finished=list(scheduler.finished_req_ids);return got
 @functools.wraps(originals["_prepare_inputs"])
 def prepare(runner,scheduler,scheduled):
  got=originals["_prepare_inputs"](runner,scheduler,scheduled);s=state(runner);s.admit()
  ids=list(runner.input_batch.req_ids[:runner.input_batch.num_reqs])
  rows=[dict(rid=rid,object_id=id(runner.requests[rid]),computed=int(runner.input_batch.num_computed_tokens_cpu[i]),
   scheduled=int(scheduler.num_scheduled_tokens[rid])) for i,rid in enumerate(ids)]
  s.ledger.prepare(rows)
  if not s.diagnostic:
   for row in rows:
    prior=s.formal_requests.get(row["rid"]);s.formal_requests[row["rid"]]=dict(object_id=row["object_id"],first_computed=row["computed"] if prior is None else prior["first_computed"],last_computed=row["computed"],last_scheduled=row["scheduled"])
  s.pending_scheduler=dict(schema="sparq.actual-scheduler-allocation/v1",request_rows=rows,
   finished_req_ids=list(getattr(s,"actual_finished",[])),
   block_ids={rid:[list(ids) for ids in runner.requests[rid].block_ids] for rid in ids},
   query_start_loc_cpu=runner.query_start_loc.cpu[:runner.input_batch.num_reqs+1].tolist(),
   request_ids_order=ids,actual_original_prepare_returned=True)
  _LOCAL.state=s;return got
 @functools.wraps(originals["_dummy_run"])
 def dummy(runner,*args,**kwargs):
  s=state(runner);s.admit();previous=getattr(_LOCAL,"state",None);_LOCAL.state=s;s.dummy_depth+=1
  profile=kwargs.get("is_profile",False);previous_profile=getattr(_LOCAL,"profile_metadata_none",False)
  try:
   require(type(profile) is bool,"explicit stock profile flag")
   if profile:
    require(kwargs.get("force_attention",False) is False and kwargs.get("is_graph_capturing",False) is False and
     kwargs.get("cudagraph_runtime_mode") in (None,Mode.NONE),"stock metadataNone profile only, never native warmup/capture")
    profile_before=(s.baseline_allocated,s.baseline_peak,{k:id(v) for k,v in s.workspaces.items()},
     {k:id(v) for k,v in s.snapshots.items()},set(s.capture_batches),dict(s.capture_inputs),s.registry)
    _LOCAL.profile_metadata_none=True
    got=originals["_dummy_run"](runner,*args,**kwargs)
    require(s.current is None and profile_before==(s.baseline_allocated,s.baseline_peak,
     {k:id(v) for k,v in s.workspaces.items()},{k:id(v) for k,v in s.snapshots.items()},
     set(s.capture_batches),dict(s.capture_inputs),s.registry),
     "metadataNone profile cannot mint native baseline/warmup/capture authority")
    return got # Bind actual16 FA, but do not stockify/budget or grant warmup.
   _LOCAL.profile_metadata_none=False
   if kwargs.get("is_graph_capturing",False):
    batch=int(args[0] if args else kwargs["num_tokens"])
    require(kwargs.get("profile_seq_lens") is None and kwargs.get("uniform_decode") is True and
     kwargs.get("cudagraph_runtime_mode")==Mode.FULL and batch in common.BATCHES,
     "exact source-supported stock capture descriptor; no alternate profile length/dummy authority")
    require(s.registry is not None and (not s.diagnostic or len([k for k in s.snapshots if k[1]==batch])==16),
     "actual all16 FA noncapture warmup allocations before native capture")
    for (prefix,b,pages),ws in s.workspaces.items():
     if b==batch:
      if s.arm=="dense":ws.native_pa.set_lengths([r.SEQ_LEN_WITH_MAX_PA_WORKSPACE]*batch)
   got=originals["_dummy_run"](runner,*args,**kwargs)
   if s.workspaces or s.snapshots or len(s.bindings)==16:
    s.ensure_registry();s.stockify()
    if s.diagnostic or s.workspaces:s.budget()
    for batch in set(k[1] for k in s.snapshots)|set(s.registry.captures):
     if batch in s.registry.captures:
      s.registry.complete(batch,acl.get_graph_params());s.capture_batches.add(batch)
   return got
  finally:s.dummy_depth-=1;_LOCAL.state=previous;_LOCAL.profile_metadata_none=previous_profile
 @functools.wraps(originals["_model_forward"])
 def model_forward(runner,*args,**kwargs):
  s=state(runner);_LOCAL.state=s;ctx=get_forward_context();batch=int(args[0] if args else kwargs["num_tokens_padded"])
  s.begin(ctx,batch)
  try:
   got=originals["_model_forward"](runner,*args,**kwargs);s.end(ctx);return got
  except BaseException as primary:
   if s.gdn_observer is not None:
    try:s.gdn_observer.abort(primary)
    except BaseException as secondary:print("GDN_ORIGINAL_MODEL_ERROR "+repr(primary)+"; retention secondary="+repr(secondary),flush=True)
   s.current=None;raise
 @functools.wraps(original_outer)
 def outer(impl,layer,*args,**kwargs):
  s=getattr(_LOCAL,"state",None);require(s is not None,"actual runner/dummy scope before outer writer")
  if getattr(_LOCAL,"profile_metadata_none",False):
   require((args[4] if len(args)>4 else kwargs.get("attn_metadata",object())) is None,
    "actual stock profile original FA metadata must be None")
  prefix=layer.layer_name;s.bind(impl,prefix);previous=getattr(_LOCAL,"prefix",None);_LOCAL.prefix=prefix
  try:return original_outer(impl,layer,*args,**kwargs) # original cache writer+notify FIRST; no repeated native writer
  finally:_LOCAL.prefix=previous
 @functools.wraps(original_impl)
 def forward(impl,query,key,value,cache,metadata,output):
  if metadata.attn_state!=a.AscendAttentionState.DecodeOnly:
   s=getattr(_LOCAL,"state",None);prefix=getattr(_LOCAL,"prefix",None)
   got=original_impl(impl,query,key,value,cache,metadata,output)
   if s is not None and s.diagnostic and not s.dummy_depth:
    require(not a._EXTRA_CTX.capturing and s.current is not None,"original mixed NONE outside capture")
    require(layer_number(prefix) not in s.mixed_fa,"one original mixed FA call per actual model turn")
    s.mixed_fa[str(layer_number(prefix))]=s.emit("actual-mixed-stock-FA".lower(),
     dict(prefix=prefix,epoch=s.current["actual_epoch"],actual_original_forward_impl_called=True,
      sparse_algorithm_active=False,native_attention_state=str(metadata.attn_state),
      num_prefills=metadata.num_prefills,num_actual_tokens=metadata.num_actual_tokens,
      query_identity=tensor_identity(query),output_identity=tensor_identity(output),
      output_finite=bool(s.t.isfinite(output[:metadata.num_actual_tokens]).all().detach().cpu().item()),
      cache_identity=[tensor_identity(x) for x in cache],independent_mixed_numeric_pass_not_claimed=True))
   return got
  s=getattr(_LOCAL,"state",None);prefix=getattr(_LOCAL,"prefix",None)
  require(s is not None and prefix in s.bindings,"actual bound FA prefix/runner")
  require(type(impl) is a.AscendAttentionBackendImpl and impl.num_heads==6 and impl.num_kv_heads==1 and impl.head_size==256 and
   not impl.enable_c8_quant and not impl.enable_hamming_sparse and impl.sinks is None and impl.sliding_window is None and
   impl.alibi_slopes is None and not impl.is_kv_producer and impl.kv_sharing_target_layer_name is None,
   "ordinary unchanged BF16 PA scope; no GDN/producer/shared/sink/quant transform")
  require(impl.key_cache.data_ptr()==cache[0].data_ptr() and impl.value_cache.data_ptr()==cache[1].data_ptr(),"native original allocator backing identity")
  if s.arm=="dense":return s.dense_forward(impl,prefix,query,key,value,cache,metadata,output,original_impl)
  return s.selected_forward(impl,prefix,query,impl.key_cache,impl.value_cache,metadata,output)
 @functools.wraps(original_backend_update)
 def backend_update(stream,ctx,tokens,config,spec=None,cp_tokens=None,draft_meta=None):
  s=getattr(_LOCAL,"state",None)
  if s is None:return original_backend_update(stream,ctx,tokens,config,spec,cp_tokens,draft_meta)
  require(not a._EXTRA_CTX.is_draft_model and spec is None and draft_meta is None,"no draft/mixed alternate update branch")
  if s.arm=="dense":
   result=original_backend_update(stream,ctx,tokens,config,spec,cp_tokens,draft_meta);s.dense_post(ctx,tokens);return result
  return s.post(ctx,tokens,stream)
 r.NPUModelRunner._update_states=update;r.NPUModelRunner._prepare_inputs=prepare
 r.NPUModelRunner._dummy_run=dummy;r.NPUModelRunner._model_forward=model_forward
 a.AscendAttentionBackendImpl.forward=outer;a.AscendAttentionBackendImpl.forward_impl=forward
 a.AscendAttentionBackendImpl.update_graph_params=staticmethod(backend_update)
 replay.wrap_original_acl(acl,get_forward_context,lambda:getattr(_LOCAL,"state",None))
 _PATCHED=True
 return dict(installed=True,diagnostic_only=mode=="diagnostic",formal_enabled=mode=="formal",model_ready=False,source=source,kernel_authority=authority)

State=StockState # Legacy source-only dense helpers; candidate uses explicit ANNState above.

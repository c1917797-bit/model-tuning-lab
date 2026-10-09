"""Actual worker candidate ANN path; meanOFF explicitly author-configurable.
All16 FA original output copies precede shared arena reuse. Stock dense and mixed
FA paths/GDN stay original. No PA tasks/handles or synthetic task_update calls.
"""
import os
import common,source_contract as c
from bridge import StockState,tensor_identity
import no_pa_full as post
import long_workspace,ann_snapshot,allocation_contract
class ANNState(StockState):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs)
  c.require(self.arm=="candidate","ANNState only explicit candidate")
  self.arena=None;self.sample_owners={};self.arena_class=None;self.forward_order=[];self.native_geometries={}
 def ensure_registry(self):
  if self.registry is None:
   c.require({r["layer"] for r in self.bindings.values()}==set(common.FA),"actual all16 bound ANN FA before capture")
   self.registry=post.Registry(dict(self.bindings))
  return self.registry
 def stockify(self):return None # Genuine noPA graph: never fabricate native handles/events.
 def budget(self):
  c.require(self.baseline_allocated is not None,"same original native-cache/GDN-backed aux baseline")
  current=self.t.npu.memory_allocated();peak=self.t.npu.max_memory_allocated();reserved=self.t.npu.memory_reserved()
  owned=(self.arena.bytes if self.arena else 0)+sum(p.bytes() for p in self.sample_owners.values())
  c.require(owned<=common.AUX_CEILING and current-self.baseline_allocated<=common.AUX_CEILING and
   peak-self.baseline_allocated<=common.AUX_CEILING,"actual allb/all16FA graph pool+guarded+oracle/transients aux <=2GiB")
  return dict(owned_guarded_bytes=owned,actual_current_allocated_bytes=current,actual_current_reserved_bytes=reserved,
   actual_delta_allocated_bytes=current-self.baseline_allocated,actual_peak_bytes=peak,
   actual_peak_upper_delta_bytes=peak-self.baseline_allocated,baseline_observation=self.baseline_peak,
   aux_ceiling_bytes=common.AUX_CEILING,baseline_point="first-original-native-cache-backed-noncapture-dummy-selected-FA",
   full_native_KV_GDN_not_removed=True,peak_graph_aux_within_conservative_ceiling=True,
   mean_configuration="author-reallocate-to-mean-value-OFF",memory_saving_claim=False,model_numeric_verified=False)
 def snapshot(self,prefix,batch,device):
  if prefix not in self.sample_owners:
   c.require(self.dummy_depth>0 and not self.a._EXTRA_CTX.capturing and self.arena is not None,
    "all layer observation owners allocated ONLY during original noncapture warmup")
   self.sample_owners[prefix]=ann_snapshot.Pool(self.core,self.t,self.npu,self.arena.pages,device)
   self.budget()
  sample=self.sample_owners[prefix].view(batch);self.snapshots[(prefix,batch)]=sample;return sample
 def begin(self,ctx,batch):
  self.admit();c.require(self.current is None,"actual single original synchronous model turn")
  self.forward_order=[]
  if self.dummy_depth:
   self.current=dict(dummy=True,batch=batch,runtime=ctx.cudagraph_runtime_mode);return
  self.actual_epoch+=1
  self.current=dict(dummy=False,batch=batch,runtime=ctx.cudagraph_runtime_mode,actual_epoch=self.actual_epoch,updated=False)
  self.replay_calls=[];self.mixed_fa={}
  ids=list(self.runner.input_batch.req_ids[:self.runner.input_batch.num_reqs]);self.current["request_ids"]=ids
  if ctx.cudagraph_runtime_mode==self.Mode.FULL:
   c.require(batch in common.BATCHES and self.runner.input_batch.num_reqs==batch and not ctx.capturing and
    ctx.batch_descriptor.uniform and ctx.batch_descriptor.num_tokens==batch and batch in self.capture_batches,
    "true original allB uniform FULL replay; no padding/capture-as-model evidence")
   topology={}
   for prefix in self.registry.bindings:
    meta=ctx.attn_metadata[prefix];lengths=list(meta.seq_lens_list)
    c.require(meta.num_prefills==0 and meta.num_actual_tokens==batch and len(lengths)==batch and
     all(type(n) is int and 0<n<=self.arena.capacity for n in lengths),"actual full native history within captured max_pages")
    topology[prefix]=lengths
   c.require(len({tuple(v) for v in topology.values()})==1,"one original request full length domain across actual16 FA")
   frame=self.ledger.decode(next(iter(topology.values())))
   self.registry.begin_replay(batch,self.actual_epoch,ctx.attn_metadata,self.runner.seq_lens[:batch],
    self.acl.get_graph_params(),frame)
   self.current.update(frame=frame,full_topology=topology)
   if self.diagnostic:
    for prefix in self.registry.bindings:self.snapshots[(prefix,batch)].prepare(self.actual_epoch)
  else:c.require(ctx.cudagraph_runtime_mode==self.Mode.NONE,"same untouched original mixed NONE path as dense")
  if self.diagnostic:
   self.gdn_observer.begin(ctx,os.environ["QWEN36_SPARQ_MODEL_TRACE_ROOT"],
    int(os.environ["QWEN36_SPARQ_ACTUAL_RANK"]),self.actual_epoch,ids,self.native_caches,self.native_impls,self.a)
 def post(self,ctx,batch,stream):
  c.require(self.current is not None and self.current["batch"]==batch,"actual original runner POST scope")
  if self.current["dummy"]:return
  c.require(ctx.cudagraph_runtime_mode==self.Mode.FULL and not self.current["updated"],"one original POST after original ACL")
  got=self.registry.post(self.original_backend_update,stream,ctx,batch,self.runner.vllm_config,self.acl.get_graph_params())
  self.current["updated"]=True;self.post_updates+=1
  if self.diagnostic:self.emit("actual-full-post-update",dict(original_POST_called_once=True,native_PA_tasks=0,
   PA_task_update_count=0,actual_16_ANN_not_PA=True,model_ready=False))
  return got
 def selected_forward(self,impl,prefix,query,kc,vc,metadata,output):
  b=int(query.shape[0]);pages=int(metadata.block_tables.shape[1]);capturing=self.a._EXTRA_CTX.capturing
  geometry=allocation_contract.observe_native_geometry(self.runner,prefix,kc,vc,metadata,b,self.t,tensor_identity)
  c.require(pages==geometry["logical_pages_per_request"] and kc.shape[0]>=16*common.SCREEN_PAGES and b in common.BATCHES and
   tuple(query.shape[1:])==(6,256) and query.dtype==kc.dtype==vc.dtype==self.t.bfloat16 and
   kc.shape==vc.shape and tuple(kc.shape[1:])==(128,1,256) and metadata.causal is True and
   metadata.num_actual_tokens==b and metadata.num_prefills==0,"actual long original local6Q/1KV/native decode geometry")
  if self.arena is None:
   c.require(self.dummy_depth>0 and not capturing,"shared long arena only original native-backed noncapture warmup")
   self.baseline_allocated=self.t.npu.memory_allocated();self.baseline_peak=self.t.npu.max_memory_allocated()
   self.arena_class=long_workspace.build(self.t)
   self.arena=self.arena_class(kc.device,pages,int(kc.shape[0]),True,0,self.t.npu.memory_allocated(),
    self.baseline_allocated,self.t.npu.max_memory_allocated(),geometry=geometry)
  c.require(pages==self.arena.pages and all(geometry[k]==self.arena.geometry[k] for k in
   ("physical_block_size","logical_block_size","context_parallel_size","max_model_len",
    "physical_pages_per_request","logical_pages_per_request","blocks_per_physical")),
   "one initialized native layout shared across all16 FA; no silent second arena")
  self.native_geometries[(prefix,b)]=geometry
  ws=self.arena.view(b);self.workspaces[(prefix,b,pages)]=ws
  if self.diagnostic:self.native_caches[(prefix,b)]=(kc,vc,metadata.block_tables)
  if capturing:
   self.ensure_registry().capture(b,prefix,id(impl),query,output,metadata.block_tables,
    self.runner.seq_lens[:b],self.acl.get_graph_params())
   self.capture_inputs[(prefix,b)]=(tensor_identity(metadata.block_tables),tensor_identity(self.runner.seq_lens[:b]))
  self.a.record_attention_compute_start()
  sample=self.snapshot(prefix,b,query.device) if self.diagnostic else None
  if sample:sample.before(query)
  # Zero is author meanOFF, NOT a meanON cache or claimed equivalence.
  zero=ws.mean_off # Dedicated guarded FP32 meanOFF, never BF16 output alias.
  c.require(zero.dtype==self.t.float32,"registered FP32 compensation meanOFF boundary")
  zero.zero_()
  def copied():
   layer=self.bindings[prefix]["layer"]
   c.require(layer not in self.forward_order and (not self.forward_order or layer>self.forward_order[-1]),
    "actual enqueued original distinct-output copy before next shared arena FA")
   self.forward_order.append(layer)
  result,ws,selected,alpha,channels=post.author_forward(self.t,self.arena,b,query,kc,vc,
   metadata.block_tables,self.runner.seq_lens[:b],output,zero,copied)
  if sample:sample.after(output[:b].view(b,6,256),ws,selected,alpha,channels)
  return result
 def end(self,ctx):
  c.require(self.current is not None,"actual original model boundary")
  current=self.current;fa_refs={}
  if current["dummy"]:
   if self.forward_order:c.require(tuple(self.forward_order)==common.FA,"all16 actual capture/warmup original output copies")
   self.model_entries+=1;self.current=None;return
  if ctx.cudagraph_runtime_mode==self.Mode.FULL:
   c.require(current["updated"] and len(self.replay_calls)==1,"actual original FULL ACL and POST both returned")
   if self.diagnostic:
    self.t.npu.current_stream().synchronize()
    from ann_model_oracle import check_layer
    observed={};b=current["batch"]
    captures=self.registry.complete(b,self.acl.get_graph_params())
    # Every pointer precondition is checked before any layer oracle, not after
    # partially publishing a turn. FULL replay never re-enters selected_forward.
    for prefix in self.registry.bindings:
     c.require((prefix,b) in self.native_caches and prefix in ctx.attn_metadata,
      "actual current truebatch native cache and keyed metadata, not last captured bucket")
     table=self.native_caches[(prefix,b)][2];current_table=ctx.attn_metadata[prefix].block_tables
     c.require(post.pointer(table)==post.pointer(current_table)==captures[prefix]["table"] and
      self.capture_inputs.get((prefix,b))==(tensor_identity(current_table),tensor_identity(self.runner.seq_lens[:b])),
      "actual current-batch native table/current metadata/capture pointer identity before full oracle")
     c.require((prefix,b) in self.native_geometries,"actual current-batch initialized geometry before oracle")
     geometry=self.native_geometries[(prefix,b)];key,value,_=self.native_caches[(prefix,b)]
     c.require(geometry["current_table_identity"]==list(tensor_identity(current_table)) and
      geometry["actual_native_key_identity"]==list(tensor_identity(key)) and
      geometry["actual_native_value_identity"]==list(tensor_identity(value)) and
      geometry["logical_pages_per_request"]==int(current_table.shape[1]),
      "current actual geometry pointers/width match retained full native K/V and metadata")
    for prefix in self.registry.bindings:
     sample=self.snapshots[(prefix,current["batch"])]
     raw=sample.device_observation(current["actual_epoch"]);observed[prefix]=raw
     result=check_layer(self.t,sample,self.native_caches[(prefix,b)],current["frame"],
      current["full_topology"][prefix],prefix,current["actual_epoch"],
      os.environ["QWEN36_SPARQ_MODEL_TRACE_ROOT"],self.core,self.native_geometries[(prefix,b)])
     result.update(raw,model_epoch=current["actual_epoch"],arm="candidate")
     fa_refs[str(self.bindings[prefix]["layer"])]=self.emit("actual-full-ann-oracle",result)
    record=self.registry.end_replay(self.replay_calls,observed)
    # Registry independently denies model acceptance; never override a grant.
    c.require(record.get("model_ready") is False,"noPA registry record cannot grant model-ready")
    turn={**self.budget(),**record,"ACL_replays":self.replay_calls,"arm":self.arm,
     "completed":True,"full64_layer_numeric_verified":False,"model_ready":False}
    self.emit("actual-full-turn",turn)
   else:
    # Formal has no tensor .item/.cpu/guards/JSON per token. Source/state
    # admission was performed outside timing. No diagnostic counters fabricated.
    self.registry.complete(current["batch"],self.acl.get_graph_params())
    c.require(self.registry.active["POST_original_returned"],"actual formal original POST returned")
    self.registry.active=None
  if self.diagnostic:
   events=self.gdn_observer.end(ctx);gdn_refs={}
   for event in events:gdn_refs[str(event["layer"])]=self.emit("actual-gdn-state",event)
   self.emit("actual-model-boundary",dict(epoch=current["actual_epoch"],batch=self.runner.input_batch.num_reqs,
    runtime="FULL" if ctx.cudagraph_runtime_mode==self.Mode.FULL else "NONE",
    request_ids=current["request_ids"],gdn=gdn_refs,mixed_FA_records=self.mixed_fa,
    native_request_rows=self.pending_scheduler,fa=fa_refs,original_PA_post_update_finished=True,
    original_POST_noPA_is_author_ANN=True,mean_configuration=False,
    all_active_GDN_dense_equivalence_not_claimed=True,model_ready=False))
  else:
   self.formal_turns+=1;self.last_ctx=ctx
   if ctx.cudagraph_runtime_mode==self.Mode.FULL:
    self.formal_full_turns+=1;self.formal_replays+=len(self.replay_calls);self.formal_post_updates=self.post_updates
    k=str(current["batch"]);self.formal_batches[k]=self.formal_batches.get(k,0)+1
  self.model_entries+=1;self.current=None

"""Candidate PA adapter for actual stock ACL FULL graph registry.
No model monkeypatch installed by import. Original selector/GraphTokenWorkspace
math is unchanged. This is a source adapter, NOT FULL-model authority.
"""
from __future__ import annotations
import math
FA=tuple(range(3,64,4))
def require(ok,why):
 if not ok:raise ValueError(why)
def clamped_host_lengths(values,batch,capacity):
 require(type(values) is list and len(values)==batch and batch in range(1,17) and
  type(capacity) is int and capacity>0 and all(type(n) is int and 0<n<=capacity for n in values),
  "true nonempty known CPU topology; no virtual padded/empty rows")
 return [min(n,128) for n in values]
class CaptureRegistry:
 """Actual FA prefix and task ordinal, never dict zip over64 metadata layers.
 Objects below must be the originals from installed GraphParams.
 """
 def __init__(self,bindings):
  require(type(bindings) is dict and len(bindings)==16 and
   {row["layer"] for row in bindings.values()}==set(FA) and
   all(type(name) is str and name and type(row["impl_id"]) is int and row["impl_id"]>0 for name,row in bindings.items()) and
   len({row["impl_id"] for row in bindings.values()})==16,"actual16FA unique full prefixes/impl identities")
  self.bindings=bindings;self.captures={};self.epoch=0;self.queued=None;self.update_counts={}
 def add(self,batch,prefix,impl_id,params,param,handle,event,owner):
  require(batch in range(1,17) and prefix in self.bindings and
   self.bindings[prefix]["impl_id"]==impl_id and len(param)==9,"exact captured prefix/trueB/9tuple")
  ordinal=len(params.attn_params[batch])
  require(len(params.handles[batch])==len(params.events[batch])==ordinal,"original task/event/parameter alignment BEFORE append")
  records=self.captures.setdefault(batch,{})
  require(prefix not in records and len(records)==ordinal,"one exact captured layer ordinal, no unknown predecessor")
  params.attn_params[batch].append(param);params.handles[batch].append(handle);params.events[batch].append(event)
  records[prefix]=dict(ordinal=ordinal,param=param,handle=handle,event=event,owner=owner,updated_epoch=0)
  return ordinal
 def adopt_existing(self,batch,prefix,impl_id,params,ordinal):
  require(batch in range(1,17) and prefix in self.bindings and self.bindings[prefix]["impl_id"]==impl_id,
   "actual original dense capture binding")
  records=self.captures.setdefault(batch,{})
  require(prefix not in records and len(records)==ordinal and
   len(params.attn_params[batch])==len(params.handles[batch])==len(params.events[batch])==ordinal+1,
   "actual original native dense PA ordinal; no append or duplicate task")
  param=params.attn_params[batch][ordinal];require(len(param)==9,"actual original dense PA9tuple")
  records[prefix]=dict(ordinal=ordinal,param=param,handle=params.handles[batch][ordinal],event=params.events[batch][ordinal],owner=None,updated_epoch=0)
  return ordinal
 def complete(self,batch,params):
  records=self.captures.get(batch,{})
  require(set(records)==set(self.bindings) and
   len(params.attn_params[batch])==len(params.handles[batch])==len(params.events[batch])==16,"actual complete16FA capture")
  for row in records.values():
   i=row["ordinal"]
   require(params.attn_params[batch][i] is row["param"] and params.handles[batch][i] is row["handle"] and
    params.events[batch][i] is row["event"],"captured stock record/handle/event identity unchanged")
  return records
 def queue(self,batch,params,host_topology,frame):
  self.complete(batch,params)
  require(self.queued is None and type(frame) is list and len(frame)==batch and
   len({r["rid"] for r in frame})==batch and
   all(type(r["generation"]) is int and r["generation"]>0 and type(r["slot"]) is int and 0<=r["slot"]<16 for r in frame),
   "real current generation/request leases, no dummy authority or overlapping async replay")
  require(type(host_topology) is dict and set(host_topology)==set(self.bindings) and
   all(type(v) is list and len(v)==batch for v in host_topology.values()),"metadata explicitly keyed16 actualFA prefixes")
  values=list(host_topology.values());require(all(v==values[0] for v in values),"FA native topology disagrees in one actual network turn")
  self.epoch+=1;self.queued=dict(batch=batch,epoch=self.epoch,topology=host_topology,frame=frame)
  return self.epoch
 def update_one(self,batch,prefix,params):
  require(self.queued is not None and self.queued["batch"]==batch,"only default stock POST-enqueue update for same actual trueB")
  records=self.complete(batch,params);record=records[prefix]
  require(record["updated_epoch"]<self.queued["epoch"],"exactly one update per FA/current replay")
  return record,self.queued["topology"][prefix],self.queued["epoch"]
 def mark(self,prefix,epoch):
  require(self.queued is not None and epoch==self.queued["epoch"],"fresh current replay epoch")
  self.captures[self.queued["batch"]][prefix]["updated_epoch"]=epoch
 def finish(self,params):
  require(self.queued is not None,"actual queued replay")
  q=self.queued;records=self.complete(q["batch"],params)
  require(all(x["updated_epoch"]==q["epoch"] for x in records.values()),"all16 fresh event/task updates before completed model turn")
  self.update_counts[q["batch"]]=self.update_counts.get(q["batch"],0)+1;self.queued=None
  return dict(batch=q["batch"],epoch=q["epoch"],request_generations=q["frame"],fresh_FA_updates=16)
def make_stock_pa(core,torch,torch_npu,acl,weak_ref_tensors,extra_context,registry,prefix,impl_id,batch,capacity):
 """No device initialization here; caller owns validated TP4 process and admission.
 Reuses exact core.NativePAHost guarded CPUint32 metadata substrate only.
 """
 class StockPAHost(core.NativePAHost):
  def execute(self,query,key,value,table,output):
   core.host_pa_layout(torch,self.context.value,self.batch)
   require(self.epoch>0,"known CPU context before stock capture/eager warmup")
   args=dict(query=query,key_cache=key,value_cache=value,num_kv_heads=1,num_heads=6,
    scale_value=1/math.sqrt(256),block_table=table,context_lens=self.context.value,out=output)
   if not extra_context.capturing:
    require(self.handle is None,"captured candidate PA must use stock replay, never a second eager native call")
    torch_npu._npu_paged_attention(**args)
    return output
   require(self.handle is None and self.params is None,"one stock FULL capture for layer/trueB")
   params=acl.get_graph_params();require(params is not None and batch in params.attn_params,"stock capture bucket initialized")
   workspace=torch_npu._npu_paged_attention_get_workspace(**args)
   stream=torch.npu.current_stream();event=torch.npu.ExternalEvent()
   event.wait(stream);event.reset(stream)
   torch.npu.graph_task_group_begin(stream)
   torch_npu._npu_paged_attention(**args,workspace=workspace)
   handle=torch.npu.graph_task_group_end(stream)
   param=(weak_ref_tensors(query),weak_ref_tensors(key),weak_ref_tensors(value),1,6,1/math.sqrt(256),
    table,self.context.value,weak_ref_tensors(output))
   registry.add(batch,prefix,impl_id,params,param,handle,event,self)
   acl.update_graph_params_workspaces(batch,workspace)
   self.params=param;self.handle=handle;self.event=event;self.workspace={"value":workspace}
   return output
  def update_stock(self,update_stream,host_lengths,record,epoch):
   require(record["owner"] is self and record["param"] is self.params and record["handle"] is self.handle and
    record["event"] is self.event,"actual captured candidate/stock owner identity")
   self.set_lengths(host_lengths)
   query,key,value,num_kv,num_heads,scale,table,context,output=self.params
   require(context is self.context.value and num_kv==1 and num_heads==6 and scale==1/math.sqrt(256),"original9tuple geometry/context identity")
   args=dict(query=query,key_cache=key,value_cache=value,num_kv_heads=num_kv,num_heads=num_heads,
    scale_value=scale,block_table=table,context_lens=self.context.value,out=output)
   # Same default installed post-replay update stream protocol. No .cpu/.item
   # on device metadata; known host lengths came from original CPU metadata.
   workspace=torch_npu._npu_paged_attention_get_workspace(**args)
   torch.npu.graph_task_update_begin(update_stream,self.handle)
   torch_npu._npu_paged_attention(**args,workspace=workspace)
   torch.npu.graph_task_update_end(update_stream)
   self.event.record(update_stream)
   self.workspace={"value":workspace};self.updated_epoch=epoch
 return StockPAHost(batch,128,capacity)
def update_candidate_graph(torch,acl,registry,update_stream,forward_context,num_tokens):
 """Called by an opt-in source-bound replacement of backend static update ONLY
 for admitted candidate/nondraft/DecodeOnly/FULL branch. Other branches original.
 Must remain in installed NPUModelRunner's default post-run_model call position.
 """
 params=acl.get_graph_params();registry.complete(num_tokens,params)
 require(registry.queued is not None and registry.queued["batch"]==num_tokens,"fresh current trueB queue before native update")
 with torch.npu.stream(update_stream):
  for prefix in registry.bindings:
   require(prefix in forward_context.attn_metadata,"actual captured FA metadata prefix missing, not a zip fallback")
   meta=forward_context.attn_metadata[prefix]
   require(meta.num_actual_tokens==num_tokens and meta.num_prefills==0 and
    list(meta.seq_lens_list)==registry.queued["topology"][prefix],"actual same queued trueB/full native CPU topology")
   record,lengths,epoch=registry.update_one(num_tokens,prefix,params)
   record["owner"].update_stock(update_stream,lengths,record,epoch);registry.mark(prefix,epoch)
 return registry.finish(params)
def record_selector_topology(torch,workspace,runner_lengths,table):
 """Device-only ops inside captured original FA forward_impl, executed again
 by stock replay. Full native lengths for selector, never min(n,128).
 Invalid padded page columns map to valid first live page before gather.
 """
 require(runner_lengths.device.type==table.device.type=="npu" and runner_lengths.dtype==torch.int32 and
  table.dtype in (torch.int32,torch.int64) and runner_lengths.shape==(workspace.batch,) and
  table.shape==(workspace.batch,workspace.max_pages),"real persistent native device table/lens captured input geometry")
 workspace.lengths.copy_(runner_lengths)
 page_index=torch.arange(workspace.max_pages,dtype=torch.int64,device=table.device)
 live_pages=torch.div(runner_lengths.to(torch.int64)+127,128,rounding_mode="floor")
 safe=torch.where(page_index[None,:]<live_pages[:,None],table,table[:,:1]).to(torch.int64)
 workspace.rows.copy_(safe)
 return workspace.rows,workspace.lengths

"""Actual installed v0.23 eager model bridge. Default OFF, no allocator eviction.
Only rank32/budget128/meanOFF exact paper-GQA-probability route is model candidate.
FULL/model graph remains unsupported and fail-closed; original mixed prefill dense.
"""
from __future__ import annotations
import functools,json,math,os,threading,time
from pathlib import Path
from receipt import *
from sparq_token_v4.core import HEADS,DIM,BLOCK,SLOTS,GraphTokenWorkspace
_PATCHED=False
_LOCAL=threading.local()
_MODE="diagnostic"
class RequestLedger:
 """Real runner request object identities + finished generations, never batch indices."""
 def __init__(self,capacity=16):
  self.capacity=capacity;self.live={};self.generations={};self.active=[];self.steps=0
 def finish(self,ids):
  for rid in ids:
   self.live.pop(rid,None)
 def prepare(self,rows,finished=()):
  self.finish(finished);require(type(rows) is list and 0<len(rows)<=self.capacity,"actual model request batch capacity")
  ids=[r["rid"] for r in rows];require(len(set(ids))==len(ids),"duplicate actual request identity")
  prepared=[]
  for row in rows:
   rid=row["rid"];require(type(rid) is str and rid and type(row["computed"]) is int and row["computed"]>=0 and
     type(row["scheduled"]) is int and row["scheduled"]>0 and type(row["object_id"]) is int and row["object_id"]>0,
     "actual request object/computed/scheduled fields")
   previous=self.live.get(rid)
   if previous is None:
    used={r["slot"] for r in self.live.values()};available=sorted(set(range(self.capacity))-used)
    require(available,"actual paused request leases exceed admitted16; never steal a live slot")
    generation=self.generations.get(rid,0)+1;self.generations[rid]=generation
    previous=dict(rid=rid,generation=generation,slot=available[0],object_id=row["object_id"],computed=row["computed"])
    self.live[rid]=previous
   require(previous["object_id"]==row["object_id"] and row["computed"]>=previous["computed"],
    "request-ID ABA or rollback/recompute requires explicit finish/new generation")
   previous["computed"]=row["computed"]
   prepared.append(dict(previous,scheduled=row["scheduled"],expected_length=row["computed"]+row["scheduled"]))
  self.active=prepared;self.steps+=1;return [dict(x) for x in prepared]
 def decode(self,lengths):
  require(len(lengths)==len(self.active) and all(type(n) is int and n>0 for n in lengths),"actual nonempty decode sequence lengths")
  require(all(x["scheduled"]==1 and x["expected_length"]==n for x,n in zip(self.active,lengths)),
   "actual query rows/runner lease/native seq lengths disagree; no batch-row alias")
  return [dict(x,native_length=n) for x,n in zip(self.active,lengths)]
def _event(out,rank,kind,data):
 if _MODE=="formal":return None
 require(out.is_absolute() and out.is_dir() and out.resolve()==out and not out.is_symlink(),"MAIN new owned model trace root")
 path=out/("rank%d-pid%d-%s-%d.json"%(rank,os.getpid(),kind,time.time_ns()))
 return write_new(path,{"schema":"sparq.actual-model-seam/v4","rank":rank,"pid":os.getpid(),"kind":kind,
  "npu_executed":None,"model_ready":False,"graph_model_verified":False,"matched1024_e2e_verified":False,**data})
def install_from_env():
 global _PATCHED,_MODE
 if os.environ.get("QWEN36_SPARQ_TOKEN_ENABLED")!="1":return {"default_enabled":False,"model_executed":False}
 _MODE=os.environ.get("QWEN36_SPARQ_MODEL_MODE","diagnostic")
 require(_MODE in ("diagnostic","formal"),"explicit diagnostic/formal model instrumentation mode")
 require(not _PATCHED,"single opt-in patch install, never chain unknown existing monkeypatch")
 path=Path(os.environ.get("QWEN36_SPARQ_SOURCE_MANIFEST",""));digest=os.environ.get("QWEN36_SPARQ_SOURCE_SHA")
 source,files=source_identity(ROOT,path,digest,"runtime")
 authority=bound(os.environ.get("QWEN36_SPARQ_NUMERIC_AUTHORITY",""),os.environ.get("QWEN36_SPARQ_NUMERIC_AUTHORITY_SHA"))
 checked=load(authority)
 require(checked.get("schema")=="sparq.complete-token-component/v4" and checked.get("source_manifest")==source and
  checked.get("source_files")==files and checked.get("MAIN_original_operation_authority_verified") is True and
  checked.get("physical_NPU_process_authority_verified") is True and checked.get("owned_stop_retention_verified") is True and
  checked.get("actual_numerical_steps")==20480 and checked.get("cases")==128,
  "actual complete original20-source numeric authority mandatory before model opt-in; no fixture/failure/partial")
 if _MODE=="formal":
  diag_ref=bound(os.environ.get("QWEN36_SPARQ_MODEL_DIAGNOSTIC_AUTHORITY",""),os.environ.get("QWEN36_SPARQ_MODEL_DIAGNOSTIC_AUTHORITY_SHA"))
  diag=load(diag_ref)
  require(diag.get("schema")=="sparq.actual-tp4-diagnostic/v4" and diag.get("source_manifest")==source and
   diag.get("source_files")==files and diag.get("numeric_authority")==authority and
   diag.get("MAIN_original_operation_authority_verified") is True and
   diag.get("actual_TP4_64_layer_model_execution_verified") is True and
   diag.get("diagnostic_generation_slots_verified") is True and
   all(type(diag.get(k)) is dict and set(diag[k])=={"path","sha256"} for k in ("original_terminal","actual_host")),
   "formal mode requires fresh original actual same-source TP4 diagnostic consumer, not kernel-only PASS")
  for k in ("original_terminal","actual_host"):bound(diag[k]["path"],diag[k]["sha256"])
 trace=Path(os.environ.get("QWEN36_SPARQ_MODEL_TRACE_ROOT",""))
 require(trace.is_absolute() and trace.is_dir() and trace.resolve()==trace and not trace.is_symlink(),"MAIN separate new owned model trace root")
 import torch,torch_npu
 import vllm_ascend.attention.attention_v1 as attention
 import vllm_ascend.worker.model_runner_v1 as runner_module
 from vllm.distributed import get_tensor_model_parallel_rank,get_tensor_model_parallel_world_size
 for alias,module in (("attention_v1",attention),("model_runner_v1",runner_module)):
  ref=MODEL_SOURCES[alias]["runtime_ref"]
  require(str(Path(module.__file__))==ref["path"] and sha(Path(module.__file__))==ref["sha256"],"actual imported model seam changed")
 original_prepare=runner_module.NPUModelRunner._prepare_inputs
 original_update=runner_module.NPUModelRunner._update_states
 original_forward=attention.AscendAttentionBackendImpl.forward_impl
 require(original_prepare.__module__==runner_module.__name__ and original_update.__module__==runner_module.__name__ and
  original_forward.__module__==attention.__name__,"unknown previous monkeypatch; no chaining/stealing native scope")
 def admitted(runner):
  require(runner.model_config.enforce_eager is True and runner.speculative_config is None and
   not runner.use_cp and not runner.use_async_scheduling and not runner.enable_enpu and
   runner.vllm_config.parallel_config.tensor_parallel_size==4 and runner.max_num_reqs<=16,
   "model scope: TP4/eager/no CP/spec/async/ENPU/max16 only; original dense comparator must match")
 def ledger(runner):
  if not hasattr(runner,"_sparq_real_request_ledger"):runner._sparq_real_request_ledger=RequestLedger(16)
  return runner._sparq_real_request_ledger
 @functools.wraps(original_update)
 def update(runner,scheduler_output):
  result=original_update(runner,scheduler_output)
  if hasattr(runner,"_sparq_real_request_ledger"):ledger(runner).finish(list(scheduler_output.finished_req_ids))
  return result
 @functools.wraps(original_prepare)
 def prepare(runner,scheduler_output,num_scheduled_tokens):
  admitted(runner);result=original_prepare(runner,scheduler_output,num_scheduled_tokens)
  ids=list(runner.input_batch.req_ids[:runner.input_batch.num_reqs])
  rows=[dict(rid=rid,object_id=id(runner.requests[rid]),computed=int(runner.input_batch.num_computed_tokens_cpu[i]),
    scheduled=int(scheduler_output.num_scheduled_tokens[rid])) for i,rid in enumerate(ids)]
  frame=ledger(runner).prepare(rows)
  _LOCAL.runner=runner;_LOCAL.frame=frame
  if _MODE=="diagnostic":_event(trace,get_tensor_model_parallel_rank(),"prepare",{"source_manifest":source,"numeric_authority":authority,
    "frame":frame,"actual_request_object_ids":{rid:id(runner.requests[rid]) for rid in ids}})
  return result
 @functools.wraps(original_forward)
 def forward(impl,query,key,value,kv_cache,metadata,output):
  rank=get_tensor_model_parallel_rank()
  require(get_tensor_model_parallel_world_size()==4 and rank in range(4),"actual TP4 rank admission")
  require(type(impl) is attention.AscendAttentionBackendImpl and impl.num_heads==HEADS and impl.num_kv_heads==1 and
   impl.head_size==DIM and math.isclose(impl.scale,1/math.sqrt(DIM),rel_tol=0,abs_tol=1e-12) and
   not impl.enable_c8_quant and not impl.enable_hamming_sparse and impl.sinks is None and impl.sliding_window is None and
   impl.alibi_slopes is None and not impl.is_kv_producer and impl.kv_sharing_target_layer_name is None,
   "exact BF16 local6/1/256 unquantized ordinary full attention scope; no GDN/C8/sink/CP/KV sharing")
  require(not attention._EXTRA_CTX.capturing,"FULL attention task-group/replay is unsupported, never pretend graph model support")
  if metadata.attn_state!=attention.AscendAttentionState.DecodeOnly:
   result=original_forward(impl,query,key,value,kv_cache,metadata,output)
   if _MODE=="diagnostic":_event(trace,rank,"dense-prefill-fallback",{"source_manifest":source,"state":metadata.attn_state.name,
     "num_actual_tokens":metadata.num_actual_tokens,"mixed_batch_sparse_transform":False})
   return result
  runner=getattr(_LOCAL,"runner",None);require(runner is not None,"actual runner request frame mandatory")
  admitted(runner);kc,vc=impl.key_cache,impl.value_cache
  require(kc.data_ptr()==kv_cache[0].data_ptr() and vc.data_ptr()==kv_cache[1].data_ptr() and kc.dtype==vc.dtype==query.dtype==torch.bfloat16 and
   tuple(kc.shape[1:])==(BLOCK,1,DIM) and kc.shape==vc.shape and kc.device.type=="npu" and
   torch_npu.get_npu_format(kc)==torch_npu.get_npu_format(vc)==2,"actual original ND native allocator backing, not replacement/double pool")
  lengths=list(metadata.seq_lens_list);frame=ledger(runner).decode(lengths);batch=len(frame)
  require(batch==query.shape[0]==metadata.num_actual_tokens and tuple(query.shape[1:])==(HEADS,DIM) and
    metadata.causal is True and metadata.num_prefills==0,"actual decode one query/request, no padded/empty/mixed reinterpretation")
  table=metadata.block_tables.detach().cpu().tolist()
  rows=[list(map(int,row[:(n+BLOCK-1)//BLOCK])) for row,n in zip(table,lengths)]
  require(len(rows)==batch and all(len(row)==(n+BLOCK-1)//BLOCK and all(0<=p<kc.shape[0] for p in row) for row,n in zip(rows,lengths)),
   "actual live block-table prefix, no invalid padded page gather")
  max_pages=metadata.block_tables.shape[1]
  if not hasattr(impl,"_sparq_token_workspaces"):impl._sparq_token_workspaces={}
  key=(batch,max_pages);workspace=impl._sparq_token_workspaces.get(key)
  if workspace is None:
   workspace=GraphTokenWorkspace(kc.device,batch,max_pages,128,32,1);impl._sparq_token_workspaces[key]=workspace
  safe_rows=[row+[row[0]]*(max_pages-len(row)) for row in rows]
  workspace.rows.copy_(torch.tensor(safe_rows,dtype=torch.int64,device=kc.device))
  workspace.lengths.copy_(torch.tensor(lengths,dtype=torch.int32,device=kc.device))
  # Original forward already performed exactly one native writer/notify. Do not write KV again.
  attention.record_attention_compute_start()
  got,selected,alpha,channels=workspace.run(query,kc,vc,None,reallocation=False,variant="paper-gqa-probability")
  if _MODE=="diagnostic":require(workspace.guards(),"actual model selected scratch/workspace native guard changed")
  output[:batch].copy_(got)
  if _MODE=="diagnostic":_event(trace,rank,"sparse-decode",{"source_manifest":source,"numeric_authority":authority,"frame":frame,
    "native_cache_pointers":[kc.data_ptr(),vc.data_ptr()],"native_cache_backing_bytes":kc.untyped_storage().nbytes()+vc.untyped_storage().nbytes(),
    "rows":rows,"lengths":lengths,"scratch_bytes":workspace.bytes,"all_allocated_workspace_bytes":sum(w.bytes for w in impl._sparq_token_workspaces.values()),
    "actual_selected_support":selected.detach().cpu().tolist(),"actual_channels":channels.detach().cpu().tolist(),"native_KV_replaced":False,"native_writer_repeated":False,
    "mean_correction":False,"paper_selector_variant":"paper-gqa-probability","kernel_graph_does_not_imply_model_graph":True})
  return output
 runner_module.NPUModelRunner._update_states=update
 runner_module.NPUModelRunner._prepare_inputs=prepare
 attention.AscendAttentionBackendImpl.forward_impl=forward
 _PATCHED=True
 return {"installed":True,"instrumentation_mode":_MODE,"formal_timing_debug_off":_MODE=="formal","source_manifest":source,"numeric_authority":authority,"model_ready":False,"graph_model_verified":False}
def main():
 import argparse
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--source-audit-only",action="store_true")
 p.add_argument("--source-manifest",type=Path);p.add_argument("--source-manifest-sha256");a=p.parse_args()
 if not a.source_audit_only:
  print(json.dumps({"default_enabled":False,"model_executed":False,"model_ready":False,"graph_model_verified":False}));return
 sr,files=source_identity(ROOT,a.source_manifest,a.source_manifest_sha256)
 print(json.dumps({"source_manifest":sr,"files":files,"model_executed":False,"model_ready":False}))
if __name__=="__main__":main()

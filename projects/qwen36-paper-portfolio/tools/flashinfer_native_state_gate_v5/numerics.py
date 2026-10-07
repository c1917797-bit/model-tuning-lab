"""MAIN-only actual full matrix producer; no Torch import on software/default path."""
from pathlib import Path
import hashlib,json,math,os,time
from contract import *
from oracle import cpu_double
def raw_tensors(value):
 if isinstance(value,dict):return {k:raw_tensors(v) for k,v in value.items()}
 if isinstance(value,(list,tuple)):return [raw_tensors(v) for v in value]
 if hasattr(value,"detach"):return value.detach().cpu()
 return value
def checkpoint(torch,out,case,step,raw):
 p=out/("raw-"+case+"-step"+str(step)+".pt")
 require(p.resolve().parent==out.resolve() and not p.exists() and not p.is_symlink(),"exact new owned raw leaf")
 with p.open("xb") as stream:torch.save(raw_tensors(raw),stream);stream.flush();os.fsync(stream.fileno())
 return p,{"file":p.name,"sha256":sha(p),"bytes":p.stat().st_size,"retained":True}
def delete_owned(p,out):
 require(p.resolve().parent==out.resolve() and p.is_file() and not p.is_symlink(),"exact owned passed checkpoint")
 p.unlink()
def per_head(got,expected):
 av=got.detach().cpu().float().reshape(-1,D).tolist();ev=expected.reshape(-1,D).tolist()
 return [metric(a,e) for a,e in zip(av,ev)]
def input_snapshot(w):
 return [x.value.clone() for x in (w.q,w.k,w.v,w.mask,*[x for part in w.parts for x in part[:3]])]
def inputs_equal(torch,w,before):
 values=[x.value for x in (w.q,w.k,w.v,w.mask,*[x for part in w.parts for x in part[:3]])]
 return all(torch.equal(a,b) for a,b in zip(values,before))
def run_case(torch,device,out,batch,qwidth,mode,trial,save,deadline):
 from native import NativeStates
 book=SlotBook(batch);total=book.total;w=NativeStates(torch,batch,qwidth,device)
 # Actual stable slot backing with two guard regions, separate CPU BF16 oracle.
 cache_shape=(total,1,N,D)
 from native import Guarded
 kc=Guarded(torch,cache_shape,torch.bfloat16,device);vc=Guarded(torch,cache_shape,torch.bfloat16,device)
 kc.value.zero_();vc.value.zero_();gold_k=torch.zeros(cache_shape,dtype=torch.bfloat16);gold_v=torch.zeros_like(gold_k)
 generator=torch.Generator(device="cpu").manual_seed(250101005+batch*100+qwidth*10+trial)
 def noise(shape):return (torch.randn(shape,generator=generator)*.05).to(torch.bfloat16)
 for slot,row in enumerate(book.rows):
  length=row["length"];key=noise((length,D));value=noise((length,D))
  gold_k[slot,0,:length]=key;gold_v[slot,0,:length]=value
 kc.value.copy_(gold_k);vc.value.copy_(gold_v)
 lengths=[[0]*qwidth for _ in range(batch)]
 q=noise((batch,H,qwidth,D)).to(device)
 w.populate(q,kc.value[:batch],vc.value[:batch],lengths);w.warm_workspace()
 for _ in range(3):w.run()
 torch.npu.synchronize();graph=None
 if mode=="graph":
  graph=torch.npu.NPUGraph()
  with torch.npu.graph(graph):w.run()
  torch.npu.synchronize()
 cache_identity=(kc.identity,vc.identity)
 case={"batch":batch,"query_width":qwidth,"mode":mode,"trial":trial,"status":"running","steps":[],
   "actual_slot_backing_bytes":kc.backing.untyped_storage().nbytes()+vc.backing.untyped_storage().nbytes(),
   "workspace_and_guard_bytes":w.bytes(),"vllm_scheduler_or_model_bound":False}
 pending=None;primary=None;raw={"stage":"initial","native_cache_k":kc.value,"native_cache_v":vc.value}
 def persist():save(case)
 try:
  for i in range(STEPS):
   require(time.monotonic()<deadline,"fixed original phase/cutoff, no retry")
   before_k=kc.value.clone();before_v=vc.value.clone();old_rows=[dict(x) for x in book.rows]
   frame=book.advance(batch,qwidth,i);touched=set()
   for entry in frame["writes"]:
    slot=entry["slot"];touched.add(slot)
    if entry["reset"]:
     kc.value[slot].zero_();vc.value[slot].zero_();gold_k[slot].zero_();gold_v[slot].zero_()
    else:
     start=entry["start"];count=entry["count"];key=noise((count,D));value=noise((count,D))
     kc.value[slot,0,start:start+count].copy_(key);vc.value[slot,0,start:start+count].copy_(value)
     gold_k[slot,0,start:start+count]=key;gold_v[slot,0,start:start+count]=value
   slot_ids=torch.tensor(frame["slots"],dtype=torch.int64,device=device)
   visible=visible_lengths(frame,qwidth)
   q_cpu=noise((batch,H,qwidth,D))
   if i:
    # Query feedback comes from previous ORIGINAL CPU oracle, not candidate.
    q_cpu=(q_cpu.float()+previous.float()*.125).to(torch.bfloat16)
   query=q_cpu.to(device);keys=kc.value.index_select(0,slot_ids);values=vc.value.index_select(0,slot_ids)
   raw=dict(stage="before-native",step=i+1,frame=frame,query=query,keys=keys,values=values,
      cache_before=(before_k,before_v),cache_after=(kc.value,vc.value),expected_cache=(gold_k,gold_v))
   w.populate(query,keys,values,visible);snap=input_snapshot(w)
   if graph is None:w.run()
   else:graph.replay()
   torch.npu.synchronize()
   expected,expected_lse=cpu_double(query,keys,values,visible);previous=expected.to(torch.bfloat16)
   got=w.got.detach().cpu();glse=w.got_lse.detach().cpu();native_full=w.out.value.detach().cpu();native_lse=w.lse.value[...,0].detach().cpu()
   valid=torch.tensor(visible)>0;domain=valid[:,None,:].expand(batch,H,qwidth)
   metrics=per_head(got,expected);native_metrics=per_head(torch.where(domain[...,None],native_full,torch.zeros_like(native_full)),expected)
   # Do not alter original native undefined values; only defined native rows
   # participate in native control comparisons. They are retained in raw.
   diff=(glse[domain].double()-expected_lse[domain]).abs()
   lse_error=float(diff.max().item()) if diff.numel() else 0.
   native_lse_diff=(native_lse[domain].double()-expected_lse[domain]).abs()
   native_lse_error=float(native_lse_diff.max().item()) if native_lse_diff.numel() else 0.
   partial_finite=True
   for outputs,lse,present in zip(*w.sanitized):
    defined=present
    partial_finite &= bool(torch.isfinite(outputs[defined]).all().item() and torch.isfinite(lse[defined]).all().item())
   untouched=all(torch.equal(kc.value[s],before_k[s]) and torch.equal(vc.value[s],before_v[s]) for s in range(total) if s not in touched)
   tail_zero=all(torch.equal(kc.value[s,0,book.rows[s]["length"]:],gold_k[s,0,book.rows[s]["length"]:].to(device)) and
     torch.equal(vc.value[s,0,book.rows[s]["length"]:],gold_v[s,0,book.rows[s]["length"]:].to(device))
      for s in range(total) if book.rows[s]["generation"]>old_rows[s]["generation"])
   row={"step":i+1,"frame":frame,"per_query_head_metrics":metrics,"native_full_per_query_head_metrics":native_metrics,
     "lse_max_abs":lse_error,"native_lse_max_abs":native_lse_error,
     "guards":w.guards() and kc.intact() and vc.intact(),"pointers":w.pointers() and kc.pointer() and vc.pointer() and cache_identity==(kc.identity,vc.identity),
     "input_immutable":inputs_equal(torch,w,snap),"cache_bitwise":torch.equal(kc.value.cpu(),gold_k) and torch.equal(vc.value.cpu(),gold_v),
     "untouched_slots_bitwise":untouched,"reuse_zeroed":tail_zero,
     "empty_output_zero":bool((got[~domain]==0).all().item()),
     "empty_lse_neginf":bool(torch.isneginf(glse[~domain]).all().item()),
     "native_defined_finite":bool(torch.isfinite(native_full[domain]).all().item() and torch.isfinite(native_lse[domain]).all().item()),
     "partial_defined_finite":partial_finite,"merge_finite":bool(torch.isfinite(got).all().item() and torch.isfinite(glse[domain]).all().item()),
     "native_undefined_padding_rewritten":False,"actual_native_update_secondary_shape":list(w.merge_raw_lse.shape)}
   pending,rr=checkpoint(torch,out,"b%d-q%d-%s-t%d"%(batch,qwidth,mode,trial),i+1,
      dict(frame=frame,input_snapshots=snap,cache_before=(before_k,before_v),cache_after=(kc.value,vc.value),
       expected_cache=(gold_k,gold_v),query=query,native_full=w.out.value,native_lse=w.lse.value,
       partials=[(part[3].value,part[4].value) for part in w.parts],candidate=w.got,candidate_lse=w.got_lse,
       expected=expected,expected_lse=expected_lse,row=row))
   row["raw_step"]=rr;case["pending_raw_step"]=rr;persist()
   checks=("guards","pointers","input_immutable","cache_bitwise","untouched_slots_bitwise","reuse_zeroed",
       "empty_output_zero","empty_lse_neginf","native_defined_finite","partial_defined_finite","merge_finite")
   require(all(row[k] is True for k in checks) and all(m["passed"] for m in metrics) and
       all(m["passed"] for m in native_metrics) and lse_error<=LIMITS["lse_max_abs"] and native_lse_error<=LIMITS["lse_max_abs"],
       "original complete numerical/partial/native/slot/guard failure; raw retained")
   delete_owned(pending,out);pending=None;row["raw_step"]["retained"]=False
   case.pop("pending_raw_step",None);case["steps"].append(row);persist()
  case["status"]="passed";persist();return case
 except BaseException as error:
  primary=error;case.update(status="failed",error=repr(error))
  if pending is None:
   try:
    pending,rr=checkpoint(torch,out,"b%d-q%d-%s-t%d-failure"%(batch,qwidth,mode,trial),len(case["steps"])+1,raw)
    case["pending_raw_step"]=rr
   except BaseException as raw_error:case["secondary_raw_capture_error"]=repr(raw_error)
  try:persist()
  except BaseException as save_error:
   case["secondary_save_error"]=repr(save_error)
   print(json.dumps({"original_error":repr(primary),"secondary_save_error":repr(save_error)}),flush=True)
  raise
 finally:
  # No retry or reset/rewrite of a failed matrix; original raw if available retained.
  case["actual_cache_bytes"]=case["actual_slot_backing_bytes"];case["ended_ns"]=time.time_ns()
  try:persist()
  except BaseException as secondary:
   if primary is None:raise
   print(json.dumps({"original_error":repr(primary),"secondary_save_error":repr(secondary)}),flush=True)

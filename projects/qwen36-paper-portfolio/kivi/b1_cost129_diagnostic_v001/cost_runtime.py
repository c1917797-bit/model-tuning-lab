"""Only the source-bound006 worker execution boundary is adapted. No controller."""
import inspect,sys,time
from pathlib import Path
import cost_monitor as M
PROFILE=dict(schema="kivi.short-cost-profile/v1",prompt_tokens=32768,outputs=[2,2,129],
 measured_decode_appends=128,local_monitoring_only=True,added_synchronizations=0,
 both_arms=True,performance_accepted=False)
def need(v,m):
 if not v:raise ValueError(m)
def build(loader,manifest,mods,new,torch,*,rank,arm,source_ref,recipe_ref):
 refs={name:manifest["runtime_roles"][name] for name in M.TARGETS if name!="writer"}
 refs["writer"]=next(r for r in manifest["dependencies"]if r["sha256"]=="051afead07ff88b65b494bacda0b50ed575fc9669509ed0dcefc53e74407e17b")
 modules={name:(new[name]if name in new else mods[name])for name in M.TARGETS if name!="writer"}
 modules["writer"]=inspect.getmodule(mods["lifecycle"].seal_k_into)
 return M.Session(refs,modules,rank=rank,arm=arm,source_ref=source_ref,recipe_ref=recipe_ref,
                  synchronize=torch.npu.synchronize)
def precheck(loader,manifest,mods,new,torch,*,rank,source_ref):
 session=build(loader,manifest,mods,new,torch,rank=rank,arm="candidate",source_ref=source_ref,recipe_ref=None)
 session.run("N1-PYTHON-API-ONLY",lambda:None)
 value=session.finish()
 need(value["stats"]==[] and value["monitor_events"]==0,"no tensor or candidate execution in API probe")
 return dict(source_ref=source_ref,rank=rank,actual_code_bindings=value["actual_code_bindings"],
  synchronize_observed_source=value["synchronize_observed_source"],python_api_checked=True,
  candidate_executed=False,new_synchronizations=0)
class Runtime:
 def __init__(self,session,ids,publish):
  need(type(ids)is list and len(ids)==3 and len(set(ids))==3 and callable(publish),"three declared original owners")
  self.session=session;self.ids={rid:name for rid,name in zip(ids,("warmup0","warmup1","request00"))}
  self.publish=publish;self.final=None;self.report=None;self.calls=0;self.completed=set();self.last_work_phase=None
 def native_final(self,ref):
  need(self.final is None,"one actual final index");self.final=ref
 def execute(self,original,worker,scheduler):
  rows=scheduler.num_scheduled_tokens
  finished=set(scheduler.finished_req_ids)
  need(type(rows)is dict and len(rows)<=1 and set(rows)<=set(self.ids)and finished<=set(self.ids),
       "actual bounded B1 scheduler attribution only")
  if rows:
   rid,n=next(iter(rows.items()));need(type(n)is int and n>0,"actual scheduled count")
   phase=self.ids[rid]+(".prefill"if n>1 else".decode");self.last_work_phase=self.ids[rid]
  else:
   need(len(finished)<=1,"actual B1 finished-only");phase=(self.ids[next(iter(finished))]+".retire")if finished else"idle"
  # Original native method is called ONCE and its identical return/exception survives.
  result=self.session.run(phase,original,worker,scheduler);self.calls+=1;self.completed.update(finished)
  if self.final is not None:
   need(self.completed==set(self.ids)and self.report is None,"all3 native finish before one report")
   value=self.session.finish();value.update(native_final_ref=self.final,native_execute_calls=self.calls,
        declared_owner_ids=list(self.ids),finished_owner_ids=sorted(self.completed),profile=PROFILE)
   self.report=self.publish(value)
  return result
 def sample(self,original,worker,*args,**kwargs):
  need(self.last_work_phase is not None and self.report is None,"original sampling after scheduled work")
  return self.session.run(self.last_work_phase+".sample",original,worker,*args,**kwargs)
def consume_bindings(value,canary,*,rank,source_ref):
 need(canary['source_ref']==source_ref and type(canary['rank'])is int and canary['rank']==rank
  and canary['python_api_checked']is True and canary['candidate_executed']is False
  and canary['new_synchronizations']==0,'actual same-rank N1 Python API qualification')
 need(value['actual_code_bindings']==canary['actual_code_bindings']
  and value['synchronize_observed_source']==canary['synchronize_observed_source'],
  'same actual N1/worker original code objects and synchronize source')
 need(bool(canary['actual_code_bindings']) and canary['synchronize_observed_source']is not None,
  'complete original monitored code, not empty synthetic qualification')
 return dict(rank=rank,original_code_binding_replayed=True,device_time_measured=False)
def consume(value,*,rank,arm,source_ref,recipe_ref,final_ref,ids,manifest):
 expected={name:manifest['runtime_roles'][name]for name in M.TARGETS if name!='writer'}
 expected['writer']=next(r for r in manifest['dependencies']if r['sha256']=='051afead07ff88b65b494bacda0b50ed575fc9669509ed0dcefc53e74407e17b')
 need(value['source_roles']==expected,'all original source-qualified measured roles')
 need(value["schema"]==M.SCHEMA and value["rank"]==rank and value["arm"]==arm
  and value["source_ref"]==source_ref and value["recipe_ref"]==recipe_ref and value["native_final_ref"]==final_ref
  and value["profile"]==PROFILE and value["declared_owner_ids"]==ids
  and value["finished_owner_ids"]==sorted(ids),"actual same-source/rank/owner/native-final cost proof")
 need(value["new_synchronizations"]==value["tensor_snapshots"]==value["per_token_file_publications"]==0
  and value["device_kernel_time_measured"]is value["numerical_verified"]is value["performance_accepted"]is value["run_authority"]is False
  and value["timings_are_inclusive"]is value["wall_includes_probe_overhead"]is True,
  "diagnostic only; no invented device or uninstrumented performance")
 windows=value["windows"];need(windows and all(r["failed"]is False for r in windows),"whole successful original windows")
 counts={}
 for w in windows:
  need(type(w["wall_ns"])is int and w["wall_ns"]>0 and type(w["thread_cpu_ns"])is int and w["thread_cpu_ns"]>=0,
       "actual nonnegative original interval")
  counts[w["phase"]]=counts.get(w["phase"],0)+1
 for name,outputs in(("warmup0",2),("warmup1",2),("request00",129)):
  need(counts.get(name+".decode")==outputs-1 and counts.get(name+".prefill")==1
   and counts.get(name+".retire")==1,"every actual full-prefill/decode/native-retire window")
 if arm=="candidate":
  for name,outputs in(("warmup0",2),("warmup1",2),("request00",129)):
   rows={r["label"]:r for r in value["stats"]if r["phase"]==name+".decode"}
   need(rows["metadata.row_plan"]["calls"]==rows["producer.append_read"]["calls"]==
        rows["kernel.forward"]["calls"]==16*(outputs-1),"all actual16FA per decode; no sampled layer")
   sync=sum(r["calls"]for label,r in rows.items()if label.startswith("existing_sync@"))
   need(sync>=4*16*(outputs-1),"existing original completion fences not removed")
 need(value["local_events"]==["PY_START","PY_RETURN"]and value["global_events"]==["PY_UNWIND"],
      "no global call/line/instruction profiler fallback")
 return dict(rank=rank,arm=arm,counts=counts,numerical_verified=False,performance_accepted=False)

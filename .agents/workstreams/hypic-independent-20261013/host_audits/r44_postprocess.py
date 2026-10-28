"""Scope original same-image CPU parser/exact-copy/full supplemental to R44."""
import argparse,copy,json,subprocess,re
from pathlib import Path
from host_audits import r44_profile_policy as policy
from host_audits.r44_scope import scope,renewal_receipt
from host_audits.r44_profile_audit import finish,save
from host_audits import r43_profile_audit as original
from host_audits.r41_profile_trace import inventory,info_records
def check_wrapper(plan,c):
 if plan.get("r44_wrapper_sha256")!=policy.sha(__file__)or plan.get("r44_source_sha256")!=c["r44_host_source_sha256"]:raise ValueError("actual R44 CPU wrapper closure required")
 policy.check(c,root=policy.W,require_new_root=False)
def validate_metadata(rows,workers):
 if set(rows)!=set(range(4))or set(workers)!=set(range(4)):raise ValueError("four raw profiler metadata required")
 for rank,(path,info)in rows.items():
  match=re.search(r"_([0-9]+)_[0-9]{17}_ascend_pt$",path.parent.name)
  activities=info.get("config",{}).get("common_config",{}).get("activities",[])
  if not match or int(match[1])!=workers[rank]or not info.get("start_info")or not info.get("end_info")or set(activities)!={"ProfilerActivity.CPU","ProfilerActivity.NPU"}:raise ValueError("actual closed four-rank metadata/PID/activities required")
def release_only(contract,output):
 cp=Path(contract).resolve();c=json.loads(cp.read_bytes());policy.check(c,root=cp.parent,require_new_root=False)
 try:
  with scope(c):original.audit(cp,live_release=True)
 except ValueError as error:
  if str(error)!="closed bounded parsed rank trace required":raise
  tb=error.__traceback__;report=None
  while tb:
   if tb.tb_frame.f_code is original.retained.audit.__code__:report=copy.deepcopy(tb.tb_frame.f_locals["report"])
   tb=tb.tb_next
  if report is None:raise RuntimeError("actual unchanged pending-trace gate not reached")
 else:raise RuntimeError("release-only expected unparsed capture, not acceptance")
 raw=Path(c["raw_root"]);launch=json.loads((raw/"launch.json").read_bytes())
 if launch.get("r43_launch_identity")!=renewal_receipt(c):raise ValueError("actual count2 renewal receipt absent")
 start=json.loads((raw/"service-start.json").read_bytes());cid=start["container_id"]
 q=subprocess.run(["docker","inspect",cid],text=True,capture_output=True)
 if q.returncode!=1 or"No such object"not in q.stderr:raise ValueError("exact own capture still present")
 rows=info_records(raw/"profiles");workers={int(k):int(v)for k,v in report["graph"]["workers"].items()}
 validate_metadata(rows,workers)
 files,total=inventory(raw/"profiles")
 report.update(valid_release_only=True,exact_owned_container_absent=True,transport_checks_passed_before_trace=True,four_rank_trace_valid=False,r44_diagnostic_transport_valid=False,r43_diagnostic_transport_valid=False,r42_diagnostic_transport_valid=False,r44_host_source_sha256=c["r44_host_source_sha256"],r44_profiler=policy.PROFILE,raw_profile_sha256={str(p.relative_to(raw/"profiles")):policy.sha(p)for p in files},raw_profile_files=len(files),raw_profile_bytes=total,full_goal_complete=False,new_performance_acceptance=False)
 digest=save(output,report);return {"output":str(output),"sha256":digest,"valid_release_only":True,"four_rank_trace_valid":False}
def run(mode,plan_path,output=None):
 plan_path=Path(plan_path).resolve();plan=json.loads(plan_path.read_bytes())
 cp=Path(plan["contract"]["path"])if isinstance(plan["contract"],dict)else policy.W/plan["contract"]
 c=json.loads(cp.read_bytes());check_wrapper(plan,c)
 with scope(c):
  if mode=="parse":
   from host_audits.r43_offline_parse_manager import run as operation
   return operation(plan_path)
  if mode=="normalize":
   from host_audits.r43_trace_timestamp_copy import run as operation
   return operation(plan_path)
  if mode!="audit":raise ValueError("exact known CPU postprocessing mode")
  from host_audits.r43_normalized_supplemental_audit import audit
  report=audit(plan_path)
 report=finish(c,report);digest=save(output,report)
 return {"output":str(output),"sha256":digest,"r44_diagnostic_transport_valid":True,"live_release_verified":report.get("live_release_verified",False)}
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--mode",choices=["release-only","parse","normalize","audit"],required=True);p.add_argument("--contract");p.add_argument("--plan");p.add_argument("--output");a=p.parse_args()
 result=release_only(a.contract,a.output)if a.mode=="release-only"else run(a.mode,a.plan,a.output)
 if result:print(json.dumps(result))

"""R42 diagnostic admission composed with the immutable R40 source/ruler gate."""
import hashlib,json,subprocess,time
from pathlib import Path
from host_audits import r40_formal_policy as prior
sha=prior.sha
BASE_SHA=prior.BASE_SHA
W=Path(__file__).resolve().parent.parent
FILES={"host_audits/r42_profile_policy.py","host_audits/r42_profile_controller.py",
 "host_audits/r41_profile_trace.py","host_audits/r42_profile_audit.py","host_audits/r42_profile_capsule.py",
 "R42_NO_PYTHON_TRACER_SINGLE_VARIABLE_PLAN_20261026.json"}
REFERENCES={"G1":("FORMAL_WARM_R40_G1_R1_20261026_CONTRACT.json","51cd249487e7928d4ce58f8ebf0cb017d4da5d10cb4a396188f79fa34115c07e"),
 "G3":("FORMAL_WARM_R40_G3_R1_20261026_CONTRACT.json","f69fd61e8eca690905ceecdddeb9ef18e4055d3e090629307d83bfc7d4cdb9cd")}
PROFILE={"profiler":"torch","torch_profiler_dir":"/scratch/profiles","ignore_frontend":True,
 "torch_profiler_with_stack":False,"torch_profiler_with_memory":False,"delay_iterations":0,"max_iterations":7}
ADDED={"r42_role","r42_reference","r42_host_source_sha256","r42_controller_sha256",
 "r42_profiler","r42_previous_audit","r42_minimum_remaining_seconds","r42_attempt","r42_failure_prerequisite","r42_minimum_cache_bytes"}
def check(c,*,root=W,require_new_root=True):
 root=Path(root).resolve();group=c.get("performance_group")
 if group not in REFERENCES:raise ValueError("only matched native/G3 diagnostic supported")
 name,digest=REFERENCES[group];p=root/name
 if sha(p)!=digest or c.get("r42_reference")!={"path":name,"sha256":digest}:
  raise ValueError("actual immutable accepted R40 reference required")
 original=json.loads(p.read_bytes());checked=prior.check(original,root=root,require_new_root=False)
 failure={"path":"/cache/cch/hypic-independent-20261013/r41-g1-r1-failure-release-audit-20261026.json","sha256":"20c91fdfe7c338c114a11f5f2af6dab7eed72bfd457569eff93a009081906591"}
 if c.get("r42_failure_prerequisite")!=failure or sha(failure["path"])!=failure["sha256"]:
  raise ValueError("actual released failed R41 capture prerequisite required")
 f=json.loads(Path(failure["path"]).read_bytes())
 if not f.get("valid_release_only")or f.get("journal_failed_requests")!=40 or f.get("four_rank_profiler_capture_accepted")is not False:
  raise ValueError("R41 failure and exact release cannot be reclassified")
 old=root/"PROFILE_R41_G1_R1_20261026_CONTRACT.json"
 if sha(old)!="4bf0a55c78898a1f363f0a546e254f90887fdf2d4c10dfdcdf0f8f42e6820d1a":raise ValueError("old failed R41 contract changed")
 old=json.loads(old.read_bytes())
 prior.retained.native._sources(root,old["r41_host_source_sha256"])
 wanted=dict(PROFILE,torch_profiler_with_stack=True)
 if old["r41_profiler"]!=wanted:raise ValueError("one actual profiler stack/module flag differs")
 if c.get("r42_minimum_cache_bytes")!=int((8.5 if group=="G1"else 6.5)*1024**3):
  raise ValueError("two-profile/one-profile cache reservation required")
 if set(c)!=set(original)|ADDED or any(c.get(k)!=v for k,v in original.items()if k not in("raw_root","container_name","formal_launch_command","formal_audit_command","purpose","prospective_state")):
  raise ValueError("R42 can only change own root/name and declared diagnostic envelope")
 if(c.get("r42_role")!="BOUNDED_OFFICIAL_PREFILL_TIMELINE_DIAGNOSTIC_NOT_PERFORMANCE"
    or c.get("r42_profiler")!=PROFILE or c.get("r42_minimum_remaining_seconds")!=(3300 if group=="G1"else 2400)):
  raise ValueError("explicit capped official diagnostic and remaining budget required")
 host=c.get("r42_host_source_sha256");prior.retained.native._sources(root,host)
 if set(host)!=FILES or c.get("r42_controller_sha256")!=host["host_audits/r42_profile_controller.py"]:
  raise ValueError("complete distinct R42 HOST/source closure required")
 plan="R42_NO_PYTHON_TRACER_SINGLE_VARIABLE_PLAN_20261026.json"
 rel=str((root/plan).relative_to(root.parent.parent.parent))
 if subprocess.check_output(["git","show","bb7585f3bfb727813331ddbb3abc74a83ef3a1f5:"+rel],cwd=str(root))!=(root/plan).read_bytes():
  raise ValueError("predeclared published R42 plan changed")
 decision=json.loads((root/"R40_FIRST_PAIR_DECISION_20261026.json").read_bytes())
 if decision.get("allow_repetition_matrix")is not False or decision["raw_decision"]["sha256"]!=sha(decision["raw_decision"]["path"]):
  raise ValueError("actual valid negative predecessor required")
 previous=c.get("r42_previous_audit")
 if group=="G1":
  if previous is not None:raise ValueError("native diagnostic begins new matched pair")
 else:
  if not isinstance(previous,dict)or sha(previous["path"])!=previous.get("sha256"):
   raise ValueError("new actual native diagnostic predecessor required")
  report=json.loads(Path(previous["path"]).read_bytes())
  if(report.get("r42_diagnostic_transport_valid")is not True or report.get("live_release_verified")is not True
     or report.get("profiler",{}).get("four_rank_trace_valid")is not True or report.get("policy",{}).get("group")!="G1"
     or report.get("r42_host_source_sha256")!=host):
   raise ValueError("native diagnostic must be valid parsed same-source and exact released")
 attempt=c.get("r42_attempt")
 if type(attempt)is not int or not 1<=attempt<=99:raise ValueError("bounded unique diagnostic attempt")
 contract="PROFILE_R42_"+group+"_R"+str(attempt)+"_20261026_CONTRACT.json"
 rawname="critical-path-r42-"+group.lower()+"-r"+str(attempt)+"-20261026"
 audit="/cache/cch/hypic-independent-20261013/r42-"+group.lower()+"-r"+str(attempt)+"-independent-audit-20261026.json"
 if(c.get("formal_launch_command")!="python3 -B -m host_audits.r42_profile_controller --contract "+contract+" --run"
    or c.get("formal_audit_command")!="python3 -B -m host_audits.r42_profile_audit --contract "+contract+" --live-release --output "+audit
    or c.get("purpose")!="R42 bounded official profiler diagnostic; retained formal transport owner does not confer performance acceptance."
    or c.get("prospective_state")!="R42_DIAGNOSTIC_UNMEASURED"):
  raise ValueError("explicit diagnostic owner commands and claim boundary required")
 raw=Path(c["raw_root"])
 if(not raw.is_absolute()or raw.is_symlink()or raw.name!=rawname
    or raw.parent!=Path("/cache/cch/hypic-independent-20261013")or(require_new_root and raw.exists())
    or c["container_name"]!="hypic-"+raw.name):
  raise ValueError("new exact own diagnostic root/container required")
 checked.update(r42_sources=host,r42_profiler=PROFILE,
  scope="Diagnostic collection only; same immutable R40 inference bytes/transport. No speed or quality acceptance.")
 return checked
def require_budget(c):
 from independent_execution_deadline import deadline_epoch
 remaining=deadline_epoch(c["absolute_stop_utc"])-time.time()
 if remaining<c["r42_minimum_remaining_seconds"]:raise TimeoutError("insufficient fixed-deadline R42 budget")
 import os
 st=os.statvfs("/cache")
 if st.f_bavail*st.f_frsize<c["r42_minimum_cache_bytes"]:raise RuntimeError("insufficient R42 capture storage reserve")
 return remaining

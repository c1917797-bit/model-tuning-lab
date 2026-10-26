"""R41 diagnostic admission composed with the immutable R40 source/ruler gate."""
import hashlib,json,subprocess,time
from pathlib import Path
from host_audits import r40_formal_policy as prior
sha=prior.sha
BASE_SHA=prior.BASE_SHA
W=Path(__file__).resolve().parent.parent
FILES={"host_audits/r41_profile_policy.py","host_audits/r41_profile_controller.py",
 "host_audits/r41_profile_trace.py","host_audits/r41_profile_audit.py","host_audits/r41_profile_capsule.py",
 "R41_CRITICAL_PATH_DIAGNOSTIC_PLAN_20261026.json"}
REFERENCES={"G1":("FORMAL_WARM_R40_G1_R1_20261026_CONTRACT.json","51cd249487e7928d4ce58f8ebf0cb017d4da5d10cb4a396188f79fa34115c07e"),
 "G3":("FORMAL_WARM_R40_G3_R1_20261026_CONTRACT.json","f69fd61e8eca690905ceecdddeb9ef18e4055d3e090629307d83bfc7d4cdb9cd")}
PROFILE={"profiler":"torch","torch_profiler_dir":"/scratch/profiles","ignore_frontend":True,
 "torch_profiler_with_stack":True,"torch_profiler_with_memory":False,"delay_iterations":0,"max_iterations":7}
ADDED={"r41_role","r41_reference","r41_host_source_sha256","r41_controller_sha256",
 "r41_profiler","r41_previous_audit","r41_minimum_remaining_seconds","r41_attempt"}
def check(c,*,root=W,require_new_root=True):
 root=Path(root).resolve();group=c.get("performance_group")
 if group not in REFERENCES:raise ValueError("only matched native/G3 diagnostic supported")
 name,digest=REFERENCES[group];p=root/name
 if sha(p)!=digest or c.get("r41_reference")!={"path":name,"sha256":digest}:
  raise ValueError("actual immutable accepted R40 reference required")
 original=json.loads(p.read_bytes());checked=prior.check(original,root=root,require_new_root=False)
 if set(c)!=set(original)|ADDED or any(c.get(k)!=v for k,v in original.items()if k not in("raw_root","container_name","formal_launch_command","formal_audit_command","purpose","prospective_state")):
  raise ValueError("R41 can only change own root/name and declared diagnostic envelope")
 if(c.get("r41_role")!="BOUNDED_OFFICIAL_PREFILL_TIMELINE_DIAGNOSTIC_NOT_PERFORMANCE"
    or c.get("r41_profiler")!=PROFILE or c.get("r41_minimum_remaining_seconds")!=(4500 if group=="G1"else 2400)):
  raise ValueError("explicit capped official diagnostic and remaining budget required")
 host=c.get("r41_host_source_sha256");prior.retained.native._sources(root,host)
 if set(host)!=FILES or c.get("r41_controller_sha256")!=host["host_audits/r41_profile_controller.py"]:
  raise ValueError("complete distinct R41 HOST/source closure required")
 plan="R41_CRITICAL_PATH_DIAGNOSTIC_PLAN_20261026.json"
 rel=str((root/plan).relative_to(root.parent.parent.parent))
 if subprocess.check_output(["git","show","550d0e8a79d14121ebdade639363385bd89eb1ee:"+rel],cwd=str(root))!=(root/plan).read_bytes():
  raise ValueError("predeclared published R41 plan changed")
 decision=json.loads((root/"R40_FIRST_PAIR_DECISION_20261026.json").read_bytes())
 if decision.get("allow_repetition_matrix")is not False or decision["raw_decision"]["sha256"]!=sha(decision["raw_decision"]["path"]):
  raise ValueError("actual valid negative predecessor required")
 previous=c.get("r41_previous_audit")
 if group=="G1":
  if previous is not None:raise ValueError("native diagnostic begins new matched pair")
 else:
  if not isinstance(previous,dict)or sha(previous["path"])!=previous.get("sha256"):
   raise ValueError("new actual native diagnostic predecessor required")
  report=json.loads(Path(previous["path"]).read_bytes())
  if(report.get("r41_diagnostic_transport_valid")is not True or report.get("live_release_verified")is not True
     or report.get("profiler",{}).get("four_rank_trace_valid")is not True or report.get("policy",{}).get("group")!="G1"
     or report.get("r41_host_source_sha256")!=host):
   raise ValueError("native diagnostic must be valid parsed same-source and exact released")
 attempt=c.get("r41_attempt")
 if type(attempt)is not int or not 1<=attempt<=99:raise ValueError("bounded unique diagnostic attempt")
 contract="PROFILE_R41_"+group+"_R"+str(attempt)+"_20261026_CONTRACT.json"
 rawname="critical-path-r41-"+group.lower()+"-r"+str(attempt)+"-20261026"
 audit="/cache/cch/hypic-independent-20261013/r41-"+group.lower()+"-r"+str(attempt)+"-independent-audit-20261026.json"
 if(c.get("formal_launch_command")!="python3 -B -m host_audits.r41_profile_controller --contract "+contract+" --run"
    or c.get("formal_audit_command")!="python3 -B -m host_audits.r41_profile_audit --contract "+contract+" --live-release --output "+audit
    or c.get("purpose")!="R41 bounded official profiler diagnostic; retained formal transport owner does not confer performance acceptance."
    or c.get("prospective_state")!="R41_DIAGNOSTIC_UNMEASURED"):
  raise ValueError("explicit diagnostic owner commands and claim boundary required")
 raw=Path(c["raw_root"])
 if(not raw.is_absolute()or raw.is_symlink()or raw.name!=rawname
    or raw.parent!=Path("/cache/cch/hypic-independent-20261013")or(require_new_root and raw.exists())
    or c["container_name"]!="hypic-"+raw.name):
  raise ValueError("new exact own diagnostic root/container required")
 checked.update(r41_sources=host,r41_profiler=PROFILE,
  scope="Diagnostic collection only; same immutable R40 inference bytes/transport. No speed or quality acceptance.")
 return checked
def require_budget(c):
 from independent_execution_deadline import deadline_epoch
 remaining=deadline_epoch(c["absolute_stop_utc"])-time.time()
 if remaining<c["r41_minimum_remaining_seconds"]:raise TimeoutError("insufficient fixed-deadline R41 budget")
 return remaining

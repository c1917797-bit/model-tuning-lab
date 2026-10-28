"""Small R43 renewal/storage envelope; retain every R42 inference and evidence gate."""
import copy,json,os,subprocess,time
from pathlib import Path
from host_audits import r42_profile_policy as prior
W=Path(__file__).resolve().parent.parent
START="2026-10-28T19:15:24Z"
STOP="2026-10-29T19:15:24Z"
RAW_PARENT=Path("/opt/host/vnf/cch-hypic-independent-20261028")
PLAN="R43_RENEWAL_REFLECTION_PLAN_20261028.json"
PLAN_COMMIT="df4bb438066415fe192fde39fd2313c4ab76ab24"
REFERENCE="PROFILE_R42_G1_R1_20261026_CONTRACT.json"
REFERENCE_SHA="9dc1500eb91add5b2234e3b7f308e52c63907007aceb8af631a689bde9b9a778"
FILES={"host_audits/r43_renewal_policy.py","host_audits/r43_profile_controller.py",
       "host_audits/r43_profile_audit.py","host_audits/r43_launch_capsule.py",PLAN}
EXTRA={"r43_host_source_sha256","r43_controller_sha256","r43_reference","r43_authority"}
CHANGED={"absolute_stop_utc","renewed_authority","raw_root","container_name",
         "formal_launch_command","formal_audit_command","prospective_state","purpose"}
sha=prior.sha
def template(group,previous=None,*,root=W):
 root=Path(root);old=json.loads((root/REFERENCE).read_bytes())
 if sha(root/REFERENCE)!=REFERENCE_SHA:raise ValueError("immutable unallocated R42 reference drift")
 if group=="G1":
  if previous is not None:raise ValueError("native begins diagnostic pair")
  return old
 if group!="G3":raise ValueError("only native/G3 diagnostic")
 c=json.loads((root/prior.REFERENCES[group][0]).read_bytes())
 c.update({k:copy.deepcopy(v)for k,v in old.items()if k.startswith("r42_")})
 raw="critical-path-r42-g3-r1-20261026";contract="PROFILE_R42_G3_R1_20261026_CONTRACT.json"
 c.update(raw_root="/cache/cch/hypic-independent-20261013/"+raw,container_name="hypic-"+raw,
  r42_reference={"path":prior.REFERENCES[group][0],"sha256":prior.REFERENCES[group][1]},
  r42_previous_audit=previous,r42_minimum_remaining_seconds=2400,r42_minimum_cache_bytes=int(6.5*1024**3),
  formal_launch_command="python3 -B -m host_audits.r42_profile_controller --contract "+contract+" --run",
  formal_audit_command="python3 -B -m host_audits.r42_profile_audit --contract "+contract+" --live-release --output /cache/cch/hypic-independent-20261013/r42-g3-r1-independent-audit-20261026.json",
  prospective_state=old["prospective_state"],purpose=old["purpose"])
 return c
def check(c,*,root=W,require_new_root=True):
 root=Path(root).resolve();group=c.get("performance_group");old=template(group,c.get("r42_previous_audit"),root=root)
 proof=prior.check(old,root=root,require_new_root=False)
 if set(c)!=set(old)|EXTRA or any(c.get(k)!=v for k,v in old.items()if k not in CHANGED):
  raise ValueError("renewal cannot change actual inference/ruler/profiler/source guards")
 authority={"start_utc":START,"absolute_stop_utc":STOP,"human":"反思为什么达不成，然后再继续穿刺24小时"}
 if c.get("r43_authority")!=authority or c.get("renewed_authority")!=authority or c.get("absolute_stop_utc")!=STOP:
  raise ValueError("exact renewed24h authority required")
 if c.get("r43_reference")!={"path":REFERENCE,"sha256":REFERENCE_SHA}:
  raise ValueError("explicit prior unexecuted reference required")
 host=c.get("r43_host_source_sha256");prior.prior.retained.native._sources(root,host)
 if set(host)!=FILES or c.get("r43_controller_sha256")!=host["host_audits/r43_profile_controller.py"]:
  raise ValueError("new small renewal HOST closure required")
 rel=str((root/PLAN).relative_to(root.parent.parent.parent))
 if subprocess.check_output(["git","show",PLAN_COMMIT+":"+rel],cwd=str(root))!=(root/PLAN).read_bytes():
  raise ValueError("published predeclared renewal plan drift")
 suffix=group.lower()+"-r1-20261028";raw=RAW_PARENT/("critical-path-r43-"+suffix)
 contract="PROFILE_R43_"+group+"_R1_20261028_CONTRACT.json"
 audit=str(RAW_PARENT/("r43-"+suffix+"-independent-audit.json"))
 if(c.get("raw_root")!=str(raw)or raw.is_symlink()or(require_new_root and raw.exists())
    or c.get("container_name")!="hypic-"+raw.name
    or c.get("formal_launch_command")!="python3 -B -m host_audits.r43_profile_controller --contract "+contract+" --run"
    or c.get("formal_audit_command")!="python3 -B -m host_audits.r43_profile_audit --contract "+contract+" --live-release --output "+audit
    or c.get("purpose")!="R43 renewed same-R42 diagnostic; profile timings are not service performance."
    or c.get("prospective_state")!="R43_RENEWED_DIAGNOSTIC_UNMEASURED"):
  raise ValueError("new exact contract/root/owner required")
 if group=="G3":
  report=json.loads(Path(c["r42_previous_audit"]["path"]).read_bytes())
  if(report.get("r43_diagnostic_transport_valid")is not True
     or report.get("r43_host_source_sha256")!=host
     or report.get("r43_authority")!=authority):
   raise ValueError("same-source newly valid native R43 predecessor required")
 proof.update(r43_host_source_sha256=host,r43_authority=authority,r43_reference=c["r43_reference"],
  scope="Renewed same-source diagnostic only; original transport/math/profiler rules retained. No performance acceptance.")
 return proof
def require_budget(c):
 from independent_execution_deadline import deadline_epoch
 remaining=deadline_epoch(c["absolute_stop_utc"])-time.time()
 if remaining<c["r42_minimum_remaining_seconds"]+90:raise TimeoutError("renewed pair budget and90s margin required")
 if RAW_PARENT.is_symlink()or not RAW_PARENT.is_dir():raise ValueError("real dedicated persistent raw parent required")
 if os.stat(RAW_PARENT).st_dev!=os.stat("/opt/host/vnf").st_dev or os.stat(RAW_PARENT).st_dev==os.stat("/cache").st_dev:
  raise ValueError("declared distinct persistent raw volume required")
 def free(p):
  s=os.statvfs(p);return s.f_bavail*s.f_frsize
 if free(RAW_PARENT)<c["r42_minimum_cache_bytes"]or free("/cache")<c["cache_free_floor"]:
  raise RuntimeError("original raw reserve plus separate cache floor required")
 return remaining

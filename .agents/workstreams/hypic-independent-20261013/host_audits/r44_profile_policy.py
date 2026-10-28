"""R44 count-two HOST envelope; retain immutable R43 inference and file guards."""
import copy,json,subprocess
from pathlib import Path
from host_audits import r43_renewal_policy as prior
W=prior.W;RAW_PARENT=prior.RAW_PARENT;sha=prior.sha
PLAN="R44_BOUNDED_PROFILE_SUCCESSOR_PLAN_20261028.json"
PLAN_SHA="66439a7a1bb743233a8c3d443e57050613f80d0b9881bb9466921ee3ef64e600"
PLAN_COMMIT="6e16c53f944a597059e39db07497794c023124b2"
REFERENCES={"G1":("PROFILE_R43_G1_R1_20261028_CONTRACT.json","8afbdd8da1a8300b01d96fef8c7ea8a1103566e538232ec372f01385621e2e67"),"G3":("PROFILE_R43_G3_R1_20261028_CONTRACT.json","1ea0d7c494b13ad36e741016dbb61bf11501280e27be42e7e11e579e026975de")}
BASE_CHECK=prior.check;BASE_BUDGET=prior.require_budget;ORIGINAL_PROFILE=prior.prior.PROFILE
PROFILE=dict(ORIGINAL_PROFILE,max_iterations=2)
FILES={"host_audits/r44_profile_policy.py","host_audits/r44_scope.py","host_audits/r44_profile_controller.py","host_audits/r44_profile_audit.py","host_audits/r44_launch_capsule.py","host_audits/r44_postprocess.py",PLAN}
EXTRA={"r44_reference","r44_host_source_sha256","r44_controller_sha256","r44_postprocess_source_sha256"}
CHANGED={"raw_root","container_name","formal_launch_command","formal_audit_command","purpose","prospective_state","r42_profiler","r42_previous_audit"}
POST={"host_audits/r43_offline_parse_manager.py":"00b6221835f8f6cb7e8f8328b5f1c6430e2967fdb93a8c74ade636e82da2c527","host_audits/r43_trace_timestamp_copy.py":"0b8466742c3b63a597cf278632b4952001c80a7180b35ffab4cb6c263b5e507e","host_audits/r43_normalized_supplemental_audit.py":"d5ae521cfeb9ced1763ce5ad0eede334c6792f386e5352f1b293353b816ff244","host_audits/r41_profile_trace.py":"46fdb2acaa01352a31a808b88a71a39bd7cfa63e2e391f7cc971bbfbcaafe74c"}
def reference(group,root=W):
 if group not in REFERENCES:raise ValueError("R44 only G1/G3")
 name,digest=REFERENCES[group];path=Path(root)/name
 if sha(path)!=digest:raise ValueError("immutable R43 reference drift")
 return json.loads(path.read_bytes())
def check_previous(report,host):
 if(report.get("r44_diagnostic_transport_valid")is not True or report.get("r44_host_source_sha256")!=host
    or report.get("r44_profiler")!=PROFILE or report.get("live_release_verified")is not True
    or report.get("profiler",{}).get("four_rank_trace_valid")is not True or report.get("policy",{}).get("group")!="G1"):
  raise ValueError("same-source actual count-two full native predecessor required")
def check(c,*,root=W,require_new_root=True):
 root=Path(root).resolve();group=c.get("performance_group");old=reference(group,root)
 saved=prior.prior.PROFILE
 prior.prior.PROFILE=ORIGINAL_PROFILE
 try:checked=BASE_CHECK(old,root=root,require_new_root=False)
 finally:prior.prior.PROFILE=saved
 if set(c)!=set(old)|EXTRA or any(c.get(k)!=v for k,v in old.items()if k not in CHANGED):raise ValueError("R44 only diagnostic count/root/owner changes permitted")
 if c.get("r44_reference")!={"path":REFERENCES[group][0],"sha256":REFERENCES[group][1]}or c.get("r42_profiler")!=PROFILE:raise ValueError("explicit original reference and count2 required")
 host=c.get("r44_host_source_sha256");prior.prior.prior.retained.native._sources(root,host)
 if set(host)!=FILES or c.get("r44_controller_sha256")!=host["host_audits/r44_profile_controller.py"]:raise ValueError("closed R44 HOST sources required")
 if c.get("r44_postprocess_source_sha256")!=POST:raise ValueError("unchanged matched postprocess helpers required")
 prior.prior.prior.retained.native._sources(root,POST)
 if sha(root/PLAN)!=PLAN_SHA:raise ValueError("published cap-two sizing plan drift")
 rel=str((root/PLAN).relative_to(root.parent.parent.parent))
 if subprocess.check_output(["git","show",PLAN_COMMIT+":"+rel],cwd=str(root))!=(root/PLAN).read_bytes():raise ValueError("predeclared R44 plan not same published bytes")
 suffix=group.lower()+"-r1-20261028";raw=RAW_PARENT/("critical-path-r44-"+suffix)
 contract="PROFILE_R44_"+group+"_R1_20261028_CONTRACT.json"
 if(c.get("raw_root")!=str(raw)or raw.is_symlink()or(require_new_root and raw.exists())or c.get("container_name")!="hypic-"+raw.name
    or c.get("formal_launch_command")!="python3 -B -m host_audits.r44_profile_controller --contract "+contract+" --run"
    or c.get("formal_audit_command")!="python3 -B -m host_audits.r44_profile_audit --contract "+contract+" --live-release --output "+str(RAW_PARENT/("r44-"+suffix+"-independent-audit.json"))
    or c.get("purpose")!="R44 bounded two-step diagnostic; full40 ruler unchanged; profile times are not service performance."
    or c.get("prospective_state")!="R44_TWO_STEP_DIAGNOSTIC_UNMEASURED"):raise ValueError("new exact R44 owner/root/commands required")
 previous=c.get("r42_previous_audit")
 if group=="G1":
  if previous is not None:raise ValueError("new count-two native must begin pair")
 else:
  if not isinstance(previous,dict)or Path(previous["path"]).parent!=RAW_PARENT or sha(previous["path"])!=previous.get("sha256"):raise ValueError("actual owned native report path/SHA required")
  check_previous(json.loads(Path(previous["path"]).read_bytes()),host)
 checked.update(r44_host_source_sha256=host,r44_postprocess_source_sha256=POST,r44_profiler=PROFILE,r42_profiler=PROFILE,r44_reference=c["r44_reference"],scope="R44 count2 diagnostic only; unchanged full40/math/source/ownership/isolation/file caps. No performance acceptance.")
 return checked
def require_budget(c):
 remaining=BASE_BUDGET(c)
 if remaining<7290:raise TimeoutError("R44 full pipeline7200s plus90s margin required")
 return remaining
def receipt(c):
 return {"diagnostic_only":True,"source_sha256":c["r44_host_source_sha256"],"outer_host_controller_sha256":c["r44_controller_sha256"],"reference":c["r44_reference"],"profiler":PROFILE,"postprocess_source_sha256":POST,"raw_root":c["raw_root"],"third_step_stops_before_third_execute":True}
def make_contract(group,previous=None,root=W):
 root=Path(root);c=reference(group,root);c["r44_reference"]={"path":REFERENCES[group][0],"sha256":REFERENCES[group][1]}
 c["r44_host_source_sha256"]={n:sha(root/n)for n in sorted(FILES)};c["r44_controller_sha256"]=c["r44_host_source_sha256"]["host_audits/r44_profile_controller.py"];c["r44_postprocess_source_sha256"]=copy.deepcopy(POST)
 c["r42_profiler"]=copy.deepcopy(PROFILE);c["r42_previous_audit"]=previous
 suffix=group.lower()+"-r1-20261028";raw=RAW_PARENT/("critical-path-r44-"+suffix);name="PROFILE_R44_"+group+"_R1_20261028_CONTRACT.json"
 c.update(raw_root=str(raw),container_name="hypic-"+raw.name,formal_launch_command="python3 -B -m host_audits.r44_profile_controller --contract "+name+" --run",formal_audit_command="python3 -B -m host_audits.r44_profile_audit --contract "+name+" --live-release --output "+str(RAW_PARENT/("r44-"+suffix+"-independent-audit.json")),purpose="R44 bounded two-step diagnostic; full40 ruler unchanged; profile times are not service performance.",prospective_state="R44_TWO_STEP_DIAGNOSTIC_UNMEASURED")
 return c

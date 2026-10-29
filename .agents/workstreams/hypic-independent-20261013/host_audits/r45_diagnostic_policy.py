"""R45 strict observational successor. Old contracts/sources remain immutable."""
import copy,hashlib,json,os,time
from pathlib import Path
from host_audits import r44_profile_policy as historical
from host_audits.r39_target_warmups import warm_descriptors
from host_audits import r30b_graph_formal_audit as retained
W=Path(__file__).resolve().parent.parent
P=Path("/opt/host/vnf/cch-hypic-independent-20261028")
REFERENCE="PROFILE_R44_G3_R1_20261028_CONTRACT.json"
REFERENCE_SHA="56a22e379fd08dfb034c0ef27cf9d784742813f456f153bc8c81a7df8f4614f3"
PLAN="R45_COMPILATION_CAUSAL_BUDGET_PLAN_20261029.json"
PLAN_SHA="9ccd579bde3e44a024a02d94be9ceef82921163aec4253e5ea4fcfa9879e0fa3"
ACTIVE="R45_COMPILATION_BUDGET_ON_MANIFEST_20261029.json"
CONTRACT="COMPILATION_BUDGET_R45_G3_R1_20261029_CONTRACT.json"
RAW=P/"compilation-budget-r45-g3-r1-20261029"
CPU_CLOCK=P/"r45-clock-source-proof-20261029/result.json"
ROLE="ONE_UNPROFILED_COMPILATION_OBSERVATION_NOT_PERFORMANCE"
DEADLINE="2026-10-29T19:15:24Z"
BASE_SHA="bf55661d61618a7f83537ce6bf477b66e80ccaf097ac714938ceee9bdf199d33"
NEW_PY={"compilation_budget_r45/"+n for n in("__init__.py","patch.py","sitecustomize.py","worker_loader.py")}
DELIVERY=NEW_PY|{"compilation_budget_r45/MANIFEST.json","compilation_budget_r45/run_with_patch.sh"}
HOST={"host_audits/r45_diagnostic_policy.py","host_audits/r45_diagnostic_controller.py",
 "host_audits/r45_diagnostic_audit.py","host_audits/r45_compilation_evidence.py",
 "host_audits/r45_launch_capsule.py",PLAN}
EXTRA={"r45_role","r45_reference","r45_host_source_sha256","r45_runtime_added_source_sha256",
 "r45_full_trace_prerequisite","r45_clock_proof","r45_minimum_remaining_seconds",
 "r45_minimum_raw_bytes","r45_diagnostic_only"}
CHANGED={"raw_root","container_name","formal_launch_command","formal_audit_command","purpose",
 "prospective_state","successor_manifest","cache_diagnostic","study_source_map_sha256",
 "host_controller_sha256","r42_profiler"}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_bytes())
def reference(root=W):
 root=Path(root)
 if sha(root/REFERENCE)!=REFERENCE_SHA:raise ValueError("immutable actual R44 G3 reference required")
 return load(root/REFERENCE)
def digest_map(m):return hashlib.sha256(json.dumps(m,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def require_budget(c):
 if c.get("absolute_stop_utc")!=DEADLINE or c.get("r45_minimum_remaining_seconds")!=7290:
  raise ValueError("fixed authority and full7290second admission")
 from independent_execution_deadline import deadline_epoch
 remaining=deadline_epoch(DEADLINE)-time.time()
 if remaining<7290:raise TimeoutError("R45 full7200second startup/warm/40/audit/release plus90second margin unavailable")
 if os.statvfs("/cache").f_bavail*os.statvfs("/cache").f_frsize<4*1024**3:raise OSError("cache4GiB floor")
 st=os.statvfs(P)
 if st.f_bavail*st.f_frsize<c["r45_minimum_raw_bytes"]:raise OSError("persistent raw6.5GiB reservation")
 return remaining
def clock_proof(value):
 if type(value)is not dict or value.get("path")!=str(CPU_CLOCK)or sha(CPU_CLOCK)!=value.get("sha256"):
  raise ValueError("actual new CPU clock proof binding")
 d=load(CPU_CLOCK)
 from host_audits.r45_launch_capsule import CLOCK_CODE
 if(d.get("helper_sha256")!=sha(W/"host_audits/r45_launch_capsule.py")
    or d.get("code_sha256")!=hashlib.sha256(CLOCK_CODE.encode()).hexdigest()
    or d.get("controller_error")is not None
    or d.get("terminal_state_before_cleanup",{}).get("Running")is not False
    or d.get("terminal_state_before_cleanup",{}).get("ExitCode")!=0):
  raise ValueError("exact CPU clock source and real terminal evidence")
 declaration=d.get("declaration",{})
 if(declaration.get("Image")!=d.get("image")or declaration.get("Id")!=d.get("cid")
    or declaration.get("HostConfig",{}).get("Devices")
    or declaration.get("HostConfig",{}).get("Privileged")is not False
    or declaration.get("HostConfig",{}).get("NetworkMode")!="none"):
  raise ValueError("actual no-device CPU declaration")
 if(d.get("exit")!=0 or d.get("exact_cpu_container_absent")is not True
    or d.get("no_devices")is not True or d.get("image")!="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"):
  raise ValueError("sameimage no-device source clock proof")
 inner=json.loads(d["stdout"])
 from host_audits.r45_compilation_evidence import exact_ns
 if(not exact_ns(inner["bracket_monotonic_ns"])<=exact_ns(inner["perf_counter_ns"])<=exact_ns(inner["bracket_monotonic_end_ns"])
    or inner.get("no_inference_imports")is not True):
  raise ValueError("actual matching monotonic/perf-counter bracket")
 host=d.get("host_clock",{})
 for clocks in(inner.get("clocks",{}),host):
  if set(clocks)!={"monotonic","perf_counter"}:raise ValueError("both actual builtin clock sources")
  for row in clocks.values():
   if row.get("implementation")!="clock_gettime(CLOCK_MONOTONIC)"or row.get("monotonic")is not True or row.get("adjustable")is not False:
    raise ValueError("actual CLOCK_MONOTONIC implementation required")
 if inner.get("time_namespace")is None or inner.get("time_namespace")!=d.get("host_time_namespace"):
  raise ValueError("actual CPU/container shared time namespace")
 return d
def check(c,*,root=W,require_new_root=True):
 root=Path(root).resolve();old=reference(root)
 # Validate the real immutable historical contract, never a fabricated view of R45.
 historical.check(old,root=root,require_new_root=False)
 if set(c)!=set(old)|EXTRA or any(c.get(k)!=v for k,v in old.items()if k not in CHANGED):
  raise ValueError("R45 permits observation/new root/manifest/owner only; old model/math/ruler unchanged")
 if(c.get("r45_role")!=ROLE or c.get("r45_diagnostic_only")is not True
    or c.get("r45_reference")!={"path":REFERENCE,"sha256":REFERENCE_SHA}
    or c.get("absolute_stop_utc")!=DEADLINE or c.get("r42_profiler")is not None
    or c.get("performance_group")!="G3"or c.get("r40_target_warmup_count")!=2
    or c.get("r40_warm_descriptors")!=warm_descriptors(c["formal_token_artifact"])
    or c.get("r45_minimum_remaining_seconds")!=7290 or c.get("r45_minimum_raw_bytes")!=6979321856):
  raise ValueError("exact new diagnostic role/authority/torchprofilerOFF/full40warm2 budget")
 host=c.get("r45_host_source_sha256")
 retained.native._sources(root,host)
 if set(host)!=HOST or host.get("host_audits/r45_diagnostic_policy.py")!=sha(__file__)or c.get("host_controller_sha256")!=host["host_audits/r45_diagnostic_controller.py"]:
  raise ValueError("closed actual R45 HOST source/owner required")
 if sha(root/PLAN)!=PLAN_SHA:raise ValueError("predeclared compilation causal-budget plan drift")
 common=c.get("cache_diagnostic",{}).get("source_sha256")
 retained.native._sources(root,common)
 expected=dict(old["cache_diagnostic"]["source_sha256"])
 expected.update({n:sha(root/n)for n in DELIVERY|{ACTIVE}})
 if(common!=expected or c["cache_diagnostic"]!=dict(old["cache_diagnostic"],compact_manifest=ACTIVE,source_sha256=common)
    or c.get("study_source_map_sha256")!=digest_map(common)):
  raise ValueError("complete original common study map plus exact observer delivery only")
 mf=load(root/ACTIVE);oldmf=load(root/old["successor_manifest"])
 added=c.get("r45_runtime_added_source_sha256")
 if type(added)is not dict or set(added)!=NEW_PY or any(sha(root/n)!=h for n,h in added.items()):
  raise ValueError("exact four new runtime source files")
 expected_mf=copy.deepcopy(oldmf)
 expected_mf["source_sha256"].update(added)
 expected_mf["compilation_budget"]={"enabled":True,"profile":"source-pinned-triton-compile-v1","max_calls":512}
 expected_mf["activation_scope"]="Explicit new R45 facade; compilation observation ON, original step durability ON, component/IO/prefix observers OFF"
 expected_mf["scope"]="R45 unprofiled compilation-budget diagnostic, not a performance acceptance. All original438 runtime and mathematical sources unchanged; source-owned bounded observation is the sole new variable."
 if mf!=expected_mf or len([n for n in mf["source_sha256"]if n.endswith(".py")])!=442:
  raise ValueError("original438 runtime bytes plus four observational files only")
 cfg,manifest=retained.components._manifest(c,root)
 if cfg!=load(root/oldmf["config"]):raise ValueError("algorithm configuration unchanged")
 axes=retained.validate_policy(c,cfg)
 if axes!={"group":"G3","algorithm_on":True,"pdc_on":False}:raise ValueError("actual G3 axes")
 prior=c.get("r45_full_trace_prerequisite")
 wanted={"path":str(P/"r44-g3-r1-normalized-supplemental-audit-20261028.json"),
         "sha256":"f374bbc84b02f5fc020660eca7993e0f17f685057527e7e61eb572bb0d37f2f0"}
 if prior!=wanted or sha(prior["path"])!=prior["sha256"]:raise ValueError("actual accepted full R44 G3 evidence prerequisite")
 report=load(prior["path"])
 if(report.get("r44_diagnostic_transport_valid")is not True or report.get("live_release_verified")is not True
    or report.get("profiler",{}).get("four_rank_trace_valid")is not True):
  raise ValueError("actual original full four-trace/math/release acceptance")
 clock_proof(c.get("r45_clock_proof"))
 if(c.get("successor_manifest")!=ACTIVE or c.get("raw_root")!=str(RAW)
    or RAW.is_symlink()or(require_new_root and RAW.exists())or c.get("container_name")!="hypic-"+RAW.name
    or c.get("formal_launch_command")!="python3 -B -m host_audits.r45_diagnostic_controller --contract "+CONTRACT+" --run"
    or c.get("formal_audit_command")!="python3 -B -m host_audits.r45_diagnostic_audit --contract "+CONTRACT+" --live-release --output "+str(P/"r45-g3-r1-independent-audit-20261029.json")
    or c.get("purpose")!="R45 unprofiled observational full40; compilation budget only, no performance acceptance."
    or c.get("prospective_state")!="R45_COMPILATION_BUDGET_UNMEASURED"):
  raise ValueError("new exact R45 contract/root/owner/commands")
 return {"configuration_valid":True,"device_run":False,"device_admission_performed":False,
  "controller_sha256":c["host_controller_sha256"],"graph_runtime":c["graph_runtime"],
  "policy":axes,"active_manifest_sha256":manifest,"runtime_python":442,"old_runtime_python_unchanged":438,
  "source_bindings":len(common),"host_source_bindings":len(host),"prerequisite":prior}
def make_contract(*,root=W,clock):
 root=Path(root);c=reference(root)
 common=dict(c["cache_diagnostic"]["source_sha256"]);common.update({n:sha(root/n)for n in DELIVERY|{ACTIVE}})
 c["cache_diagnostic"]=dict(c["cache_diagnostic"],compact_manifest=ACTIVE,source_sha256=common)
 host={n:sha(root/n)for n in sorted(HOST)}
 c.update(raw_root=str(RAW),container_name="hypic-"+RAW.name,successor_manifest=ACTIVE,
  formal_launch_command="python3 -B -m host_audits.r45_diagnostic_controller --contract "+CONTRACT+" --run",
  formal_audit_command="python3 -B -m host_audits.r45_diagnostic_audit --contract "+CONTRACT+" --live-release --output "+str(P/"r45-g3-r1-independent-audit-20261029.json"),
  host_controller_sha256=host["host_audits/r45_diagnostic_controller.py"],study_source_map_sha256=digest_map(common),
  purpose="R45 unprofiled observational full40; compilation budget only, no performance acceptance.",
  prospective_state="R45_COMPILATION_BUDGET_UNMEASURED",r42_profiler=None,r45_role=ROLE,r45_diagnostic_only=True,
  r45_reference={"path":REFERENCE,"sha256":REFERENCE_SHA},r45_host_source_sha256=host,
  r45_runtime_added_source_sha256={n:sha(root/n)for n in sorted(NEW_PY)},
  r45_full_trace_prerequisite={"path":str(P/"r44-g3-r1-normalized-supplemental-audit-20261028.json"),"sha256":"f374bbc84b02f5fc020660eca7993e0f17f685057527e7e61eb572bb0d37f2f0"},
  r45_clock_proof=clock,r45_minimum_remaining_seconds=7290,r45_minimum_raw_bytes=6979321856)
 return c

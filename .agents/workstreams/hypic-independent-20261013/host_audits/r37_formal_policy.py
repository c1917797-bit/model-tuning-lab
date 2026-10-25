"""Final-source formal G1/G3 policy; no inference execution or historical timing reuse."""
import hashlib,json,sys
from pathlib import Path
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits import r30_graph_formal_audit as old
BASE_SHA=old.BASE_SHA
ENTRY="host_audits/r37_formal_policy.py"
HOST={"host_audits/r37_formal_policy.py","host_audits/r37_formal_controller.py",
      "host_audits/r37_formal_audit.py","host_audits/r30_graph_formal_controller.py",
      "host_audits/r30_graph_formal_audit.py","host_audits/r30b_graph_formal_audit.py",
      "host_audits/r27_graph_controller.py","host_audits/r27_graph_canary_audit.py",
      "host_audits/r26_group_performance.py","host_audits/r36_durability_evidence.py"}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(root,name):return old.native._read(old.native._inside(root,name))
def bound(c,root):
    source=c.get("r37_host",{}).get("source_sha256")
    old.native._sources(root,source)
    if set(source)!=HOST or source[ENTRY]!=sha(__file__):
        raise ValueError("exact separately bound R37 HOST closure required")
    if c.get("host_controller_source_sha256")!=source:
        raise ValueError("same actual HOST source map required")
    if(c.get("host_controller_sha256")!=source["host_audits/r37_formal_controller.py"]
       or c.get("controller_sha256")!=BASE_SHA or c.get("base_controller_sha256")!=BASE_SHA
       or sha(root/"formal_r15_tp4.py")!=BASE_SHA):
        raise ValueError("unchanged real owner and distinct actual adapter required")
    common=c.get("baseline_host_source_sha256")or c.get("cache_diagnostic",{}).get("source_sha256")
    old.native._sources(root,common)
    if hashlib.sha256(json.dumps(common,sort_keys=True,separators=(",",":")).encode()).hexdigest()!=c.get("study_source_map_sha256"):
        raise ValueError("complete common study identity required")
    return common
def prerequisite(c,root):
    spec=c.get("r37_prerequisite",{})
    report=old.native._inside(root,spec.get("report"))
    if sha(report)!=spec.get("sha256"):raise ValueError("sealed R36 decision summary required")
    d=json.loads(report.read_bytes());proof=d["independent_replay"];raw=Path(proof["path"])
    if not raw.is_absolute()or sha(raw)!=proof["sha256"]:
        raise ValueError("original independently replayed R36 decision drift")
    original=json.loads(raw.read_bytes())
    if(original["state"]!="SUPPORTED_BOUNDED_STEP_DURABILITY_EFFECT"
       or original.get("independent_audits_replayed")is not True
       or original.get("native_speed_gain_proven")is not False
       or original["B_gain_percent"]<5 or original["control_relative_drift_percent"]>5
       or d.get("all_three_arms_exact_released")is not True):
        raise ValueError("valid bounded effect and honest comparison required")
    for item in original["arms"]:
        if sha(root/item["contract"])!=item["contract_sha256"]or sha(item["audit"])!=item["audit_sha256"]:
            raise ValueError("R36 original arm binding drift")
        audit=json.loads(Path(item["audit"]).read_bytes())
        if not(audit.get("bounded_step_durability_screen_valid")is True and audit.get("live_release_verified")is True):
            raise ValueError("three valid released R36 arms required")
    anchor=read(root,"STEP_DURABILITY_R36_B1_R2_20261025_CONTRACT.json")
    for key in("image","model","model_config_sha256","physical_npus","tp","port","hccl_ports",
               "cpu_set","enable_thinking","formal_token_artifact","enable_prefix_caching","enforce_eager","absolute_stop_utc"):
        if c.get(key)!=anchor.get(key):raise ValueError("actual model/input/authority bridge differs: "+key)
    oldmf=read(root,anchor["successor_manifest"]);mf=read(root,c["successor_manifest"])
    oldpy={n:h for n,h in oldmf["source_sha256"].items()if n.endswith(".py")}
    newpy={n:h for n,h in mf["source_sha256"].items()if n.endswith(".py")}
    if oldpy!=newpy:raise ValueError("formal runtime Python differs from accepted R36")
    cfg=read(root,mf["config"]);anchorcfg=read(root,oldmf["config"])
    clean={k:v for k,v in anchorcfg.items()if k not in("r33_prefix_terminal_diagnostic","r33_prefix_terminal_only")}
    formal=read(root,"FORMAL_GRAPH_R30_G3_CONFIG_20261025.json")
    if clean!=formal:raise ValueError("diagnostic removal changes more than R33 observer flags")
    want=formal if c["performance_group"]=="G3"else read(root,"FORMAL_GRAPH_R30_G1_CONFIG_20261025.json")
    if cfg!=want:raise ValueError("exact original formal configuration required")
    for key in("r33_prefix_terminal_diagnostic","r33_prefix_terminal_only"):
        if key in cfg:raise ValueError("R33 shape oracle must not enter formal timed work")
    candidate=c["performance_group"]=="G3"
    expected={"enabled":True,"profile":"selected-model-step-durability-v1"}if candidate else None
    if mf.get("step_durability")!=expected or "evidence_io_budget"in mf:
        raise ValueError("formal durability switch/observer policy differs")
    return {"report":report.name,"sha256":spec["sha256"],"python_sources":len(newpy),
        "runtime_python_identical_to_R36":True,"r33_observer_removed_only":True,
        "historical_timing_reused":False,"scope":"R36 bounded NPU math/graph/durability evidence; not formal native speed or full task quality"}
def check(c,*,root=W,require_new_root=True):
    root=Path(root).resolve();common=bound(c,root)
    cfg,manifest=old.components._manifest(c,root)
    policy=old.validate_policy(c,cfg)
    if(c.get("r37_role")!="FINAL_SOURCE_FORMAL_G1_G3_FIRST_PAIR"
       or c.get("profile_diagnostic")is not None
       or c.get("request_timeout_seconds")!=1800
       or c.get("cache_free_floor")!=4*1024**3):
        raise ValueError("actual full40 formal contract and bounded resource floor required")
    if(c["graph_runtime"].get("candidate_enabled")is not policy["algorithm_on"]
       or c.get("r37_step_durability")is not policy["algorithm_on"]):
        raise ValueError("native/treatment axes differ")
    prior=prerequisite(c,root)
    raw=Path(c["raw_root"])
    if not raw.is_absolute()or(require_new_root and raw.exists()):
        raise ValueError("new immutable absolute formal root required")
    from independent_execution_deadline import deadline_epoch
    deadline_epoch(c["absolute_stop_utc"])
    return {"configuration_valid":True,"device_run":False,"source_bindings":len(common),
        "controller_sha256":c["host_controller_sha256"],"graph_runtime":c["graph_runtime"],
        "active_manifest_sha256":manifest,"policy":policy,"prerequisite":prior}

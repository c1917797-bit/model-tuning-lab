"""R40 current-source full40 native/G3 policy with equal actual targetwarm2."""
import hashlib,json,sys
from pathlib import Path
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits import r30_graph_formal_audit as retained
from host_audits.r39_target_warmups import warm_descriptors
BASE_SHA=retained.BASE_SHA
ENTRY="host_audits/r40_formal_policy.py"
NEW={"host_audits/r40_formal_policy.py","host_audits/r40_formal_controller.py",
     "host_audits/r40_formal_audit.py","host_audits/r40_formal_warm_workload.py",
     "host_audits/r40_formal_warm_evidence.py","host_audits/r40_launch_capsule.py","R39_THREE_ARM_DECISION_20261026.json",
     "R40_EQUAL_TARGET_WARM_FORMAL_PLAN_20261026.json"}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(root,name):return retained.native._read(retained.native._inside(root,name))
def check(c,*,root=W,require_new_root=True):
    root=Path(root).resolve();host=c.get("host_controller_source_sha256")
    retained.native._sources(root,host)
    prior=read(root,"TARGET_WARMUP_R39_A2_R1_20261026_CONTRACT.json")
    expected=set(prior["host_controller_source_sha256"])|NEW
    if(set(host)!=expected or host.get(ENTRY)!=sha(__file__)
       or any(host.get(n)!=h for n,h in prior["host_controller_source_sha256"].items())
       or c.get("r40_host",{}).get("source_sha256")!=host
       or c.get("host_controller_sha256")!=host["host_audits/r40_formal_controller.py"]
       or c.get("controller_sha256")!=BASE_SHA or c.get("base_controller_sha256")!=BASE_SHA
       or sha(root/"formal_r15_tp4.py")!=BASE_SHA):
        raise ValueError("actual R40 HOST and retained owner closure required")
    common=c.get("baseline_host_source_sha256")or c.get("cache_diagnostic",{}).get("source_sha256")
    retained.native._sources(root,common)
    if hashlib.sha256(json.dumps(common,sort_keys=True,separators=(",",":")).encode()).hexdigest()!=c.get("study_source_map_sha256"):
        raise ValueError("same complete common study source map required")
    group=c.get("performance_group");on=group=="G3"
    if(group not in("G1","G3")or c.get("r40_role")!="CURRENT_SOURCE_EQUAL_TARGETWARM2_FORMAL40_FIRST_PAIR"
       or c.get("formal_performance")is not True or c.get("formal_quality")is not False
       or c.get("profile_diagnostic")is not None or c.get("max_output_tokens")!=1024
       or c.get("request_timeout_seconds")!=1800 or c.get("cache_free_floor")!=4*1024**3
       or c.get("physical_npus")!=[0,1,2,3]or c.get("tp")!=4
       or c.get("absolute_stop_utc")!="2026-10-26T06:36:27Z"
       or c.get("r40_target_warmup_count")!=2 or type(c.get("r40_target_warmup_count"))is not int
       or c.get("r40_warm_descriptors")!=warm_descriptors(c["formal_token_artifact"])
       or c.get("r40_minimum_remaining_seconds")!=(3600 if on else 5400)):
        raise ValueError("exact current authority/full40/fixed1024/equal2warm ruler required")
    plan_name="R40_EQUAL_TARGET_WARM_FORMAL_PLAN_20261026.json"
    plan=read(root,plan_name);p=plan["protocol"]
    if(p["requests"]!=40 or p["concurrency"]!=16 or p["fixed_output_tokens"]!=1024
       or p["extra_full_target_warmups"]!=2 or p["retries"]!=0 or plan["authority"]["stop_utc"]!=c["absolute_stop_utc"]):
        raise ValueError("predeclared equal warm formal plan drift")
    name="R39_THREE_ARM_DECISION_20261026.json";d=read(root,name);proof=d["independent_replay"]
    if(c.get("r40_prerequisite")!={"report":name,"sha256":sha(root/name)}
       or d["state"]!="SUPPORTED_BOUNDED_TARGET_WARMUP_COUNT_EFFECT"
       or d["all_three_arms_exact_released"]is not True or sha(proof["path"])!=proof["sha256"]):
        raise ValueError("actual independently replayed R39 decision required")
    raw=json.loads(Path(proof["path"]).read_bytes())
    if(raw["all_arms_actual16_and_fourworker_hot"]is not True or raw["native_speed_gain_proven"]is not False
       or raw["measured_unit_gain_percent"]<5 or raw["control_drift_percent"]>5):
        raise ValueError("bounded warm effect is not a native gain")
    for a in raw["arms"]:
        if sha(root/a["contract"])!=a["contract_sha256"]or sha(a["audit"])!=a["audit_sha256"]:
            raise ValueError("original R39 arm evidence drift")
    for key in("image","model","model_config_sha256","physical_npus","tp","port","hccl_ports","cpu_set",
               "enable_thinking","formal_token_artifact","enable_prefix_caching","enforce_eager","absolute_stop_utc"):
        if c.get(key)!=prior.get(key):raise ValueError("retained actual identity differs: "+key)
    cfg,manifest=retained.components._manifest(c,root)
    mf=read(root,c["successor_manifest"]);oldmf=read(root,prior["successor_manifest"])
    py={n:h for n,h in mf["source_sha256"].items()if n.endswith(".py")}
    oldpy={n:h for n,h in oldmf["source_sha256"].items()if n.endswith(".py")}
    if py!=oldpy or len(py)!=438:raise ValueError("actual accepted runtime438 must remain identical")
    want=read(root,"FORMAL_STEP_R37_"+group+"_CONFIG_20261025.json")
    if(cfg!=want or any(k in cfg for k in("r33_prefix_terminal_diagnostic","r33_prefix_terminal_only"))
       or mf.get("component_cost_budget")is not None or mf.get("evidence_io_budget")is not None
       or mf.get("step_durability")!=({"enabled":True,"profile":"selected-model-step-durability-v1"}if on else None)):
        raise ValueError("original formal math and observerOFF/durability axes required")
    axes=retained.validate_policy(c,cfg)
    if(axes["algorithm_on"]is not on or c["graph_runtime"].get("candidate_enabled")is not on
       or c.get("r40_step_durability")is not on):
        raise ValueError("actual native/HYPIC policy axes differ")
    previous=c.get("r40_previous_audit")
    if on:
        if type(previous)is not dict or previous.get("group")!="G1"or sha(previous["path"])!=previous["sha256"]:
            raise ValueError("exact accepted native predecessor audit required")
        accepted=json.loads(Path(previous["path"]).read_bytes())
        if(accepted.get("formal_r40_full40_valid")is not True or accepted.get("live_release_verified")is not True
           or accepted.get("r40_launch_identity",{}).get("group")!="G1"
           or accepted["r40_launch_identity"].get("host_sources")!=host
           or accepted["r40_launch_identity"].get("study_source_map_sha256")!=c["study_source_map_sha256"]):
            raise ValueError("actual valid released same-source native arm required")
    elif previous is not None:raise ValueError("native starts a fresh same-source pair")
    rawroot=Path(c["raw_root"])
    if not rawroot.is_absolute()or rawroot.is_symlink()or(require_new_root and rawroot.exists()):
        raise ValueError("new immutable absolute R40 root required")
    from independent_execution_deadline import deadline_epoch
    deadline_epoch(c["absolute_stop_utc"])
    return {"configuration_valid":True,"device_run":False,"controller_sha256":c["host_controller_sha256"],"source_bindings":len(common),"host_source_bindings":len(host),
        "runtime_python":438,"active_manifest_sha256":manifest,"policy":axes,
        "graph_runtime":c["graph_runtime"],"prerequisite":c["r40_prerequisite"],
        "scope":"Current accepted original mathematics, equal explicit2targetwarm+4preps/full40 ruler; no native speed claim before actual matched arms."}

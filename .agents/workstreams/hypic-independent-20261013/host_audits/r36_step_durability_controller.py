"""R36 same-source selected-step evidence durability A/B/A screen."""
import argparse,copy,hashlib,json,os,sys,threading,time
from pathlib import Path
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
import formal_r15_tp4 as base
import independent_formal_workload as workload_slot
from independent_warm_profile_workload import run_profile_workload
from host_audits import r30_graph_formal_controller as graph
from host_audits import r35_evidence_io_controller as prior
retained=graph.evidence
ENTRY="host_audits/r36_step_durability_controller.py"
BASE_SHA="bf55661d61618a7f83537ce6bf477b66e80ccaf097ac714938ceee9bdf199d33"
_LOCK=threading.Lock()
SPEC={"requests":16,"output_tokens":64,"max_iterations":16,"delay_iterations":0}
EXPERIMENT_KEYS={"r33_prefix_terminal_diagnostic","r33_prefix_terminal_only"}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def prerequisite(c,root):
    anchor_name="EVIDENCE_IO_R35_OBSERVE_R1_20261025_CONTRACT.json"
    reference=c["r36_prerequisite"];report_name="R35_DEVICE_IO_DECISION_20261025.json"
    for name in(anchor_name,report_name):
        if c["host_controller_source_sha256"].get(name)!=sha(root/name):
            raise ValueError("source-bound completed R35 prerequisite required")
    if reference["report"]!=report_name or reference["sha256"]!=sha(root/report_name):
        raise ValueError("R35 decision identity differs")
    decision=json.loads((root/report_name).read_bytes())
    if(decision["state"]!="VALID_MATERIAL_SELECTED_STEP_IO_BUDGET_NOT_SPEED_ACCEPTANCE"
       or decision["independent_audit"]["valid"]is not True
       or decision["independent_audit"]["exact_live_release_verified"]is not True
       or decision["opportunity"]["conditional_fsync_fraction"]<0.05
       or sha(decision["independent_audit"]["path"])!=decision["independent_audit"]["sha256"]):
        raise ValueError("measured material original IO budget required")
    old=json.loads((root/anchor_name).read_bytes())
    for key in("image","model","model_config_sha256","physical_npus","tp","port","hccl_ports",
               "cpu_set","enable_thinking","formal_token_artifact","enable_prefix_caching",
               "enforce_eager","graph_runtime","r33_protocol"):
        if c.get(key)!=old.get(key):raise ValueError("durability screen changed retained identity: "+key)
    old_mf=json.loads((root/old["successor_manifest"]).read_bytes())
    new_mf=json.loads((root/c["successor_manifest"]).read_bytes())
    old_py={n:h for n,h in old_mf["source_sha256"].items()if n.endswith(".py")}
    new_py={n:h for n,h in new_mf["source_sha256"].items()if n.endswith(".py")}
    added=set(new_py)-set(old_py);changed={n for n in old_py if new_py.get(n)!=old_py[n]}
    wanted={"independent_evidence_step_durability.py","step_durability_r36/__init__.py",
            "step_durability_r36/patch.py","step_durability_r36/sitecustomize.py"}
    if added!=wanted or changed!={"graph_candidate/worker_loader.py"}:
        raise ValueError("only own writer durability policy and bootstrap additions allowed")
    expected={"enabled":True,"profile":"selected-model-step-durability-v1"}if c["r33_arm"]=="B1"else None
    if(new_mf.get("step_durability")!=expected or new_mf.get("evidence_io_budget")is not None
       or new_mf.get("r36_code_checkpoint")!=c["r36_code_checkpoint"]):
        raise ValueError("exact source-bound durability switch/observeroff required")
    cfg=json.loads((root/new_mf["config"]).read_bytes())
    old_cfg=json.loads((root/old_mf["config"]).read_bytes())
    if cfg!=old_cfg or cfg.get("r33_prefix_terminal_only")is not False:
        raise ValueError("no algorithm or prefix-output treatment change allowed")
    return {"report":report_name,"sha256":reference["sha256"],"python_sources":len(new_py),
        "runtime_additions":sorted(added),"changed_own_loader":["graph_candidate/worker_loader.py"],
        "durability_enabled":c["r33_arm"]=="B1",
        "scope":"Same original math/event writes/guards, only default-off selected-step durability cadence changes. Measured original IO budget is an opportunity, not predicted speed."}

def check_contract(c,*,source_root=W,require_new_root=True):
    root=Path(source_root).resolve();sources=c["host_controller_source_sha256"]
    retained.native._sources(root,sources)
    if (sources.get(ENTRY)!=sha(__file__)or c["host_controller_sha256"]!=sha(__file__)
            or c["controller_sha256"]!=BASE_SHA or c["base_controller_sha256"]!=BASE_SHA
            or sha(base.__file__)!=BASE_SHA):
        raise ValueError("actual R33 HOST and unchanged owner identities required")
    if (c.get("r36_role")!="SELECTED_STEP_DURABILITY_SINGLE_VARIABLE_SCREEN"or c.get("r33_arm")not in("A1","B1","A2")
            or c.get("formal_performance")is not False or c.get("formal_quality")is not False
            or c.get("max_output_tokens")!=64 or c.get("profile_diagnostic")!=SPEC
            or c.get("performance_group")!="G3"or c.get("enable_prefix_caching")is not False
            or c.get("cache_free_floor")!=4*1024**3):
        raise ValueError("bounded unprofiled same-HYPIC durability screen required")
    cfg,manifest=retained.components._manifest(c,root)
    bound=c["cache_diagnostic"]["source_sha256"]
    retained.native._sources(root,bound)
    if hashlib.sha256(json.dumps(bound,sort_keys=True,separators=(",",":")).encode()).hexdigest()!=c["study_source_map_sha256"]:
        raise ValueError("same A/B source map required")
    prior=prerequisite(c,root)
    raw=Path(c["raw_root"])
    if not raw.is_absolute()or(require_new_root and raw.exists()):
        raise ValueError("new immutable absolute R33 root required")
    from independent_execution_deadline import deadline_epoch
    deadline_epoch(c["absolute_stop_utc"])
    return {"configuration_valid":True,"device_run":False,"controller_sha256":sha(__file__),
        "graph_runtime":c["graph_runtime"],"active_manifest_sha256":manifest,
        "source_bindings":len(bound),"prerequisite":prior,"arm":c["r33_arm"]}

# Retain the already-reviewed HOST warm48/8+39 proof and diagnostic workload.
run_unit=prior.run_unit

def run_contract(c,*,source_root=W):
    checked=check_contract(c,source_root=source_root)
    if not _LOCK.acquire(blocking=False):raise RuntimeError("one R33 driver per process")
    original_write=base.write;original_snapshot=base.snapshot
    original_workload=workload_slot.run_formal_workload;launches=0;units=0
    raw=Path(c["raw_root"])
    def write(root,name,data):
        nonlocal launches
        if name=="launch.json":
            if Path(root)!=raw or launches:raise ValueError("one exact R33 launch")
            launches+=1;graph.rewrite_launch(data,c,checked)
            argv=data["argv"];old_path="PYTHONPATH=/probe/graph_candidate/bootstrap:/probe:"
            matches=[i for i,x in enumerate(argv)if x.startswith(old_path)]
            if len(matches)!=1:raise ValueError("one source-owned bootstrap path required")
            i=matches[0];argv[i]=argv[i].replace(old_path,"PYTHONPATH=/probe/evidence_io_r35:/probe:",1)
            image_index=argv.index(c["image"])
            argv[image_index:image_index]=["-e","INDEPENDENT_PREFIX_TERMINAL_ONLY=0","-e","INDEPENDENT_EVIDENCE_IO_BUDGET=0",
                "-e","INDEPENDENT_EVIDENCE_STEP_DURABILITY="+("1"if c["r33_arm"]=="B1"else"0")]
            if "--profiler-config"in data["argv"]:raise ValueError("R33 cannot enable profiler")
            data["r33_trial"]={"arm":c["r33_arm"],"profiler_enabled":False,
                "host_sources":c["host_controller_source_sha256"],"diagnostic":SPEC,
                "owner_branch_adapter":"formal_performance branch with explicit HOST diagnostic workload substitution"}
        return original_write(root,name,data)
    def snapshot(cid=None):
        result=original_snapshot(cid)
        if cid:
            stat=os.statvfs("/cache")
            if stat.f_bavail*stat.f_frsize<c["cache_free_floor"]:
                base.stop_owned_on_foreign(cid,image=c["image"])
                raise RuntimeError("R33 storage floor stopped exact owned service")
        return result
    def unit(*args,**kwargs):
        nonlocal units
        units+=1
        if units!=1:raise ValueError("one bounded R36 workload")
        return run_unit(*args,**kwargs,raw=raw,manifest=checked["active_manifest_sha256"],contract=c)
    live=copy.deepcopy(c);live["formal_performance"]=True
    # Only select the retained owner's workload branch. The actual unit remains
    # explicitly diagnostic and both contracts/launch receipts state this.
    base.write=write;base.snapshot=snapshot;workload_slot.run_formal_workload=unit
    try:
        result=base.run_contract(live)
        if launches!=1 or units!=1:raise ValueError("actual R33 launch/workload missing")
        return result
    finally:
        if base.write is write:base.write=original_write
        if base.snapshot is snapshot:base.snapshot=original_snapshot
        if workload_slot.run_formal_workload is unit:workload_slot.run_formal_workload=original_workload
        _LOCK.release()

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True);p.add_argument("--run",action="store_true")
    a=p.parse_args();c=json.loads(Path(a.contract).read_bytes())
    if a.run:run_contract(c)
    else:print(json.dumps(check_contract(c)))

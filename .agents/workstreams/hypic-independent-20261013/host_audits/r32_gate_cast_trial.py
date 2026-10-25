"""R32 HOST-only A/B/A diagnostic, no profiler, unchanged guard/cleanup owner."""
import argparse,copy,hashlib,json,os,sys,threading,time
from pathlib import Path
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
import formal_r15_tp4 as base
import independent_formal_workload as workload_slot
from independent_warm_profile_workload import run_profile_workload
from host_audits import r30_graph_formal_controller as graph
retained=graph.evidence
ENTRY="host_audits/r32_gate_cast_trial.py"
BASE_SHA="bf55661d61618a7f83537ce6bf477b66e80ccaf097ac714938ceee9bdf199d33"
_LOCK=threading.Lock()
SPEC={"requests":16,"output_tokens":64,"max_iterations":16,"delay_iterations":0}
EXPERIMENT_KEYS={"c1_gate_cast_diagnostic","c1_gate_cast_hoist"}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def prerequisite(c,root):
    anchor=root/"FORMAL_GRAPH_R30_G3_R1_20261025_CONTRACT.json"
    if sha(anchor)!="278fc2663df36a562d2b65b3bb291d1bcfe6fab5bc2a89ff089b0b9fc84a3489":
        raise ValueError("original R30 source anchor drift")
    old=json.loads(anchor.read_bytes());prior=retained.prerequisite(old,root)
    for key in("image","model","model_config_sha256","physical_npus","tp","port","hccl_ports",
               "cpu_set","enable_thinking","formal_token_artifact","enable_prefix_caching",
               "enforce_eager","graph_runtime","absolute_stop_utc"):
        if c.get(key)!=old.get(key):raise ValueError("R32 changed retained identity: "+key)
    old_mf=json.loads((root/old["successor_manifest"]).read_bytes())
    new_mf=json.loads((root/c["successor_manifest"]).read_bytes())
    old_py={n:h for n,h in old_mf["source_sha256"].items()if n.endswith(".py")}
    new_py={n:h for n,h in new_mf["source_sha256"].items()if n.endswith(".py")}
    changed={n for n in set(old_py)|set(new_py)if old_py.get(n)!=new_py.get(n)}
    if changed!={"independent_recurrent_boundary.py","graph_candidate/activation.py","independent_gate_cast_delivery.py"}:
        raise ValueError("only named gate-cast runtime source seams may differ")
    cfg=json.loads((root/new_mf["config"]).read_bytes())
    old_cfg=json.loads((root/old_mf["config"]).read_bytes())
    if {k:v for k,v in cfg.items()if k not in EXPERIMENT_KEYS}!=old_cfg:
        raise ValueError("R32 changed another algorithm/guard/logging parameter")
    if cfg.get("c1_gate_cast_diagnostic")is not True or cfg.get("c1_gate_cast_hoist")is not(c["r32_arm"]=="B1"):
        raise ValueError("one exact hoist boolean differs between A/B")
    return dict(prior,scope="Original historical graph/numerical source anchor only; new gate placement needs actual first-shape private NPU checks.",
                runtime_differences=sorted(changed),python_sources=len(new_py))

def check_contract(c,*,source_root=W,require_new_root=True):
    root=Path(source_root).resolve();sources=c["host_controller_source_sha256"]
    retained.native._sources(root,sources)
    if (sources.get(ENTRY)!=sha(__file__)or c["host_controller_sha256"]!=sha(__file__)
            or c["controller_sha256"]!=BASE_SHA or c["base_controller_sha256"]!=BASE_SHA
            or sha(base.__file__)!=BASE_SHA):
        raise ValueError("actual R32 HOST and unchanged owner identities required")
    if (c.get("r32_role")!="UNPROFILED_GATE_CAST_A_B_A"or c.get("r32_arm")not in("A1","B1","A2")
            or c.get("formal_performance")is not False or c.get("formal_quality")is not False
            or c.get("max_output_tokens")!=64 or c.get("profile_diagnostic")!=SPEC
            or c.get("performance_group")!="G3"or c.get("enable_prefix_caching")is not False
            or c.get("cache_free_floor")!=4*1024**3):
        raise ValueError("bounded unprofiled same-HYPIC diagnostic required")
    cfg,manifest=retained.components._manifest(c,root)
    bound=c["cache_diagnostic"]["source_sha256"]
    retained.native._sources(root,bound)
    if hashlib.sha256(json.dumps(bound,sort_keys=True,separators=(",",":")).encode()).hexdigest()!=c["study_source_map_sha256"]:
        raise ValueError("same A/B source map required")
    prior=prerequisite(c,root)
    raw=Path(c["raw_root"])
    if not raw.is_absolute()or(require_new_root and raw.exists()):
        raise ValueError("new immutable absolute R32 root required")
    from independent_execution_deadline import deadline_epoch
    deadline_epoch(c["absolute_stop_utc"])
    return {"configuration_valid":True,"device_run":False,"controller_sha256":sha(__file__),
        "graph_runtime":c["graph_runtime"],"active_manifest_sha256":manifest,
        "source_bindings":len(bound),"prerequisite":prior,"arm":c["r32_arm"]}

def run_unit(artifact,*,send_warmup,send_measured,guard,record,require_material_ready):
    times={}
    names={"profile-private-warmup":"r32-private-warmup","profile-start":"r32-begin",
           "profile-response":"r32-response","profile-stop":"r32-end"}
    def control(action):
        if action=="start_profile":
            if times:raise ValueError("duplicate R32 start")
            times["start"]=time.monotonic()
        elif action=="stop_profile":times["stop"]=time.monotonic()
        else:raise ValueError("unexpected diagnostic control")
        return {"profiler_enabled":False,"action":"begin"if action=="start_profile"else"end"}
    def log(item):
        item=dict(item,event=names.get(item.get("event"),item.get("event")))
        record(item)
    unit=run_profile_workload(artifact,SPEC,send=send_warmup,control=control,
        guard=guard,record=log,require_material_ready=require_material_ready)
    if set(times)!={"start","stop"}or not times["stop"]>times["start"]:
        raise ValueError("complete unprofiled client time envelope required")
    unit["diagnostic_makespan_seconds"]=times["stop"]-times["start"]
    unit["profiler_enabled"]=False
    unit["scope"]="Unprofiled integrated16/c16/32768/64 single-variable diagnostic, not formal1024 performance or fullquality."
    return unit

def run_contract(c,*,source_root=W):
    checked=check_contract(c,source_root=source_root)
    if not _LOCK.acquire(blocking=False):raise RuntimeError("one R32 driver per process")
    original_write=base.write;original_snapshot=base.snapshot
    original_workload=workload_slot.run_formal_workload;launches=0;units=0
    raw=Path(c["raw_root"])
    def write(root,name,data):
        nonlocal launches
        if name=="launch.json":
            if Path(root)!=raw or launches:raise ValueError("one exact R32 launch")
            launches+=1;graph.rewrite_launch(data,c,checked)
            if "--profiler-config"in data["argv"]:raise ValueError("R32 cannot enable profiler")
            data["r32_trial"]={"arm":c["r32_arm"],"profiler_enabled":False,
                "host_sources":c["host_controller_source_sha256"],"diagnostic":SPEC,
                "owner_branch_adapter":"formal_performance branch with explicit HOST diagnostic workload substitution"}
        return original_write(root,name,data)
    def snapshot(cid=None):
        result=original_snapshot(cid)
        if cid:
            stat=os.statvfs("/cache")
            if stat.f_bavail*stat.f_frsize<c["cache_free_floor"]:
                base.stop_owned_on_foreign(cid,image=c["image"])
                raise RuntimeError("R32 storage floor stopped exact owned service")
        return result
    def unit(*args,**kwargs):
        nonlocal units
        units+=1
        if units!=1:raise ValueError("one bounded R32 workload")
        return run_unit(*args,**kwargs)
    live=copy.deepcopy(c);live["formal_performance"]=True
    # Only select the retained owner's workload branch. The actual unit remains
    # explicitly diagnostic and both contracts/launch receipts state this.
    base.write=write;base.snapshot=snapshot;workload_slot.run_formal_workload=unit
    try:
        result=base.run_contract(live)
        if launches!=1 or units!=1:raise ValueError("actual R32 launch/workload missing")
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

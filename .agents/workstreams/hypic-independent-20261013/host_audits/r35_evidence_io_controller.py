"""R35 selected-step evidence emitter/fsync cost observation; no IO treatment."""
import argparse,copy,hashlib,json,os,sys,threading,time
from pathlib import Path
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
import formal_r15_tp4 as base
import independent_formal_workload as workload_slot
from independent_warm_profile_workload import run_profile_workload
from host_audits import r30_graph_formal_controller as graph
retained=graph.evidence
ENTRY="host_audits/r35_evidence_io_controller.py"
BASE_SHA="bf55661d61618a7f83537ce6bf477b66e80ccaf097ac714938ceee9bdf199d33"
_LOCK=threading.Lock()
SPEC={"requests":16,"output_tokens":64,"max_iterations":16,"delay_iterations":0}
EXPERIMENT_KEYS={"r33_prefix_terminal_diagnostic","r33_prefix_terminal_only"}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def prerequisite(c,root):
    anchor=root/"PREFIX_TERMINAL_R34_A1_RENEWAL_20261025_CONTRACT.json"
    if sha(anchor)!="177e1963058b90509b9b5d827f0650876488d71e32a0d43ba5485cab3126544f":
        raise ValueError("retained R34 control source anchor changed")
    old=json.loads(anchor.read_bytes())
    reference=c["r35_prerequisite"];p=root/reference["report"]
    if reference["report"]!="R34_THREE_ARM_DECISION_20261025.json"or sha(p)!=reference["sha256"]:
        raise ValueError("sealed valid R34 decision required")
    d=json.loads(p.read_bytes())
    if d["state"]!="INSUFFICIENT_NET_GAIN_AT_SCREEN_THRESHOLD"or d["independent_audits_replayed"]is not True:
        raise ValueError("prior measured route decision changed")
    for arm in d["arms"]:
        if sha(root/arm["contract"])!=arm["contract_sha256"]or sha(arm["audit"])!=arm["audit_sha256"]:
            raise ValueError("historical control/audit archive changed")
    for key in("image","model","model_config_sha256","physical_npus","tp","port","hccl_ports",
               "cpu_set","enable_thinking","formal_token_artifact","enable_prefix_caching",
               "enforce_eager","graph_runtime","r33_protocol"):
        if c.get(key)!=old.get(key):raise ValueError("IO diagnostic changed retained identity: "+key)
    old_mf=json.loads((root/old["successor_manifest"]).read_bytes())
    new_mf=json.loads((root/c["successor_manifest"]).read_bytes())
    old_py={n:h for n,h in old_mf["source_sha256"].items()if n.endswith(".py")}
    new_py={n:h for n,h in new_mf["source_sha256"].items()if n.endswith(".py")}
    added=set(new_py)-set(old_py)
    changed={n for n in old_py if new_py.get(n)!=old_py[n]}
    wanted={"independent_evidence_io_budget.py","evidence_io_r35/__init__.py",
            "evidence_io_r35/patch.py","evidence_io_r35/sitecustomize.py"}
    if added!=wanted or changed!={"graph_candidate/worker_loader.py"}:
        raise ValueError("only own loader observer and four named additions allowed")
    if(new_mf.get("evidence_io_budget")!={"enabled":True,"profile":"owned-evidence-io-budget-v1"}
       or new_mf.get("r35_code_checkpoint")!=c["r35_code_checkpoint"]):
        raise ValueError("explicit source-bound IO observation required")
    cfg=json.loads((root/new_mf["config"]).read_bytes())
    old_cfg=json.loads((root/old_mf["config"]).read_bytes())
    if cfg!=old_cfg or cfg.get("r33_prefix_terminal_only")is not False:
        raise ValueError("no algorithm or prefix-output treatment change allowed")
    return {"report":reference["report"],"sha256":reference["sha256"],"python_sources":len(new_py),
        "runtime_additions":sorted(added),"changed_own_loader":["graph_candidate/worker_loader.py"],
        "scope":"R34 valid numerical/hot control, unchanged algorithm Python and original emitter/fsync; only bounded IO observer wiring changed. Not formal quality/speed."}

def check_contract(c,*,source_root=W,require_new_root=True):
    root=Path(source_root).resolve();sources=c["host_controller_source_sha256"]
    retained.native._sources(root,sources)
    if (sources.get(ENTRY)!=sha(__file__)or c["host_controller_sha256"]!=sha(__file__)
            or c["controller_sha256"]!=BASE_SHA or c["base_controller_sha256"]!=BASE_SHA
            or sha(base.__file__)!=BASE_SHA):
        raise ValueError("actual R33 HOST and unchanged owner identities required")
    if (c.get("r35_role")!="OWNED_EMITTER_FSYNC_BUDGET_DIAGNOSTIC"or c.get("r33_arm")!="A1"
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
        raise ValueError("new immutable absolute R33 root required")
    from independent_execution_deadline import deadline_epoch
    deadline_epoch(c["absolute_stop_utc"])
    return {"configuration_valid":True,"device_run":False,"controller_sha256":sha(__file__),
        "graph_runtime":c["graph_runtime"],"active_manifest_sha256":manifest,
        "source_bindings":len(bound),"prerequisite":prior,"arm":c["r33_arm"]}

def run_unit(artifact,*,send_warmup,send_measured,guard,record,require_material_ready,raw,manifest,contract):
    from concurrent.futures import ThreadPoolExecutor,as_completed
    from independent_formal_warmups import build_warmups,execute_warmups
    from host_audits.r33_prefix_terminal_evidence import pre_timing_proof
    data=Path(artifact["path"]).read_bytes()
    if hashlib.sha256(data).hexdigest()!=artifact["sha256"]:raise ValueError("same input bytes required")
    inputs=json.loads(data);cases=inputs["requests"][:16]
    if len(cases)!=16 or any(len(x["token_ids"])!=32768 for x in cases):raise ValueError("exact c16 input required")
    execute_warmups(build_warmups(inputs),send=send_warmup,guard=guard,record=record,
                    require_material_ready=require_material_ready)
    def one(case):
        began=time.monotonic();guard()
        try:
            response=send_warmup({"model":"qwen3.5","prompt":case["token_ids"],"temperature":0,"seed":0,
                "max_tokens":64,"ignore_eos":True})
            if response["usage"]["prompt_tokens"]!=32768 or response["usage"]["completion_tokens"]!=64:
                raise ValueError("exact diagnostic token count required")
            return {"index":case["index"],"ok":True,"response":response,"elapsed_seconds":time.monotonic()-began}
        except Exception as exc:return {"index":case["index"],"ok":False,"error":{"type":type(exc).__name__,"message":str(exc)}}
    def wave(event,number):
        result=[]
        with ThreadPoolExecutor(max_workers=16)as pool:
            for f in as_completed([pool.submit(one,x)for x in cases]):
                item=f.result();result.append(item);record(dict(item,event=event,wave=number,scored=False));guard()
        if len(result)!=16 or not all(x["ok"]for x in result):raise RuntimeError("bounded R33 wave failed")
        return result
    warm=[]
    for number in range(3):warm.extend(wave("r33-private-warmup",number))
    guard()
    from host_audits.r30b_graph_formal_audit import parse_info_graph
    from host_audits.r34_live_native_log import take_owned_log
    native_data,native_receipt=take_owned_log(raw,contract,backend=base)
    info=parse_info_graph(native_data)
    proof=pre_timing_proof(raw,info["workers"],manifest)
    proof["native_log_snapshot"]=native_receipt
    record(dict(proof,event="r33-warm-proof",scored=False))
    began=time.monotonic();record({"event":"r33-begin","scored":False,"profiler_enabled":False})
    results=wave("r33-response",0)
    elapsed=time.monotonic()-began
    record({"event":"r33-end","scored":False,"profiler_enabled":False})
    return {"valid":True,"results":results,"private_warmup_results":warm,
        "input_sha256":artifact["sha256"],"diagnostic_makespan_seconds":elapsed,
        "warm_proof":proof,"profiler_enabled":False,
        "scope":"Unprofiled integrated16/c16/32768/64;48privatewarm and actual shape-proof before timer. Not formal1024/quality."}

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
            argv[image_index:image_index]=["-e","INDEPENDENT_PREFIX_TERMINAL_ONLY=0","-e","INDEPENDENT_EVIDENCE_IO_BUDGET=1"]
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
        if units!=1:raise ValueError("one bounded R33 workload")
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

"""R38 single bounded component observation; unchanged owner owns admission/cleanup."""
import argparse,concurrent.futures,copy,hashlib,json,os,sys,threading,time
from pathlib import Path
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
import formal_r15_tp4 as base
import independent_formal_workload as workload_slot
from independent_formal_client import completion_payload
from independent_formal_warmups import build_warmups,execute_warmups
from host_audits import r30_graph_formal_controller as graph
native=graph.evidence.native
components=graph.evidence.components
ENTRY="host_audits/r38_component_controller.py"
BASE_SHA="bf55661d61618a7f83537ce6bf477b66e80ccaf097ac714938ceee9bdf199d33"
SPEC={"requests":16,"concurrency":16,"output_tokens":1024,"unscored_preparations":4,"retries":0}
_LOCK=threading.Lock()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def prerequisite(c,root):
    name="R37_FIRST_PAIR_DECISION_20261026.json"
    if c["host_controller_source_sha256"].get(name)!=sha(root/name):
        raise ValueError("sealed R37 negative pair binding required")
    prior=json.loads((root/name).read_bytes())
    if(prior["state"]!="FIRST_PAIR_VALID_NO_NATIVE_SPEED_GAIN"
       or prior["native_speed_gain_proven"]is not False
       or prior["exact_live_release_verified_both"]is not True):
        raise ValueError("actual retained R37 terminal pair required")
    replay=prior["independent_replay"]
    if sha(replay["path"])!=replay["sha256"]:raise ValueError("R37 raw decision changed")
    for g in prior["groups"]:
        if sha(g["audit"])!=g["audit_sha256"]or sha(root/g["contract"])!=g["contract_sha256"]:
            raise ValueError("R37 immutable audit/contract changed")
    old=json.loads((root/"FORMAL_STEP_R37_G3_R2_20261025_CONTRACT.json").read_bytes())
    for k in("image","model","model_config_sha256","physical_npus","tp","port","hccl_ports","cpu_set",
             "enable_thinking","formal_token_artifact","enable_prefix_caching","enforce_eager","graph_runtime"):
        if c.get(k)!=old.get(k):raise ValueError("R38 retained identity differs: "+k)
    before=json.loads((root/old["successor_manifest"]).read_bytes())
    after=json.loads((root/c["successor_manifest"]).read_bytes())
    oldpy={n:h for n,h in before["source_sha256"].items()if n.endswith(".py")}
    newpy={n:h for n,h in after["source_sha256"].items()if n.endswith(".py")}
    added=set(newpy)-set(oldpy)
    wanted={"independent_component_cost_budget.py","component_budget_r38/__init__.py",
            "component_budget_r38/patch.py","component_budget_r38/sitecustomize.py"}
    if added!=wanted or {n for n in oldpy if newpy.get(n)!=oldpy[n]}!={"graph_candidate/worker_loader.py"}:
        raise ValueError("only owned observer/helper/bootstrap additions and loader may differ")
    cfg=json.loads((root/after["config"]).read_bytes())
    if cfg!=json.loads((root/before["config"]).read_bytes()):
        raise ValueError("R38 original algorithm configuration must remain identical")
    if(after.get("component_cost_budget")!={"enabled":True,"profile":"selected-component-cost-v1"}
       or after.get("step_durability")!={"enabled":True,"profile":"selected-model-step-durability-v1"}
       or after.get("evidence_io_budget")is not None or after.get("r38_code_checkpoint")!=c["r38_code_checkpoint"]):
        raise ValueError("exact explicit component observation/step durability switch required")
    if any(k in cfg for k in("r33_prefix_terminal_diagnostic","r33_prefix_terminal_only")):
        raise ValueError("R33 observer remains absent")
    return {"report":name,"sha256":sha(root/name),"raw_decision_sha256":replay["sha256"],
        "runtime_python":len(newpy),"original_math_sources_unchanged":True,
        "scope":"R37 first-pair negative retained; CPU-span observation is not a speed treatment."}
def check_contract(c,*,source_root=W,require_new_root=True):
    root=Path(source_root).resolve();sources=c["host_controller_source_sha256"]
    native._sources(root,sources)
    if(sources.get(ENTRY)!=sha(__file__)or c["host_controller_sha256"]!=sha(__file__)
       or sources.get("formal_r15_tp4.py")!=BASE_SHA or sha(base.__file__)!=BASE_SHA
       or c["controller_sha256"]!=BASE_SHA or c["base_controller_sha256"]!=BASE_SHA):
        raise ValueError("actual narrow HOST and unchanged owner identity required")
    if(c.get("r38_role")!="SELECTED_COMPONENT_COST_OBSERVATION"or c.get("r38_protocol")!=SPEC
       or c.get("formal_performance")is not False or c.get("formal_quality")is not False
       or c.get("performance_group")!="G3"or c.get("physical_npus")!=[0,1,2,3]or c.get("tp")!=4
       or c.get("max_output_tokens")!=1024 or c.get("cache_free_floor")!=4*1024**3
       or c.get("absolute_stop_utc")!="2026-10-26T06:36:27Z"
       or c.get("cache_diagnostic",{}).get("compact_manifest")!=c.get("successor_manifest")):
        raise ValueError("bounded16/fixed1024 single-TP4 diagnostic contract required")
    cfg,digest=components._manifest(c,root);bound=c["cache_diagnostic"]["source_sha256"]
    native._sources(root,bound)
    if hashlib.sha256(json.dumps(bound,sort_keys=True,separators=(",",":")).encode()).hexdigest()!=c["study_source_map_sha256"]:
        raise ValueError("frozen source map differs")
    prior=prerequisite(c,root);raw=Path(c["raw_root"])
    if not raw.is_absolute()or(require_new_root and raw.exists()):raise ValueError("new immutable raw root required")
    from independent_execution_deadline import deadline_epoch
    deadline_epoch(c["absolute_stop_utc"])
    return {"configuration_valid":True,"device_run":False,"controller_sha256":sha(__file__),
        "graph_runtime":c["graph_runtime"],"active_manifest_sha256":digest,"source_bindings":len(bound),
        "prerequisite":prior,"protocol":SPEC}
def run_unit(spec,*,send_warmup,send_measured,guard,record,require_material_ready):
    p=Path(spec["path"])
    if not p.is_absolute()or p.is_symlink()or p.stat().st_size>33554432:
        raise ValueError("bounded original token artifact required")
    data=p.read_bytes()
    if hashlib.sha256(data).hexdigest()!=spec["sha256"]:raise ValueError("R38 immutable input drift")
    artifact=json.loads(data);cases=artifact["requests"]
    if len(cases)!=40 or [c["index"]for c in cases]!=list(range(40)):
        raise ValueError("original exact40 artifact, explicit first16 selection required")
    execute_warmups(build_warmups(artifact),send=send_warmup,guard=guard,record=record,
                    require_material_ready=require_material_ready)
    payloads=[completion_payload(c)for c in cases[:16]]
    guard();started=time.monotonic();record({"event":"r38-begin","scored":False,"protocol":SPEC})
    def one(i):
        try:
            guard();result=send_measured(payloads[i]);guard()
            if(result.get("completion_tokens")!=1024 or result.get("usage",{}).get("prompt_tokens")!=32768
               or result.get("finish_reason")!="length"or not result.get("request_id")):
                raise ValueError("actual fixed32768/1024 stream required")
            return {"index":i,"ok":True,"metrics":result}
        except Exception as error:return {"index":i,"ok":False,"error":{"type":type(error).__name__,"message":str(error)}}
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=16)as pool:
        for future in concurrent.futures.as_completed([pool.submit(one,i)for i in range(16)]):
            item=future.result();record(dict(item,event="r38-response",scored=False));results.append(item)
    guard();span=time.monotonic()-started;results.sort(key=lambda r:r["index"])
    record({"event":"r38-end","scored":False,"requests":16})
    ids=[x["metrics"]["request_id"]for x in results if x["ok"]]
    return {"valid":len(ids)==len(set(ids))==16,"results":results,"requests":16,"concurrency":16,
        "retries":0,"output_tokens":1024,"input_sha256":spec["sha256"],"summary":None,
        "diagnostic_makespan_seconds":span,"protocol":SPEC,"formal_performance":False,
        "scope":"Single bounded observed16/c16/fixed1024 diagnostic; not formal40, paired speed or quality."}
def rewrite_launch(data,c,checked):
    graph.rewrite_launch(data,c,checked);argv=data["argv"]
    old="PYTHONPATH=/probe/graph_candidate/bootstrap:/probe:"
    matches=[i for i,x in enumerate(argv)if x.startswith(old)]
    if len(matches)!=1:raise ValueError("one actual graph bootstrap required")
    i=matches[0];argv[i]=argv[i].replace(old,"PYTHONPATH=/probe/component_budget_r38:/probe:",1)
    flags=["INDEPENDENT_COMPONENT_COST_BUDGET=1","INDEPENDENT_EVIDENCE_STEP_DURABILITY=1",
           "INDEPENDENT_EVIDENCE_IO_BUDGET=0","INDEPENDENT_PREFIX_TERMINAL_ONLY=0"]
    at=argv.index(c["image"]);argv[at:at]=sum((["-e",x]for x in flags),[])
    if any(argv.count(x)!=1 for x in flags)or "--profiler-config"in argv:
        raise ValueError("actual one explicit diagnostic switch per key required")
    if argv.count("INDEPENDENT_GRAPH_MANIFEST=/probe/"+c["successor_manifest"])!=1:
        raise ValueError("actual consumed manifest differs")
    data["r38_observation"]={"protocol":SPEC,"formal_performance":False,
        "host_sources":c["host_controller_source_sha256"],"bootstrap":"component_budget_r38",
        "original_component_functions_and_guards_unchanged":True}
    return data
def run_contract(c,*,source_root=W):
    checked=check_contract(c,source_root=source_root)
    if not _LOCK.acquire(blocking=False):raise RuntimeError("one R38 driver per process")
    original_write=base.write;original_snapshot=base.snapshot;original_workload=workload_slot.run_formal_workload
    launches=units=0;raw=Path(c["raw_root"])
    def write(root,name,data):
        nonlocal launches
        if name=="launch.json":
            if Path(root)!=raw or launches:raise ValueError("one exact actual R38 launch")
            launches+=1;rewrite_launch(data,c,checked)
        return original_write(root,name,data)
    def snapshot(cid=None):
        result=original_snapshot(cid)
        if cid:
            s=os.statvfs("/cache")
            if s.f_bavail*s.f_frsize<c["cache_free_floor"]:
                base.stop_owned_on_foreign(cid,image=c["image"])
                raise RuntimeError("storage floor stopped exact owned service")
        return result
    def unit(*a,**kw):
        nonlocal units
        units+=1
        if units!=1:raise ValueError("one R38 bounded workload")
        return run_unit(*a,**kw)
    live=copy.deepcopy(c);live["formal_performance"]=True
    base.write=write;base.snapshot=snapshot;workload_slot.run_formal_workload=unit
    try:
        result=base.run_contract(live)
        if launches!=1 or units!=1:raise ValueError("actual bounded launch/workload missing")
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

"""HOST R39 first-use target-path warmup-count contrast; unchanged runtime438."""
import argparse,copy,hashlib,json,os,sys,threading
from pathlib import Path
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits import r38_component_controller as prior
from host_audits.r39_target_warmups import run_unit as warmed_unit,warm_descriptors
base=prior.base;workload_slot=prior.workload_slot;native=prior.native;components=prior.components
BASE_SHA=prior.BASE_SHA;SPEC=prior.SPEC
ENTRY="host_audits/r39_warmup_controller.py"
_LOCK=threading.Lock()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check_contract(c,*,source_root=W,require_new_root=True):
    root=Path(source_root).resolve();sources=c["host_controller_source_sha256"]
    native._sources(root,sources)
    if(sources.get(ENTRY)!=sha(__file__)or c["host_controller_sha256"]!=sha(__file__)
       or sources.get("formal_r15_tp4.py")!=BASE_SHA or sha(base.__file__)!=BASE_SHA
       or c["controller_sha256"]!=BASE_SHA or c["base_controller_sha256"]!=BASE_SHA):
        raise ValueError("actual R39 HOST/unchanged owner identities required")
    arm=c.get("r39_arm");count=2 if arm=="B1"else 0
    if(c.get("r39_role")!="TARGET_PATH_WARMUP_COUNT_CAUSAL_SCREEN"or arm not in("A1","B1","A2")
       or c.get("r39_target_warmup_count")!=count or type(c.get("r39_target_warmup_count"))is not int
       or c.get("r38_protocol")!=SPEC or c.get("formal_performance")is not False or c.get("formal_quality")is not False
       or c.get("performance_group")!="G3"or c.get("physical_npus")!=[0,1,2,3]or c.get("tp")!=4
       or c.get("max_output_tokens")!=1024 or c.get("cache_free_floor")!=4*1024**3
       or c.get("absolute_stop_utc")!="2026-10-26T06:36:27Z"
       or c.get("cache_diagnostic",{}).get("compact_manifest")!=c.get("successor_manifest")):
        raise ValueError("one bounded16/fixed1024 warmup-count contrast required")
    cfg,digest=components._manifest(c,root);bound=c["cache_diagnostic"]["source_sha256"]
    native._sources(root,bound)
    if hashlib.sha256(json.dumps(bound,sort_keys=True,separators=(",",":")).encode()).hexdigest()!=c["study_source_map_sha256"]:
        raise ValueError("shared actual source map differs")
    basis=prior.prerequisite(c,root)
    name="R38_COMPONENT_COST_DECISION_20261026.json"
    if sources.get(name)!=sha(root/name):raise ValueError("actual observed component budget binding required")
    r38=json.loads((root/name).read_bytes());proof=r38["independent_audit"]
    if(r38["state"]!="VALID_COMPONENT_OBSERVATION_AUDITED_RELEASED_NO_SPEED_ACCEPTANCE"
       or proof["valid"]is not True or proof["exact_live_release_verified"]is not True
       or sha(proof["path"])!=proof["sha256"]or r38["source_bindings"]!=len(bound)
       or r38["runtime_python"]!=438):
        raise ValueError("actual R38 numerical/mechanism/source/release observation required")
    previous=c.get("r39_previous_audit")
    if arm=="A1":
        if previous is not None:raise ValueError("A1 must start from accepted R38 prerequisite")
    else:
        wanted="A1"if arm=="B1"else"B1"
        if(type(previous)is not dict or previous.get("arm")!=wanted or sha(previous["path"])!=previous["sha256"]):
            raise ValueError("exact accepted predecessor audit required")
        report=json.loads(Path(previous["path"]).read_bytes())
        if(report.get("valid")is not True or report.get("live_release_verified")is not True
           or report.get("r39_trial",{}).get("arm")!=wanted
           or report["r39_trial"].get("study_source_map_sha256")!=c["study_source_map_sha256"]
           or report["r39_trial"].get("host_sources")!=sources):
            raise ValueError("predecessor source/arm/valid/exact-release differs")
    desc=warm_descriptors(c["formal_token_artifact"])
    if c.get("r39_warm_descriptors")!=desc:raise ValueError("frozen full target warmup descriptors differ")
    raw=Path(c["raw_root"])
    if not raw.is_absolute()or(require_new_root and raw.exists()):raise ValueError("new immutable R39 raw root required")
    from independent_execution_deadline import deadline_epoch
    deadline_epoch(c["absolute_stop_utc"])
    return {"configuration_valid":True,"device_run":False,"controller_sha256":sha(__file__),
        "graph_runtime":c["graph_runtime"],"active_manifest_sha256":digest,"source_bindings":len(bound),
        "prerequisite":basis,"r38_budget":proof,"protocol":SPEC,"arm":arm,"target_warmup_count":count}
def rewrite_launch(data,c,checked):
    prior.rewrite_launch(data,c,checked)
    data["r39_trial"]={"arm":c["r39_arm"],"target_warmup_count":c["r39_target_warmup_count"],
        "warm_descriptors":c["r39_warm_descriptors"],"common_cache_preparations":4,
        "study_source_map_sha256":c["study_source_map_sha256"],"host_sources":c["host_controller_source_sha256"],
        "algorithm_changed":False,"formal_performance":False}
    return data
def run_contract(c,*,source_root=W):
    checked=check_contract(c,source_root=source_root)
    if not _LOCK.acquire(blocking=False):raise RuntimeError("one R39 driver per process")
    original_write=base.write;original_snapshot=base.snapshot;original_workload=workload_slot.run_formal_workload
    launches=units=0;raw=Path(c["raw_root"])
    def write(root,name,data):
        nonlocal launches
        if name=="launch.json":
            if Path(root)!=raw or launches:raise ValueError("one exact R39 launch")
            launches+=1;rewrite_launch(data,c,checked)
        return original_write(root,name,data)
    def snapshot(cid=None):
        result=original_snapshot(cid)
        if cid:
            s=os.statvfs("/cache")
            if s.f_bavail*s.f_frsize<c["cache_free_floor"]:
                base.stop_owned_on_foreign(cid,image=c["image"])
                raise RuntimeError("storage floor stopped exact owned R39 container")
        return result
    def unit(*a,**kw):
        nonlocal units
        units+=1
        if units!=1:raise ValueError("one bounded R39 workload")
        return warmed_unit(*a,**kw,target_warmups=c["r39_target_warmup_count"],
                           expected_warm_descriptors=c["r39_warm_descriptors"])
    live=copy.deepcopy(c);live["formal_performance"]=True
    base.write=write;base.snapshot=snapshot;workload_slot.run_formal_workload=unit
    try:
        result=base.run_contract(live)
        if launches!=1 or units!=1:raise ValueError("actual bounded R39 launch/workload missing")
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

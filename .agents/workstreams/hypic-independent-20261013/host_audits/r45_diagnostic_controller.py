"""HOST R45 observational owner: unchanged full40/warm2 execution and exact cleanup."""
import argparse,json,os,sys,threading,time
from pathlib import Path
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
import formal_r15_tp4 as base
import independent_formal_workload as workload_slot
from host_audits import r30_graph_formal_controller as graph
from host_audits import r45_diagnostic_policy as policy
from host_audits.r40_formal_warm_workload import run_unit
_LOCK=threading.Lock()
def check_contract(c,*,source_root=W,require_new_root=True):
    return policy.check(c,root=source_root,require_new_root=require_new_root)
def identity(c):
    return {"role":c["r45_role"],"diagnostic_only":True,"torch_profiler":False,"compilation_observer":True,"clock_proof":c["r45_clock_proof"],"group":c["performance_group"],"algorithm_on":c["performance_group"]=="G3",
        "step_durability":c["performance_group"]=="G3","component_observer":False,"io_observer":False,
        "prefix_observer":False,"target_warmups":2,"common_cache_preparations":4,
        "actual_workload":"retained independent_formal_workload full40 with HOST-only2targetwarm insertion",
        "host_sources":c["r45_host_source_sha256"],"study_source_map_sha256":c["study_source_map_sha256"]}
def rewrite_launch(data,c,checked):
    graph.rewrite_launch(data,c,checked);argv=data["argv"];on=c["performance_group"]=="G3"
    if on:
        prefix="PYTHONPATH=/probe/graph_candidate/bootstrap:/probe:"
        indexes=[i for i,x in enumerate(argv)if x.startswith(prefix)]
        if len(indexes)!=1:raise ValueError("one actual native graph bootstrap required")
        i=indexes[0];argv[i]=argv[i].replace(prefix,"PYTHONPATH=/probe/compilation_budget_r45:/probe:",1)
        idx=argv.index(c["image"]);argv[idx:idx]=["-e","INDEPENDENT_COMPILATION_BUDGET=1","-e","INDEPENDENT_COMPONENT_COST_BUDGET=0",
            "-e","INDEPENDENT_EVIDENCE_STEP_DURABILITY=1","-e","INDEPENDENT_EVIDENCE_IO_BUDGET=0",
            "-e","INDEPENDENT_PREFIX_TERMINAL_ONLY=0"]
        wanted={"INDEPENDENT_COMPILATION_BUDGET":"1","INDEPENDENT_COMPONENT_COST_BUDGET":"0","INDEPENDENT_EVIDENCE_STEP_DURABILITY":"1",
            "INDEPENDENT_EVIDENCE_IO_BUDGET":"0","INDEPENDENT_PREFIX_TERMINAL_ONLY":"0",
            "INDEPENDENT_GRAPH_MANIFEST":"/probe/"+c["successor_manifest"]}
        if any([x for x in argv if x.startswith(k+"=")]!=[k+"="+v]for k,v in wanted.items()):
            raise ValueError("actual compilation observation/stepdurable environment differs")
    elif any(x.startswith("INDEPENDENT_")or":/probe"in x for x in argv):
        raise ValueError("native group cannot import or mount algorithm")
    if "--profiler-config"in argv:raise ValueError("no profiler in formal pair")
    data["graph_runtime"]["bootstrap"]="compilation_budget_r45" if on else None
    if on:data["graph_runtime"]["pythonpath_change"]["to"]=argv[i]
    data["r45_launch_identity"]=identity(c)
    return data
def clock_sources():
    return {name:{"implementation":info.implementation,"monotonic":info.monotonic,"adjustable":info.adjustable,"resolution":info.resolution}
        for name in("monotonic","perf_counter")for info in(time.get_clock_info(name),)}
def clock_observation(snapshot):
    host=os.readlink("/proc/self/ns/time")
    pids={pid for n,pid in snapshot["processes"]}
    workers={str(pid):os.readlink("/proc/"+str(pid)+"/ns/time")for pid in pids}
    if any(value!=host for value in workers.values()):raise ValueError("actual worker/host monotonic namespace differs")
    return {"host_time_namespace":host,"process_time_namespaces":workers,"host_clock":clock_sources()}

def run_contract(c,*,source_root=W):
    checked=check_contract(c,source_root=source_root)
    policy.require_budget(c)
    if not _LOCK.acquire(blocking=False):raise RuntimeError("one R45 owner per process")
    original_write=base.write;original_snapshot=base.snapshot;original_unit=workload_slot.run_formal_workload
    launches=units=0;raw=Path(c["raw_root"])
    def write(root,name,data):
        nonlocal launches
        if name=="launch.json":
            if Path(root)!=raw or launches:raise ValueError("one exact R45 launch")
            launches+=1;rewrite_launch(data,c,checked)
        return original_write(root,name,data)
    def snapshot(cid=None):
        result=original_snapshot(cid)
        if cid:
            st=os.statvfs("/cache")
            if st.f_bavail*st.f_frsize<c["cache_free_floor"]:
                base.stop_owned_on_foreign(cid,image=c["image"])
                raise RuntimeError("storage floor stopped exact owned R45 service")
        result["r45_clock"] = clock_observation(result)
        return result
    def unit(*args,**kwargs):
        nonlocal units
        units+=1
        if units!=1:raise ValueError("one actual full40 unit required")
        return run_unit(*args,**kwargs,expected_warm_descriptors=c["r40_warm_descriptors"])
    base.write=write;base.snapshot=snapshot;workload_slot.run_formal_workload=unit
    try:
        result=base.run_contract(c)
        if launches!=1 or units!=1:raise ValueError("actual full40 owner launch/unit missing")
        return result
    finally:
        if base.write is write:base.write=original_write
        if base.snapshot is snapshot:base.snapshot=original_snapshot
        if workload_slot.run_formal_workload is unit:workload_slot.run_formal_workload=original_unit
        _LOCK.release()
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True);p.add_argument("--run",action="store_true")
    a=p.parse_args();c=json.loads(Path(a.contract).read_bytes())
    if a.run:run_contract(c)
    else:print(json.dumps(check_contract(c)))

"""Actual full40 owner with R37 source-bound delivery; default offline check."""
import argparse,json,os,sys,threading
from pathlib import Path
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
import formal_r15_tp4 as base
from host_audits import r30_graph_formal_controller as graph
from host_audits import r37_formal_policy as policy
_LOCK=threading.Lock()
def check_contract(c,*,source_root=W,require_new_root=True):
    return policy.check(c,root=source_root,require_new_root=require_new_root)
def rewrite_launch(data,c,checked):
    graph.rewrite_launch(data,c,checked)
    argv=data["argv"];on=c["performance_group"]=="G3"
    if on:
        prefix="PYTHONPATH=/probe/graph_candidate/bootstrap:/probe:"
        indexes=[i for i,x in enumerate(argv)if x.startswith(prefix)]
        if len(indexes)!=1:raise ValueError("one actual native graph bootstrap required")
        i=indexes[0];argv[i]=argv[i].replace(prefix,"PYTHONPATH=/probe/step_durability_r36:/probe:",1)
        argv[argv.index(c["image"]):argv.index(c["image"])]=[
            "-e","INDEPENDENT_EVIDENCE_STEP_DURABILITY=1","-e","INDEPENDENT_EVIDENCE_IO_BUDGET=0",
            "-e","INDEPENDENT_PREFIX_TERMINAL_ONLY=0"]
        expected={"INDEPENDENT_GRAPH_HYPIC":"1","INDEPENDENT_GRAPH_MANIFEST":"/probe/"+c["successor_manifest"],
                  "INDEPENDENT_GRAPH_RAW":"/scratch/diagnostics","INDEPENDENT_EVIDENCE_STEP_DURABILITY":"1",
                  "INDEPENDENT_EVIDENCE_IO_BUDGET":"0","INDEPENDENT_PREFIX_TERMINAL_ONLY":"0"}
        for name,value in expected.items():
            if[x for x in argv if x.startswith(name+"=")]!=[name+"="+value]:
                raise ValueError("actual base-consumed R37 environment differs: "+name)
    elif any(x.startswith("INDEPENDENT_")or":/probe"in x for x in argv):
        raise ValueError("native G1 may not import or mount algorithm")
    if "--profiler-config"in argv:raise ValueError("no profiler in formal pair")
    data["r37_launch_identity"]={"role":c["r37_role"],"algorithm_on":on,
        "step_durability":on,"io_observer":False,"prefix_observer":False,
        "actual_workload":"unchanged independent_formal_workload.run_formal_workload"}
    return data
def run_contract(c,*,source_root=W):
    checked=check_contract(c,source_root=source_root)
    if not _LOCK.acquire(blocking=False):raise RuntimeError("one owned R37 controller")
    original_write=base.write;original_snapshot=base.snapshot;launches=0
    raw=Path(c["raw_root"])
    def write(root,name,data):
        nonlocal launches
        if name=="launch.json":
            if Path(root)!=raw or launches:raise ValueError("one exact formal launch")
            launches+=1;rewrite_launch(data,c,checked)
        return original_write(root,name,data)
    def snapshot(cid=None):
        result=original_snapshot(cid)
        if cid:
            stat=os.statvfs("/cache")
            if stat.f_bavail*stat.f_frsize<c["cache_free_floor"]:
                base.stop_owned_on_foreign(cid,image=c["image"])
                raise RuntimeError("storage floor stopped exact owned service")
        return result
    base.write=write;base.snapshot=snapshot
    try:
        result=base.run_contract(c)
        if launches!=1:raise ValueError("actual formal launch absent")
        return result
    finally:
        if base.write is write:base.write=original_write
        if base.snapshot is snapshot:base.snapshot=original_snapshot
        _LOCK.release()
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True);p.add_argument("--run",action="store_true")
    a=p.parse_args();c=json.loads(Path(a.contract).read_bytes())
    if a.run:run_contract(c)
    else:print(json.dumps(check_contract(c)))

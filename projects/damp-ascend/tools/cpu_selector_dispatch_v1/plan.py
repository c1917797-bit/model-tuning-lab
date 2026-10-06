#!/usr/bin/env python3
"""Read-only CPU selector dispatch planning. Never creates, starts or stops a container."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

REPO=Path("/opt/host/vnf/austinov/model-tuning-lab")
PROJECT=REPO/"projects/damp-ascend"
RESULTS=Path("/cache/cch/qwen36-damp-20261006")
PYTHON="/usr/local/python3.12.13/bin/python3"
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
NAME="qwen36_damp_cpu_selector_20261006_v1"
CANARY_NAME="qwen36_damp_cpu_selector_preflight_20261006_v2"
MODEL=Path("/cache/efim/Qwen3.6-27B")
POST=PROJECT/"tools/post_reference_plan_v1"
POST_PINS={
 "post_reference_contract.py":"643f0ce23c7e6a45471f2e8d37439634ab74e27a92c90ed47ea9767312ce4e78",
 "run.py":"a5196a4283a5d88e5d2418dcc7e64bc652131507d574484b2781a595739c6771",
 "test_contract.py":"9a57157039d77041f4e2a08b803644ca304ccbfde901deb1160bcf9d4d49bb9f",
 "MANIFEST.json":"c57a9cde12eb00c4895894958ae004e3dedc2644f323f2682706da12b26e5423",
 "READY.md":"5e33131b6e6fe6510be8197a70c4f00fda0326081e8305957bb6a0046ce32cda"}
GIB=1024**3

def require(ok,message):
    if not ok:raise ValueError(message)

def parent_contract():
    import hashlib
    for name,expected in POST_PINS.items():
        path=POST/name
        require(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==expected,
                "frozen parent dispatch source drift: "+name)
    spec=importlib.util.spec_from_file_location("damp_cpu_dispatch_parent",POST/"post_reference_contract.py")
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    value.frozen_modules();value.manifest_identity()
    return value

def protection_roots(results,output):
    results=Path(results).resolve(strict=True);output=Path(output)
    require(output.parent.resolve()==results and not output.exists() and not output.is_symlink(),
            "new direct child output; old plans cannot be overwritten")
    children=sorted(results.iterdir(),key=lambda p:p.name)
    require(len(children)<=256,"bounded explicit result-child read-only mount list required")
    for path in children:
        require(not path.is_symlink() and path.resolve().parent==results and
                (path.is_dir() or path.is_file()) and "," not in str(path),
                "symlink/nonordinary result child requires independent review")
    return children

def create_argv(children,name=CANARY_NAME,command=None):
    # All existing result children are explicitly RO; only new children may be created.
    args=["docker","create","--name",name,"--label","model-tuning-lab.cpu-selector-owner=main-cpu-selector-v1",
        "--network","none","--cap-drop","ALL","--security-opt","no-new-privileges",
        "--memory","4g","--memory-swap","4g","--cpus","2","--pids-limit","512",
        "--workdir",str(REPO),"--entrypoint",PYTHON]
    for key,value in {
        "PYTHONDONTWRITEBYTECODE":"1","DAMP_CALIBRATION_CPU_ONLY":"1",
        "ASCEND_RT_VISIBLE_DEVICES":"","CUDA_VISIBLE_DEVICES":"",
        "OMP_NUM_THREADS":"8","MKL_NUM_THREADS":"8","TORCH_DEVICE_BACKEND_AUTOLOAD":"0",
        "PYTHONPATH":str(PROJECT/"calibration")+":"+str(PROJECT/"collector")}.items():
        args+=["--env",key+"="+value]
    for path,readonly in [(REPO,True),(MODEL,True),(RESULTS,False)]+[(p,True) for p in children]:
        args+=["--mount","type=bind,src="+str(path)+",dst="+str(path)+(",readonly" if readonly else "")]
    # Default entrypoint is the read-only canary; finalized selector uses a distinct container.
    canary_command=["-B","-c",
        "import os,runpy,sys,torch; assert not os.path.exists('/dev/davinci0'); "
        "assert not os.path.exists('/dev/davinci4'); assert torch.empty(1).device.type=='cpu'; "
        "assert torch.__version__=='2.10.0+cpu'; "
        "assert 'torch_npu' not in sys.modules; "
        "sys.path.insert(0,'"+str(Path(__file__).resolve().parent)+"'); "
        "from plan import parent_contract; parent_contract(); "
        "sys.path.insert(0,'"+str(POST)+"'); "
        "sys.argv=['run.py']; runpy.run_path('"+str(POST/"run.py")+"',run_name='__main__')"]
    return args+[IMAGE]+(canary_command if command is None else command)

def packet(parent,children,lock_sha=None,result_sha=None):
    ready=bool(lock_sha and result_sha)
    # Fresh identity/inspection is MAIN-owned, never inferred from file existence or a template.
    result={"schema":"damp-cpu-selector-dispatch-plan/v1","status":"prepared-not-executed",
        "container_name":NAME,"image_id":IMAGE,"devices":[],"privileged":False,
        "canary_name":CANARY_NAME,"canary_create_argv":create_argv(children),
        "canary_start_argv":["docker","start","--attach",CANARY_NAME],"readonly_children":[str(p) for p in children],
        "output_dir":str(parent.PLANS),"host_mem_required_bytes":12*GIB,"ordinary_host_reserve_bytes":8*GIB,
        "container_memory_limit_bytes":4*GIB,"cpu_threads":8,"cpu_quota":2,"selector_create_argv":None,
        "reference_finalized":False,"launchable":False,"selector_executed":False,"npu_executed":False,
        "main_required_before_actual_launch":["fresh image/name/mount/no-device inspection",
            "actual canary exit0 receipt","fresh ordinary RAM>=12GiB and disk/cgroup/mount-headroom admission",
            "actual Docker NCPU>=2; any concurrent task CPU quotas considered together",
            "fresh RO child list and actual five POST file hashes before/after run",
            "actual parent terminal successful owned stop, RESULT and SOURCE_LOCK byte hashes",
            "distinct source-bound selector container (do not restart canary as selector)",
            "MAIN retained-output controller with 8GiB reserve and phase deadline"],
        "with_four_allT_shards_host_mem_required_bytes":44*GIB,
        "monitoring":["actual first three plan mtimes for steady-state estimate",
            "cgroup memory.current/peak and host MemAvailable","no automatic retry/no partial service admission"],
        "not_proven":["actual192 plans","NPU numerical/graph","service","E2E performance","task accuracy"]}
    if ready:
        # Source-hash-check finalized receipts, but still do not claim container/resource admission.
        parent.finalized(lock_sha,result_sha)
        result["reference_finalized"]=True
        result["selector_command"]=["-B",str(POST/"run.py"),"--execute",
            "--source-lock-sha256",lock_sha,"--parent-result-sha256",result_sha,
            "--output-dir",str(parent.PLANS)]
        result["selector_create_argv"]=create_argv(children,NAME,
            result["selector_command"])
        insertion=result["selector_create_argv"].index("--env")
        result["selector_create_argv"][insertion:insertion]=["--env","DAMP_POST_REFERENCE_CPU_EXECUTE=1"]
        result["selector_start_argv"]=["docker","start","--attach",NAME]
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-lock-sha256");p.add_argument("--parent-result-sha256")
    a=p.parse_args()
    require(bool(a.source_lock_sha256)==bool(a.parent_result_sha256),"both actual parent hashes required")
    parent=parent_contract()
    children=protection_roots(RESULTS,parent.PLANS)
    print(json.dumps(packet(parent,children,a.source_lock_sha256,a.parent_result_sha256),
        sort_keys=True,allow_nan=False));return 0

if __name__=="__main__":raise SystemExit(main())

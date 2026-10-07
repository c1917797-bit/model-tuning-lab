#!/usr/bin/env python3
"""MAIN-owned bounded immutable-image compilation, never maps a compute device."""
import argparse, hashlib, json, os, shutil, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab")
PROJECT=ROOT/"projects/kvbuffer-parallel-ascend"
BASE=PROJECT/"tools/split_gate_v2"
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
OWNER="kvbuffer-native-order-build-v2"
NAME="kvbuffer_native_order_v2_build_20261007"
OUT=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006/build-native-order-v2-20261007-0924")
MEM=8*1024**3

def require(v,s):
    if not v:raise ValueError(s)
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def record(path,obj):
    with path.open("x") as f:f.write(json.dumps(obj,indent=2,allow_nan=False)+"\n")
def cmd(argv,*,timeout=60):
    p=subprocess.run(argv,capture_output=True,text=True,timeout=timeout)
    return {"command":argv,"exit_code":p.returncode,"stdout":p.stdout,"stderr":p.stderr}
def manifest():
    sys.path.insert(0,str(BASE));import contract
    ref={"path":str(BASE/"SOURCE_MANIFEST.json"),"sha256":digest(BASE/"SOURCE_MANIFEST.json")}
    require(ref["sha256"]=="508ff442ede945b8fb5930f79ee597ec1dba07e5d4e778d9abc85aafda6ce9c9","manifest differs")
    return contract.source_admission(ref)

def inside():
    require(os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD")=="0","no backend autoload")
    require(os.environ.get("PYTHONDONTWRITEBYTECODE")=="1","no bytecode")
    require(not list(Path("/dev").glob("davinci[0-9]*")),"compile cannot map compute devices")
    m,before=manifest()
    require(OUT.is_dir() and not (OUT/"build").exists(),"new build subdir")
    start=datetime.now(timezone.utc).isoformat(); commands=[]
    a=["cmake","-S",str(PROJECT/"operator/native_order_v2"),"-B",str(OUT/"build"),
       "-DCMAKE_BUILD_TYPE=Release","-DPython3_EXECUTABLE=/usr/local/python3.12.13/bin/python3"]
    for i,a in enumerate((a,["cmake","--build",str(OUT/"build"),"-j2"])):
        r=cmd(a,timeout=600);record(OUT/("command-%d.json"%i),r);commands.append(r)
        require(r["exit_code"]==0,"compile/link command failed, original retained")
    lib=OUT/"build/libqwen36_gdn_kvbuffer_native_order_v2_ops.so"
    require(lib.is_file() and not lib.is_symlink(),"ordinary actual library")
    export=cmd(["nm","-D","--defined-only",str(lib)]);record(OUT/"exports.json",export)
    require(export["exit_code"]==0,"nm failed")
    symbol="qwen36_gdn_kvbuffer_native_order_v2_kernel"
    matches=[line.split() for line in export["stdout"].splitlines() if line.split()[-1:]==[symbol]]
    require(len(matches)==1 and matches[0][-2] in ("T","W"),"ASC kernel not defined")
    _,after=manifest();require(before==after,"source changed during build")
    receipt={"schema":"kvbp.native-order-build/v2","status":"compiled_no_device",
             "npu_executed":False,"image_id":IMAGE,"namespace":"qwen36_kvbuffer_native_order_v2",
             "sources":m["operator_sources"],"npu_arch":"dav-2201",
             "library_sha256":digest(lib),"commands":commands,
             "exported_kernel":{"name":symbol,"defined":True,"type":matches[0][-2]},
             "sources_before":before,"sources_after":after,
             "started_utc":start,"completed_utc":datetime.now(timezone.utc).isoformat()}
    record(OUT/"build-receipt.json",receipt)
    print(json.dumps({"build_receipt":str(OUT/"build-receipt.json"),
                     "build_sha256":digest(OUT/"build-receipt.json"),
                     "library":str(lib),"library_sha256":digest(lib),"npu_executed":False}),flush=True)

def host():
    require(ROOT.resolve()==ROOT and OUT.parent.is_dir() and not OUT.parent.is_symlink(),
            "canonical paths")
    require(not OUT.exists() and not OUT.is_symlink(),"fresh unique output")
    m,_=manifest()
    info=cmd(["/usr/bin/docker","info","--format","{{json .}}"])
    require(info["exit_code"]==0,"Docker engine unavailable");engine=json.loads(info["stdout"])
    require(engine["NCPU"]>=3,"summed CPU capacity")
    mi={l.split(":")[0]:int(l.split()[1])*1024 for l in Path("/proc/meminfo").read_text().splitlines()
        if l.startswith(("MemAvailable:","MemTotal:","Hugetlb:"))}
    require(mi["MemAvailable"]>=MEM+8*1024**3,"8GiB cap + unchanged 8GiB ordinary reserve")
    require(shutil.disk_usage(OUT.parent).free>=13*1024**3,"5GiB build budget + 8GiB reserve")
    require(len(Path("/proc/1/mountinfo").read_text().splitlines())<95000,"mount reserve")
    old=cmd(["/usr/bin/docker","ps","-a","--filter","name=^/"+NAME+"$","--format","{{.ID}}"])
    require(old["exit_code"]==0 and not old["stdout"].strip(),"no duplicate container")
    OUT.mkdir()
    record(OUT/"host-preflight.json",{"memory":mi,"engine_cpus":engine["NCPU"],
                                    "npu_executed":False,"sources":m["operator_sources"],
                                    "fresh_utc":datetime.now(timezone.utc).isoformat()})
    argv=["/usr/bin/docker","create","--name",NAME,"--label","model-tuning-lab.owner="+OWNER,
          "--network","none","--cap-drop","ALL","--security-opt","no-new-privileges",
          "--cpus","1","--memory",str(MEM),"--memory-swap",str(MEM),"--pids-limit","512",
          "--env","TORCH_DEVICE_BACKEND_AUTOLOAD=0","--env","PYTHONDONTWRITEBYTECODE=1",
          "--env","OMP_NUM_THREADS=1","--env","ASCEND_RT_VISIBLE_DEVICES=",
          "--mount","type=bind,src="+str(ROOT)+",dst="+str(ROOT)+",readonly",
          "--mount","type=bind,src="+str(OUT)+",dst="+str(OUT),
          "--mount","type=bind,src=/usr/local/Ascend/driver,dst=/usr/local/Ascend/driver,readonly",
          "--workdir",str(ROOT),"--entrypoint","/bin/bash",IMAGE,"-c","exec sleep infinity"]
    created=cmd(argv);record(OUT/"create.json",created)
    require(created["exit_code"]==0,"container create failed")
    cid=created["stdout"].strip();require(len(cid)==64,"exact owned ID")
    primary=None
    try:
        v=cmd(["/usr/bin/docker","inspect",cid]);record(OUT/"inspect-before.json",v)
        require(v["exit_code"]==0,"inspect");v=json.loads(v["stdout"])[0]
        require(v["Id"]==cid and v["Name"]=="/"+NAME and v["Image"]==IMAGE and
                v["Config"]["Labels"].get("model-tuning-lab.owner")==OWNER and
                not v["HostConfig"]["Privileged"] and not v["HostConfig"]["Devices"] and
                v["HostConfig"]["Memory"]==MEM,"exact no-device ownership")
        s=cmd(["/usr/bin/docker","start",cid]);record(OUT/"start.json",s)
        require(s["exit_code"]==0,"start failed")
        a=["/usr/bin/docker","exec",cid,"/bin/bash","-c",
           'source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"',
           "kvbp-build","/usr/local/python3.12.13/bin/python3","-B",str(Path(__file__).resolve()),"--inside"]
        run=cmd(a,timeout=1320);record(OUT/"original-build-child.json",run)
        require(run["exit_code"]==0,"real build child failed")
        print(json.dumps(run),flush=True)
    except BaseException as e:
        primary=e;print(json.dumps({"original_error":repr(e),"output":str(OUT)}),flush=True);raise
    finally:
        try:
            v=cmd(["/usr/bin/docker","inspect",cid]);record(OUT/"inspect-prestop.json",v)
            require(v["exit_code"]==0,"cleanup inspect");v=json.loads(v["stdout"])[0]
            require(v["Id"]==cid and v["Name"]=="/"+NAME and v["Image"]==IMAGE and
                    v["Config"]["Labels"].get("model-tuning-lab.owner")==OWNER and
                    not v["HostConfig"]["Devices"],"cleanup exact owned no-device target")
            s=cmd(["/usr/bin/docker","stop","--time","15",cid]);record(OUT/"stop.json",s)
            require(s["exit_code"]==0,"stop failed")
            v=cmd(["/usr/bin/docker","inspect",cid]);record(OUT/"inspect-stopped.json",v)
            require(v["exit_code"]==0 and json.loads(v["stdout"])[0]["State"]["Pid"]==0,
                    "actual owned process release")
        except BaseException as e:
            print(json.dumps({"secondary_cleanup_error":repr(e),"original_error":repr(primary)}),flush=True)
            if primary is None:raise

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
    p.add_argument("--inside",action="store_true");a=p.parse_args()
    if a.inside:inside()
    elif a.execute:host()
    else:print(json.dumps({"default_enabled":False,"npu_executed":False,"out":str(OUT)}))
if __name__=="__main__":main()

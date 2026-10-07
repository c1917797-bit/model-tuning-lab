#!/usr/bin/env python3
"""MAIN-owned namespace-only build successor v3. Operator ABI v2. DEFAULT OFF."""
import argparse, hashlib, io, json, os, shutil, subprocess, sys, tarfile, time
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab")
PROJECT=ROOT/"projects/kvbuffer-parallel-ascend"
BASE=PROJECT/"tools/native_copy_trace_v2"
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
OWNER="kvbuffer-native-copy-trace-build-v3"
NAME="kvbuffer_native_copy_trace_v3_build_20261007_1400"
OUT=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006/build-native-copy-trace-v3-20261007-1400")
MEM=8*1024**3
EXPECTED_MANIFEST=None

def require(v,s):
    if not v:raise ValueError(s)
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def record(path,obj):
    with path.open("x") as f:f.write(json.dumps(obj,indent=2,allow_nan=False)+"\n")
def cmd(argv,*,timeout=60):
    p=subprocess.run(argv,capture_output=True,text=True,timeout=timeout)
    return {"command":argv,"exit_code":p.returncode,"stdout":p.stdout,"stderr":p.stderr}
def manifest():
    require(EXPECTED_MANIFEST and digest(BASE/"SOURCE_MANIFEST_V3.json")==EXPECTED_MANIFEST,"explicit manifest identity")
    m=json.loads((BASE/"SOURCE_MANIFEST_V3.json").read_text())
    require(m["schema"]=="kvbp.native-recurrent-copy-trace-manifest/v3" and m["image_id"]==IMAGE,"actual source contract")
    before={}
    for rel,expected in m["files"].items():
        path=ROOT/rel
        require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(ROOT),"bounded ordinary source")
        require(digest(path)==expected,"source changed "+rel);before[str(path)]=expected
    prefix="projects/kvbuffer-parallel-ascend/operator/native_copy_trace_v2/"
    m["operator_sources"]={p[len(prefix):]:s for p,s in m["files"].items() if p.startswith(prefix) and
                            p.endswith((".h",".cpp",".asc","CMakeLists.txt"))}
    require(len(m["operator_sources"])==8,"exact eight compiler inputs")
    sdk=Path("/usr/local/Ascend/cann-9.1.0/aarch64-linux/include/tiling/platform/platform_ascendc.h")
    if os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD")=="0":
        require(digest(sdk)==m["platform_header_sha256"],"actual pinned SDK header")
    before[str(BASE/"SOURCE_MANIFEST_V3.json")]=EXPECTED_MANIFEST
    return m,before

def inside():
    require(os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD")=="0","no backend autoload")
    require(os.environ.get("PYTHONDONTWRITEBYTECODE")=="1","no bytecode")
    require(not list(Path("/dev").glob("davinci[0-9]*")),"compile cannot map compute devices")
    m,before=manifest()
    require(OUT.is_dir() and not (OUT/"build").exists(),"new build subdir")
    start=datetime.now(timezone.utc).isoformat(); commands=[]
    archive=OUT/"source-archive.tar.gz"
    with archive.open("xb") as f:
        with tarfile.open(fileobj=f,mode="w:gz") as tar:
            for rel,expected in sorted(m["files"].items()):
                payload=(ROOT/rel).read_bytes()
                require(hashlib.sha256(payload).hexdigest()==expected,"archive source changed "+rel)
                entry=tarfile.TarInfo(rel);entry.size=len(payload);entry.mode=0o644
                tar.addfile(entry,io.BytesIO(payload))
            payload=(BASE/"SOURCE_MANIFEST_V3.json").read_bytes()
            require(hashlib.sha256(payload).hexdigest()==EXPECTED_MANIFEST,"archive manifest changed")
            entry=tarfile.TarInfo(str((BASE/"SOURCE_MANIFEST_V3.json").relative_to(ROOT)))
            entry.size=len(payload);entry.mode=0o644;tar.addfile(entry,io.BytesIO(payload))
    a=["cmake","-S",str(PROJECT/"operator/native_copy_trace_v2"),"-B",str(OUT/"build"),
       "-DCMAKE_BUILD_TYPE=Release","-DPython3_EXECUTABLE=/usr/local/python3.12.13/bin/python3"]
    for i,a in enumerate((a,["cmake","--build",str(OUT/"build"),"--parallel","1"])):
        r=cmd(a,timeout=600);record(OUT/("command-%d.json"%i),r);commands.append(r)
        require(r["exit_code"]==0,"compile/link command failed, original retained")
    lib=OUT/"build/libqwen36_native_recurrent_copy_trace_v2_ops.so"
    require(lib.is_file() and not lib.is_symlink(),"ordinary actual library")
    export=cmd(["nm","-D","--defined-only",str(lib)]);record(OUT/"exports.json",export)
    require(export["exit_code"]==0,"nm failed")
    symbol="qwen36_native_recurrent_copy_trace_v2_kernel"
    matches=[line.split() for line in export["stdout"].splitlines() if line.split()[-1:]==[symbol]]
    require(len(matches)==1 and matches[0][-2] in ("T","W"),"ASC kernel not defined")
    _,after=manifest();require(before==after,"source changed during build")
    receipt={"schema":"kvbp.native-recurrent-copy-trace-build/v3","status":"compiled_no_device",
             "npu_executed":False,"image_id":IMAGE,"namespace":"qwen36_native_recurrent_copy_trace_v2",
             "sources":m["operator_sources"],"npu_arch":"dav-2201",
             "library_sha256":digest(lib),"commands":commands,
             "exported_kernel":{"name":symbol,"defined":True,"type":matches[0][-2]},
             "sources_before":before,"sources_after":after,
             "source_archive":{"path":str(archive),"sha256":digest(archive)},
             "started_utc":start,"completed_utc":datetime.now(timezone.utc).isoformat()}
    record(OUT/"build-receipt.json",receipt)
    meta=cmd(["/usr/local/python3.12.13/bin/python3","-B",str(BASE/"meta_probe.py"),"--library",str(lib),"--library-sha256",digest(lib),"--output",str(OUT/"meta-receipt.json")],timeout=180)
    record(OUT/"original-meta-child.json",meta);require(meta["exit_code"]==0,"actual load/schema/Meta failed, retained")
    print(json.dumps({"build_receipt":str(OUT/"build-receipt.json"),
                     "build_sha256":digest(OUT/"build-receipt.json"),
                     "library":str(lib),"library_sha256":digest(lib),"meta_receipt":str(OUT/"meta-receipt.json"),"meta_sha256":digest(OUT/"meta-receipt.json"),"npu_executed":False}),flush=True)

def host(script_sha):
    require(digest(__file__)==script_sha,"MAIN exact builder source")
    require(ROOT.resolve()==ROOT and OUT.parent.is_dir() and not OUT.parent.is_symlink(),
            "canonical paths")
    require(not OUT.exists() and not OUT.is_symlink(),"fresh unique output")
    require(datetime.now(timezone.utc).timestamp()+1410 < datetime.fromisoformat("2026-10-08T08:29:54+00:00").timestamp(),"fixed KV cutoff includes cleanup")
    m,before=manifest()
    sys.path.insert(0,str(BASE));import audit_sources_v3
    source_audit=audit_sources_v3.audit()
    info=cmd(["/usr/bin/docker","info","--format","{{json .}}"])
    require(info["exit_code"]==0,"Docker engine unavailable");engine=json.loads(info["stdout"])
    require(engine["NCPU"]>=5,"summed CPU capacity")
    mi={l.split(":")[0]:int(l.split()[1])*1024 for l in Path("/proc/meminfo").read_text().splitlines()
        if l.startswith(("MemAvailable:","MemTotal:","Hugetlb:"))}
    require(mi["MemAvailable"]>=MEM+2*1024**3+8*1024**3,"8GiB build + summed2GiB preparers + unchanged8GiB reserve")
    require(shutil.disk_usage(OUT.parent).free>=13*1024**3,"5GiB build budget + 8GiB reserve")
    require(len(Path("/proc/1/mountinfo").read_text().splitlines())<95000,"mount reserve")
    old=cmd(["/usr/bin/docker","ps","-a","--filter","name=^/"+NAME+"$","--format","{{.ID}}"])
    require(old["exit_code"]==0 and not old["stdout"].strip(),"no duplicate container")
    OUT.mkdir()
    record(OUT/"host-preflight.json",{"source_audit":source_audit,"memory":mi,"engine_cpus":engine["NCPU"],
                                    "npu_executed":False,"sources":m["operator_sources"],
                                    "sources_complete":before,"fresh_utc":datetime.now(timezone.utc).isoformat()})
    argv=["/usr/bin/docker","create","--name",NAME,"--label","model-tuning-lab.owner="+OWNER,
          "--label","model-tuning-lab.producer-sha256="+script_sha,
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
                v["HostConfig"]["Memory"]==v["HostConfig"]["MemorySwap"]==MEM and
                not v["HostConfig"].get("DeviceRequests") and not v["HostConfig"].get("DeviceCgroupRules") and
                v["HostConfig"]["NanoCpus"]==10**9 and v["HostConfig"]["NetworkMode"]=="none" and
                v["HostConfig"]["PidsLimit"]==512 and v["HostConfig"].get("CapDrop")==["ALL"] and
                v["HostConfig"].get("SecurityOpt")==["no-new-privileges"] and
                len(v["Mounts"])==3 and all(x["Type"]=="bind" for x in v["Mounts"]) and
                {x["Destination"]:(x["Source"],x["RW"]) for x in v["Mounts"]}=={
                    str(ROOT):(str(ROOT),False),str(OUT):(str(OUT),True),
                    "/usr/local/Ascend/driver":("/usr/local/Ascend/driver",False)}, "exact no-device ownership")
        s=cmd(["/usr/bin/docker","start",cid]);record(OUT/"start.json",s)
        require(s["exit_code"]==0,"start failed")
        a=["/usr/bin/docker","exec",cid,"/bin/bash","-c",
           'source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"',
           "native-copy-build","/usr/local/python3.12.13/bin/python3","-B",str(Path(__file__).resolve()),"--inside","--script-sha256",script_sha,"--manifest-sha256",EXPECTED_MANIFEST]
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
            require(v["exit_code"]==0,"release inspect")
            state=json.loads(v["stdout"])[0]
            require(state["State"]["Pid"]==0 and not state["State"]["Running"] and
                    not state["State"]["OOMKilled"] and not state.get("ExecIDs"),"actual owned process release")
        except BaseException as e:
            print(json.dumps({"secondary_cleanup_error":repr(e),"original_error":repr(primary)}),flush=True)
            if primary is None:raise

def main():
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group()
    g.add_argument("--execute",action="store_true");g.add_argument("--inside",action="store_true")
    p.add_argument("--script-sha256");p.add_argument("--manifest-sha256");a=p.parse_args()
    global EXPECTED_MANIFEST
    EXPECTED_MANIFEST=a.manifest_sha256
    if a.inside or a.execute:require(a.manifest_sha256 and a.script_sha256 and digest(__file__)==a.script_sha256,"explicit expected builder SHA")
    if a.inside:inside()
    elif a.execute:host(a.script_sha256)
    else:print(json.dumps({"default_enabled":False,"npu_executed":False,"out":str(OUT)}))
if __name__=="__main__":main()

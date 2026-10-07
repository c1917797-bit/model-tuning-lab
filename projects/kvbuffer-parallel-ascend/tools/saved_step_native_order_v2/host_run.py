#!/usr/bin/env python3
"""MAIN-only single-card saved-step diagnostic admission. Default OFF, never serving."""
import argparse,hashlib,json,os,re,shutil,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab")
PROJECT=ROOT/"projects/kvbuffer-parallel-ascend"
BASE=PROJECT/"tools/split_gate_v2"
REPLAY=PROJECT/"tools/saved_step_native_order_v2/replay.py"
MANIFEST_SHA="508ff442ede945b8fb5930f79ee597ec1dba07e5d4e778d9abc85aafda6ce9c9"
REPLAY_SHA="bf83bb028ef309c826abd1a28dd4b32cbff6fcc390b71f2432c47986064b7e00"
BUILD=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006/build-native-order-v2-20261007-0924")
REFS={
 "library":{"path":str(BUILD/"build/libqwen36_gdn_kvbuffer_native_order_v2_ops.so"),"sha256":"77b4d61f94b4a8747bd08d2223b11d87702b43186acfd2f1b2e220f7b64a065c"},
 "build":{"path":str(BUILD/"build-receipt.json"),"sha256":"ff4c4a22ccf3e03d57baf08d59d6494e0f1435c74fbd132bbba1e98850e30dd8"},
 "meta":{"path":str(BUILD/"meta-report-format-v2.json"),"sha256":"fb765a5389ad97464597f16a43915440a46b654b3419d86a9894692d487592ee"}}
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
OLD_BUILD=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006/build-p1-v1")
OLD_GATE=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006/split-dispatch-native-20261007-0830/b1/results/gate")
OUT=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006/saved-step-native-order-v2-20261007-0944")
NAME="kvbuffer_native_order_v2_savedstep_20261007_0944"
OWNER="kvbuffer-native-order-v2-savedstep"
MEM=8*1024**3
NATIVE="/vllm-workspace/vllm-ascend/vllm_ascend/vllm_ascend_C.cpython-312-aarch64-linux-gnu.so"
NATIVE_SHA="eaa9457a21a45e2cb027c1345ee670b59d10fcd6f4a8be8b0b1bf2fde1d2232a"
DOCKER="/usr/bin/docker"
SMI="/usr/local/sbin/npu-smi"

def require(v,text):
    if not v:raise ValueError(text)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,obj):
    with Path(p).open("x") as f:
        f.write(json.dumps(obj,indent=2,allow_nan=False)+"\n");f.flush();os.fsync(f.fileno())
    return {"path":str(p),"sha256":sha(p)}
def contract():
    sys.path.insert(0,str(BASE));import contract as c
    return c
def source():
    c=contract();ref={"path":str(BASE/"SOURCE_MANIFEST.json"),"sha256":MANIFEST_SHA}
    m,s=c.source_admission(ref);c.artifacts(REFS,m)
    require(sha(REPLAY)==REPLAY_SHA,"saved-step source changed")
    return c,ref,m,s
def run(argv,timeout=30):
    p=subprocess.run(argv,capture_output=True,text=True,timeout=timeout)
    return {"argv":argv,"exit_code":p.returncode,"stdout":p.stdout,"stderr":p.stderr,
            "observed_utc":datetime.now(timezone.utc).isoformat()}
def command_file(name,argv,timeout=30):
    v=run(argv,timeout);ref=write(OUT/(name+".json"),v)
    require(v["exit_code"]==0,"command failed, original retained: "+name)
    return v,ref
def process_rows(text):
    result=[]
    for line in text.splitlines():
        cols=line.split("|")
        if len(cols)<5:continue
        first=cols[1].split();second=cols[2].strip()
        if len(first)==2 and all(x.isdigit() for x in first) and second.isdigit():
            result.append((int(first[0]),int(first[1]),int(second)))
    return result
def idle(text):
    rows=process_rows(text)
    for physical in (4,5,6,7):
        require("No running processes found in NPU "+str(physical) in text,
                "authorized lane compute not idle or observation incomplete")
        require(not any(n==physical for n,_,_ in rows),"actual authorized compute PID")
        lines=text.splitlines()
        ix=next((i for i,l in enumerate(lines)
                 if re.match(r"\|\s*"+str(physical)+r"\s+910B4\s*\|",l)),None)
        require(ix is not None and "| OK " in lines[ix],"fresh physical health")
        parts=lines[ix+1].split("|");vals=parts[3].split()
        require(vals and vals[0]=="0" and re.search(r"\b28[0-9][0-9]\s*/\s*32768\b",parts[3]),
                "AICore/HBM idle baseline")
def inspected(cid):
    v,ref=command_file("inspect-"+str(time.time_ns()),[DOCKER,"inspect",cid])
    x=json.loads(v["stdout"])[0];h=x["HostConfig"]
    expected={"/dev/davinci5":"/dev/davinci0","/dev/davinci_manager":"/dev/davinci_manager",
              "/dev/devmm_svm":"/dev/devmm_svm","/dev/hisi_hdc":"/dev/hisi_hdc"}
    require(x["Id"]==cid and x["Name"]=="/"+NAME and x["Image"]==IMAGE and
            x["Config"]["Labels"].get("model-tuning-lab.owner")==OWNER and
            not h["Privileged"] and h["Memory"]==MEM and h["MemorySwap"]==MEM and
            h["NanoCpus"]==10**9 and h["NetworkMode"]=="none" and not h.get("DeviceRequests") and
            not h.get("DeviceCgroupRules") and len(h["Devices"])==4 and
            {d["PathOnHost"]:d["PathInContainer"] for d in h["Devices"]}==expected,
            "exact owned nonprivileged physical5->logical0")
    mounts={v["Destination"]:(v["Source"],v["RW"]) for v in x["Mounts"]}
    for p in (ROOT,BUILD,OLD_BUILD,OLD_GATE,Path("/usr/local/Ascend/driver")):
        require(mounts.get(str(p))==(str(p),False),"actual exact readonly mount")
    require(mounts.get(str(OUT))==(str(OUT),False) and
            mounts.get("/kvbuffer-results")==(str(OUT),True),"actual proof alias/results mounts")
    return x,ref
def inside_canary():
    c,ref,m,s=source()
    require(os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0" and
            os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD")=="0","canary env")
    native=c.legacy().NATIVE_PINS
    require({p:sha(p) for p in native}==native,"actual image native sources")
    import torch,torch_npu
    from vllm_ascend.utils import enable_custom_op
    from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton
    torch_npu.npu.set_compile_mode(jit_compile=False);torch.npu.set_device(0)
    require(torch.npu.device_count()==1 and torch.npu.get_device_name(0)=="Ascend910B4",
            "actual one logical0 910B4")
    require(enable_custom_op(),"actual native op bootstrap");init_device_properties_triton()
    x=torch.arange(16,dtype=torch.float32,device="npu:0");y=x*2;torch.npu.synchronize()
    require(torch.equal(y.cpu(),torch.arange(16,dtype=torch.float32)*2),"actual NPU tiny arithmetic")
    paths={line.split()[-1] for line in Path("/proc/self/maps").read_text().splitlines()
           if len(line.split())>=6}
    require(NATIVE in paths and sha(NATIVE)==NATIVE_SHA,"actual native mapped SO")
    _,_,_,after=source();require(s==after,"source closure changed")
    write(Path("/kvbuffer-results/canary.json"),
          {"status":"pass","pid":os.getpid(),"device_count":1,"logical":0,"soc":"Ascend910B4",
           "source_manifest":ref,"sources":s,"native_sources":native,
           "native_mapped":{NATIVE:NATIVE_SHA},"host_launcher_sha256":sha(__file__),
           "tiny_arithmetic":True,"numerical_candidate_verified":False})
    # Bounded context hold solely to prove host physical/PID attribution; never timed as performance.
    time.sleep(12)
def exec_argv(cid,python_args):
    return [DOCKER,"exec",cid,"/bin/bash","-c",
            'source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"',"kvbp-diagnostic",
            "/usr/local/python3.12.13/bin/python3","-B",*python_args]
def observed_child(cid,label,argv,target,limit):
    start=time.monotonic();proofs=[];p=None
    stdout=OUT/(label+".stdout");stderr=OUT/(label+".stderr")
    with stdout.open("x") as so,stderr.open("x") as se:
        p=subprocess.Popen(argv,stdout=so,stderr=se,cwd=ROOT)
        try:
            while p.poll() is None:
                require(time.monotonic()-start<limit,"bounded child timeout; no automatic retry")
                v=run([SMI,"info"]);write(OUT/(label+"-smi-"+str(time.time_ns())+".json"),v)
                require(v["exit_code"]==0,"live NPU observation failed")
                top=run([DOCKER,"top",cid,"-eo","pid,ppid,args"])
                require(top["exit_code"]==0,"live Docker process observation failed")
                top_ref=write(OUT/(label+"-top-"+str(time.time_ns())+".json"),top)
                for physical,chip,pid in process_rows(v["stdout"]):
                    if physical!=5:continue
                    require(chip==0,"observed unexpected chip")
                    cp=Path("/proc")/str(pid)/"cgroup"
                    if cp.is_file() and cid in cp.read_text() and any(
                            line.split() and line.split()[0]==str(pid) and target in line
                            for line in top["stdout"].splitlines()):
                        proofs.append({"physical":physical,"pid":pid,"cgroup":cp.read_text(),"top":top_ref,
                                       "observed_utc":v["observed_utc"]})
                # Only protected/outside ownership observations, never any external mutation.
                require(not any(physical in (4,6,7) for physical,_,_ in process_rows(v["stdout"])),
                        "another paper acquired authorized lane")
                time.sleep(1)
            result={"argv":argv,"exit_code":p.returncode,"stdout_ref":{"path":str(stdout),"sha256":sha(stdout)},
                    "stderr_ref":{"path":str(stderr),"sha256":sha(stderr)},
                    "physical_pid_proofs":proofs,"duration_seconds":time.monotonic()-start}
            evidence=write(OUT/(label+"-child.json"),result)
            require(p.returncode==0,"real child failed; raw stdout/stderr retained")
            require(proofs,"missing actual workload physical5/PID proof")
            return evidence
        finally:
            if p.poll() is None:
                inspected(cid);run([DOCKER,"stop","--time","15",cid],30)
                p.wait(timeout=30)
def host():
    c,ref,m,s=source()
    require(ROOT.resolve()==ROOT and OUT.parent.is_dir() and not OUT.exists() and not OUT.is_symlink(),
            "fresh exact output")
    require(datetime.now(timezone.utc)<datetime.fromisoformat("2026-10-08T08:29:54+00:00"),
            "fixed KVBuffer cutoff")
    memory={l.split(":")[0]:int(l.split()[1])*1024 for l in Path("/proc/meminfo").read_text().splitlines()
            if l.startswith(("MemTotal:","MemAvailable:","Hugetlb:"))}
    require(memory["MemAvailable"]>=MEM+8*1024**3,"8GiB cap plus unchanged8GiB reserve")
    require(shutil.disk_usage(OUT.parent).free>=13*1024**3,"5GiB workspace plus8GiB reserve")
    require(len(Path("/proc/1/mountinfo").read_text().splitlines())<95000,"mount reserve")
    engine=run([DOCKER,"info","--format","{{json .}}"])
    require(engine["exit_code"]==0 and json.loads(engine["stdout"])["NCPU"]>=3,"joint1CPU+2CPU reserve")
    smi=run([SMI,"info"]);require(smi["exit_code"]==0,"fresh smi");idle(smi["stdout"])
    old=run([DOCKER,"ps","-a","--filter","name=^/"+NAME+"$","--format","{{.ID}}"])
    require(old["exit_code"]==0 and not old["stdout"].strip(),"unique container, no duplicate launch")
    OUT.mkdir()
    resources=write(OUT/"resources.json",{"memory":memory,"engine":engine,"smi":smi,
                "source_manifest":ref,"sources":s,"host_launcher_sha256":sha(__file__),
                "ordinary_memory_budget":MEM,"reserve":8*1024**3,"model_admitted":False,
                "preflight_utc":datetime.now(timezone.utc).isoformat()})
    argv=[DOCKER,"create","--name",NAME,"--label","model-tuning-lab.owner="+OWNER,
          "--network","none","--cap-drop","ALL","--security-opt","no-new-privileges",
          "--memory",str(MEM),"--memory-swap",str(MEM),"--cpus","1","--pids-limit","512",
          "--env","ASCEND_RT_VISIBLE_DEVICES=0","--env","TORCH_DEVICE_BACKEND_AUTOLOAD=0",
          "--env","PYTHONDONTWRITEBYTECODE=1","--env","OMP_NUM_THREADS=1"]
    for h,d in (("/dev/davinci5","/dev/davinci0"),("/dev/davinci_manager","/dev/davinci_manager"),
                ("/dev/devmm_svm","/dev/devmm_svm"),("/dev/hisi_hdc","/dev/hisi_hdc")):
        require(Path(h).exists(),"real host device node");argv+=["--device",h+":"+d]
    for p in (ROOT,BUILD,OLD_BUILD,OLD_GATE,OUT,Path("/usr/local/Ascend/driver")):
        require(p.is_dir(),"actual mount source");argv+=["--mount","type=bind,src="+str(p)+",dst="+str(p)+",readonly"]
    argv+=["--mount","type=bind,src="+str(OUT)+",dst=/kvbuffer-results",
           "--workdir",str(ROOT),"--entrypoint","/bin/bash",IMAGE,"-c","exec sleep infinity"]
    created,_=command_file("create",argv);cid=created["stdout"].strip()
    require(re.fullmatch("[0-9a-f]{64}",cid),"exact Docker ID")
    primary=None
    try:
        x,inspect_ref=inspected(cid);require(not x["State"]["Running"] and x["State"]["Pid"]==0,"new stopped")
        command_file("start",[DOCKER,"start",cid])
        canary_child=observed_child(cid,"canary",exec_argv(cid,[str(Path(__file__).resolve()),"--inside-canary"]),
                                    str(Path(__file__).resolve()),120)
        proof=json.loads((OUT/"canary.json").read_text())
        require(proof["status"]=="pass" and proof["sources"]==s and
                proof["host_launcher_sha256"]==sha(__file__),"actual canary original")
        x,inspect_ref=inspected(cid);require(x["State"]["Running"] and not x["State"]["OOMKilled"],"owned live")
        identity={"schema":"kvbp.split-launch-identity/v2","image_id":IMAGE,
           "protocol":c.protocol(1,5),"physical_devices":[5],"logical_to_physical":{"0":5},
           "fresh_idle_verified":True,"nonprivileged":True,"source_canary_passed":True,
           "memory_cgroup_bytes":MEM,"source_manifest":ref,"sources":s,"artifact_refs":REFS,
           "preflight_utc":datetime.now(timezone.utc).isoformat(),
           "diagnostic_script":{"path":str(REPLAY),"sha256":REPLAY_SHA},
           "host_launcher_sha256":sha(__file__),
           "evidence":{"resources":resources,"inspect":inspect_ref,"canary_child":canary_child,
                       "canary":{"path":str(OUT/"canary.json"),"sha256":sha(OUT/"canary.json")}}}
        write(OUT/"identity.json",identity);c.validate_identity(identity,1,5,ref,m,s,REFS)
        args=[str(REPLAY),"--execute","--script-sha256",REPLAY_SHA,"--source-manifest",ref["path"],
              "--source-manifest-sha256",MANIFEST_SHA]
        for k,label in (("library","library"),("build","build-receipt"),("meta","meta-receipt")):
            args+=["--"+label,REFS[k]["path"],"--"+label+"-sha256",REFS[k]["sha256"]]
        args+=["--identity",str(OUT/"identity.json"),"--output-dir","/kvbuffer-results/diagnostic"]
        original=observed_child(cid,"diagnostic",exec_argv(cid,args),str(REPLAY),600)
        result=json.loads((OUT/"diagnostic/report.json").read_text())
        require(result["status"]=="new_single_step_numerical_pass" and
                result["matrix_verified"] is False and result["serving_ready"] is False,"scoped real result")
        write(OUT/"RESULT.json",{"status":result["status"],"original_child":original,
              "report":{"path":str(OUT/"diagnostic/report.json"),"sha256":sha(OUT/"diagnostic/report.json")},
              "matrix_verified":False,"e2e_verified":False,"task_accuracy_verified":False})
        print(json.dumps({"status":result["status"],"output":str(OUT),"container":cid}),flush=True)
    except BaseException as e:
        primary=e
        write(OUT/"host-error.json",{"error":repr(e),"output":str(OUT),"container":cid})
        print(json.dumps({"original_error":repr(e),"output":str(OUT),"container":cid}),flush=True)
        raise
    finally:
        try:
            x,_=inspected(cid)
            command_file("stop",[DOCKER,"stop","--time","15",cid],40)
            x,release=inspected(cid)
            require(not x["State"]["Running"] and x["State"]["Pid"]==0 and
                    not x.get("ExecIDs") and not x["State"]["OOMKilled"],"owned process/lease release")
            write(OUT/"release.json",{"container":cid,"inspect":release,"retained":True,
                  "deleted":False,"pid":0,"no_exec":True,"no_oom":True})
        except BaseException as e:
            print(json.dumps({"primary":repr(primary),"secondary_cleanup":repr(e)}),flush=True)
            if primary is None:raise
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
    p.add_argument("--inside-canary",action="store_true");a=p.parse_args()
    if a.inside_canary:inside_canary()
    elif a.execute:host()
    else:print(json.dumps({"default_enabled":False,"npu_executed":False,"serving_ready":False,
                         "output":str(OUT),"scope":"one saved B1 fixture, original thresholds"}))
if __name__=="__main__":main()

#!/usr/bin/env python3
"""MAIN-only, CPU/no-device bounded schema producer; explicit opt-in."""
import argparse, importlib.util, json, os, resource, subprocess, sys, time
from pathlib import Path
ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab")
FI=ROOT/"projects/qwen36-paper-portfolio/tools/flashinfer_native_state_gate_v3"
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(FI))
import contract as c
import host as fhost
H=fhost.H
DOCKER="/usr/bin/docker";PRLIMIT="/usr/bin/prlimit";PY="/usr/local/python3.12.13/bin/python3"
OWNER="flashinfer-no-device-schema-v1";GIB=1024**3
ENV={"TORCH_DEVICE_BACKEND_AUTOLOAD":"0","ASCEND_RT_VISIBLE_DEVICES":"",
    "PYTHONDONTWRITEBYTECODE":"1","OMP_NUM_THREADS":"1","MKL_NUM_THREADS":"1","OPENBLAS_NUM_THREADS":"1"}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--execute",action="store_true")
    p.add_argument("--output-dir",type=Path)
    a=p.parse_args()
    if not a.execute:
        print(json.dumps({"default_enabled":False,"npu_executed":False}));return
    c.require(a.output_dir is not None,"new output explicit")
    source,files=c.source_identity(FI/"SOURCE_MANIFEST.json","cac64aad92d738c6319c3c0d8eaea6af1926d925fbf4ec3f7a427936d1803caa")
    own_before={name:c.sha(BASE/name) for name in ("producer.py","host_preflight.py")}
    host=H.cpu_view(os.getpid());daemon=H.daemon_view();cpu=H.cpu_admission(host,daemon)
    os.sched_setaffinity(0,{cpu["host_cpu"]})
    soft,hard=resource.getrlimit(resource.RLIMIT_AS)
    c.require(hard==resource.RLIM_INFINITY,"Docker-only AS restore needs unlimited hard limit")
    resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,hard))
    H.fresh_output(a.output_dir);out=a.output_dir
    start=time.monotonic();deadline=start+240;cid=None;primary=None;secondary=[]
    expected=None;seq=0;proof_before=None;proof_after=None;stopped=None;child=None
    def call(label,argv,limit=30,check=True):
        nonlocal seq
        c.require(time.monotonic()<deadline,"whole CPU stage240s including cleanup")
        requested=list(argv)
        wrapped=[PRLIMIT,"--as=unlimited","--",*requested] if requested[0]==DOCKER else requested
        result=H.frozen().run(wrapped,min(limit,max(.5,deadline-time.monotonic())))
        result["requested_argv"]=requested
        ref=c.write_new(out/("%03d-%s.json"%(seq,label)),result);seq+=1
        rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss+resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
        c.require(rss<=256*1024,"actual host plus Docker client RSS256MiB")
        if check:c.require(result["exit_code"]==0,"exact command failed: "+str(ref))
        return result,ref
    def memory():
        mem={l.split(":")[0]:int(l.split()[1])*1024 for l in Path("/proc/meminfo").read_text().splitlines()
            if l.startswith(("MemAvailable:","Hugetlb:","SwapTotal:","SwapFree:"))}
        c.require(mem["MemAvailable"]>=int(16.25*GIB) and mem["SwapTotal"]==mem["SwapFree"],"ordinary RAM8GiBguest+.25host+8reserve unchanged")
        disk=__import__("shutil").disk_usage(out.parent).free
        c.require(disk>=9*GIB,"CPU output1GiB plus unchanged8GiB disk reserve")
        return {"memory":mem,"disk_free_bytes":disk,"host":H.cpu_view(os.getpid()),"daemon":H.daemon_view(),"allocation":cpu}
    def inspect():
        raw,ref=call("inspect",[DOCKER,"inspect",cid])
        xs=json.loads(raw["stdout"]);c.require(len(xs)==1,"one exact owned inspect");x=xs[0];hc=x["HostConfig"];cfg=x["Config"]
        c.require(x["Id"]==cid and x["Image"]==c.IMAGE and x["Name"]=="/"+name and cfg["Labels"].get("model-tuning-lab.owner")==OWNER and
            cfg["Labels"].get("producer-sha256")==own_before["producer.py"] and cfg["Labels"].get("controller-sha256")==own_before["host_preflight.py"],
            "exact source-bound CID/image/owner")
        c.require(not hc["Privileged"] and not hc.get("Devices") and not hc.get("DeviceRequests") and not hc.get("DeviceCgroupRules") and
            hc["Memory"]==8*GIB and hc["MemorySwap"]==8*GIB and hc["NanoCpus"]==10**9 and hc["CpusetCpus"]==str(cpu["guest_cpu"]) and
            hc["NetworkMode"]=="none" and hc["IpcMode"]=="private" and hc["ShmSize"]==2*GIB and hc["PidsLimit"]==512 and
            set(hc.get("CapDrop") or [])=={"ALL"} and set(hc.get("SecurityOpt") or [])=={"no-new-privileges"},"actual CPU-only no-device limits")
        c.require(cfg["Entrypoint"]==["/bin/bash"] and cfg["Cmd"]==inner and cfg["WorkingDir"]==str(ROOT),"complete original producer argv")
        c.require({m["Destination"]:(m["Source"],m["RW"]) for m in x["Mounts"]}==mounts and len(x["Mounts"])==len(mounts),"exact read-only source/driver and owned output")
        c.require(all(cfg["Env"].count(k+"="+v)==1 for k,v in ENV.items()),"actual no-device environment")
        return x,ref
    name="fi-no-device-"+out.name
    c.require(__import__("re").fullmatch("[A-Za-z0-9_-]{1,100}",name),"bounded name")
    mounts={str(ROOT):(str(ROOT),False),"/usr/local/Ascend/driver":("/usr/local/Ascend/driver",False),"/abi-results":(str(out),True)}
    inner=["-c",'source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"',"fi-no-device",PY,"-B",str(BASE/"producer.py"),"--execute",
        "--source-manifest",str(FI/"SOURCE_MANIFEST.json"),"--source-manifest-sha256",source["sha256"],
        "--producer-sha256",own_before["producer.py"],"--output","/abi-results/report.json"]
    try:
        res=memory()
        smi,proof_before=call("smi-before",["/usr/local/sbin/npu-smi","info"])
        protected=H.frozen().protected(smi["stdout"])
        c.write_new(out/"PLAN.json",{"schema":"flashinfer.no-device-plan/v1","source_manifest":source,"sources":files,
            "own_sources":own_before,"npu_executed":False,"guest_memory_bytes":8*GIB,"host_memory_bytes":256*1024**2,
            "ordinary_reserve_bytes":8*GIB,"resources":res,"lease_seconds":240,"cleanup_reserve_seconds":90})
        unique,_=call("unique",[DOCKER,"ps","-a","--filter","name=^/"+name+"$","--format","{{.ID}}"])
        c.require(not unique["stdout"].strip(),"never reuse old CPU preflight")
        argv=[DOCKER,"create","--name",name,"--label","model-tuning-lab.owner="+OWNER,
            "--label","producer-sha256="+own_before["producer.py"],"--label","controller-sha256="+own_before["host_preflight.py"],
            "--network","none","--cap-drop","ALL","--security-opt","no-new-privileges",
            "--memory",str(8*GIB),"--memory-swap",str(8*GIB),"--cpus","1","--cpuset-cpus",str(cpu["guest_cpu"]),
            "--ipc","private","--shm-size",str(2*GIB),"--pids-limit","512","--workdir",str(ROOT),"--entrypoint","/bin/bash"]
        for k,v in ENV.items():argv+=["--env",k+"="+v]
        for dst,(src,rw) in mounts.items():argv+=["--mount","type=bind,source="+src+",destination="+dst+("" if rw else ",readonly")]
        created,create_ref=call("create",[*argv,c.IMAGE,*inner])
        cid=created["stdout"].strip();c.require(__import__("re").fullmatch("[a-f0-9]{64}",cid),"actual exact CID")
        c.write_new(out/"OWNED.json",{"cid":cid,"name":name,"image":c.IMAGE,"owner":OWNER,"create_receipt":create_ref})
        x,_=inspect();c.require(not x["State"]["Running"] and x["State"]["Pid"]==0,"new CPU CID not already live")
        call("start",[DOCKER,"start",cid])
        x,_=inspect()
        if x["State"]["Running"]:
            guest=H.cpu_view(x["State"]["Pid"])
            c.require(guest["effective_capacity"]==1 and guest["effective_cpus"]==[cpu["guest_cpu"]],"actual guest effective CPU")
            c.write_new(out/"guest-cpu.json",guest)
        while x["State"]["Running"]:
            c.require(time.monotonic()<deadline-90,"CPU child deadline retains90s cleanup")
            memory();time.sleep(.5);x,_=inspect()
        c.require(x["State"]["ExitCode"]==0 and not x["State"]["OOMKilled"],"actual CPU schema producer exit")
        report=json.loads((out/"report.json").read_bytes())
        c.require(report["passed"] and report["source_manifest"]==source and report["sources_before"]==report["sources_after"]==files and
            report["producer_sha256"]==own_before["producer.py"] and report["npu_executed"] is False and
            report["device_inventory_before"]==report["device_inventory_after"]==[] and not report["schema_failures"],"actual complete no-device schema receipt")
        child=c.bound(out/"report.json",c.sha(out/"report.json"))
    except BaseException as error:primary=error
    finally:
        if cid:
            try:
                x,_=inspect();call("stop-retain",[DOCKER,"stop","--time","15",cid],40)
                x,stopped=inspect()
                c.require(not x["State"]["Running"] and x["State"]["Pid"]==0 and not x.get("ExecIDs") and not x["State"].get("OOMKilled"),"exact CPU CID stopped retained")
                call("logs",[DOCKER,"logs",cid],30,False)
            except BaseException as error:secondary.append(repr(error))
        try:
            smi,proof_after=call("smi-after",["/usr/local/sbin/npu-smi","info"])
            c.require(H.frozen().protected(smi["stdout"])==protected,"protected0–3 identity changed during CPU check")
            _,after=c.source_identity(FI/"SOURCE_MANIFEST.json",source["sha256"])
            c.require(after==files and own_before=={n:c.sha(BASE/n) for n in own_before},"source before/after unchanged")
        except BaseException as error:secondary.append(repr(error))
        result={"schema":"flashinfer.no-device-host-result/v1","passed":primary is None and not secondary,
            "source_manifest":source,"sources":files,"own_sources":own_before,"container_id":cid,
            "report":child,"stopped_retained_inspect":stopped,"smi_before":proof_before,"smi_after":proof_after,
            "primary_error":repr(primary) if primary else None,"secondary_errors":secondary,
            "npu_executed":False,"model_executed":False,"elapsed_seconds":time.monotonic()-start}
        rr=c.write_new(out/"RESULT.json",result)
        print("MAIN_FLASHINFER_NO_DEVICE_HOST_V1 "+json.dumps({"result":rr,"passed":result["passed"],"npu_executed":False}),flush=True)
    if primary:raise primary
    c.require(not secondary,"secondary owned retention/source failure")
if __name__=="__main__":main()

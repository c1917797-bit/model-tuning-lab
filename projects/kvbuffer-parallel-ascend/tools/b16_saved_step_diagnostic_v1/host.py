#!/usr/bin/env python3
"""MAIN-only B16 saved failure host. Default OFF; no retry; stop exact own only."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,os,re,shutil,subprocess,sys,time
from pathlib import Path
from datetime import datetime,timezone,timedelta
ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab")
HERE=ROOT/"projects/kvbuffer-parallel-ascend/tools/b16_saved_step_diagnostic_v1"
FULL=ROOT/"projects/kvbuffer-parallel-ascend/tools/full_matrix_host_v2/host.py"
FULL_SHA="ab0296c698df00c9c3b2ce377601f6d6723adde6efb4a9e65407beca51ba5f86"
REPLAY=HERE/"replay.py"
REPLAY_SHA="86cd69ee8c3de19ffeea91e753cc8056320e192c208741775d97bb0938530a00"
OUT=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006/b16-saved-step-diagnostic-v1-20261007")
NAME="kvbuffer_b16_saved_step_diagnostic_v1_20261007"
OWNER="kvbuffer-b16-saved-step-diagnostic-v1"
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
MEM=8*1024**3;RESERVE=8*1024**3;CAP=600;CLEANUP=90
CUTOFF=datetime.fromisoformat("2026-10-08T08:29:54+00:00")
DOCKER="/usr/bin/docker";SMI="/usr/local/sbin/npu-smi"
_FROZEN=None
def require(v,message):
    if not v:raise ValueError(message)
def sha(p):
    p=Path(p);require(p.is_file() and not p.is_symlink(),"ordinary exact evidence/source")
    return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    with Path(p).open("x") as f:
        f.write(json.dumps(v,indent=2,allow_nan=False)+"\n");f.flush();os.fsync(f.fileno())
    return {"path":str(p),"sha256":sha(p)}
def frozen():
    global _FROZEN
    require(sha(FULL)==FULL_SHA and sha(REPLAY)==REPLAY_SHA,"unchanged frozen producer/new replay")
    if _FROZEN is None:
        spec=importlib.util.spec_from_file_location("_kvbp_b16_frozen_full",FULL)
        _FROZEN=importlib.util.module_from_spec(spec);sys.modules[spec.name]=_FROZEN
        spec.loader.exec_module(_FROZEN)
    return _FROZEN
def sources():
    h=frozen();c,r,m,s=h.legacy().source()
    require(len(s)==64 and r==h.SOURCE_REF and h.legacy().REFS==h.REFS,"source64/actual artifacts")
    c.artifacts(h.REFS,m);return h,c,r,m,s
def run(argv,timeout=30):return frozen().run(argv,timeout)
def capture(label,argv,timeout=30):
    v=run(argv,timeout);ref=write(OUT/(label+"-"+str(time.time_ns())+".json"),v)
    require(v["exit_code"]==0,"original command failed, retained "+label);return v,ref
def mounts():
    h=frozen()
    original_raw=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006/full-native-order-v2-20261007-1010")
    native_header=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006/native-source-snapshot-20261007-1052")
    vals={str(p):(str(p),False) for p in (ROOT,h.BUILD,h.legacy().OLD_BUILD,h.legacy().OLD_GATE,
             original_raw,native_header,OUT,Path("/usr/local/Ascend/driver"))}
    vals["/kvbuffer-results"]=(str(OUT),True);return vals
def devices():
    return {"/dev/davinci6":"/dev/davinci0","/dev/davinci_manager":"/dev/davinci_manager",
            "/dev/devmm_svm":"/dev/devmm_svm","/dev/hisi_hdc":"/dev/hisi_hdc"}
def validate_inspect(x,cid,script_sha):
    h=x["HostConfig"];label=x["Config"]["Labels"]
    require(x["Id"]==cid and re.fullmatch("[0-9a-f]{64}",cid) and x["Name"]=="/"+NAME and x["Image"]==IMAGE and
       label.get("model-tuning-lab.owner")==OWNER and label.get("model-tuning-lab.run")==NAME and
       label.get("model-tuning-lab.producer-sha256")==script_sha and h["Privileged"] is False and
       h["Memory"]==h["MemorySwap"]==MEM and h["NanoCpus"]==10**9 and h["NetworkMode"]=="none" and
       h["PidsLimit"]==512 and set(h.get("CapDrop",[]))=={"ALL"} and
       set(h.get("SecurityOpt",[]))=={"no-new-privileges"} and not h.get("DeviceRequests") and
       not h.get("DeviceCgroupRules"),"exact nonprivileged owned identity/resources/security")
    ds=h["Devices"];require(len(ds)==4 and {v["PathOnHost"]:v["PathInContainer"] for v in ds}==devices()
       and all(v["CgroupPermissions"]=="rwm" for v in ds),"exact physical6 logical0")
    ms=x["Mounts"];require(len(ms)==len(mounts()) and all(v["Type"]=="bind" for v in ms) and
       {v["Destination"]:(v["Source"],v["RW"]) for v in ms}==mounts(),"exact readonly/full mounts")
    return x
def inspect(cid,script_sha,timeout=30):
    v,ref=capture("inspect",[DOCKER,"inspect",cid],timeout)
    # Raw Docker list is durable BEFORE identity predicates.
    raw=write(OUT/("inspect-raw-"+str(time.time_ns())+".json"),json.loads(v["stdout"]))
    x=json.loads(v["stdout"])[0];validate_inspect(x,cid,script_sha);return x,raw
def floor(memory,cpu,disk):
    require(memory>=MEM+RESERVE,"8GiB own plus unchanged8GiB ordinary reserve")
    require(cpu>=3,"1CPU plus2CPU reserve")
    require(disk>=5*1024**3+RESERVE,"5GiB workspace plus8GiB reserve")
    return {"ram_floor":MEM+RESERVE,"cpu_floor":3,"disk_floor":13*1024**3,
            "full_model_floor_unchanged":72*1024**3}
def resources():
    memory={l.split(":")[0]:int(l.split()[1])*1024 for l in Path("/proc/meminfo").read_text().splitlines()
            if l.startswith(("MemAvailable:","Hugetlb:"))}
    engine=run([DOCKER,"info","--format","{{json .}}"]);require(engine["exit_code"]==0,"actual engine")
    disk=shutil.disk_usage(OUT.parent).free;budget=floor(memory["MemAvailable"],json.loads(engine["stdout"])["NCPU"],disk)
    require(len(Path("/proc/1/mountinfo").read_text().splitlines())<95000,"mount reserve")
    return {"memory":memory,"engine":engine,"disk_free":disk,"budget":budget,
            "global_future_cap_guarantee":False}
def proc_raw(pid):
    row={"pid":pid,"files":{}}
    for name in ("stat","cgroup","cmdline","status"):
        try:
            b=(Path("/proc")/str(pid)/name).read_bytes()
            row["files"][name]={"raw_hex":b.hex(),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
        except BaseException as e:row["files"][name]={"read_error":repr(e)}
    return row
def validate_pid(physical,chip,pid,cid,target,top,expected):
    require(physical==6 and chip==0,"actual physical6/chip0")
    proof=frozen().gate_process(pid)
    require(cid in proof["cgroup"],"actual PID belongs to exact CID")
    line=next((l for l in top.splitlines() if l.split() and l.split()[0]==str(pid)),None)
    require(line is not None and target in line and proof["argv"]==expected,"actual exact target/argv")
    return proof
def observe_child(cid,label,argv,target,deadline,script_sha,protected):
    p=None;primary=None;secondary=[];proofs=[];ref=None
    stdout=OUT/(label+".stdout");stderr=OUT/(label+".stderr")
    expected=argv[argv.index("/usr/local/python3.12.13/bin/python3"):]
    with stdout.open("x") as so,stderr.open("x") as se:
        try:
            p=subprocess.Popen(argv,stdout=so,stderr=se,cwd=ROOT)
            while p.poll() is None:
                require(time.monotonic()<deadline-CLEANUP,"600s total cap includes cleanup, no retry")
                smi,sr=capture(label+"-smi",[SMI,"info"]);top,tr=capture(label+"-top",[DOCKER,"top",cid,"-eo","pid,ppid,args"])
                iv,ir=capture(label+"-inspect-before-predicate",[DOCKER,"inspect",cid])
                rows=frozen().legacy().process_rows(smi["stdout"])
                # Preserve complete telemetry BEFORE ownership/resource/protection predicates.
                snapshot={"smi":sr,"top":tr,"inspect":ir,
                    "processes":[proc_raw(pid) for n,ch,pid in rows if n in (4,5,6,7)],
                    "ownership_validated":False,"observed_ns":time.time_ns()}
                raw=write(OUT/(label+"-pid-before-predicate-"+str(time.time_ns())+".json"),snapshot)
                # A child exit may make the already-sampled SMI stale: do not predicate stale PIDs.
                if p.poll() is not None:break
                validate_inspect(json.loads(iv["stdout"])[0],cid,script_sha)
                require(frozen().protected(smi["stdout"])==protected,"protected0-3 PID/starttime change")
                for physical in (4,5,7):frozen().idle_one(smi["stdout"],physical)
                for n,ch,pid in rows:
                    if n==6:proofs.append({**validate_pid(n,ch,pid,cid,target,top["stdout"],expected),
                                          "raw_before_predicate":raw,"smi":sr,"top":tr,"inspect":ir})
                ma=next(int(l.split()[1])*1024 for l in Path("/proc/meminfo").read_text().splitlines()
                        if l.startswith("MemAvailable:"))
                write(OUT/("resource-tick-"+str(time.time_ns())+".json"),{"MemAvailable":ma,"reserve":RESERVE})
                require(ma>=RESERVE and shutil.disk_usage(OUT).free>=RESERVE,"runtime RAM/disk reserve")
                require(datetime.now(timezone.utc)<CUTOFF,"fixed cutoff")
                time.sleep(.5)
        except BaseException as e:primary=e
        finally:
            if p is not None and p.poll() is None:
                try:
                    inspect(cid,script_sha,min(30,max(1,deadline-time.monotonic())))
                    st=run([DOCKER,"stop","--time","15",cid],min(30,max(1,deadline-time.monotonic())))
                    secondary.append({"owned_stop":st});p.wait(timeout=min(30,max(1,deadline-time.monotonic())))
                except BaseException as e:
                    secondary.append({"cleanup_error":repr(e)})
                    if primary is None:primary=e
            value={"argv":argv,"exit_code":p.returncode if p else None,
                "child_started":p is not None,"child_termination_observed":p is not None and p.returncode is not None,
                "stdout":{"path":str(stdout),"sha256":sha(stdout)},"stderr":{"path":str(stderr),"sha256":sha(stderr)},
                "actual_pid_proofs":proofs,"primary_error":repr(primary) if primary else None,"secondary":secondary}
            try:ref=write(OUT/(label+"-child.json"),value)
            except BaseException as e:
                if primary is None:primary=e
                try:print(json.dumps({"primary":repr(primary),"secondary_save":repr(e)}),flush=True)
                except BaseException:pass
    if primary is not None:raise primary
    require(p.returncode==0,"original real child failure, bytes retained")
    require(proofs,"no actual workload PID proof; not canary substitution")
    return ref
def inside_canary():
    h,_,_,_,s=sources();h.legacy().inside_canary()
    proof=json.loads((Path("/kvbuffer-results")/"canary.json").read_bytes())
    require(proof["sources"]==s and proof["status"]=="pass","actual frozen source canary")
def execute(a):
    require(sha(__file__)==a.script_sha256,"MAIN expected host source")
    h,c,r,m,s=sources()
    require(OUT.parent.is_dir() and not OUT.exists() and not OUT.is_symlink(),"unique new output, never overwrite")
    require(datetime.now(timezone.utc)+timedelta(seconds=CAP)<=CUTOFF,"600s plus fixed cutoff, no timer reset")
    rs=resources();smi=run([SMI,"info"]);require(smi["exit_code"]==0,"fresh SMI");h.legacy().idle(smi["stdout"])
    prot=h.protected(smi["stdout"])
    exists=run([DOCKER,"ps","-a","--filter","name=^/"+NAME+"$","--format","{{.ID}}"])
    require(exists["exit_code"]==0 and not exists["stdout"].strip(),"unique name no retry")
    OUT.mkdir();deadline=time.monotonic()+CAP
    rr=write(OUT/"resources-original.json",{**rs,"smi":smi,"protected0_3":prot,"deadline_seconds":CAP,"cleanup":CLEANUP})
    argv=[DOCKER,"create","--name",NAME,"--label","model-tuning-lab.owner="+OWNER,
       "--label","model-tuning-lab.run="+NAME,"--label","model-tuning-lab.producer-sha256="+a.script_sha256,
       "--network","none","--cap-drop","ALL","--security-opt","no-new-privileges","--memory",str(MEM),
       "--memory-swap",str(MEM),"--cpus","1","--pids-limit","512","--env","ASCEND_RT_VISIBLE_DEVICES=0",
       "--env","TORCH_DEVICE_BACKEND_AUTOLOAD=0","--env","PYTHONDONTWRITEBYTECODE=1","--env","OMP_NUM_THREADS=1"]
    for src,dst in devices().items():
        require(Path(src).exists(),"actual device node");argv+=["--device",src+":"+dst]
    for dst,(src,rw) in mounts().items():
        require(Path(src).is_dir(),"actual mount root")
        argv+=["--mount","type=bind,src="+src+",dst="+dst+("" if rw else ",readonly")]
    argv+=["--workdir",str(ROOT),"--entrypoint","/bin/bash",IMAGE,"-c","exec sleep infinity"]
    created,_=capture("create",argv);cid=created["stdout"].strip();require(re.fullmatch("[0-9a-f]{64}",cid),"actual CID")
    primary=None
    try:
        inspect(cid,a.script_sha256);capture("start",[DOCKER,"start",cid])
        can=observe_child(cid,"canary",h.legacy().exec_argv(cid,[str(HERE/"host.py"),"--inside-canary"]),
                    str(HERE/"host.py"),deadline,a.script_sha256,prot)
        cp={"path":str(OUT/"canary.json"),"sha256":sha(OUT/"canary.json")}
        require(json.loads(Path(cp["path"]).read_bytes())["sources"]==s,"actual canary sources")
        _,ir=inspect(cid,a.script_sha256)
        identity={"schema":"kvbp.split-launch-identity/v2","image_id":IMAGE,"protocol":c.protocol(16,6),
           "physical_devices":[6],"logical_to_physical":{"0":6},"fresh_idle_verified":True,"nonprivileged":True,
           "source_canary_passed":True,"memory_cgroup_bytes":MEM,"source_manifest":r,"sources":s,"artifact_refs":h.REFS,
           "preflight_utc":datetime.now(timezone.utc).isoformat(),
           "diagnostic_script":{"path":str(REPLAY),"sha256":REPLAY_SHA},
           "evidence":{"resources":rr,"container_inspect":ir,"canary_child":can,"canary":cp}}
        identity_ref=write(OUT/"identity.json",identity);c.validate_identity(identity,16,6,r,m,s,h.REFS)
        args=[str(REPLAY),"--execute","--script-sha256",REPLAY_SHA,"--source-manifest",r["path"],
              "--source-manifest-sha256",r["sha256"],"--identity",identity_ref["path"],"--output-dir","/kvbuffer-results/diagnostic"]
        for k,label in (("library","library"),("build","build-receipt"),("meta","meta-receipt")):
            args+=["--"+label,h.REFS[k]["path"],"--"+label+"-sha256",h.REFS[k]["sha256"]]
        child=observe_child(cid,"diagnostic",h.legacy().exec_argv(cid,args),str(REPLAY),deadline,a.script_sha256,prot)
        write(OUT/"RESULT.json",{"status":"diagnostic-child-completed","child":child,"identity":identity_ref,
             "matrix_verified":False,"e2e_verified":False,"serving_ready":False})
    except BaseException as e:
        primary=e
        try:write(OUT/"host-error.json",{"primary":repr(e),"container":cid,"sources":s})
        except BaseException as secondary:
            try:print(json.dumps({"primary":repr(e),"secondary_save":repr(secondary)}),flush=True)
            except BaseException:pass
        raise
    finally:
        try:
            inspect(cid,a.script_sha256,min(30,max(1,deadline-time.monotonic())))
            capture("stop",[DOCKER,"stop","--time","15",cid],min(30,max(1,deadline-time.monotonic())))
            x,ir=inspect(cid,a.script_sha256,min(30,max(1,deadline-time.monotonic())))
            require(not x["State"]["Running"] and x["State"]["Pid"]==0 and not x.get("ExecIDs")
                    and not x["State"]["OOMKilled"],"own exact stopped/Pid0/noExec/noOOM")
            write(OUT/"STOP_RETAIN.json",{"container_id":cid,"inspect":ir,"stopped":True,"retained":True,"deleted":False})
            last,lr=capture("release-smi",[SMI,"info"])
            require(h.protected(last["stdout"])==prot,"protected0-3 unchanged")
            h.legacy().idle(last["stdout"])
            _,_,_,_,after=sources();require(after==s,"unchanged source64")
            write(OUT/"POST_RELEASE.json",{"smi":lr,"protected0_3":prot,"sources_before":s,"sources_after":after})
        except BaseException as e:
            try:print(json.dumps({"primary":repr(primary),"secondary_cleanup":repr(e)}),flush=True)
            except BaseException:pass
            if primary is None:raise
def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group();g.add_argument("--execute",action="store_true")
    g.add_argument("--inside-canary",action="store_true");g.add_argument("--source-audit-only",action="store_true")
    p.add_argument("--script-sha256");a=p.parse_args(argv)
    if a.inside_canary:inside_canary()
    elif a.source_audit_only:
        _,_,r,_,s=sources();print(json.dumps({"source_count":len(s),"source_manifest":r,"npu_executed":False}))
    elif a.execute:
        require(a.script_sha256 is not None,"explicit host SHA");execute(a)
    else:print(json.dumps({"default_enabled":False,"npu_executed":False,"output":str(OUT),"physical":6,
          "serving_ready":False,"scope":"one saved B16 failure; no matrix/performance/accuracy claim"}))
if __name__=="__main__":main()

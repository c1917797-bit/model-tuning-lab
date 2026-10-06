#!/usr/bin/env python3
"""MAIN-only one-shot all-T correctness dispatcher; default dry-plan, no performance."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime,timezone

sys.dont_write_bytecode=True
REPO=Path("/opt/host/vnf/austinov/model-tuning-lab")
PROJECT=REPO/"projects/damp-ascend"
ROOT=Path("/cache/cch/qwen36-damp-20261006")
BASE=Path(__file__).resolve().parent
PLAN=PROJECT/"tools/allT_dispatch_plan_v1"
PLAN_PINS={"plan.py":"b2facaebbdef3fcc8636af4fc0b2b8a230947e9d31e734f4769f3b75b7410179",
 "test_plan_contract.py":"92489e9331cc5d69a34344caccece1633f21c17893a0c516d1e9eb8bef651983",
 "READY.md":"33de6895aca9c6c7cb429ff211d49a17ee7af1efd3a83ce5707e90a97d621403"}
ORIGINAL=PROJECT/"tools/run_full_capture.py"
ORIGINAL_SHA="9ad5e359766578a24f06e127a990ab93d1e86555baa15d1abb7bb2b3ffc51122"
SMOKE=PROJECT/"tools/run_collector_smoke.py"
SMOKE_SHA="da541917ebd8764a81624a215a157b6d4e18fbaaa53d9310be54a104d2fbbf92"
POST=PROJECT/"tools/post_reference_plan_v1"
POST_SHA="643f0ce23c7e6a45471f2e8d37439634ab74e27a92c90ed47ea9767312ce4e78"
POST_RUN_SHA="a5196a4283a5d88e5d2418dcc7e64bc652131507d574484b2781a595739c6771"
PARENT_AUDIT=ROOT/"full-reference-resume-v1-launch"
PARENT_OPERATION="exec-0000000000000455"
PARENT_NAME="qwen36_damp_full_reference_resume_20261006_v1"
PARENT_ID="b6e2a1510fb809d0913ee214d28cf0df238930eadd1e39189eba54b0d2f9e1f1"
PARENT_PEER="lgw_a6109c51076a4a2c9d2674ca5a8704a0"
DEADLINE="2026-10-07T08:48:03Z"
GIB=1024**3
GATE_TIMEOUT=3600
COMMAND_TIMEOUT=90
CANARY_TIMEOUT=90
RUNTIME_RESERVE=8*GIB
MOUNT_PLAN_RESERVE=2560  # Conservative policy, not measured kernel mount upper bound.
MOUNT_RUNTIME_RESERVE=512
OWN_NAMES=("controller.py","test_controller.py","READY.md")

def require(ok,reason):
    if not ok:raise RuntimeError(reason)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def checked(path,digest):
    p=Path(path)
    require(p.is_absolute() and p.is_file() and not p.is_symlink(),"missing/nonordinary absolute artifact")
    require(isinstance(digest,str) and re.fullmatch("[a-f0-9]{64}",digest),"lowercase SHA256")
    require(sha(p)==digest,"source/artifact drift: "+str(p))
    return p

def reject_nonfinite_json(value):
    raise ValueError("nonfinite JSON token: "+str(value))

def read_json(path,maximum=16*1024*1024):
    p=Path(path)
    require(p.is_file() and not p.is_symlink() and p.stat().st_size<=maximum,"bounded ordinary JSON")
    return json.loads(p.read_text(),parse_constant=reject_nonfinite_json)

def write_new(path,value):
    with Path(path).open("x",encoding="utf-8") as f:
        json.dump(value,f,indent=2,sort_keys=True,allow_nan=False);f.write("\n")

def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def source_preparation():
    for n,h in PLAN_PINS.items():checked(PLAN/n,h)
    checked(ORIGINAL,ORIGINAL_SHA);checked(SMOKE,SMOKE_SHA)
    checked(POST/"post_reference_contract.py",POST_SHA)
    checked(POST/"run.py",POST_RUN_SHA)
    planner=load_module("damp_allT_controller_frozen_plan",PLAN/"plan.py")
    original=load_module("damp_allT_controller_frozen_full",ORIGINAL)
    parent=load_module("damp_allT_controller_frozen_post",POST/"post_reference_contract.py")
    source=planner.source_admission()
    native,missing=planner.native_identity()
    require(not missing,"actual native identity unavailable: "+repr(missing))
    parent.frozen_modules();parent.manifest_identity()
    safety=original.helper()  # Imports only; no Docker/NPU call until execute.
    require("torch" not in sys.modules and "torch_npu" not in sys.modules,"source preparation must stay stdlib")
    return planner,original,parent,safety,{"source":source,"native":native,"plan_pins":PLAN_PINS,
        "host_source_pins":{str(ORIGINAL):ORIGINAL_SHA,str(SMOKE):SMOKE_SHA,
                            str(POST/"post_reference_contract.py"):POST_SHA,
                            str(POST/"run.py"):POST_RUN_SHA}}

def packet_identity(path,digest):
    checked(path,digest)
    require(Path(path).resolve()==BASE/"PACKET.json","this NEW packet only")
    packet=read_json(path)
    require(packet.get("schema")=="damp-allT-controller-source/v1" and
            set(packet.get("sources",{}))==set(OWN_NAMES),"exact controller source packet")
    for name,h in packet["sources"].items():checked(BASE/name,h)
    return packet

def deadline_ok(now=None):
    now=now or datetime.now(timezone.utc)
    require(now<datetime.fromisoformat(DEADLINE.replace("Z","+00:00")),"fixed DAMP deadline passed")

def parent_terminal(raw):
    d=raw.get("structuredContent",raw)
    require(d.get("operationId")==PARENT_OPERATION and d.get("terminal") is True,
            "actual MA0455 terminal operation receipt required")
    op=d.get("operation",{})
    require(op.get("routeDecision")=="peer_direct" and op.get("targetPeerId")==PARENT_PEER,
            "actual original MA peer/direct route proof required")
    result=op.get("result",{});r=result.get("record",{})
    require(result.get("found") is True and result.get("ok") is True and
            result.get("lane")=="job" and r.get("lane")=="job" and
            result.get("state")=="completed" and r.get("id")==PARENT_OPERATION and
            r.get("state")=="completed" and r.get("exitCode")==0 and
            r.get("cancelled") is False and r.get("timedOut") is False and r.get("error") is None and
            r.get("command")=="/usr/bin/python3" and r.get("cwd")==str(REPO),
            "authoritative actual exec record must be completed0, not outer ok alone")
    return {"operation_id":PARENT_OPERATION,"peer":PARENT_PEER,"state":"completed","exit_code":0,
            "scope":"actual MAIN persisted AWMCP terminal record; controller has no remote credentials"}

def parse_processes(raw):
    """Actual combined NPU/Chip first process-table column; fail closed on unknown rows."""
    require("Process id" in raw,"actual process table missing")
    body=raw.split("Process id",1)[1].splitlines()[1:]
    rows={i:[] for i in range(8)};empty=set()
    for line in body:
        text=line.strip()
        if not text or text.startswith("+"):continue
        m=re.fullmatch(r"\|\s*No running processes found in NPU (\d+)\s*\|",text)
        if m:
            card=int(m[1]);require(card in rows,"unknown NPU empty row");empty.add(card);continue
        fields=[x.strip() for x in text.split("|")]
        require(len(fields)==6 and fields[0]==fields[-1]=="","unknown native process-table shape")
        pair=re.fullmatch(r"(\d+)\s+(\d+)",fields[1])
        require(pair and fields[2].isdigit() and fields[4].isdigit(),"unknown native combined process row")
        card,chip=map(int,pair.groups());pid=int(fields[2])
        require(card in rows and chip==0 and pid>0 and fields[3],"unexpected card/chip/PID")
        require(not any(x["pid"]==pid for x in rows[card]),"duplicate process row")
        rows[card].append({"pid":pid,"name":fields[3],"memory_mib":int(fields[4])})
    require(all(rows[i] or i in empty for i in rows) and not any(rows[i] and i in empty for i in rows),
            "complete all-card process/empty coverage required")
    return rows

def proc_identity(pid):
    p=Path("/proc")/str(pid)
    stat=(p/"stat").read_text();tail=stat[stat.rfind(")")+2:].split()
    require(len(tail)>19,"PID stat malformed")
    return {"pid":pid,"start_ticks":int(tail[19]),"cgroup":(p/"cgroup").read_text(),
            "cmdline":(p/"cmdline").read_bytes().replace(b"\0",b" ").decode(errors="replace")}

def protected_fingerprint(rows):
    return {str(card):[{k:v for k,v in proc_identity(r["pid"]).items() if k!="cmdline"}
                      for r in rows[card]] for card in range(4)}

def owner_pid(pid,cid):
    require(re.fullmatch("[a-f0-9]{64}",cid),"exact immutable container ID")
    identity=proc_identity(pid)
    require(any(cid==component or component=="docker-"+cid+".scope"
                for line in identity["cgroup"].splitlines()
                for component in line.split(":",2)[-1].split("/")),
            "NPU PID not in exact owned container cgroup")
    return identity

def inspect_proof(entry,e,cid):
    require(entry.get("Id")==cid and re.fullmatch("[a-f0-9]{64}",cid) and
            entry.get("Name")=="/"+e["container_name"] and entry.get("Image")==
            "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1",
            "exact new owned container name/ID/image required")
    h=entry["HostConfig"];config=entry["Config"];labels=config.get("Labels") or {}
    require(h.get("Privileged") is False and h.get("NetworkMode")=="none" and
            not h.get("DeviceRequests") and h.get("IpcMode")!="host" and
            h.get("Memory")==8*GIB and h.get("MemorySwap")==8*GIB and
            h.get("NanoCpus")==10**9 and set(h.get("CapDrop",[]))=={"ALL"} and
            any(x in ("no-new-privileges","no-new-privileges=true") for x in h.get("SecurityOpt",[])),
            "actual nonprivileged/no-network/no-swap1CPU8GiB constraints")
    require(labels.get("model-tuning-lab.owner")=="damp-allT-dispatch-v1" and
            labels.get("model-tuning-lab.run")==e["container_name"].split("_20261006_",1)[1],
            "actual controller-owned prepared label mismatch")
    mapping={x["PathOnHost"]:x["PathInContainer"] for x in h.get("Devices",[])}
    wanted={"/dev/davinci"+str(e["physical_card"]):"/dev/davinci0",
        **{"/dev/"+n:"/dev/"+n for n in ("davinci_manager","devmm_svm","hisi_hdc")}}
    require(mapping==wanted and len(h.get("Devices",[]))==4,"single authorized physical card only")
    argv=e["docker_create_argv"]
    expected={}
    for i,x in enumerate(argv):
        if x=="--mount":
            fields=dict(v.split("=",1) for v in argv[i+1].split(",") if "=" in v)
            expected[fields["target"]]=(fields["source"],not argv[i+1].endswith(",readonly"))
    mounts=entry.get("Mounts",[])
    require(len(mounts)==len(expected) and {m["Destination"] for m in mounts}==set(expected),
            "no missing/extra container mounts")
    for m in mounts:
        source,rw=expected[m["Destination"]]
        require(m.get("Type")=="bind" and m.get("RW") is rw and
                Path(m["Source"]).resolve()==Path(source).resolve(),"actual mount/source/mutability mismatch")
    env=dict(x.split("=",1) for x in config.get("Env",[]) if "=" in x)
    for i,x in enumerate(argv):
        if x=="-e":
            k,v=argv[i+1].split("=",1);require(env.get(k)==v,"actual environment drift")
    after=argv[argv.index("--entrypoint")+2:]
    require(config.get("Entrypoint")==["/bin/bash"] and config.get("Cmd")==after[1:] and
            config.get("WorkingDir")==str(REPO),"actual command/entrypoint/cwd drift")
    return {"id":cid,"physical":e["physical_card"],"logical":0,"privileged":False,
            "create_argv_sha256":e["create_argv_sha256"],"state":entry["State"]}

def parse_cgroup(text):
    rows={}
    for line in text.splitlines():
        fields=line.split(":",2);require(len(fields)==3 and fields[2].startswith("/"),"actual cgroup syntax")
        require(".." not in Path(fields[2]).parts,"cgroup traversal")
        if fields[0]=="0" and fields[1]=="":rows["unified"]=fields[2]
        for key in fields[1].split(","):
            if key:rows[key]=fields[2]
    return rows

def cgroup_mounts(raw):
    result={}
    for line in raw.splitlines():
        left,sep,right=line.partition(" - ");require(sep,"mountinfo syntax")
        fields=left.split();tail=right.split()
        if tail[0]=="cgroup2":result["unified"]=(Path(fields[4]),Path(fields[3]))
        elif tail[0]=="cgroup":
            for controller in tail[2].split(","):
                if controller in ("memory","cpu","cpuacct"):result[controller]=(Path(fields[4]),Path(fields[3]))
    return result

def cgroup_path(rows,mounts,controller,name):
    require(controller in rows and controller in mounts,"missing actual cgroup controller")
    mount,root=mounts[controller]
    group=Path(rows[controller])
    require(group.is_relative_to(root),"actual cgroup not under mount root")
    p=mount/group.relative_to(root)
    require(p.resolve().is_relative_to(mount.resolve()),"cgroup outside controller mount")
    return p/name

def cgroup_record(entry,cid,mem,quota):
    pid=entry["State"].get("Pid");require(type(pid) is int and pid>0,"running cgroup PID required")
    owner_pid(pid,cid)
    text=(Path("/proc")/str(pid)/"cgroup").read_text()
    rows=parse_cgroup(text);mounts=cgroup_mounts(Path("/proc/self/mountinfo").read_text())
    def path(controller,name):return cgroup_path(rows,mounts,controller,name)
    if "unified" in rows:
        limit=int(path("unified","memory.max").read_text())
        swap=int(path("unified","memory.swap.max").read_text())
        current=int(path("unified","memory.current").read_text())
        cpu=path("unified","cpu.max").read_text().split()
        require(len(cpu)==2 and cpu[0]!="max" and int(cpu[0])==quota*int(cpu[1]),
                "actual unified CPU quota mismatch")
        require(limit==mem and swap==0,"actual unified memory/no-swap cap mismatch")
        peak_path=path("unified","memory.peak")
        peak=int(peak_path.read_text()) if peak_path.is_file() else None
        kind="v2"
    else:
        limit=int(path("memory","memory.limit_in_bytes").read_text())
        current=int(path("memory","memory.usage_in_bytes").read_text())
        peak=int(path("memory","memory.max_usage_in_bytes").read_text())
        period=int(path("cpu","cpu.cfs_period_us").read_text())
        ticks=int(path("cpu","cpu.cfs_quota_us").read_text())
        require(limit==mem and ticks==quota*period,"actual v1 memory/CPU cap mismatch")
        memsw=path("memory","memory.memsw.limit_in_bytes")
        if memsw.is_file():require(int(memsw.read_text())==mem,"actual v1 mem+swap cap mismatch")
        else:
            require(re.search(r"^SwapTotal:\s*0\s+kB",Path("/proc/meminfo").read_text(),re.M),
                    "v1 missing memsw requires actual no host swap")
        kind="v1"
    require(0<=current<=mem,"actual cgroup memory accounting")
    return {"container_id":cid,"kind":kind,"memory_limit_bytes":limit,
            "memory_current_bytes":current,"memory_peak_bytes":peak,"cpu_quota":quota}

class Commands:
    def __init__(self,audit):
        self.audit=Path(audit);self.index=0
    def run(self,label,argv,timeout=COMMAND_TIMEOUT,allowed=(0,)):
        self.index+=1;stem=f"{self.index:04d}-{label}"
        started=time.monotonic();out=self.audit/(stem+".stdout");err=self.audit/(stem+".stderr")
        result=None;error=None
        with out.open("xb") as stdout,err.open("xb") as stderr:
            try:
                result=subprocess.run(argv,stdout=stdout,stderr=stderr,timeout=timeout,check=False)
            except BaseException as e:error=repr(e)
        row={"argv":argv,"exit_code":None if result is None else result.returncode,"error":error,
            "stdout":str(out),"stdout_sha256":sha(out),"stderr":str(err),"stderr_sha256":sha(err),
            "elapsed_seconds":time.monotonic()-started,"automatic_retry":False}
        write_new(self.audit/(stem+".receipt.json"),row)
        require(error is None and result.returncode in allowed,"command failed; retain "+stem)
        return out.read_text(errors="replace"),result.returncode
    def json(self,label,argv):
        stdout,_=self.run(label,argv);return json.loads(stdout)

def inspect(cmd,cid,label="inspect"):
    value=cmd.json(label,["docker","inspect",cid]);require(len(value)==1,"unique actual container")
    return value[0]

def mount_budget(cmd):
    text,_=cmd.run("dockerd-pid",["pgrep","-x","dockerd"])
    require(re.fullmatch(r"\d+\s*",text) is not None,"one actual Docker daemon PID")
    pid=int(text);identity=proc_identity(pid)
    require(Path("/proc",str(pid),"exe").resolve().name=="dockerd","daemon executable mismatch")
    maximum=int(Path("/proc/sys/fs/mount-max").read_text())
    own=Path("/proc/self/mountinfo").read_text()
    daemon=(Path("/proc")/str(pid)/"mountinfo").read_text()
    current=max(len(own.splitlines()),len(daemon.splitlines()))
    require(maximum-current>=MOUNT_PLAN_RESERVE,"actual mount namespace headroom below conservative2560")
    return {"mount_max":maximum,"self_mount_count":len(own.splitlines()),
            "daemon_mount_count":len(daemon.splitlines()),"daemon_identity":identity,
            "remaining":maximum-current,"policy_reserve":MOUNT_PLAN_RESERVE,
            "bound_measured":False}

def selector_budget(cmd,allow):
    stdout,_=cmd.run("running-IDs",["docker","ps","--quiet","--no-trunc"])
    ids=[x for x in stdout.splitlines() if x.strip()]
    selectors=[]
    for cid in ids:
        require(re.fullmatch("[a-f0-9]{64}",cid),"actual full running container ID")
        entry=inspect(cmd,cid,"running-inspect")
        labels=entry["Config"].get("Labels") or {}
        if labels.get("model-tuning-lab.cpu-selector-owner")=="main-cpu-selector-v1":
            require(allow,"CPU selector running; default four-shard controller requires no fitting overlap")
            h=entry["HostConfig"]
            require(entry["Image"]=="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
                and h.get("Privileged") is False and not h.get("Devices") and not h.get("DeviceRequests")
                and h.get("NanoCpus")==2*10**9 and h.get("Memory")==4*GIB and h.get("MemorySwap")==4*GIB,
                "actual explicit CPU-selector2CPU4GiB/no-device constraints")
            selectors.append({"id":cid,"name":entry["Name"],
                "cgroup":cgroup_record(entry,cid,4*GIB,2)})
    require(len(selectors)<=1,"only one admitted optional CPU selector")
    return selectors

def fresh_resources(cmd,safety,planner,protected=None,allow_selector=False):
    # Reuse actual frozen host safety parser/canary-idle envelope, not an invented idle assertion.
    safety.output=lambda argv,timeout=30:cmd.run("host-safety",argv,timeout)[0]
    snap=safety.idle_snapshot()
    rows=parse_processes(snap["npu_smi"])
    require(all(not rows[x] for x in range(4,8)),"real external/owned NPU worker still live")
    protection=protected_fingerprint(rows)
    require(protected is None or protection==protected,"protected0-3 PID/start/cgroup changed; never stop them")
    selectors=selector_budget(cmd,allow_selector)
    minimum=44*GIB if selectors else planner.AGGREGATE_MIN_BYTES
    m=re.search(r"^MemAvailable:\s*(\d+)\s+kB",snap["meminfo"],re.M)
    require(m and int(m[1])*1024>=minimum,"fresh ordinaryRAM40/44GiB admission; never reclaim HugeTLB")
    available=int(m[1])*1024;disk=shutil.disk_usage(ROOT).free
    require(disk>=planner.DISK_MIN_BYTES,"fresh result filesystem free disk")
    engine=cmd.json("docker-info",["docker","info","--format","{{json .}}"])
    require(type(engine.get("NCPU")) is int and engine["NCPU"]>=planner.JOINT_CPU_QUOTA,"fresh Docker NCPU joint6 quota")
    nodes=cmd.run("node-holders",["fuser","-v"]+["/dev/davinci"+str(i) for i in range(4,8)],allowed=(0,1))
    mounting=mount_budget(cmd)
    return {"observed_at_unix_ns":time.time_ns(),"snapshot":snap,"processes":rows,"protected":protection,
        "ordinary_mem_available_bytes":available,"free_disk_bytes":disk,"ram_admission_bytes":minimum,
        "docker_info":engine,"selectors_observed":selectors,"node_holders_exit":nodes[1],
        "mount_headroom":mounting,"scope":"fresh actual local source/resource checks; no performance"}

def absent_names(cmd,entries):
    for e in entries:
        text,code=cmd.run("name-absence",["docker","container","inspect",e["container_name"]],allowed=(0,1))
        require(code==1,"planned name already exists; never restart or overwrite")
        # Original stderr is retained by Commands; verify actual exact not-found, not daemon failure.
        receipt=read_json(cmd.audit/(f"{cmd.index:04d}-name-absence.receipt.json"))
        err=Path(receipt["stderr"]).read_text()
        require("No such object: "+e["container_name"] in err or
                "No such container: "+e["container_name"] in err,"actual name absence unproven")

def parent_stopped(cmd,original,parent,args):
    operation=parent_terminal(read_json(checked(args.parent_operation_receipt,args.parent_operation_sha256)))
    lock=parent.finalized(args.source_lock_sha256,args.parent_result_sha256)
    require(lock["recovery"]["fresh_container_id"]==PARENT_ID,"actual source-lock parent ID mismatch")
    create=read_json(PARENT_AUDIT/"create-command.json")["argv"]
    require(create[create.index("--name")+1]==PARENT_NAME,"actual original parent name")
    owner=create[create.index("--label")+1].split("=",1)
    require(owner[0]==original.LABEL and owner[1],"actual parent owner nonce")
    original.NAME=PARENT_NAME
    entry=inspect(cmd,PARENT_ID,"parent-stopped-inspect")
    original.container_proof(entry,PARENT_ID,owner[1])
    require(entry["State"]["Status"]=="exited" and not entry["State"]["Running"],"parent TP4 still running")
    return {"operation":operation,"container_id":PARENT_ID,"parent_result_sha256":args.parent_result_sha256,
        "source_lock_sha256":args.source_lock_sha256,"stopped_inspection":entry}

def filesystem_preflight_code(planner):
    # Run within the NEW correctly mapped container but do not import Torch/NPU.
    spec={"candidate":(str(planner.LIBRARY),planner.LIBRARY_SHA),
          "native":(planner.NATIVE_SO,planner.NATIVE_SO_SHA)}
    return "import hashlib,json,pathlib; rows="+repr(spec)+"; "+\
        "result={k:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for k,(p,h) in rows.items()}; "+\
        "assert all(result[k]==h for k,(p,h) in rows.items()); "+\
        "print(json.dumps({'schema':'damp_allT_container_files_v1','hashes':result,'npu_executed':False}))"

def immutable_exec(argv,cid):
    require(argv[:2]==["docker","exec"] and re.fullmatch("[a-f0-9]{64}",cid),"exact owned exec ID")
    actual=list(argv);actual[2]=cid;return actual

def json_line(path,schema):
    rows=[]
    for line in Path(path).read_text(errors="replace").splitlines():
        try:x=json.loads(line,parse_constant=reject_nonfinite_json)
        except ValueError:continue
        if isinstance(x,dict) and x.get("schema")==schema:rows.append(x)
    require(len(rows)==1,"one actual source-bound result JSON required")
    return rows[0]

def stop_owned(cmd,entry,cid):
    actual=inspect(cmd,cid,"stop-preinspect");inspect_proof(actual,entry,cid)
    if actual["State"]["Running"]:
        cmd.run("owned-stop",["docker","stop","--time","30",cid],timeout=45)
    after=inspect(cmd,cid,"stop-afterinspect");inspect_proof(after,entry,cid)
    require(not after["State"]["Running"] and after["State"]["Status"] in ("exited","created"),
            "exact owned container stopped/retained")
    return {"id":cid,"name":entry["container_name"],"status":after["State"]["Status"],"deleted":False}

def parallel_jobs(cmd,entries,cids,key,timeout,monitor=None):
    jobs=[];started=time.monotonic()
    try:
        for e in entries:
            cid=cids[e["physical_card"]];inspect_proof(inspect(cmd,cid,"dispatch-inspect"),e,cid)
            argv=immutable_exec(e[key],cid)
            stem="parallel-"+key+"-physical"+str(e["physical_card"])
            out=cmd.audit/(stem+".stdout");err=cmd.audit/(stem+".stderr")
            a=out.open("xb")
            try:b=err.open("xb")
            except BaseException:a.close();raise
            job={"entry":e,"cid":cid,"argv":argv,"out":out,"err":err,"a":a,"b":b,"proc":None}
            jobs.append(job)
            job["proc"]=subprocess.Popen(argv,stdout=a,stderr=b)
        while any(j["proc"].poll() is None for j in jobs):
            deadline_ok()
            require(time.monotonic()-started<=timeout,"one-shot parallel phase timeout; no retry")
            require(all(j["proc"].poll() in (None,0) for j in jobs),"first real shard failure; no retry")
            if monitor is not None:monitor()
            time.sleep(3)
        require(all(j["proc"].returncode==0 for j in jobs),"parallel phase failed")
    finally:
        for j in jobs:
            proc=j["proc"]
            if proc is not None and proc.poll() is None:
                # Only local owned docker-exec client. Outer execute stops exact containers.
                proc.terminate()
                try:proc.wait(timeout=10)
                except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=10)
            j["a"].close();j["b"].close()
            write_new(cmd.audit/("parallel-"+key+"-physical"+str(j["entry"]["physical_card"])+".receipt.json"),
                {"argv":j["argv"],"container_id":j["cid"],"exit_code":None if proc is None else proc.returncode,
                 "stdout":str(j["out"]),"stdout_sha256":sha(j["out"]),"stderr":str(j["err"]),
                 "stderr_sha256":sha(j["err"]),"automatic_retry":False,
                 "scope":"correctness scheduling only, not performance"})
    return jobs

def monitor_owned(cmd,entries,cids,protected,audit,index,daemon_identity,allow_selector):
    raw,_=cmd.run("runtime-npu-smi",["npu-smi","info"])
    rows=parse_processes(raw)
    require(protected_fingerprint(rows)==protected,"protected0-3 changed; no signal sent to external work")
    process=[];cgroups=[]
    for e in entries:
        card=e["physical_card"];cid=cids[card]
        current=inspect(cmd,cid,"runtime-inspect");inspect_proof(current,e,cid)
        for row in rows[card]:
            process.append({"physical":card,**owner_pid(row["pid"],cid)})
        cgroup=cgroup_record(current,cid,8*GIB,1)
        require(not current["State"].get("OOMKilled"),"actual owned cgroup OOM")
        require(cgroup["memory_current_bytes"]<8*GIB,"owned cgroup at memory cap")
        cgroups.append(cgroup)
    rawmem=Path("/proc/meminfo").read_text();m=re.search(r"^MemAvailable:\s*(\d+)\s+kB",rawmem,re.M)
    require(m and int(m[1])*1024>=RUNTIME_RESERVE,"ordinary RAM below8GiB runtime reserve")
    require(shutil.disk_usage(ROOT).free>=GIB,"runtime free disk below1GiB")
    # The admission budget is conservative; never raise mount-max.
    daemon=proc_identity(daemon_identity["pid"])
    require(daemon["start_ticks"]==daemon_identity["start_ticks"] and
            daemon["cgroup"]==daemon_identity["cgroup"],"actual Docker daemon changed during gate")
    maximum=int(Path("/proc/sys/fs/mount-max").read_text())
    counts={"self":len(Path("/proc/self/mountinfo").read_text().splitlines()),
            "daemon":len((Path("/proc")/str(daemon["pid"])/"mountinfo").read_text().splitlines())}
    require(maximum-max(counts.values())>=MOUNT_RUNTIME_RESERVE,
            "runtime own/daemon mount namespace reserve")
    selectors=selector_budget(cmd,allow_selector)
    write_new(audit/("monitor-"+str(index)+".json"),{"npu_smi":raw,"processes":process,
        "ordinary_mem_available_bytes":int(m[1])*1024,"protected":protected,
        "cgroups":cgroups,"mount_max":maximum,"mount_counts":counts,
        "selectors_observed":selectors})

def execute(args,prepared):
    require(os.environ.get("DAMP_ALLT_DISPATCH_CONTROLLER_EXECUTE")=="1","MAIN explicit execution opt-in")
    require(Path.cwd().resolve()==REPO,"canonical host cwd required")
    deadline_ok();packet_identity(args.packet_manifest,args.packet_sha256)
    planner,original,parent,safety,source=prepared
    root=ROOT/("allT-dispatch-"+args.run_id)
    initial=planner.make_plan(args.run_id,root)
    require(not root.exists() and not root.is_symlink(),"new external result root only")
    # No container/NPU before parent terminal and all source evidence checks.
    checked(args.parent_operation_receipt,args.parent_operation_sha256)
    parent_terminal(read_json(args.parent_operation_receipt))
    parent.finalized(args.source_lock_sha256,args.parent_result_sha256)
    root.mkdir(exist_ok=False);audit=root/"launch";audit.mkdir()
    cmd=Commands(audit);entries=initial["shards"];cids={};failed=None;results=None
    try:
        write_new(audit/"SOURCE.json",{"packet":packet_identity(args.packet_manifest,args.packet_sha256),
            "packet_sha256":args.packet_sha256,"source":source,"initial_plan":initial})
        write_new(audit/"PARENT_TERMINAL.json",parent_stopped(cmd,original,parent,args))
        image=cmd.json("image-inspect",["docker","image","inspect",planner.IMAGE])
        require(len(image)==1 and image[0]["Id"]==planner.IMAGE and image[0]["Architecture"]=="arm64","actual immutable image")
        before=fresh_resources(cmd,safety,planner,allow_selector=args.allow_cpu_selector)
        protected=before["protected"];write_new(audit/"PRELAUNCH.json",before)
        absent_names(cmd,entries)
        for e in entries:
            Path(e["host_output_mount"]).mkdir(exist_ok=False)
        # Sources rechecked immediately before the first create; no copied caches.
        source_preparation();packet_identity(args.packet_manifest,args.packet_sha256)
        for e in entries:
            deadline_ok()
            stdout,_=cmd.run("create-physical"+str(e["physical_card"]),e["docker_create_argv"])
            cid=stdout.strip()
            require(re.fullmatch("[a-f0-9]{64}",cid),"unknown create outcome; no guessing/retry/foreign cleanup")
            cids[e["physical_card"]]=cid
            inspect_proof(inspect(cmd,cid,"created-inspect"),e,cid)
            cmd.run("start-physical"+str(e["physical_card"]),["docker","start",cid])
            actual=inspect(cmd,cid,"started-inspect");inspect_proof(actual,e,cid)
            cgroup_record(actual,cid,8*GIB,1)
            # Existing native identity is checked before create. Actual immutable-image
            # file bytes rechecked here, before any Torch/NPU canary.
            argv=["docker","exec",cid,planner.PYTHON,"-B","-c",filesystem_preflight_code(planner)]
            cmd.run("file-source-preflight",argv)
        canary_before=fresh_resources(cmd,safety,planner,protected,args.allow_cpu_selector)
        write_new(audit/"CANARY_PRECHECK.json",canary_before)
        jobs=parallel_jobs(cmd,entries,cids,"docker_canary_exec_argv",CANARY_TIMEOUT)
        for j in jobs:
            e=j["entry"];canary=json_line(j["out"],"damp_allT_canary_v1")
            write_new(e["expected_canary_path"],canary)
        final=fresh_resources(cmd,safety,planner,protected,args.allow_cpu_selector)
        info=root/"engine-info.json";write_new(info,final["docker_info"])
        admission={"schema":"damp_allT_MAIN_live_admission_v1","observed_at_unix_ns":final["observed_at_unix_ns"],
            "capture_operation_id":PARENT_OPERATION,"capture_terminal":True,"owned_TP4_lease_released":True,
            "physical_npu_ids":[4,5,6,7],"exclusive_resource_check_passed":True,"protected_NPU0_3_unchanged":True,
            "ordinary_mem_available_bytes":final["ordinary_mem_available_bytes"],
            "per_card_cgroup_limit_bytes":8*GIB,"free_disk_bytes":final["free_disk_bytes"],
            "docker_cpu_capacity":{"observed_at_unix_ns":final["observed_at_unix_ns"],
                "info_path":str(info),"info_sha256":sha(info),"per_numeric_shard_cpu_quota":1,
                "numeric_shards_cpu_quota":4,"optional_selector_cpu_quota":2,"joint_cpu_quota":6,
                "formal_performance_exclusive":True},"cards":{}}
        for e in entries:
            cid=cids[e["physical_card"]];actual=inspect(cmd,cid,"final-inspect");inspect_proof(actual,e,cid)
            proof={"physical_npu_ids":[e["physical_card"]],"logical_to_physical":{"0":e["physical_card"]},
                "privileged":False,"exclusive_resource_check_passed":True,
                "observed_at_unix_ns":time.time_ns(),"container_id":cid,
                "container_inspect":actual,"fresh_resource_audit":str(audit/"FINAL_PRECHECK.json")}
            write_new(e["expected_device_proof_path"],proof)
            admission["cards"][str(e["physical_card"])]={"container_name":e["container_name"],"container_id":cid,
                "container_image_id":planner.IMAGE,"create_argv_sha256":e["create_argv_sha256"],
                "fresh_created_from_this_plan":True,"inspect_single_card_scope_passed":True,
                "device_proof":e["expected_device_proof_path"],"device_proof_sha256":sha(e["expected_device_proof_path"]),
                "canary":e["expected_canary_path"],"canary_sha256":sha(e["expected_canary_path"])}
        write_new(audit/"FINAL_PRECHECK.json",final)
        write_new(root/"admission.json",admission)
        # Existing frozen planner enforces real5min/canary/schema/source contract.
        planner.validate_live_admission(admission,entries,planner.gate_contract(),time.time_ns())
        source_preparation();packet_identity(args.packet_manifest,args.packet_sha256);deadline_ok()
        write_new(audit/"EXECUTION_PLAN.json",{"shards":entries,"immutable_ID_exec":True,"not_performance":True})
        count=[0]
        def monitor():
            count[0]+=1;monitor_owned(cmd,entries,cids,protected,audit,count[0],
                final["mount_headroom"]["daemon_identity"],args.allow_cpu_selector)
        print("START four disjoint real-T correctness shards; not formal performance",flush=True)
        parallel_jobs(cmd,entries,cids,"docker_gate_exec_argv",GATE_TIMEOUT,monitor)
        reports=[]
        for e in entries:
            p=Path(e["gate_output"])/"report.json";report=read_json(p,64*1024*1024)
            binding=report.get("bindings",{})
            require(binding.get("source_manifest_sha256")==planner.SOURCE_SHA and
                    binding.get("runtime_manifest_sha256")==planner.RUNTIME_SHA and
                    binding.get("library_sha256")==planner.LIBRARY_SHA and
                    binding.get("build_receipt_sha256")==planner.RECEIPT_SHA,
                    "actual shard must match the exact source/runtime/library/build receipts")
            reports.append(report)
        gate=planner.gate_contract();sys.path.insert(0,str(planner.GATE))
        results=gate.validate_shards(reports)
        source_preparation();packet_identity(args.packet_manifest,args.packet_sha256);deadline_ok()
        write_new(audit/"AGGREGATE.json",{"source_bound_gate":results,
            "reports":[{"path":str(Path(e["gate_output"])/"report.json"),
                         "sha256":sha(Path(e["gate_output"])/"report.json")} for e in entries],
            "npu_executed":True,"serving_ready":False,"performance_claim":False,"task_accuracy_claim":False})
    except BaseException as error:
        failed=repr(error)
        retained=[]
        for e in entries:
            p=Path(e["gate_output"])/"report.json"
            try:retained.append({"physical":e["physical_card"],"path":str(p),
                "sha256":sha(p) if p.is_file() else None,"content":read_json(p,64*1024*1024) if p.is_file() else None})
            except BaseException as copy_error:retained.append({"physical":e["physical_card"],"copy_error":repr(copy_error)})
        write_new(audit/"FAILURE.json",{"original_error":failed,"nullable_gate_reports":retained,
            "automatic_retry":False,"unknown_creates_not_reclaimed":True,"scope":"implementation/resource/numerical gate failure; not paper-wide no-go"})
    finally:
        stops=[]
        for e in entries:
            cid=cids.get(e["physical_card"])
            if cid is not None:
                try:stops.append(stop_owned(cmd,e,cid))
                except BaseException as error:
                    stops.append({"id":cid,"stop_error":repr(error),"deleted":False})
                    if failed is None:failed="owned stop failed; MAIN attention required"
        write_new(audit/"STOP_RETAIN.json",stops)
        if any("stop_error" in row for row in stops):
            write_new(audit/"STOP_FAILURE.json",{"records":stops,"MAIN_attention_required":True,
                "no_delete":True,"original_failure":failed})
        if cids:
            try:
                safety.output=lambda argv,timeout=30:cmd.run("release-safety",argv,timeout)[0]
                released=safety.idle_snapshot();rows=parse_processes(released["npu_smi"])
                require(protected_fingerprint(rows)==protected,"protected0-3 changed during cleanup")
                require(all(not rows[card] for card in range(4,8)),"owned/external workers still on4-7 after release")
                write_new(audit/"POST_RELEASE.json",{"snapshot":released,"protected":protected,
                    "all_authorized_target_cards_process_empty":True})
            except BaseException as error:
                write_new(audit/"RELEASE_FAILURE.json",{"error":repr(error),"no_external_signals":True,
                    "MAIN_attention_required":True,"original_failure":failed})
                if failed is None:failed="post-release proof failed; MAIN attention required"
    require(failed is None,"failed one-shot controller; evidence retained: "+str(audit))
    write_new(audit/"RESULT.json",{"status":"restricted_allT_correctness_dispatch_pass",
        "aggregate":results,"exact_owned_containers_stopped_and_retained":True,
        "serving_ready":False,"general_sr_supported":False,"performance_claim":False,"task_accuracy_claim":False,
        "deadline":DEADLINE})
    return {"status":"restricted_allT_correctness_dispatch_pass","audit":str(audit),"not_performance":True}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute",action="store_true")
    parser.add_argument("--run-id",default="v1")
    for name in ("packet-manifest","parent-operation-receipt"):
        parser.add_argument("--"+name,type=Path)
    for name in ("packet-sha256","parent-operation-sha256","source-lock-sha256","parent-result-sha256"):
        parser.add_argument("--"+name)
    parser.add_argument("--allow-cpu-selector",action="store_true",help="observe/admit one existing2CPU4GiB CPU-only selector, never start it")
    args=parser.parse_args()
    if args.execute:
        require(os.environ.get("DAMP_ALLT_DISPATCH_CONTROLLER_EXECUTE")=="1",
                "MAIN explicit execution opt-in")
        for field in ("packet_manifest","packet_sha256","parent_operation_receipt","parent_operation_sha256",
                      "source_lock_sha256","parent_result_sha256"):
            require(getattr(args,field) is not None,"required actual source/parent argument: "+field)
    prepared=source_preparation()
    if not args.execute:
        planner=prepared[0]
        packet=planner.make_plan(args.run_id,ROOT/("allT-dispatch-"+args.run_id))
        print(json.dumps({"schema":"damp-allT-controller-plan/v1","status":"dry-plan-not-executed",
            "source":prepared[4],"shards":packet["shards"],"deadline":DEADLINE,"no_docker_or_npu":True,
            "pending":["actual MA0455 terminal record/hash","actual source-lock/result hashes",
                       "MAIN reviewed NEW packet hash","fresh execute-time inspections/resource/canary"],
            "serving_ready":False,"performance_claim":False},allow_nan=False))
        return 0
    print(json.dumps(execute(args,prepared),allow_nan=False));return 0

if __name__=="__main__":raise SystemExit(main())

#!/usr/bin/env python3
"""MAIN-only H8 B16/physical6 host controller. Default OFF; no algorithm edits."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,math,os,re,resource,shutil,stat,subprocess,sys,time
from datetime import datetime,timedelta,timezone
from pathlib import Path,PurePosixPath

ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab")
BASE=ROOT/"projects/kvbuffer-parallel-ascend/tools/short_horizon_h8_gate_v4"
FROZEN=ROOT/"projects/kvbuffer-parallel-ascend/tools/full_matrix_host_v2/host.py"
FROZEN_SHA="ab0296c698df00c9c3b2ce377601f6d6723adde6efb4a9e65407beca51ba5f86"
OLD=ROOT/"projects/kvbuffer-parallel-ascend/tools/saved_step_native_order_v2/host_run.py"
OLD_SHA="86c1ca7f59c6ad5b2b4d5efb155394455a12376cf368e06f9e2e13d39b7192fc"
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
NATIVE="/vllm-workspace/vllm-ascend/vllm_ascend/vllm_ascend_C.cpython-312-aarch64-linux-gnu.so"
NATIVE_SHA="eaa9457a21a45e2cb027c1345ee670b59d10fcd6f4a8be8b0b1bf2fde1d2232a"
OWNER="kvbuffer-h8-host-v1"
DOCKER="/usr/bin/docker";PRLIMIT="/usr/bin/prlimit";SMI="/usr/local/sbin/npu-smi"
PY="/usr/local/python3.12.13/bin/python3"
MEM=8*1024**3;HOST_MEM=256*1024**2;RESERVE=8*1024**3
WORKSPACE=5*1024**3;PHASE_SECONDS=5400;CLEANUP_SECONDS=90
CUTOFF=datetime.fromisoformat("2026-10-08T08:29:54+00:00")
BATCH=16;PHYSICAL=6
_FROZEN=None

def require(ok,why):
    if not ok:raise ValueError(why)
def utc():return datetime.now(timezone.utc)
def sha(path):
    p=Path(path);require(p.is_file() and not p.is_symlink(),"ordinary exact source/evidence")
    return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(path,digest):
    p=Path(path);require(p.is_absolute() and ".." not in p.parts and
        re.fullmatch("[0-9a-f]{64}",digest or "") is not None,"explicit absolute SHA-bound Ref")
    require(sha(p)==digest,"Ref bytes changed: "+str(p))
    return {"path":str(p),"sha256":digest}
def write(path,value):
    with Path(path).open("x") as f:
        f.write(json.dumps(value,indent=2,allow_nan=False)+"\n");f.flush();os.fsync(f.fileno())
    return {"path":str(path),"sha256":sha(path)}
def frozen():
    global _FROZEN
    require(sha(FROZEN)==FROZEN_SHA and sha(OLD)==OLD_SHA,"frozen helper closure changed")
    if _FROZEN is None:
        spec=importlib.util.spec_from_file_location("_h8_frozen_host_helpers",FROZEN)
        _FROZEN=importlib.util.module_from_spec(spec);spec.loader.exec_module(_FROZEN)
        _FROZEN.legacy()
    return _FROZEN
def controller_contract():
    require(Path(__file__).resolve()==BASE/"host_run.py","MAIN must integrate reviewed controller first")
    spec=importlib.util.spec_from_file_location("_h8_controller_contract",BASE/"contract.py")
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module
def source_inputs(a):
    c=controller_contract()
    sr=ref(a.source_manifest,a.source_manifest_sha256)
    m,s=c.source_admission(sr)
    require(len(s)==84 and s.get(str(BASE/"host_run.py"))==sha(__file__),"actual current84 source closure")
    artifacts={name:ref(path,digest) for name,path,digest in
       (("library",a.library,a.library_sha256),("build",a.build_receipt,a.build_receipt_sha256),
        ("meta",a.meta_receipt,a.meta_receipt_sha256))}
    checked=c.artifacts(artifacts,m)
    protocol=c.protocol(BATCH,PHYSICAL)
    require(c.IMAGE==IMAGE and c.CGROUP_BYTES==MEM and
        protocol.get("candidate_namespace")=="qwen36_kvbuffer_short_horizon_v3" and
        protocol.get("materialization_interval")==8 and protocol.get("storage_log_capacity")==16,
        "new H8 namespace/interval/storage protocol, not old numerical authority")
    frozen()
    return c,sr,m,s,artifacts,checked,protocol

def cpus(text):
    require(type(text) is str,"actual CPU-list text")
    result=set()
    for field in text.strip().split(","):
        if not field:continue
        require(re.fullmatch("[0-9]+(?:-[0-9]+)?",field) is not None,"malformed CPU list")
        bounds=[int(v) for v in field.split("-")];lo=bounds[0];hi=bounds[-1]
        require(lo<=hi and hi<=1048576,"bounded CPU range");result.update(range(lo,hi+1))
    return result
def quota(text,version,period=None):
    if version==2:
        words=text.split();require(len(words)==2,"actual cpu.max")
        q=words[0];p=int(words[1]);require(p>0,"positive CPU period")
        require(q=="max" or (q.isdigit() and int(q)>0),"positive actual v2 quota")
        return None if q=="max" else int(q)/p
    q=int(text);p=int(period);require(p>0 and (q==-1 or q>0),"actual v1 CPU quota/period")
    return None if q==-1 else q/p
def hierarchy(pid,controller):
    proc=Path("/proc")/str(pid)
    groups={}
    for line in (proc/"cgroup").read_text().splitlines():
        ident,names,path=line.split(":",2)
        if ident=="0" and not names:groups["v2"]=path
        for name in names.split(","):groups[name]=path
    candidates=[]
    for line in Path("/proc/self/mountinfo").read_text().splitlines():
        left,right=line.split(" - ",1);fields=left.split();parts=right.split()
        if parts[0]=="cgroup2" and "v2" in groups:candidates.append((2,fields[3],fields[4],groups["v2"]))
        if parts[0]=="cgroup" and controller in parts[2].split(",") and controller in groups:
            candidates.append((1,fields[3],fields[4],groups[controller]))
    require(len(candidates)==1,"one complete actual "+controller+" cgroup hierarchy")
    version,root,mount,group=candidates[0]
    require(root=="/","hidden cgroup ancestors are not admission proof")
    logical=PurePosixPath(group);require(logical.is_absolute() and ".." not in logical.parts,"actual cgroup path")
    leaf=Path(mount)/str(logical).lstrip("/")
    boundary=Path(mount);chain=[]
    while True:
        require(leaf==boundary or boundary in leaf.parents,"bounded cgroup ancestor walk")
        chain.append(leaf)
        if leaf==boundary:break
        leaf=leaf.parent
    return version,group,mount,chain
def cpu_view(pid):
    h=frozen();before=h.process_identity(pid)
    version,group,mount,chain=hierarchy(pid,"cpu")
    limits=[];quota_rows=[]
    for path in chain:
        if version==1:
            q=(path/"cpu.cfs_quota_us").read_text().strip();p=(path/"cpu.cfs_period_us").read_text().strip()
            cap=quota(q,1,p)
        else:
            file=path/"cpu.max"
            require(file.is_file() or path==Path(mount),"actual cpu.max missing")
            q=file.read_text().strip() if file.is_file() else "max 100000";p=None;cap=quota(q,2)
        key="cpu:"+str(path.relative_to(mount))
        quota_rows.append(dict(key=key,path=str(path),quota=q,period=p,capacity=cap))
        if cap is not None:limits.append(cap)
    cv,cg,cm,cp_chain=hierarchy(pid,"cpuset");allowed=None;sets=[]
    for path in cp_chain:
        names=("cpuset.cpus.effective","cpuset.cpus") if cv==2 else ("cpuset.effective_cpus","cpuset.cpus")
        file=next((path/n for n in names if (path/n).is_file()),None)
        require(file is not None,"actual cpuset control missing")
        text=file.read_text().strip();value=cpus(text);sets.append(dict(path=str(file),value=text))
        if value:allowed=value if allowed is None else allowed&value
    require(allowed,"nonempty effective ancestor cpuset")
    affinity=set(os.sched_getaffinity(pid));effective=allowed&affinity
    require(effective,"actual PID has no eligible CPU")
    cap=min([len(effective),*limits])
    require(h.process_identity(pid)==before,"CPU process identity changed during observation")
    return dict(process=before,version=version,cgroup=group,affinity=sorted(affinity),
        ancestor_cpuset=sorted(allowed),effective_cpus=sorted(effective),
        effective_capacity=cap,quota_ancestors=quota_rows,cpuset_ancestors=sets)
def cpu_admission(host,daemon):
    require(host["effective_capacity"]>=1 and daemon["effective_capacity"]>=3,"actual host1/daemon guest1+reserve2 capacity")
    eligible=set(daemon["effective_cpus"]);host_cpu=min(host["effective_cpus"])
    spare=sorted(eligible-{host_cpu});require(len(spare)>=3,"distinct host1/guest1/reserve2 CPU slots")
    common={r["key"]:r["capacity"] for r in host["quota_ancestors"]}
    shared=[r["capacity"] for r in daemon["quota_ancestors"] if r["key"] in common and r["capacity"] is not None]
    shared += [common[r["key"]] for r in daemon["quota_ancestors"] if r["key"] in common and common[r["key"]] is not None]
    require(not shared or min(shared)>=4,"shared ancestor cannot admit summed4 CPU budget")
    return dict(host_cpu=host_cpu,guest_cpu=spare[0],reserve_cpus=spare[1:3],
        host_cpu_budget=1,guest_cpu_budget=1,reserve_cpu_budget=2,
        common_finite_capacity=min(shared) if shared else None,future_external_guarantee=False)
def daemon_view():
    files=[Path("/run/docker.pid"),Path("/var/run/docker.pid")]
    file=next((p for p in files if p.is_file()),None);require(file is not None,"actual dockerd PID file required")
    pid=int(file.read_text().strip());require(pid>1,"actual daemon PID")
    proc=frozen().gate_process(pid)
    require(proc["argv"] and Path(proc["argv"][0]).name=="dockerd","PID file does not identify actual Docker daemon")
    return cpu_view(pid)
def protected_map(protected):
    return {str(card):[{k:v for k,v in row.items() if k not in ("physical","chip")}
            for row in protected if row["physical"]==card] for card in range(4)}
def started(proof):
    ticks=os.sysconf("SC_CLK_TCK")
    lines=[l for l in Path("/proc/stat").read_text().splitlines() if l.startswith("btime ")]
    require(len(lines)==1 and ticks>0,"actual boot-time/tick identity")
    boot=int(lines[0].split()[1])
    return {**proof,"boot_unix_seconds":boot,"clock_ticks_per_second":ticks,
        "started_utc":datetime.fromtimestamp(boot+proof["start_ticks"]/ticks,timezone.utc).isoformat()}
def device_fd_holders():
    # A device declaration is not occupation. An actual open physical6 FD is
    # separate UDA/context-conflict evidence; manager/control FDs do not count.
    device=Path("/dev/davinci6").stat()
    require(stat.S_ISCHR(device.st_mode),"actual physical6 character device")
    found=[];pids=[p for p in Path("/proc").iterdir() if p.name.isdigit()]
    require(len(pids)<=16384,"bounded actual PID inventory")
    for proc in pids:
        try:
            fds=list((proc/"fd").iterdir());require(len(fds)<=16384,"bounded actual FD inventory")
            hit=False
            for fd in fds:
                try:target=os.readlink(fd)
                except FileNotFoundError:continue
                if re.fullmatch(r"/dev/davinci[0-9]+",target):
                    try:opened=fd.stat()
                    except FileNotFoundError:continue
                    if stat.S_ISCHR(opened.st_mode) and opened.st_rdev==device.st_rdev:
                        hit=True;break
            if hit:found.append(started(frozen().gate_process(int(proc.name))))
        except (FileNotFoundError,ProcessLookupError):continue
        except PermissionError:raise ValueError("physical6 FD ownership unreadable; no fabricated UDA clearance")
    return found

class Controller:
    def __init__(self,a):
        self.a=a;self.out=a.output_dir;self.h=frozen()
        self.cid=None;self.name="kvbuffer-h8-"+self.out.name;self.seq=0;self.primary=None
        self.secondary=[];self.child=None;self.child_label=None;self.child_started=None
        self.child_request=None;self.canary_proofs=[];self.gate_proofs=[];self.protected=None
        self.created_monotonic=time.monotonic();self.deadline=self.created_monotonic+PHASE_SECONDS
        self.cleanup_deadline=None;self.cpu=None;self.expected=None;self.source=None
    def remaining(self,cleanup=False,cap=30):
        if cleanup:
            if self.cleanup_deadline is None:self.cleanup_deadline=time.monotonic()+CLEANUP_SECONDS
            value=self.cleanup_deadline-time.monotonic()
        else:
            value=min(self.deadline-time.monotonic(),(CUTOFF-utc()).total_seconds())-CLEANUP_SECONDS
        require(value>0,"fixed phase/cutoff and cleanup reserve exhausted")
        return min(cap,value)
    def wrapper(self,argv):
        return [PRLIMIT,"--as=unlimited","--",*argv] if argv[0]==DOCKER else list(argv)
    def rss(self):
        own=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        child=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
        require(own+child<=HOST_MEM//1024,"actual host+CLI cumulative peak RSS exceeds256MiB")
        return dict(host_peak_rss_kib=own,child_peak_rss_kib=child,aggregate_peak_rss_kib=own+child)
    def call(self,label,argv,cap=30,cleanup=False):
        requested=list(argv);wrapped=self.wrapper(requested)
        try:result=self.h.run(wrapped,self.remaining(cleanup,cap))
        except BaseException as error:
            result=dict(argv=wrapped,requested_argv=requested,exit_code=None,
                error=repr(error),observed_utc=utc().isoformat())
            receipt=write(self.out/(label+"-"+str(time.time_ns())+".json"),result)
            raise RuntimeError("command failure retained: "+str(receipt)) from error
        result.update(requested_argv=requested)
        receipt=write(self.out/(label+"-"+str(time.time_ns())+".json"),result)
        self.rss()
        require(result["exit_code"]==0,"actual command failed; retained "+str(receipt))
        return result,receipt
    def mounts(self,artifacts):
        mounts={str(ROOT):(str(ROOT),False),
          "/usr/local/Ascend/driver":("/usr/local/Ascend/driver",False),
          str(self.out):(str(self.out),False),"/kvbuffer-results":(str(self.out),True)}
        for r in artifacts.values():mounts[r["path"]]=(r["path"],False)
        return mounts
    def inspect(self,cleanup=False):
        raw,receipt=self.call("inspect",[DOCKER,"inspect",self.cid],cleanup=cleanup)
        rows=json.loads(raw["stdout"]);require(len(rows)==1,"single exact owned CID inspect")
        value=rows[0];validate_inspect(value,self.expected)
        # OOM/exit are outcome checks, not a reason to lose exact safe stop authority.
        return value,receipt
    def resources(self,initial=False):
        memory={l.split(":")[0]:int(l.split()[1])*1024 for l in Path("/proc/meminfo").read_text().splitlines()
           if l.startswith(("MemAvailable:","MemTotal:","Hugetlb:","SwapTotal:","SwapFree:"))}
        require(memory["SwapTotal"]==memory["SwapFree"],"active swap is not admitted")
        require(memory["MemAvailable"]>=RESERVE+HOST_MEM+(MEM if initial else 0),
           "ordinary host RAM floor; HugeTLB never additive")
        disk=shutil.disk_usage(self.out.parent).free
        require(disk>=RESERVE+(WORKSPACE if initial else 0),"ordinary workspace/reserve floor")
        if self.out.exists():
            used=sum(p.stat().st_size for p in self.out.rglob("*") if p.is_file())
            require(used<=WORKSPACE,"owned output allowance exceeded; stop-retain not delete")
        else:used=0
        host=cpu_view(os.getpid());daemon=daemon_view();allocation=cpu_admission(host,daemon)
        if self.cpu is None:self.cpu=allocation
        require(allocation==self.cpu,"effective host/daemon CPU admission changed")
        engine,er=self.call("engine",[DOCKER,"info","--format","{{json .}}"])
        require(json.loads(engine["stdout"])["NCPU"]>=4,"engine CPU inventory contradicts actual admission")
        return dict(memory=memory,disk_free_bytes=disk,output_bytes=used,
            host_cpu=host,daemon_cpu=daemon,cpu_allocation=allocation,engine=er,
            ordinary_floor_bytes=RESERVE+HOST_MEM+(MEM if initial else 0),
            output_allowance_bytes=WORKSPACE,disk_reserve_bytes=RESERVE,
            full_model_floor_unchanged_bytes=72*1024**3,**self.rss())
    def observe(self,label,expected_argv=None,initial=False,cleanup=False):
        raw,sr=self.call("smi",[SMI,"info"],cleanup=cleanup)
        text=raw["stdout"];protected=self.h.protected(text)
        if self.protected is None:self.protected=protected
        record=dict(label=label,observed_utc=raw["observed_utc"],smi=sr,
            npu_smi=text,protected0_3=protected,declared_only_containers=[],actual_compute=[],
            actual_physical6_fd_holders=[])
        # Save raw state before any protection/ownership assertion.
        initial_ref=write(self.out/("observation-raw-"+str(time.time_ns())+".json"),record)
        require(protected==self.protected,"protected0..3 PID/start_ticks/cgroup/argv-hash changed")
        process_rows=self.h.legacy().process_rows(text)
        proofs=[]
        for card in (4,5,6,7):
            rows=[(n,ch,pid) for n,ch,pid in process_rows if n==card]
            if card!=PHYSICAL or self.cid is None:
                self.h.idle_one(text,card);continue
            if not rows:self.h.idle_one(text,card)
            for physical,chip,pid in rows:
                proof=started(self.h.gate_process(pid))
                record["actual_compute"].append(dict(physical=physical,chip=chip,**proof))
                write(self.out/("actual-compute-"+str(time.time_ns())+".json"),
                    dict(physical=physical,chip=chip,stage=label,**proof,smi=sr))
                require(chip==0 and self.cid in proof["cgroup"],"actual foreign physical6 process/UDA conflict")
                require(expected_argv is not None and proof["argv"]==expected_argv,
                    "actual NPU Python PID/argv is not this canary/numerical child")
                require(datetime.fromisoformat(proof["started_utc"])>=self.child_started-timedelta(seconds=1),
                    "actual child kernel start-time predates this dispatch")
                proofs.append(dict(physical=physical,chip=chip,stage=label,**proof,
                    smi=sr,raw_observation=initial_ref,observed_utc=raw["observed_utc"]))
        holders=device_fd_holders();record["actual_physical6_fd_holders"]=holders
        write(self.out/("actual-device-fd-"+str(time.time_ns())+".json"),dict(holders=holders,smi=sr))
        for holder in holders:
            require(self.cid is not None and self.cid in holder["cgroup"],
                    "actual physical6 device FD/UDA ownership conflict")
        running,psr=self.call("running",[DOCKER,"ps","-q","--no-trunc"],cleanup=cleanup)
        for cid in running["stdout"].split():
            r,ir=self.call("declared-container",[DOCKER,"inspect",cid],cleanup=cleanup)
            x=json.loads(r["stdout"])[0]
            declared={d["PathOnHost"] for d in (x["HostConfig"].get("Devices") or [])}
            if declared&{"/dev/davinci"+str(n) for n in (4,5,6,7)}:
                # Declarations alone are recorded, never blocking or stop authority.
                record["declared_only_containers"].append(dict(cid=cid,inspect=ir,devices=sorted(declared)))
        record["resources"]=self.resources(initial)
        record["actual_compute_proofs"]=proofs
        completed=write(self.out/("observation-"+str(time.time_ns())+".json"),record)
        for proof in proofs:proof["complete_observation"]=completed
        return proofs,completed
    def create(self,artifacts,source_ref,source):
        self.expected=dict(cid=None,name=self.name,image=IMAGE,owner=OWNER,source=source_ref,
            host_sha256=sha(__file__),guest_cpu=self.cpu["guest_cpu"],mounts=self.mounts(artifacts))
        require(re.fullmatch("[A-Za-z0-9_-]{1,100}",self.name),"bounded unique container name")
        old,_=self.call("unique-name",[DOCKER,"ps","-a","--filter","name=^/"+self.name+"$","--format","{{.ID}}"])
        require(not old["stdout"].strip(),"exact name already exists; never reuse/retry")
        cmd=create_argv(self.expected)
        for src,rw in self.expected["mounts"].values():require(Path(src).exists(),"actual mount source absent")
        for host in expected_devices():require(Path(host).exists(),"actual authorized device node absent")
        result,created=self.call("create",cmd,cap=60)
        cid=result["stdout"].strip();require(re.fullmatch("[0-9a-f]{64}",cid),"complete created CID")
        self.cid=cid;self.expected["cid"]=cid
        write(self.out/"OWNED.json",dict(schema="kvbp.h8-host-owned/v1",**self.expected,
            create_receipt=created,sources=source))
        x,ir=self.inspect()
        require(not x["State"]["Running"] and x["State"]["Pid"]==0 and not x.get("ExecIDs"),
           "new exact container unexpectedly live")
        self.call("start",[DOCKER,"start",cid],cap=60)
        x,ir=self.inspect()
        require(x["State"]["Running"] and x["State"]["Pid"]>0,"exact owned init not started")
        guest=cpu_view(x["State"]["Pid"])
        require(guest["effective_capacity"]==1 and guest["effective_cpus"]==[self.cpu["guest_cpu"]],
            "actual guest cgroup quota/cpuset differs from declared one CPU")
        write(self.out/"guest-cgroup-cpu.json",guest)
        return ir
    def observed_child(self,label,args,limit):
        requested=self.h.legacy().exec_argv(self.cid,args)
        expected=[PY,"-B",*args]
        so=self.out/(label+".stdout");se=self.out/(label+".stderr")
        proof=[];failure=None
        self.child_started=utc();self.child_label=label;self.child_request=requested
        with so.open("x") as stdout,se.open("x") as stderr:
            try:
                self.child=subprocess.Popen(self.wrapper(requested),stdout=stdout,stderr=stderr,cwd=ROOT)
                end=time.monotonic()+min(limit,self.remaining(cap=PHASE_SECONDS))
                while self.child.poll() is None:
                    require(time.monotonic()<end,"bounded original child timeout; no retry")
                    rows,_=self.observe(label,expected)
                    proof.extend(rows);time.sleep(1)
                rows,_=self.observe(label,expected);proof.extend(rows)
                require(self.child.returncode==0,"actual "+label+" child exit "+str(self.child.returncode))
                require(proof,"no actual physical6 NPU Python PID/argv/start/cgroup proof")
                ids={(p["pid"],p["start_ticks"]) for p in proof}
                require(len(ids)==1,"actual "+label+" process identity drift")
                if label=="matrix":
                    require(not ids&{(p["pid"],p["start_ticks"]) for p in self.canary_proofs},
                        "numerical compute proof must not be borrowed from canary")
                self.rss()
            except BaseException as error:failure=error
        # Failed running child is stopped by exact-owned cleanup, not killed here.
        terminated=self.child is not None and self.child.poll() is not None
        receipt=write(self.out/(label+"-child.json"),dict(requested_argv=requested,
            actual_host_argv=self.wrapper(requested),expected_image_python_argv=expected,
            child_host_pid=self.child.pid if self.child is not None else None,
            child_started_utc=self.child_started.isoformat(),child_termination_observed=terminated,
            exit_code=self.child.returncode if terminated else None,
            stdout_ref=({"path":str(so),"sha256":sha(so)} if terminated else None),
            stderr_ref=({"path":str(se),"sha256":sha(se)} if terminated else None),
            pending_stdout_path=str(so),pending_stderr_path=str(se),
            physical_pid_proofs=proof,primary_error=repr(failure) if failure else None))
        if label=="canary":self.canary_proofs=proof
        if label=="matrix":self.gate_proofs=proof
        if failure is not None:raise failure
        return receipt
    def cleanup(self):
        result=dict(container=self.cid,stopped=False,retained=False,deleted=False,
            errors=[],primary_error=repr(self.primary) if self.primary else None)
        if self.cid is None:return write(self.out/"cleanup.json",result)
        try:
            _,before=self.inspect(cleanup=True);result["before_inspect"]=before
            stopped,sr=self.call("stop-retain",[DOCKER,"stop","--time","15",self.cid],cap=40,cleanup=True)
            result["stop_receipt"]=sr
            x,after=self.inspect(cleanup=True);result["after_inspect"]=after
            require(not x["State"]["Running"] and x["State"]["Pid"]==0 and not x.get("ExecIDs"),
                "exact owned container/process still live")
            result.update(stopped=True,retained=True)
            require(not x["State"].get("OOMKilled",False),"OOM invalidates numerical stage")
            if self.child is not None and self.child.poll() is None:
                self.child.wait(timeout=self.remaining(cleanup=True,cap=20))
            require(self.child is None or self.child.poll() is not None,"foreground Docker CLI termination pending")
            raw,sr=self.call("release-smi",[SMI,"info"],cleanup=True)
            result["release_smi"]=sr
            require(self.h.protected(raw["stdout"])==self.protected,
                "protected0..3 identity changed; retain separate cleanup failure")
            self.h.idle_one(raw["stdout"],PHYSICAL)
        except BaseException as error:
            result["errors"].append(repr(error));self.secondary.append(repr(error))
            # Never discard unresolved exact CID or claim successful retain/release.
        return write(self.out/"cleanup.json",result)

def expected_devices():
    return {"/dev/davinci6":"/dev/davinci0","/dev/davinci_manager":"/dev/davinci_manager",
            "/dev/devmm_svm":"/dev/devmm_svm","/dev/hisi_hdc":"/dev/hisi_hdc"}
def labels(e):
    return {"model-tuning-lab.owner":OWNER,"model-tuning-lab.run":e["name"],
            "model-tuning-lab.source-manifest-sha256":e["source"]["sha256"],
            "model-tuning-lab.controller-sha256":e["host_sha256"]}
def environment():
    return {"ASCEND_RT_VISIBLE_DEVICES":"0","TORCH_DEVICE_BACKEND_AUTOLOAD":"0",
            "PYTHONDONTWRITEBYTECODE":"1","OMP_NUM_THREADS":"1","MKL_NUM_THREADS":"1",
            "OPENBLAS_NUM_THREADS":"1"}
def create_argv(e):
    argv=[DOCKER,"create","--name",e["name"],"--network","none","--cap-drop","ALL",
        "--security-opt","no-new-privileges","--memory",str(MEM),"--memory-swap",str(MEM),
        "--cpus","1","--cpuset-cpus",str(e["guest_cpu"]),"--pids-limit","512",
        "--ipc","private","--shm-size",str(2*1024**3),"--workdir",str(ROOT),
        "--entrypoint","/bin/bash"]
    for k,v in labels(e).items():argv+=["--label",k+"="+v]
    for k,v in environment().items():argv+=["--env",k+"="+v]
    for host,guest in expected_devices().items():argv+=["--device",host+":"+guest+":rwm"]
    for dst,(src,rw) in e["mounts"].items():
        require("," not in src and "," not in dst,"ordinary comma-free exact bind paths")
        argv+=["--mount","type=bind,source="+src+",destination="+dst+("" if rw else ",readonly")]
    return [*argv,IMAGE,"-c","exec /bin/sleep infinity"]
def validate_inspect(x,e):
    require(type(x) is dict and re.fullmatch("[0-9a-f]{64}",e["cid"] or ""),
            "complete exact owned CID required before stop")
    h=x["HostConfig"];cfg=x["Config"]
    require(x["Id"]==e["cid"] and x["Name"]=="/"+e["name"] and x["Image"]==IMAGE and
        cfg["Image"]==IMAGE and cfg["Entrypoint"]==["/bin/bash"] and
        cfg["Cmd"]==["-c","exec /bin/sleep infinity"] and cfg["WorkingDir"]==str(ROOT),
        "full exact CID/image/init identity")
    actual_labels=cfg.get("Labels") or {}
    require(all(actual_labels.get(k)==v for k,v in labels(e).items()),"owned source/controller labels")
    env=cfg.get("Env") or []
    require(all(env.count(k+"="+v)==1 and sum(z.startswith(k+"=") for z in env)==1
                for k,v in environment().items()),"exact nonduplicated runtime environment")
    require(h["Privileged"] is False and h["Memory"]==MEM and h["MemorySwap"]==MEM and
        h["NanoCpus"]==10**9 and h["CpusetCpus"]==str(e["guest_cpu"]) and
        h["NetworkMode"]=="none" and h["IpcMode"]=="private" and h["ShmSize"]==2*1024**3 and
        h["PidsLimit"]==512 and not h.get("DeviceRequests") and not h.get("DeviceCgroupRules") and
        set(h.get("CapDrop") or [])=={"ALL"} and
        set(h.get("SecurityOpt") or [])=={"no-new-privileges"},
        "exact owned isolation/resources; declarations not foreign occupation")
    devices=h["Devices"]
    require(len(devices)==4 and {d["PathOnHost"]:d["PathInContainer"] for d in devices}==
        expected_devices() and all(d["CgroupPermissions"]=="rwm" for d in devices),
        "single physical6 to logical0 and exact control-node map")
    mounts=x["Mounts"];want={dst:(src,bool(rw)) for dst,(src,rw) in e["mounts"].items()}
    require(len(mounts)==len(want) and all(m["Type"]=="bind" for m in mounts) and
        {m["Destination"]:(m["Source"],m["RW"]) for m in mounts}==want,
        "complete exact immutable inputs/new output mounts")

def explicit_flags(a):
    return ["--source-manifest",str(a.source_manifest),"--source-manifest-sha256",a.source_manifest_sha256,
        "--library",str(a.library),"--library-sha256",a.library_sha256,
        "--build-receipt",str(a.build_receipt),"--build-receipt-sha256",a.build_receipt_sha256,
        "--meta-receipt",str(a.meta_receipt),"--meta-receipt-sha256",a.meta_receipt_sha256]
def numerical_argv(a,identity):
    return [str(BASE/"run.py"),"--execute","--batch","16","--physical-device","6",
        *explicit_flags(a),"--identity",str(identity),"--output-dir","/kvbuffer-results/gate"]
def inside_canary(a):
    # Only the MAIN-owned container dispatch reaches this lazy NPU import.
    c,sr,m,s,artifacts,checked,p=source_inputs(a)
    require(os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0" and
        os.environ.get("PYTHONDONTWRITEBYTECODE")=="1","canary logical0/no bytecode")
    pins=c.legacy().NATIVE_PINS
    require({n:sha(n) for n in pins}==pins,"actual image native source pins")
    cg=c.legacy().cgroup_limit()
    import torch,torch_npu
    from vllm_ascend.utils import enable_custom_op
    from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton
    torch_npu.npu.set_compile_mode(jit_compile=False);torch.npu.set_device(0)
    require(torch.npu.device_count()==1 and torch.npu.current_device()==0,"actual canary logical0 singleton")
    require(enable_custom_op(),"actual canary native bootstrap")
    init_device_properties_triton()
    x=torch.tensor([1.,2.,3.],device="npu",dtype=torch.float32)
    y=x*2;torch.npu.synchronize()
    require(y.cpu().tolist()==[2.,4.,6.],"fresh tiny canary actual arithmetic")
    mapped=[l.split()[-1] for l in Path("/proc/self/maps").read_text().splitlines()
        if len(l.split())>=6 and l.split()[-1]==NATIVE]
    require(mapped and sha(NATIVE)==NATIVE_SHA,"same image actually mapped native library")
    _,after=c.source_admission(sr);require(s==after,"actual canary current84 source before/after")
    r=write(Path("/kvbuffer-results/canary.json"),dict(schema="kvbp.h8-host-canary/v1",
        fresh_canary_passed=True,candidate_numerical_verified=False,serving_ready=False,
        pid=os.getpid(),image_id=IMAGE,source_manifest=sr,sources_before=s,sources_after=after,
        artifact_refs=artifacts,protocol=p,memory_cgroup_bytes=MEM,cgroup=cg,
        logical_device_count=1,logical_device=0,native_library={"path":NATIVE,"sha256":NATIVE_SHA},
        script_sha256=sha(__file__),created_utc=utc().isoformat()))
    print(json.dumps({"actual_canary":r,"candidate_numerical_verified":False}),flush=True)
    # This is only an observation window, never a timing sample.
    time.sleep(30)

def fresh_output(path):
    require(path is not None and path.is_absolute() and ".." not in path.parts,
            "explicit absolute new output leaf")
    require(Path("/cache/cch") in path.parents and path.parent.is_dir() and
        path.parent.resolve()==path.parent and not path.exists() and not path.is_symlink(),
        "new nonsymlink leaf beneath existing /cache/cch parent; no overwrite/reuse")
    path.mkdir(exist_ok=False)
def execute(a):
    c,sr,m,s,artifacts,checked,protocol=source_inputs(a)
    require((CUTOFF-utc()).total_seconds()>=PHASE_SECONDS,
            "whole fixed5400s phase includes90s cleanup before fixed cutoff")
    capacity=cpu_view(os.getpid());os.sched_setaffinity(0,{min(capacity["effective_cpus"])})
    soft,hard=resource.getrlimit(resource.RLIMIT_AS)
    require(hard==resource.RLIM_INFINITY,"host finite hard AS would prevent Docker-only child restoration")
    resource.setrlimit(resource.RLIMIT_AS,(HOST_MEM,hard))
    fresh_output(a.output_dir);ctl=Controller(a);primary=None;numeric=None;completeness=None
    initial=None;canary=None;identity_ref=None;gate_child=None;after=None;cleanup_ref=None
    try:
        _,initial=ctl.observe("preflight",initial=True)
        plan=write(ctl.out/"PLAN.json",dict(schema="kvbp.h8-host-plan/v1",default_enabled=False,
            MAIN_only_dispatch=True,source_manifest=sr,sources=s,artifact_refs=artifacts,
            artifact_admission=checked,protocol=protocol,controller_sha256=sha(__file__),
            frozen_host={"path":str(FROZEN),"sha256":FROZEN_SHA},
            phase_seconds=PHASE_SECONDS,cleanup_seconds=CLEANUP_SECONDS,cutoff_utc=CUTOFF.isoformat(),
            memory_guest_bytes=MEM,memory_host_bytes=HOST_MEM,memory_reserve_bytes=RESERVE,
            ordinary_ram_floor_bytes=MEM+HOST_MEM+RESERVE,
            cpu_allocation=ctl.cpu,preflight=initial))
        inspect_ref=ctl.create(artifacts,sr,s)
        cc=ctl.observed_child("canary",[str(BASE/"host_run.py"),"--inside-canary",
            *explicit_flags(a)],120)
        canary=ref(ctl.out/"canary.json",sha(ctl.out/"canary.json"))
        cv=json.loads(Path(canary["path"]).read_bytes())
        require(cv["schema"]=="kvbp.h8-host-canary/v1" and cv["fresh_canary_passed"] is True and
            cv["candidate_numerical_verified"] is False and cv["sources_before"]==s and
            cv["sources_after"]==s and cv["source_manifest"]==sr and cv["artifact_refs"]==artifacts and
            cv["protocol"]==protocol and cv["native_library"]=={"path":NATIVE,"sha256":NATIVE_SHA} and
            cv["memory_cgroup_bytes"]==MEM and cv["script_sha256"]==sha(__file__) and
            cv["pid"]==ctl.canary_proofs[-1]["namespace_pids"][-1],
            "fresh actual canary/current84/native/PID proof")
        _,inspect_ref=ctl.inspect()
        identity=dict(schema="kvbp.short-horizon-launch-identity/v4",image_id=IMAGE,
            protocol=protocol,physical_devices=[PHYSICAL],logical_to_physical={"0":PHYSICAL},
            fresh_idle_verified=True,nonprivileged=True,source_canary_passed=True,
            memory_cgroup_bytes=MEM,source_manifest=sr,sources=s,artifact_refs=artifacts,
            preflight_utc=utc().isoformat(),evidence={"plan":plan,"preflight":initial,
            "canary_child":cc,"canary":canary,"actual_owned_inspect":inspect_ref,
            "owned":ref(ctl.out/"OWNED.json",sha(ctl.out/"OWNED.json")),
            "actual_guest_cpu":ref(ctl.out/"guest-cgroup-cpu.json",sha(ctl.out/"guest-cgroup-cpu.json"))})
        c.validate_identity(identity,BATCH,PHYSICAL,sr,m,s,artifacts)
        identity_ref=write(ctl.out/"identity.json",identity)
        gate_child=ctl.observed_child("matrix",numerical_argv(a,ctl.out/"identity.json"),ctl.remaining(cap=PHASE_SECONDS))
        numeric=ref(ctl.out/"gate/report.json",sha(ctl.out/"gate/report.json"))
        report=json.loads(Path(numeric["path"]).read_bytes())
        completeness=c.validate_cases(report,BATCH)
        require(completeness["changing_feedback_steps"]==640 and report["sources_before"]==s and
            report["sources_after"]==s and report["source_manifest"]==sr and
            report["artifact_refs"]==artifacts and report["launch_identity"]==identity and
            report["launch_identity_sha256"]==identity_ref["sha256"] and
            report["script_sha256"]==s[str(BASE/"run.py")] and report["protocol"]==protocol and
            report["loaded_libraries"].get(str(a.library))==artifacts["library"]["sha256"] and
            report["loaded_libraries"].get(NATIVE)==NATIVE_SHA,
            "actual new640-step report/script/output/artifact/source/identity linkage")
        _,_,_,after,after_artifacts,_,_=source_inputs(a)
        require(after==s and after_artifacts==artifacts,"actual post-numerical source/artifact drift")
    except BaseException as error:
        primary=error;ctl.primary=error
    finally:
        try:cleanup_ref=ctl.cleanup()
        except BaseException as error:
            ctl.secondary.append(repr(error))
            # No cleanup failure is allowed to replace the original primary.
        try:
            if ctl.child is not None:
                done=ctl.child.poll() is not None
                write(ctl.out/"foreground-final.json",dict(stage=ctl.child_label,
                    requested_argv=ctl.child_request,host_pid=ctl.child.pid,terminated=done,
                    exit_code=ctl.child.returncode if done else None,
                    stdout_ref=ref(ctl.out/(ctl.child_label+".stdout"),sha(ctl.out/(ctl.child_label+".stdout"))) if done else None,
                    stderr_ref=ref(ctl.out/(ctl.child_label+".stderr"),sha(ctl.out/(ctl.child_label+".stderr"))) if done else None))
        except BaseException as error:ctl.secondary.append(repr(error))
        success=primary is None and not ctl.secondary and cleanup_ref is not None and numeric is not None
        result=dict(schema="kvbp.h8-host-result/v1",status="kernel_numerics_checked" if success else "failed",
            default_enabled=False,npu_executed=bool(ctl.canary_proofs or ctl.gate_proofs),
            numerical_report_checked=success,MAIN_original_operation_authority_verified=False,
            serving_ready=False,matched_e2e_verified=False,task_accuracy_verified=False,
            sources_before=s,sources_after=after,source_manifest=sr,artifact_refs=artifacts,
            actual_report=numeric,report_completeness=completeness,identity=identity_ref,
            canary=canary,actual_numerical_child=gate_child,cleanup=cleanup_ref,
            exact_container=ctl.cid,container_deleted=False,cutoff_utc=CUTOFF.isoformat(),
            phase_elapsed_seconds=time.monotonic()-ctl.created_monotonic,
            primary_error=repr(primary) if primary else None,secondary_errors=ctl.secondary,
            protected0_3=protected_map(ctl.protected or []),
            canary_process_proofs=ctl.canary_proofs,numerical_process_proofs=ctl.gate_proofs)
        final=write(ctl.out/"RESULT.json",result)
        print("MAIN_KVBUFFER_H8_HOST_V1_CHILD "+json.dumps({"result":final,"status":result["status"],
            "MAIN_original_operation_authority_verified":False}),flush=True)
    if primary is not None:raise primary
    require(not ctl.secondary,"secondary exact stop-retain/release failure: "+repr(ctl.secondary))

def parser():
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group()
    for flag in ("--execute","--inside-canary","--source-audit-only"):group.add_argument(flag,action="store_true")
    for name in ("source-manifest","library","build-receipt","meta-receipt"):
        p.add_argument("--"+name,type=Path);p.add_argument("--"+name+"-sha256")
    p.add_argument("--output-dir",type=Path)
    return p
def main(argv=None):
    a=parser().parse_args(argv)
    if not (a.execute or a.inside_canary or a.source_audit_only):
        print(json.dumps(dict(default_enabled=False,npu_executed=False,serving_ready=False,
            batch=BATCH,physical_device=PHYSICAL,materialization_interval=8,storage_log_capacity=16,
            actual_source_build_meta_numerics_and_MAIN_operation_pending=True)))
        return 0
    require(all(getattr(a,n) is not None for n in ("source_manifest","source_manifest_sha256",
        "library","library_sha256","build_receipt","build_receipt_sha256","meta_receipt","meta_receipt_sha256")),
        "explicit source/library/build/Meta paths and SHA256 required")
    if a.inside_canary:inside_canary(a)
    elif a.source_audit_only:
        _,sr,_,s,ar,checked,p=source_inputs(a)
        print(json.dumps(dict(source_audit_passed=True,source_manifest=sr,sources=s,
            artifact_refs=ar,artifact_admission=checked,protocol=p,npu_executed=False,serving_ready=False)))
    else:execute(a)
    return 0
if __name__=="__main__":sys.exit(main())

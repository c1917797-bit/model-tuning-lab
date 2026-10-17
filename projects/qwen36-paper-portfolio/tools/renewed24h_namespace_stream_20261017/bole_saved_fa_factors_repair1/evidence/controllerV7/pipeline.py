"""MAIN-only complete numerical->paired service->consumer->fixed1024 entry.

Default prints source-bound plan: NO Docker/HTTP/NPU/model execution.
--execute is an explicit serial MAIN admission, never a preparation action.
Exact owned CIDs are stopped and retained, never rm. First failure is terminal.
"""
import argparse,concurrent.futures as cf,hashlib,importlib.util,json,os,resource,shutil,subprocess,time,uuid
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import urlopen
from qwen36_deltalog_mixed import contract as c
import service_checks as sc
import authority as au
import cpu_capacity as cpu
import native_preflight as np
from consume_model import collect

ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab")
HOST=ROOT/"projects/kvbuffer-parallel-ascend/tools/full_matrix_host_v2/host.py"
HOST_SHA="ab0296c698df00c9c3b2ce377601f6d6723adde6efb4a9e65407beca51ba5f86"
OLD=ROOT/"projects/kvbuffer-parallel-ascend/tools/saved_step_native_order_v2/host_run.py"
OLD_SHA="86c1ca7f59c6ad5b2b4d5efb155394455a12376cf368e06f9e2e13d39b7192fc"
DOCKER="/usr/bin/docker";SMI="/usr/local/sbin/npu-smi";PY="/usr/local/python3.12.13/bin/python3"
OWNER="qwen36-deltalog-mixed-v7-MAIN"
PRLIMIT="/usr/bin/prlimit"
CUTOFF=datetime.fromisoformat("2026-10-09T11:17:31+00:00")
KV_CUTOFF="2026-10-08T08:29:54Z" # separate original clock, never reset by this CLI
RESERVE=8*1024**3;HOST_RESERVE=256*1024**2
SERVICE_OPTIONS=("--model","--served-model-name","--tensor-parallel-size","--dtype",
 "--mamba-cache-mode","--no-enable-prefix-caching","--enable-prefix-caching","--enable-chunked-prefill","--enable-prompt-tokens-details",
 "--max-model-len","--max-num-seqs","--max-num-batched-tokens","--no-async-scheduling",
 "--enforce-eager","--port","--host")
def require(value,reason):
    if not value:raise ValueError(reason)
def save(path,value):
    # Failure/cleanup observations are append-only separate files, not overwrite.
    with Path(path).open("x") as out:out.write(json.dumps(value,indent=2,allow_nan=False)+"\n")
def load_host():
    c.require_digest(HOST,HOST_SHA);c.require_digest(OLD,OLD_SHA)
    spec=importlib.util.spec_from_file_location("_deltalog_MAIN_frozen_host",HOST)
    h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
    h.legacy() # verifies and imports its pinned real dependency, no KV execution
    return h
def service_args(stage=None):
    args=[PY,"-B","-m","vllm.entrypoints.openai.api_server",
        "--model","/model","--served-model-name","qwen36-deltalog-pair",
        "--tensor-parallel-size","4","--dtype","bfloat16",
        "--mamba-cache-mode","none","--no-enable-prefix-caching","--enable-chunked-prefill",
        "--max-model-len","40960","--max-num-seqs","16",
        "--max-num-batched-tokens","40960","--gpu-memory-utilization","0.9","--no-async-scheduling",
        "--enforce-eager","--port","8000","--host","0.0.0.0"]
    if stage=="qualify":
        args[args.index("--mamba-cache-mode")+1]="align"
        args[args.index("--no-enable-prefix-caching")]="--enable-prefix-caching"
        args.append("--enable-prompt-tokens-details")
    return args
def source_preflight(a,root):
    global CUTOFF
    proof=au.validate(a.authority,a.authority_sha256)
    CUTOFF=datetime.fromtimestamp(proof["cutoff_epoch"],timezone.utc)
    a.current_authority=proof
    require(not a.run_root.exists(),"owned output root must be new; no overwrite/reuse")
    require(a.run_root.parent.is_dir(),"existing explicit result parent required")
    require(a.run_root.resolve().is_relative_to(Path("/cache/cch")),"results restricted to /cache/cch")
    c.require_digest(a.library,c.DECODE_SHA)
    c.require_digest(a.model_dir/"config.json",c.CONFIG_SHA)
    c.require_digest(a.legacy_plugin/"qwen36_deltalog_plugin/patch.py",c.LEGACY_SHA)
    c.require_digest(a.consumer_dir/"deltalog_candidate_npu_probe.py",
        "a0ea94634efc732f409a3f09cc7faf8fa2db07b8ab4da92a73352301371e9ef2")
    load_host()
    if a.resume_numeric_receipt:validate_resume(a,root)
    require(root.resolve()!=a.run_root.resolve(),"source/result mount collision")
    require(root.resolve()!=a.legacy_plugin.resolve(),"independent default-off legacy mount")
    require(1024<=a.port<=65535,"explicit unprivileged loopback port")
    return dict(schema="qwen36-deltalog-complete-plan/v7",source_digest=c.package_digest(root),
        image=c.IMAGE,MAIN_execute_required=True,executed=False,
        current_authority=a.current_authority,cutoff_utc=CUTOFF.isoformat(),
        historical_portfolio_cutoff="2026-10-09T11:17:31Z",kv_original_cutoff=KV_CUTOFF,
        physical_numeric=a.physical_device,physical_model=[4,5,6,7],protected=[0,1,2,3],
        source_pins=dict(host=HOST_SHA,host_dependency=OLD_SHA,library=c.DECODE_SHA,config=c.CONFIG_SHA),
        stages=(["actual-no-device-dlopen-schema-meta"] if a.stop_after_native else ["actual-no-device-dlopen-schema-meta"]+(["numeric160-and-actual-cli-help"] if a.stop_after_numerics else
            (["strict-original-numeric-provenance"] if a.resume_numeric_receipt else ["numeric160-and-actual-cli-help"])+
            ["dense-PDCoff-replay2+8/mixed/fixed1024","candidate-PDCon-cache-copy-qualification",
             "candidate-PDCoff-real-opt-in/replay2+8/mixed/fixed1024","strict-model-consumer"])),
        finaltasks2048=dict(status="pending",reason="MAIN official task CLI identity not frozen; no new scorer"),
        final_acceptance=False,stage_aware_mode=("native-only" if a.stop_after_native else "numeric-only" if a.stop_after_numerics else "resume" if a.resume_numeric_receipt else "full"),
        required_initial_memavailable_bytes=(16 if a.stop_after_numerics or a.stop_after_native else 72)*1024**3+HOST_RESERVE,
        resume_numeric_receipt=str(a.resume_numeric_receipt) if a.resume_numeric_receipt else None,max_MAIN_lease_seconds=a.lease_seconds,cleanup_reserve_seconds=180,serving_graph_scope="both-enforce-eager; numerical NPUGraph separate",
        mounts=dict(packet_ro=str(root),legacy_ro=str(a.legacy_plugin),library_ro=str(a.library),
            consumer_ro=str(a.consumer_dir),driver_ro="/usr/local/Ascend/driver",
            numeric_config_ro=str(a.model_dir/"config.json"),model_ro=(None if a.stop_after_numerics or a.stop_after_native else str(a.model_dir)),
            results_rw=str(a.run_root)),
        resource_bytes=dict(native_limit=8*1024**3,sequential_stages=True,numeric_limit=8*1024**3,model_limit=64*1024**3,
            reserve=RESERVE,host_reserve=HOST_RESERVE,numeric_floor=16*1024**3+HOST_RESERVE,
            model_floor=72*1024**3+HOST_RESERVE,swap_addition=0,hugetlb_addition=0),
        cleanup=dict(exact_owned_cid_only=True,stop=True,retain=True,rm_authorized=False),
        service_argv=service_args(),cache_qualification_argv=service_args("qualify"),screen_protocol=dict(input_tokens=32768,prefix_tokens=16384,
            output_tokens=1024,requests=40,concurrency=16,warmup_requests=2,PDC=False,
            graph_scope="both-enforce-eager; profile FULL_DECODE_ONLY is a separate diagnostic",
            async_scope="both-no-async; runtime copy bridge rejects async"))
def check_inspect(x,cid,stage,output,root,a,allow_oom=False):
    require(x["Id"]==cid and len(cid)==64 and x["Image"]==c.IMAGE,"exact CID/image")
    require(x["Config"].get("Labels",{}).get("qwen36.owner")==OWNER,"exact ownership label")
    require(x["Config"].get("Labels",{}).get("qwen36.stage")==stage,"exact stage label")
    require(not x.get("ExecIDs"),"no extraneous live container exec")
    hc=x["HostConfig"];limit=(8 if stage in ("numeric","native") else 64)*1024**3
    require(hc["Memory"]==limit and hc["MemorySwap"]==limit,"bounded RAM; no swap extension")
    require(hc["NanoCpus"]==10**9 and hc["IpcMode"]=="private","one CPU/private IPC")
    require(hc["ShmSize"]==2*1024**3 and hc["PidsLimit"]==512,"SHM/PID bounds")
    require(not hc["Privileged"] and "ALL" in hc.get("CapDrop",[]),"no privileges")
    require(any("no-new-privileges" in s for s in hc.get("SecurityOpt",[])),"no new privileges")
    require(hc["NetworkMode"]==("none" if stage in ("numeric","native") else "bridge"),"scoped network")
    expected={
      "/deltalog-mixed-plugin":(str(root.resolve()),False),
      "/legacy-deltalog-plugin":(str(a.legacy_plugin.resolve()),False),
      "/candidate-library.so":(str(a.library.resolve()),False),
      "/model-consumers":(str(a.consumer_dir.resolve()),False),
      "/usr/local/Ascend/driver":("/usr/local/Ascend/driver",False),
      "/deltalog-results":(str(output.resolve()),True)}
    expected["/model-config.json" if stage in ("numeric","native") else "/model"]=(
      str((a.model_dir/"config.json" if stage in ("numeric","native") else a.model_dir).resolve()),False)
    if stage in ("candidate","qualify"):expected["/numeric-receipt.json"]=(str(a.numeric_receipt_path.resolve()),False)
    mounts={m["Destination"]:(m["Source"],m["RW"]) for m in x["Mounts"]}
    require(mounts==expected,"only exact non-overwriting mounts")
    cards=[] if stage=="native" else [a.physical_device] if stage=="numeric" else [4,5,6,7]
    devices={(d["PathOnHost"],d["PathInContainer"]) for d in hc.get("Devices") or []}
    required={(f"/dev/davinci{p}",f"/dev/davinci{i}") for i,p in enumerate(cards)}
    if stage!="native":required|={(p,p) for p in ("/dev/davinci_manager","/dev/devmm_svm","/dev/hisi_hdc")}
    require(not hc.get("DeviceRequests") and not hc.get("DeviceCgroupRules"),"no unaccounted device requests/rules")
    require(devices==required,"only physical4..7 mapped to logical0..; exact control devices")
    if not allow_oom:require(not x["State"].get("OOMKilled",False),"container OOM is a failed run")
    if stage not in ("numeric","native"):
        bindings=hc["PortBindings"]
        require(bindings=={"8000/tcp":[{"HostIp":"127.0.0.1","HostPort":str(a.port)}]},"only loopback service")
    if stage=="native":
        require(not hc.get("PortBindings"),"no native-preflight host ports")
        require(x["Config"]["Cmd"]==["/bin/bash","-c",'source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"',
            "deltalog-pipeline",PY,"-B","/deltalog-mixed-plugin/native_preflight.py","--produce","/deltalog-results/native-meta.json"],
            "actual no-device producer command")
        env=dict(item.split("=",1) for item in x["Config"]["Env"])
        require(env.get("TORCH_DEVICE_BACKEND_AUTOLOAD")=="0" and env.get("ASCEND_RT_VISIBLE_DEVICES")=="" and
            env.get("QWEN36_DELTALOG_ENABLE")=="0" and env.get("QWEN36_DELTALOG_MIXED_ENABLE")=="0",
            "actual no-device/default-OFF environment")
    return x
class Lane:
    def __init__(self,a,root):
        self.a=a;self.root=root;self.h=load_host();self.baseline=None;self.seq=0
        self.active=None;self.cards=[];self.output=None;self.stage=None;self.pid_proofs={};self.secondary=[]
        self.lease_deadline=time.monotonic()+a.lease_seconds
    def run(self,argv,timeout=60):
        # Go reserves virtual address arenas; do not confuse VAS with ordinary RAM.
        # No threaded preexec_fn, shell, privilege or Docker-daemon limits change.
        requested=list(argv)
        wrapper=[PRLIMIT,"--as=unlimited","--"]+requested if requested[0]==DOCKER else requested
        result=self.h.run(wrapper,timeout)
        host=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        child=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
        result.update(requested_argv=requested,host_peak_rss_kib=host,child_peak_rss_kib=child,
            aggregate_peak_rss_kib=host+child,host_RLIMIT_AS=resource.getrlimit(resource.RLIMIT_AS))
        require(host+child<=HOST_RESERVE//1024,"aggregate actual host+child peak RSS exceeds256MiB")
        return result
    def call(self,argv,timeout=60,ok=True):
        remaining=min((CUTOFF-datetime.now(timezone.utc)).total_seconds(),self.lease_deadline-time.monotonic())-180
        require(remaining>0,"new48h authority cutoff/cleanup reserve exhausted")
        result=self.run(argv,timeout=min(timeout,max(1,remaining)))
        if ok:require(result["exit_code"]==0,"command failed: "+json.dumps(result))
        return result
    def inspect(self,cid,cleanup=False):
        r=self.run([DOCKER,"inspect",cid],30) if cleanup else self.call([DOCKER,"inspect",cid])
        require(r["exit_code"]==0,"exact CID inspection failed")
        rows=json.loads(r["stdout"]);require(len(rows)==1,"single exact CID inspection")
        x=check_inspect(rows[0],cid,self.stage,self.output,self.root,self.a,allow_oom=cleanup)
        return r,x
    def cpu_observe(self,stage):
        memory={}
        for line in Path("/proc/meminfo").read_text().splitlines():
            k,v=line.split(":",1);memory[k]=int(v.split()[0])*1024
        require(memory["SwapTotal"]==memory["SwapFree"],"swap-active run rejected")
        floor=RESERVE+HOST_RESERVE+(0 if self.active else ((64 if stage=="model" else 8)*1024**3))
        require(memory["MemAvailable"]>=floor,"fresh ordinary MemAvailable floor; HugeTLB not additive")
        free=shutil.disk_usage(self.a.run_root.parent).free
        require(free>=8*1024**3,"unchanged disk reserve")
        engine_receipt=self.call([DOCKER,"info","--format","{{json .}}"])
        engine_info=json.loads(engine_receipt["stdout"])
        pid_receipt=self.call(["/usr/bin/systemctl","show","docker.service","--property=MainPID","--value"])
        pid=int(pid_receipt["stdout"].strip());require(pid>0,"actual dockerd MainPID")
        identity=self.h.process_identity(pid)
        argv=(Path("/proc")/str(pid)/"cmdline").read_bytes().split(b"\0")
        require(argv and Path(os.fsdecode(argv[0])).name=="dockerd","observed engine process identity")
        host=cpu.capacity(os.getpid(),getattr(self.a,"host_original_affinity",os.sched_getaffinity(0)))
        engine=cpu.capacity(pid)
        effective=cpu.consume(host,engine,engine_info)
        # Revalidate process identity after reading cgroups to reject PID reuse.
        require(self.h.process_identity(pid)==identity,"engine process changed during capacity read")
        return dict(schema="qwen36-deltalog-live-cpu-resources/v7",
            observed_utc=datetime.now(timezone.utc).isoformat(),meminfo_bytes=memory,
            ordinary_floor_bytes=floor,disk_free_bytes=free,effective_cpu=effective,
            actual_engine_command=engine_receipt,actual_engine_pid_command=pid_receipt,
            engine_identity=identity,host_affinity_current=sorted(os.sched_getaffinity(0)),
            host_inherited_affinity=sorted(getattr(self.a,"host_original_affinity",os.sched_getaffinity(0))))
    def observe(self,stage,require_idle=False,need_process=False):
        smi=self.call([SMI,"info"],30);raw=smi["stdout"]
        protected=self.h.protected(raw)
        if self.baseline is None:self.baseline=protected
        require(protected==self.baseline,"protected0..3 PID/start_ticks/cgroup/argv identity changed")
        rows=self.h.legacy().process_rows(raw);proof=[]
        for card in (4,5,6,7):
            owned=[pid for n,ch,pid in rows if n==card]
            if require_idle or card not in self.cards:self.h.idle_one(raw,card)
            for pid in owned:
                p=self.h.gate_process(pid)
                require(self.active and self.active in p["cgroup"],"foreign physical4..7 process/cgroup")
                require(any("python" in s or "vllm" in s for s in p["argv"]),"actual numerical/model process argv")
                proof.append(dict(physical=card,**p));self.pid_proofs[(card,pid)]=p
        if need_process:
            require({p["physical"] for p in proof}==set(self.cards),"actual per-card owned service process evidence")
        cpu_record=self.cpu_observe(stage)
        # Device declarations alone never prove allocation/compute or reserve a card.
        # Actual fresh SMI PID/cgroup/HBM above remains the fail-closed authority.
        running=self.call([DOCKER,"ps","-q","--no-trunc"])
        lane_containers=[]
        for cid in running["stdout"].split():
            r=self.call([DOCKER,"inspect",cid]);x=json.loads(r["stdout"])[0]
            used={d["PathOnHost"] for d in x["HostConfig"].get("Devices") or []}
            if used & {f"/dev/davinci{n}" for n in (4,5,6,7)}:
                lane_containers.append(dict(cid=cid,name=x["Name"],declared_devices=sorted(used),
                    owned=cid==self.active,actual_state=x["State"]))
        record=dict(schema="qwen36-deltalog-live-observation/v4",observed_utc=datetime.now(timezone.utc).isoformat(),
            source_handles=[str(HOST),str(OLD)],npu_smi=smi,protected=protected,
            owned_process_proofs=proof,active=self.active,lane_containers=lane_containers,
            cpu_resources=cpu_record,meminfo_bytes=cpu_record["meminfo_bytes"],
            disk_free_bytes=cpu_record["disk_free_bytes"])
        if self.a.run_root.exists():
            save(self.a.run_root/("observation-"+str(self.seq)+".json"),record);self.seq+=1
        return record
    def create(self,stage):
        self.stage=stage;self.secondary=[];self.output=self.a.run_root/stage;self.output.mkdir()
        (self.output/"audit").mkdir()
        self.cards=[] if stage=="native" else [self.a.physical_device] if stage=="numeric" else [4,5,6,7]
        if stage=="native":save(self.output/"cpu-resource-before.json",self.cpu_observe("native"))
        else:self.observe("numeric" if stage=="numeric" else "model",require_idle=True)
        name="q36-deltalog-v7-"+stage+"-"+uuid.uuid4().hex[:12]
        cmd=[DOCKER,"create","--name",name,"--label","qwen36.owner="+OWNER,
            "--label","qwen36.stage="+stage,"--cpus=1","--memory="+("8g" if stage in ("numeric","native") else "64g"),
            "--memory-swap="+("8g" if stage in ("numeric","native") else "64g"),
            "--ipc=private","--shm-size=2g","--pids-limit=512","--cap-drop=ALL",
            "--security-opt=no-new-privileges","--network="+("none" if stage in ("numeric","native") else "bridge")]
        def mount(src,dst,ro=True):
            cmd.extend(["--mount","type=bind,src="+str(Path(src).resolve())+",dst="+dst+(",readonly" if ro else "")])
        mount(self.root,"/deltalog-mixed-plugin");mount(self.a.legacy_plugin,"/legacy-deltalog-plugin")
        mount(self.a.library,"/candidate-library.so");mount(self.a.consumer_dir,"/model-consumers")
        mount("/usr/local/Ascend/driver","/usr/local/Ascend/driver")
        mount(self.output,"/deltalog-results",False)
        mount(self.a.model_dir/"config.json" if stage in ("numeric","native") else self.a.model_dir,
              "/model-config.json" if stage in ("numeric","native") else "/model")
        if stage not in ("numeric","native"):cmd.extend(["--publish",f"127.0.0.1:{self.a.port}:8000"])
        for physical,logical in [(p,i) for i,p in enumerate(self.cards)]:
            cmd.append(f"--device=/dev/davinci{physical}:/dev/davinci{logical}")
        if stage!="native":
            for device in ("/dev/davinci_manager","/dev/devmm_svm","/dev/hisi_hdc"):
                require(Path(device).exists(),"actual device missing: "+device);cmd.append("--device="+device)
        env={"OMP_NUM_THREADS":"1","MKL_NUM_THREADS":"1","OPENBLAS_NUM_THREADS":"1",
            "PYTHONDONTWRITEBYTECODE":"1","ASCEND_RT_VISIBLE_DEVICES":",".join(str(i) for i in range(len(self.cards))),
            "PYTHONPATH":"/deltalog-mixed-plugin:/legacy-deltalog-plugin",
            "QWEN36_DELTALOG_ENABLE":"0","QWEN36_DELTALOG_MIXED_ENABLE":"0",
            "QWEN36_DELTALOG_MIXED_ADMITTED":"0","VLLM_WORKER_MULTIPROC_METHOD":"spawn"}
        if stage=="native":
            env["TORCH_DEVICE_BACKEND_AUTOLOAD"]="0"
            inner=[PY,"-B","/deltalog-mixed-plugin/native_preflight.py","--produce","/deltalog-results/native-meta.json"]
        elif stage=="numeric":
            env["TORCH_DEVICE_BACKEND_AUTOLOAD"]="0"
            inner=[PY,"-B","/deltalog-mixed-plugin/numeric_entry.py"]
        else:
            inner=service_args(stage)
            if stage in ("candidate","qualify"):
                numeric=json.loads((self.a.numeric_receipt_path).read_text())
                c.accept_matrix(numeric,c.package_digest(self.root))
                mount(self.a.numeric_receipt_path,"/numeric-receipt.json")
                env.update(QWEN36_DELTALOG_MIXED_ENABLE="1",QWEN36_DELTALOG_MIXED_ADMITTED="1",
                    QWEN36_DELTALOG_MIXED_NUMERIC_RECEIPT="/numeric-receipt.json",
                    QWEN36_DELTALOG_LIBRARY="/candidate-library.so",
                    QWEN36_DELTALOG_MIXED_AUDIT="/deltalog-results/audit")
        for k,v in env.items():cmd.extend(["-e",k+"="+v])
        cmd+=[c.IMAGE,"/bin/bash","-c",
            'source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"',"deltalog-pipeline"]+inner
        save(self.output/"create-argv.json",dict(argv=cmd,physical=self.cards,environment=env))
        r=self.call(cmd,60);save(self.output/"create-receipt.json",r)
        cid=r["stdout"].strip();require(len(cid)==64 and all(ch in "0123456789abcdef" for ch in cid),"exact created CID")
        self.active=cid
        r,x=self.inspect(cid);save(self.output/"inspect-created.json",r)
        require(not x["State"]["Running"] and x["State"]["Pid"]==0,"new container not started unexpectedly")
        save(self.output/"start-receipt.json",self.call([DOCKER,"start",cid],60))
    def guarded(self,fn):
        with cf.ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(fn)
            while not future.done():
                try:self.observe("numeric" if self.stage=="numeric" else "model")
                except BaseException as primary:
                    # Stop only after exact identity revalidation so blocking HTTP
                    # unwinds promptly; protected/unowned jobs are never touched.
                    try:
                        self.inspect(self.active,cleanup=True)
                        receipt=self.run([DOCKER,"stop","--time","15",self.active],45)
                        require(receipt["exit_code"]==0,"guard-triggered owned stop failed")
                    except BaseException as secondary:self.secondary.append(dict(primary=repr(primary),cleanup=repr(secondary)))
                    raise
                try:return future.result(timeout=5)
                except cf.TimeoutError:pass
            result=future.result()
            self.observe("numeric" if self.stage=="numeric" else "model")
            return result
    def health(self):
        until=time.monotonic()+1800;base=f"http://127.0.0.1:{self.a.port}"
        while time.monotonic()<until:
            self.observe("model")
            r,x=self.inspect(self.active)
            require(x["State"]["Running"],"service exited before health")
            try:
                with urlopen(base+"/health",timeout=5) as resp:
                    if resp.status==200:
                        self.observe("model",need_process=True);return base
            except OSError:pass
            time.sleep(5)
        raise TimeoutError("actual service health")
    def native(self):
        self.create("native");until=time.monotonic()+1200
        while True:
            r,x=self.inspect(self.active)
            if not x["State"]["Running"]:
                save(self.output/"inspect-exited.json",r)
                require(x["State"]["ExitCode"]==0,"actual no-device dlopen/schema/Meta failed; original logs retained")
                report=json.loads((self.output/"native-meta.json").read_text())
                np.consume(report,self.root);return report
            require(time.monotonic()<until,"actual CPU no-device preflight bounded1200s")
            save(self.output/("cpu-resource-"+str(time.time_ns())+".json"),self.cpu_observe("native"))
            time.sleep(5)
    def numeric(self):
        self.create("numeric")
        while True:
            r,x=self.inspect(self.active)
            self.observe("numeric")
            if not x["State"]["Running"]:
                save(self.output/"inspect-exited.json",r)
                require(x["State"]["ExitCode"]==0,"numerical/actual CLI-help producer failed")
                numeric=json.loads((self.output/"numeric160.json").read_text())
                c.accept_matrix(numeric,c.package_digest(self.root))
                c.accept_qualification_directory(self.output,self.root)
                return numeric
            time.sleep(5)
    def service(self,stage,prompts=None):
        self.create(stage);base=self.health();model="qwen36-deltalog-pair"
        if prompts is None:
            def build_prompts():
                from prompt_source import build
                rows={str(n):sc.prompt(base,model,n) for n in (128,1024,8192,9216)}
                rows["screen"]=build(base,model)
                return rows
            prompts=self.guarded(build_prompts)
            save(self.a.run_root/"immutable-prompts.json",dict(config=c.CONFIG_SHA,model=model,
                prompts=prompts,prompt_sha256={k:([sc.digest_tokens(row) for row in v] if k=="screen" else sc.digest_tokens(v)) for k,v in prompts.items()}))
        replay=self.guarded(lambda:sc.replay(base,model,prompts["1024"]))
        save(self.output/"replay.json",replay)
        sc.replay_identity(replay) # dense and candidate determinism includes both warmups
        mixed=self.guarded(lambda:sc.mixed_workload(base,model,prompts))
        save(self.output/"mixed-http.json",mixed)
        if stage=="qualify":
            cache=self.guarded(lambda:sc.cache_copy_workload(base,model,prompts["screen"]))
            save(self.output/"cache-copy-http.json",cache)
            sc.accept_cache_copy_workload(cache)
            return prompts,replay,None
        perf=self.guarded(lambda:sc.perf(base,model,prompts,
            only_case=(self.a.screen_input_tokens,self.a.screen_batch)))
        save(self.output/"fixed1024.json",perf)
        self.observe("model",need_process=True)
        return prompts,replay,perf
    def cleanup(self):
        if not self.active:return
        cid=self.active;errors=[];released=False;identity=False
        try:
            r,x=self.inspect(cid,cleanup=True);save(self.output/"cleanup-before-inspect.json",r);identity=True
        except BaseException as error:errors.append(dict(operation="exact-before-inspect",error=repr(error)))
        if identity:
            try:
                logs=self.run([DOCKER,"logs","--timestamps","--tail","10000",cid],30)
                save(self.output/"actual-container-logs.json",logs)
                require(logs["exit_code"]==0,"owned logs collection failed")
            except BaseException as error:errors.append(dict(operation="logs",error=repr(error)))
            try:
                receipt=self.run([DOCKER,"stop","--time","15",cid],45)
                save(self.output/"stop-retain-receipt.json",receipt)
                require(receipt["exit_code"]==0,"exact owned stop failed")
            except BaseException as error:errors.append(dict(operation="stop",error=repr(error)))
            try:
                r,x=self.inspect(cid,cleanup=True);save(self.output/"cleanup-after-inspect.json",r)
                require(not x["State"]["Running"] and x["State"]["Pid"]==0 and not x.get("ExecIDs"),
                    "exact owned container remains live")
                released=True
                require(not x["State"].get("OOMKilled",False),"OOM invalidates stage")
            except BaseException as error:errors.append(dict(operation="after-inspect",error=repr(error)))
        if released:
            self.active=None;self.cards=[]
            try:
                if self.stage=="native":save(self.output/"cpu-resource-after.json",self.cpu_observe("native"))
                else:self.observe("numeric",require_idle=True)
            except BaseException as error:errors.append(dict(operation="resource-release",error=repr(error)))
        # Unknown/live CID stays active; never falsely report stopped-retained.
        save(self.output/"cleanup-verdict.json",dict(cid=cid,retained=released,stopped=released,
            resource_release_verified=released and not errors,rm_authorized=False,errors=errors,
            unresolved_active_cid=self.active,secondary_guard_cleanup=self.secondary))
        require(not errors and released,"owned cleanup/resource release failed: "+repr(errors))
def run_stage(lane,fn,verdict):
    primary=None
    try:return fn()
    except BaseException as error:primary=error;raise
    finally:
        try:lane.cleanup()
        except BaseException as cleanup:
            verdict.setdefault("secondary_cleanup_errors",[]).append(repr(cleanup))
            if primary is None:raise
        finally:verdict["unresolved_active_cid"]=lane.active
def accept_native_provenance(output,root,a,lane):
    report_path=output/"native-meta.json";report=json.loads(report_path.read_text())
    np.consume(report,root)
    created=json.loads((output/"create-receipt.json").read_text())
    require(created["exit_code"]==0,"actual no-device child create receipt")
    cid=created["stdout"].strip()
    require(len(cid)==64 and all(ch in "0123456789abcdef" for ch in cid),"exact CPU child CID")
    for name in ("inspect-created.json","inspect-exited.json","cleanup-after-inspect.json"):
        receipt=json.loads((output/name).read_text());require(receipt["exit_code"]==0,"actual CPU inspect command")
        rows=json.loads(receipt["stdout"]);require(len(rows)==1,"one actual CPU child")
        x=check_inspect(rows[0],cid,"native",output,root,a)
        if name!="inspect-created.json":
            require(not x["State"]["Running"] and x["State"]["Pid"]==0 and x["State"]["ExitCode"]==0,
                "actual native preflight child successful and stopped")
    cleanup=json.loads((output/"cleanup-verdict.json").read_text())
    require(cleanup["cid"]==cid and cleanup["retained"] is True and cleanup["errors"]==[] and
        cleanup["resource_release_verified"] is True,"actual CPU child stop-retain/resource release")
    receipt=lane.call([DOCKER,"inspect",cid]);x=json.loads(receipt["stdout"])[0]
    check_inspect(x,cid,"native",output,root,a)
    require(not x["State"]["Running"] and x["State"]["Pid"]==0 and x["State"]["ExitCode"]==0,
        "fresh original no-device child identity")
    return dict(schema="qwen36-deltalog-native-provenance/v7",actual_report_ref=dict(path=str(report_path),sha256=c.sha(report_path)),
        source_digest=c.package_digest(root),original_child_cid=cid,actual_fresh_inspect=receipt,
        npu_executed=False,model_executed=False,meta_preflight_consumed=True)
def accept_service_cli(path):
    row=json.loads(Path(path).read_text())
    stream=json.loads((Path(path).parent/"actual-stream-source-pins.json").read_bytes())
    require(stream.get("schema")=="qwen36-deltalog-stream-source/v1" and
        stream.get("source_digest")==c.package_digest(Path(__file__).resolve().parent) and
        stream.get("pins")==sc.STREAM_SOURCE_PINS,"actual same-image streaming API source identity")
    require(row["exit_code"]==0,"actual image CLI-help failed; model interface pending")
    require(row["argv"]==[PY,"-B","-m","vllm.entrypoints.openai.api_server","--help"],
        "actual exact same-image service CLI-help argv")
    for option in SERVICE_OPTIONS:require(option in row["stdout"],"actual service option absent: "+option)
    return True
def validate_resume(a,root,lane=None):
    path=a.numeric_receipt_path.resolve(strict=True)
    require(path.name=="numeric160.json" and path.parent.name=="numeric","exact original numeric-stage receipt")
    original=path.parent.parent
    require(original.is_relative_to(Path("/cache/cch")) and original!=a.run_root.resolve(),
        "original private result path; new resume output must not overwrite it")
    report=json.loads(path.read_text());digest=c.package_digest(root);c.accept_matrix(report,digest)
    c.accept_qualification_directory(path.parent,root)
    plan=json.loads((original/"plan.json").read_text())
    require(plan["source_digest"]==digest and plan["image"]==c.IMAGE,"original v6 source/image identity")
    pins=dict(host=HOST_SHA,host_dependency=OLD_SHA,library=c.DECODE_SHA,config=c.CONFIG_SHA)
    require(plan["source_pins"]==pins,"original source/library/config/helper pins")
    final=json.loads((original/"pipeline-verdict.json").read_text())
    require(final["source_digest"]==digest and final["numeric160"] is True and final["status"] in
        ("numeric-stage-complete-model-service-pending","available-stages-complete-finaltasks-pending"),
        "actual original pipeline numeric completion required")
    created=json.loads((path.parent/"create-receipt.json").read_text())
    require(created["exit_code"]==0,"actual original child creation")
    cid=created["stdout"].strip()
    require(len(cid)==64 and all(ch in "0123456789abcdef" for ch in cid),"original exact child CID")
    original_args=argparse.Namespace(**vars(a));original_args.run_root=original
    for name in ("inspect-created.json","inspect-exited.json","cleanup-after-inspect.json"):
        row=json.loads((path.parent/name).read_text())
        require(row["exit_code"]==0,"actual original inspection failed")
        x=json.loads(row["stdout"])[0]
        check_inspect(x,cid,"numeric",path.parent,root,original_args)
        if name!="inspect-created.json":
            require(not x["State"]["Running"] and x["State"]["Pid"]==0 and x["State"]["ExitCode"]==0,
                "original native producer child did not exit0/stay stopped")
    cleanup=json.loads((path.parent/"cleanup-verdict.json").read_text())
    require(cleanup["cid"]==cid and cleanup["retained"] is True and cleanup["errors"]==[],
        "actual stopped-retained original child/release proof")
    argv=json.loads((path.parent/"create-argv.json").read_text())["argv"]
    require(argv[0:2]==[DOCKER,"create"] and "/deltalog-mixed-plugin/numeric_entry.py" in argv,
        "original full native producer actual child command")
    proof=dict(schema="qwen36-deltalog-numeric-resume/v7",source_digest=digest,
        original_numeric=str(path),numeric_sha256=c.sha(path),original_child_cid=cid,
        original_plan_sha256=c.sha(original/"plan.json"),
        original_cleanup_sha256=c.sha(path.parent/"cleanup-verdict.json"),
        complete_native_cases=len(report["cases"]),native_steps=160,fresh_original_child_pending=lane is None)
    if lane is not None:
        r=lane.call([DOCKER,"inspect",cid]);x=json.loads(r["stdout"])[0]
        check_inspect(x,cid,"numeric",path.parent,root,original_args)
        require(not x["State"]["Running"] and x["State"]["Pid"]==0 and x["State"]["ExitCode"]==0,
            "fresh original exact child no longer stopped/successful")
        proof.update(fresh_original_child_pending=False,actual_fresh_original_child_inspect=r)
    return report,proof
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--authority",type=Path,required=True)
    p.add_argument("--authority-sha256",required=True)
    p.add_argument("--run-root",type=Path,required=True);p.add_argument("--library",type=Path,required=True)
    p.add_argument("--legacy-plugin",type=Path,required=True);p.add_argument("--consumer-dir",type=Path,required=True)
    p.add_argument("--model-dir",type=Path,default=Path("/cache/efim/Qwen3.6-27B"))
    p.add_argument("--physical-device",type=int,choices=range(4,8),default=4)
    p.add_argument("--port",type=int,default=19136);p.add_argument("--lease-seconds",type=int,default=16200)
    p.add_argument("--execute",action="store_true")
    p.add_argument("--screen-input-tokens",type=int,choices=(32768,),default=32768)
    p.add_argument("--screen-batch",type=int,choices=(16,),default=16)
    stage=p.add_mutually_exclusive_group()
    stage.add_argument("--stop-after-native",action="store_true")
    stage.add_argument("--stop-after-numerics",action="store_true")
    stage.add_argument("--resume-numeric-receipt",type=Path)
    a=p.parse_args();require(600<=a.lease_seconds<=16200,"bounded explicit MAIN lease ≤4.5h")
    a.host_original_affinity=sorted(os.sched_getaffinity(0))
    os.sched_setaffinity(0,{min(a.host_original_affinity)})
    original=resource.getrlimit(resource.RLIMIT_AS)
    require(original[1]==resource.RLIM_INFINITY,"original hard AS limit must permit Docker CLI safe VAS restoration")
    resource.setrlimit(resource.RLIMIT_AS,(HOST_RESERVE,original[1]))
    require(Path(PRLIMIT).is_file(),"actual prlimit utility required")
    a.numeric_receipt_path=(a.resume_numeric_receipt.resolve(strict=True) if a.resume_numeric_receipt else a.run_root/"numeric/numeric160.json")
    root=Path(__file__).resolve().parent
    plan=source_preflight(a,root);print(json.dumps(plan,sort_keys=True))
    if not a.execute:return
    lane=Lane(a,root)
    lane.cpu_observe("native") # no card query/allocation before actual dlopen/Meta preflight
    disk_floor=(11 if a.stop_after_native else 13 if a.stop_after_numerics else 18 if a.resume_numeric_receipt else 23)*1024**3
    require(shutil.disk_usage(a.run_root.parent).free>=disk_floor,"fresh per-stage output allowance plus unchanged8GiB disk reserve")
    a.run_root.mkdir(exist_ok=False);save(a.run_root/"plan.json",plan)
    verdict={"schema":"qwen36-deltalog-complete-result/v7","source_digest":c.package_digest(root),
        "status":"running","final_acceptance":False,"finaltasks2048":"pending-official-MAIN-runner-identity",
        "serving_graph_scope":"both-enforce-eager; no serving graph-replay claim"}
    try:
        native=run_stage(lane,lane.native,verdict)
        native_proof=accept_native_provenance(a.run_root/"native",root,a,lane)
        save(a.run_root/"native-preflight-consumed.json",native_proof)
        verdict.update(native_preflight=True,native_preflight_ref=native_proof["actual_report_ref"])
        if a.stop_after_native:
            verdict.update(status="native-no-device-complete-numeric-model-pending",numeric160=False,
                actual_model_consumer=False,same_stack_fixed1024=False)
            return
        lane.observe("numeric" if a.stop_after_numerics else "model",require_idle=True) # fresh actual SMI PID/cgroup/HBM gate
        if a.resume_numeric_receipt:
            numeric,provenance=validate_resume(a,root,lane)
            save(a.run_root/"resume-validation.json",provenance)
        else:
            numeric=run_stage(lane,lane.numeric,verdict)
        if a.stop_after_numerics:
            verdict.update(status="numeric-stage-complete-model-service-pending",numeric160=True,
                actual_model_consumer=False,same_stack_fixed1024=False,numeric_receipt=str(a.numeric_receipt_path),
                numeric_receipt_sha256=c.sha(a.numeric_receipt_path))
            return
        accept_service_cli(a.numeric_receipt_path.parent/"actual-service-cli-help.json")
        prompts,dense,dp=run_stage(lane,lambda:lane.service("dense"),verdict)
        _,qualification,_=run_stage(lane,lambda:lane.service("qualify",prompts),verdict)
        qualified_replay=sc.compare_replays(dense,qualification)
        save(a.run_root/"qualified-cache-replay.json",qualified_replay)
        require(qualified_replay["greedy_matches"]==8 and qualified_replay["warmup_divergences"]==0,
                "actual PDC ON cache lifecycle replay differs from dense")
        _,candidate,cp=run_stage(lane,lambda:lane.service("candidate",prompts),verdict)
        paired=sc.compare_replays(dense,candidate);save(a.run_root/"paired-replay.json",paired)
        report=collect([a.run_root/"qualify/audit",a.run_root/"candidate/audit"],numeric,paired)
        try:c.validate_model_receipt(report,c.package_digest(root));report["passed"]=True
        except BaseException as error:report.update(passed=False,error=repr(error));raise
        finally:save(a.run_root/"model-consumer-verdict.json",report)
        performance=sc.accept_perf_pair(dp,cp);save(a.run_root/"fixed1024-pair.json",performance)
        verdict.update(status="available-stages-complete-finaltasks-pending",numeric160=True,
            actual_model_consumer=True,same_stack_fixed1024=True)
    except BaseException as error:verdict.update(status="failed",error=repr(error));raise
    finally:save(a.run_root/"pipeline-verdict.json",verdict)
if __name__=="__main__":main()

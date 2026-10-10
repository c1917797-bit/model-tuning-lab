#!/usr/bin/env python3
"""DEFAULT OFF MAIN-only SKVQ native baseline calibration dispatcher.
Not a quantized cache/service/E2E gate. No subprocess or Torch at import.
"""
import argparse,datetime,hashlib,json,os,re,resource,shutil,subprocess,sys,time,traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-calibration-capture-chain-v1-001")
ORDER=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-tp4-qkv-loader-order-v1-001")
TRAIN=Path("/cache/cch/qwen36-damp-20261006/calibration-inputs/source-v2")
TRAIN_GUEST="/cache/cch/qwen36-damp-20261006/calibration-inputs/source-v1"
LINEAR=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/source-public-linear-660-20261008-1106-001/linear.py")
MODEL=Path("/cache/efim/Qwen3.6-27B")
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
PY="/usr/local/python3.12.13/bin/python3";DOCKER="/usr/bin/docker";PRLIMIT="/usr/bin/prlimit";SMI="/usr/local/sbin/npu-smi"
DEADLINE=1791788425
TOTAL=7200;CLEANUP=180;GIB=2**30;OWNER="skvq-current72h-preprojection-v1-006"
sys.path.insert(0,str(BASE));from io_contract import publish_json,reference,require
import resources as R
import current_contract as C
from physical_hbm import actual_hbm
import mount_preflight as M
import input_dependency as D
PROJECTION=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-preprojection-capture-adapter-v1-001")
def closure():return C.source()
def newroot(p):
    p=Path(p)
    require(p.is_absolute() and ".." not in p.parts and p.parent==HERE.parent and
       p.parent.resolve()==p.parent and re.fullmatch("run-skvq-current72h-projection-006-[a-zA-Z0-9-]+",p.name) and
       not p.exists() and not p.is_symlink(),"absent exact new hostroot under lowbit")
    p.mkdir();return p
def payload(ctl):
    # Actual index/payload binding, not model marketing identity. No invented
    # publisher receipt. Reject missing/non-indexed/non-BF16 weight payload.
    index=MODEL/"model.safetensors.index.json"
    v=json.loads(index.read_text());wm=v["weight_map"]
    require(type(wm) is dict and wm and all(type(k) is str and type(f) is str for k,f in wm.items()),"actual safetensors index")
    files=sorted(set(wm.values()));require(len(files)<=128,"bounded actual weight shards")
    rows=[];covered=set()
    for name in files:
        require(Path(name).name==name and name.endswith(".safetensors"),"ordinary exact shard name")
        ctl.left();ctl.guard();p=MODEL/name
        with p.open("rb") as f:
            n=int.from_bytes(f.read(8),"little");require(0<n<=16*2**20,"bounded actual safetensors header")
            header=json.loads(f.read(n))
        tensors={k for k in header if k!="__metadata__"}
        require(tensors=={k for k,f in wm.items() if f==name},"index actual tensor membership")
        for k in tensors:
            h=header[k];require(h["dtype"] in ("BF16","F32") and type(h["shape"]) is list and
              len(h["data_offsets"])==2 and 0<=h["data_offsets"][0]<=h["data_offsets"][1]<=p.stat().st_size-8-n,
              "actual native BF16/F32 payload bounds; not quantized substitute")
        require(not covered&tensors,"unique actual tensor keys");covered|=tensors
        digest=hashlib.sha256();count=0
        with p.open("rb") as f:
            for b in iter(lambda:f.read(1048576),b""):
                digest.update(b);count+=len(b)
                if count%(64*2**20)==0:ctl.left();ctl.guard()
        rows.append(dict(path=str(p),sha256=digest.hexdigest(),bytes=count))
    require(covered==set(wm),"all actual indexed weights")
    return dict(index=reference(index),shards=rows,actual_weight_publisher_identity_pending=True,
      path_is_not_marketing_identity=True)
class Control:
    def __init__(self,out,limit=TOTAL):
        require(type(limit)is int and limit in(1200,TOTAL),"fixed CPU-only1200 or original capture7200; no extra clock")
        self.limit=limit
        self.out=out;self.start=time.monotonic();self.end=min(self.start+limit,self.start+DEADLINE-time.time())
        self.current=None;self.owned=[];self.secondary=[];self.primary=None;self.seq=0;self.child=None;self.protected=None
        self.spend=[];self.observations=[];self.rss_latched=None;self.cleanup_spent=0.;self.cleanup_started=None
    def left(self,cleanup=False,cap=30):
        value=self.end-time.monotonic()-(0 if cleanup else CLEANUP)
        if cleanup:
            require(self.cleanup_started is not None,"cleanup scope entered")
            value=min(value,CLEANUP-self.cleanup_spent-(time.monotonic()-self.cleanup_started))
        require(value>0,"total7200 includes180 cleanup and portfolio hard cutoff, never reset")
        return min(cap,value)
    def save(self,label,value):return publish_json(self.out/(label+"-"+str(time.time_ns())+".json"),value)
    def guard(self):
        try:
            value=R.rss();self.save("ACTUAL_HOST_CLI_RSS",value)
            require(value["live_sum_bytes"]<=R.HOST and value["conservative_cumulative_peak_sum_bytes"]<=R.HOST,"actual host+CLI summed RSS512MiB")
            return value
        except BaseException as e:self.rss_latched=repr(e);raise
    def wrapper(self,argv):return [PRLIMIT,"--as=unlimited","--",*argv] if argv[0]==DOCKER else argv
    def call(self,label,argv,cleanup=False,create=False,cap=30):
        # Exact-owned read-only observer/stop is permitted after RSS latch.
        if cleanup:
            require(argv[0] in (DOCKER,SMI) and
              ((argv[0]==DOCKER and argv[1] in ("inspect","stop") and self.current and self.current["cid"] in argv) or
               (argv==[SMI,"info"])),"narrow exact cleanup command, no broad stop")
        else:require(self.rss_latched is None,"failed RSS cannot re-admit")
        wrapped=self.wrapper(list(argv));value=None
        try:
            p=subprocess.run(wrapped,capture_output=True,text=True,timeout=self.left(cleanup,cap))
            value=dict(argv=list(argv),actual_wrapped_argv=wrapped,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,observed_epoch=time.time())
            if create and p.returncode==0 and re.fullmatch("[0-9a-f]{64}",p.stdout.strip()):
                # Latch immediately before persistence/RSS/inspect can fail.
                self.current["cid"]=p.stdout.strip();self.owned.append(self.current)
            raw=self.save(label,value)
            if create and self.current["cid"]:self.save("OWNED",dict(**self.current,create_raw=raw))
            if not cleanup:self.guard()
            require(p.returncode==0,"actual child command exit retained "+str(raw))
            return value,raw
        except BaseException as e:
            if value is None:self.save(label+"-exception",dict(argv=argv,actual_wrapped_argv=wrapped,error=repr(e),traceback=traceback.format_exc()))
            raise
    def devices(self,npu):
        return ({"/dev/davinci"+str(i):"/dev/davinci"+str(i-4) for i in range(4,8)} |
          {"/dev/"+k:"/dev/"+k for k in ("davinci_manager","devmm_svm","hisi_hdc")}) if npu else {}
    def env(self,npu):
        return dict(ASCEND_RT_VISIBLE_DEVICES="0,1,2,3" if npu else "",TORCH_DEVICE_BACKEND_AUTOLOAD="0",
           PYTHONDONTWRITEBYTECODE="1",OMP_NUM_THREADS="1",MKL_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",
           MAIN_SKVQ_CPU_ENABLE="1",QWEN36_SKVQ_CAPTURE_ENABLE="1",QWEN36_SKVQ_TP4_CAPTURE_ENABLE="1",QWEN36_SKVQ_PROJECTION_CAPTURE_ENABLE="1",
           QWEN36_SKVQ_PROJECTION_CONSUME_ENABLE="1")
    def mounts(self,npu,inputs=None):
        m={str(p):(str(p),False) for p in (HERE,BASE,ORDER,PROJECTION,MODEL,LINEAR)}
        m[TRAIN_GUEST]=(str(TRAIN),False)
        # Frozen full consumer opens every donor snapshot; mount exact files RO.
        pins=json.loads((BASE/"source_pins.json").read_text())
        require(len(pins["sources"])==8,"exact eight immutable donor source inputs")
        for pin in pins["sources"]:
            p=Path(pin["snapshot"])
            require(p.is_absolute() and reference(p)["sha256"]==pin["sha256"],"actual donor snapshot byte pin")
            m[str(p)]=(str(p),False)
        manifest=json.loads((HERE/"SOURCE_MANIFEST.json").read_text())
        for row in manifest["dependencies"]:
            p=Path(row["path"])
            if not any(p==Path(q) or Path(q)in p.parents for q in m):m[str(p)]=(str(p),False)
        for dst,value in D.mounts().items():
            require(dst not in m,"unique CPU dependency RO mount");m[dst]=value
        m[str(self.out)]=(str(self.out),True)
        if inputs:m[str(inputs)]=(str(inputs),False)
        if npu:m["/usr/local/Ascend/driver"]=("/usr/local/Ascend/driver",False)
        return m
    def validate(self,x,e):
        h=x["HostConfig"];c=x["Config"]
        require(x["Id"]==e["cid"] and x["Name"]=="/"+e["name"] and x["Image"]==IMAGE and c["Image"]==IMAGE and
          c["Entrypoint"]==["/bin/bash"] and c["Cmd"]==["-c","exec /bin/sleep infinity"] and
          c["Labels"].get("model-tuning-lab.owner")==OWNER and
          c["Labels"].get("model-tuning-lab.source")==e["source"],"exact owned full CID/image/source/init")
        require(not h["Privileged"] and h["Memory"]==e["mem"] and h["MemorySwap"]==e["mem"] and
          h["NanoCpus"]==4*10**9 and h["CpusetCpus"]==e["cpuset"] and h["CgroupnsMode"]=="host" and
          h["NetworkMode"]=="none" and h["IpcMode"]=="private" and h["ShmSize"]==2*GIB and h["PidsLimit"]==1024 and
          set(h.get("CapDrop") or [])=={"ALL"} and set(h.get("SecurityOpt") or [])=={"no-new-privileges"} and
          not h.get("DeviceRequests") and not h.get("DeviceCgroupRules"),"actual cgroup/isolation binding")
        ds=h.get("Devices") or []
        require(len(ds)==len(e["devices"]) and {d["PathOnHost"]:d["PathInContainer"] for d in ds}==e["devices"] and
          all(d["CgroupPermissions"]=="rwm" for d in ds),"exact Devices[] or only4-7 mapping, no0-3")
        ms=x["Mounts"];require(len(ms)==len(e["mounts"]) and len({m["Destination"] for m in ms})==len(ms) and
          all(m["Type"]=="bind" for m in ms) and {m["Destination"]:(m["Source"],m["RW"]) for m in ms}==e["mounts"],"mounts semantic set, not array order")
        for k,v in e["env"].items():require(c["Env"].count(k+"="+v)==1 and sum(z.startswith(k+"=") for z in c["Env"])==1,"exact nonduplicated env")
        return x
    def inspect(self,cleanup=False):
        v,r=self.call("inspect",[DOCKER,"inspect",self.current["cid"]],cleanup);xs=json.loads(v["stdout"])
        require(len(xs)==1,"one actual owned inspect");return self.validate(xs[0],self.current),r
    def observe(self,active=False,cleanup=False):
        v,r=self.call("smi",[SMI,"info"],cleanup);h=R.helper().frozen();prot=h.protected(v["stdout"])
        if self.protected is None:self.protected=prot
        owned_cids=[e["cid"] for e in self.owned if e.get("cid")]
        owned_host_pids=[os.getpid()]
        boundary=C.protected_module().protected_boundary(self.protected,prot,owned_cids,owned_host_pids)
        pr=self.save("PROTECTED",dict(smi=r,actual=prot,original=self.protected,boundary=boundary,
          owned_cids=owned_cids,owned_host_pids=owned_host_pids,
          current_cid=self.current["cid"] if self.current else None,
          current_phase=self.current["phase"] if self.current else None))
        proofs=[];hbm=[]
        for card in (4,5,6,7):
            hbm.append(actual_hbm(v["stdout"],card))
            rows=[row for row in h.legacy().process_rows(v["stdout"]) if row[0]==card]
            if not active or not rows:h.idle_one(v["stdout"],card)
            for physical,chip,pid in rows:
                proof=h.gate_process(pid);require(chip==0 and self.current["cid"] in proof["cgroup"],"actual foreign workload/ownership conflict")
                proofs.append(dict(physical=physical,chip=chip,smi=r,**proof))
        rr=self.save("OWNED_NPU_OBSERVATION",dict(proofs=proofs,smi=r,actual_hbm=hbm,protected_boundary_ref=pr));self.observations.append(rr)
        return r,proofs
    def create(self,phase,npu,mem,inputs=None):
        rs=R.fresh(mem,self.out);require(rs["disk_available_bytes"]>=320*GIB if npu else rs["disk_available_bytes"]>=8*GIB,"actual disk budget")
        if npu:self.observe()
        rr=self.save("FRESH_RESOURCES",rs);allocation=rs["allocation"]
        e=dict(cid=None,name="skvq-"+self.out.name+"-"+phase,source=closure()["sha256"],
          cpuset=",".join(map(str,allocation["guest_cpus"])),mem=mem,phase=phase,npu=npu,
          mounts=self.mounts(npu,inputs),devices=self.devices(npu),env=self.env(npu),resource_ref=rr)
        pre=M.observe(e["mounts"],phase,closure())
        e["mount_preflight_ref"]=self.save("EXACT_MOUNT_TRAIN_PREFLIGHT",pre)
        require(pre["passed"],"exact mount/TRAIN preflight refusal: "+json.dumps(pre["errors"],sort_keys=True))
        self.current=e
        v,_=self.call("unique",[DOCKER,"ps","-a","--filter","name=^/"+e["name"]+"$","--format","{{.ID}}"])
        require(not v["stdout"].strip(),"unique exact new name; never reuse")
        argv=[DOCKER,"create","--name",e["name"],"--network","none","--cap-drop","ALL","--security-opt","no-new-privileges",
          "--memory",str(mem),"--memory-swap",str(mem),"--cpus","4","--cpuset-cpus",e["cpuset"],"--pids-limit","1024",
          "--cgroupns","host","--ipc","private","--shm-size",str(2*GIB),"--entrypoint","/bin/bash",
          "--label","model-tuning-lab.owner="+OWNER,"--label","model-tuning-lab.source="+e["source"]]
        for k,v in e["env"].items():argv+=["--env",k+"="+v]
        for src,dst in e["devices"].items():require(Path(src).exists(),"actual device");argv+=["--device",src+":"+dst+":rwm"]
        for dst,(src,rw) in e["mounts"].items():
            require(Path(src).exists() and "," not in src and "," not in dst,"actual exact comma-free mount")
            argv+=["--mount","type=bind,source="+src+",destination="+dst+("" if rw else ",readonly")]
        argv += [IMAGE,"-c","exec /bin/sleep infinity"]
        v,_=self.call("create",argv,create=True);require(e["cid"],"completed full64 CID only")
        x,_=self.inspect();require(not x["State"]["Running"] and x["State"]["Pid"]==0,"new stopped")
        self.call("start",[DOCKER,"start",e["cid"]]);x,ir=self.inspect()
        require(x["State"]["Running"] and x["State"]["Pid"]>0 and not x["State"]["OOMKilled"],"actual own init")
        guest=R.guest(x["State"]["Pid"],allocation["guest_cpus"],mem);gr=self.save("ACTUAL_GUEST",guest)
        self.spend.append(dict(phase=phase,cid=e["cid"],memory=mem,cpu=4,started_elapsed=time.monotonic()-self.start))
        return rs,rr,guest,gr,ir
    def exec(self,label,args,npu=False,cap=900,env=None):
        argv=[DOCKER,"exec"]
        for k,v in (env or {}).items():argv+=["--env",k+"="+v]
        argv+=[self.current["cid"],"/bin/bash","-c",'source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"',"skvq-owned",PY,"-B",*args]
        wrapped=self.wrapper(argv);so=self.out/(label+".stdout");se=self.out/(label+".stderr");primary=None
        deadline=time.monotonic()+self.left(cap=cap)
        with so.open("x") as o,se.open("x") as e:
            self.child=subprocess.Popen(wrapped,stdout=o,stderr=e)
            try:
                while self.child.poll() is None:
                    require(time.monotonic()<deadline,"actual bounded original child timeout; no retry")
                    x,_=self.inspect();require(x["State"]["Running"] and not x["State"]["OOMKilled"],"exact guest live/noOOM")
                    self.guard()
                    fields={l.split(":")[0]:int(l.split()[1])*1024 for l in Path("/proc/meminfo").read_text().splitlines() if l.startswith("MemAvailable:")}
                    require(fields["MemAvailable"]>=R.RESERVE+R.HOST,"runtime ordinary reserve, capspent cannot release HugeTLB")
                    require(shutil.disk_usage(self.out).free>=8*GIB,"actual runtime disk reserve")
                    if npu:self.observe(active=True)
                    time.sleep(min(10,max(.01,deadline-time.monotonic())))
                require(self.child.returncode==0,"actual child nonzero; raw stdout/stderr retained")
            except BaseException as err:primary=err
        done=self.child.poll() is not None
        r=self.save(label+"-CLI",dict(argv=argv,actual_wrapped_argv=wrapped,host_pid=self.child.pid,
          exit_code=self.child.returncode if done else None,terminated=done,
          stdout=reference(so) if done else {"pending_path":str(so)},stderr=reference(se) if done else {"pending_path":str(se)},
          primary=repr(primary) if primary else None))
        if primary:raise primary
        return r
    def cleanup(self):
        if not self.current or not self.current["cid"]:return None
        if self.current.get("released"):return self.current["release_ref"]
        self.cleanup_started=time.monotonic()
        result=dict(cid=self.current["cid"],retained=True,deleted=False,primary=repr(self.primary),rss_latched=self.rss_latched)
        try:
            self.inspect(cleanup=True);_,sr=self.call("stop",[DOCKER,"stop","--time","15",self.current["cid"]],True,cap=40)
            x,ir=self.inspect(cleanup=True);require(not x["State"]["Running"] and x["State"]["Pid"]==0 and not x.get("ExecIDs"),"exactowned stopped/Pid0/noExec")
            result.update(stop=sr,inspect=ir,noOOM=not x["State"]["OOMKilled"])
            if self.child and self.child.poll() is None:self.child.wait(timeout=self.left(True,30))
            require(self.child is None or self.child.poll() is not None,"original CLI reaped")
            if self.current["npu"]:result["release_smi"]=self.observe(cleanup=True)[0]
            require(not x["State"]["OOMKilled"],"actual OOM prevents completion")
            result["released"]=True
        except BaseException as e:self.secondary.append(repr(e));result["secondary"]=repr(e)
        self.cleanup_spent+=time.monotonic()-self.cleanup_started;self.cleanup_started=None
        r=self.save("STOP_RETAIN",result);self.child=None
        if result.get("released"):self.current.update(released=True,release_ref=r)
        return r
def execute(a):
    require(os.environ.get("MAIN_SKVQ_HOST_ENABLE")=="1","explicit MAIN opt-in")
    limit=1200 if a.cpu_inputs_only else TOTAL
    require(time.time()+limit<=DEADLINE,"whole fixed stage including180 before immutable portfolio cutoff")
    C.configure(a.source_manifest_sha256);lock=closure();R.helper();v=R.helper().cpu_view(os.getpid());os.sched_setaffinity(0,{min(v["effective_cpus"])})
    soft,hard=resource.getrlimit(resource.RLIMIT_AS);require(hard==resource.RLIM_INFINITY,"Docker-only child AS restoration requires unlimited hardAS")
    resource.setrlimit(resource.RLIMIT_AS,(R.HOST,hard))
    out=newroot(a.output);ctl=Control(out,limit);result=None;rawpayload=None
    try:
        cpu=out/"cpu";cpu.mkdir();ctl.create("preflight",False,8*GIB)
        ctl.exec("actual23-inputs",[str(HERE/"inside_cpu.py"),"--execute","--output",str(cpu)],cap=900,env={"SKVQ_CURRENT_MANIFEST_SHA256":lock["sha256"]})
        actual=json.loads((cpu/"CPU_COMPLETE.json").read_text());require(actual["status"]=="ACTUAL23_AND_REAL_TRAIN_INPUTS_CONSUMED","actual CLI complete")
        config_ref=reference(cpu/"ACTUAL_ENGINE_CONFIG.json")
        publish_json(out/"CPU_CONFIG_REF.json",config_ref)
        ctl.cleanup();require(not ctl.secondary,"CPU guest fully released beforeTP4")
        if a.cpu_inputs_only:
            result=dict(status="REAL_CPU_INPUTS_CONSUMED_NO_NPU",cpu_complete=reference(cpu/"CPU_COMPLETE.json"),
              actual_input_dependency_ref=reference(cpu/"INPUT_DEPENDENCY.json"),
              inputs=reference(cpu/"run-skvq-train-inputs-001-main/INPUTS.json"),input_consumer=reference(cpu/"INPUTS_CONSUMED.json"))
        else:
            inputs=cpu/"run-skvq-train-inputs-001-main";rawpayload=payload(ctl);ctl.save("ACTUAL_MODEL_PAYLOAD",rawpayload)
            rs,rr,g,gr,ir=ctl.create("tp4-capture",True,64*GIB,inputs)
            n1=out/"N1.json"
            ctl.exec("all4-n1",[str(HERE/"n1_check.py"),"--execute","--source-manifest-sha256",lock["sha256"],"--output",str(n1),"--cpu-config-ref-json",str(out/"CPU_CONFIG_REF.json")],True,180,{"MAIN_OWNED_CID":ctl.current["cid"]})
            require(json.loads(n1.read_text())["status"]=="SKVQ_ALL4_TINY_N1_CHECKED","actual all4 source-bound canary")
            left=min(4200,int(ctl.left(cap=TOTAL))-1800);require(left>=600,"full capture and independent consumer fit remaining original total")
            producer=out/"run-skvq-capture-projection-001-main"
            raw_smi,_=ctl.observe()
            admission=dict(schema="MAIN_SKVQ_FRESH_CAPTURE_ADMISSION_V1",current_source_ref=lock,current_clock=C.clock(),n1_ref=reference(n1),image=IMAGE,physical_npus=[4,5,6,7],
              owned_cid=ctl.current["cid"],inside_output_root=str(producer),observed_epoch=time.time(),max_total_seconds=left,
              cleanup_included_seconds=180,memory_guest_bytes=64*GIB,memory_host_bytes=R.HOST,memory_reserve_bytes=R.RESERVE,
              ordinary_available_bytes=rs["memory"]["MemAvailable"],guest_cpu_effective=g["cpu"]["effective_capacity"],
              host_cpu_effective=rs["host_cpu"]["effective_capacity"],joint_ancestor_cpu_budget=7,reserve_cpu=2,
              cpu_all_ancestors_checked=True,daemon_ancestors_checked=True,mounts_exact_semantic_set_checked=True,
              devices_exact_checked=True,source_manifest_consumed=True,input_raw_consumed=True,disk_available_bytes=rs["disk_available_bytes"],
              foreign_physical_npus_protected=[0,1,2,3],protected_services_untouched=True,raw_refs=[rr,gr,ir,raw_smi,lock,reference(cpu/"CPU_COMPLETE.json")])
            ar=publish_json(out/"CAPTURE_ADMISSION.json",admission)
            ctl.exec("capture256",[str(HERE/"capture_current.py"),"--execute","--source-manifest-sha256",lock["sha256"],"--inputs",str(inputs/"INPUTS.json"),
               "--output",str(producer),"--admission",ar["path"],"--max-total-seconds",str(left)],True,left,
               {"MAIN_OWNED_CID":ctl.current["cid"]})
            ctl.cleanup();require(not ctl.secondary,"TP4 exact stop-retain before independent CPU consumer")
            ctl.create("independent-consumer",False,2*GIB,inputs)
            cr=ctl.exec("consume-full256-preprojection",[str(HERE/"consume_stage.py"),"--execute","--source-manifest-sha256",lock["sha256"],"--root",str(producer),
              "--output",str(out/"CAPTURE_CONSUMED.json")],cap=ctl.left(cap=TOTAL))
            ctl.cleanup();require(not ctl.secondary,"consumer exact stop-retain")
            consumed=json.loads((out/"CAPTURE_CONSUMED.json").read_text())
            require(consumed["events"]==16384 and consumed["global_QKV_head_order_verified_from_actual_bound_loader"] is True,"all real256x16x4 originalQKV independently consumed")
            require(payload(ctl)==rawpayload,"actual whole payload after capture source lock");closure()
            result=dict(status="FULL_NATIVE_BASELINE_CAPTURE_CONSUMED_NOT_CALIBRATED",consumer=reference(out/"CAPTURE_CONSUMED.json"),consumer_cli=cr)
    except BaseException as e:ctl.primary=e
    finally:
        try:ctl.cleanup()
        except BaseException as e:ctl.secondary.append("cleanup persistence/observer: "+repr(e))
        terminal=dict(schema="SKVQ_HOST_CAPTURE_RESULT_V1",status=result["status"] if result and not ctl.primary and not ctl.secondary else "FAILED",
          cpu_input_only=a.cpu_inputs_only,
          result=result,primary=repr(ctl.primary) if ctl.primary else None,secondary=ctl.secondary,
          source_lock=lock,current_clock=C.clock(),actual_payload=rawpayload,owned=ctl.owned,capspent=ctl.spend,
          elapsed_seconds=time.monotonic()-ctl.start,max_total_seconds=limit,cleanup_included_seconds=CLEANUP,actual_cleanup_spent_seconds=ctl.cleanup_spent,
          host_pid=os.getpid(),protected0_3=ctl.protected,actual_npu_observations=ctl.observations,
          formal_start_utc=None,formal_deadline_utc=None,portfolio_deadline_utc="2026-10-12T07:00:25Z",
          author_calibration_pending=True,packed_cache_and_service_pending=True,native_ready=False,model_ready=False,
          e2e32768_pending=True,MAIN_original_operation_consumer_pending=True)
        try:
            r=publish_json(out/"HOST_RESULT.json",terminal);print(json.dumps(dict(host_result=r,status=terminal["status"])))
        except BaseException as e:
            print(json.dumps(dict(original_terminal=terminal,secondary_terminal_persistence=repr(e))),flush=True)
            if ctl.primary:raise ctl.primary
            raise
    if ctl.primary:raise ctl.primary
    require(not ctl.secondary,"secondary cleanup failures cannot promote")
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true");p.add_argument("--output",type=Path);p.add_argument("--source-manifest-sha256");p.add_argument("--cpu-inputs-only",action="store_true");a=p.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,native_ready=False,model_launched=False)));return
    require(a.output,"explicit absent new output");execute(a)
if __name__=="__main__":main()

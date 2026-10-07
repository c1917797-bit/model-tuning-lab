#!/usr/bin/env python3
"""MAIN-only joint B1/physical5 + B16/physical6 producer. Default OFF, kernel-only."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,os,re,shutil,subprocess,sys,time
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab")
HERE=ROOT/"projects/kvbuffer-parallel-ascend/tools/full_matrix_host_v2"
OLD=ROOT/"projects/kvbuffer-parallel-ascend/tools/saved_step_native_order_v2/host_run.py"
OLD_SHA="86c1ca7f59c6ad5b2b4d5efb155394455a12376cf368e06f9e2e13d39b7192fc"
SOURCE_REF={"path":str(ROOT/"projects/kvbuffer-parallel-ascend/tools/split_gate_v2/SOURCE_MANIFEST.json"),
 "sha256":"508ff442ede945b8fb5930f79ee597ec1dba07e5d4e778d9abc85aafda6ce9c9"}
BUILD=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006/build-native-order-v2-20261007-0924")
REFS={
 "library":{"path":str(BUILD/"build/libqwen36_gdn_kvbuffer_native_order_v2_ops.so"),"sha256":"77b4d61f94b4a8747bd08d2223b11d87702b43186acfd2f1b2e220f7b64a065c"},
 "build":{"path":str(BUILD/"build-receipt.json"),"sha256":"ff4c4a22ccf3e03d57baf08d59d6494e0f1435c74fbd132bbba1e98850e30dd8"},
 "meta":{"path":str(BUILD/"meta-report-format-v2.json"),"sha256":"fb765a5389ad97464597f16a43915440a46b654b3419d86a9894692d487592ee"}}
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
OUTROOT=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006/full-native-order-v2-20261007-1010")
ARMS={"b1":{"batch":1,"physical":5,"name":"kvbuffer_full_native_v2_b1_20261007_1010"},
      "b16":{"batch":16,"physical":6,"name":"kvbuffer_full_native_v2_b16_20261007_1010"}}
OWNER="kvbuffer-full-matrix-native-v2"
MEM=8*1024**3
RESERVE=8*1024**3
PHASE_SECONDS=5400
CLEANUP_SECONDS=90
CUTOFF=datetime.fromisoformat("2026-10-08T08:29:54+00:00")
DOCKER="/usr/bin/docker";SMI="/usr/local/sbin/npu-smi"
_LEGACY=None
_CLEANUP_DEADLINE=None
def require(v,why):
    if not v:raise ValueError(why)
def sha(path):
    p=Path(path);require(p.is_file() and not p.is_symlink(),"ordinary exact source/evidence")
    return hashlib.sha256(p.read_bytes()).hexdigest()
def write(path,obj):
    with Path(path).open("x") as f:
        f.write(json.dumps(obj,indent=2,allow_nan=False)+"\n");f.flush();os.fsync(f.fileno())
    return {"path":str(path),"sha256":sha(path)}
def checked_ref(r):
    require(type(r) is dict and set(r)=={"path","sha256"} and type(r["path"]) is str and
            Path(r["path"]).is_absolute() and ".." not in Path(r["path"]).parts and
            re.fullmatch("[0-9a-f]{64}",r["sha256"]) is not None,"exact absolute Ref")
    require(sha(r["path"])==r["sha256"],"Ref changed")
    return Path(r["path"]).read_bytes()
def legacy():
    global _LEGACY
    require(sha(OLD)==OLD_SHA,"frozen saved-step helper drift")
    if _LEGACY is None:
        spec=importlib.util.spec_from_file_location("_kvbp_full_matrix_frozen_host",OLD)
        _LEGACY=importlib.util.module_from_spec(spec);spec.loader.exec_module(_LEGACY)
    return _LEGACY
def sources(manifest_sha):
    ref={"path":str(HERE/"SOURCE_MANIFEST.json"),"sha256":manifest_sha}
    m=json.loads(checked_ref(ref))
    require(m.get("schema")=="kvbp.full-matrix-host-sources/v2" and
            m.get("default_enabled") is False and m.get("npu_executed") is False and
            m.get("source64")==SOURCE_REF and m.get("artifact_refs")==REFS and
            m.get("frozen_host")=={"path":str(OLD),"sha256":OLD_SHA} and
            set(m.get("files",{}))=={"host.py","test_host.py","READY.md"},"exact NEW producer closure")
    own={str(HERE/n):sha(HERE/n) for n in m["files"]}
    require(own=={str(HERE/n):h for n,h in m["files"].items()},"producer source drift")
    c,r,old_m,s=legacy().source()
    require(r==SOURCE_REF and len(s)==64 and legacy().REFS==REFS,"unchanged exact64/native artifacts")
    c.artifacts(REFS,old_m)
    return c,r,old_m,s,ref,own
def run(argv,timeout=30):return legacy().run(argv,timeout)
def write_raw(path,data):
    require(type(data) is bytes,"raw evidence bytes only")
    with Path(path).open("xb") as f:f.write(data);f.flush();os.fsync(f.fileno())
    return {"path":str(path),"sha256":sha(path)}
def capture(out,label,argv,timeout=30):
    v=run(argv,timeout);r=write(out/(label+"-"+str(time.time_ns())+".json"),v)
    require(v["exit_code"]==0,"command failed; original retained: "+label)
    return v,r
def utc():return datetime.now(timezone.utc)
def start_ticks(text):
    # /proc/PID/stat field22; comm may contain spaces or parentheses.
    tail=text[text.rfind(")")+2:].split()
    require(len(tail)>19,"complete actual proc stat")
    return int(tail[19])
def process_identity(pid):
    base=Path("/proc")/str(pid)
    return {"pid":pid,"start_ticks":start_ticks((base/"stat").read_text()),
            "cgroup":(base/"cgroup").read_text(),
            "cmdline_sha256":hashlib.sha256((base/"cmdline").read_bytes()).hexdigest()}
def protected(text):
    return sorted([{"physical":n,"chip":ch,**process_identity(pid)}
                  for n,ch,pid in legacy().process_rows(text) if n in (0,1,2,3)],
                  key=lambda v:(v["physical"],v["chip"],v["pid"]))
def gate_process(pid):
    proof=process_identity(pid);base=Path("/proc")/str(pid)
    proof["argv"]=[x.decode() for x in (base/"cmdline").read_bytes().split(b"\0") if x]
    rows=[l for l in (base/"status").read_text().splitlines() if l.startswith("NSpid:")]
    require(len(rows)==1,"actual namespace PID observation")
    proof["namespace_pids"]=[int(x) for x in rows[0].split()[1:]]
    require(proof["namespace_pids"] and proof["namespace_pids"][0]==pid,"host actual namespace PID")
    return proof
def protected_receipt(out,label,text):
    values=protected(text)
    processes={str(n):[{k:v for k,v in row.items() if k not in ("physical","chip")}
                        for row in values if row["physical"]==n] for n in range(4)}
    return write(out/(label+".json"),{"schema":"kvbp.native-order-protected-processes/v2",
           "observed_ns":time.time_ns(),"processes":processes}),processes
def resource_floor(memory,ncpu,disk):
    require(memory>=2*MEM+RESERVE,"joint16GiB + unchanged8GiB ordinary reserve")
    require(ncpu>=4,"joint2CPU + unchanged2CPU reserve")
    require(disk>=2*5*1024**3+RESERVE,"joint2x5GiB workspace + unchanged8GiB reserve")
    return {"ordinary_ram_floor":2*MEM+RESERVE,"cpu_floor":4,
            "disk_floor":2*5*1024**3+RESERVE,"full_model_floor_unchanged":72*1024**3}
def resources(out=None):
    fields={l.split(":")[0]:int(l.split()[1])*1024 for l in Path("/proc/meminfo").read_text().splitlines()
            if l.startswith(("MemTotal:","MemAvailable:","Hugetlb:"))}
    engine=run([DOCKER,"info","--format","{{json .}}"]);require(engine["exit_code"]==0,"actual engine")
    ncpu=json.loads(engine["stdout"])["NCPU"];disk=shutil.disk_usage(OUTROOT.parent).free
    resource_floor(fields["MemAvailable"],ncpu,disk)
    require(len(Path("/proc/1/mountinfo").read_text().splitlines())<95000,"unchanged mount reserve")
    value={"memory":fields,"engine":engine,"disk_free":disk,"budget":resource_floor(fields["MemAvailable"],ncpu,disk),
           "observed_utc":utc().isoformat(),"external_future_caps_guaranteed":False}
    return value,write(out/("resources-"+str(time.time_ns())+".json"),value) if out else None
def expected_devices(arm):
    return {"/dev/davinci"+str(ARMS[arm]["physical"]):"/dev/davinci0",
            "/dev/davinci_manager":"/dev/davinci_manager","/dev/devmm_svm":"/dev/devmm_svm",
            "/dev/hisi_hdc":"/dev/hisi_hdc"}
def expected_mounts(arm):
    old=legacy()
    mounts={str(p):(str(p),False) for p in
            (ROOT,BUILD,old.OLD_BUILD,old.OLD_GATE,OUTROOT,Path("/usr/local/Ascend/driver"))}
    mounts["/kvbuffer-results"]=(str(OUTROOT/arm),True)
    return mounts
def validate_inspect(x,cid,arm,joint_sha,own):
    cfg=ARMS[arm];h=x["HostConfig"];labels=x["Config"]["Labels"]
    require(x["Id"]==cid and re.fullmatch("[0-9a-f]{64}",cid) and x["Name"]=="/"+cfg["name"] and
            x["Image"]==IMAGE and labels.get("model-tuning-lab.owner")==OWNER and
            labels.get("model-tuning-lab.joint-sha256")==joint_sha and
            labels.get("model-tuning-lab.arm")==arm and labels.get("model-tuning-lab.run")==cfg["name"] and
            labels.get("model-tuning-lab.producer-sha256")==own[str(HERE/"host.py")] and
            h["Privileged"] is False and h["Memory"]==MEM and h["MemorySwap"]==MEM and
            h["NanoCpus"]==10**9 and h["NetworkMode"]=="none" and not h.get("DeviceRequests") and
            not h.get("DeviceCgroupRules") and h["PidsLimit"]==512 and
            set(h.get("CapDrop",[]))=={"ALL"} and
            set(h.get("SecurityOpt",[]))=={"no-new-privileges"},"exact sameJOINT owned/cgroup/security")
    ds=h["Devices"]
    require(len(ds)==4 and {d["PathOnHost"]:d["PathInContainer"] for d in ds}==expected_devices(arm) and
            all(d["CgroupPermissions"]=="rwm" for d in ds),"exact arm physical->logical0 map")
    ms=x["Mounts"]
    require(len(ms)==len(expected_mounts(arm)) and
            {v["Destination"]:(v["Source"],v["RW"]) for v in ms}==expected_mounts(arm) and
            all(v["Type"]=="bind" for v in ms),"exact full mount set")
    return x
def inspected(out,cid,arm,joint_sha,own,timeout=30):
    v,r=capture(out,"inspect",[DOCKER,"inspect",cid],timeout)
    x=json.loads(v["stdout"])[0];validate_inspect(x,cid,arm,joint_sha,own)
    raw_ref=write_raw(out/("inspect-raw-"+str(time.time_ns())+".json"),v["stdout"].encode())
    return x,raw_ref
def load_joint(path,digest,source_ref,s,producer_ref,own,now=None):
    r={"path":str(path),"sha256":digest};j=json.loads(checked_ref(r))
    require(Path(path)==OUTROOT/"JOINT.json" and j.get("schema")=="kvbp.full-matrix-joint/v2" and
            j.get("status")=="prepared-not-executed" and j.get("npu_executed") is False and
            j.get("source_manifest")==source_ref and j.get("sources")==s and
            j.get("producer_manifest")==producer_ref and j.get("producer_sources")==own and
            j.get("artifact_refs")==REFS and j.get("arms")==ARMS and j.get("image")==IMAGE and
            j.get("owner")==OWNER and j.get("output_root")==str(OUTROOT),"exact original JOINT bytes")
    require(j.get("phase_seconds")==PHASE_SECONDS and j.get("cleanup_seconds")==CLEANUP_SECONDS and
            j.get("cutoff_utc")==CUTOFF.isoformat() and j.get("budgets")==
            {"ram":2*MEM+RESERVE,"cpu":4,"disk":18*1024**3},"unchanged joint summed budget")
    receipt=json.loads(checked_ref(j["resource_receipt"]))
    require(receipt["protected0_3"]==j["protected0_3"] and
            receipt["smi"]["exit_code"]==0,"original fresh JOINT resource/protected receipt")
    rs=receipt["resources"]
    resource_floor(rs["memory"]["MemAvailable"],json.loads(rs["engine"]["stdout"])["NCPU"],rs["disk_free"])
    t=datetime.fromisoformat(j["prepared_utc"])
    n=now or utc();require(t.tzinfo is not None and 0<=(n-t).total_seconds()<=600,"fresh JOINT <=600s")
    require(n<CUTOFF and t+timedelta(seconds=PHASE_SECONDS+CLEANUP_SECONDS)<=CUTOFF,"fixed cutoff, no reset")
    return j,r
def arm_lease(arm,joint_ref,s,own):
    p=OUTROOT/arm/"OWNED.json"
    if not p.exists():return None
    require(not p.is_symlink(),"ordinary peer lease")
    v=json.loads(p.read_bytes());require(set(v)=={"schema","arm","cid","joint","sources","producer_sources",
            "image","owner","name","physical","targets"} and v["schema"]=="kvbp.full-matrix-owned/v2" and
            v["arm"]==arm and v["joint"]==joint_ref and v["sources"]==s and
            v["producer_sources"]==own and v["image"]==IMAGE and v["owner"]==OWNER and
            v["name"]==ARMS[arm]["name"] and v["physical"]==ARMS[arm]["physical"] and
            v["targets"]==[str(HERE/"host.py"),str(legacy().BASE/"run.py")] and
            re.fullmatch("[0-9a-f]{64}",v["cid"]) is not None,"exact committed peer lease")
    return v
def validate_pid(physical,chip,pid,arm,cid,top):
    require(physical==ARMS[arm]["physical"] and chip==0,"actual arm physical/chip")
    proof=gate_process(pid)
    require(cid in proof["cgroup"],"actual PID belongs to exact CID")
    targets=[str(HERE/"host.py"),str(legacy().BASE/"run.py")]
    line=next((l for l in top.splitlines() if l.split() and l.split()[0]==str(pid)),None)
    require(line is not None and any(t in line for t in targets),"actual owned target PID")
    return {"physical":physical,"chip":chip,**proof}
def idle_one(text,physical):
    rows=legacy().process_rows(text)
    require("No running processes found in NPU "+str(physical) in text and
            not any(n==physical for n,_,_ in rows),"unowned physical compute must be idle")
    lines=text.splitlines();ix=next((i for i,l in enumerate(lines)
          if re.match(r"\|\s*"+str(physical)+r"\s+910B4\s*\|",l)),None)
    require(ix is not None and "| OK " in lines[ix],"fresh physical health")
    parts=lines[ix+1].split("|");vals=parts[3].split()
    require(vals and vals[0]=="0" and re.search(r"\b28[0-9][0-9]\s*/\s*32768\b",parts[3]),
            "AICore/HBM idle baseline unchanged")
def observe(out,arm,joint,joint_ref,s,own,cid=None,target=None):
    v,smi_ref=capture(out,"smi",[SMI,"info"])
    require(protected(v["stdout"])==joint["protected0_3"],"protected0-3 original PID/start_ticks identity changed")
    proofs=[]
    for other in ARMS:
        lease=arm_lease(other,joint_ref,s,own)
        if not lease:
            idle_one(v["stdout"],ARMS[other]["physical"]);continue
        x,ir=inspected(out,lease["cid"],other,joint_ref["sha256"],own)
        actual=[(n,ch,pid) for n,ch,pid in legacy().process_rows(v["stdout"]) if n==ARMS[other]["physical"]]
        if not actual:continue # own committed lease may be starting/importing; no compute proof asserted
        require(x["State"]["Running"] and x["State"]["Pid"]>0 and not x["State"]["OOMKilled"],"live exact owned peer")
        top,tr=capture(out,"top",[DOCKER,"top",lease["cid"],"-eo","pid,ppid,args"])
        for n,ch,pid in actual:
            proof=validate_pid(n,ch,pid,other,lease["cid"],top["stdout"])
            if other==arm:
                require(cid==lease["cid"] and target is not None and any(
                    l.split() and l.split()[0]==str(pid) and target in l for l in top["stdout"].splitlines()),
                    "self actual current child target")
                proofs.append({**proof,"inspect":ir,"top":tr,"smi":smi_ref,"npu_smi":v["stdout"],"observed_utc":v["observed_utc"]})
    for physical in (4,7):idle_one(v["stdout"],physical)
    fields={l.split(":")[0]:int(l.split()[1])*1024 for l in Path("/proc/meminfo").read_text().splitlines()
            if l.startswith("MemAvailable:")}
    write(out/("resource-tick-"+str(time.time_ns())+".json"),{"MemAvailable":fields["MemAvailable"],
          "ordinary_reserve_bytes":RESERVE,"observed_ns":time.time_ns()})
    require(fields["MemAvailable"]>=RESERVE,"runtime unchanged ordinary8GiB reserve")
    require(shutil.disk_usage(out).free>=RESERVE,"runtime disk reserve")
    require(utc()<datetime.fromisoformat(joint["prepared_utc"])+timedelta(seconds=PHASE_SECONDS) and
            utc()<CUTOFF-timedelta(seconds=CLEANUP_SECONDS),"joint phase/cutoff elapsed; no retry")
    return proofs
def publish_lease(out,arm,cid,joint_ref,s,own):
    value={"schema":"kvbp.full-matrix-owned/v2","arm":arm,"cid":cid,"joint":joint_ref,
           "sources":s,"producer_sources":own,"image":IMAGE,"owner":OWNER,"name":ARMS[arm]["name"],
           "physical":ARMS[arm]["physical"],"targets":[str(HERE/"host.py"),str(legacy().BASE/"run.py")]}
    r=write(out/"OWNED.pending.json",value)
    os.link(r["path"],out/"OWNED.json") # exclusive atomic publication, pending original retained
    return {"path":str(out/"OWNED.json"),"sha256":sha(out/"OWNED.json")}
def cleanup_timeout(cap):
    global _CLEANUP_DEADLINE
    if _CLEANUP_DEADLINE is None:_CLEANUP_DEADLINE=time.monotonic()+CLEANUP_SECONDS
    remaining=_CLEANUP_DEADLINE-time.monotonic()
    require(remaining>0,"bounded cleanup90s elapsed; retain partial and original error")
    return min(cap,remaining)
def observed_child(out,cid,label,argv,target,limit,arm,joint,joint_ref,s,own):
    start=time.monotonic();proofs=[];p=None;primary=None;secondary=[];evidence=None
    stdout=out/(label+".stdout");stderr=out/(label+".stderr")
    with stdout.open("x") as so,stderr.open("x") as se:
        try:
            p=subprocess.Popen(argv,stdout=so,stderr=se,cwd=ROOT)
            while p.poll() is None:
                require(time.monotonic()-start<limit,"bounded child timeout; no automatic retry")
                rows=observe(out,arm,joint,joint_ref,s,own,cid,target)
                expected=argv[argv.index("/usr/local/python3.12.13/bin/python3"):]
                require(all(row["argv"]==expected for row in rows),"actual original image Python argv")
                proofs.extend(rows);time.sleep(1)
        except BaseException as e:primary=e
        finally:
            if p is not None:
                try:
                    if p.poll() is None:
                        inspected(out,cid,arm,joint_ref["sha256"],own,cleanup_timeout(30))
                        stop=run([DOCKER,"stop","--time","15",cid],cleanup_timeout(30))
                        secondary.append({"owned_stop_attempt":stop});p.wait(timeout=cleanup_timeout(30))
                except BaseException as e:
                    secondary.append({"cleanup_error":repr(e)})
                    if primary is None:primary=e
            try:
                evidence=write(out/(label+"-child.json"),{"argv":argv,
                    "exit_code":p.returncode if p is not None else None,"child_started":p is not None,
                    "child_termination_observed":p is not None and p.returncode is not None,
                    "stdout_ref":{"path":str(stdout),"sha256":sha(stdout)},
                    "stderr_ref":{"path":str(stderr),"sha256":sha(stderr)},"physical_pid_proofs":proofs,
                    "duration_seconds":time.monotonic()-start,"primary_error":repr(primary) if primary else None,
                    "secondary_cleanup":secondary})
            except BaseException as e:
                if primary is None:primary=e
                try:print(json.dumps({"primary":repr(primary),"secondary_child_evidence":repr(e)}),flush=True)
                except BaseException:pass
        if primary is not None:raise primary
        require(p.returncode==0,"real child failed; raw stdout/stderr retained")
        require(proofs,"missing actual workload physical/PID proof")
        return evidence
def prepare(a):
    c,r,m,s,pr,own=sources(a.producer_manifest_sha256)
    require(ROOT.resolve()==ROOT and OUTROOT.parent.is_dir() and not OUTROOT.exists() and
            not OUTROOT.is_symlink(),"fresh exact NEW joint output")
    now=utc();require(now+timedelta(seconds=PHASE_SECONDS+CLEANUP_SECONDS)<=CUTOFF,"fixed phase+cleanup cutoff")
    rs,_=resources()
    smi=run([SMI,"info"]);require(smi["exit_code"]==0,"fresh joint smi");legacy().idle(smi["stdout"])
    for arm in ARMS:
        old=run([DOCKER,"ps","-a","--filter","name=^/"+ARMS[arm]["name"]+"$","--format","{{.ID}}"])
        require(old["exit_code"]==0 and not old["stdout"].strip(),"unique exact arm name; no retry")
    prot=protected(smi["stdout"]);OUTROOT.mkdir()
    rr=write(OUTROOT/"resources-original.json",{"resources":rs,"smi":smi,"protected0_3":prot})
    j={"schema":"kvbp.full-matrix-joint/v2","status":"prepared-not-executed","npu_executed":False,
       "prepared_utc":now.isoformat(),"phase_seconds":PHASE_SECONDS,"cleanup_seconds":CLEANUP_SECONDS,
       "cutoff_utc":CUTOFF.isoformat(),"budgets":{"ram":2*MEM+RESERVE,"cpu":4,"disk":18*1024**3},
       "arms":ARMS,"source_manifest":r,"sources":s,"producer_manifest":pr,"producer_sources":own,
       "artifact_refs":REFS,"image":IMAGE,"owner":OWNER,"output_root":str(OUTROOT),
       "protected0_3":prot,"resource_receipt":rr,"future_external_resource_guarantee":False}
    joint_ref=write(OUTROOT/"JOINT.json",j)
    print(json.dumps({"joint":joint_ref,"status":j["status"],"npu_executed":False,
                      "MAIN_two_original_arm_operations_required":True}),flush=True)
def inside_canary(a):
    _,r,_,s,pr,own=sources(a.producer_manifest_sha256)
    j,jr=load_joint(a.joint,a.joint_sha256,r,s,pr,own)
    legacy().inside_canary() # original source-bound native arithmetic once; no candidate claim
    original={"path":"/kvbuffer-results/canary.json","sha256":sha("/kvbuffer-results/canary.json")}
    proof=json.loads(checked_ref(original))
    require(proof["status"]=="pass" and proof["host_launcher_sha256"]==OLD_SHA and proof["sources"]==s,
            "actual frozen native canary, not mock")
    native=write_raw(Path("/kvbuffer-results/native-library-readback.so"),Path(legacy().NATIVE).read_bytes())
    require(native["sha256"]==legacy().NATIVE_SHA,"actual native binary bytes")
    write(Path("/kvbuffer-results/canary-producer.json"),
          {"original_native_canary":original,"joint":jr,"producer_manifest":pr,"producer_sources":own,
           "arm":a.arm,"host_launcher_sha256":own[str(HERE/"host.py")],"status":"pass",
           "candidate_numerical_verified":False,"native_library":native})
def execute(a):
    c,r,m,s,pr,own=sources(a.producer_manifest_sha256)
    j,jr=load_joint(a.joint,a.joint_sha256,r,s,pr,own)
    arm=a.arm;out=OUTROOT/arm
    require(not out.exists() and not out.is_symlink(),"unique independent arm output")
    rs,_=resources();out.mkdir()
    rr=write(out/"resources-original.json",rs)
    observe(out,arm,j,jr,s,own)
    before_smi,bsr=capture(out,"protected-before",[SMI,"info"])
    pb,pids_before=protected_receipt(out,"protected-processes-before",before_smi["stdout"])
    require(protected(before_smi["stdout"])==j["protected0_3"],"actual original protected before")
    old=run([DOCKER,"ps","-a","--filter","name=^/"+ARMS[arm]["name"]+"$","--format","{{.ID}}"])
    write(out/"original-name-check.json",old)
    require(old["exit_code"]==0 and not old["stdout"].strip(),"no duplicate exact arm")
    cfg=ARMS[arm];argv=[DOCKER,"create","--name",cfg["name"],"--label","model-tuning-lab.owner="+OWNER,
       "--label","model-tuning-lab.joint-sha256="+jr["sha256"],"--label","model-tuning-lab.arm="+arm,
       "--label","model-tuning-lab.run="+cfg["name"],
       "--label","model-tuning-lab.producer-sha256="+own[str(HERE/"host.py")],
       "--network","none","--cap-drop","ALL","--security-opt","no-new-privileges",
       "--memory",str(MEM),"--memory-swap",str(MEM),"--cpus","1","--pids-limit","512",
       "--env","ASCEND_RT_VISIBLE_DEVICES=0","--env","TORCH_DEVICE_BACKEND_AUTOLOAD=0",
       "--env","PYTHONDONTWRITEBYTECODE=1","--env","OMP_NUM_THREADS=1"]
    for h,d in expected_devices(arm).items():
        require(Path(h).exists(),"actual device node");argv+=["--device",h+":"+d]
    for dst,(src,rw) in expected_mounts(arm).items():
        require(Path(src).is_dir(),"actual immutable bind root")
        argv+=["--mount","type=bind,src="+src+",dst="+dst+("" if rw else ",readonly")]
    argv+=["--workdir",str(ROOT),"--entrypoint","/bin/bash",IMAGE,"-c","exec sleep infinity"]
    created,_=capture(out,"create",argv);cid=created["stdout"].strip()
    require(re.fullmatch("[0-9a-f]{64}",cid),"exact actual created CID");primary=None
    report_ref=ident=original=None;release_ref=None;before_source=s;after_source=None
    actual_inspect=device_ref=None;runner_expected=None;native_ref=None
    try:
        inspected(out,cid,arm,jr["sha256"],own);lease=publish_lease(out,arm,cid,jr,s,own)
        capture(out,"start",[DOCKER,"start",cid])
        baseargs=[str(HERE/"host.py"),"--inside-canary","--arm",arm,"--joint",jr["path"],
                  "--joint-sha256",jr["sha256"],"--producer-manifest-sha256",pr["sha256"]]
        child=observed_child(out,cid,"canary",legacy().exec_argv(cid,baseargs),str(HERE/"host.py"),
                             120,arm,j,jr,s,own)
        cp={"path":str(out/"canary-producer.json"),"sha256":sha(out/"canary-producer.json")}
        proof=json.loads(checked_ref(cp));require(proof["status"]=="pass" and proof["joint"]==jr and
                    proof["producer_sources"]==own and proof["arm"]==arm,"actual native producer canary")
        _,ir=inspected(out,cid,arm,jr["sha256"],own);actual_inspect=ir
        raw_canary=json.loads(checked_ref(child))
        require(raw_canary["physical_pid_proofs"],"actual separate canary PID proof")
        first_canary=raw_canary["physical_pid_proofs"][0]
        canary_cgroup=write_raw(out/"canary-cgroup-original.txt",first_canary["cgroup"].encode())
        preflight_utc=utc().isoformat()
        device_ref=write(out/"device-proof.json",{"schema":"kvbp.native-order-device-binding/v2",
             "container_id":cid,"image_id":IMAGE,"physical_devices":[cfg["physical"]],
             "logical_to_physical":{"0":cfg["physical"]},"preflight_utc":preflight_utc,
             "separate_canary_not_gate":True,
             "raw_refs":{"canary":cp,"mapping":ir,"host_processes":first_canary["top"],"cgroup":canary_cgroup}})
        native_ref={"path":str(out/"native-library-readback.so"),"sha256":sha(out/"native-library-readback.so")}
        require(native_ref["sha256"]==legacy().NATIVE_SHA,"actual native external binary Ref")
        identity={"schema":"kvbp.split-launch-identity/v2","image_id":IMAGE,
           "protocol":c.protocol(cfg["batch"],cfg["physical"]),"physical_devices":[cfg["physical"]],
           "logical_to_physical":{"0":cfg["physical"]},"fresh_idle_verified":True,"nonprivileged":True,
           "source_canary_passed":True,"memory_cgroup_bytes":MEM,"source_manifest":r,"sources":s,
           "artifact_refs":REFS,"preflight_utc":preflight_utc,"joint":jr,"producer_sources":own,
           "evidence":{"resources":rr,"joint":jr,"lease":lease,"container_inspect":ir,"canary_child":child,
                       "canary":cp,"device_proof":device_ref}}
        ident=write(out/"identity.json",identity);c.validate_identity(identity,cfg["batch"],cfg["physical"],r,m,s,REFS)
        args=[str(legacy().BASE/"run.py"),"--execute","--batch",str(cfg["batch"]),
           "--physical-device",str(cfg["physical"]),"--source-manifest",r["path"],
           "--source-manifest-sha256",r["sha256"],"--identity",ident["path"],"--output-dir","/kvbuffer-results/gate"]
        for key,flag in (("library","library"),("build","build-receipt"),("meta","meta-receipt")):
            args+=["--"+flag,REFS[key]["path"],"--"+flag+"-sha256",REFS[key]["sha256"]]
        runner_expected=["/usr/local/python3.12.13/bin/python3","-B",*args]
        write(out/"MAIN-EXPECTATION-INPUT.json",{"container_id":cid,"owner":OWNER,"run_id":cfg["name"],
              "physical_device":cfg["physical"],"batches":[cfg["batch"]],"runner_argv":runner_expected})
        remaining=(datetime.fromisoformat(j["prepared_utc"])+timedelta(seconds=PHASE_SECONDS)-utc()).total_seconds()
        require(remaining>0,"original phase budget exhausted")
        original=observed_child(out,cid,"matrix",legacy().exec_argv(cid,args),str(legacy().BASE/"run.py"),
                                remaining,arm,j,jr,s,own)
        report_ref={"path":str(out/"gate/report.json"),"sha256":sha(out/"gate/report.json")}
        report=json.loads(checked_ref(report_ref));complete=c.validate_cases(report,cfg["batch"])
        _,_,_,after,_,own_after=sources(a.producer_manifest_sha256)
        require(after==s and own_after==own,"source drift during actual full matrix");after_source=after
        write(out/"RESULT.json",{"schema":"kvbp.full-matrix-arm-result/v2","status":report["status"],
            "joint":jr,"arm":arm,"original_child":original,"report":report_ref,"report_completeness":complete,
            "MAIN_operation_authority_verified":False,"e2e_verified":False,"task_accuracy_verified":False})
    except BaseException as e:
        primary=e
        try:write(out/"host-error.json",{"error":repr(e),"output":str(out),"container":cid,"joint":jr})
        except BaseException as secondary:
            try:print(json.dumps({"primary":repr(e),"secondary_host_evidence":repr(secondary)}),flush=True)
            except BaseException:pass
        raise
    finally:
        try:
            inspected(out,cid,arm,jr["sha256"],own,cleanup_timeout(30))
            capture(out,"stop",[DOCKER,"stop","--time","15",cid],cleanup_timeout(40))
            x,ir=inspected(out,cid,arm,jr["sha256"],own,cleanup_timeout(30))
            require(not x["State"]["Running"] and x["State"]["Pid"]==0 and not x.get("ExecIDs") and
                    not x["State"]["OOMKilled"],"own exact stopped/Pid0/noExec/noOOM")
            release_ref=ir
            write(out/"release.json",{"container":cid,"inspect":ir,"retained":True,"deleted":False,
                                      "pid":0,"no_exec":True,"no_oom":True,"joint":jr})
        except BaseException as e:
            try:print(json.dumps({"primary":repr(primary),"secondary_cleanup":repr(e)}),flush=True)
            except BaseException:pass
            if primary is None:raise
    # Marker publication only after real native cases, source checks and exact owned cleanup.
    require(report_ref is not None and release_ref is not None and original is not None,"actual completion only")
    after_smi,asr=capture(out,"protected-after-release",[SMI,"info"])
    pa,pids_after=protected_receipt(out,"protected-processes-after",after_smi["stdout"])
    require(protected(after_smi["stdout"])==j["protected0_3"] and pids_before==pids_after,
            "historical protected0-3 unchanged after actual cleanup")
    require(not any(n==cfg["physical"] for n,_,_ in legacy().process_rows(after_smi["stdout"])),"own actual card released")
    release_processes=write_raw(out/"release-processes-original.txt",after_smi["stdout"].encode())
    child_record=json.loads(checked_ref(original));pid_proofs=child_record["physical_pid_proofs"]
    require(child_record["exit_code"]==0 and child_record["child_termination_observed"] and
            child_record["primary_error"] is None and pid_proofs,"actual numerical child success only")
    gate_first,gate_last=pid_proofs[0],pid_proofs[-1]
    require(gate_first["pid"]==gate_last["pid"] and gate_first["start_ticks"]==gate_last["start_ticks"] and
            gate_first["argv"]==gate_last["argv"]==runner_expected,"actual gate waiting PID/argv continuity")
    actual_gate=write(out/"actual-gate-process.json",{"physical_card":cfg["physical"],
            "separate_canary_not_gate":True,"process":gate_first,"npu_smi":gate_first["npu_smi"]})
    waiting=write(out/"waiting-process.json",gate_last)
    all_producer={**own,str(OLD):OLD_SHA,str(legacy().REPLAY):legacy().REPLAY_SHA}
    final_child=write(out/"native-order-child.json",{"schema":"kvbp.native-order-child/v2",
        "evidence_kind":"actual-main-execution","report":report_ref,"identity":ident,
        "producer_sources":all_producer,"source_before":before_source,"source_after":after_source,
        "service_ready":False,"performance":False,
        "execution":{"command":DOCKER,"args":child_record["argv"][1:],"cwd":str(ROOT),
                     "exit_code":child_record["exit_code"],"error":None,"cancelled":False,"timed_out":False,
                     "stdout":child_record["stdout_ref"],"stderr":child_record["stderr_ref"]},
        "image_identity_path":ident["path"],"image_output_dir":"/kvbuffer-results/gate",
        "container_inspect":actual_inspect,"stopped_inspect":release_ref,"device_proof":device_ref,
        "actual_gate_process":actual_gate,"waiting_process":waiting,"release_processes":release_processes,
        "protected0_3":pids_before,"protected_processes_before":pb,"protected_processes_after":pa,
        "resource_refs":[rr,j["resource_receipt"],*[
            {"path":str(p),"sha256":sha(p)} for p in sorted(out.glob("resource-tick-*.json"))]],
        "native_library":native_ref,"cleanup":{"container_id":cid,"stopped":True,"retained":True,"deleted":False}})
    print("MAIN_KVBUFFER_NATIVE_ORDER_V2_CHILD "+json.dumps({"report":report_ref,"identity":ident,"child":final_child}),flush=True)
def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group();g.add_argument("--prepare",action="store_true")
    g.add_argument("--execute",action="store_true");g.add_argument("--inside-canary",action="store_true")
    g.add_argument("--source-audit-only",action="store_true")
    p.add_argument("--arm",choices=tuple(ARMS));p.add_argument("--joint",type=Path)
    p.add_argument("--joint-sha256");p.add_argument("--producer-manifest-sha256");a=p.parse_args(argv)
    if not any((a.prepare,a.execute,a.inside_canary,a.source_audit_only)):
        print(json.dumps({"default_enabled":False,"npu_executed":False,"serving_ready":False,
             "source64_fresh_check_pending":True,"output":str(OUTROOT),"scope":"B1/B16 isolated kernel matrix only"}));return
    require(a.producer_manifest_sha256 and re.fullmatch("[0-9a-f]{64}",a.producer_manifest_sha256),
            "explicit exact producer manifest SHA")
    if a.source_audit_only:
        _,_,_,s,_,own=sources(a.producer_manifest_sha256)
        print(json.dumps({"status":"source-only-not-execution","source_count":len(s),"producer_sources":own,
                          "npu_executed":False,"serving_ready":False}));return
    if a.prepare:
        require(not any((a.arm,a.joint,a.joint_sha256)),"prepare has no arm/future proof");prepare(a);return
    require(a.arm is not None and a.joint is not None and a.joint_sha256,"actual MAIN JOINTRef required")
    if a.inside_canary:inside_canary(a)
    else:execute(a)
if __name__=="__main__":main()

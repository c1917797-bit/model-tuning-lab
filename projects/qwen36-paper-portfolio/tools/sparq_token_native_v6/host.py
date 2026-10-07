"""MAIN-only SparQ native-state host owner, default OFF.
Reuse only exact frozen hardware/CPU/process/cleanup substrate; no H8 algorithm authority.
"""
from __future__ import annotations
import importlib.metadata,importlib.util,json,os,re,resource,sys,time
from datetime import datetime,timezone
from pathlib import Path
import receipt as c
from receipt import require,sha,bound,load,write_new,IMAGE
BASE=c.ROOT
ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab")
INTEGRATED=ROOT/"projects/qwen36-paper-portfolio/tools/sparq_token_native_v6"
H8=Path(next(iter(c.DEPENDENCIES)));H8_SHA=c.DEPENDENCIES[str(H8)]
OWNER=c.OWNER
DOCKER="/usr/bin/docker";PY="/usr/local/python3.12.13/bin/python3"
MEM=8*1024**3;HOST_MEM=256*1024**2;RESERVE=8*1024**3;WORKSPACE=5*1024**3
PHASE_SECONDS=5400;CLEANUP_SECONDS=90
CUTOFF=datetime.fromisoformat(c.CUT)
def utc():return datetime.now(timezone.utc)
def formal_time_failures(deadline):
 errors=[]
 if time.monotonic()>deadline:errors.append("formal whole phase5400 exhausted; safety-only recovery")
 if utc()>=CUTOFF:errors.append("fixed portfolio cutoff exhausted; safety-only recovery")
 return errors
def helpers():
 require(sha(H8)==H8_SHA,"actual reviewed generic H8 helper changed")
 spec=importlib.util.spec_from_file_location("_sparq_frozen_h8_host",H8)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 require(module.FROZEN_SHA==c.DEPENDENCIES[str(module.FROZEN)] and module.OLD_SHA==c.DEPENDENCIES[str(module.OLD)],"frozen dependency closure")
 return module
H=helpers()
def expected_devices(mode="npu"):
    require(mode in ("cpu","npu"),"explicit exact device phase")
    if mode=="cpu":return {}
    return {"/dev/davinci6":"/dev/davinci0","/dev/davinci_manager":"/dev/davinci_manager",
            "/dev/devmm_svm":"/dev/devmm_svm","/dev/hisi_hdc":"/dev/hisi_hdc"}
def labels(e):
    return {"model-tuning-lab.owner":OWNER,"model-tuning-lab.device-phase":e.get("mode","npu"),"model-tuning-lab.run":e["name"],
            "model-tuning-lab.source-manifest-sha256":e["source"]["sha256"],
            "model-tuning-lab.controller-sha256":e["host_sha256"],
            "model-tuning-lab.numeric-script-sha256":e["numeric_sha256"]}
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
    for host,guest in expected_devices(e.get("mode","npu")).items():argv+=["--device",host+":"+guest+":rwm"]
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
    devices=h.get("Devices") or []
    require(len(devices)==len(expected_devices(e.get("mode","npu"))) and {d["PathOnHost"]:d["PathInContainer"] for d in devices}==
        expected_devices(e.get("mode","npu")) and all(d["CgroupPermissions"]=="rwm" for d in devices),
        "single physical6 to logical0 and exact control-node map")
    mounts=x["Mounts"];want={dst:(src,bool(rw)) for dst,(src,rw) in e["mounts"].items()}
    require(len(mounts)==len(want) and all(m["Type"]=="bind" for m in mounts) and
        {m["Destination"]:(m["Source"],m["RW"]) for m in mounts}==want,
        "complete exact immutable inputs/new output mounts")


class Controller(H.Controller):
 def __init__(self,a):
  super().__init__(a)
  self.name="sparq-token-"+self.out.name
 def remaining(self,cleanup=False,cap=30):
  now=time.monotonic()
  if cleanup:
   # No new work/lease renewal: an already owned CID gets at most 90s safety
   # recovery even after the formal lease/cutoff failed. Failure remains latched.
   if self.cleanup_deadline is None:self.cleanup_deadline=now+CLEANUP_SECONDS
   value=self.cleanup_deadline-now
  else:value=min(self.deadline-now,(CUTOFF-utc()).total_seconds())-CLEANUP_SECONDS
  require(value>0,"fixed SparQ phase/cutoff and cleanup reserve exhausted")
  return min(cap,value)
 def call(self,label,argv,cap=30,cleanup=False):
  if not cleanup:return super().call(label,argv,cap=cap,cleanup=False)
  requested=list(argv)
  require(re.fullmatch("[0-9a-f]{64}",self.cid or "") and self.expected is not None and
   self.expected["cid"]==self.cid,"cleanup requires complete exact owned CID")
  identity=(self.cid,c.canonical(self.expected))
  permitted=(label=="inspect" and requested==[DOCKER,"inspect",self.cid])
  if label=="stop-retain":
   permitted=(requested==[DOCKER,"stop","--time","15",self.cid] and
    getattr(self,"_cleanup_owned_identity",None)==identity)
  if label=="release-smi":
   permitted=(requested==[H.SMI,"info"] and getattr(self,"_cleanup_owned_identity",None)==identity and
    getattr(self,"_cleanup_stopped",False))
  require(permitted,"cleanup-only inspect/exact validated stop-retain/release; no work or foreign stop")
  wrapped=self.wrapper(requested)
  try:result=self.h.run(wrapped,self.remaining(cleanup=True,cap=cap))
  except BaseException as error:
   result=dict(argv=wrapped,requested_argv=requested,exit_code=None,
    error=repr(error),observed_utc=utc().isoformat(),cleanup_safety_only=True)
   retained=H.write(self.out/(label+"-"+str(time.time_ns())+".json"),result)
   raise RuntimeError("command failure retained: "+str(retained)) from error
  own=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
  child=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
  violations=[]
  if own+child>HOST_MEM//1024:violations.append("actual host+CLI cumulative peak RSS exceeds256MiB")
  violations.extend(formal_time_failures(self.deadline))
  # Preserve the original resource/time failure as secondary, never hide it
  # behind successful stop. Do not rerun normal ordinary-RAM/CPU admission.
  for error in violations:
   if error not in self.secondary:self.secondary.append(error)
  result.update(requested_argv=requested,cleanup_safety_only=True,
   original_admission_failures=violations,
   cleanup_resource_snapshot=dict(host_peak_rss_kib=own,child_peak_rss_kib=child,
    aggregate_peak_rss_kib=own+child,formal_limit_bytes=HOST_MEM),
   cleanup_remaining_seconds=max(0,self.cleanup_deadline-time.monotonic()),
   formal_deadline_monotonic=self.deadline,formal_cutoff=CUTOFF.isoformat())
  retained=H.write(self.out/(label+"-"+str(time.time_ns())+".json"),result)
  require(result["exit_code"]==0,"actual command failed; retained "+str(retained))
  return result,retained
 def mounts(self,artifacts=None):
  # Same absolute source/evidence paths are readable in image and host.
  # Only the distinct owned /sparq-results alias is writable.
  mounts={str(ROOT):(str(ROOT),False),"/usr/local/Ascend/driver":("/usr/local/Ascend/driver",False),
    str(self.out):(str(self.out),False),"/sparq-results":(str(self.out),True)}
  require(BASE==INTEGRATED,"MAIN integrates complete reviewed independent packet before dispatch")
  return mounts
 def inspect(self,cleanup=False):
  raw,r=self.call("inspect",[DOCKER,"inspect",self.cid],cleanup=cleanup)
  rows=json.loads(raw["stdout"]);require(len(rows)==1,"single complete exact owned CID")
  validate_inspect(rows[0],self.expected)
  if cleanup:
   self._cleanup_owned_identity=(self.cid,c.canonical(self.expected))
   self._cleanup_stopped=(not rows[0]["State"]["Running"] and rows[0]["State"]["Pid"]==0 and not rows[0].get("ExecIDs"))
  return rows[0],r
 def create_owned(self,source):
  # Creation is NOT cleanup admission. Existing fresh observe/resources and
  # name/mount/device checks remain in create(); normal time/RSS gates stay.
  require(self.cid is None and self.expected is not None and self.expected["cid"] is None and
   source["host.py"]==sha(__file__) and self.expected["host_sha256"]==source["host.py"] and
   self.expected["numeric_sha256"]==source["numeric_gate.py"],"one fresh source-bound create only")
  requested=create_argv(self.expected);wrapped=self.wrapper(requested)
  self.rss()
  try:result=self.h.run(wrapped,self.remaining(cleanup=False,cap=60))
  except BaseException as error:
   result=dict(argv=wrapped,requested_argv=requested,exit_code=None,error=repr(error),observed_utc=utc().isoformat())
   retained=write_new(self.out/("create-"+str(time.time_ns())+".json"),result)
   raise RuntimeError("create command failure retained: "+str(retained)) from error
  result.update(requested_argv=requested)
  cid=result["stdout"].strip() if isinstance(result.get("stdout"),str) else None
  valid=(result.get("exit_code")==0 and re.fullmatch("[0-9a-f]{64}",cid or "") is not None)
  # Capture completed CLI's exact success CID BEFORE persistence/post-admission
  # can fail. Cleanup still requires full inspect/source ownership, not this CID alone.
  if valid:self.cid=cid;self.expected["cid"]=cid
  retained=write_new(self.out/("create-"+str(time.time_ns())+".json"),result)
  require(result.get("exit_code")==0,"actual create failed; retained "+str(retained))
  require(valid,"complete actual created CID; retained "+str(retained))
  write_new(self.out/"OWNED.json",dict(schema="sparq.token-owned/v4",**self.expected,create_receipt=retained,sources=source))
  # A successful create never bypasses resource/time admission or authorizes
  # start on failure; only exact validated safety stop remains available.
  self.rss();self.remaining(cleanup=False,cap=60)
  return result,retained
 def create(self,artifacts,source_ref,source):
  self.expected=dict(cid=None,name=self.name,image=IMAGE,owner=OWNER,source=source_ref,
    host_sha256=sha(__file__),numeric_sha256=source["numeric_gate.py"],guest_cpu=self.cpu["guest_cpu"],mounts=self.mounts(),mode=getattr(self,"device_phase","npu"))
  require(re.fullmatch("[A-Za-z0-9_-]{1,100}",self.name),"bounded unique container name")
  old,_=self.call("unique-name",[DOCKER,"ps","-a","--filter","name=^/"+self.name+"$","--format","{{.ID}}"])
  require(not old["stdout"].strip(),"exact name exists; never reuse or retry")
  for src,rw in self.expected["mounts"].values():require(Path(src).exists(),"actual exact mount source absent")
  for path in expected_devices(self.expected["mode"]):require(Path(path).exists(),"actual authorized device absent")
  created,cr=self.create_owned(source)
  cid=self.cid
  x,ir=self.inspect();require(not x["State"]["Running"] and x["State"]["Pid"]==0 and not x.get("ExecIDs"),"fresh owned CID unexpectedly live")
  self.call("start",[DOCKER,"start",cid],cap=60)
  x,ir=self.inspect();require(x["State"]["Running"] and x["State"]["Pid"]>0,"fresh exact owned init not live")
  guest=H.cpu_view(x["State"]["Pid"])
  require(guest["effective_capacity"]==1 and guest["effective_cpus"]==[self.cpu["guest_cpu"]],"actual guest cgroup CPU quota/cpuset")
  write_new(self.out/"guest-cgroup-cpu.json",guest)
  return ir
class CPUController(Controller):
 def __init__(self,a):
  super().__init__(a);self.device_phase="cpu";self.name="sparq-cpu-"+self.out.parent.name
def source_flags(a):
 return ["--source-manifest",str(a.source_manifest),"--source-manifest-sha256",a.source_manifest_sha256]
def host_argv(a):
 return ["/usr/bin/python3","-B",str(INTEGRATED/"numeric_gate.py"),"--host-execute",*source_flags(a),"--output",str(a.output_dir)]
def numerical_args(a,proof):
 return c.image_argv(BASE,Path("/sparq-results/gate"),proof,{"path":str(a.source_manifest),"sha256":a.source_manifest_sha256})[2:]
def translate(r,out):
 p=Path(r["path"]);root=Path("/sparq-results")
 require(root in p.parents and ".." not in p.parts,"original producer-owned image output path")
 hp=out/p.relative_to(root);require(hp.resolve()==hp and hp.is_file() and not hp.is_symlink(),"exact mapped original output")
 return bound(hp,r["sha256"])
def canary_version(text):
 rows=re.findall(r'(?im)^\s*(?:version|cann_version)\s*[:=]\s*["\x27]?([0-9]+\.[0-9]+\.[0-9]+(?:[._+\-][A-Za-z0-9.]+)?)',text)
 require(rows and len(set(rows))==1 and rows[0]=="9.1.0","actual install-info exact CANN9.1.0 required; path name is not a version receipt")
 return rows[0]
def cann_version_source():
 roots=(Path("/usr/local/Ascend/cann-9.1.0"),Path("/usr/local/Ascend/cann-9.1.0/aarch64-linux"),Path("/etc/Ascend"))
 candidates=[]
 for root in roots:
  if root.is_dir():
   candidates += list(root.glob("*install.info"))+list(root.glob("version.info"))+list(root.glob("version.cfg"))
 require(len(candidates)<=64,"bounded actual CANN metadata candidate inventory")
 matches=[]
 for path in sorted(set(candidates)):
  if path.is_file() and not path.is_symlink() and path.stat().st_size<=128*1024:
   try:version=canary_version(path.read_text())
   except (ValueError,UnicodeError):continue
   matches.append((path,version))
 require(matches,"actual exact CANN version metadata missing; no inferred version/PASS")
 return matches[0]
def snapshot(alias,path,host_root):
 require(re.fullmatch("[a-z0-9_]{1,64}",alias),"exact bounded snapshot alias")
 src=Path(path);require(src.is_absolute() and src.is_file() and not src.is_symlink(),"actual ordinary deployed source/native library")
 before=sha(src);dst=Path("/sparq-results/stack_snapshots")/(alias+".bin")
 with src.open("rb") as r,dst.open("xb") as w:
  for chunk in iter(lambda:r.read(1024*1024),b""):w.write(chunk)
  w.flush();os.fsync(w.fileno())
 require(sha(src)==before and sha(dst)==before,"runtime source/snapshot bytes changed")
 return {"runtime_ref":{"path":str(src),"sha256":before},
   "snapshot_ref":{"path":str(host_root/"stack_snapshots"/dst.name),"sha256":before}}
def inside_canary(a,source,files):
 require(a.host_output_root and a.host_output_root.is_absolute() and ".." not in a.host_output_root.parts and
   Path("/cache/cch") in a.host_output_root.parents and a.host_output_root.is_dir(),"exact owned host output absolute readonly alias")
 require(os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD")=="0" and os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0" and os.environ.get("PYTHONDONTWRITEBYTECODE")=="1","canary logical0/no bytecode")
 require(all(os.environ.get(k)=="1" for k in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS")) and len(os.sched_getaffinity(0))==1,"actual guest one CPU threads/affinity")
 from sparq_token_v4.proof import cgroup_memory
 cg=cgroup_memory();vp,version=cann_version_source()
 require(a.native_abi and a.native_abi_sha256,"bound original no-device ABI required before canary init")
 abi_ref=bound(a.native_abi,a.native_abi_sha256);abi=c.load(abi_ref)
 import torch,torch_npu
 from preflight import recheck_preinit
 recheck_preinit(torch,torch_npu,abi,source,files)
 from vllm_ascend.utils import enable_custom_op
 from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton
 torch.set_num_threads(1);torch_npu.npu.set_compile_mode(jit_compile=False);torch.npu.set_device(0)
 require(torch.npu.device_count()==1 and torch.npu.current_device()==0,"actual canary physical6-only logical0")
 require(enable_custom_op(),"actual native bootstrap");init_device_properties_triton()
 value=torch.tensor([1.,2.,3.],device="npu",dtype=torch.float32)*2;torch.npu.synchronize()
 require(value.cpu().tolist()==[2.,4.,6.],"fresh tiny canary actual arithmetic, not candidate numerical gate")
 pkg=importlib.util.find_spec("vllm_ascend")
 require(pkg is not None and pkg.submodule_search_locations and len(pkg.submodule_search_locations)==1,"actual installed Ascend package root")
 cp=Path(pkg.submodule_search_locations[0])/"attention/context_parallel"
 native=Path(torch_npu._C.__file__)
 mapped={line.split()[-1] for line in Path("/proc/self/maps").read_text().splitlines() if len(line.split())>=6}
 require(str(native) in mapped and native.suffix==".so","actual TorchNPU native mapped ABI library")
 require(str(H.NATIVE) in mapped and sha(H.NATIVE)==H.NATIVE_SHA,"same exact image mapped vllm native bootstrap")
 stack={"vllm_ascend":importlib.metadata.version("vllm-ascend"),"torch_npu":torch_npu.__version__,"torch":torch.__version__,"cann":version}
 require(stack["vllm_ascend"]=="0.23.0","actual installed v0.23.0 exact package")
 out=Path("/sparq-results");snap=out/"stack_snapshots";snap.mkdir(exist_ok=False)
 refs={alias:snapshot(alias,path,a.host_output_root) for alias,path in (
   ("device_operator","/vllm-workspace/vllm-ascend/vllm_ascend/device/device_op.py"),("torch_npu_library",native),
   ("vllm_ascend_library",H.NATIVE),("cann_version",vp),("cann_env","/usr/local/Ascend/cann-9.1.0/set_env.sh"))}
 _,after=c.source_identity(BASE,a.source_manifest,a.source_manifest_sha256,"runtime");require(files==after,"actual canary full12-source before/after")
 r=write_new(out/"canary.json",{"schema":"sparq.token-canary/v4","fresh_canary_passed":True,
   "candidate_numerical_verified":False,"serving_ready":False,"pid":os.getpid(),"image_id":IMAGE,
   "source_manifest":source,"sources_before":files,"sources_after":after,"memory_cgroup_bytes":MEM,"cgroup":cg,
   "stack":stack,"stack_source_refs":refs,"native_no_device_abi":abi_ref,"preinit_actual_exports":abi["actual_exports"],"script_sha256":sha(__file__),"created_utc":utc().isoformat()})
 print("MAIN_SPARQ_TOKEN_V5_CANARY "+json.dumps({"canary":r,"candidate_numerical_verified":False}),flush=True)
 time.sleep(30) # Actual PID observation window only, never candidate timing.
def make_device_proof(fields):
 """Same actual producer used by dispatch and source-bound stdlib regression; not an authority writer."""
 require(type(fields) is dict and fields["container_inspect"]["Config"]["Labels"].get("model-tuning-lab.owner")==c.OWNER,
  "single frozen source-bound owner shared by host and proof")
 owned=c.load(fields["cpu_only_owned"]);out=Path(owned["mounts"]["/sparq-results"][0])
 require(owned["mode"]=="cpu" and owned["mounts"]["/sparq-results"][1] is True and
  Path("/cache/cch") in out.parents and fields["native_no_device_abi"]["path"]==str(out/"ABI.json"),
  "proof CPU output root derives from source-bound actual owned mount, not ABI argv")
 require("cpu_host_output_root" not in fields,"producer alone derives CPU output identity")
 return dict(fields,cpu_host_output_root=str(out))
def execute(a,source,files):
 require(BASE==INTEGRATED and Path(__file__)==INTEGRATED/"host.py","MAIN integrates exact independent reviewed packet")
 require((CUTOFF-utc()).total_seconds()>=PHASE_SECONDS,"whole fixed5400s includes90cleanup before cutoff")
 require(a.output and a.source_manifest==INTEGRATED/"SOURCE_MANIFEST.json","explicit new host output/current source manifest")
 a.output_dir=a.output
 actual=[sys.executable,"-B",*sys.argv];expected=host_argv(a);require(actual==expected,"single frozen exact MAIN CLI")
 capacity=H.cpu_view(os.getpid());os.sched_setaffinity(0,{min(capacity["effective_cpus"])})
 soft,hard=resource.getrlimit(resource.RLIMIT_AS);require(hard==resource.RLIM_INFINITY,"Docker-only AS restoration needs inherited unlimited hard limit")
 resource.setrlimit(resource.RLIMIT_AS,(HOST_MEM,hard))
 H.fresh_output(a.output_dir);ctl=Controller(a)
 primary=None;numeric=None;complete=None;initial=None;canary=None;proof_ref=None;child_ref=None;after=None
 cleanup=None;protected_before=None;protected_after=None;stopped=None;abi_ref=None;abi_child=None;cpu_ctl=None;cpu_cleanup=None;cpu_inspect=None;cpu_stopped=None;probe_idle=None
 try:
  _,initial=ctl.observe("preflight",initial=True)
  protected_before=write_new(ctl.out/"protected-before.json",{"processes":H.protected_map(ctl.protected),"observation":initial})
  plan=write_new(ctl.out/"PLAN.json",{"schema":"sparq.token-host-plan/v4","source_manifest":source,"sources":files,"dependencies":c.DEPENDENCIES,
    "default_enabled":False,"MAIN_only_dispatch":True,"cutoff":c.CUT,"phase_seconds":PHASE_SECONDS,"cleanup_seconds":CLEANUP_SECONDS,"common_created_monotonic":ctl.created_monotonic,"common_deadline_monotonic":ctl.deadline,
    "guest_memory_bytes":MEM,"host_memory_bytes":HOST_MEM,"reserve_memory_bytes":RESERVE,"ordinary_floor_bytes":MEM+HOST_MEM+RESERVE,
    "guest_cpu_budget":1,"host_cpu_budget":1,"reserve_cpu_budget":2,"actual_cpu_allocation":ctl.cpu,"preflight":initial})
  cpu_out=ctl.out/"cpu-preflight";cpu_out.mkdir(exist_ok=False)
  cpu_ctl=CPUController(__import__("argparse").Namespace(output_dir=cpu_out))
  cpu_ctl.created_monotonic=ctl.created_monotonic;cpu_ctl.deadline=ctl.deadline
  cpu_ctl.cpu=ctl.cpu;cpu_ctl.protected=ctl.protected
  cpu_ctl.create({},source,files);_,cpu_inspect=cpu_ctl.inspect()
  # A real no-device source/exports/signature child MUST finish before canary.
  probe_args=c.abi_image_argv(BASE,source,cpu_out)[2:]
  abi_raw,abi_child=cpu_ctl.call("native-no-device",cpu_ctl.h.legacy().exec_argv(cpu_ctl.cid,probe_args),cap=120)
  abi_ref=bound(cpu_out/"ABI.json",sha(cpu_out/"ABI.json"));abi=c.load(abi_ref)
  require(abi["schema"]=="sparq.actual-no-device-abi/v5" and abi["source_manifest"]==source and abi["sources_before"]==abi["sources_after"]==files and
    abi["native_export_arguments_checked"] is True and abi["actual_source_import_checked"] is True and abi["script_sha256"]==files["preflight.py"] and
    abi["actual_device_initialized_before"] is False and abi["actual_device_initialized_after"] is False and abi["npu_executed"] is False,"actual BEFORE-device ABI/source prerequisite")
  from preflight import validate_abi
  validate_abi(abi,source,files)
  c.validate_cpu_abi_child(cpu_ctl.cid,cpu_out,source,c.load(abi_child),abi)
  markers=[line for line in abi_raw["stdout"].splitlines() if line.startswith("MAIN_SPARQ_TOKEN_V5_NO_DEVICE ")]
  require(len(markers)==1 and translate(json.loads(markers[0].split(" ",1)[1])["actual_abi"],cpu_out)==abi_ref,"original actual no-device stdout binds actual ABI bytes")
  cpu_cleanup=cpu_ctl.cleanup();cc=c.load(cpu_cleanup)
  require(cc["stopped"] is True and cc["retained"] is True and cc["deleted"] is False and cc["errors"]==[] and
   cc["primary_error"] is None and not cpu_ctl.secondary,"actual CPU-only exact stop-retain must precede new NPU guest")
  cpu_stopped=cc["after_inspect"]
  _,probe_idle=ctl.observe("post-no-device",initial=True)
  ctl.create({},source,files)
  canary_child=ctl.observed_child("canary",[str(BASE/"numeric_gate.py"),"--inside-canary",*source_flags(a),"--host-output-root",str(ctl.out),"--native-abi",abi_ref["path"],"--native-abi-sha256",abi_ref["sha256"]],120)
  canary=bound(ctl.out/"canary.json",sha(ctl.out/"canary.json"));cv=c.load(canary)
  require(cv["schema"]=="sparq.token-canary/v4" and cv["fresh_canary_passed"] is True and cv["candidate_numerical_verified"] is False and
    cv["sources_before"]==cv["sources_after"]==files and cv["source_manifest"]==source and cv["script_sha256"]==files["host.py"] and
    cv["native_no_device_abi"]==abi_ref and cv["preinit_actual_exports"]==abi["actual_exports"] and cv["pid"]==ctl.canary_proofs[-1]["namespace_pids"][-1],"fresh this-source owned canary, no H8 authority reuse")
  _,launch_observation=ctl.observe("launch-preflight")
  x,ir=ctl.inspect();resources=c.load(launch_observation)["resources"]
  guest=bound(ctl.out/"guest-cgroup-cpu.json",sha(ctl.out/"guest-cgroup-cpu.json"))
  proof=make_device_proof({"schema":"sparq.token-device-proof/v4","privileged":False,"container_id":ctl.cid,"container_inspect":x,"logical_to_physical":{"0":6},
    "physical_npu_ids":[6],"source_manifest":source,"sources":files,"observed_at_unix_ns":time.time_ns(),
    "exclusive_resource_check_passed":True,"fresh_resource_audit":{"actual_observation":launch_observation,"actual_resources":resources,"protected_before":protected_before},
    "actual_guest_cpu":c.load(guest),"native_no_device_abi":abi_ref,"native_no_device_child":abi_child,
    "canary":canary,"canary_child":canary_child,"cpu_container_id":cpu_ctl.cid,"cpu_only_inspect":cpu_inspect,
    "cpu_only_owned":bound(cpu_out/"OWNED.json",sha(cpu_out/"OWNED.json")),"cpu_only_cleanup":cpu_cleanup,"cpu_stopped_inspect":cpu_stopped,"actual_owned_inspect":ir,"plan":plan,"probe_idle":probe_idle})
  pending={"path":str(ctl.out/"proof.json"),"sha256":"@ACTUAL_DEVICE_PROOF_SHA256@"}
  proof["image_python_argv_template"]=[PY,"-B",*numerical_args(a,pending)]
  proof_ref=write_new(ctl.out/"proof.json",proof);args=numerical_args(a,proof_ref)
  from sparq_token_v4.proof import validate_proof
  validate_proof(proof_ref["path"],proof_ref["sha256"],source,files,[PY,"-B",*args])
  child_ref=ctl.observed_child("matrix",args,ctl.remaining(cap=5280))
  numeric=bound(ctl.out/"gate/REPORT.json",sha(ctl.out/"gate/REPORT.json"));report=c.load(numeric)
  require(report["source_manifest"]==source and report["sources_before"]==report["sources_after"]==files and
    report["device_proof"]==proof_ref and report["script_sha256"]==files["numeric_gate.py"] and report["native_no_device_abi"]==abi_ref,"actual producer/source/proof/ABI linkage")
  complete=c.validate_matrix(report,ctl.out/"gate")
  from receipt import marker
  child=c.load(child_ref);mk=marker(Path(child["stdout_ref"]["path"]).read_text())
  require(translate(mk["report"],ctl.out)==numeric and mk["source_manifest"]==source and mk["device_proof"]==proof_ref and
    mk["script_sha256"]==files["numeric_gate.py"] and mk["status"]=="passed","actual numerical child stdout -> complete immutable report")
 except BaseException as error:primary=error;ctl.primary=error
 finally:
  if cpu_ctl is not None and cpu_cleanup is None:
   cpu_ctl.primary=primary
   try:cpu_cleanup=cpu_ctl.cleanup();cpu_stopped=c.load(cpu_cleanup).get("after_inspect")
   except BaseException as error:ctl.secondary.append("CPU cleanup: "+repr(error))
   ctl.secondary.extend("CPU: "+s for s in cpu_ctl.secondary)
  try:cleanup=ctl.cleanup()
  except BaseException as error:ctl.secondary.append(repr(error))
  try:
   _,after=c.source_identity(BASE,a.source_manifest,a.source_manifest_sha256,"host");require(after==files,"actual full sources before/after")
  except BaseException as error:ctl.secondary.append(repr(error))
  try:
   if cleanup:
    cr=c.load(cleanup);stopped=cr.get("after_inspect")
    if cr.get("release_smi"):
     release=c.load(cr["release_smi"])
     protected_after=write_new(ctl.out/"protected-after.json",{"processes":H.protected_map(ctl.h.protected(release["stdout"])),"release_smi":cr["release_smi"]})
   if ctl.child is not None:
    done=ctl.child.poll() is not None
    write_new(ctl.out/"foreground-final.json",{"stage":ctl.child_label,"requested_argv":ctl.child_request,"host_pid":ctl.child.pid,"terminated":done,"exit_code":ctl.child.returncode if done else None})
  except BaseException as error:ctl.secondary.append(repr(error))
  # Final source/protected/foreground checks are part of the same whole5400.
  # Safety-only release never grants a new numerical lease or successful result.
  for error in formal_time_failures(ctl.deadline):
   if error not in ctl.secondary:ctl.secondary.append(error)
  success=primary is None and not ctl.secondary and all((numeric,complete,child_ref,cleanup,protected_after,stopped,proof_ref,abi_ref,cpu_cleanup,cpu_inspect,cpu_stopped,abi_child,probe_idle))
  result={"schema":"sparq.token-host-result/v4","status":"kernel_numerics_checked" if success else "failed","source_manifest":source,
    "sources_before":files,"sources_after":after,"dependencies":c.DEPENDENCIES,"container_id":ctl.cid,"source_device_proof":proof_ref,
    "native_no_device_abi":abi_ref,"native_no_device_child":abi_child,"cpu_container_id":cpu_ctl.cid if cpu_ctl else None,
    "cpu_only_inspect":cpu_inspect,"cpu_only_cleanup":cpu_cleanup,"cpu_stopped_inspect":cpu_stopped,
    "common_created_monotonic":ctl.created_monotonic,"common_deadline_monotonic":ctl.deadline,"producer_report":numeric,"numerical_child":child_ref,
    "actual_host_argv":actual,"expected_host_argv":expected,"actual_host_process":{"pid":os.getpid(),"argv":actual,
      "cmdline_sha256":__import__("hashlib").sha256(Path("/proc/self/cmdline").read_bytes()).hexdigest(),"stat":Path("/proc/self/stat").read_text(),"cgroup":Path("/proc/self/cgroup").read_text()},
    "host_script_sha256":files["host.py"],"entry_script_sha256":files["numeric_gate.py"],"output_dir":str(ctl.out),
    "actual_npu_python_process_proofs":[dict(p,borrowed_from_canary=False) for p in ctl.gate_proofs],
    "canary_process_proofs":ctl.canary_proofs,"canary":canary,"preflight":initial,"protected_before":protected_before,"protected_after":protected_after,
    "stopped_owned_inspect":stopped,"cleanup":cleanup,"phase_elapsed_seconds":time.monotonic()-ctl.created_monotonic,
    "primary_error":repr(primary) if primary else None,"secondary_errors":ctl.secondary,"report_completeness":complete,
    "default_enabled":False,"numerical_component_checked":bool(success),"MAIN_original_operation_authority_verified":False,
    "npu_executed":bool(ctl.canary_proofs or ctl.gate_proofs),"ready":False,"service_ready":False,"model_executed":False,
    "matched1024_e2e_verified":False,"final2048_task_verified":False}
  rr=write_new(ctl.out/"RESULT.json",result)
  print("MAIN_SPARQ_TOKEN_V5_HOST "+json.dumps({"result":rr,"status":result["status"],"source_manifest":source,
    "host_script_sha256":files["host.py"],"entry_script_sha256":files["numeric_gate.py"]}),flush=True)
 if primary is not None:raise primary
 require(not ctl.secondary,"secondary exact stop-retain/release/source failure: "+repr(ctl.secondary));require(success,"actual numerical result remains unready")

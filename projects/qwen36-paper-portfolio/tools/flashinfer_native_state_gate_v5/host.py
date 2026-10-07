"""MAIN-only FlashInfer native-state host owner, default OFF.
Reuse only exact frozen hardware/CPU/process/cleanup substrate; no H8 algorithm authority.
"""
from __future__ import annotations
import importlib.metadata,importlib.util,json,os,re,resource,sys,time
from datetime import datetime,timezone
from pathlib import Path
import contract as c
from contract import require,sha,bound,load_ref,write_new,IMAGE
BASE=c.ROOT
ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab")
INTEGRATED=ROOT/"projects/qwen36-paper-portfolio/tools/flashinfer_native_state_gate_v5"
H8=Path(next(iter(c.DEPENDENCIES)));H8_SHA=c.DEPENDENCIES[str(H8)]
OWNER="flashinfer-native-state-v5"
DOCKER="/usr/bin/docker";PY="/usr/local/python3.12.13/bin/python3"
MEM=8*1024**3;HOST_MEM=256*1024**2;RESERVE=8*1024**3;WORKSPACE=5*1024**3
PHASE_SECONDS=5400;CLEANUP_SECONDS=90
CUTOFF=datetime.fromisoformat(c.CUT)
def utc():return datetime.now(timezone.utc)
def helpers():
 require(sha(H8)==H8_SHA,"actual reviewed generic H8 helper changed")
 spec=importlib.util.spec_from_file_location("_flashinfer_frozen_h8_host",H8)
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
  self.name="flashinfer-state-"+self.out.name
 def remaining(self,cleanup=False,cap=30):
  now=time.monotonic();cut=(CUTOFF-utc()).total_seconds()
  if cleanup:
   if self.cleanup_deadline is None:self.cleanup_deadline=now+CLEANUP_SECONDS
   value=min(self.cleanup_deadline-now,self.deadline-now,cut)
  else:value=min(self.deadline-now,cut)-CLEANUP_SECONDS
  require(value>0,"fixed FlashInfer phase/cutoff and cleanup reserve exhausted")
  return min(cap,value)
 def mounts(self,artifacts=None):
  # Same absolute source/evidence paths are readable in image and host.
  # Only the distinct owned /flashinfer-results alias is writable.
  mounts={str(ROOT):(str(ROOT),False),"/usr/local/Ascend/driver":("/usr/local/Ascend/driver",False),
    str(self.out):(str(self.out),False),"/flashinfer-results":(str(self.out),True)}
  require(BASE==INTEGRATED,"MAIN integrates complete reviewed independent packet before dispatch")
  return mounts
 def inspect(self,cleanup=False):
  raw,r=self.call("inspect",[DOCKER,"inspect",self.cid],cleanup=cleanup)
  rows=json.loads(raw["stdout"]);require(len(rows)==1,"single complete exact owned CID")
  validate_inspect(rows[0],self.expected)
  return rows[0],r
 def create(self,artifacts,source_ref,source):
  self.expected=dict(cid=None,name=self.name,image=IMAGE,owner=OWNER,source=source_ref,
    host_sha256=sha(__file__),guest_cpu=self.cpu["guest_cpu"],mounts=self.mounts(),mode=getattr(self,"device_phase","npu"))
  require(re.fullmatch("[A-Za-z0-9_-]{1,100}",self.name),"bounded unique container name")
  old,_=self.call("unique-name",[DOCKER,"ps","-a","--filter","name=^/"+self.name+"$","--format","{{.ID}}"])
  require(not old["stdout"].strip(),"exact name exists; never reuse or retry")
  for src,rw in self.expected["mounts"].values():require(Path(src).exists(),"actual exact mount source absent")
  for path in expected_devices(self.expected["mode"]):require(Path(path).exists(),"actual authorized device absent")
  created,cr=self.call("create",create_argv(self.expected),cap=60)
  cid=created["stdout"].strip();require(re.fullmatch("[0-9a-f]{64}",cid),"complete actual created CID")
  self.cid=cid;self.expected["cid"]=cid
  write_new(self.out/"OWNED.json",dict(schema="flashinfer.native-state-owned/v5",**self.expected,create_receipt=cr,sources=source))
  x,ir=self.inspect();require(not x["State"]["Running"] and x["State"]["Pid"]==0 and not x.get("ExecIDs"),"fresh owned CID unexpectedly live")
  self.call("start",[DOCKER,"start",cid],cap=60)
  x,ir=self.inspect();require(x["State"]["Running"] and x["State"]["Pid"]>0,"fresh exact owned init not live")
  guest=H.cpu_view(x["State"]["Pid"])
  require(guest["effective_capacity"]==1 and guest["effective_cpus"]==[self.cpu["guest_cpu"]],"actual guest cgroup CPU quota/cpuset")
  write_new(self.out/"guest-cgroup-cpu.json",guest)
  return ir
class CPUController(Controller):
 def __init__(self,a):
  super().__init__(a);self.device_phase="cpu";self.name="flashinfer-cpu-"+self.out.parent.name
def source_flags(a):
 return ["--source-manifest",str(a.source_manifest),"--source-manifest-sha256",a.source_manifest_sha256]
def host_argv(a):
 return ["/usr/bin/python3","-B",str(INTEGRATED/"main.py"),"--host-execute",*source_flags(a),"--output-dir",str(a.output_dir)]
def numerical_args(a,launch):
 return [str(BASE/"main.py"),"--execute",*source_flags(a),"--launch-proof",launch["path"],
   "--launch-proof-sha256",launch["sha256"],"--output-dir","/flashinfer-results/gate"]
def translate(r,out):
 p=Path(r["path"]);root=Path("/flashinfer-results")
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
 before=sha(src);dst=Path("/flashinfer-results/stack_snapshots")/(alias+".bin")
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
 from main import cgroup_memory
 cg=cgroup_memory();vp,version=cann_version_source()
 require(a.no_device_abi_ref and a.no_device_abi_ref_sha256,"bound no-device ABI Ref mandatory before canary/device import")
 ndref=bound(a.no_device_abi_ref,a.no_device_abi_ref_sha256);nd=c.validate_no_device_abi(load_ref(ndref),source,files)
 import torch,torch_npu
 from native import verify_preinit
 preinit=verify_preinit(torch,torch_npu,nd)
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
 out=Path("/flashinfer-results");snap=out/"stack_snapshots";snap.mkdir(exist_ok=False)
 refs={alias:snapshot(alias,path,a.host_output_root) for alias,path in (
   ("attention_cp",cp/"attention_cp.py"),("common_cp",cp/"common_cp.py"),("torch_npu_library",native),
   ("vllm_ascend_library",H.NATIVE),("cann_version",vp),("cann_env","/usr/local/Ascend/cann-9.1.0/set_env.sh"))}
 require(stack==nd["actual_stack"] and all(nd["actual_runtime_sources"][alias]==pair["runtime_ref"] for alias,pair in refs.items()),"actual pre-device source/stack versus canary changed")
 _,after=c.source_identity(a.source_manifest,a.source_manifest_sha256);require(files==after,"actual canary full12-source before/after")
 r=write_new(out/"canary.json",{"schema":"flashinfer.native-state-canary/v5","fresh_canary_passed":True,
   "candidate_numerical_verified":False,"serving_ready":False,"pid":os.getpid(),"image_id":IMAGE,
   "source_manifest":source,"sources_before":files,"sources_after":after,"memory_cgroup_bytes":MEM,"cgroup":cg,
   "stack":stack,"stack_source_refs":refs,"no_device_abi":ndref,"preinit_actual_exports":preinit,"script_sha256":sha(__file__),"created_utc":utc().isoformat()})
 print("MAIN_FLASHINFER_NATIVE_STATE_V5_CANARY "+json.dumps({"canary":r,"candidate_numerical_verified":False}),flush=True)
 time.sleep(30) # Actual PID observation window only, never candidate timing.
def execute(a,source,files):
 require(BASE==INTEGRATED and Path(__file__)==INTEGRATED/"host.py","MAIN integrates exact reviewed independent packet first")
 require((CUTOFF-utc()).total_seconds()>=PHASE_SECONDS,"whole fixed5400s includes90cleanup before portfolio cutoff")
 require(a.output_dir and a.source_manifest==INTEGRATED/"SOURCE_MANIFEST.json","explicit new output and current integrated source manifest required")
 actual=[sys.executable,"-B",*sys.argv];expected=host_argv(a)
 require(actual==expected,"single frozen exact MAIN CLI; no wrapper/argv-substring authority")
 capacity=H.cpu_view(os.getpid());os.sched_setaffinity(0,{min(capacity["effective_cpus"])})
 soft,hard=resource.getrlimit(resource.RLIMIT_AS);require(hard==resource.RLIM_INFINITY,"Docker-only AS restoration needs unlimited inherited hard limit")
 resource.setrlimit(resource.RLIMIT_AS,(HOST_MEM,hard))
 H.fresh_output(a.output_dir);ctl=Controller(a)
 primary=None;numeric=None;complete=None;initial=None;canary=None;launch_ref=None;child_ref=None;after=None
 cleanup=None;protected_before=None;protected_after=None;stopped=None;ndref=None;ndchild=None;ndidle=None
 cpu_ctl=None;cpu_cleanup=None;cpu_inspect=None;cpu_stop_inspect=None;cpu_ended=None
 try:
  _,initial=ctl.observe("preflight",initial=True)
  protected_before=write_new(ctl.out/"protected-before.json",{"processes":H.protected_map(ctl.protected),"observation":initial})
  plan=write_new(ctl.out/"PLAN.json",{"schema":"flashinfer.native-state-host-plan/v5","source_manifest":source,"sources":files,
    "dependencies":c.DEPENDENCIES,"default_enabled":False,"MAIN_only_dispatch":True,"cutoff":c.CUT,
    "phase_seconds":PHASE_SECONDS,"cleanup_seconds":CLEANUP_SECONDS,"common_created_monotonic":ctl.created_monotonic,"common_deadline_monotonic":ctl.deadline,"guest_memory_bytes":MEM,
    "host_memory_bytes":HOST_MEM,"reserve_memory_bytes":RESERVE,"ordinary_floor_bytes":MEM+HOST_MEM+RESERVE,
    "guest_cpu_budget":1,"host_cpu_budget":1,"reserve_cpu_budget":2,"actual_cpu_allocation":ctl.cpu,"preflight":initial})
  cpu_out=ctl.out/"cpu-preflight";cpu_out.mkdir(exist_ok=False)
  cpu_args=__import__("argparse").Namespace(output_dir=cpu_out)
  cpu_ctl=CPUController(cpu_args);cpu_ctl.created_monotonic=ctl.created_monotonic;cpu_ctl.deadline=ctl.deadline
  cpu_ctl.cpu=ctl.cpu;cpu_ctl.protected=ctl.protected
  cpu_ctl.create({},source,files);_,cpu_inspect=cpu_ctl.inspect()
  ndargv=[str(BASE/"main.py"),"--no-device-abi",*source_flags(a),"--output-dir","/flashinfer-results"]
  ndraw,ndchild=cpu_ctl.call("no-device-abi",cpu_ctl.h.legacy().exec_argv(cpu_ctl.cid,ndargv),cap=120)
  ndref=bound(cpu_out/"NO_DEVICE_ABI.json",sha(cpu_out/"NO_DEVICE_ABI.json"))
  nd=c.validate_no_device_abi(load_ref(ndref),source,files)
  require(ndraw["requested_argv"]==cpu_ctl.h.legacy().exec_argv(cpu_ctl.cid,ndargv),"actual exact CPU-only original child argv")
  ndmarkers=[l for l in ndraw["stdout"].splitlines() if l.startswith("MAIN_FLASHINFER_NATIVE_STATE_V5_NO_DEVICE ")]
  require(len(ndmarkers)==1,"one original actual CPU-only no-device terminal marker")
  ndmarker=json.loads(ndmarkers[0].split(" ",1)[1])
  require(translate(ndmarker["no_device_abi"],cpu_out)==ndref and ndmarker["status"]=="actual-schema-checked" and
   ndmarker["source_manifest"]==source and ndmarker["entry_script_sha256"]==files["main.py"],"original CPU child binds actual ABI bytes")
  cpu_cleanup=cpu_ctl.cleanup();cc=load_ref(cpu_cleanup)
  require(cc["stopped"] is True and cc["retained"] is True and cc["deleted"] is False and cc["errors"]==[] and
   cc["primary_error"] is None and not cpu_ctl.secondary,"CPU exact owned stop-retain must finish before NPU create")
  cpu_stop_inspect=cc["after_inspect"];cpu_ended=utc().isoformat()
  _,ndidle=ctl.observe("post-no-device-idle",initial=True)
  # New NPU CID, SAME original whole phase/deadline. No overlap/two active8GiB guests.
  ctl.create({},source,files)
  canary_child=ctl.observed_child("canary",[str(BASE/"main.py"),"--inside-canary",*source_flags(a),"--host-output-root",str(ctl.out),"--no-device-abi-ref",ndref["path"],"--no-device-abi-ref-sha256",ndref["sha256"]],120)
  canary=bound(ctl.out/"canary.json",sha(ctl.out/"canary.json"));cv=load_ref(canary)
  require(cv["schema"]=="flashinfer.native-state-canary/v5" and cv["fresh_canary_passed"] is True and
    cv["candidate_numerical_verified"] is False and cv["sources_before"]==cv["sources_after"]==files and
    cv["source_manifest"]==source and cv["no_device_abi"]==ndref and cv["preinit_actual_exports"]==nd["actual_exports"] and cv["script_sha256"]==files["host.py"] and
    cv["pid"]==ctl.canary_proofs[-1]["namespace_pids"][-1],"fresh this-source owned actual canary, not H8/old authority")
  _,ir=ctl.inspect()
  pending={"path":str(ctl.out/"launch.json"),"sha256":None}
  # The launch argv includes its own file SHA, which would be cyclic.
  # Bind the explicit proof path in launch; SHA is separately frozen in child CLI/report.
  launch={"schema":"portfolio.native-device-launch/v1","image_id":IMAGE,"owner":OWNER,"container_id":ctl.cid,
    "physical_devices":[6],"logical_to_physical":{"0":6},"memory_cgroup_bytes":MEM,"guest_cpu_budget":1,
    "fresh_idle_verified":True,"source_canary_passed":True,"nonprivileged":True,"actual_effective_cgroup_cpu_verified":True,
    "cpu_container_id":cpu_ctl.cid,"source_manifest":source,"sources":files,"stack":cv["stack"],"stack_source_refs":cv["stack_source_refs"],
    "preflight_utc":utc().isoformat(),
    "launch_sha_binding":"separate immutable Ref in actual exact child CLI/report; no cyclic self-hash",
    "evidence":{"inspect":ir,"resources":initial,"protected":protected_before,"canary":canary,
      "canary_child":canary_child,"no_device_abi":ndref,"no_device_child":ndchild,"cpu_only_inspect":cpu_inspect,"cpu_only_owned":bound(cpu_out/"OWNED.json",sha(cpu_out/"OWNED.json")),"cpu_only_cleanup":cpu_cleanup,"cpu_stopped_inspect":cpu_stop_inspect,"post_no_device_idle":ndidle,"guest_cpu":bound(ctl.out/"guest-cgroup-cpu.json",sha(ctl.out/"guest-cgroup-cpu.json")),"plan":plan}}
  # The proof's exact argv field uses an explicit SHA placeholder, accepted only
  # at the single launch-proof-sha256 position after actual file Ref verification.
  args=numerical_args(a,{"path":pending["path"],"sha256":"@ACTUAL_LAUNCH_SHA256@"})
  launch["image_python_argv_template"]=[PY,"-B",*args]
  launch_ref=write_new(ctl.out/"launch.json",launch)
  actual_args=numerical_args(a,launch_ref)
  c.validate_launch(launch,source,files,[PY,"-B",*actual_args],launch_ref=launch_ref)
  child_ref=ctl.observed_child("matrix",actual_args,ctl.remaining(cap=5280))
  numeric=bound(ctl.out/"gate/report.json",sha(ctl.out/"gate/report.json"));report=load_ref(numeric)
  require(report["source_manifest"]==source and report["sources_before"]==report["sources_after"]==files and
    report["launch_proof"]==launch_ref and report["launch_identity"]==launch and
    report["script_sha256"]==files["main.py"] and report["no_device_abi"]==ndref and report["preinit_actual_exports"]==nd["actual_exports"],"actual complete source/report/launch identity")
  complete=c.validate_cases(report,read_case=lambda r:load_ref(translate(r,ctl.out)))
  from consumer import producer_marker
  marker=producer_marker(Path(load_ref(child_ref)["stdout_ref"]["path"]).read_text())
  require(translate(marker["report"],ctl.out)==numeric and marker["source_manifest"]==source and
    marker["launch_proof"]==launch_ref and marker["producer_script_sha256"]==files["main.py"] and marker["status"]=="passed","actual stdout/new-output immutable report linkage")
 except BaseException as error:primary=error;ctl.primary=error
 finally:
  # On first failure, each own exact CID keeps independent original/secondary errors.
  if cpu_ctl is not None and cpu_cleanup is None:
   cpu_ctl.primary=primary
   try:
    cpu_cleanup=cpu_ctl.cleanup();cc=load_ref(cpu_cleanup);cpu_stop_inspect=cc.get("after_inspect")
   except BaseException as error:ctl.secondary.append("CPU cleanup: "+repr(error))
   ctl.secondary.extend("CPU: "+s for s in cpu_ctl.secondary)
  try:cleanup=ctl.cleanup()
  except BaseException as error:ctl.secondary.append(repr(error))
  try:
   _,after=c.source_identity(a.source_manifest,a.source_manifest_sha256);require(after==files,"actual complete source before/after")
  except BaseException as error:ctl.secondary.append(repr(error))
  try:
   if cleanup:
    cr=load_ref(cleanup);stopped=cr.get("after_inspect")
    if cr.get("release_smi"):
     release=load_ref(cr["release_smi"])
     protected_after=write_new(ctl.out/"protected-after.json",{"processes":H.protected_map(ctl.h.protected(release["stdout"])),"release_smi":cr["release_smi"]})
   if ctl.child is not None:
    done=ctl.child.poll() is not None
    write_new(ctl.out/"foreground-final.json",{"stage":ctl.child_label,"requested_argv":ctl.child_request,
      "host_pid":ctl.child.pid,"terminated":done,"exit_code":ctl.child.returncode if done else None})
  except BaseException as error:ctl.secondary.append(repr(error))
  success=primary is None and not ctl.secondary and all((numeric,complete,child_ref,cleanup,protected_after,stopped,launch_ref,ndref,ndchild,ndidle,cpu_cleanup,cpu_inspect,cpu_stop_inspect))
  result={"schema":"flashinfer.native-state-host-result/v5","status":"kernel_numerics_checked" if success else "failed",
    "source_manifest":source,"sources_before":files,"sources_after":after,"dependencies":c.DEPENDENCIES,
    "container_id":ctl.cid,"source_launch_proof":launch_ref,"producer_report":numeric,"numerical_child":child_ref,
    "actual_host_argv":actual,"expected_host_argv":expected,"actual_host_process":{"pid":os.getpid(),
      "argv":actual,"cmdline_sha256":__import__("hashlib").sha256(Path("/proc/self/cmdline").read_bytes()).hexdigest(),
      "stat":Path("/proc/self/stat").read_text(),"cgroup":Path("/proc/self/cgroup").read_text()},
    "host_script_sha256":files["host.py"],"entry_script_sha256":files["main.py"],"output_dir":str(ctl.out),
    "actual_npu_python_process_proofs":[dict(p,borrowed_from_canary=False) for p in ctl.gate_proofs],
    "no_device_abi":ndref,"no_device_child":ndchild,"cpu_container_id":cpu_ctl.cid if cpu_ctl else None,"cpu_only_inspect":cpu_inspect,"cpu_only_cleanup":cpu_cleanup,"cpu_stopped_inspect":cpu_stop_inspect,"cpu_ended_utc":cpu_ended,"common_created_monotonic":ctl.created_monotonic,"common_deadline_monotonic":ctl.deadline,"post_no_device_idle":ndidle,"canary_process_proofs":ctl.canary_proofs,"canary":canary,"preflight":initial,"protected_before":protected_before,
    "protected_after":protected_after,"stopped_owned_inspect":stopped,"cleanup":cleanup,"phase_elapsed_seconds":time.monotonic()-ctl.created_monotonic,
    "primary_error":repr(primary) if primary else None,"secondary_errors":ctl.secondary,"report_completeness":complete,
    "default_enabled":False,"numerical_component_checked":bool(success),"MAIN_original_operation_authority_verified":False,
    "npu_executed":bool(ctl.canary_proofs or ctl.gate_proofs),"serving_ready":False,"model_lifecycle_verified":False,
    "native_scheduler_or_tiling_benefit_verified":False,"matched1024_e2e_verified":False,"final2048_task_verified":False}
  r=write_new(ctl.out/"RESULT.json",result)
  print("MAIN_FLASHINFER_NATIVE_STATE_V5_HOST "+json.dumps({"result":r,"status":result["status"],"source_manifest":source,
    "host_script_sha256":files["host.py"],"entry_script_sha256":files["main.py"]}),flush=True)
 if primary is not None:raise primary
 require(not ctl.secondary,"secondary exact stop-retain/release/source failure: "+repr(ctl.secondary))
 require(success,"actual numerical result remains unready")

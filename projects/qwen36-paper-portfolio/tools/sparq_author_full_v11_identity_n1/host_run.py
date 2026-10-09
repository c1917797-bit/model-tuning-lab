"""MAIN-only one-entry TP4 matched-screen/final-task controller, default OFF."""
from __future__ import annotations
import argparse,datetime,json,os,re,resource,shutil,stat,subprocess,time
from pathlib import Path
import service_contract as c
DOCKER="/usr/bin/docker";SMI="/usr/local/sbin/npu-smi";PRLIMIT="/usr/bin/prlimit"
MEM=64*c.GIB;HOST_MEM=256*1024**2;RESERVE=8*c.GIB;WORKSPACE=10*c.GIB
PHASE=5400;CLEANUP=90;OWNER="sparq-author-ann-fp32-stock-full-v3";PHYSICAL=(4,5,6,7)
H=c.module(c.H8,c.DEPS[str(c.H8)],"_sparq_tp4_frozen_host")
_NATIVE_BOUNDARY=None
def protected_boundary(before,after,owned_cids=(),owned_host_pids=()):
 global _NATIVE_BOUNDARY
 if _NATIVE_BOUNDARY is None:
  km=c.obj(dict(path=str(c.KERNEL/"SOURCE_MANIFEST.json"),sha256=c.KERNEL_SHA))
  # Exact new native source includes the source-reviewed protected observer repair.
  import sys
  original=list(sys.path)
  try:
   sys.path.insert(0,str(c.KERNEL))
   _NATIVE_BOUNDARY=c.module(c.KERNEL/"host.py",km["files"]["host.py"],"_sparq_full_new_boundary")
  finally:sys.path[:]=original
 return _NATIVE_BOUNDARY.protected_boundary(before,after,owned_cids,owned_host_pids)
def utc():return datetime.datetime.now(datetime.timezone.utc)
def formal_time_failures(deadline):
 errors=[]
 if time.monotonic()>deadline:errors.append("formal whole phase5400 exhausted; safety-only recovery")
 if utc()>=datetime.datetime.fromisoformat(c.CUT):errors.append("fixed portfolio cutoff exhausted; safety-only recovery")
 return errors
def device_map():
 x={"/dev/davinci%d"%p:"/dev/davinci%d"%i for i,p in enumerate(PHYSICAL)}
 x.update({"/dev/"+n:"/dev/"+n for n in ("davinci_manager","devmm_svm","hisi_hdc")});return x
def cpu_admission(host,daemon):
 c.require(host["effective_capacity"]>=1 and daemon["effective_capacity"]>=6,"actual host1/guest4/reserve2 quota")
 hc=min(host["effective_cpus"]);spare=sorted(set(daemon["effective_cpus"])-{hc})
 c.require(len(spare)>=6,"distinct host1/guest4/reserve2 cpusets")
 common={x["key"]:x["capacity"] for x in host["quota_ancestors"]}
 limits=[v for x in daemon["quota_ancestors"] if x["key"] in common for v in (x["capacity"],common[x["key"]]) if v is not None]
 c.require(not limits or min(limits)>=7,"shared finite ancestor quota must cover summed7CPU")
 return dict(host_cpu=hc,guest_cpus=spare[:4],reserve_cpus=spare[4:6],host_cpu_budget=1,guest_cpu_budget=4,reserve_cpu_budget=2,
  common_finite_capacity=min(limits) if limits else None)
def environment(cpu=False):
 return dict(ASCEND_RT_VISIBLE_DEVICES="" if cpu else "0,1,2,3",TORCH_DEVICE_BACKEND_AUTOLOAD="0",PYTHONDONTWRITEBYTECODE="1",
  OMP_NUM_THREADS="1",MKL_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",QWEN36_SPARQ_TOKEN_ENABLED="0",SPARQ_TP4_SERVICE="0",VLLM_DISABLE_REQUEST_ID_RANDOMIZATION="1")
def labels(e):
 return {"model-tuning-lab.owner":OWNER,"model-tuning-lab.run":e["name"],"model-tuning-lab.arm":e["arm"],
  "model-tuning-lab.source-manifest-sha256":e["source"]["sha256"],"model-tuning-lab.controller-sha256":e["host_sha256"]}
def create_argv(e):
 cpu=e["arm"]=="cpu-preflight";mem=8*c.GIB if cpu else MEM;cores=1 if cpu else 4
 args=[DOCKER,"create","--name",e["name"],"--network","none","--cap-drop","ALL","--security-opt","no-new-privileges",
  "--memory",str(mem),"--memory-swap",str(mem),"--cpus",str(cores),"--cpuset-cpus",",".join(map(str,e["guest_cpus"])),
  "--pids-limit","2048","--ipc","private","--shm-size",str(4*c.GIB),"--workdir",str(c.ROOT),"--entrypoint","/bin/bash"]
 for k,v in labels(e).items():args+=["--label",k+"="+v]
 for k,v in environment(cpu).items():args+=["--env",k+"="+v]
 for p,n in ({} if cpu else device_map()).items():args+=["--device",p+":"+n+":rwm"]
 for n,(p,rw) in e["mounts"].items():
  c.require("," not in p and "," not in n,"exact ordinary bind paths")
  args+=["--mount","type=bind,source="+p+",destination="+n+("" if rw else ",readonly")]
 return [*args,c.IMAGE,"-c","exec /bin/sleep infinity"]
def validate_inspect(x,e):
 c.require(x["Id"]==e["cid"] and re.fullmatch("[a-f0-9]{64}",e["cid"]) and x["Image"]==c.IMAGE and x["Name"]=="/"+e["name"],
  "full exact owned CID/image/name before any stop")
 h=x["HostConfig"];cfg=x["Config"];cpu=e["arm"]=="cpu-preflight";mem=8*c.GIB if cpu else MEM;cores=1 if cpu else 4
 c.require(cfg["Image"]==c.IMAGE and cfg["Entrypoint"]==["/bin/bash"] and cfg["Cmd"]==["-c","exec /bin/sleep infinity"] and
  cfg["WorkingDir"]==str(c.ROOT) and all(cfg["Labels"].get(k)==v for k,v in labels(e).items()),"owned exact source labels/init")
 env=cfg.get("Env") or []
 c.require(all(env.count(k+"="+v)==1 and sum(s.startswith(k+"=") for s in env)==1 for k,v in environment(cpu).items()),"no duplicated/drifted guest environment")
 c.require(h["Privileged"] is False and h["Memory"]==h["MemorySwap"]==mem and h["NanoCpus"]==cores*10**9 and
  h["CpusetCpus"]==",".join(map(str,e["guest_cpus"])) and h["IpcMode"]=="private" and h["NetworkMode"]=="none" and h["ShmSize"]==4*c.GIB and
  h["PidsLimit"]==2048 and not h.get("DeviceRequests") and not h.get("DeviceCgroupRules") and
  set(h.get("CapDrop") or [])=={"ALL"} and set(h.get("SecurityOpt") or [])=={"no-new-privileges"},"actual bounded isolated TP4 resources")
 dev=h.get("Devices") or []
 c.require(len(dev)==(0 if cpu else 7) and {d["PathOnHost"]:d["PathInContainer"] for d in dev}==({} if cpu else device_map()) and
  all(d["CgroupPermissions"]=="rwm" for d in dev),"only physical4..7 -> logical0..3, protected0..3 never mapped")
 mounts=x["Mounts"];want={n:(p,bool(rw)) for n,(p,rw) in e["mounts"].items()}
 c.require(len(mounts)==len(want) and all(m["Type"]=="bind" for m in mounts) and
  {m["Destination"]:(m["Source"],m["RW"]) for m in mounts}==want,"full exact immutable inputs/owned output mounts")
def fd_holders():
 devices={p:Path("/dev/davinci%d"%p).stat().st_rdev for p in PHYSICAL}
 found=[];procs=[p for p in Path("/proc").iterdir() if p.name.isdigit()];c.require(len(procs)<=16384,"bounded actual process inventory")
 for p in procs:
  try:
   fds=list((p/"fd").iterdir());c.require(len(fds)<=16384,"bounded actual FD inventory")
   hit=set()
   for fd in fds:
    try:
     target=os.readlink(fd)
     if re.fullmatch(r"/dev/davinci[0-9]+",target):
      s=fd.stat()
      if stat.S_ISCHR(s.st_mode):hit.update(k for k,v in devices.items() if s.st_rdev==v)
    except FileNotFoundError:continue
   if hit:found.append(dict(physical_devices=sorted(hit),**H.started(H.frozen().gate_process(int(p.name)))))
  except (FileNotFoundError,ProcessLookupError):continue
  except PermissionError:raise ValueError("actual4..7 UDA FD ownership unreadable; fail closed")
 return found
def actual_hbm(text,card):
 # npu-smi25.2 puts Memory and HBM in ONE third pipe segment.
 # Bind the exact header/order, then fullmatch both ratios; never search
 # the first ratio or guess a new pipe column from a different device format.
 c.require(type(card) is int and card in PHYSICAL,"actual owned physical4..7 only")
 lines=text.splitlines()
 headers=[l.split("|") for l in lines if re.match(r"\|\s*Chip\b",l)]
 c.require(len(headers)==1,"one actual Chip/Bus/AICore/Memory/HBM header")
 header=headers[0]
 c.require(len(header)==5 and not header[0].strip() and not header[4].strip() and
  header[1].strip()=="Chip" and header[2].strip()=="Bus-Id" and
  re.fullmatch(r"AICore\(%\)\s+Memory-Usage\(MB\)\s+HBM-Usage\(MB\)",header[3].strip()) is not None,
  "actual third-segment header AICore then Memory then HBM, units MB")
 indices=[i for i,l in enumerate(lines) if re.match(r"\|\s*"+str(card)+r"\s+910B4\s*\|",l)]
 c.require(len(indices)==1 and indices[0]+1<len(lines),"unique installed910B4 card and following chip row")
 health=lines[indices[0]].split("|")
 c.require(len(health)==5 and not health[0].strip() and not health[4].strip() and
  health[2].strip()=="OK","actual owned-card health OK")
 parts=lines[indices[0]+1].split("|")
 c.require(len(parts)==5 and not parts[0].strip() and not parts[4].strip() and parts[1].strip()=="0" and
  re.fullmatch(r"[0-9A-Fa-f]{4}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}\.[0-7]",parts[2].strip()) is not None,
  "complete actual chip0 Bus-Id and one metrics segment")
 match=re.fullmatch(r"\s*([0-9]+(?:\.[0-9]+)?)\s+([0-9]+)\s*/\s*([0-9]+)\s+([0-9]+)\s*/\s*([0-9]+)\s*",parts[3])
 c.require(match is not None,"actual AICore plus exactly Memory and HBM ratios; unknown schema rejected")
 core,mem_used,mem_total,used,total=match.groups()
 c.require(0<=float(core)<=100 and 0<=int(mem_used)<=int(mem_total),"finite actual AICore and Memory range")
 used,total=int(used),int(total)
 c.require(total==32768 and 0<=used<=total-c.HBM_RESERVE_MIB,
  "actual physical HBM reserve3GiB percard; include full weights/native/GDN/allaux/driver, no allocator simulation")
 return dict(physical=card,used_mib=used,total_mib=total,reserve_mib=c.HBM_RESERVE_MIB,full_actual_physical_hbm=True)
class Controller(H.Controller):
 def __init__(self,a,parent_start):
  super().__init__(a);self.name="sparq-tp4-"+self.out.parent.name+"-"+self.out.name
  self.created_monotonic=parent_start;self.deadline=parent_start+PHASE;self.server=None;self.client=None
  self.server_started=None;self.process_proofs=[];self.observations=[];self.server_argv=None;self.client_argv=None
 def remaining(self,cleanup=False,cap=30):
  now=time.monotonic()
  if cleanup:
   if self.cleanup_deadline is None:self.cleanup_deadline=now+CLEANUP
   value=self.cleanup_deadline-now
  else:value=min(self.deadline-now,(datetime.datetime.fromisoformat(c.CUT)-utc()).total_seconds())-CLEANUP
  c.require(value>0,"one whole5400 including90cleanup/fixed cutoff, never reset per arm")
  return min(cap,value)
 def call(self,label,argv,cap=30,cleanup=False):
  if not cleanup:return super().call(label,argv,cap=cap,cleanup=False)
  requested=list(argv)
  c.require(re.fullmatch("[0-9a-f]{64}",self.cid or "") and self.expected is not None and
   self.expected["cid"]==self.cid,"cleanup requires complete exact owned CID")
  identity=(self.cid,c.canonical(self.expected))
  permitted=(label=="inspect" and requested==[DOCKER,"inspect",self.cid])
  if label=="stop-retain":
   permitted=(requested==[DOCKER,"stop","--time","15",self.cid] and
    getattr(self,"_cleanup_owned_identity",None)==identity)
  if label=="release":
   permitted=(requested==[H.SMI,"info"] and getattr(self,"_cleanup_owned_identity",None)==identity and
    getattr(self,"_cleanup_stopped",False))
  c.require(permitted,"cleanup-only inspect/exact validated stop-retain/release; no work or foreign stop")
  wrapped=self.wrapper(requested)
  try:result=self.h.run(wrapped,self.remaining(cleanup=True,cap=cap))
  except BaseException as error:
   result=dict(argv=wrapped,requested_argv=requested,exit_code=None,
    error=repr(error),observed_utc=utc().isoformat(),cleanup_safety_only=True)
   retained=c.write(self.out/(label+"-"+str(time.time_ns())+".json"),result)
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
   formal_deadline_monotonic=self.deadline,formal_cutoff=c.CUT)
  retained=c.write(self.out/(label+"-"+str(time.time_ns())+".json"),result)
  c.require(result["exit_code"]==0,"actual command failed; retained "+str(retained))
  return result,retained
 def resources(self,initial=False):
  mem={l.split(":")[0]:int(l.split()[1])*1024 for l in Path("/proc/meminfo").read_text().splitlines()
   if l.startswith(("MemAvailable:","MemTotal:","Hugetlb:","SwapTotal:","SwapFree:"))}
  c.require(mem["SwapTotal"]==mem["SwapFree"] and mem["MemAvailable"]>=RESERVE+HOST_MEM+(MEM if initial else 0),
   "actual ordinary RAM72.25GiB initial/8.25 live floor; HugeTLB never additive")
  free=shutil.disk_usage(self.out.parent).free;used=sum(p.stat().st_size for p in self.out.parent.rglob("*") if p.is_file())
  c.require(free>=RESERVE+(WORKSPACE if initial else 0) and used<=WORKSPACE,"joint whole packet10GiB output plus8GiB diskreserve, stop retain not delete")
  host=H.cpu_view(os.getpid());daemon=H.daemon_view();allocation=cpu_admission(host,daemon)
  if self.cpu is None:self.cpu=allocation
  c.require(allocation==self.cpu,"effective host/daemon quota/cpuset admission changed")
  engine,er=self.call("engine",[DOCKER,"info","--format","{{json .}}"])
  c.require(json.loads(engine["stdout"])["NCPU"]>=7,"engine inventory contradicts actual summed CPU admission")
  return dict(memory=mem,disk_free_bytes=free,output_bytes=used,host_cpu=host,daemon_cpu=daemon,cpu_allocation=allocation,
   engine=er,ordinary_floor_bytes=RESERVE+HOST_MEM+(MEM if initial else 0),output_allowance_bytes=WORKSPACE,**self.rss())
 def observe(self,label,initial=False,cleanup=False):
  raw,sr=self.call("smi",[SMI,"info"],cleanup=cleanup);text=raw["stdout"];protect=self.h.protected(text)
  if self.protected is None:self.protected=protect
  record=dict(label=label,npu_smi=text,smi=sr,protected0_3=protect,actual_compute=[],declared_only_containers=[],
   observed_utc=raw["observed_utc"],actual_device_fd_holders=[],actual_hbm=[])
  original=c.write(self.out/("observation-raw-%d.json"%time.time_ns()),record)
  record["protected_boundary"]=protected_boundary(self.protected,protect,[self.cid] if self.cid else [],[os.getpid()])
  for card in PHYSICAL:
   record["actual_hbm"].append(actual_hbm(text,card))
   rows=[(n,ch,pid) for n,ch,pid in self.h.legacy().process_rows(text) if n==card]
   if self.cid is None or not rows:self.h.idle_one(text,card)
   for n,ch,pid in rows:
    p=H.started(self.h.gate_process(pid));proof=dict(physical=n,chip=ch,stage=label,**p,smi=sr,raw_observation=original)
    record["actual_compute"].append(proof)
    c.require(ch==0 and self.cid is not None and self.cid in p["cgroup"] and self.server_started is not None and
      datetime.datetime.fromisoformat(p["started_utc"])>=self.server_started-datetime.timedelta(seconds=1) and
      p["argv"] and Path(os.readlink(Path("/proc")/str(pid)/"exe")).name.startswith("python"),"real foreign PID/UDA/start/program conflict; never canary authority")
    proof["actual_executable"]=os.readlink(Path("/proc")/str(pid)/"exe");self.process_proofs.append(proof)
  holders=fd_holders();record["actual_device_fd_holders"]=holders
  c.require(all(self.cid is not None and self.cid in p["cgroup"] for p in holders),"actual foreign4..7 FD/UDA conflict")
  running,pr=self.call("running",[DOCKER,"ps","-q","--no-trunc"],cleanup=cleanup)
  for cid in running["stdout"].split():
   r,ir=self.call("declared",[DOCKER,"inspect",cid],cleanup=cleanup);x=json.loads(r["stdout"])[0]
   declared={d["PathOnHost"] for d in (x["HostConfig"].get("Devices") or [])}
   if declared&set(device_map()):record["declared_only_containers"].append(dict(cid=cid,inspect=ir,devices=sorted(declared)))
  record["resources"]=self.resources(initial)
  completed=c.write(self.out/("observation-%d.json"%time.time_ns()),record);self.observations.append(completed)
  return completed
 def inspect(self,cleanup=False):
  raw,r=self.call("inspect",[DOCKER,"inspect",self.cid],cleanup=cleanup);rows=json.loads(raw["stdout"])
  c.require(len(rows)==1,"one complete exact own inspect");validate_inspect(rows[0],self.expected)
  if cleanup:
   self._cleanup_owned_identity=(self.cid,c.canonical(self.expected))
   self._cleanup_stopped=(not rows[0]["State"]["Running"] and rows[0]["State"]["Pid"]==0 and not rows[0].get("ExecIDs"))
  return rows[0],r
 def create_owned(self,source):
  # Creation is NOT cleanup admission. Existing fresh observe/resources and
  # name/mount/device checks remain in create(); normal time/RSS gates stay.
  c.require(self.cid is None and self.expected is not None and self.expected["cid"] is None and
   source["host_run.py"]==c.sha(__file__) and self.expected["host_sha256"]==source["host_run.py"],"one fresh source-bound create only")
  requested=create_argv(self.expected);wrapped=self.wrapper(requested)
  self.rss()
  try:result=self.h.run(wrapped,self.remaining(cleanup=False,cap=60))
  except BaseException as error:
   result=dict(argv=wrapped,requested_argv=requested,exit_code=None,error=repr(error),observed_utc=utc().isoformat())
   retained=c.write(self.out/("create-"+str(time.time_ns())+".json"),result)
   raise RuntimeError("create command failure retained: "+str(retained)) from error
  result.update(requested_argv=requested)
  cid=result["stdout"].strip() if isinstance(result.get("stdout"),str) else None
  valid=(result.get("exit_code")==0 and re.fullmatch("[0-9a-f]{64}",cid or "") is not None)
  # Capture completed CLI's exact success CID BEFORE persistence/post-admission
  # can fail. Cleanup still requires full inspect/source ownership, not this CID alone.
  if valid:self.cid=cid;self.expected["cid"]=cid
  retained=c.write(self.out/("create-"+str(time.time_ns())+".json"),result)
  c.require(result.get("exit_code")==0,"actual create failed; retained "+str(retained))
  c.require(valid,"complete actual created CID; retained "+str(retained))
  c.write(self.out/"OWNED.json",dict(**self.expected,create_receipt=retained,sources=source))
  # A successful create never bypasses resource/time admission or authorizes
  # start on failure; only exact validated safety stop remains available.
  self.rss();self.remaining(cleanup=False,cap=60)
  return result,retained
 def create(self,refs,sources,model,arm):
  mounts={str(c.BASE):(str(c.BASE),False),str(c.KERNEL):(str(c.KERNEL),False),"/usr/local/Ascend/driver":("/usr/local/Ascend/driver",False),
   "/models/Qwen3.6-27B":(model["host_model_root"],False),str(self.out.parent):(str(self.out.parent),False),
   str(self.out):(str(self.out),True)}
  for p in c.required_source_mounts():
   if not p.startswith(str(c.KERNEL)+"/") and not p.startswith(str(c.BASE)+"/"):mounts[p]=(p,False)
  for ref in refs.values():
   p=ref["path"]
   if not (p.startswith(str(c.BASE)+"/") or p.startswith(str(c.KERNEL)+"/") or p.startswith(str(self.out.parent)+"/")):mounts[p]=(p,False)
  # Prior numeric tree and original terminal are immutable, never a device lease.
  mounts.update(c.component_readonly_mounts(refs["component"]))
  if "diagnostic" in refs:
   diagnostic=c.obj(refs["diagnostic"])
   # Whole original terminal and exact previous owned output stay readonly. No
   # PID namespace workaround or forged extraction; live host replay happens
   # once BEFORE admission, guest only rebinds original immutable bytes.
   prior=Path(diagnostic["actual_host"]["path"]).parent
   c.require(Path("/cache/cch") in prior.parents and prior.is_dir() and not prior.is_symlink(),"actual diagnostic owned result root")
   mounts[str(prior)]=(str(prior),False)
   terminal=diagnostic["original_terminal"]["path"]
   if not terminal.startswith(str(prior)+"/"):
    mounts[terminal]=(terminal,False)
  if "tasks" in refs:
   tm=c.task_manifest(refs["tasks"])
   for t in tm["tasks"].values():
    for key in ("dataset","prompts","scorer_source","prompt_source","no_thinking_template_source"):p=t[key]["path"];mounts[p]=(p,False)
  self.expected=dict(cid=None,name=self.name,image=c.IMAGE,arm=arm,source=refs["source"],host_sha256=c.sha(__file__),
   guest_cpus=self.cpu["guest_cpus"][:1] if arm=="cpu-preflight" else self.cpu["guest_cpus"],mounts=mounts)
  c.require(re.fullmatch("[A-Za-z0-9_-]{1,100}",self.name),"bounded new owner name")
  old,_=self.call("unique-name",[DOCKER,"ps","-a","--filter","name=^/"+self.name+"$","--format","{{.ID}}"])
  c.require(not old["stdout"].strip(),"owned name exists, no reuse/retry")
  for p,rw in mounts.values():c.require(Path(p).exists(),"actual exact mounted artifact absent")
  for p in ({} if arm=="cpu-preflight" else device_map()):c.require(Path(p).exists(),"actual mapped device absent")
  r,cr=self.create_owned(sources["files"]);cid=self.cid
  x,ir=self.inspect();c.require(not x["State"]["Running"] and x["State"]["Pid"]==0,"fresh exact owner not stopped")
  self.call("start",[DOCKER,"start",cid],cap=60);x,ir=self.inspect()
  c.require(x["State"]["Running"] and x["State"]["Pid"]>0 and not x["State"].get("OOMKilled"),"actual owned live init")
  cv=H.cpu_view(x["State"]["Pid"]);c.require(cv["effective_capacity"]==(1 if arm=="cpu-preflight" else 4) and cv["effective_cpus"]==self.expected["guest_cpus"],"actual guest ancestor4CPU/cpuset")
  c.write(self.out/"guest-cgroup-cpu.json",cv);return ir
 def cleanup(self):
  v=dict(container=self.cid,stopped=False,retained=False,deleted=False,primary_error=repr(self.primary) if self.primary else None,errors=[])
  if self.cid is None:return c.write(self.out/"cleanup.json",v)
  try:
   x,ir=self.inspect(cleanup=True);v["before_inspect"]=ir
   r,sr=self.call("stop-retain",[DOCKER,"stop","--time","15",self.cid],cap=40,cleanup=True);v["stop_receipt"]=sr
   x,ir=self.inspect(cleanup=True);v["after_inspect"]=ir
   c.require(not x["State"]["Running"] and x["State"]["Pid"]==0 and not x.get("ExecIDs"),"exact own init/executions still live")
   v.update(stopped=True,retained=True)
   c.require(not x["State"].get("OOMKilled"),"actual OOM invalidates stage")
   for p in (self.server,self.client):
    if p is not None and p.poll() is None:p.wait(timeout=self.remaining(cleanup=True,cap=20))
    c.require(p is None or p.poll() is not None,"foreground Docker CLI termination pending")
   raw,sr=self.call("release",[SMI,"info"],cleanup=True);v["release_smi"]=sr
   v["protected_boundary"]=protected_boundary(self.protected,self.h.protected(raw["stdout"]),[self.cid],[os.getpid()])
   for card in PHYSICAL:self.h.idle_one(raw["stdout"],card)
  except BaseException as secondary:v["errors"].append(repr(secondary));self.secondary.append(repr(secondary))
  return c.write(self.out/"cleanup.json",v)
def flags(refs):
 out=[]
 for n in ("source","component","model-manifest",*(("diagnostic",) if "diagnostic" in refs else ())):
  r=refs[n];out+=["--"+n,r["path"],"--"+n+"-sha256",r["sha256"]]
 return out
def identity_args(refs,identity,arm,port,mode):
 args=[str(c.BASE/"full_entry.py"),"--execute","--source-manifest-sha256",refs["source"]["sha256"],
  "--numeric-authority",refs["component"]["path"],"--numeric-authority-sha256",refs["component"]["sha256"],
  "--identity",identity["path"],"--identity-sha256",identity["sha256"],
  "--mode",mode,"--arm",arm,"--port",str(port),"--output",str(Path(identity["path"]).parent/"service")]
 if "diagnostic" in refs:args+=["--diagnostic",refs["diagnostic"]["path"],"--diagnostic-sha256",refs["diagnostic"]["sha256"]]
 return args
def write_process(ctl,label,p,requested,started):
 done=p is not None and p.poll() is not None
 return c.write(ctl.out/(label+"-child.json"),dict(requested_argv=requested,actual_host_argv=ctl.wrapper(requested),child_host_pid=p.pid if p else None,
  child_started_utc=started.isoformat() if started else None,child_termination_observed=done,exit_code=p.returncode if done else None,
  stdout_ref=c.bound(ctl.out/(label+".stdout"),c.sha(ctl.out/(label+".stdout"))) if done else None,
  stderr_ref=c.bound(ctl.out/(label+".stderr"),c.sha(ctl.out/(label+".stderr"))) if done else None))
def run_arm(a,refs,sources,model,arm,round_index,start,protected):
 out=a.output/("round%d-%s"%(round_index,arm));out.mkdir();sub=argparse.Namespace(output_dir=out);ctl=Controller(sub,start);ctl.protected=protected
 primary=None;http=None;trace=None;cleanup=None;server_args=None;client_args=None;client_start=None;identity=None;before=None;formal_stats=None
 try:
  before=ctl.observe("preflight",initial=True);ins=ctl.create(refs,sources,model,arm)
  ident=dict(schema="sparq.tp4-arm-identity/v1",mode=a.mode,source=refs["source"],component=refs["component"],model_manifest=refs["model-manifest"],
   arm=arm,port=a.port,container_id=ctl.cid,actual_owned_inspect=ins,preflight=before,created_ns=time.time_ns(),
   memory_bytes=MEM,native_bytes=c.NATIVE_BYTES,state_ceiling_bytes=c.TOTAL_STATE_CEILING,logical_to_physical={"0":4,"1":5,"2":6,"3":7},
   image_argv_template=[])
  identity_path=out/"identity.json";placeholder=dict(path=str(identity_path),sha256="@ACTUAL_IDENTITY_SHA256@")
  ident["image_argv_template"]=[c.PY,"-B",*identity_args(refs,placeholder,arm,a.port,a.mode)]
  identity=c.write(identity_path,ident);server_args=c.docker_argv(ctl.cid,identity_args(refs,identity,arm,a.port,a.mode))
  ctl.server_started=utc();ctl.server_argv=server_args
  with (out/"server.stdout").open("x") as so,(out/"server.stderr").open("x") as se:
   ctl.server=subprocess.Popen(ctl.wrapper(server_args),stdout=so,stderr=se,cwd=c.ROOT)
   end=time.monotonic()+min(1800,ctl.remaining(cap=PHASE))
   while True:
    c.require(ctl.server.poll() is None and time.monotonic()<end,"actual model startup failed/timed out; no retry")
    ctl.observe("startup")
    health=[c.PY,"-B","-c","import urllib.request; r=urllib.request.urlopen('http://127.0.0.1:%d/health',timeout=2); assert r.status==200"%a.port]
    req=[DOCKER,"exec",ctl.cid,*health]
    raw=ctl.h.run(ctl.wrapper(req),min(4,ctl.remaining(cap=4)))
    hr=c.write(out/("health-%d.json"%time.time_ns()),dict(**raw,requested_argv=req))
    if raw["exit_code"]==0:break
    time.sleep(1)
   args=[str(c.BASE/"bench.py"),"--execute","--arm-dir",str(out/"service"),"--port",str(a.port),"--output",str(out/"client")]
   # Tasks are run only after three actual paired screens meet benefit gate; separate final arms below.
   if getattr(a,"run_tasks_this_arm",False):args+=["--tasks",refs["tasks"]["path"],"--tasks-sha256",refs["tasks"]["sha256"]]
   client_args=c.docker_argv(ctl.cid,args);ctl.client_argv=client_args;client_start=utc()
   with (out/"client.stdout").open("x") as co,(out/"client.stderr").open("x") as ce:
    ctl.client=subprocess.Popen(ctl.wrapper(client_args),stdout=co,stderr=ce,cwd=c.ROOT)
    while ctl.client.poll() is None:
     c.require(ctl.server.poll() is None,"actual server died during workload")
     ctl.remaining(cap=PHASE);ctl.observe("workload");time.sleep(1)
    c.require(ctl.client.returncode==0,"actual client/stream/task producer failed")
   ctl.observe("post-workload")
   if a.mode=="formal":
    args=[str(c.BASE/"formal_stats.py"),"--execute","--trace",str(out/"service/trace"),"--source",refs["source"]["path"],"--source-sha256",refs["source"]["sha256"],"--output",str(out/"FORMAL_FINALIZATION.json")]
    raw,terminal=ctl.call("formal-finalization",c.docker_argv(ctl.cid,args),cap=45)
    formal_stats=dict(report=c.bound(out/"FORMAL_FINALIZATION.json",c.sha(out/"FORMAL_FINALIZATION.json")),original_child=terminal)
    c.require(c.obj(formal_stats["report"])["source"]==refs["source"],"actual same-source post-timing finalizer")
   if a.mode=="diagnostic":
    trace_root=out/"service/trace"
    paths=sorted(trace_root.glob("rank*.json"));c.require(paths,"actual whole model trace missing")
    parts=[]
    for offset in range(0,len(paths),512):
     parts.append(c.write(out/("TRACE_INDEX-%06d.json"%(offset//512)),dict(source=refs["source"],trace_root=str(trace_root),
      events=[c.bound(p,c.sha(p)) for p in paths[offset:offset+512]])))
    trace=c.write(out/"TRACE_INDEX.json",dict(schema="sparq.actual-entire-model-trace/v1",source=refs["source"],
     trace_root=str(trace_root),chunks=parts,sampled=False,http=c.bound(out/"client/REPORT.json",c.sha(out/"client/REPORT.json")),arm=c.bound(out/"service/ARM.json",c.sha(out/"service/ARM.json"))))
   http=c.bound(out/"client/REPORT.json",c.sha(out/"client/REPORT.json"))
   c.require(c.obj(http)["status"]=="complete","actual full40 client report")
   if getattr(a,"run_tasks_this_arm",False):
    task_inputs=c.task_manifest(refs["tasks"]);scores={}
    actual_http=c.obj(http)
    c.require(set(actual_http.get("tasks",{}))=={"LongBench-v2","GSM8K"},"full actual2048 response matrix")
    for task,t in task_inputs["tasks"].items():
     meta=actual_http["tasks"][task];r=meta["responses"]
     score_image=str(out/"client"/task/"SCORE.json")
     score_host=out/"client"/task/"SCORE.json"
     cli=[r["path"] if v=="@RESPONSES@" else score_image if v=="@OUTPUT@" else v for v in t["scorer_cli"]]
     c.require(cli[0]==c.PY and cli[1]=="-B" and cli[2]==t["scorer_source"]["path"],"unchanged actual scorer entry")
     c.bound(t["scorer_source"]["path"],t["scorer_source"]["sha256"])
     raw,terminal=ctl.call("score-"+task,c.docker_argv(ctl.cid,cli[2:]),cap=ctl.remaining(cap=PHASE))
     scored=c.bound(score_host,c.sha(score_host));score=c.obj(scored)
     responses=c.obj(c.bound(out/"client"/task/"RESPONSES.json",r["sha256"]))
     c.require(score.get("schema")=="qwen36.actual-task-score/v1" and score.get("task")==task and score.get("arm")==arm and
      score.get("responses_sha256")==r["sha256"] and score.get("protocol_identity")==responses["protocol_identity"] and
      score.get("request_count")==t["request_count"] and type(score.get("score")) in (int,float) and
      0<=score["score"]<=1 and score.get("scorer_source")==t["scorer_source"],
      "actual scorer full task/protocol/response/source/count identity, not unknown stdout PASS")
     c.bound(t["scorer_source"]["path"],t["scorer_source"]["sha256"])
     scores[task]=dict(score=scored,actual_scorer_terminal=terminal,original_cli=cli,responses=r)
    c.write(out/"TASK_SCORES.json",dict(schema="sparq.actual-task-scores/v1",tasks=refs["tasks"],arm=arm,scores=scores))

 except BaseException as error:primary=error;ctl.primary=error
 finally:
  try:cleanup=ctl.cleanup()
  except BaseException as e:ctl.secondary.append(repr(e))
  child={}
  for label,p,argv,seen in (("server",ctl.server,server_args,ctl.server_started),("client",ctl.client,client_args,client_start)):
   if argv:
    try:child[label]=write_process(ctl,label,p,argv,seen)
    except BaseException as e:ctl.secondary.append(repr(e))
  for error in formal_time_failures(ctl.deadline):
   if error not in ctl.secondary:ctl.secondary.append(error)
  success=primary is None and not ctl.secondary and http is not None and cleanup is not None
  result=c.write(out/"RESULT.json",dict(schema="sparq.tp4-arm-result/v1",mode=a.mode,status="complete" if success else "failed",arm=arm,round=round_index,
   source=refs["source"],component=refs["component"],model_manifest=refs["model-manifest"],diagnostic=refs.get("diagnostic"),identity=identity,preflight=before,
   http=http,actual_model_trace=trace,formal_stats=formal_stats,task_scores=c.bound(out/"TASK_SCORES.json",c.sha(out/"TASK_SCORES.json")) if (out/"TASK_SCORES.json").is_file() else None,children=child,cleanup=cleanup,container_id=ctl.cid,process_proofs=ctl.process_proofs,observations=ctl.observations,
   protected0_3=H.protected_map(ctl.protected or []),primary=repr(primary) if primary else None,secondary=ctl.secondary,
   model_ready=False,graph_model_source_supported=True,graph_model_numeric_verified=False,original_operation_authority_verified=False))
 if primary:raise primary
 c.require(not ctl.secondary,"secondary precise stop-retain failure")
 return result,ctl.protected

def cpu_phase(a,refs,sources,model,start):
 """Sequential owned Devices[]8GiB/1CPU closure, SAME whole5400 deadline.
 Stops retained before any four-device arm; a failed cleanup forbids later work.
 """
 out=a.output/"cpu-preflight";out.mkdir()
 ctl=Controller(argparse.Namespace(output_dir=out),start);primary=None;probe=None;cleanup=None;original=None;terminal=None
 try:
  ctl.observe("cpu-source-preflight",initial=True)
  original=ctl.create(refs,sources,model,"cpu-preflight")
  args=[str(c.BASE/"full_cpu_preflight.py"),"--execute","--source-manifest-sha256",refs["source"]["sha256"],"--output",str(out/"REPORT.json")]
  raw,terminal=ctl.call("full-cpu-source",c.docker_argv(ctl.cid,args),cap=180)
  probe=c.bound(out/"REPORT.json",c.sha(out/"REPORT.json"));p=c.obj(probe)
  import identity_bridge
  identity_bridge.static_probe(p,refs["source"],sources["files"],ctl.cid)
  c.require(p["model_executed"] is False and p["npu_executed"] is False,"actual same-source FULL static no-device closure")
  lines=[l for l in raw["stdout"].splitlines() if l.startswith("MAIN_SPARQ_FULL_CPU ")]
  c.require(len(lines)==1 and json.loads(lines[0].split(" ",1)[1])==dict(result=probe,status="source-static-checked"),
   "original CPU stdout -> whole source receipt exact binding")
 except BaseException as error:primary=error;ctl.primary=error
 finally:
  try:cleanup=ctl.cleanup()
  except BaseException as error:ctl.secondary.append(repr(error))
  for error in formal_time_failures(ctl.deadline):
   if error not in ctl.secondary:ctl.secondary.append(error)
  cr=c.obj(cleanup) if cleanup else {}
  success=primary is None and not ctl.secondary and cr.get("stopped") is True and cr.get("retained") is True and cr.get("errors")==[]
  ref=c.write(out/"RESULT.json",dict(schema="sparq.full-model-cpu-stage/v1",status="complete" if success else "failed",
   source=refs["source"],container_id=ctl.cid,probe=probe,inspect=original,original_child=terminal,cleanup=cleanup,primary=repr(primary) if primary else None,
   secondary=ctl.secondary,created_monotonic=start,deadline_monotonic=start+PHASE,ready=False))
 if primary:raise primary
 c.require(success,"no-device exact stop-retain prerequisite incomplete")
 return ref


def post_model_cpu(a,refs,sources,model,start,trace):
 out=a.output/"cpu-model-check";out.mkdir();ctl=Controller(argparse.Namespace(output_dir=out),start)
 primary=None;report=None;cleanup=None;owned=None;terminal=None
 try:
  ctl.observe("post-model-CPU-preflight",initial=True)
  owned=ctl.create(refs,sources,model,"cpu-preflight")
  args=[str(c.BASE/"model_cpu_check.py"),"--execute",*sum((["--"+n,refs[n]["path"],"--"+n+"-sha256",refs[n]["sha256"]] for n in ("source","component")),[]),
   "--trace",trace["path"],"--trace-sha256",trace["sha256"],"--output",str(out/"REPORT.json")]
  raw,terminal=ctl.call("full64-independent-CPU",c.docker_argv(ctl.cid,args),cap=ctl.remaining(cap=PHASE))
  report=c.bound(out/"REPORT.json",c.sha(out/"REPORT.json"));x=c.obj(report)
  c.require(x["status"]=="checked" and x["source"]==refs["source"] and x["source_files"]==sources["files"] and
   x["refs"]==dict(source=refs["source"],component=refs["component"],trace=trace) and x["first_exception"] is None and
   x["initialized_before"] is False and x["initialized_after"] is False and x["actual_device_fds"]==[],
   "actual full64 independent no-device CPU report, not kernel/model mock")
  marks=[l for l in raw["stdout"].splitlines() if l.startswith("MAIN_SPARQ_FULL_MODEL_CPU ")]
  c.require(len(marks)==1 and json.loads(marks[0].split(" ",1)[1])==dict(result=report,status="checked"),
   "actual original CPU command terminal -> whole independent check")
 except BaseException as error:primary=error;ctl.primary=error
 finally:
  try:cleanup=ctl.cleanup()
  except BaseException as error:ctl.secondary.append(repr(error))
  for error in formal_time_failures(ctl.deadline):
   if error not in ctl.secondary:ctl.secondary.append(error)
  cr=c.obj(cleanup) if cleanup else {}
  success=primary is None and not ctl.secondary and cr.get("stopped") is True and cr.get("retained") is True and cr.get("errors")==[]
  result=c.write(out/"RESULT.json",dict(schema="sparq.full64-CPU-stage/v1",status="complete" if success else "failed",
   source=refs["source"],component=refs["component"],trace=trace,owned_inspect=owned,container_id=ctl.cid,
   original_child=terminal,report=report,cleanup=cleanup,primary=repr(primary) if primary else None,secondary=ctl.secondary,
   same_whole_deadline_monotonic=start+PHASE,ready=False))
 if primary:raise primary
 c.require(success,"full64 no-device CPU source/math/cleanup gate failed")
 return result

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true");p.add_argument("--source-audit-only",action="store_true")
 for name in ("source","component","model-manifest","tasks","diagnostic"):
  p.add_argument("--"+name);p.add_argument("--"+name+"-sha256")
 p.add_argument("--mode",choices=("diagnostic","formal"),default="diagnostic");p.add_argument("--output",type=Path);p.add_argument("--port",type=int,default=8241)
 p.add_argument("--final-tasks",action="store_true");a=p.parse_args()
 if a.source_audit_only:
  c.require(not a.execute and a.source and a.source_sha256,"explicit software source audit without model execute")
  ref=c.bound(a.source,a.source_sha256);m=c.source(ref);print(json.dumps(dict(source_audit_passed=True,source=ref,source_count=m["source_count"],npu_executed=False,model_ready=False,runtime_imports_pending_admitted_N1=True)));return
 if not a.execute:print(json.dumps(dict(enabled=False,model_ready=False,npu_executed=False,actual_TP4_model_and_tasks_pending=True)));return
 c.require(c.BASE==c.INTEGRATED and all(getattr(a,n.replace("-","_")) and getattr(a,n.replace("-","_")+"_sha256")
  for n in ("source","component","model-manifest")),"MAIN actual integrated own/kernel/model Refs mandatory")
 refs={n:c.bound(getattr(a,n.replace("-","_")),getattr(a,n.replace("-","_")+"_sha256")) for n in ("source","component","model-manifest")}
 start=time.monotonic()
 c.require((datetime.datetime.fromisoformat(c.CUT)-utc()).total_seconds()>=PHASE,"whole5400 begins before source/model full rehash; no preparation lease reset")
 host=H.cpu_view(os.getpid());os.sched_setaffinity(0,{min(host["effective_cpus"])})
 soft,hard=resource.getrlimit(resource.RLIMIT_AS);c.require(hard==resource.RLIM_INFINITY,"Docker-only child AS restoration requires unlimited hard AS")
 resource.setrlimit(resource.RLIMIT_AS,(HOST_MEM,hard))
 sources=c.source(refs["source"]);c.component(refs["component"],replay=True);model=c.model(refs["model-manifest"])
 if a.mode=="formal":
  c.require(a.diagnostic and a.diagnostic_sha256,"formal mode requires actual same-source TP4 diagnostic Ref")
  refs["diagnostic"]=c.bound(a.diagnostic,a.diagnostic_sha256);c.diagnostic_authority(refs["diagnostic"],refs["component"],refs["source"],replay=True)
 if a.final_tasks:
  c.require(a.mode=="formal","final tasks forbidden before diagnostic authority/formal paired screens")
  c.require(a.tasks and a.tasks_sha256,"final task artifacts missing; cannot create synthetic score PASS")
  refs["tasks"]=c.bound(a.tasks,a.tasks_sha256);c.task_manifest(refs["tasks"])
 c.require((datetime.datetime.fromisoformat(c.CUT)-utc()).total_seconds()>=PHASE,"whole5400/90cleanup before fixed cutoff")
 c.require(a.output and a.output.is_absolute() and a.output.parent.is_dir() and a.output.parent.resolve()==a.output.parent and
  Path("/cache/cch") in a.output.parents and not a.output.exists() and ".." not in a.output.parts,"new actual output leaf, no overwrite/resume")
 c.require(time.monotonic()<start+PHASE-CLEANUP,"source/model identity rehash consumes original whole phase lease")
 a.output.mkdir();results=[];protected=None;primary=None;benefit=None;cpu_result=None;post_cpu_result=None
 plan=c.write(a.output/"PLAN.json",dict(schema="sparq.tp4-service-plan/v1",mode=a.mode,refs=refs,source_files=sources["files"],protocol=c.DIAGNOSTIC_PROTOCOL if a.mode=="diagnostic" else c.PROTOCOL,
  physical_devices=[4,5,6,7],logical_to_physical={"0":4,"1":5,"2":6,"3":7},phase_seconds=PHASE,cleanup_seconds=CLEANUP,stock_full_decode_only_for_both_arms=True,preparer_remote_exec_must_be_zero=True,
  created_monotonic=start,deadline_monotonic=start+PHASE,cutoff=c.CUT,execution_clock=c.execution_clock(),memory_guest_bytes=MEM,memory_host_bytes=HOST_MEM,
  memory_reserve_bytes=RESERVE,ordinary_floor_bytes=MEM+HOST_MEM+RESERVE,output_bytes=WORKSPACE,
  rounds=0 if a.mode=="diagnostic" else 3,arm_order=["candidate"] if a.mode=="diagnostic" else ["dense","candidate","candidate","dense","dense","candidate"],final_task_requested=a.final_tasks,
  final_task_scorer_is_actual_external_frozen_source=True,graph_model_source_supported=True,graph_model_numeric_verified=False,
  actual_host_process=H.frozen().gate_process(os.getpid()),expected_host_argv=["/usr/bin/python3","-B",str(c.BASE/"host_run.py"),*__import__("sys").argv[1:]]))
 try:
  cpu_result=cpu_phase(a,refs,sources,model,start)
  if a.mode=="diagnostic":
   rr,protected=run_arm(a,refs,sources,model,"candidate",0,start,protected);results.append(rr)
   post_cpu_result=post_model_cpu(a,refs,sources,model,start,c.obj(rr)["actual_model_trace"])
  for r,arms in enumerate(() if a.mode=="diagnostic" else (("dense","candidate"),("candidate","dense"),("dense","candidate"))):
   pair={}
   for arm in arms:
    rr,protected=run_arm(a,refs,sources,model,arm,r,start,protected);results.append(rr)
    pair[arm]=c.obj(c.obj(rr)["http"])["metrics"]["output_tokens_per_second"]
   ratio=pair["candidate"]/pair["dense"];c.require(ratio>=1.10,"actual paired1024 screen benefit below1.10; retain bounded negative, no final tasks")
  if a.mode=="formal":benefit={"three_pairs_completed":True,"threshold":1.10}
  if a.final_tasks:
   a.run_tasks_this_arm=True
   for arm in ("dense","candidate"):
    rr,protected=run_arm(a,refs,sources,model,arm,3,start,protected);results.append(rr)
 except BaseException as e:
  primary=e
  results=[c.bound(path,c.sha(path)) for path in sorted(a.output.glob("round*/RESULT.json"))]
 after_sources=None;final_secondary=[]
 try:after_sources=c.source(refs["source"])["files"]
 except BaseException as error:
  if primary is None:primary=error
  else:final_secondary.append(repr(error))
 final_time_errors=formal_time_failures(start+PHASE);final_secondary.extend(final_time_errors)
 if primary is None and final_time_errors:primary=ValueError("; ".join(final_time_errors))
 final=c.write(a.output/"RESULT.json",dict(schema="sparq.tp4-service-host/v1",execution_clock=c.execution_clock(),mode=a.mode,status="complete" if primary is None else "failed",plan=plan,refs=refs,arms=results,
  benefit=benefit,cpu_stage=cpu_result,post_model_cpu=post_cpu_result,source_files_before=sources["files"],source_files_after=after_sources,secondary=final_secondary,primary=repr(primary) if primary else None,phase_elapsed_seconds=time.monotonic()-start,graph_model_source_supported=True,graph_model_numeric_verified=False,
  model_ready=False,MAIN_original_operation_authority_verified=False,final2048_scores_pending=a.final_tasks))
 print("MAIN_SPARQ_TP4_SERVICE "+json.dumps(dict(result=final,status=c.obj(final)["status"])),flush=True)
 if primary:raise primary
if __name__=="__main__":main()

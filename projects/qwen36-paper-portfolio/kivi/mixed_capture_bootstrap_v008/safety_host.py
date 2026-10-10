"""MAIN-only one-entry TP4 matched-screen/final-task controller, default OFF."""
from __future__ import annotations
import argparse,datetime,json,os,re,resource,shutil,stat,subprocess,time
from pathlib import Path
import model_contract as c
DOCKER="/usr/bin/docker";SMI="/usr/local/sbin/npu-smi";PRLIMIT="/usr/bin/prlimit"
MEM=64*c.GIB;HOST_MEM=512*1024**2;RESERVE=8*c.GIB+512*1024**2;WORKSPACE=160*c.GIB
PHASE=5400;CLEANUP=90;OWNER="kivi-mixed-capture-and-independent-cpu-v2";PHYSICAL=(4,5,6,7)
H=c.module(c.H8,c.DEPS[str(c.H8)],"_sparq_tp4_frozen_host")
_NATIVE_BOUNDARY=None
def protected_boundary(before,after,owned_cids=(),owned_host_pids=()):
 return c.protected_module().protected_boundary(before,after,owned_cids,owned_host_pids)

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
 return dict(ASCEND_RT_VISIBLE_DEVICES="" if cpu else "0,1,2,3",TORCH_DEVICE_BACKEND_AUTOLOAD="0",
  PYTHONDONTWRITEBYTECODE="1",OMP_NUM_THREADS="1",MKL_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",
  TMPDIR="/adakv-results",VLLM_DISABLE_REQUEST_ID_RANDOMIZATION="1",
  QWEN36_KIVI_FIRSTDECODE_DIAGNOSTIC="1",QWEN36_KIVI_STAGED_NUMERIC_CAPTURE="1",QWEN36_KIVI_PACKED_QKAV_QWEN_INSTALLER="1",
  QWEN36_KIVI_ACTUAL_INGRESS_BINDING="1",QWEN36_KIVI_FIELD_GEOMETRY_DIAGNOSTIC="1",
  QWEN36_KIVI_LAYOUT_DIAGNOSTIC="1",QWEN36_KIVI_PACKED_QKAV_OWNED_SEAM="1",
  QWEN36_KIVI_PACKED_QKAV_SOURCE_CANDIDATE="1")

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
 # Stable at creation and after canonical JSON roundtrip; no mount set/RW change.
 for n in sorted(e["mounts"]):
  p,rw=e["mounts"][n]
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
  super().__init__(a);self.name="kivi-tp4-"+self.out.parent.name+"-"+self.out.name
  self.created_monotonic=parent_start;self.deadline=parent_start+c.phase_seconds();self.server=None;self.client=None
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
  if own+child>HOST_MEM//1024:violations.append("actual host+CLI cumulative peak RSS exceeds512MiB")
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
   "actual ordinary RAM73GiB initial/9GiB live floor; HugeTLB never additive")
  free=shutil.disk_usage(self.out.parent).free;scan,used=c.output_scan(self.out.parent)
  scan_ref=c.write(self.out/("OUTPUT-SCAN-%d.json"%time.time_ns()),scan)
  c.require(free>=RESERVE+(WORKSPACE if initial else 0) and used<=WORKSPACE,"joint whole packet32GiB output plus8.5GiB diskreserve, stop retain not delete")
  host=H.cpu_view(os.getpid());daemon=H.daemon_view()
  peer=c.peer_module().check_peer(self,c.PEER_LEASE_REF) if c.PEER_LEASE_REF is not None else None
  allocation=c.peer_module().choose_allocation(host,daemon,peer) if peer is not None else cpu_admission(host,daemon)
  if peer is not None:c.require(mem["MemAvailable"]>=int(81.5*c.GIB),"fresh conservative summed TP4+CPU8+twohost+reserve81.5GiB")
  if self.cpu is None:self.cpu=allocation
  c.require(allocation==self.cpu,"effective host/daemon quota/cpuset admission changed")
  engine,er=self.call("engine",[DOCKER,"info","--format","{{json .}}"])
  c.require(json.loads(engine["stdout"])["NCPU"]>=7,"engine inventory contradicts actual summed CPU admission")
  return dict(actual_output_scan_ref=scan_ref,memory=mem,disk_free_bytes=free,output_bytes=used,host_cpu=host,daemon_cpu=daemon,cpu_allocation=allocation,
   engine=er,ordinary_floor_bytes=RESERVE+HOST_MEM+(MEM if initial else 0),output_allowance_bytes=WORKSPACE,**self.rss())
 def observe(self,label,initial=False,cleanup=False):
  if c.RUNTIME_PHASE=="cpu-numeric":
   c.require(not cleanup,"CPU normal observation cannot act as cleanup")
   proof=self.inspect()[1] if self.cid else None
   value=dict(schema="kivi.actual-cpu-only-resource-observation/v1",label=label,
    inspected=proof,resources=self.resources(initial),devices=[],npu_ownership_claim=False)
   r=c.write(self.out/("CPU-OBSERVATION-%d.json"%time.time_ns()),value)
   self.observations.append(r);return r
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
   source["safety_host.py"]==c.sha(__file__) and self.expected["host_sha256"]==source["safety_host.py"],"one fresh source-bound create only")
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
  # Same actual source-qualified native IPC TMPDIR alias; no Ada graph/algorithm aliases.
  mounts["/adakv-results"]=(str(self.out),True)
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
  if c.RUNTIME_PHASE=="cpu-numeric":return self.cleanup_cpu_only()
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

 def cleanup_cpu_only(self):
  # Same exact create/inspect/stop-retain predicates. No NPU-owned release claim:
  # another MAIN job may use4..7 after our earlier candidate release was proved.
  v=dict(container=self.cid,stopped=False,retained=False,deleted=False,
   primary_error=repr(self.primary) if self.primary else None,errors=[],
   schema="kivi.actual-devices-empty-cleanup/v1",npu_release_claim=False)
  if self.cid is None:return c.write(self.out/"cleanup.json",v)
  try:
   c.require(self.expected["arm"]=="cpu-preflight","CPU-only branch cannot stop candidate")
   x,ir=self.inspect(cleanup=True);v["before_inspect"]=ir
   c.require(x["HostConfig"].get("Devices",[])==[],"actual no-device CPU before stop")
   r,sr=self.call("stop-retain",[DOCKER,"stop","--time","15",self.cid],cap=40,cleanup=True);v["stop_receipt"]=sr
   x,ir=self.inspect(cleanup=True);v["after_inspect"]=ir
   c.require(not x["State"]["Running"] and x["State"]["Pid"]==0 and not x.get("ExecIDs")
    and not x["State"].get("OOMKilled"),"exact CPU stopped/Pid0/noExec/noOOM")
   v.update(stopped=True,retained=True)
   for p in(self.server,self.client):
    if p is not None and p.poll() is None:p.wait(timeout=self.remaining(cleanup=True,cap=20))
    c.require(p is None or p.poll() is not None,"foreground CPU CLI terminated")
  except BaseException as error:v["errors"].append(repr(error));self.secondary.append(repr(error))
  return c.write(self.out/"cleanup.json",v)

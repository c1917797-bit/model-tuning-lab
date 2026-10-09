"""One MAIN host, sequential Devices[] prerequisite then FOUR disjoint guests.
Frozen native matrix/oracle bodies are not patched/import-replaced. Default OFF.
No predecessor partial results count toward new128; no cross-paper concurrency.
"""
import argparse,hashlib,json,os,re,resource,shutil,stat,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
import shard_contract as sc
INTEGRATED=Path("/opt/host/vnf/austinov/model-tuning-lab/projects/qwen36-paper-portfolio/tools/sparq_ann_disjoint4_numeric_v1")
DOCKER="/usr/bin/docker"
def utc():return datetime.now(timezone.utc)
def extract_original(envelope,peer):
 """Whole ORIGINAL terminal reader for a failed predecessor, not numerical PASS."""
 sc.need(type(envelope) is dict,"whole original envelope")
 out=envelope.get("structuredContent",envelope)
 if "structuredContent" in envelope:
  blocks=[b for b in envelope.get("content",[]) if b.get("type")=="text"]
  if blocks:sc.need(len(blocks)==1 and json.loads(blocks[0]["text"])==out,"original textual/structured disagreement")
 op=out.get("operation",out)
 oid=out.get("operationId")
 sc.need(re.fullmatch("exec-[0-9a-f]{16}",oid or "") and op.get("targetPeerId")==peer and
  op.get("routeDecision") in ("peer_direct","upstream_local_peer"),"original target/route/operation ID")
 for key in ("targetPeerId","routeDecision"):
  if key in out and op is not out:sc.need(out[key]==op.get(key),"original duplicate origin disagreement")
 rec=op.get("result",{}).get("record")
 sc.need(type(rec) is dict and rec.get("id")==oid and rec.get("exitCode")==1 and
  rec.get("cancelled") is False and rec.get("timedOut") is False and rec.get("error") is None and
  type(rec.get("command")) is str and type(rec.get("args")) is list and
  type(rec.get("stdout")) is str and type(rec.get("stderr")) is str and
  rec.get("state")=="completed","actual prior host terminal1, not lost/running/cancelled/outer timeout")
 for obj in (envelope,out,op,op.get("result",{}),rec):
  sc.need(not any("truncat" in str(k).lower() and v not in (False,None,0,"") for k,v in obj.items()),"complete original, no truncated receipts")
 return rec
def previous_admission(result_ref,terminal_ref,c):
 sc.need(result_ref=={"path":"/cache/cch/qwen36-paper-preparation-20261007/sparse/MAIN-sparq-author-ann-fixedcap-v10-native-user72h-20261009-001/RESULT.json",
 "sha256":"2ccdd2fefdab1152490b55a13547482caf42ece3a16da65898c8f34fe1fcd4c3"},"only actual expired single-card predecessor, immutable")
 r=c.load(result_ref);rec=extract_original(c.load(terminal_ref),"lgw_a6109c51076a4a2c9d2674ca5a8704a0")
 sc.need(r["source_manifest"]==sc.BASE_SOURCE and r["status"]=="failed" and
  r["numerical_component_checked"] is False and "bounded original child timeout" in (r["primary_error"] or "") and
  r["secondary_errors"]==[] and r["model_executed"] is False and r["matched1024_e2e_verified"] is False,
  "source-bound sole scheduling timeout; not a math/cleanup failure automatic retry")
 marker=[line for line in rec["stdout"].splitlines() if line.startswith("MAIN_SPARQ_TOKEN_V5_HOST ")]
 sc.need(len(marker)==1 and json.loads(marker[0].split(" ",1)[1])["result"]==result_ref,"actual whole failed terminal binds prior RESULT")
 sc.need([rec["command"],*rec["args"]]==r["actual_host_argv"] and r["actual_host_argv"]==r["expected_host_argv"],"prior complete command/args binding")
 for key,ik,cid in (("cleanup","stopped_owned_inspect",r["container_id"]),
                   ("cpu_only_cleanup","cpu_stopped_inspect",r["cpu_container_id"])):
  cr=c.load(r[key]);raw=c.load(r[ik]);x=json.loads(raw["stdout"])[0]
  sc.need(cr["container"]==cid and cr["stopped"] is True and cr["retained"] is True and cr["deleted"] is False and
   cr["errors"]==[] and x["Id"]==cid and x["Image"]==c.IMAGE and x["State"]["Running"] is False and
   x["State"]["Pid"]==0 and x["State"]["OOMKilled"] is False and not x.get("ExecIDs"),"both actual prior CID stopped-retained/noOOM")
 sc.need(c.load(r["cleanup"]).get("release_smi") and c.load(r["protected_after"]),"actual prior postconditions, never partial salvage")
 return dict(result=result_ref,whole_terminal=terminal_ref,partial_cases_used=0,status="prior-timeout-not-promoted")
def host_argv(a):
 return ["/usr/bin/python3","-B",str(INTEGRATED/"shard_host.py"),"--execute",
 "--source-manifest",str(a.source_manifest),"--source-manifest-sha256",a.source_manifest_sha256,
 "--predecessor-result",str(a.predecessor_result),"--predecessor-result-sha256",a.predecessor_result_sha256,
 "--predecessor-terminal",str(a.predecessor_terminal),"--predecessor-terminal-sha256",a.predecessor_terminal_sha256,
 "--output",str(a.output)]
def devices(card):
 sc.need(card in sc.CARDS,"authorized physical4..7 only")
 return {"/dev/davinci%d"%card:"/dev/davinci0",**{p:p for p in ("/dev/davinci_manager","/dev/devmm_svm","/dev/hisi_hdc")}}
def card_labels(e,nh):
 value=nh.labels(e);value["model-tuning-lab.owner"]=sc.OWNER
 value.update({"sparq.disjoint-packet":e["packet_source"]["sha256"],"sparq.shard-id":str(e["shard_id"]),"sparq.physical":str(e["physical"])})
 return value
def inspect_card(x,e,nh):
    sc.need(type(x) is dict and re.fullmatch("[0-9a-f]{64}",e["cid"] or ""),
            "complete exact owned CID required before stop")
    h=x["HostConfig"];cfg=x["Config"]
    sc.need(x["Id"]==e["cid"] and x["Name"]=="/"+e["name"] and x["Image"]==nh.IMAGE and
        cfg["Image"]==nh.IMAGE and cfg["Entrypoint"]==["/bin/bash"] and
        cfg["Cmd"]==["-c","exec /bin/sleep infinity"] and cfg["WorkingDir"]==str(nh.ROOT),
        "full exact CID/image/init identity")
    actual_labels=cfg.get("Labels") or {}
    sc.need(all(actual_labels.get(k)==v for k,v in card_labels(e,nh).items()),"owned source/controller labels")
    env=cfg.get("Env") or []
    sc.need(all(env.count(k+"="+v)==1 and sum(z.startswith(k+"=") for z in env)==1
                for k,v in nh.environment().items()),"exact nonduplicated runtime environment")
    sc.need(h["Privileged"] is False and h["Memory"]==sc.GUEST_BYTES and h["MemorySwap"]==sc.GUEST_BYTES and
        h["NanoCpus"]==10**9 and h["CpusetCpus"]==str(e["guest_cpu"]) and
        h["NetworkMode"]=="none" and h["IpcMode"]=="private" and h["ShmSize"]==2*1024**3 and
        h["PidsLimit"]==512 and not h.get("DeviceRequests") and not h.get("DeviceCgroupRules") and
        set(h.get("CapDrop") or [])=={"ALL"} and
        set(h.get("SecurityOpt") or [])=={"no-new-privileges"},
        "exact owned isolation/resources; declarations not foreign occupation")
    drows=h.get("Devices") or []
    sc.need(len(drows)==len(devices(e["physical"])) and {d["PathOnHost"]:d["PathInContainer"] for d in drows}==
        devices(e["physical"]) and all(d["CgroupPermissions"]=="rwm" for d in drows),
        "one assigned physical4..7 to logical0 and exact control-node map")
    mounts=x["Mounts"];want={dst:(src,bool(rw)) for dst,(src,rw) in e["mounts"].items()}
    sc.need(len(mounts)==len(want) and all(m["Type"]=="bind" for m in mounts) and
        {m["Destination"]:(m["Source"],m["RW"]) for m in mounts}==want,
        "complete exact immutable inputs/new output mounts")
def card_create_argv(e,nh):
 # Transparent exact argv extension; no global helper variable changes.
 argv=nh.create_argv(e);key="model-tuning-lab.owner="+nh.OWNER
 sc.need(argv.count(key)==1 and argv.count("/dev/davinci6:/dev/davinci0:rwm")==1,"source-bound creation substitution positions")
 argv[argv.index(key)]="model-tuning-lab.owner="+sc.OWNER
 argv[argv.index("/dev/davinci6:/dev/davinci0:rwm")]="/dev/davinci%d:/dev/davinci0:rwm"%e["physical"]
 at=argv.index(nh.IMAGE)
 argv[at:at]=["--label","sparq.disjoint-packet="+e["packet_source"]["sha256"],
 "--label","sparq.shard-id="+str(e["shard_id"]),"--label","sparq.physical="+str(e["physical"])]
 return argv
def closure_mounts(ctl,co,nh):
 mounts=nh.Controller.mounts(ctl)
 for path in [str(sc.ROOT),co.allocation_ref["path"],co.packet_source["path"],*co.manifest["native_external_pins"]]:
  p=Path(path)
  # Do not duplicate covered RO tree or nest another RW mount.
  covered=any(not rw and (p==Path(dst) or Path(dst) in p.parents) for dst,(_,rw) in mounts.items())
  if not covered:mounts[path]=(path,False)
 for dst,(src,rw) in mounts.items():
  sc.need(Path(src).exists() and ".." not in Path(src).parts,"complete existing immutable source mount")
  if rw:sc.need(dst=="/sparq-results" and src==str(ctl.out),"only exact owned output writable")
 return mounts
def holders(cards):
 targets={}
 for card in cards:
  p=Path("/dev/davinci%d"%card);sc.need(p.is_char_device(),"actual authorized character device")
  targets[p.stat().st_rdev]=card
 result=[];proc=list(Path("/proc").iterdir());sc.need(len(proc)<=32768,"bounded actual process inventory")
 for p in proc:
  if not p.name.isdigit():continue
  try:fd=list((p/"fd").iterdir())
  except (FileNotFoundError,ProcessLookupError):continue
  sc.need(len(fd)<=16384,"bounded actual device FDs")
  hit=set()
  for f in fd:
   try:s=f.stat()
   except (FileNotFoundError,ProcessLookupError):continue
   if stat.S_ISCHR(s.st_mode) and s.st_rdev in targets:hit.add(targets[s.st_rdev])
  if hit:
   try:
    cg=(p/"cgroup").read_text();st=(p/"stat").read_text();cmd=(p/"cmdline").read_bytes()
   except (FileNotFoundError,ProcessLookupError):continue
   for card in sorted(hit):result.append(dict(physical=card,pid=int(p.name),cgroup=cg,stat=st,cmdline_sha256=hashlib.sha256(cmd).hexdigest()))
 return result
class Joint:
 def __init__(self,a,own,manifest,c,nh,source,files):
  self.a=a;self.out=a.output;self.packet_source=own;self.manifest=manifest;self.c=c;self.nh=nh;self.source=source;self.files=files
  self.created=time.monotonic();self.deadline=self.created+sc.PHASE_SECONDS;self.cleanup_deadline=None
  self.cards=[];self.cpu=None;self.protected=None;self.secondary=[];self.resources_plan=None;self.seq=0
  self.allocation_ref=c.write_new(self.out/"ALLOCATION.json",sc.allocation())
  self.clock=sc.own_clock(manifest);self.host_initial=nh.H.cpu_view(os.getpid());self.daemon_initial=nh.H.daemon_view()
  self.resources_plan=sc.joint_budget(self.host_initial,self.daemon_initial)
  os.sched_setaffinity(0,{self.resources_plan["host_cpu"]})
  soft,hard=resource.getrlimit(resource.RLIMIT_AS);sc.need(hard==resource.RLIM_INFINITY,"Docker CLI-only inherited AS restoration")
  resource.setrlimit(resource.RLIMIT_AS,(sc.HOST_BYTES,hard))
 def live(self):
  return [v for v in ([self.cpu] if self.cpu else [])+self.cards if v.cid is not None]
 def rss(self):
  own=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;child=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
  now=0
  for ctl in self.cards:
   if ctl.child and ctl.child.poll() is None:
    try:
     rows=Path("/proc/%d/status"%ctl.child.pid).read_text().splitlines()
     now+=next(int(x.split()[1]) for x in rows if x.startswith("VmRSS:"))
    except (FileNotFoundError,ProcessLookupError):pass
  aggregate=max(own+child,own+now)
  sc.need(aggregate<=sc.HOST_BYTES//1024,"joint one-host + concurrent CLI actual RSS exceeds256MiB")
  return dict(host_peak_rss_kib=own,cumulative_child_peak_rss_kib=child,actual_live_cli_rss_kib=now,aggregate_rss_kib=aggregate)
 def resources(self,initial=False):
  h=self.nh.H
  mem={l.split(":")[0]:int(l.split()[1])*1024 for l in Path("/proc/meminfo").read_text().splitlines()
   if l.startswith(("MemAvailable:","MemTotal:","Hugetlb:","SwapTotal:","SwapFree:"))}
  running=sum(bool(v.cid) for v in self.cards)
  floor=sc.RESERVE_BYTES+sc.HOST_BYTES+(max(0,4-running)*sc.GUEST_BYTES if initial else 0)
  sc.need(mem["SwapTotal"]==mem["SwapFree"] and mem["MemAvailable"]>=floor,"joint ordinary RAM floor, HugeTLB not additive")
  free=shutil.disk_usage(self.out).free;used=sum(p.stat().st_size for p in self.out.rglob("*") if p.is_file())
  sc.need(used<=sc.OUTPUT_BYTES and free>=sc.RESERVE_BYTES+(max(0,sc.OUTPUT_BYTES-used) if initial else 0),"four5GiB outputs +8GiB disk reserve")
  host=h.cpu_view(os.getpid());daemon=h.daemon_view();plan=sc.joint_budget(host,daemon)
  sc.need(plan==self.resources_plan,"joint effective CPU/cgroup admission changed")
  for ctl in self.live():
   if ctl.out.exists():sc.need(sum(p.stat().st_size for p in ctl.out.rglob("*") if p.is_file())<=5*1024**3,"one shard5GiB actual output limit")
  return dict(memory=mem,disk_free_bytes=free,output_bytes=used,ordinary_floor_bytes=floor,
   joint_guest_memory_bytes=4*sc.GUEST_BYTES,host_memory_bytes=sc.HOST_BYTES,reserve_memory_bytes=sc.RESERVE_BYTES,
   host_cpu=host,daemon_cpu=daemon,cpu_allocation=plan,**self.rss())
 def protected_check(self,observed):
  if self.protected is None:self.protected=observed
  return self.nh.protected_boundary(self.protected,observed,[v.cid for v in self.live()],[os.getpid()])
 def observe(self,caller,label,expected=None,initial=False):
  raw,sr=caller.call("joint-smi",[self.nh.H.SMI,"info"])
  text=raw["stdout"];record=dict(label=label,observed_utc=raw["observed_utc"],smi=sr,npu_smi=text,
   protected0_3=caller.h.protected(text),actual_compute=[],declared_only_containers=[])
  before=self.c.write_new(self.out/("joint-raw-"+str(time.time_ns())+".json"),record)
  record["protected_boundary"]=self.protected_check(record["protected0_3"])
  rows=caller.h.legacy().process_rows(text);proofs_by={v.card:[] for v in self.cards}
  bycard={v.card:v for v in self.cards if v.cid is not None}
  for card in sc.CARDS:
   live=[r for r in rows if r[0]==card];ctl=bycard.get(card)
   if not live:caller.h.idle_one(text,card)
   for physical,chip,pid in live:
    proof=self.nh.H.started(caller.h.gate_process(pid))
    self.c.write_new(self.out/("joint-actual-process-"+str(time.time_ns())+".json"),dict(physical=card,chip=chip,**proof))
    sc.need(ctl is not None and chip==0 and ctl.cid in proof["cgroup"] and ctl.child is not None and
     ctl.child_label in ("canary","matrix") and proof["argv"]==ctl.expected_child_argv,
     "actual foreign PID/UDA or non-matching this owned card child")
    sc.need(datetime.fromisoformat(proof["started_utc"])>=ctl.child_started-self.nh.H.timedelta(seconds=1),"real startedtime not another dispatch")
    item=dict(physical=physical,chip=chip,stage=ctl.child_label,**proof,smi=sr,raw_observation=before,observed_utc=raw["observed_utc"])
    proofs_by[card].append(item);record["actual_compute"].append(item)
  fds=holders(sc.CARDS);record["actual_device_fd_holders"]=fds
  for fd in fds:
   ctl=bycard.get(fd["physical"]);sc.need(ctl is not None and ctl.cid in fd["cgroup"],"foreign actual device FD/UDA")
  # Declarations alone are observations, not occupancy or stop authority.
  raw,pr=caller.call("joint-running",[DOCKER,"ps","-q","--no-trunc"])
  for cid in raw["stdout"].split():
   r,ir=caller.call("joint-declared",[DOCKER,"inspect",cid]);x=json.loads(r["stdout"])[0]
   ds={d["PathOnHost"] for d in x["HostConfig"].get("Devices") or []}
   if ds & {"/dev/davinci%d"%n for n in sc.CARDS}:record["declared_only_containers"].append(dict(cid=cid,inspect=ir,devices=sorted(ds)))
  record["resources"]=self.resources(initial)
  ref=self.c.write_new(self.out/("joint-observation-"+str(time.time_ns())+".json"),record)
  for ctl in self.cards:
   for proof in proofs_by[ctl.card]:
    proof["complete_observation"]=ref
    (ctl.canary_proofs if ctl.child_label=="canary" else ctl.gate_proofs).append(proof)
  return proofs_by.get(getattr(caller,"card",None),[]),ref
def controller_classes(co):
 nh=co.nh;c=co.c
 class CPU(nh.CPUController):
  def mounts(self,artifacts=None):return closure_mounts(self,co,nh)
  def resources(self,initial=False):return co.resources(initial)
  def rss(self):return co.rss()
 class Card(nh.Controller):
  def __init__(self,a,part):
   super().__init__(a);self.card=part["physical"];self.part=part;self.name="sparq-disjoint-%d-"%self.card+co.out.name
   self.created_monotonic=co.created;self.deadline=co.deadline;self.cpu=dict(guest_cpu=co.resources_plan["guest_cpus"][part["shard_id"]])
   self.expected_child_argv=None;self.so=None;self.se=None;self.end=None;self.child_ref=None
  def mounts(self,artifacts=None):return closure_mounts(self,co,nh)
  def resources(self,initial=False):return co.resources(initial)
  def rss(self):return co.rss()
  def check_protected(self,observed):return co.protected_check(observed)
  def observe(self,label,expected_argv=None,initial=False,cleanup=False):
   sc.need(not cleanup,"joint cleanup has exact inspect/stop/release-only lane")
   return co.observe(self,label,expected_argv,initial)
  def inspect(self,cleanup=False):
   raw,ref=self.call("inspect",[DOCKER,"inspect",self.cid],cleanup=cleanup);xs=json.loads(raw["stdout"]);sc.need(len(xs)==1,"one exact owned CID")
   inspect_card(xs[0],self.expected,nh)
   if cleanup:
    self._cleanup_owned_identity=(self.cid,c.canonical(self.expected))
    self._cleanup_stopped=not xs[0]["State"]["Running"] and xs[0]["State"]["Pid"]==0 and not xs[0].get("ExecIDs")
   return xs[0],ref
  def create(self,artifacts,source_ref,source):
   self.expected=dict(cid=None,name=self.name,image=c.IMAGE,owner=sc.OWNER,source=source_ref,host_sha256=co.manifest["files"]["shard_host.py"],
    numeric_sha256=co.manifest["files"]["shard_numeric.py"],guest_cpu=self.cpu["guest_cpu"],mounts=self.mounts(),mode="npu",
    physical=self.card,shard_id=self.part["shard_id"],packet_source=co.packet_source)
   sc.need(re.fullmatch("[A-Za-z0-9_-]{1,100}",self.name),"bounded unique owned name")
   old,_=self.call("unique-name",[DOCKER,"ps","-a","--filter","name=^/"+self.name+"$","--format","{{.ID}}"])
   sc.need(not old["stdout"].strip(),"existing name never reused")
   for src,rw in self.expected["mounts"].values():sc.need(Path(src).exists(),"mount closure before create")
   for path in devices(self.card):sc.need(Path(path).is_char_device(),"physical authorized node exists")
   self.rss();argv=card_create_argv(self.expected,nh)
   raw=self.h.run(self.wrapper(argv),self.remaining(cap=60));raw["requested_argv"]=argv
   cid=raw.get("stdout","").strip();valid=raw.get("exit_code")==0 and re.fullmatch("[0-9a-f]{64}",cid or "") is not None
   if valid:self.cid=cid;self.expected["cid"]=cid
   ref=c.write_new(self.out/("create-"+str(time.time_ns())+".json"),raw)
   sc.need(valid,"actual create64CID captured before persistence/RSS, no retry")
   c.write_new(self.out/"OWNED.json",dict(schema="sparq.disjoint-owned/v1",**self.expected,create_receipt=ref,sources=source,packet_files=co.manifest["files"]))
   self.rss();self.remaining(cap=60)
   x,ir=self.inspect();sc.need(not x["State"]["Running"] and x["State"]["Pid"]==0 and not x.get("ExecIDs"),"fresh exact CID")
   self.call("start",[DOCKER,"start",self.cid],cap=60);x,ir=self.inspect();sc.need(x["State"]["Running"] and x["State"]["Pid"]>0,"owned fresh init")
   guest=nh.H.cpu_view(x["State"]["Pid"])
   sc.need(guest["effective_capacity"]==1 and guest["effective_cpus"]==[self.cpu["guest_cpu"]],"actual guest1CPU effective cgroup")
   c.write_new(self.out/"guest-cgroup-cpu.json",guest);return ir
  def begin(self,label,args,limit):
   sc.need(self.child is None or self.child.poll() is not None,"one active child per owned card")
   self.child_started=utc();self.child_label=label;self.child_request=self.h.legacy().exec_argv(self.cid,args)
   self.expected_child_argv=[c.PY,"-B",*args];self.end=time.monotonic()+min(limit,self.remaining(cap=5280))
   self.so=self.out/(label+".stdout");self.se=self.out/(label+".stderr")
   self.sf=self.so.open("x");self.ef=self.se.open("x")
   self.child=subprocess.Popen(self.wrapper(self.child_request),stdout=self.sf,stderr=self.ef,cwd=nh.ROOT)
  def finish(self):
   sc.need(self.child is not None and self.child.poll() is not None,"actual child termination")
   self.sf.close();self.ef.close();proofs=self.canary_proofs if self.child_label=="canary" else self.gate_proofs
   ids={(p["pid"],p["start_ticks"]) for p in proofs}
   failure=None
   if self.child.returncode!=0:failure="actual child exit"+str(self.child.returncode)
   elif len(ids)!=1:failure="missing/drift actual this-child NPU PID/argv/cgroup/start"
   elif self.child_label=="matrix" and ids & {(p["pid"],p["start_ticks"]) for p in self.canary_proofs}:failure="borrowed canary identity"
   self.child_ref=c.write_new(self.out/(self.child_label+"-child.json"),dict(requested_argv=self.child_request,
    actual_host_argv=self.wrapper(self.child_request),expected_image_python_argv=self.expected_child_argv,
    child_host_pid=self.child.pid,child_started_utc=self.child_started.isoformat(),child_termination_observed=True,
    exit_code=self.child.returncode,stdout_ref=c.bound(self.so,c.sha(self.so)),stderr_ref=c.bound(self.se,c.sha(self.se)),
    physical_pid_proofs=proofs,primary_error=failure))
   sc.need(failure is None,failure);return self.child_ref
  def cleanup(self):
   # Shared90s, never normal resource/time/RSS gate before inspect/stop authority.
   self.cleanup_deadline=co.cleanup_deadline
   result=dict(container=self.cid,stopped=False,retained=False,deleted=False,errors=[],primary_error=repr(self.primary) if self.primary else None)
   if self.cid is None:return c.write_new(self.out/"cleanup.json",result)
   try:
    _,before=self.inspect(cleanup=True);result["before_inspect"]=before
    _,stop=self.call("stop-retain",[DOCKER,"stop","--time","15",self.cid],cap=40,cleanup=True);result["stop_receipt"]=stop
    x,after=self.inspect(cleanup=True);result["after_inspect"]=after
    sc.need(not x["State"]["Running"] and x["State"]["Pid"]==0 and not x.get("ExecIDs"),"exact owned stopped/PID0/noExec")
    result.update(stopped=True,retained=True);sc.need(not x["State"]["OOMKilled"],"OOM invalid")
    if self.child is not None and self.child.poll() is None:self.child.wait(timeout=self.remaining(cleanup=True,cap=20))
    sc.need(self.child is None or self.child.poll() is not None,"foreground child unreaped")
    for f in (getattr(self,"sf",None),getattr(self,"ef",None)):
     if f is not None and not f.closed:f.close()
    raw,sr=self.call("release-smi",[nh.H.SMI,"info"],cleanup=True);result["release_smi"]=sr
    result["protected_boundary"]=co.protected_check(self.h.protected(raw["stdout"]));self.h.idle_one(raw["stdout"],self.card)
   except BaseException as error:result["errors"].append(repr(error));self.secondary.append(repr(error))
   return c.write_new(self.out/"cleanup.json",result)
 return CPU,Card
def wait_all(co,active):
 """ONE host event loop, no monitoring threads or extra controller CPU."""
 while any(ctl.child.poll() is None for ctl in active):
  for ctl in active:
   if ctl.child.poll() is None:sc.need(time.monotonic()<ctl.end,"bounded shard child timeout, whole lease not reset")
  co.observe(active[0],"joint-children")
  time.sleep(1)
 co.observe(active[0],"joint-children-finished")
 return [ctl.finish() for ctl in active]

def execute(a,own,manifest):
 c,source,files=sc.native();nh=__import__("host")
 sc.need(sc.ROOT==INTEGRATED and Path(__file__).resolve()==INTEGRATED/"shard_host.py","MAIN must integrate reviewed separate packet, no private ON")
 actual=[sys.executable,"-B",*sys.argv];sc.need(actual==host_argv(a),"one exact source/old-terminal/newoutput CLI")
 sc.need((nh.CUTOFF-utc()).total_seconds()>=sc.PHASE_SECONDS,"whole5400incl90 fits actual authorized first-repair cutoff")
 predecessor=previous_admission(dict(path=str(a.predecessor_result),sha256=a.predecessor_result_sha256),
  dict(path=str(a.predecessor_terminal),sha256=a.predecessor_terminal_sha256),c)
 nh.H.fresh_output(a.output);co=Joint(a,own,manifest,c,nh,source,files);CPU,Card=controller_classes(co)
 primary=None;after=None;cpu_fields=None;packet_cpu=None;initial=None;release=None;parts=[];cpu_cleanup=None
 process=dict(pid=os.getpid(),argv=actual,stat=Path("/proc/self/stat").read_text(),cgroup=Path("/proc/self/cgroup").read_text(),
  cmdline_sha256=hashlib.sha256(Path("/proc/self/cmdline").read_bytes()).hexdigest())
 try:
  cp=co.out/"cpu-preflight";cp.mkdir(exist_ok=False)
  co.cpu=CPU(argparse.Namespace(output_dir=cp));co.cpu.cpu=dict(guest_cpu=co.resources_plan["guest_cpus"][0])
  co.cpu.created_monotonic=co.created;co.cpu.deadline=co.deadline
  _,initial=co.cpu.observe("preflight",initial=True);co.protected=co.cpu.protected
  engine,er=co.cpu.call("engine-joint",[DOCKER,"info","--format","{{json .}}"])
  sc.need(json.loads(engine["stdout"])["NCPU"]>=7,"engine CPU corroborates effective host/daemon sevenCPU")
  plan=c.write_new(co.out/"PLAN.json",dict(schema="sparq.disjoint4-host-plan/v1",packet_source=own,native_source=source,
   execution_clock=co.clock,source_derived_allocation=co.allocation_ref,predecessor=predecessor,phase_seconds=5400,cleanup_seconds=90,
   common_created_monotonic=co.created,common_deadline_monotonic=co.deadline,resources=co.resources(True),engine=er,
   MAIN_only_dispatch=True,partial_salvage=False))
  co.cpu.create({},source,files);_,cpu_inspect=co.cpu.inspect()
  abi_raw,abi_child=co.cpu.call("native-no-device",c.docker_argv(co.cpu.cid,c.abi_image_argv(nh.BASE,source,cp)),cap=180)
  abi_ref=c.bound(cp/"ABI.json",c.sha(cp/"ABI.json"));abi=c.load(abi_ref)
  __import__("preflight").validate_abi(abi,source,files)
  c.validate_cpu_abi_child(co.cpu.cid,cp,source,c.load(abi_child),abi)
  marks=[x for x in abi_raw["stdout"].splitlines() if x.startswith("MAIN_SPARQ_TOKEN_V5_NO_DEVICE ")]
  sc.need(len(marks)==1 and nh.translate(json.loads(marks[0].split(" ",1)[1])["actual_abi"],cp)==abi_ref,"actual ABI stdout/original source42 bytes")
  audit_argv=[c.PY,"-B",str(sc.ROOT/"shard_numeric.py"),"--cpu-audit-only","--source-manifest",own["path"],"--source-manifest-sha256",own["sha256"]]
  audit_raw,audit_child=co.cpu.call("packet-no-device",c.docker_argv(co.cpu.cid,audit_argv),cap=120)
  packet_cpu=c.bound(cp/"PACKET_CPU.json",c.sha(cp/"PACKET_CPU.json"));pr=c.load(packet_cpu)
  sc.need(pr["schema"]=="sparq.disjoint4-no-device-packet/v1" and pr["status"]=="software-checked" and
   pr["packet_source"]==own and pr["native_source"]==source and pr["native_files"]==files and
   pr["argv"]==audit_argv and pr["npu_executed"] is False and pr["device_nodes"]==[],"actual no-device own packet + original42 prerequisites")
  am=[x for x in audit_raw["stdout"].splitlines() if x.startswith("MAIN_SPARQ_DISJOINT_CPU ")]
  sc.need(len(am)==1 and nh.translate(json.loads(am[0].split(" ",1)[1])["report"],cp)==packet_cpu,"original packet CPU stdout binds actual bytes")
  cpu_cleanup=co.cpu.cleanup();cc=c.load(cpu_cleanup)
  sc.need(cc["stopped"] and cc["retained"] and not cc["deleted"] and cc["errors"]==[] and not co.cpu.secondary,"Devices[] CPU stop before all NPU")
  cpu_fields=dict(cpu_container_id=co.cpu.cid,cpu_only_inspect=cpu_inspect,
   cpu_only_owned=c.bound(cp/"OWNED.json",c.sha(cp/"OWNED.json")),cpu_only_cleanup=cpu_cleanup,
   cpu_stopped_inspect=cc["after_inspect"],cpu_host_output_root=str(cp),
   native_no_device_abi=abi_ref,native_no_device_child=abi_child,packet_cpu=packet_cpu,packet_cpu_child=audit_child)
  # ALL four new CIDs share the same source/clock and are stopped-before-start
  # after the original CPU phase. Each physical mapping is explicitly validated.
  for part in sc.allocation()["shards"]:
   out=co.out/("shard-%d-physical%d"%(part["shard_id"],part["physical"]));out.mkdir(exist_ok=False)
   ctl=Card(argparse.Namespace(output_dir=out),part);co.cards.append(ctl)
   co.observe(ctl,"card-precreate",initial=True);ctl.create({},source,files)
   args=[str(nh.BASE/"numeric_gate.py"),"--inside-canary",*nh.source_flags(argparse.Namespace(source_manifest=Path(source["path"]),source_manifest_sha256=source["sha256"])),
    "--host-output-root",str(out),"--native-abi",abi_ref["path"],"--native-abi-sha256",abi_ref["sha256"]]
   ctl.begin("canary",args,120);canary_child=wait_all(co,[ctl])[0]
   canary=c.bound(out/"canary.json",c.sha(out/"canary.json"));cv=c.load(canary)
   sc.need(cv["schema"]=="sparq.token-canary/v4" and cv["fresh_canary_passed"] is True and
    cv["source_manifest"]==source and cv["sources_before"]==cv["sources_after"]==files and
    cv["script_sha256"]==files["host.py"] and cv["native_no_device_abi"]==abi_ref and
    cv["preinit_actual_exports"]==abi["actual_exports"] and cv["pid"]==ctl.canary_proofs[-1]["namespace_pids"][-1],
    "actual this-card native42 canary; not another device/child authority")
   ctl.canary=canary;ctl.canary_child=canary_child
  # Fresh audit and exact proof are made immediately before each actual launch.
  for ctl in co.cards:
   _,obs=co.observe(ctl,"shard-launch");x,ir=ctl.inspect()
   proof=dict(schema="sparq.disjoint-device-proof/v1",privileged=False,container_id=ctl.cid,container_inspect=x,
    logical_to_physical={"0":ctl.card},physical_npu_ids=[ctl.card],source_manifest=source,sources=files,
    observed_at_unix_ns=time.time_ns(),exclusive_resource_check_passed=True,
    fresh_resource_audit=dict(actual_observation=obs,actual_resources=c.load(obs)["resources"],protected_before=initial),
    actual_guest_cpu=c.load(c.bound(ctl.out/"guest-cgroup-cpu.json",c.sha(ctl.out/"guest-cgroup-cpu.json"))),
    actual_owned_inspect=ir,canary=ctl.canary,canary_child=ctl.canary_child,plan=plan,probe_idle=initial,
    allocation_ref=co.allocation_ref,allocation_sha256=sc.digest(sc.allocation()),shard_id=ctl.part["shard_id"],
    packet_source=own,common_created_monotonic=co.created,common_deadline_monotonic=co.deadline,**cpu_fields)
   pending=dict(path=str(ctl.out/"proof.json"),sha256="@ACTUAL_DEVICE_PROOF_SHA256@")
   proof["image_python_argv_template"]=sc.shard_argv(Path("/sparq-results/gate"),pending,co.allocation_ref,own,ctl.part["shard_id"])
   ctl.proof=c.write_new(ctl.out/"proof.json",proof);argv=sc.shard_argv(Path("/sparq-results/gate"),ctl.proof,co.allocation_ref,own,ctl.part["shard_id"])
   __import__("shard_proof").validate_proof(ctl.proof["path"],ctl.proof["sha256"],source,files,argv)
   ctl.begin("matrix",argv[2:],ctl.remaining(cap=5280))
  child_refs=wait_all(co,co.cards)
  for ctl,child_ref in zip(co.cards,child_refs):
   report_ref=c.bound(ctl.out/"gate/REPORT.json",c.sha(ctl.out/"gate/REPORT.json"));report=c.load(report_ref)
   sc.check_headers(report,sc.allocation(),ctl.part["shard_id"])
   sc.need(report["packet_source"]==own and report["source_manifest"]==source and
    report["sources_before"]==report["sources_after"]==files and report["device_proof"]==ctl.proof and
    report["native_no_device_abi"]==cpu_fields["native_no_device_abi"] and report["script_sha256"]==manifest["files"]["shard_numeric.py"],"real shard source/proof/native/producer closure")
   from shard_rows import validate_case_set
   checked=validate_case_set(report,ctl.out/"gate",{sc.coordinate(v) for v in ctl.part["assigned_cases"]})
   child=c.load(child_ref);text=Path(c.bound(child["stdout_ref"]["path"],child["stdout_ref"]["sha256"])["path"]).read_text()
   markers=[x for x in text.splitlines() if x.startswith("MAIN_SPARQ_DISJOINT_REPORT ")]
   sc.need(len(markers)==1 and nh.translate(json.loads(markers[0].split(" ",1)[1])["report"],ctl.out)==report_ref,"actual shard stdout binds immutable report")
   parts.append(dict(shard_id=ctl.part["shard_id"],physical=ctl.card,container_id=ctl.cid,output=str(ctl.out),
    source_device_proof=ctl.proof,producer_report=report_ref,numerical_child=child_ref,report_completeness=checked,
    owned=c.bound(ctl.out/"OWNED.json",c.sha(ctl.out/"OWNED.json")),
    actual_guest_cpu=c.bound(ctl.out/"guest-cgroup-cpu.json",c.sha(ctl.out/"guest-cgroup-cpu.json")),
    canary=ctl.canary,canary_child=ctl.canary_child,canary_process_proofs=ctl.canary_proofs,
    actual_npu_python_process_proofs=[dict(p,borrowed_from_canary=False) for p in ctl.gate_proofs]))
 except BaseException as error:
  primary=error
 finally:
  # One shared90-second safety cleanup lane, never four independent renewals.
  co.cleanup_deadline=time.monotonic()+sc.CLEANUP_SECONDS
  if co.cleanup_deadline>co.deadline:
   co.secondary.append("formal lease exhausted; bounded safety-only recovery, never numeric PASS")
  if co.cpu and cpu_cleanup is None:
   co.cpu.primary=primary;co.cpu.cleanup_deadline=co.cleanup_deadline
   try:cpu_cleanup=co.cpu.cleanup()
   except BaseException as error:co.secondary.append("CPU cleanup:"+repr(error))
  cleanup_records=[]
  for ctl in co.cards:
   ctl.primary=primary
   try:
    ref=ctl.cleanup();cleanup_records.append(dict(shard_id=ctl.part["shard_id"],container_id=ctl.cid,cleanup=ref,
     stopped_owned_inspect=c.load(ref).get("after_inspect")))
   except BaseException as error:co.secondary.append("card cleanup:"+repr(error))
   co.secondary.extend(ctl.secondary)
  if co.cpu:co.secondary.extend(co.cpu.secondary)
  try:
   own_after,_=sc.own_identity(a.source_manifest,a.source_manifest_sha256);_,after=c.source_identity(nh.BASE,Path(source["path"]),source["sha256"])
   sc.need(own_after==own and after==files,"all packet/native42 immutable")
   caller=co.cards[-1] if co.cards else co.cpu
   if caller and caller.cid:
    raw,sr=caller.call("release-smi",[nh.H.SMI,"info"],cleanup=True)
    for card in sc.CARDS:caller.h.idle_one(raw["stdout"],card)
    release=c.write_new(co.out/"RELEASE.json",dict(smi=sr,protected_boundary=co.protected_check(caller.h.protected(raw["stdout"])),all_cards=list(sc.CARDS),no_owned_compute=True))
  except BaseException as error:co.secondary.append("source/release:"+repr(error))
  elapsed=time.monotonic()-co.created
  if elapsed>sc.PHASE_SECONDS or utc()>=nh.CUTOFF:co.secondary.append("whole5400/cutoff elapsed; safety-only cleanup not permission")
  success=primary is None and not co.secondary and len(parts)==4 and len(cleanup_records)==4 and bool(release and cpu_fields)
  if success:
   success=all(c.load(r["cleanup"])["stopped"] and c.load(r["cleanup"])["retained"] and c.load(r["cleanup"])["errors"]==[] for r in cleanup_records)
  result=dict(schema="sparq.disjoint4-host-result/v1",status="complete-disjoint-numerics" if success else "failed",
   packet_source=own,native_source=source,native_sources_before=files,native_sources_after=after,
   packet_files=manifest["files"],allocation=co.allocation_ref,execution_clock=co.clock,predecessor=predecessor,
   actual_host_argv=actual,expected_host_argv=host_argv(a),actual_host_process=process,host_script_sha256=manifest["files"]["shard_host.py"],
   output_dir=str(co.out),common_created_monotonic=co.created,common_deadline_monotonic=co.deadline,
   phase_seconds=5400,cleanup_seconds=90,phase_elapsed_seconds=elapsed,joint_resource_plan=co.resources_plan,preflight=initial,
   cpu_fields=cpu_fields,cpu_cleanup=cpu_cleanup,parts=parts,cleanup_records=cleanup_records,release=release,
   primary_error=repr(primary) if primary else None,secondary_errors=co.secondary,numerical_component_checked=bool(success),
   MAIN_original_operation_authority_verified=False,partial_cases_used=0,model_executed=False,
   matched1024_e2e_verified=False,final2048_task_verified=False,ready=False)
  rr=c.write_new(co.out/"RESULT.json",result)
  print("MAIN_SPARQ_DISJOINT_HOST "+json.dumps(dict(result=rr,status=result["status"],packet_source=own)),flush=True)
 if primary is not None:raise primary
 sc.need(success,"all four independent reports/source/CID/release/time mandatory, no partial promotion")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 g=p.add_mutually_exclusive_group();g.add_argument("--execute",action="store_true");g.add_argument("--source-audit-only",action="store_true")
 for key in ("source-manifest","predecessor-result","predecessor-terminal","output"):p.add_argument("--"+key,type=Path)
 for key in ("source-manifest","predecessor-result","predecessor-terminal"):p.add_argument("--"+key+"-sha256")
 a=p.parse_args()
 if not (a.execute or a.source_audit_only):
  print(json.dumps(dict(status="disabled",ready=False,torch_imported="torch" in sys.modules,npu_executed=False)));return
 own,m=sc.own_identity(a.source_manifest,a.source_manifest_sha256)
 if a.source_audit_only:
  print(json.dumps(dict(packet_source=own,native_source=sc.BASE_SOURCE,ready=False,source_count=50)));return
 execute(a,own,m)
if __name__=="__main__":main()

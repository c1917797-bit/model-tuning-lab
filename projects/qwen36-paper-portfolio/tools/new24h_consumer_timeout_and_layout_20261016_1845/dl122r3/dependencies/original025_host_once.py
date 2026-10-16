"""MAIN-only owned CPU -> TP4 model once. No source-only/ABI promotion. Default OFF."""
import argparse,datetime,json,os,resource,subprocess,sys,time
from pathlib import Path
import model_contract as c
def utc():return datetime.datetime.now(datetime.timezone.utc)
def flags(refs,names):
 return sum((["--"+n,refs[n]["path"],"--"+n+"-sha256",refs[n]["sha256"]]for n in names),[])
def fresh_leaf(path):
 p=c.ordinary(path);c.require(Path("/cache/cch")in p.parents and p.parent.is_dir()and not p.exists(),"new exact owned leaf")
 p.mkdir(mode=0o700);return p
def outputs(leaf):
 for n in("graph-output","qkv-output","identities","audit-parent"): (leaf/n).mkdir()
def child(ctl,label,args,limit,observe=True):
 argv=c.docker_argv(ctl.cid,args);start=utc();ctl.server_started=start
 so=ctl.out/(label+".stdout");se=ctl.out/(label+".stderr")
 with so.open("x")as stdout,se.open("x")as stderr:
  p=subprocess.Popen(ctl.wrapper(argv),stdout=stdout,stderr=stderr,cwd=c.ROOT);ctl.server=p;ctl.server_argv=argv
  deadline=time.monotonic()+min(limit,ctl.remaining(cap=limit))
  while p.poll()is None:
   c.require(time.monotonic()<deadline,"bounded original child; never retry")
   if observe:ctl.observe(label)
   else:ctl.remaining(cap=limit)
   time.sleep(1)
  if observe:ctl.observe(label+"-finished")
 r=c.write(ctl.out/(label+"-CHILD.json"),dict(requested_argv=argv,actual_host_argv=ctl.wrapper(argv),
  child_host_pid=p.pid,child_started_utc=start.isoformat(),child_termination_observed=True,exit_code=p.returncode,
  stdout_ref=c.ref(so),stderr_ref=c.ref(se)))
 c.require(p.returncode==0,"actual original child failed "+str(r));return r
class Joint:
 def __init__(self,start):
  self.start=start;self.deadline=start+5400;self.cleanup_used=0.;self.cleanup_started=None;self.secondary=[];self.recovery_deadline=None
 def begin_cleanup(self):
  c.require(self.cleanup_started is None,"no overlapping cleanup")
  now=time.monotonic();self.cleanup_started=now;formal=min(self.deadline-now,c.CUTOFF-time.time())
  remaining=90-self.cleanup_used
  if min(remaining,formal)<=0:
   self.secondary.append("formal cleanup/phase expired; bounded safety-only recovery, stage FAILED")
   if self.recovery_deadline is None:self.recovery_deadline=now+90
   return self.recovery_deadline
  return now+min(remaining,formal)
 def end_cleanup(self):
  self.cleanup_used+=time.monotonic()-self.cleanup_started;self.cleanup_started=None
 def rss(self):
  own=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;ch=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
  c.require(own+ch<=512*1024,"host+CLI cumulative peak512MiB")
  return dict(host_peak_rss_kib=own,child_peak_rss_kib=ch,aggregate_rss_kib=own+ch)
def controller(S,co):
 class Owned(S.Controller):
  def rss(self):return co.rss()
  def remaining(self,cleanup=False,cap=30):
   if cleanup:
    c.require(self.cleanup_deadline is not None,"one joint bounded cleanup lane")
    value=self.cleanup_deadline-time.monotonic()
    c.require(value>0,"bounded exact owned recovery exhausted");return min(value,cap)
   return super().remaining(False,cap)
  def cleanup(self):
   self.cleanup_deadline=co.begin_cleanup()
   try:return super().cleanup()
   finally:co.end_cleanup()
 return Owned
def namespace_raw(ctl,refs):
 from identity_collect import journal_bindings
 assignments=journal_bindings(ctl.out/"identities/live","assignment")
 workers=journal_bindings(ctl.out/"identities/live","worker_update")
 c.require(assignments and len(workers)==4,"actual live frontend/all4 native callbacks before stop")
 front={json.dumps(r["identity"],sort_keys=True)for r in assignments}
 ranks={}
 for row in workers:
  rank=row["rank"];c.require(rank not in ranks,"one rank/namespace")
  ranks[rank]=row["identity"]
 c.require(len(front)==1 and set(ranks)==set(range(4)),"one actual frontend/all4 namespace identity")
 expected=[json.loads(next(iter(front))),*[ranks[r]for r in range(4)]];ids=[x["pid"]for x in expected]
 c.require(len(set(ids))==5,"actual distinct five namespace PIDs")
 host=[]
 for wanted in expected:
  matches=[]
  for root in Path("/proc").iterdir():
   if not root.name.isdigit():continue
   try:
    cg=(root/"cgroup").read_text()
    if ctl.cid not in cg:continue
    status=(root/"status").read_text()
    ns=[int(v)for line in status.splitlines()if line.startswith("NSpid:")for v in line.split()[1:]]
    if not ns or ns[-1]!=wanted["pid"]:continue
    p=ctl.h.gate_process(int(root.name));proof=ctl.h.started(p)if hasattr(ctl.h,"started")else __import__("safety_host").H.started(p)
    stat=(root/"stat").read_text();fields=stat[stat.rfind(")")+2:].split()
    c.require(int(fields[19])==wanted["start_ticks"] and fields[0]!="Z","same actual live namespace/start before raw snapshot")
    exe=os.readlink(root/"exe");matches.append(dict(guest_pid=wanted["pid"],host_pid=int(root.name),
     nspid=ns,start_ticks=int(fields[19]),cgroup=cg,executable=exe,stat=stat,program=proof,
     container_id=ctl.cid,physical_devices=sorted({p["physical"]for p in ctl.process_proofs if p["pid"]==int(root.name)})))
   except(FileNotFoundError,ProcessLookupError):continue
  c.require(len(matches)==1,"one readable exact owned host-to-guest namespace map; not journal authority")
  host.append(matches[0])
 for rank,wanted in ranks.items():
  found=next(x for x in host if x["guest_pid"]==wanted["pid"])
  c.require(found["physical_devices"]==[rank+4],"actual NPU worker rank<->physical SMI observed, not canary")
 hr=c.write(ctl.out/"HOST_NAMESPACE.json",dict(schema="adakv.actual-host-namespace/v1",container_id=ctl.cid,
  namespace_processes=host,observed_utc=utc().isoformat(),actual_owned_inspect=ctl.inspect()[1]))
 args=[str(c.BASE/"process_probe.py"),"--execute","--pids",",".join(map(str,ids)),"--cid",ctl.cid,"--output",str(ctl.out/"GUEST_NAMESPACE.json")]
 raw,cr=ctl.call("actual-guest-process-read",c.docker_argv(ctl.cid,args),cap=30)
 guest=c.ref(ctl.out/"GUEST_NAMESPACE.json")
 # This is raw evidence only. Independent original-terminal consumer sets trust.
 header=dict(schema="vllm023.completion-identity-bundle/v1",profile=c.PROFILE,rows=[],ordered_request_keys=[],
  rank_bindings={str(r):v for r,v in ranks.items()},assignment_process_binding=expected[0],
  controller_authority_independently_consumed=False,original_controller_terminal_ref=None,
  independent_controller_consumer_ref=None,host_namespace_ref=hr,guest_namespace_ref=guest,original_guest_reader=cr)
 return c.write(ctl.out/"IDENTITY_HEADER_RAW.json",header)
def launch_args(refs,mat,identity,leaf,port,cache_bytes,current):
 audit,service=c.audit_package(mat)
 return [str(service/"launch.py"),"--execute","--arm","candidate","--identity",identity["path"],"--identity-sha256",identity["sha256"],
  "--native-gate-authority",c.component(current)["authority"]["path"],
  "--native-gate-authority-sha256",c.component(current)["authority"]["sha256"],
  "--cache-bytes",str(cache_bytes),"--output","/adakv-results/service","--port",str(port),
  "--graph-source",mat["graph_source"]["path"],"--graph-source-sha256",mat["graph_source"]["sha256"],
  "--caller-source",mat["caller_source"]["path"],"--caller-source-sha256",mat["caller_source"]["sha256"],
  "--diagnostic-source",str(Path(mat["root"])/"diagnostic/SOURCE_MANIFEST.json"),
  "--diagnostic-source-sha256",next(r["sha256"]for r in mat["files"]if r["path"]==str(Path(mat["root"])/"diagnostic/SOURCE_MANIFEST.json")),
  "--graph-output","/adakv-graph-diagnostics/live","--snapshot-output","/adakv-qkv-diagnostics/live",
  "--identity-output","/adakv-request-identities/live","--observer-profile","checked",
  "--model-audit","--model-audit-source",audit["path"],"--model-audit-source-sha256",audit["sha256"],
  "--model-audit-output",str(leaf/"audit-parent/live")]
def run(a,refs,m,mat,model,start):
 import safety_host as S
 co=Joint(start);Owned=controller(S,co);owned=[];primary=None;cpu=None;npu=None;protected=None;server_process=None;client_process=None;server_started=None;client_started=None
 source_map=dict(files={Path(r["path"]).name:r["sha256"]for r in m["files"]})
 c.configure(m,mat)
 try:
  leaf=fresh_leaf(a.output/"cpu-preflight");outputs(leaf);ctl=Owned(argparse.Namespace(output_dir=leaf),start);owned.append(ctl)
  ctl.observe("cpu-preflight",initial=True);ctl.create(refs,source_map,model,"cpu-preflight")
  args=[str(c.BASE/"guest_probe.py"),"--execute","--mode","cpu",*flags(refs,("source","materialization")),"--output",str(leaf/"REPORT.json")]
  ch=child(ctl,"source-probe",args,180,observe=False);clean=ctl.cleanup();ctl._adakv017_cleanup_done=True
  c.require(not ctl.secondary and c.obj(clean)["errors"]==[]and c.obj(clean)["stopped"]is True,"actual CPU stopped-retained before any NPU")
  cpu=dict(child=ch,report=c.ref(leaf/"REPORT.json"),cleanup=clean,owned=c.ref(leaf/"OWNED.json"));protected=ctl.protected
  # Fresh original standalone consumer replay under MAIN one CPU before model.
  replay=fresh_leaf(a.output/"current-ABI-replay");current=c.component_rows(refs["component"],replay)
  leaf=fresh_leaf(a.output/"candidate");outputs(leaf);ctl=Owned(argparse.Namespace(output_dir=leaf),start);ctl.protected=protected;owned.append(ctl)
  pre=ctl.observe("model-preflight",initial=True);runtime_refs=dict(refs,component=current)
  owned_inspect=ctl.create(runtime_refs,source_map,model,"candidate")
  canary_args=[str(c.BASE/"guest_probe.py"),"--execute","--mode","n1",*flags(refs,("source","materialization")),
   "--cid",ctl.cid,"--output",str(leaf/"CANARY_N1.json")]
  n1child=child(ctl,"canary-N1",canary_args,180);canary=c.ref(leaf/"CANARY_N1.json")
  c.require(c.obj(canary)["status"]=="canary-N1-checked","all4 actual canary/native runtime prerequisites")
  _,service=c.audit_package(mat);source=current
  authority=c.component(current)["authority"]
  ident=dict(schema="adakv.paged-service-identity/v2",image_id=c.IMAGE,arm="candidate",port=a.port,
   common=__import__("launch_builder").common(a.cache_bytes),native_gate_authority_sha256=authority["sha256"],
   physical_devices=[4,5,6,7],logical_to_physical={"0":4,"1":5,"2":6,"3":7},nonprivileged=True,
   fresh_idle_verified=True,source_canary_passed=True,ordinary_ram_floor_bytes=73*c.GIB,
   preflight_utc=utc().isoformat(),container_id=ctl.cid,
   evidence=dict(actual_owned_inspect=owned_inspect,preflight=pre,canary=canary,canary_child=n1child,
    current5120_consumer=current,source=refs["source"],materialization=refs["materialization"]))
  identity=c.write(leaf/"identity.json",ident);args=launch_args(refs,mat,identity,leaf,a.port,a.cache_bytes,current)
  argv=c.docker_argv(ctl.cid,args);ctl.server_started=utc();ctl.server_argv=argv
  with (leaf/"server.stdout").open("x")as so,(leaf/"server.stderr").open("x")as se:
   ctl.server=subprocess.Popen(ctl.wrapper(argv),stdout=so,stderr=se,cwd=c.ROOT);server_process=ctl.server;server_started=ctl.server_started.isoformat()
   deadline=time.monotonic()+min(1800,ctl.remaining(cap=1800))
   while True:
    c.require(ctl.server.poll()is None and time.monotonic()<deadline,"actual model startup failed/no retry")
    ctl.observe("model-startup")
    health=[c.PY,"-B","-c","import urllib.request; assert urllib.request.urlopen('http://127.0.0.1:%d/health',timeout=2).status==200"%a.port]
    raw=ctl.h.run(ctl.wrapper(["/usr/bin/docker","exec",ctl.cid,*health]),min(4,ctl.remaining(cap=4)))
    c.write(leaf/("health-"+str(time.time_ns())+".json"),raw)
    if raw["exit_code"]==0:break
    time.sleep(1)
   client_args=[str(c.BASE/"lifecycle_client.py"),"--execute",*flags(refs,("source","materialization")),
    "--arm-dir","/adakv-results/service","--audit",str(leaf/"audit-parent/live"),
    "--journals","/adakv-request-identities/live","--output","/adakv-results/client","--port",str(a.port),
    "--budget-seconds",str(int(min(4700,ctl.remaining(cap=4700))))]
   client_argv=c.docker_argv(ctl.cid,client_args);ctl.client_argv=client_argv
   with (leaf/"client.stdout").open("x")as so2,(leaf/"client.stderr").open("x")as se2:
    client_started=utc().isoformat();ctl.client=subprocess.Popen(ctl.wrapper(client_argv),stdout=so2,stderr=se2,cwd=c.ROOT);client_process=ctl.client
    while ctl.client.poll()is None:
     c.require(ctl.server.poll()is None,"actual model died during lifecycle/full40")
     ctl.remaining(cap=5400);ctl.observe("model-workload");time.sleep(1)
    c.require(ctl.client.returncode==0,"actual original whole lifecycle client failed")
   ctl.observe("model-after-workload")
   namespace=namespace_raw(ctl,refs)
   until=time.monotonic()+min(30,ctl.remaining(cap=30))
   finals=[leaf/"audit-parent/live"/("MODEL-FINAL-r%d.json"%r)for r in range(4)]
   while not all(p.is_file()for p in finals):
    c.require(time.monotonic()<until and ctl.server.poll()is None,"actual all4 native final drain not complete")
    ctl.observe("model-drain");time.sleep(.1)
   npu=dict(container=ctl.cid,owned=c.ref(leaf/"OWNED.json"),identity=identity,canary=canary,canary_child=n1child,
    server_argv=argv,client_argv=client_argv,client_report=c.ref(leaf/"client/REPORT.json"),
    namespace_raw=namespace,rank_finals=[c.ref(p)for p in finals],worker_process_proofs=ctl.process_proofs,
    observations=ctl.observations,current_abi_replay=current)
 except BaseException as error:primary=error
 finally:
  for ctl in reversed(owned):
   if ctl.cid and not getattr(ctl,"_adakv017_cleanup_done",False):
    ctl.primary=primary
    try:
     clean=ctl.cleanup();ctl._adakv017_cleanup_done=True
     if npu and ctl.cid==npu["container"]:npu["cleanup"]=clean
    except BaseException as error:co.secondary.append(repr(error))
   co.secondary.extend(ctl.secondary)
  try:
   current_source=c.source(refs["source"]);c.materialization(refs["materialization"])
   unchanged_after={r["path"]:c.sha(r["path"])for r in current_source["files"]}
  except BaseException as error:unchanged_after=None;co.secondary.append("after-source closure "+repr(error))
  if npu:
   npu["server_child"]=dict(requested_argv=npu["server_argv"],actual_host_argv=owned[-1].wrapper(npu["server_argv"]),
    pid=server_process.pid,started_utc=server_started,termination_observed=server_process.poll()is not None,
    exit_code=server_process.returncode,stdout_ref=c.ref(owned[-1].out/"server.stdout"),stderr_ref=c.ref(owned[-1].out/"server.stderr"))
   npu["client_child"]=dict(requested_argv=npu["client_argv"],actual_host_argv=owned[-1].wrapper(npu["client_argv"]),
    pid=client_process.pid,started_utc=client_started,termination_observed=client_process.poll()is not None,
    exit_code=client_process.returncode,stdout_ref=c.ref(owned[-1].out/"client.stdout"),stderr_ref=c.ref(owned[-1].out/"client.stderr"))
  co.secondary.extend(S.formal_time_failures(co.deadline))
  if co.cleanup_used>90:co.secondary.append("joint cleanup90 exceeded; bounded safety recovery not PASS")
  success=primary is None and not co.secondary and cpu is not None and npu is not None
  result=c.write(a.output/"RESULT.json",dict(schema="adakv.tp4-model-once-host/v1",
   status="HOST_COMPLETE_PENDING_ORIGINAL_CONSUMPTION"if success else"failed",source=refs["source"],
   materialization=refs["materialization"],component=refs["component"],model_manifest=refs["model-manifest"],
   cpu=cpu,npu=npu,primary=repr(primary)if primary else None,secondary=co.secondary,
   phase_seconds=5400,cleanup_seconds=90,cumulative_cleanup_seconds=co.cleanup_used,elapsed_seconds=time.monotonic()-start,
   unchanged_source_after=unchanged_after,cpu_plan=owned[-1].cpu if owned else None,actual_host_argv=["/usr/bin/python3","-B",*sys.argv],actual_host_process=S.H.frozen().gate_process(os.getpid()),
   ready=False,model_consumer_required=True,formal_performance=False,task=False))
 print("MAIN_ADAKV_TP4_MODEL_ONCE "+json.dumps(dict(result=result,status=c.obj(result)["status"])),flush=True)
 if primary:raise primary
 c.require(success,"secondary/source/cleanup incomplete");return result
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 for n in("source","materialization","component","software","audit-software","model-manifest"):
  p.add_argument("--"+n);p.add_argument("--"+n+"-sha256")
 p.add_argument("--output",type=Path);p.add_argument("--cache-bytes",type=int);p.add_argument("--port",type=int,default=8236);a=p.parse_args()
 if not a.execute:print(json.dumps(dict(enabled=False,Torch=False,NPU=False,ready=False)));return
 start=time.monotonic();c.require(time.time()+5400<=c.CUTOFF,"fixed72h whole5400 fit before any source rehash")
 refs={n:c.bound(getattr(a,n.replace("-","_")),getattr(a,n.replace("-","_")+"_sha256"))for n in
  ("source","materialization","component","software","audit-software","model-manifest")}
 m=c.source(refs["source"]);mat=c.materialization(refs["materialization"]);c.component(refs["component"])
 own=c.obj(refs["software"]);audit=c.obj(refs["audit-software"])
 c.require(own["schema"]=="adakv.tp4-model-once-software/v1"and own["source"]==refs["source"]and own["successful"]is True and
  own["tests"]==m["tests_declared"]and own["NPU"]is own["model"]is own["ready"]is False,"actual complete own software prerequisite")
 c.require(audit["schema"]=="adakv.full-request-software/v1"and audit["source"]==dict(path=str(c.AUDIT/"SOURCE_MANIFEST.json"),sha256=c.AUDIT_SHA)and
  audit["tests"]==50 and audit["successful"]is True and audit["npu_executed"]is audit["model_verified"]is audit["ready"]is False,"actual current025 all-source50 software, not model authority")
 import safety_host as S
 host=S.H.cpu_view(os.getpid());os.sched_setaffinity(0,{min(host["effective_cpus"])})
 soft,hard=resource.getrlimit(resource.RLIMIT_AS);c.require(hard==resource.RLIM_INFINITY,"restore Docker child AS only")
 resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,hard))
 model=c.model(refs["model-manifest"]);c.require(type(a.cache_bytes)is int and 0<a.cache_bytes<=10*c.GIB,
  "predeclared equal common native bytes <=10GiB, no saving claim from config")
 c.require(not a.output.exists()and a.output.parent==c.PREP/"lowbit"and a.output.name.startswith("run-adakv-model-once-017-main-"),
  "new exact bounded once output")
 a.output=fresh_leaf(a.output);run(a,refs,m,mat,model,start)
if __name__=="__main__":main()

"""MAIN-owned common dense/OFF or KIVI/ON B1 short129 cost attribution; not performance.
Each arm: same660 CPU8 -> TP4 EAGER, two32768+2 warmups then32768+129.
Not final C16/FULL/mixed/task acceptance. Actual018 whole/raw prerequisite. Default OFF.
"""
import argparse,datetime,json,os,resource,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import model_contract as c
def utc():return datetime.datetime.now(datetime.timezone.utc)
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
  def observe(self,*args,**kwargs):
   began=time.perf_counter_ns();cpu=time.process_time_ns()
   try:return super().observe(*args,**kwargs)
   finally:
    label=args[0]if args else str(kwargs.get("label","unknown"))
    costs=getattr(self,"cost_observations",None)
    if costs is None:costs={};self.cost_observations=costs
    row=costs.setdefault(label,dict(calls=0,wall_ns=0,process_cpu_ns=0))
    row["calls"]+=1;row["wall_ns"]+=time.perf_counter_ns()-began;row["process_cpu_ns"]+=time.process_time_ns()-cpu
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

def input_recipe(refs,model,leaf,run_id):
 source=c.obj(refs["source"])
 row=next(r for r in source["files"]if Path(r["path"]).name=="input_recipe.py")
 maker=c.module(row["path"],row["sha256"],"_kivi_firstdecode_input")
 return maker.create(c,refs["source"],refs["model-manifest"],leaf,run_id)
def owner_precondition(ctl,refs,pre,cpu,n1):
 return c.write(ctl.out/"OWNER_PRECONDITION.json",dict(schema="kivi.firstdecode.actual-owned-precondition/v1",
  source=refs["source"],container_id=ctl.cid,image=c.IMAGE,physical_devices=[4,5,6,7],
  logical_to_physical={"0":4,"1":5,"2":6,"3":7},guest_limit_bytes=64*c.GIB,host_limit_bytes=512*1024**2,
  ordinary_initial_floor_bytes=73*c.GIB,phase_seconds_including_cleanup=5400,cleanup_seconds=90,
  hbm_reserve_mib_per_card=3072,portfolio_cutoff=c.CUTOFF,owned_inspect_ref=c.checked(ctl.inspect()[1]),
  resource_ref=pre,mapping_ref=c.write(ctl.out/"ACTUAL_DEVICE_MAP.json",dict(
   schema="kivi.actual-owned-device-map/v1",container_id=ctl.cid,device_map=__import__("safety_host").device_map(),
   inspect=c.checked(ctl.inspect()[1]),source=refs["source"])),
  clock_ref=c.write(ctl.out/"ACTUAL_CLOCK.json",dict(source=refs["source"],cutoff_epoch=c.CUTOFF,
   observed_epoch=time.time(),whole_start_monotonic=ctl.created_monotonic,whole_deadline_monotonic=ctl.deadline,
   total_seconds=5400,cleanup_seconds=90,remaining_seconds=ctl.remaining(cap=5400))),
  canary_ref=n1,cpu_ref=cpu["report"],model_ready=False,performance_ready=False))
def make_recipe(ctl,refs,m,model,cpu,pre,n1,prepared):
 run_id,plan,protocol=prepared
 root=ctl.out/("run-kivi-owned-layout-"+run_id);root.mkdir()
 raw=ctl.out/"packed-raw";raw.mkdir()
 owner=owner_precondition(ctl,refs,pre,cpu,n1)
 recipe=dict(schema="kivi.firstdecode-bootstrap-recipe/v1",source_ref=refs["source"],run_id=run_id,
  container_id=ctl.cid,image_id=c.IMAGE,native_worker_qualified_name="vllm_ascend.worker.worker.NPUWorker",
  worker_qualified_name="kivi_firstdecode_bootstrap.FirstDecodeWorker",run_authority=False,
  cache_bytes=6*c.GIB,bits=2,diagnostic_root=str(root),raw_root=str(raw),algorithm_arm=c.SCREEN_ARM,
  screen_output_counts=[2,2,129],cost_profile=__import__("cost_runtime").PROFILE,
  firstdecode_prerequisite_ref=refs["firstdecode-gate"],
  external_owner_authority_ref=owner,compiled_numeric_qualification_ref=refs["component"],
  native_format_binding=c.obj(cpu["report"])["native_format_binding"],
  actual_input_protocol_ref=protocol,declared_ingress_plan_ref=plan,
  frontend_binding_path=str(root/"ACTUAL_FRONTEND.json"),rank_bindings_path=str(root/"ACTUAL_ALL4_RANKS.json"),
  rank_request_paths={str(rank):str(root/("ACTUAL_OWNER_REQUEST-r%d.json"%rank))for rank in range(4)})
 return c.write(ctl.out/"RECIPE.json",recipe)
def attempt_bind(ctl,recipe,ownership):
 paths=[Path(recipe["rank_request_paths"][str(r)])for r in range(4)]
 front=Path(recipe["frontend_binding_path"])
 if not all(p.is_file()for p in paths+[front]):return False
 actual=ownership.complete_host_bindings(ctl,[c.ref(p)for p in paths],c.ref(front),
  recipe["external_owner_authority_ref"],c.obj,c.write)
 c.write(Path(recipe["rank_bindings_path"]),actual);return True
def run(a,refs,m,model,start):
 import safety_host as S
 co=Joint(start);Owned=controller(S,co);owned=[];primary=None;cpu=None;npu=None;before=None;after=None
 source_map=dict(files={Path(r["path"]).name:r["sha256"]for r in m["files"]})
 protected=None;server_process=None;client_process=None;worker_fault_refs=[];worker_first_fault=None
 try:
  # Execute the complete real input producer before any CPU/NPU container lease.
  candidate_leaf=fresh_leaf(a.output/"candidate");outputs(candidate_leaf)
  run_id=str(time.time_ns())
  plan,protocol=input_recipe(refs,model,candidate_leaf,run_id)
  prepared=(run_id,plan,protocol)
  leaf=fresh_leaf(a.output/"cpu-preflight");outputs(leaf)
  ctl=Owned(argparse.Namespace(output_dir=leaf),start);owned.append(ctl)
  ctl.observe("cpu-preflight",initial=True);ctl.create(refs,source_map,model,"cpu-preflight")
  args=[str(c.BASE/"guest_probe.py"),"--execute","--mode","cpu","--source-manifest-sha256",refs["source"]["sha256"],
        "--output",str(leaf/"REPORT.json"),"--cache-bytes",str(6*c.GIB),"--port",str(a.port)]
  ch=child(ctl,"cpu-import-parser",args,180,observe=False)
  report=c.ref(leaf/"REPORT.json")
  c.require(c.obj(report)["status"]=="CPU_IMPORT_PARSER_CHECKED","actual CPU8 source/parser result")
  clean=ctl.cleanup();ctl._kivi_cleanup_done=True
  c.require(c.obj(clean)["stopped"]is True and c.obj(clean)["retained"]is True and c.obj(clean)["errors"]==[]and not ctl.secondary,
    "actual CPU stop-retain before devices")
  cpu=dict(child=ch,report=report,cleanup=clean,owned=c.ref(leaf/"OWNED.json"));protected=ctl.protected
  leaf=candidate_leaf;ctl=Owned(argparse.Namespace(output_dir=leaf),start)
  ctl.protected=protected;owned.append(ctl);pre=ctl.observe("model-preflight",initial=True)
  ctl.create(refs,source_map,model,"candidate")
  args=[str(c.BASE/"guest_probe.py"),"--execute","--mode","n1","--source-manifest-sha256",refs["source"]["sha256"],
        "--output",str(leaf/"CANARY_N1.json"),"--cache-bytes",str(6*c.GIB),"--port",str(a.port)]
  n1child=child(ctl,"all4-N1",args,180);n1=c.ref(leaf/"CANARY_N1.json")
  c.require(c.obj(n1)["status"]=="N1_ALL4_TINY_CHECKED"and len(c.obj(n1)["canary"])==4,"actual source-bound four tiny canaries")
  rr=make_recipe(ctl,refs,m,model,cpu,pre,n1,prepared);recipe=c.obj(rr)
  boundary_ref=next(r for r in m["files"]if Path(r["path"]).name=="runtime_boundary.py")
  boundary=c.module(boundary_ref["path"],boundary_ref["sha256"],"_kivi_host_runtime_boundary")
  ref_json=leaf/"RECIPE_REF.json";c.write(ref_json,rr)
  own=next(r for r in m["files"]if Path(r["path"]).name=="ownership.py")
  ownership=c.module(own["path"],own["sha256"],"_kivi_firstdecode_host_ownership")
  argv=c.docker_argv(ctl.cid,[str(c.BASE/"server_entry.py"),"--execute","--source-manifest-sha256",refs["source"]["sha256"],
   "--recipe-ref-json",str(ref_json),"--cache-bytes",str(6*c.GIB),"--port",str(a.port)])
  ctl.server_started=utc();ctl.server_argv=argv;began=ctl.server_started.isoformat();bound=False
  with(leaf/"server.stdout").open("x")as stdout,(leaf/"server.stderr").open("x")as stderr:
   ctl.server=subprocess.Popen(ctl.wrapper(argv),stdout=stdout,stderr=stderr,cwd=c.ROOT);server_process=ctl.server
   until=time.monotonic()+min(1800,ctl.remaining(cap=1800))
   while True:
    boundary.raise_if_any(c,recipe,rr,refs["source"],boundary_ref)
    c.require(ctl.server.poll()is None and time.monotonic()<until,"actual model startup failed/bounded, no retry")
    ctl.observe("model-startup")
    if not bound:bound=attempt_bind(ctl,recipe,ownership)
    health=[c.PY,"-I","-B","-c","import urllib.request; assert urllib.request.urlopen('http://127.0.0.1:%d/health',timeout=2).status==200"%a.port]
    raw=ctl.h.run(ctl.wrapper(["/usr/bin/docker","exec",ctl.cid,*health]),min(4,ctl.remaining(cap=4)))
    c.write(leaf/("HEALTH-%d.json"%time.time_ns()),raw)
    if raw["exit_code"]==0:
     c.require(bound,"health never substitutes actual all4 owned binding");break
    time.sleep(1)
   client_args=[str(c.BASE/"client.py"),"--execute","--source-manifest-sha256",refs["source"]["sha256"],
    "--recipe-ref-json",str(ref_json),"--output",str(leaf/"CLIENT_RESULT.json"),"--port",str(a.port)]
   ctl.client_argv=c.docker_argv(ctl.cid,client_args);client_started=utc().isoformat()
   with(leaf/"client.stdout").open("x")as so,(leaf/"client.stderr").open("x")as se:
    ctl.client=subprocess.Popen(ctl.wrapper(ctl.client_argv),stdout=so,stderr=se,cwd=c.ROOT);client_process=ctl.client
    while ctl.client.poll()is None:
     boundary.raise_if_any(c,recipe,rr,refs["source"],boundary_ref)
     c.require(ctl.server.poll()is None,"actual model died during firstdecode")
     ctl.observe("model-firstdecode");time.sleep(1)
    c.require(ctl.client.returncode==0,"actual full firstdecode/native-finish client failed")
   client=c.ref(leaf/"CLIENT_RESULT.json");cr=c.obj(client)
   c.require(cr["status"]=="COST129_HTTP_NATIVE_FINISHED"and len(cr["rank_bundle_refs"])==4,"actual all4 final/raw index")
   ctl.observe("model-after-firstdecode")
   npu=dict(container=ctl.cid,owned=c.ref(leaf/"OWNED.json"),recipe=rr,
    source=refs["source"],all4_namespace=c.ref(leaf/"KIVI_ALL4_NAMESPACE_RAW.json"),canary=n1,canary_child=n1child,
    server_argv=argv,client_argv=ctl.client_argv,client_report=client,
    rank_bundle_refs=cr["rank_bundle_refs"],worker_process_proofs=ctl.process_proofs,observations=ctl.observations,
    server_started_utc=began,client_started_utc=client_started)
 except BaseException as error:
  primary=error;worker_fault_refs=getattr(error,"worker_fault_refs",[])
  worker_first_fault=getattr(error,"worker_first_fault",None)
 finally:
  for ctl in reversed(owned):
   if ctl.cid and not getattr(ctl,"_kivi_cleanup_done",False):
    ctl.primary=primary
    try:
     clean=ctl.cleanup();ctl._kivi_cleanup_done=True
     if npu and ctl.cid==npu["container"]:npu["cleanup"]=clean
    except BaseException as error:co.secondary.append(repr(error))
   co.secondary.extend(ctl.secondary)
  try:
   c.source(refs["source"]);after={r["path"]:c.sha(r["path"])for r in m["files"]}
  except BaseException as error:co.secondary.append("after-source "+repr(error))
  if npu:
   leaf=owned[-1].out
   for kind,proc in(("server",server_process),("client",client_process)):
    npu[kind+"_child"]=dict(requested_argv=npu[kind+"_argv"],actual_host_argv=owned[-1].wrapper(npu[kind+"_argv"]),
     pid=proc.pid,termination_observed=proc.poll()is not None,exit_code=proc.returncode,
     stdout_ref=c.ref(leaf/(kind+".stdout")),stderr_ref=c.ref(leaf/(kind+".stderr")))
  co.secondary.extend(S.formal_time_failures(co.deadline))
  if co.cleanup_used>90:co.secondary.append("joint90cleanup exceeded")
  success=primary is None and not co.secondary and cpu is not None and npu is not None
  result=c.write(a.output/"RESULT.json",dict(schema="kivi.actual-b1-cost129-owned-host/v1",
   algorithm_arm=c.SCREEN_ARM,firstdecode_prerequisite=refs["firstdecode-gate"],
   status="COST129_ARM_PENDING_INDEPENDENT_ATTRIBUTION"if success else"failed",
   source=refs["source"],component=refs["component"],model_manifest=refs["model-manifest"],software=refs["software"],software_stage=refs["software-stage"],
   cpu=cpu,npu=npu,worker_first_fault_refs=worker_fault_refs,worker_first_fault=worker_first_fault,
   primary=repr(primary)if primary else None,secondary=co.secondary,phase_seconds=5400,cleanup_seconds=90,
   cumulative_cleanup_seconds=co.cleanup_used,elapsed_seconds=time.monotonic()-start,
   cost_host_observations=[dict(cid=ctl.cid,by_label=getattr(ctl,"cost_observations",{}))for ctl in owned],
   cost_host_timing_scope="inclusive existing observe; process CPU excludes Docker CLI/other processes; no change to observation cadence",
   unchanged_source_after=after,actual_host_argv=["/usr/bin/python3","-I","-B",*sys.argv],
   actual_host_process=S.H.frozen().gate_process(os.getpid()),model_ready=False,performance_ready=False,run_authority=False,
   whole176=False,full_model_correctness_verified=False,independent_raw_consumer_required=True))
 print(json.dumps(dict(result=result,status=c.obj(result)["status"])),flush=True)
 if primary:raise primary
 c.require(success,"secondary/source/cleanup incomplete");return result
def consume_software_stage(ref,source,software):
 """Pure replay of this owned Devices[] software stage, not model permission."""
 import safety_host as S
 value=c.obj(ref)
 c.require(value["schema"]=="kivi.actual-firstdecode-software-cpu-host/v1"
  and value["status"]=="SOFTWARE_ONLY_CONSUMED" and value["source"]==source
  and value["report"]==software and value["primary"]is None and value["secondary"]==[]
  and value["NPU_created"]is value["model_ready"]is value["run_authority"]is False,
  "whole actual same-source CPU-only software stage")
 owned=c.obj(value["owned"]);clean=c.obj(value["cleanup"]);child_result=c.obj(value["child"])
 c.require(owned["arm"]=="cpu-preflight" and owned["source"]==source
  and clean["container"]==owned["cid"] and clean["stopped"]is clean["retained"]is True
  and clean["deleted"]is False and clean["errors"]==[],"actual CPU-only own stop-retain")
 for ref_name,stopped in (("before_inspect",False),("after_inspect",True)):
  raw=c.obj(clean[ref_name]);rows=json.loads(raw["stdout"])
  c.require(raw["exit_code"]==0 and len(rows)==1,"whole original CPU inspect command")
  x=rows[0];S.validate_inspect(x,owned)
  c.require((x["HostConfig"].get("Devices")or[])==[] and not x["State"].get("OOMKilled"),
   "actual Devices[] no OOM, not a declared flag")
  if stopped:c.require(x["State"]["Running"]is False and x["State"]["Pid"]==0 and not x.get("ExecIDs"),
   "actual CPU init/exec release")
 stop=c.obj(clean["stop_receipt"])
 c.require(stop["requested_argv"]==[S.DOCKER,"stop","--time","15",owned["cid"]]
  and stop["exit_code"]==0,"exact own CPU stop success")
 report=c.obj(software)
 c.require(report["source"]==source and report["successful"]is True and report["NPU"]is False
  and report["python_version"][:2]==[3,12] and report["execution_profile"]=="same660-Devices[]-CPU8"
  and report["no_framework_import"]is True,
  "actual original Python3.12 software and namespace8GiB")
 l=sys.modules["_kivi_firstdecode_source_loader"];m=c.obj(source);memory=l.memory_module(m)
 memory.consume_memory(report["memory_before"],expected_limit=8*c.GIB,container_id=owned["cid"])
 memory.consume_memory(report["memory_after"],expected_limit=8*c.GIB,container_id=owned["cid"])
 expected=c.docker_argv(owned["cid"],[str(c.BASE/"software_check.py"),"--execute",
  "--source-manifest-sha256",source["sha256"],"--output",software["path"]])
 c.require(child_result["requested_argv"]==expected and child_result["exit_code"]==0
  and child_result["child_termination_observed"]is True,"actual same-image exact software child")
 return value
def software_only(a,refs,m,model,start):
 """Reuse the existing CPU arm/controller; never call candidate create or N1."""
 import safety_host as S
 co=Joint(start);co.deadline=start+240;Owned=controller(S,co)
 leaf=fresh_leaf(a.output/"cpu-preflight");outputs(leaf)
 ctl=Owned(argparse.Namespace(output_dir=leaf),start);ctl.deadline=co.deadline
 primary=None;child_ref=None;report=None;cleanup=None
 try:
  ctl.observe("software-cpu-preflight",initial=True)
  ctl.create(refs,dict(files={Path(r["path"]).name:r["sha256"]for r in m["files"]}),model,"cpu-preflight")
  child_ref=child(ctl,"full-software",[str(c.BASE/"software_check.py"),"--execute",
   "--source-manifest-sha256",refs["source"]["sha256"],"--output",str(leaf/"SOFTWARE.json")],150,observe=False)
  report=c.ref(leaf/"SOFTWARE.json");sw=c.obj(report)
  c.require(sw["source"]==refs["source"] and sw["successful"]is True
   and sw["tests"]==m["software_tests_declared"] and sw["NPU"]is sw["model_ready"]is False,
   "actual complete original software; not a fixture subset")
 except BaseException as error:primary=error
 finally:
  if ctl.cid:
   ctl.primary=primary
   try:cleanup=ctl.cleanup()
   except BaseException as error:co.secondary.append(repr(error))
  co.secondary.extend(ctl.secondary);co.secondary.extend(S.formal_time_failures(co.deadline))
  if co.cleanup_used>90:co.secondary.append("joint90cleanup exceeded")
  try:c.source(refs["source"])
  except BaseException as error:co.secondary.append("after-source "+repr(error))
  success=primary is None and not co.secondary and cleanup is not None and report is not None
  result=c.write(a.output/"RESULT.json",dict(schema="kivi.actual-firstdecode-software-cpu-host/v1",
   status="SOFTWARE_ONLY_CONSUMED"if success else"failed",source=refs["source"],
   child=child_ref,report=report,owned=c.ref(leaf/"OWNED.json")if ctl.cid else None,
   cleanup=cleanup,primary=repr(primary)if primary else None,secondary=co.secondary,
   phase_seconds=240,cleanup_seconds=90,elapsed_seconds=time.monotonic()-start,
   NPU_created=False,model_ready=False,run_authority=False))
 if primary:raise primary
 c.require(success,"CPU-only software terminal incomplete")
 consume_software_stage(result,refs["source"],report)
 print(json.dumps(dict(result=result,software=report,NPU=False)));return result
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 p.add_argument("--software-only",action="store_true")
 p.add_argument("--arm",choices=("dense","candidate"))
 p.add_argument("--predecessor-arguments");p.add_argument("--predecessor-arguments-sha256")
 p.add_argument("--software-stage");p.add_argument("--software-stage-sha256")
 for name in("source","component","software","model-manifest"):
  p.add_argument("--"+name);p.add_argument("--"+name+"-sha256")
 p.add_argument("--output",type=Path);p.add_argument("--port",type=int,default=8250);a=p.parse_args()
 if not a.execute:print(json.dumps(dict(enabled=False,model_ready=False)));return
 start=time.monotonic();c.require(time.time()+5400<=c.CUTOFF,"fixed portfolio whole5400 fit before work")
 names=("source","component","model-manifest")if a.software_only else("source","component","software","model-manifest","software-stage")
 refs={name:c.bound(getattr(a,name.replace("-","_")),getattr(a,name.replace("-","_")+"_sha256"))for name in names}
 m=c.source(refs["source"]);c.configure(m)
 c.set_arm(a.arm if a.arm is not None else"candidate")
 c.require(a.software_only or a.arm is not None,"explicit single dense or candidate arm")
 row=next(r for r in m["files"]if Path(r["path"]).name=="prerequisite.py")
 pre=c.module(row["path"],row["sha256"],"_kivi_firstdecode_packed3_gate");pre.consumed(refs["component"],c.obj)
 if not a.software_only:
  consume_software_stage(refs["software-stage"],refs["source"],refs["software"])
  sw=c.obj(refs["software"]);c.require(sw["source"]==refs["source"]and sw["successful"]is True
   and sw["tests"]==m["software_tests_declared"]and sw["NPU"]is sw["model_ready"]is False,"actual new own full software prerequisite")
 host=c.module(c.H8,c.DEPS[str(c.H8)],"_sparq_tp4_frozen_host").cpu_view(os.getpid())
 os.sched_setaffinity(0,{min(host["effective_cpus"])})
 soft,hard=resource.getrlimit(resource.RLIMIT_AS);c.require(hard==resource.RLIM_INFINITY,"Docker child AS restore requires infinite hard limit")
 resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,hard))
 model=c.model(refs["model-manifest"])
 c.require(a.output is not None and not a.output.exists()and a.output.parent==c.PREP/"lowbit"
  and a.output.name.startswith("run-kivi-b1-cost129-"),"new exact cache output only")
 a.output=fresh_leaf(a.output)
 if a.software_only:return software_only(a,refs,m,model,start)
 # The original raw whole consumer uses strict fixed namespaces. Run its pure
 # read-only replay in a bounded fresh HOST process, never edit old globals.
 original=c.bound(a.predecessor_arguments,a.predecessor_arguments_sha256)
 checker=next(r for r in m["files"]if Path(r["path"]).name=="screen_gate.py")
 gate=c.module(checker["path"],checker["sha256"],"_kivi_screen_host_gate")
 refs["firstdecode-gate"]=gate.host_replay(c,refs["source"],original,a.output,start)
 return run(a,refs,m,model,start)
if __name__=="__main__":main()

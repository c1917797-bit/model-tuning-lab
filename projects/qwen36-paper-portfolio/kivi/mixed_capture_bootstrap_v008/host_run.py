"""MAIN-owned collect16 then immediate stop-retain. Separate Devices[] CPU command.
Default OFF. Full sources and actual firstdecode consumption precede any create.
"""
import argparse,datetime,json,os,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import model_contract as c
from host_common import utc,fresh_leaf,outputs,child,Joint,controller
def input_recipe(refs,model,leaf,run_id):
 row=next(r for r in c.ACTIVE["files"]if Path(r["path"]).name=="input_recipe.py")
 return c.module(row["path"],row["sha256"],"_mixed_input_recipe").create(c,refs["source"],refs["model-manifest"],leaf,run_id)
def owner_precondition(ctl,refs,pre,cpu,n1):
 return c.write(ctl.out/"OWNER_PRECONDITION.json",dict(schema="kivi.mixed.actual-owned-precondition/v2",
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
 recipe=dict(schema="kivi.mixed-bootstrap-recipe/v2",source_ref=refs["source"],run_id=run_id,
  container_id=ctl.cid,image_id=c.IMAGE,native_worker_qualified_name="vllm_ascend.worker.worker.NPUWorker",
  worker_qualified_name="kivi_mixed_bootstrap.MixedWorker",run_authority=False,
  cache_bytes=6*c.GIB,bits=2,diagnostic_root=str(root),raw_root=str(raw),
  external_owner_authority_ref=owner,compiled_numeric_qualification_ref=refs["component"],
  native_format_binding=c.obj(cpu["report"])["native_format_binding"],
  actual_input_protocol_ref=protocol,declared_ingress_plan_ref=plan,
  frontend_binding_path=str(root/"ACTUAL_FRONTEND.json"),rank_bindings_path=str(root/"ACTUAL_ALL4_RANKS.json"),
  capture_plan_ref=protocol,capture_ref_paths=[str(raw/("STAGE-%02d-CAPTURE-REF.json"%i))for i in range(16)],
  capture_deadline_epoch=min(c.CUTOFF,time.time()+ctl.remaining(cap=5400)),
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
  inputs=input_recipe(refs,model,candidate_leaf,run_id)
  plan,protocol=inputs["ingress_plan_ref"],inputs["capture_plan_ref"]
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
     ctl.observe("model-mixed-capture");time.sleep(1)
    c.require(ctl.client.returncode==0,"actual full firstdecode/native-finish client failed")
   client=c.ref(leaf/"CLIENT_RESULT.json");cr=c.obj(client)
   c.require(cr["status"]=="ALL16_RAW_AND_NATIVE_FINAL_OBSERVED"and len(cr["rank_final_refs"])==4 and len(cr["capture_receipt_refs"])==16,"actual all4 final/raw index")
   ctl.observe("model-after-mixed-capture")
   npu=dict(container=ctl.cid,owned=c.ref(leaf/"OWNED.json"),recipe=rr,
    source=refs["source"],all4_namespace=c.ref(leaf/"KIVI_ALL4_NAMESPACE_RAW.json"),canary=n1,canary_child=n1child,
    server_argv=argv,client_argv=ctl.client_argv,client_report=client,
    rank_final_refs=cr["rank_final_refs"],worker_process_proofs=ctl.process_proofs,observations=ctl.observations,
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
  result=c.write(a.output/"RESULT.json",dict(schema="kivi.actual-mixed-owned-capture-host/v2",
   status="ALL16_CAPTURED_RELEASED_NUMERIC_PENDING"if success else"failed",
   source=refs["source"],firstdecode_predecessor=refs["firstdecode-args"],component=refs["component"],model_manifest=refs["model-manifest"],software=refs["software"],
   cpu=cpu,npu=npu,worker_first_fault_refs=worker_fault_refs,worker_first_fault=worker_first_fault,
   primary=repr(primary)if primary else None,secondary=co.secondary,phase_seconds=5400,cleanup_seconds=90,
   cumulative_cleanup_seconds=co.cleanup_used,elapsed_seconds=time.monotonic()-start,
   unchanged_source_after=after,actual_host_argv=["/usr/bin/python3","-I","-B",*sys.argv],
   actual_host_process=S.H.frozen().gate_process(os.getpid()),model_ready=False,performance_ready=False,run_authority=False,
   whole176=False,full_model_correctness_verified=False,independent_raw_consumer_required=True))
 print(json.dumps(dict(result=result,status=c.obj(result)["status"])),flush=True)
 if primary:raise primary
 c.require(success,"secondary/source/cleanup incomplete");return result

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 p.add_argument("--phase",choices=["capture","cpu-numeric"],default="capture")
 for name in("source","component","software","model-manifest","firstdecode-args","capture-result","capture-terminal","peer-lease"):
  p.add_argument("--"+name);p.add_argument("--"+name+"-sha256")
 p.add_argument("--capture-peer");p.add_argument("--capture-operation")
 p.add_argument("--capture-command");p.add_argument("--capture-args")
 p.add_argument("--output",type=Path);p.add_argument("--port",type=int,default=8250)
 a=p.parse_args()
 if not a.execute:print(json.dumps(dict(enabled=False,model_ready=False,performance_ready=False)));return
 import resource
 start=time.monotonic()
 refs={n:c.bound(getattr(a,n.replace("-","_")),getattr(a,n.replace("-","_")+"_sha256"))
  for n in("source","component","software","model-manifest","firstdecode-args")}
 m=c.source(refs["source"]);c.configure(m);c.RUNTIME_PHASE=a.phase
 budget=c.module(c.BASE/"budget.py",next(r["sha256"]for r in m["files"]if Path(r["path"]).name=="budget.py"),"_mixed_budget")
 if a.phase=="capture":budget.preregister(time.time())
 else:budget.require_fit(time.time(),"cpu-numeric")
 if a.peer_lease:c.PEER_LEASE_REF=c.bound(a.peer_lease,a.peer_lease_sha256)
 c.require(a.phase=="capture" or c.PEER_LEASE_REF is None,"one independent CPU peer only; no multi-CPU scheduler")
 gate=c.module(c.BASE/"prerequisite.py",next(r["sha256"]for r in m["files"]if Path(r["path"]).name=="prerequisite.py"),"_mixed_packed3_gate")
 gate.consumed(refs["component"],c.obj)
 sw=c.obj(refs["software"]);c.require(sw["source"]==refs["source"]and sw["successful"]is True
  and sw["tests"]==m["software_tests_declared"]and sw["NPU"]is sw["model_ready"]is False,"actual same-source full software")
 pre=c.module(c.BASE/"firstdecode_precondition.py",next(r["sha256"]for r in m["files"]if Path(r["path"]).name=="firstdecode_precondition.py"),"_mixed_firstdecode_gate")
 predecessor=pre.replay(c,m,refs["firstdecode-args"])
 host=c.module(c.H8,c.DEPS[str(c.H8)],"_sparq_tp4_frozen_host").cpu_view(os.getpid())
 # Peer-aware host placement is deferred until fresh actual peer validation in
 # resources; callers with a peer must pre-place this MAIN host on a distinct CPU.
 if c.PEER_LEASE_REF is None:os.sched_setaffinity(0,{min(host["effective_cpus"])})
 else:c.require(len(host["effective_cpus"])==1,"MAIN must pre-place peer-aware host to exact distinct CPU")
 soft,hard=resource.getrlimit(resource.RLIMIT_AS)
 c.require(hard==resource.RLIM_INFINITY,"original Docker AS hard restore")
 resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,hard))
 model=c.model(refs["model-manifest"])
 c.require(a.output is not None and not a.output.exists()and a.output.parent==c.PREP/"lowbit"
  and a.output.name.startswith("run-kivi-mixed-"),"new exact mixed output only")
 a.output=fresh_leaf(a.output)
 c.write(a.output/"FIRSTDECODE-PREDECESSOR.json",predecessor)
 if a.phase=="capture":return run(a,refs,m,model,start)
 row=next(r for r in m["files"]if Path(r["path"]).name=="cpu_phase.py")
 return c.module(row["path"],row["sha256"],"_mixed_independent_cpu_phase").run(a,refs,m,model,start)
if __name__=="__main__":main()

"""Thin reuse of the existing Devices[] software-only controller branch.
CPU8/host512MiB, phase240 including90 cleanup, no TP4/N1/model creation.
"""
import argparse,json,os,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import model_contract as c
from host_common import fresh_leaf,outputs,child,Joint,controller
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
 l=sys.modules["_kivi_mixed_source_loader"];m=c.obj(source);memory=l.memory_module(m)
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
 for name in("source","component","model-manifest"):
  p.add_argument("--"+name);p.add_argument("--"+name+"-sha256")
 p.add_argument("--output",type=Path);a=p.parse_args()
 if not a.execute:print(json.dumps(dict(enabled=False,NPU=False,model_ready=False)));return
 import resource
 start=time.monotonic();c.require(time.time()+240<=c.CUTOFF,"unchanged absolute cutoff, complete240 fit")
 refs={n:c.bound(getattr(a,n.replace("-","_")),getattr(a,n.replace("-","_")+"_sha256"))
  for n in("source","component","model-manifest")}
 m=c.source(refs["source"]);c.configure(m)
 row=next(r for r in m["files"]if Path(r["path"]).name=="prerequisite.py")
 gate=c.module(row["path"],row["sha256"],"_mixed_software_component_gate");gate.consumed(refs["component"],c.obj)
 host=c.module(c.H8,c.DEPS[str(c.H8)],"_sparq_tp4_frozen_host").cpu_view(os.getpid())
 os.sched_setaffinity(0,{min(host["effective_cpus"])})
 soft,hard=resource.getrlimit(resource.RLIMIT_AS)
 c.require(hard==resource.RLIM_INFINITY,"original Docker AS hard restore")
 resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,hard))
 model=c.model(refs["model-manifest"])
 c.require(a.output is not None and not a.output.exists()and a.output.parent==c.PREP/"lowbit"
  and a.output.name.startswith("run-kivi-mixed-software-"),"exclusive own software output")
 a.output=fresh_leaf(a.output)
 return software_only(a,refs,m,model,start)
if __name__=="__main__":main()

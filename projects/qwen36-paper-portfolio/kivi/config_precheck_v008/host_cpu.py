"""One reviewed Devices[] CPU8 precheck using the unchanged v007 controller.
No model service or NPU workload; independent standalone diagnostic, not PASS.
"""
import argparse,json,os,resource,sys,time
from pathlib import Path
BASE=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/kivi-model-firstdecode-bootstrap-v1-007")
sys.path.insert(0,str(BASE))
import model_contract as c
import host_run as h
PROBE=Path("/opt/host/vnf/austinov/model-tuning-lab/projects/qwen36-paper-portfolio/kivi/config_precheck_v008/config_cpu.py")
PROBE_SHA="b1e205d6991c84aa19e2aa96620941e8b68e85222c39d3056172c7efe8831702"
def main():
 p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true");p.add_argument("--output",type=Path);a=p.parse_args()
 if not a.execute:print(json.dumps(dict(enabled=False,NPU=False)));return
 start=time.monotonic()
 c.require(time.time()+5400<c.CUTOFF,"original fixed cutoff and bounded CPU work")
 refs={
 "source":c.bound(BASE/"SOURCE_MANIFEST.json","e20059758ee2408951066a265050d66653484174232bc118d69eca5c802f2581"),
 "component":c.bound(c.PREP/"lowbit/run-kivi-packed3-consume-main-signed-v3-20261010-001/RESULT.json","d686123d97f9856d72bd2efc4a7d3441cc0a5794250ebd8807519071af3b217d"),
 "model-manifest":c.bound(c.MODEL_REF["path"],c.MODEL_REF["sha256"]),
 "probe":c.bound(PROBE,PROBE_SHA)}
 m=c.source(refs["source"]);c.configure(m)
 import safety_host as S
 host=S.H.cpu_view(os.getpid());os.sched_setaffinity(0,{min(host["effective_cpus"])})
 soft,hard=resource.getrlimit(resource.RLIMIT_AS);c.require(hard==resource.RLIM_INFINITY,"existing Docker AS wrapper")
 resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,hard))
 model=c.model(refs["model-manifest"])
 c.require(a.output is not None and a.output.parent==c.PREP/"lowbit" and a.output.name.startswith("run-kivi-config-cpu8-"),"new exact diagnostic root")
 out=h.fresh_leaf(a.output);leaf=h.fresh_leaf(out/"cpu-preflight");h.outputs(leaf)
 joint=h.Joint(start);Own=h.controller(S,joint);ctl=Own(argparse.Namespace(output_dir=leaf),start)
 error=None;child=None;cleanup=None;report=None
 try:
  ctl.observe("config-cpu8-initial",initial=True)
  ctl.create(refs,dict(files={Path(r["path"]).name:r["sha256"] for r in m["files"]}),model,"cpu-preflight")
  child=h.child(ctl,"actual-model-scheduler-config",[str(PROBE),"--execute","--probe-source-sha256",PROBE_SHA,
   "--upstream-root",str(BASE),"--upstream-sha256",refs["source"]["sha256"],
   "--output",str(leaf/"CONFIG_PRECHECK.json"),"--cache-bytes",str(10*c.GIB),"--port","8250"],240,observe=False)
  report=c.ref(leaf/"CONFIG_PRECHECK.json")
  v=c.obj(report)
  c.require(v["status"]=="ACTUAL_MODEL_SCHEDULER_CONFIG_CHECKED" and v["full_engine_config_verified"] is False
   and v["NPU_initialized"] is False,"real partial CPU config result only")
 except BaseException as exc:error=exc
 finally:
  ctl.primary=error
  try:cleanup=ctl.cleanup()
  except BaseException as exc:joint.secondary.append(repr(exc))
  result=c.write(out/"RESULT.json",dict(schema="kivi.standalone-cpu-config-original/v1",
   status="ACTUAL_PARTIAL_CONFIG_CHECKED" if error is None and not joint.secondary and not ctl.secondary else "failed",
   upstream_source=refs["source"],probe_source=refs["probe"],host_source=c.ref(__file__),
   child=child,report=report,cleanup=cleanup,primary=repr(error) if error else None,
   secondary=joint.secondary+ctl.secondary,elapsed_seconds=time.monotonic()-start,
   NPU=False,model_ready=False,performance_ready=False,full_engine_config_verified=False))
 print(json.dumps(dict(result=result,status=c.obj(result)["status"])),flush=True)
 if error:raise error
 c.require(not joint.secondary and not ctl.secondary,"actual cleanup also required")
if __name__=="__main__":main()

"""Bounded no-device official-image wiring for the new R45 startup facade."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
W=Path(__file__).resolve().parent.parent
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
NAME="hypic-r45-worker-loader-image-20261029"
ROOT=Path("/opt/host/vnf/cch-hypic-independent-20261028/r45-worker-loader-image-20261029")
INNER=r'''
import hashlib,inspect,json,sys
from pathlib import Path
from compilation_budget_r45 import worker_loader as w
path=Path("/probe/R45_COMPILATION_BUDGET_ON_MANIFEST_20261029.json")
mp,m,cfg=w._manifest(path)
source=Path(w.__file__).read_bytes()
for name,value in vars(w).items():
 if inspect.isfunction(value)and value.__module__==w.__name__:w.verify_raw_function(w,source,value,name=name)
events=[]
observer=w._activate_compilation(m,events.append)
health=observer.health()
observer.stop()
assert observer.closed and not health["failed"] and health["calls"]==0
assert len(events)==1 and events[0]["event"]=="r45_compilation_observer_installed"
assert w.WORKER not in sys.modules
print(json.dumps({"actual_loader_manifest_and_source_functions_verified":True,
 "actual_loader_observer_factory_and_slot_uninstall":True,"health":health,
 "original438_runtime_and_four_new_sources":len([p for p in m["source_sha256"]if p.endswith(".py")]),
 "loader_sha256":hashlib.sha256(source).hexdigest(),"manifest_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
 "events":events,"native_worker_import_executed":False,"device_allocation":False,
 "scope":"CPU facade source/ABI only; no native worker execution, TP activation, backend compilation, numerical/performance or real rollback acceptance."}))
'''
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(plan_path):
 plan_path=Path(plan_path).resolve();p=json.loads(plan_path.read_bytes())
 if (plan_path.parent!=W or p.get("schema")!="hypic-r45-loader-image-plan/v1"
     or p.get("image")!=IMAGE or p.get("root")!=str(ROOT)or p.get("name")!=NAME
     or p.get("helper_sha256")!=sha(__file__)or p.get("inner_sha256")!=hashlib.sha256(INNER.encode()).hexdigest()):
  raise ValueError("exact new source/CPU-only plan required")
 manifest=W/"R45_COMPILATION_BUDGET_ON_MANIFEST_20261029.json"
 if p.get("manifest_sha256")!=sha(manifest):raise ValueError("new manifest source drift")
 sources=json.loads(manifest.read_bytes())["source_sha256"]
 for n,h in sources.items():
  f=(W/n).resolve()
  if not f.is_relative_to(W)or sha(f)!=h:raise ValueError("runtime source drift: "+n)
 if ROOT.exists()or ROOT.is_symlink():raise ValueError("new immutable CPU evidence root required")
 old=subprocess.run(["docker","ps","-a","--filter","name=^/"+NAME+"$","--format","{{.ID}}"],capture_output=True,text=True,check=True)
 if old.stdout.strip():raise ValueError("exact CPU name must be unused")
 ROOT.mkdir()
 argv=["docker","create","--name",NAME,"--label","hypic.owner=hypic-independent-20261013",
  "--label","hypic.attempt=r45-worker-loader-image-20261029","--network","none","--cpuset-cpus","112-119",
  "--memory","8g","--pids-limit","256","-v",str(W)+":/probe:ro",
  "-v","/usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64:ro",
  "-e","PYTHONPATH=/probe","-e","PYTHONDONTWRITEBYTECODE=1",
  "-e","INDEPENDENT_GRAPH_HYPIC=0","-e","INDEPENDENT_COMPILATION_BUDGET=0",
  IMAGE,"python3","-B","-c",INNER]
 creation=subprocess.run(argv,capture_output=True,text=True,check=True)
 cid=creation.stdout.strip()
 if len(cid)!=64 or any(x not in"0123456789abcdef"for x in cid):raise ValueError("exact CPU CID required")
 spec=json.loads(subprocess.check_output(["docker","inspect",cid]))[0]
 if(spec["Id"]!=cid or spec["Image"]!=IMAGE or spec["HostConfig"].get("Privileged")
    or spec["HostConfig"].get("Devices")or spec["HostConfig"].get("NetworkMode")!="none"):
  raise ValueError("no-device official image declaration required")
 raw={"plan_sha256":sha(plan_path),"helper_sha256":sha(__file__),"inner_sha256":p["inner_sha256"],
      "manifest_sha256":sha(manifest),"cid":cid,"argv":argv,"declaration":spec,"no_devices":True}
 error=None
 try:
  result=subprocess.run(["docker","start","-a",cid],capture_output=True,text=True,timeout=180)
  raw.update(exit=result.returncode,stdout=result.stdout,stderr=result.stderr)
 except BaseException as e:
  error=e;raw["controller_error"]={"type":type(e).__name__,"message":str(e)}
 finally:
  current=json.loads(subprocess.check_output(["docker","inspect",cid]))[0]
  if(current["Id"]!=cid or current["Config"].get("Labels",{}).get("hypic.attempt")!="r45-worker-loader-image-20261029"):
   raise ValueError("exact CPU cleanup ownership lost")
  raw["terminal_state_before_cleanup"]=current["State"]
  subprocess.run(["docker","rm","-f",cid],capture_output=True,text=True,check=True)
  q=subprocess.run(["docker","inspect",cid],capture_output=True,text=True)
  raw["exact_cpu_container_absent"]=q.returncode!=0 and q.stdout.strip()=="[]"and("No such object"in q.stderr or"No such container"in q.stderr)
  for n,h in sources.items():
   if sha(W/n)!=h:raise ValueError("runtime source changed during CPU probe: "+n)
  data=(json.dumps(raw,sort_keys=True)+"\n").encode()
  with(ROOT/"result.json").open("xb")as f:f.write(data);f.flush();os.fsync(f.fileno())
  print(json.dumps({"path":str(ROOT/"result.json"),"sha256":hashlib.sha256(data).hexdigest(),"exit":raw.get("exit"),
                   "exact_cpu_container_absent":raw["exact_cpu_container_absent"],"stdout":raw.get("stdout"),"stderr":raw.get("stderr")}))
 if error:raise error
 if raw["exit"]!=0 or not raw["exact_cpu_container_absent"]:raise RuntimeError("CPU loader wiring failed")
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--plan",required=True);run(p.parse_args().plan)

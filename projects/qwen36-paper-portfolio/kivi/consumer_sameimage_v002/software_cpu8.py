"""MAIN-only same660 Devices=[] software184 through ORIGINAL CPU8 controller.
No mathematical/reference implementation, no model/NPU start, default OFF.
"""
import argparse,hashlib,importlib.util,json,os,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
REMOTE_ROOT="/cache/cch/qwen36-paper-preparation-20261007/recurrent/kivi-consumer-sameimage-software-v002-20261011"
PHASE=270;CHILD=150
def need(value,message):
 if not value:raise ValueError(message)
def wire(row,limit=128*1024):
 need(type(row)is dict and set(row)=={"path","bytes","sha256"},"exact source Ref3")
 p=Path(row["path"]);need(p.is_absolute()and not p.is_symlink()and p.resolve()==p and p.is_file(),"ordinary source")
 b=p.read_bytes();need(type(row["bytes"])is int and 0<len(b)==row["bytes"]<=limit
  and hashlib.sha256(b).hexdigest()==row["sha256"],"complete source bytes/SHA")
 return b
def load(row,name):
 need(name not in sys.modules,"no ambient software module")
 b=wire(row);compile(b,row["path"],"exec")
 spec=importlib.util.spec_from_file_location(name,row["path"]);mod=importlib.util.module_from_spec(spec)
 sys.modules[name]=mod
 try:spec.loader.exec_module(mod)
 except BaseException:sys.modules.pop(name,None);raise
 return mod
def audited_profile(digest):
 p=HERE/"SOURCE_MANIFEST.json";b=p.read_bytes()
 need(hashlib.sha256(b).hexdigest()==digest,"exact software wrapper source")
 m=json.loads(b)
 for name,row in m["files"].items():
  need(row["path"]==str(HERE/name),"wrapper exact file location");wire(row)
 profile=json.loads(wire(m["mounts"]))
 need(profile["schema"]=="kivi.reviewed-consumer-software-mounts/v1"
  and profile["Devices"]==[]and profile["software_tests"]==184
  and profile["default_enabled"]is profile["NPU"]is False,"source-qualified Devices[] software only")
 return m,profile
def extra_mounts(core,p,wrapper_manifest):
 mounts={}
 def add(src,dest):
  need(type(dest)is str and Path(dest).is_absolute()and ".."not in Path(dest).parts
   and dest not in mounts,"unique exact readonly alias")
  mounts[dest]=(src,False)
 for q in p["source_roots"]:
  need(Path(q).is_dir()and Path(q).resolve()==Path(q)and not Path(q).is_symlink(),"exact reviewed software source root")
  add(q,q)
 for q in (p["whole_source"],p["raw_source"],wrapper_manifest):
  core.read(q);add(q["path"],q["path"])
 for row in p["reviewed_aliases"]:
  need(row["RW"]is False,"readonly infrastructure alias");core.read(row["source"])
  add(row["source"]["path"],row["destination"])
 for q in p["reviewed_peer"]+p["actual_artifacts"]:
  core.read(q);add(q["path"],q["path"])
 return mounts
def guest_args(profile,output):
 raw=Path(profile["raw_source"]["path"]).parent;whole=Path(profile["whole_source"]["path"]).parent
 return [str(raw/"main.py"),"--execute","--mode","software","--source-manifest-sha256",profile["raw_source"]["sha256"],
  "--base-whole",str(whole),"--producer-archive",str(Path(profile["producer_source"]["path"]).parent),
  "--reviewed-deps","/kivi-reviewed-deps","--peer-source-archive",str(Path(profile["reviewed_peer"][0]["path"]).parent),
  "--output",str(output)]
def run(a):
 start=time.monotonic();m,profile=audited_profile(a.source_sha256)
 whole=json.loads(wire(profile["whole_source"]));raw=json.loads(wire(profile["raw_source"]))
 need(raw["base_whole"]==profile["whole_source"]and raw["software_tests"]==184
  and whole["producer_source"]==profile["producer_source"],"exact whole/raw/producer closure")
 core_row=dict(path=str(Path(profile["whole_source"]["path"]).parent/"consume_whole.py"),
  **whole["files"]["consume_whole.py"])
 core=load(core_row,"_kivi_consumer_software_whole")
 ctx=core.Context(profile["producer_source"]);c=ctx.c
 need("model_contract"not in sys.modules,"no foreign controller namespace");sys.modules["model_contract"]=c
 S=core.source_module(ctx.own["safety_host.py"],"safety_host")
 H=core.source_module(ctx.own["host_run.py"],"_kivi_consumer_original_host")
 adapter=core.source_module(dict(path=str(Path(profile["raw_source"]["path"]).parent/"cpu_raw_resources.py"),
  **raw["files"]["cpu_raw_resources.py"]),"_kivi_consumer_cpu_resources")
 host=S.H.cpu_view(os.getpid())
 need(type(a.host_cpu)is int and a.host_cpu in host["effective_cpus"],"MAIN explicit eligible host CPU")
 os.sched_setaffinity(0,{a.host_cpu})
 adapter.install(S,dict(mode="standalone"),opt_in=True,reviewed_profile=raw["reviewed_peer_profile"])
 # The old mathematical consumer is NOT invoked by this software-only wrapper.
 record=core.obj(profile["actual_artifacts"][1])
 need(record["source"]==ctx.producer,"exact original018 fixture source")
 refs=dict(source=ctx.producer,component=record["component"],software=record["software"])
 refs["model-manifest"]=record["model_manifest"]
 need(refs["model-manifest"]==ctx.m["model_manifest"]and refs["component"]==ctx.m["packed3_qualification_ref"],
  "unchanged original input/source identity")
 model=c.obj(refs["model-manifest"]) # metadata only: no weights loaded/hashed by this wrapper
 need(model["host_model_root"]=="/cache/efim/Qwen3.6-27B"and model["image_id"]==c.IMAGE,"actual checkpoint mount metadata")
 extras=extra_mounts(core,profile,core.ref(HERE/"SOURCE_MANIFEST.json"))
 co=H.Joint(start);co.deadline=start+PHASE
 Original=H.controller(S,co)
 class SoftwareCPU(Original):
  def create_owned(self,sources):
   need(self.expected["arm"]=="cpu-preflight","cannot create NPU stage")
   for dest,value in extras.items():
    need(dest not in self.expected["mounts"]or tuple(self.expected["mounts"][dest])==value,"no mount shadow/RW drift")
    self.expected["mounts"][dest]=value
   return super().create_owned(sources)
 source_map=dict(files={Path(q["path"]).name:q["sha256"]for q in ctx.m["files"]})
 ctl=None;primary=None;child=None;report=None;cleanup=None;actual=None
 output=c.ordinary(a.output)
 need(output.parent==c.PREP/"lowbit"and output.name.startswith("run-kivi-consumer-software184-")
  and not output.exists(),"fresh exact standalone software output")
 try:
  H.fresh_leaf(output);leaf=H.fresh_leaf(output/"cpu-preflight");H.outputs(leaf)
  ctl=SoftwareCPU(argparse.Namespace(output_dir=leaf),start);ctl.deadline=co.deadline
  ctl.observe("consumer-software184-preflight",initial=True)
  ctl.create(refs,source_map,model,"cpu-preflight")
  actual=ctl.inspect()[0]
  need(actual["HostConfig"].get("Devices",[])==[]and not actual["HostConfig"].get("DeviceRequests"),
   "actual device-free CPU8 owner")
  args=guest_args(profile,leaf/"SOFTWARE184.json")
  # Bound the genuine child, not a rewritten suite or extracted validator.
  program="import resource,runpy,sys;resource.setrlimit(resource.RLIMIT_CPU,(120,120));resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));sys.argv="+repr(args)+";runpy.run_path(sys.argv[0],run_name='__main__')"
  child=H.child(ctl,"software184",["-c",program],CHILD,observe=False)
  report=c.ref(leaf/"SOFTWARE184.json");row=c.obj(report)
  need(row["source"]==profile["raw_source"]and row["tests"]==184 and row["successful"]is True
   and row["primary"]is None and row["software_only"]is True
   and all(row[k]is False for k in("NPU","model_ready","performance_ready","run_authority","whole176")),
   "actual complete184 software only")
  ctl.observe("consumer-software184-complete")
 except BaseException as error:primary=error
 finally:
  if ctl is not None and ctl.cid:
   ctl.primary=primary
   try:cleanup=ctl.cleanup()
   except BaseException as error:co.secondary.append(repr(error))
   co.secondary.extend(ctl.secondary)
  if time.monotonic()>co.deadline:co.secondary.append("software270 whole exhausted")
  if co.cleanup_used>90:co.secondary.append("software90 cleanup exhausted")
  value=dict(schema="kivi.actual-consumer-software-cpu-host/v1",source=core.ref(HERE/"SOURCE_MANIFEST.json"),
   raw_source=profile["raw_source"],whole_source=profile["whole_source"],producer_source=ctx.producer,
   status="SOFTWARE184_AND_EXACT_CPU8_RELEASED"if primary is None and not co.secondary and report else"failed",
   primary=repr(primary)if primary else None,secondary=co.secondary,tests=184,
   actual_child=child,software_report=report,owned=core.ref(ctl.out/"OWNED.json")if ctl and ctl.cid else None,
   cleanup=cleanup,observations=ctl.observations if ctl else[],elapsed_seconds=time.monotonic()-start,
   phase_seconds=PHASE,child_seconds=CHILD,cleanup_seconds=90,
   Devices=[],NPU=False,model_ready=False,performance_ready=False,run_authority=False,
   independent_raw_checked=False,weights_loaded=False,model_started=False)
  result=c.write(output/"RESULT.json",value)
  print(json.dumps(result),flush=True)
 if primary:raise RuntimeError("software first-fault retained "+str(result))from primary
 need(value["status"]=="SOFTWARE184_AND_EXACT_CPU8_RELEASED","software release/secondary failure")
 return 0
def main():
 p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true")
 p.add_argument("--source-sha256");p.add_argument("--host-cpu",type=int);p.add_argument("--output",type=Path)
 a=p.parse_args()
 if not a.execute:
  print(json.dumps(dict(default_enabled=False,NPU=False,model_ready=False,performance_ready=False)));return 0
 need(a.source_sha256 and a.output and a.host_cpu is not None,"MAIN source/CPU/new output required")
 return run(a)
if __name__=="__main__":raise SystemExit(main())

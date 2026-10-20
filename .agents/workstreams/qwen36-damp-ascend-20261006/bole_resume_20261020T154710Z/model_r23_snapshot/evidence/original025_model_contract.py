"""AdaKV018 exact source/ABI/materialization facade. Never grants ready from source."""
import hashlib,importlib.util,json,os,re,subprocess,sys,time
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab");KERNEL=ROOT
GIB=1024**3;PY="/usr/local/python3.12.13/bin/python3"
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
CUT="2026-10-12T07:00:25+00:00";CUTOFF=1791788425;HBM_RESERVE_MIB=3072
PREP=Path("/cache/cch/qwen36-paper-preparation-20261007")
AUDIT=BASE/"audit_source"
AUDIT_SHA="31e2df3e3d807404c1912023a9222054b96c056d5737cfcd32f8539e09f63cbe"
NATIVE=PREP/"sparse/adakv-native-serial-once-v1-016"
NATIVE_SHA="201ad2395f3f2213cd8e8d5c5486d6d1f94633615b94f279c42a33db3e2e757d"
CONSUMER=Path("/cache/cch/qwen36-paper-preparation-20261007/sparse/adakv-native-derived-consumer-v1-017")
CONSUMER_SHA="2a8a6497413ddaaa3101df1fcea0ca6f55c0aa0e0e401567381ac4bb117411d5"
H8=ROOT/"projects/kvbuffer-parallel-ascend/tools/short_horizon_h8_gate_v4/host_run.py"
DEPS={str(H8):"4ddd75d6ce7558f0131992da3a5514df43dfb4b33f45674722ba5769ecef5e20",
 str(ROOT/"projects/kvbuffer-parallel-ascend/tools/full_matrix_host_v2/host.py"):"ab0296c698df00c9c3b2ce377601f6d6723adde6efb4a9e65407beca51ba5f86",
 str(ROOT/"projects/kvbuffer-parallel-ascend/tools/saved_step_native_order_v2/host_run.py"):"86c1ca7f59c6ad5b2b4d5efb155394455a12376cf368e06f9e2e13d39b7192fc"}
MODEL_REF=dict(path=str(PREP/"sparse/actual-input-inventory-v1-001/MAIN-original-checkpoint-fullhash-20261008-001/ACTUAL_MODEL_MANIFEST.json"),sha256="11ac18fa31878609b6b56a9c9213d12729cdb466d14c587efcf6d261566a706c")
CONFIG_SHA="69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c"
PROFILE=dict(endpoint="/v1/completions",prompt_count=1,n=1,beam_search=False,streaming_input=False)
ACTIVE=None
def require(v,why):
 if not v:raise ValueError(why)
def ordinary(p):
 p=Path(p);require(p.is_absolute() and p.resolve()==p and ".."not in p.parts and not p.is_symlink(),"ordinary exact absolute path");return p
def canonical(x):return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
def sha(p):
 p=ordinary(p);require(p.is_file(),"actual regular file");h=hashlib.sha256()
 with p.open("rb")as s:
  for b in iter(lambda:s.read(1024**2),b""):h.update(b)
 return h.hexdigest()
def bound(p,h):
 p=ordinary(p);require(re.fullmatch("[0-9a-f]{64}",h or"")and sha(p)==h,"actual Ref whole SHA");return dict(path=str(p),sha256=h)
def ref(p):return bound(p,sha(p))
def obj(r,limit=8*1024**2):
 p=Path(bound(r["path"],r["sha256"])["path"]);require(p.stat().st_size<=limit,"bounded whole evidence JSON")
 def pairs(items):
  d={}
  for k,v in items:require(k not in d,"duplicate original JSON key");d[k]=v
  return d
 def bad(v):raise ValueError("nonfinite JSON "+v)
 return json.loads(p.read_bytes(),object_pairs_hook=pairs,parse_constant=bad)
def write(p,x,limit=8*1024**2):
 p=ordinary(p);require(p.parent.is_dir()and not p.exists(),"exclusive owned evidence")
 b=canonical(x)+b"\n";require(0<limit<=65*1024**2 and len(b)<=limit,"bounded complete JSON")
 tmp=p.with_name("."+p.name+".pending-"+str(time.time_ns()))
 with tmp.open("xb")as s:require(s.write(b)==len(b),"whole unpublished bytes");s.flush();os.fsync(s.fileno())
 os.link(tmp,p);fd=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)
 return ref(p)
def module(path,digest,name):
 p=Path(bound(path,digest)["path"])
 if name in sys.modules:
  old=sys.modules[name];require(Path(old.__file__).resolve()==p and sha(p)==digest,"foreign preloaded namespace");return old
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m
 try:spec.loader.exec_module(m)
 except BaseException:sys.modules.pop(name,None);raise
 require(Path(m.__file__).resolve()==p and sha(p)==digest,"module source unchanged");return m
def source(r):
 m=obj(r);require(m["schema"]=="adakv.tp4-model-once-source/v1"and m["root"]==str(BASE)and
  m["default_enabled"]is m["ready"]is False,"exact current private024 not historical source")
 for row in m["files"]+m["dependencies"]:
  bound(row["path"],row["sha256"]);require("bytes"not in row or Path(row["path"]).stat().st_size==row["bytes"],"whole source byte count")
 require(m["audit_source"]==dict(path=str(AUDIT/"SOURCE_MANIFEST.json"),sha256=AUDIT_SHA)and
  m["native_source"]==dict(path=str(NATIVE/"SOURCE_MANIFEST.json"),sha256=NATIVE_SHA)and
  m["native_consumer_source"]==dict(path=str(CONSUMER/"SOURCE_MANIFEST.json"),sha256=CONSUMER_SHA),"exact024 audit/native16/derived17 source predecessors")
 clock=obj(m["clock"]);require(clock["total_cutoff_epoch"]==CUTOFF,"actual authorized72h not reset")
 return m
def protected_module():
 manifest=obj(dict(path=str(NATIVE/"SOURCE_MANIFEST.json"),sha256=NATIVE_SHA))
 own={Path(r["path"]).name:r for r in manifest["files"]}
 original=list(sys.path)
 try:
  sys.path.insert(0,str(NATIVE))
  module(own["once_contract.py"]["path"],own["once_contract.py"]["sha256"],"once_contract")
  return module(own["safety_lifecycle.py"]["path"],own["safety_lifecycle.py"]["sha256"],"_adakv017_exact_protected_boundary")
 finally:sys.path[:]=original
def audit_source_identity(value):
 require(type(value)is dict and set(value)in ({"path","sha256"},{"path","sha256","bytes"}),
  "exact source identity Ref; no extra origin fields")
 identity=bound(value["path"],value["sha256"])
 if "bytes"in value:
  require(type(value["bytes"])is int and value["bytes"]>0 and
   Path(identity["path"]).stat().st_size==value["bytes"],"actual source Ref byte size")
 return identity
def audit_package(material):
 r=audit_source_identity(material["audit_source"]);root=Path(material["root"])/"service"
 require(r["path"]==str(root/"AUDIT_SOURCE_MANIFEST.json"),"actual016 relocated source")
 raw=obj(r);require(raw["root"]==str(root)and raw["schema"]=="adakv.full-request-model-source/v1"and raw["ready"]is False,"actual model audit source")
 original=obj(dict(path=str(AUDIT/"SOURCE_MANIFEST.json"),sha256=AUDIT_SHA))
 package={x["name"]:x["sha256"]for x in original["files"]if x["name"].startswith("adakv_model_gate/")}
 require({x["name"]:x["sha256"]for x in raw["files"]}==package,"all relocated016 independent algorithms byte exact")
 for row in raw["files"]:bound(root/row["name"],row["sha256"])
 return r,root
def materialization(r):
 x=obj(r);require(x["schema"]=="adakv.full-request-source-materialization/v1"and x["status"]=="SOURCE_MATERIALIZED_ONLY"and
  x["source"]==dict(path=str(AUDIT/"SOURCE_MANIFEST.json"),sha256=AUDIT_SHA)and x["ready"]is False,"actual new016 materialization")
 for row in x["files"]:bound(row["path"],row["sha256"])
 audit_package(x);return x
def model(r,host=True):
 require(r==MODEL_REF,"exact actual original checkpoint")
 m=obj(r);require(m["schema"]=="qwen36.actual-model-manifest/v1"and m["host_model_root"]=="/cache/efim/Qwen3.6-27B"and
  m["complete_file_count"]==29 and m["weight_shard_count"]==15 and m["total_bytes"]==55586107940 and
  m["image_id"]==IMAGE and m["config_sha256"]==CONFIG_SHA,"actual29file/15shard identity")
 root=Path(m["host_model_root"]if host else"/models/Qwen3.6-27B");seen=set()
 for row in m["files"]:
  name=row["relative_path"];require(name not in seen and not Path(name).is_absolute()and ".."not in Path(name).parts,"unique model files");seen.add(name)
  path=root/name;require(path.stat().st_size==row["size_bytes"],"actual model byte size");bound(path,row["sha256"])
 return m
def component(r,replay=False):
 x=obj(r);require(x["schema"]=="adakv.native-serial-original-consumed/v1"and x["status"]=="NATIVE32X160_CONSUMED"and
  x["source"]==dict(path=str(NATIVE/"SOURCE_MANIFEST.json"),sha256=NATIVE_SHA)and
  x.get("consumer_source")==dict(path=str(CONSUMER/"SOURCE_MANIFEST.json"),sha256=CONSUMER_SHA)and x["cases"]==32 and x["steps"]==5120 and
  x["selector_verified"]is x["model"]is x["performance"]is x["quality"]is x["ready"]is False,"actual016 ABI is not selector/model ready")
 for key in("original_terminal","original_result","authority","independent_rows","row_consumer_child"):obj(x[key])
 return x
def configure(m,material):
 global ACTIVE
 require(ACTIVE is None,"one explicit runtime source context no namespace rewriting")
 ACTIVE=(m,material)
def required_source_mounts():
 require(ACTIVE is not None,"explicit source context before creating guest")
 m,mat=ACTIVE
 native=obj(dict(path=str(NATIVE/"SOURCE_MANIFEST.json"),sha256=NATIVE_SHA))
 consumer=obj(dict(path=str(CONSUMER/"SOURCE_MANIFEST.json"),sha256=CONSUMER_SHA))
 require(consumer["producer_source"]==dict(path=str(NATIVE/"SOURCE_MANIFEST.json"),sha256=NATIVE_SHA),
  "explicit derived17 immutable16 producer")
 refs=m["dependencies"]+mat["files"]+native["files"]+native["dependencies"]+consumer["files"]+consumer["dependencies"]
 for key in("service_source","graph_source","caller_source","audit_source"):
  manifest=obj(mat[key])
  def collect(value):
   if type(value)is dict:
    if "path"in value and "sha256"in value and Path(value["path"]).is_absolute():
     bound(value["path"],value["sha256"]);refs.append(value)
    else:
     for item in value.values():collect(item)
   elif type(value)is list:
    for item in value:collect(item)
  collect(manifest)
 paths=[r["path"]for r in refs]
 roots=set(DEPS)|{str(BASE),str(ROOT),str(AUDIT),str(NATIVE),str(CONSUMER),str(Path(mat["root"]))}
 for path in paths:
  p=Path(path)
  if not any(p==Path(root)or Path(root)in p.parents for root in roots):roots.add(str(p.parent))
 return sorted(root for root in roots if not any(Path(parent)in Path(root).parents for parent in roots))
def component_readonly_mounts(r):
 x=component(r);roots=set()
 def walk(v):
  if type(v)is dict:
   if "path"in v and "sha256"in v:
    bound(v["path"],v["sha256"]);roots.add(str(Path(v["path"]).parent))
   else:
    for q in v.values():walk(q)
  elif type(v)is list:
   for q in v:walk(q)
 walk(x);return {root:(root,False)for root in roots if not any(Path(parent)in Path(root).parents for parent in roots)}
def docker_argv(cid,args):
 require(re.fullmatch("[a-f0-9]{64}",cid or""),"exact owned CID")
 return ["/usr/bin/docker","exec",cid,"/bin/bash","-c",'source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"',"kvbp-diagnostic",PY,"-B",*args]
def prompt_ids(i):
 require(type(i)is int and 0<=i<40,"fixed40 prompt index")
 return [1000+j%257 for j in range(16384)]+[2000+(i*131+j*17)%4093 for j in range(16384)]
def digest(x):return hashlib.sha256(canonical(x)).hexdigest()
def component_rows(component_ref,out):
 """Fresh exact derived17 CLI: immutable16 producer, isolated original013 rows, no namespace injection."""
 old=component(component_ref);whole=obj(old["original_terminal"]);outer=whole.get("structuredContent",whole)
 op=outer["operation"];record=op["result"]["record"]
 stamp=str(time.time_ns())
 replay=PREP/"lowbit"/("run-adakv-native-serial-consume-014-main-017-"+stamp)
 row_output=PREP/"lowbit"/("run-adakv-native-row-consumer-013-main-017-"+stamp)
 require(not replay.exists() and not row_output.exists() and Path(out).is_dir(),"new independent original016 replay and original013 row leaves")
 argv=["/usr/bin/python3","-B",str(CONSUMER/"consume_once.py"),"--execute",
  "--source",old["source"]["path"],"--source-sha256",old["source"]["sha256"],
  "--consumer-source",old["consumer_source"]["path"],"--consumer-source-sha256",old["consumer_source"]["sha256"],
  "--result",old["original_result"]["path"],"--result-sha256",old["original_result"]["sha256"],
  "--terminal",old["original_terminal"]["path"],"--terminal-sha256",old["original_terminal"]["sha256"],
  "--peer",op["targetPeerId"],"--operation",outer["operationId"],
  "--expected-command",record["command"],"--expected-args",json.dumps(record["args"]),
  "--output",str(replay),"--row-output",str(row_output)]
 so=Path(out)/"ORIGINAL015.stdout";se=Path(out)/"ORIGINAL015.stderr";primary=None
 with so.open("x")as stdout,se.open("x")as stderr:
  child=subprocess.Popen(argv,stdout=stdout,stderr=stderr,cwd=ROOT)
  try:child.wait(timeout=75)
  except BaseException as error:
   primary=error;child.kill();child.wait(timeout=10)
 cr=write(Path(out)/"ORIGINAL015_REPLAY_CHILD.json",dict(argv=argv,pid=child.pid,exit_code=child.returncode,
  primary=repr(primary)if primary else None,termination_observed=child.poll()is not None,
  stdout=ref(so),stderr=ref(se),source=dict(path=str(NATIVE/"SOURCE_MANIFEST.json"),sha256=NATIVE_SHA),
  consumer_source=dict(path=str(CONSUMER/"SOURCE_MANIFEST.json"),sha256=CONSUMER_SHA)))
 if primary:raise primary
 require(child.returncode==0,"actual source-bound derived17 original016 whole CLI failed; retained "+str(cr))
 rr=ref(replay/"RESULT.json");result=component(rr)
 require(result["authority"]!=old["authority"],"actual fresh5120 authority not reused bool")
 return rr

def audit_resource(material,source_package=None):
 _,runtime_root=audit_package(material)
 root=runtime_root if source_package is None else ordinary(source_package)
 require(root in(runtime_root,AUDIT),"explicit verified private or materialized audit package")
 original=obj(dict(path=str(AUDIT/"SOURCE_MANIFEST.json"),sha256=AUDIT_SHA))
 own={r["name"]:r for r in original["files"]}
 package=module(root/"adakv_model_gate/__init__.py",own["adakv_model_gate/__init__.py"]["sha256"],"adakv_model_gate")
 require(list(package.__path__)==[str(root/"adakv_model_gate")]and
  package.__spec__.origin==str(root/"adakv_model_gate/__init__.py"),
  "exact source-bound audit package search path")
 return module(root/"adakv_model_gate/resource_guard.py",own["adakv_model_gate/resource_guard.py"]["sha256"],"adakv_model_gate.resource_guard")

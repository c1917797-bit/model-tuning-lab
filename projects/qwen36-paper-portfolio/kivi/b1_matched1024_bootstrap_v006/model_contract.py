"""Concrete KIVI first-decode adaptation of the reviewed Ada025 safety facade.
Only scope/Refs/argv/mounts differ. No borrowed Ada model authority.
"""
import hashlib,importlib.util,json,os,re,sys,time
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab");KERNEL=ROOT
GIB=1024**3;PY="/usr/local/python3.12.13/bin/python3"
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
CUT="2026-10-12T07:00:25+00:00";CUTOFF=1791788425;HBM_RESERVE_MIB=3072
PREP=Path("/cache/cch/qwen36-paper-preparation-20261007")
H8=ROOT/"projects/kvbuffer-parallel-ascend/tools/short_horizon_h8_gate_v4/host_run.py"
DEPS={str(H8):"4ddd75d6ce7558f0131992da3a5514df43dfb4b33f45674722ba5769ecef5e20",
 str(ROOT/"projects/kvbuffer-parallel-ascend/tools/full_matrix_host_v2/host.py"):"ab0296c698df00c9c3b2ce377601f6d6723adde6efb4a9e65407beca51ba5f86",
 str(ROOT/"projects/kvbuffer-parallel-ascend/tools/saved_step_native_order_v2/host_run.py"):"86c1ca7f59c6ad5b2b4d5efb155394455a12376cf368e06f9e2e13d39b7192fc"}
MODEL_REF=dict(path=str(PREP/"sparse/actual-input-inventory-v1-001/MAIN-original-checkpoint-fullhash-20261008-001/ACTUAL_MODEL_MANIFEST.json"),sha256="11ac18fa31878609b6b56a9c9213d12729cdb466d14c587efcf6d261566a706c")
CONFIG_SHA="69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c"
ACTIVE=None
SCREEN_ARM=None
def set_arm(arm):
 global SCREEN_ARM
 require(SCREEN_ARM is None and arm in('dense','candidate'),'one explicit matched algorithm arm')
 SCREEN_ARM=arm
def require(v,why):
 if not v:raise ValueError(why)
def ordinary(p):
 p=Path(p);require(p.is_absolute()and p.resolve()==p and ".."not in p.parts and not p.is_symlink(),"ordinary exact absolute path");return p
def canonical(x):return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
def sha(p):
 p=ordinary(p);require(p.is_file(),"actual regular file");h=hashlib.sha256()
 with p.open("rb")as s:
  for b in iter(lambda:s.read(1024**2),b""):h.update(b)
 return h.hexdigest()
def bound(p,h):
 p=ordinary(p);require(re.fullmatch("[0-9a-f]{64}",h or"")and sha(p)==h,"actual complete SHA")
 return dict(path=str(p),bytes=p.stat().st_size,sha256=h)
def ref(p):return bound(p,sha(p))
def checked(r):
 require(type(r)is dict and set(r)in({"path","sha256"},{"path","bytes","sha256"}),"strict2/3 original Ref")
 actual=bound(r["path"],r["sha256"])
 if "bytes"in r:require(type(r["bytes"])is int and r["bytes"]>0 and r["bytes"]==actual["bytes"],"actual bytes nonbool")
 return actual
def obj(r,limit=8*1024**2):
 r=checked(r);require(r["bytes"]<=limit,"bounded whole evidence JSON")
 def pairs(rows):
  answer={}
  for k,v in rows:require(k not in answer,"duplicate original JSON key");answer[k]=v
  return answer
 def bad(v):raise ValueError("nonfinite JSON "+v)
 return json.loads(Path(r["path"]).read_bytes(),object_pairs_hook=pairs,parse_constant=bad)
def write(p,x,limit=8*1024**2):
 p=ordinary(p);require(p.parent.is_dir()and not p.exists(),"exclusive owned evidence")
 b=canonical(x)+b"\n";require(len(b)<=limit<=65*1024**2,"bounded complete JSON")
 tmp=p.with_name("."+p.name+".pending-"+str(time.time_ns()))
 with tmp.open("xb")as s:require(s.write(b)==len(b),"whole write");s.flush();os.fsync(s.fileno())
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
 return m
def source(r):
 l=module(BASE/"loader.py",next(x["sha256"]for x in obj(r)["files"]if Path(x["path"]).name=="loader.py"),"_kivi_firstdecode_source_loader")
 m,actual=l.source(r["sha256"]);require(actual==checked(r),"exact current source context")
 return m
def configure(m):
 global ACTIVE
 require(ACTIVE is None,"one explicit source context");ACTIVE=m
def role(name):
 require(ACTIVE is not None,"source context first");return ACTIVE["runtime_roles"][name]
def protected_module():
 # This imports ONLY the exact reviewed infrastructure function, never Ada numerical receipts.
 contract=role("protected_contract");life=role("protected_lifecycle")
 original=list(sys.path)
 try:
  sys.path.insert(0,str(Path(contract["path"]).parent))
  module(contract["path"],contract["sha256"],"once_contract")
  return module(life["path"],life["sha256"],"_kivi_firstdecode_protected_boundary")
 finally:sys.path[:]=original
def required_source_mounts():
 require(ACTIVE is not None,"source context before guest")
 refs=ACTIVE["files"]+ACTIVE["dependencies"]+[ACTIVE["donor_manifest"]]
 roots={str(BASE),str(ROOT)}
 for row in refs:
  checked(row);p=Path(row["path"])
  if not any(p==Path(q)or Path(q)in p.parents for q in roots):roots.add(str(p))
 return sorted(q for q in roots if not any(Path(p)in Path(q).parents for p in roots))
def component_readonly_mounts(r):
 x=obj(r);roots={}
 def walk(v):
  if type(v)is dict:
   if set(v)in({"path","sha256"},{"path","sha256","bytes"}):
    rr=checked(v);roots[rr["path"]]=(rr["path"],False)
   else:
    for z in v.values():walk(z)
  elif type(v)is list:
   for z in v:walk(z)
 walk(x);roots[r["path"]]=(r["path"],False)
 return roots
def model(r,host=True):
 require({k:r[k]for k in("path","sha256")}==MODEL_REF,"original complete checkpoint identity")
 m=obj(r);require(m["schema"]=="qwen36.actual-model-manifest/v1"and m["host_model_root"]=="/cache/efim/Qwen3.6-27B"
  and m["complete_file_count"]==29 and m["weight_shard_count"]==15 and m["total_bytes"]==55586107940
  and m["image_id"]==IMAGE and m["config_sha256"]==CONFIG_SHA,"same29file15shard model")
 root=Path(m["host_model_root"]if host else"/models/Qwen3.6-27B");seen=set()
 for row in m["files"]:
  name=row["relative_path"];require(name not in seen and not Path(name).is_absolute()and ".."not in Path(name).parts,"unique actual model files");seen.add(name)
  path=root/name;require(path.stat().st_size==row["size_bytes"],"actual model bytes");bound(path,row["sha256"])
 return m
def docker_argv(cid,args):
 require(re.fullmatch("[a-f0-9]{64}",cid or""),"exact own CID")
 return ["/usr/bin/docker","exec",cid,"/bin/bash","-c",'source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"',"kivi-firstdecode",PY,"-I","-B",*args]
def output_scan(root):
 scanner=role("output_scanner");s=module(scanner["path"],scanner["sha256"],"_kivi_firstdecode_strict_output")
 # Same stock TMPDIR alias; scope only actual direct owned CPU/candidate stages.
 parents=[Path(root)/n for n in("cpu-preflight","candidate")if(Path(root)/n).is_dir()]
 raw=s.scan(root,socket_parent=parents,ipc_source=s.IPC_SOURCE)
 used=s.consume(raw,root);return raw,used

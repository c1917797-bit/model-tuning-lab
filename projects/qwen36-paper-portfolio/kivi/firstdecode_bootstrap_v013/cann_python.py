"""Image660 CANN Python namespace qualification, not import/device permission.
Explicit fixed root under -I; no environment-wide PYTHONPATH assimilation.
CPU resolves and hashes only. N1/real worker separately prove imported ACL.
"""
import hashlib,importlib.machinery,importlib.util,os,sys,types
from pathlib import Path
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
ROOT="/usr/local/Ascend/cann-9.1.0/python/site-packages"
ACL=ROOT+"/acl.so"
ACL_BYTES=1073832
ACL_SHA="34303ba302bde3cd44dd5bd7bc01fb216cbc5123e7db797a9834c9fa58e3f185"
ENV="/usr/local/Ascend/cann-9.1.0/set_env.sh"
ENV_BYTES=5112
ENV_SHA="de50f1bf5b960f8305792ef407e3bfc3fc1b6d82931d0feae39ac4c965690aaf"
PROOF_SHA="8bb531a2a6d033fbed14010a5acbd0f317717fc491825a09ea09175dd72eaec9"
def need(v,m):
 if not v:raise ValueError(m)
def file_identity(path,size,digest):
 p=Path(path);need(p.is_absolute()and p.resolve()==p and not p.is_symlink()and p.is_file(),"ordinary actual CANN file")
 a=p.stat();wire=p.read_bytes();b=p.stat()
 need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(b.st_dev,b.st_ino,b.st_size,b.st_mtime_ns)
  and len(wire)==size and hashlib.sha256(wire).hexdigest()==digest,"actual whole stable CANN file identity")
 return dict(path=str(p),size_bytes=len(wire),sha256=digest)
def config(m,checked):
 x=m["cann_python_binding"]
 need(set(x)=={"image","pythonpath_root","acl_file","acl_bytes","acl_sha256","set_env_file","set_env_bytes","set_env_sha256","resolution_ref"}
  and x["image"]==IMAGE and x["pythonpath_root"]==ROOT and x["acl_file"]==ACL
  and type(x["acl_bytes"])is int and x["acl_bytes"]==ACL_BYTES and x["acl_sha256"]==ACL_SHA
  and x["set_env_file"]==ENV and type(x["set_env_bytes"])is int and x["set_env_bytes"]==ENV_BYTES
  and x["set_env_sha256"]==ENV_SHA and x["resolution_ref"]["sha256"]==PROOF_SHA,
  "one source-bound real image660 CANN root/binary/export proof")
 checked(x["resolution_ref"]);return x
def spec_identity(spec):
 need(spec is not None and spec.name=="acl"and spec.origin==ACL
  and isinstance(spec.loader,importlib.machinery.ExtensionFileLoader)
  and spec.loader.path==ACL,"actual selected ACL extension origin/loader, no Python stub")
 return dict(name=spec.name,origin=spec.origin,loader_type=type(spec.loader).__module__+"."+type(spec.loader).__qualname__,
  binary=file_identity(ACL,ACL_BYTES,ACL_SHA))
def cached(*,required=False,memcpy_required=False):
 value=sys.modules.get("acl")
 need(value is not None or not any(k.startswith("acl.")for k in sys.modules),"orphan/unknown ACL cached namespace")
 if value is None:
  need(not required and not memcpy_required,"actual ACL import has not occurred")
  return dict(imported=False,memcpy_observed=False)
 need(type(value)is types.ModuleType and getattr(value,"__file__",None)==ACL,
  "foreign cached ACL origin; never delete or replace unknown module")
 actual=spec_identity(getattr(value,"__spec__",None))
 rt=sys.modules.get("acl.rt",getattr(value,"rt",None))
 memcpy=getattr(rt,"memcpy",None)if rt is not None else None
 if memcpy_required:need(callable(memcpy),"actual native ACL rt.memcpy import missing")
 return dict(imported=True,origin=actual,memcpy_observed=callable(memcpy),
  memcpy_type=(type(memcpy).__module__+"."+type(memcpy).__qualname__)if memcpy is not None else None,
  memcpy_module=getattr(memcpy,"__module__",None),import_is_not_device_correctness=True)
def install(m,checked,source):
 x=config(m,checked);before=list(sys.path)
 need(Path(ROOT).is_dir()and Path(ROOT).resolve()==Path(ROOT)and not Path(ROOT).is_symlink(),
  "actual fixed ordinary CANN Python directory")
 env=file_identity(ENV,ENV_BYTES,ENV_SHA)
 cached_before=cached()
 # Direct fixed-root resolution is source proof; this never executes ACL.
 selected=spec_identity(importlib.machinery.PathFinder.find_spec("acl",[ROOT]))
 if ROOT not in sys.path:sys.path.insert(0,ROOT)
 try:
  active=spec_identity(importlib.util.find_spec("acl"))
  need(active==selected,"effective selected ACL origin equals fixed source-pinned root")
 except BaseException:
  sys.path[:]=before;raise
 return dict(schema="kivi.actual-cann-python-binding/v1",source_ref=source,
  image=IMAGE,pythonpath_root=ROOT,set_env=env,fixed_root_resolution=selected,effective_resolution=active,
  sys_path_before=before,sys_path_after=list(sys.path),isolated_flag=sys.flags.isolated,
  cached_before=cached_before,acl_import_executed_by_helper=False,
  actual_import_required_at_N1_and_worker=True,model_ready=False,performance_ready=False)

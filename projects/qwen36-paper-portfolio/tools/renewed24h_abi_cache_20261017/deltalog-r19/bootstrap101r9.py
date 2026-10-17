"""Explicit source-bound import roots for isolated server and spawned workers."""
import hashlib,importlib,json,os,sys
from pathlib import Path
def checked(r):
 p=Path(r['path']);b=p.read_bytes()
 if not p.is_absolute() or p.is_symlink() or (len(b),hashlib.sha256(b).hexdigest())!=(r['bytes'],r['sha256']):raise ValueError('bootstrap exact source Ref')
 return p
def install(m,root):
 root=Path(root).resolve()
 if root!=Path(m['root']).resolve():raise ValueError('bootstrap own root')
 for r in m['files'].values():checked(r)
 pr=m.get('plugin_source') or m['plugin_template_ref'];pm=json.loads(checked(pr).read_bytes());plugin=Path(pr['path']).parent
 for r in pm['files'].values():checked(r)
 worker=checked(m['donor008_host_ref']).parent
 payload=m.get('firstdecode_contract',{}).get('payload_source')
 extra=()
 if payload is not None:
  pm=json.loads(checked(payload).read_bytes())
  for r in pm['files'].values():checked(r)
  extra=(Path(payload['path']).parent,)
 roots=(root,plugin,worker)+extra
 for p in reversed(roots):
  s=str(p)
  while s in sys.path:sys.path.remove(s)
  sys.path.insert(0,s)
 return roots
def package_proof(m):
 package=importlib.import_module('qwen36_deltalog_service')
 pm=json.loads(checked(m.get('plugin_source') or m['plugin_template_ref']).read_bytes())
 r=pm['files']['qwen36_deltalog_service/__init__.py'];p=checked(r)
 if Path(package.__file__).resolve()!=p.resolve():raise ValueError('bootstrap package origin')
 runtime=importlib.import_module('qwen36_deltalog_service.runtime');rr=pm['files']['qwen36_deltalog_service/runtime.py'];rp=checked(rr)
 if Path(runtime.__file__).resolve()!=rp.resolve():raise ValueError('bootstrap runtime origin')
 return dict(module=package.__name__,file=str(p),ref=r,runtime_ref=rr,pid=os.getpid(),isolated=bool(sys.flags.isolated))

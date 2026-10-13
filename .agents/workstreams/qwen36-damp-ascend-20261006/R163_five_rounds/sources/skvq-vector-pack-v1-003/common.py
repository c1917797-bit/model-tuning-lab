"""Frozen executor joins only; never creates hardware admission."""
import hashlib,importlib.util,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent
START=1791916056
CUT=1792002456
def need(v,m):
 if not v:raise ValueError(m)
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['bytes'])is int and r['bytes']>=0,'strict Ref3')
 p=Path(r['path']);need(p.is_absolute()and p.resolve()==p and not p.is_symlink()and p.is_file(),'ordinary source/input');before=p.stat();wire=p.read_bytes();after=p.stat()
 need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)and len(wire)==r['bytes']and hashlib.sha256(wire).hexdigest()==r['sha256'],'whole stable bytes');return wire
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def obj(r):return json.loads(checked(r))
def load(name,r):
 wire=checked(r);need(name not in sys.modules,'no foreign/partial module: '+name);s=importlib.util.spec_from_file_location(name,r['path']);m=importlib.util.module_from_spec(s);sys.modules[name]=m
 try:exec(compile(wire,r['path'],'exec',dont_inherit=True),m.__dict__)
 except BaseException:sys.modules.pop(name,None);raise
 need(ref(m.__file__)==r,'actual module bytes');return m
def boot(path,sha):
 own=ref(path);need(own['sha256']==sha and Path(path)==P/'SOURCE_MANIFEST.json','own manifest');m=obj(own)
 need(m['schema']=='skvq.vector256-cohort-source/v1'and m['root']==str(P)and m['default_enabled']is m['ready']is False and(m['start_epoch'],m['cutoff'])==(START,CUT),'new R156 source scope')
 for r in [*m['files'].values(),*m['dependencies']]:checked(r)
 W=load('_vector_window',m['window']);W.validate(checked(m['authority']));return own,m
def contract(m,refs):
 b=load('_vector_owner_binding',m['owner_binding']);B=b.base();A=load('_vector_controller_adapter',m['controller_adapter']);pm=obj(m['cohort_policy']);policy=load('_vector_device_policy',pm['files']['cohort_policy.py']);Q=A.private_contract(B,checked(m['donor_contract']),P,refs,policy.devices)
 Q.PHASE=180;Q.CLEANUP=60
 store=load('_vector_inspect_store',m['inspect_store']);store.install(Q,B);return B,A,Q
def publish(p,v):
 need(not p.exists()and p.parent.is_dir(),'exclusive artifact');wire=(json.dumps(v,sort_keys=True,allow_nan=False)+'\n').encode()
 with p.open('xb')as f:need(f.write(wire)==len(wire),'complete publication')
 return ref(p)

"""Exact stable streamed Ref3 checks; no expanded blob index or backend."""
import hashlib,json,os,re
from pathlib import Path
def need(v,s):
 if not v:raise ValueError(s)
def checked_path(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['path'])is str and type(r['bytes'])is int and r['bytes']>=0 and type(r['sha256'])is str and re.fullmatch('[a-f0-9]{64}',r['sha256'])is not None,'exact bounded Ref3 fields')
 p=Path(r['path']);need(p.is_absolute()and p.is_file()and not any(q.is_symlink()for q in(p,*p.parents)),'ordinary actual immutable file/parents');return p
def identity(s):return(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def ref(path):
 p=Path(path);need(p.is_absolute()and p.is_file()and not any(q.is_symlink()for q in(p,*p.parents)),'ordinary actual immutable file/parents');h=hashlib.sha256();n=0
 with p.open('rb')as f:
  before=os.fstat(f.fileno())
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b);n+=len(b)
  after=os.fstat(f.fileno())
 need(identity(before)==identity(after)==identity(p.stat())and n==before.st_size,'complete stable Ref hash read')
 return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def obj_file(r):
 p=checked_path(r);need(ref(p)==r,'exact stable streamed bytes/SHA');return p
def obj(r):return json.loads(obj_file(r).read_bytes())

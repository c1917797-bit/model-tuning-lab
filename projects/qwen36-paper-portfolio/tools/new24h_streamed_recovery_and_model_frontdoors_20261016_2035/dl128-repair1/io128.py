"""Source/JSON-only reads: bounded by actual files, streamed hashes, no backend."""
import hashlib,json,os
from pathlib import Path
def need(v,m):
 if not v:raise ValueError(m)
def obj_file(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'},'exact Ref3')
 p=Path(r['path']);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary actual input')
 key=lambda x:(x.st_dev,x.st_ino,x.st_size,x.st_mtime_ns,x.st_ctime_ns)
 with p.open('rb')as f:
  a=os.fstat(f.fileno());h=hashlib.sha256();n=0
  for b in iter(lambda:f.read(1048576),b''):n+=len(b);h.update(b)
  z=os.fstat(f.fileno())
 need(key(a)==key(z)==key(p.stat())and(n,h.hexdigest())==(r['bytes'],r['sha256']),'exact stable bytes/SHA')
 return p
def obj(r):return json.loads(obj_file(r).read_bytes())
def ref(p):
 p=Path(p);h=hashlib.sha256();n=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):n+=len(b);h.update(b)
 return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def write(p,v):
 with Path(p).open('x',encoding='utf8',newline='\n')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')

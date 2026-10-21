"""Only ordinary Ref3 reads; no import/device/resource authorization."""
import hashlib,json
from pathlib import Path
def need(v,s):
 if not v:raise ValueError(s)
def ref(p):
 p=Path(p);before=p.stat();digest=hashlib.sha256();size=0
 with p.open('rb')as f:
  for block in iter(lambda:f.read(2**20),b''):digest.update(block);size+=len(block)
 after=p.stat()
 need((before.st_size,before.st_mtime_ns,before.st_ino)==(after.st_size,after.st_mtime_ns,after.st_ino)and size==after.st_size,'stable bounded Ref read')
 return dict(path=str(p),bytes=size,sha256=digest.hexdigest())
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'},'exact Ref3')
 p=Path(r['path']);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents))and ref(p)==r,'ordinary exact evidence bytes')
 return p
def obj(r):return json.loads(checked(r).read_bytes())

def write(p,value):
 with Path(p).open('x',encoding='utf8',newline='\n')as f:
  json.dump(value,f,sort_keys=True,allow_nan=False);f.write('\n')
 return ref(p)


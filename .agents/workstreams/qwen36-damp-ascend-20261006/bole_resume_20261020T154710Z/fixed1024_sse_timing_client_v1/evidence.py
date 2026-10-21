"""Small full-byte evidence helpers, no network or device access."""
import hashlib,json,os,re
from pathlib import Path

def need(v,s):
 if not v:raise ValueError(s)
def strict_json(data):
 def pairs(rows):
  d={}
  for k,v in rows:need(k not in d,'duplicate JSON key');d[k]=v
  return d
 return json.loads(data,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in()).throw(ValueError(x)))
def ref(p):
 p=Path(p);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary absolute full file')
 a=p.stat();h=hashlib.sha256();n=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b);n+=len(b)
 z=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns)and n==z.st_size,'stable whole-file read');return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['bytes'])is int and r['bytes']>=0 and type(r['sha256'])is str and re.fullmatch('[0-9a-f]{64}',r['sha256']),'typed complete Ref3');need(ref(r['path'])==r,'full byte/SHA/path identity');return Path(r['path'])
def obj(r):return strict_json(checked(r).read_bytes())
def exclusive_json(p,v):
 p=Path(p);need(p.is_absolute()and p.parent.is_dir()and not any(x.is_symlink()for x in(p,*p.parents)),'new ordinary evidence output')
 data=(json.dumps(v,sort_keys=True,allow_nan=False)+'\n').encode();fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb')as f:f.write(data);f.flush();os.fsync(f.fileno())
 fd=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)
 return ref(p)

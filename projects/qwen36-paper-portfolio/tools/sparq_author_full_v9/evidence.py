"""Bounded immutable evidence primitives. Stdlib only; no execution permission."""
import hashlib,json,os,re,secrets
from pathlib import Path
def require(ok,why):
 if not ok:raise ValueError(why)
def sha(path):
 p=Path(path);require(p.is_absolute() and p.is_file() and not p.is_symlink(),"exact ordinary immutable evidence")
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1024**2),b""):h.update(b)
 return h.hexdigest()
def bound(path,digest):
 p=Path(path);require(p.is_absolute() and ".." not in p.parts and re.fullmatch("[0-9a-f]{64}",digest or "")
  and sha(p)==digest,"actual exact path/SHA Ref")
 return dict(path=str(p),sha256=digest)
def obj(ref):
 bound(ref["path"],ref["sha256"]);p=Path(ref["path"]);require(p.stat().st_size<=2*1024**2,"bounded whole JSON evidence")
 return json.loads(p.read_bytes())
def write(path,value):
 p=Path(path);require(p.is_absolute() and Path("/cache/cch") in p.parents and p.parent.resolve()==p.parent
  and p.parent.is_dir() and not p.exists(),"new exact owned evidence output")
 data=json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()+b"\n"
 require(len(data)<=2*1024**2,"bounded whole immutable JSON")
 temporary=p.with_name("."+p.name+".pending-"+secrets.token_hex(16))
 try:
  with temporary.open("xb") as f:
   require(f.write(data)==len(data),"complete temporary bytes");f.flush();os.fsync(f.fileno())
  os.link(temporary,p,follow_symlinks=False)
  fd=os.open(str(p.parent),os.O_RDONLY|os.O_DIRECTORY)
  try:os.fsync(fd);temporary.unlink();os.fsync(fd)
  finally:os.close(fd)
 except BaseException:
  print(json.dumps(dict(error="atomic-publication-failed",final=str(p),retained_temporary=str(temporary))),flush=True);raise
 return bound(p,sha(p))

"""Explicit source-bound reads and exclusive outputs; no backend import."""
import hashlib,importlib.util,json,time
from pathlib import Path
def need(x,m):
 if not x:raise ValueError(m)
def ref(p):
 p=Path(p);h=hashlib.sha256();n=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);n+=len(b)
 return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def checked(r):
 p=Path(r['path']);need(set(r)=={'path','bytes','sha256'}and p.is_absolute()and not p.is_symlink()and ref(p)==r,'exact actual Ref3');return p
def obj(r):return json.loads(checked(r).read_bytes())
def write(p,v):
 with Path(p).open('x')as f:json.dump(v,f,sort_keys=True,allow_nan=False)
def load(r,name):
 s=importlib.util.spec_from_file_location(name,checked(r));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def source(r):
 m=obj(r);need(m['schema']=='deltalog.deadpayload-native-bridge-source/v024'and m['root']==str(Path(__file__).resolve().parent)and m['default_enabled']is False,'new source/defaultOFF')
 for f in m['files'].values():checked(f)
 checked(m['probe_ref']);checked(m['library_ref']);return m
def window(r):
 a=obj(r);need(r['sha256']=='71211e77fc870a8c94a7f80424925e38e1e092b9374d3a6a1066960ea74fbf99'and a['cutoff_epoch']==1792135097 and 1791962297<=time.time()<1792135097-2880,'fixed authority/whole owner2880 budget')


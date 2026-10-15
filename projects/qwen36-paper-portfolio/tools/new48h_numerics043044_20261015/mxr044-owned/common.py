"""Small exact-source utilities; resource ownership stays original042/069."""
import hashlib,importlib.util,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent
def need(v,m):
 if not v:raise ValueError(m)
def ref(p):
 p=Path(p);h=hashlib.sha256();n=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);n+=len(b)
 return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and Path(r['path']).is_absolute()and not Path(r['path']).is_symlink()and ref(r['path'])==r,'exact ordinary Ref3');return Path(r['path'])
def obj(r):return json.loads(checked(r).read_bytes())
def load(r,name):
 need(name not in sys.modules,'no foreign support module '+name)
 s=importlib.util.spec_from_file_location(name,checked(r));v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v);return v
def write(p,v):
 with Path(p).open('x',encoding='utf8',newline='\n')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')
 return ref(p)
def source(sr):
 m=obj(sr);need(m['schema']=='mxr.block-refinement-owned-source/v044'and m['root']==str(P)and m['default_enabled']is False and m['prepared_only']is False,'new own exact bound source')
 for r in m['files'].values():checked(r)
 return m

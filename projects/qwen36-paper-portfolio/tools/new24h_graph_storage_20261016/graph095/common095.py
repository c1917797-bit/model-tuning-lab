import hashlib,importlib.util,json,sys,time
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
 p=Path(r['path']);need(type(r)is dict and set(r)=={'path','bytes','sha256'}and p.is_absolute()and p.is_file()and not any(q.is_symlink()for q in(p,*p.parents)),'ordinary exact Ref3');a=p.stat();need(ref(p)==r,'exact bytes/SHA');b=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(b.st_dev,b.st_ino,b.st_size,b.st_mtime_ns),'stable source');return p
def obj(r):return json.loads(checked(r).read_bytes())
def load(r,n):
 s=importlib.util.spec_from_file_location(n,checked(r));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def write(p,v):
 with Path(p).open('x',encoding='utf8',newline='\n')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')
def source(sr):
 m=obj(sr);need(m['schema']=='deltalog.graph-owned-source/v095'and m['root']==str(P)and m['default_enabled']is False and m['prepared_only']is False,'exact095 source/defaultOFF/bound actual051');[checked(r)for r in m['files'].values()];return m
def window(m):
 a=obj(m['authority_ref']);need(a['start_epoch']==1792134133 and a['cutoff_epoch']==1792220533 and 1792134133<=time.time()<1792220533,'exact fixed24h authority');return a
def build(m):
 v=obj(m['build_ref']);need(v['schema']=='deltalog-split-scale-actual-build/v051'and v['source_manifest']==m['kernel_source_ref']and v['primary']is None and v['Devices']==[],'actual051 build, not numerical qualification');checked(m['kernel_source_ref']);need([a['library']for a in v['artifacts']]==[m['production_library'],m['debug_library']],'same actual dualDSO');[checked(r)for r in(m['production_library'],m['debug_library'])];return v

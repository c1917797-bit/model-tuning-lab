import hashlib,importlib.util,json,os,time
from pathlib import Path

def need(v,m):
    if not v:raise ValueError(m)

def ref(p):
    p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())

def checked(r):
    need(type(r)is dict and set(r)=={'path','bytes','sha256'},'Ref3')
    p=Path(r['path']);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents))and ref(p)==r,'exact ordinary source')
    return p

def obj(r):return json.loads(checked(r).read_bytes())

def load(r,n):
    s=importlib.util.spec_from_file_location(n,checked(r));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v

def write(p,v):
    with Path(p).open('x',encoding='utf8',newline='\n')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')

def source(sr):
    m=obj(sr);need(m['schema']=='bole.tree-fa-owned-source/v118c'and m['prepared_only']is False,'actual116 bound source')
    need(Path(m['root'])==Path(__file__).resolve().parent,'actual split root')
    for r in m['files'].values():checked(r)
    checked(m['prepared_template'])
    return m

def window(m):
    a=obj(m['authority_ref']);need(a['start_epoch']==1792134133 and a['cutoff_epoch']==1792220533 and 1792134133<=time.time()<1792220533,'new24h authority')

def save(t,p,v,root):
    need(not p.exists(),'freshraw');t.save(v,p)
    total=sum(x.stat().st_size for x in root.rglob('*')if x.is_file())
    need(total<=768*2**20,'768MiB hard raw evidence cap; no truncation')
    return ref(p)

import hashlib,importlib.util,json,os,time
from pathlib import Path

def need(v,m):
    if not v:raise ValueError(m)

def ref(p):
    p=Path(p);a=p.stat();h=hashlib.sha256();n=0
    with p.open('rb')as f:
        for block in iter(lambda:f.read(2**20),b''):h.update(block);n+=len(block)
    z=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns)and n==z.st_size,'stable streamed immutable read')
    return dict(path=str(p),bytes=n,sha256=h.hexdigest())

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
    m=obj(sr);need(m['schema']=='bole.tree-fa-owned-source/vFAfactor'and m['prepared_only']is False,'actual116 bound source')
    need(Path(m['root'])==Path(__file__).resolve().parent,'actual split root')
    for r in m['files'].values():checked(r)
    checked(m['prepared_template'])
    return m

def window(m):
    a=obj(m['authority_ref']);need(a['schema']=='ascend.paper-portfolio.explicit-renewed24h/v1'and a['start_epoch']==1792226600 and a['cutoff_epoch']==1792313000 and 1792226600<=time.time()<1792313000,'new24h authority')

def save(t,p,v,root):
    need(not p.exists(),'freshraw');t.save(v,p)
    total=sum(x.stat().st_size for x in root.rglob('*')if x.is_file())
    need(total<=768*2**20,'768MiB hard raw evidence cap; no truncation')
    return ref(p)

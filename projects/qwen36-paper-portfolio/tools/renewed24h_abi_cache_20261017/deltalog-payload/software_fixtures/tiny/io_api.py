"""Small source-pinned I/O; never supplies an execution/admission capability."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path

def need(value, why):
    if not value: raise ValueError(why)

def ref(path):
    p=Path(path); h=hashlib.sha256(); size=0
    with p.open('rb') as f:
        for raw in iter(lambda:f.read(1048576),b''): h.update(raw); size+=len(raw)
    return dict(path=str(p),bytes=size,sha256=h.hexdigest())

def checked(r):
    need(type(r) is dict and set(r)=={'path','bytes','sha256'},'exact Ref3')
    p=Path(r['path']); need(p.is_absolute() and p.is_file() and not any(q.is_symlink() for q in (p,*p.parents)),'ordinary exact input')
    before=p.stat(); need(ref(p)==r,'whole actual bytes/SHA')
    after=p.stat(); need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'stable input')
    return p

def obj(r): return json.loads(checked(r).read_bytes())

def load(r,name):
    p=checked(r); s=importlib.util.spec_from_file_location(name,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def write(p,v):
    p=Path(p)
    with p.open('x',encoding='utf8',newline='\n') as f:
        json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
    if os.name!='nt':
        fd=os.open(str(p.parent),os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)

def verify_source(sr,here):
    m=obj(sr);need(m['schema']=='deltalog.whole-storage-byteabi-source/v1' and m['root']==str(here) and m['default_enabled'] is False,'exact tiny own source/defaultOFF')
    for r in m['files'].values():checked(r)
    checked(m['authority_ref']);checked(m['cann_helper_ref'])
    return m

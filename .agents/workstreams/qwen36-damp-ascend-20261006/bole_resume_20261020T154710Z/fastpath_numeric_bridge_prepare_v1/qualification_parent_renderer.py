"""Pinned, temporary parent-renderer namespace. Never leaves worker modules replaced."""
import contextlib
import hashlib
import importlib.util
from pathlib import Path
import sys
NAMES=('performance_followup_delta.py','paired_contract.py','paired_receipt_consumer.py',
       'validated_performance_policy.py','followup_binding_delta.py',
       'followup_source_validate.py','paired_prepare.py')

def need(v,s):
    if not v:raise ValueError(s)

def refbytes(path,raw):
    return dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def checked(ref):
    need(type(ref)is dict and set(ref)=={'path','bytes','sha256'}and type(ref['bytes'])is int and
         0<=ref['bytes']<=128*2**20,'complete bounded parent Ref3')
    p=Path(ref['path']);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),
                            'ordinary pinned parent source')
    before=p.stat();raw=p.read_bytes();after=p.stat()
    need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==
         (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)and
         refbytes(p,raw)==ref,'stable complete pinned parent source')
    return raw

def readset(root):
    root=Path(root)
    return {name:refbytes(root/name,(root/name).read_bytes())for name in NAMES}

def once(s,a,b):
    need(s.count(a)==1,'exact once source transformation '+a[:80]);return s.replace(a,b,1)

@contextlib.contextmanager
def modules(refs,root):
    need(type(refs)is dict and set(refs)==set(NAMES),'all and only original parent renderer modules')
    root=Path(root)
    need(all(Path(refs[n]['path'])==root/n for n in NAMES),'exact parent preparation paths')
    # ALL files validated before the FIRST external module byte executes.
    texts={n:checked(refs[n])for n in NAMES}
    old={n[:-3]:sys.modules.get(n[:-3])for n in NAMES};old_path=list(sys.path)
    loaded={}
    try:
        sys.path.insert(0,str(root))
        for name in NAMES:
            key=name[:-3]
            spec=importlib.util.spec_from_file_location(key,refs[name]['path'])
            module=importlib.util.module_from_spec(spec)
            sys.modules[key]=module
            exec(compile(texts[name],refs[name]['path'],'exec'),module.__dict__)
            need(Path(module.__file__)==Path(refs[name]['path']),'loaded actual pinned parent identity')
            loaded[name]=module
        need(set(loaded['paired_prepare.py'].HELPERS)==set(NAMES),'same complete original parent helper closure')
        yield loaded
    finally:
        sys.path[:]=old_path
        for name,module in old.items():
            if module is None:sys.modules.pop(name,None)
            else:sys.modules[name]=module

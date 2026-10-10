"""Exact source loader for the explicit first-decode worker; DEFAULT-OFF entries
do not call this. Reuses the immutable existing bootstrap runtime module loader.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
BASE=Path(__file__).resolve().parent
DONOR_MANIFEST_SHA="39f0cd37b348d0cf91cc48deb940426b6a88e5b9d7ab7153c621baf1b8ade2c9"
DONOR_MAIN_SHA="7bb80c55d376ddb1c6ece97d75387211aa005d8f02a276ba3ee6ebf738a05fde"
KERNEL_SHA="ecdae41fa1a3487beb872b01522bbb586f3546100f9fd22b9dd4159ca9c0ac2a"
INSTALLER_SHA="9e41be3e47291ed6552b338934f6b6d804760949d84d8f9751ddde6290a3dc98"
PRODUCER_SHA="f7e392325cf3f83cd45d12c9269b6b4fa65914ff139b9f4cd60a68c4cef4aac5"
PROVENANCE_SHA="a93894bbbd0d73b72c9bc43664a121106525fa5a27bca0d361aff9a2ba00def7"
def need(v,m):
    if not v:raise ValueError(m)
def checked(r,maximum=8*1024**2):
    need(type(r)is dict and set(r)=={"path","bytes","sha256"} and type(r["bytes"])is int
         and 0<r["bytes"]<=maximum,"exact bounded3Ref")
    p=Path(r["path"]);need(p.is_absolute() and p.resolve()==p and not p.is_symlink() and p.is_file(),
                           "actual ordinary source/input")
    before=p.stat();wire=p.read_bytes();after=p.stat()
    need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==
         (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)
         and len(wire)==r["bytes"] and hashlib.sha256(wire).hexdigest()==r["sha256"],
         "whole stable byte source identity")
    return wire
def obj(r):return json.loads(checked(r))
def ref(path):
    p=Path(path);b=p.read_bytes()
    return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def module(name,r):
    wire=checked(r)
    if name in sys.modules:
        old=sys.modules[name]
        need(Path(old.__file__).resolve()==Path(r["path"]) and ref(old.__file__)==r,
             "no foreign cached namespace")
        return old
    spec=importlib.util.spec_from_file_location(name,r["path"]);m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m
    try:exec(compile(wire,r["path"],"exec"),m.__dict__)
    except BaseException:del sys.modules[name];raise
    return m
def source(expected):
    r=ref(BASE/"SOURCE_MANIFEST.json");need(r["sha256"]==expected,"exact new own source manifest")
    m=obj(r);need(m["schema"]=="kivi.actual-firstdecode-bootstrap-sources/v1"
                 and m["root"]==str(BASE) and m["default_enabled"]is False
                 and m["model_ready"]is False,"new source is not model permission")
    for row in m["files"]+m["dependencies"]:
        wire=checked(row)
        if row["path"].endswith(".py"):compile(wire,row["path"],"exec")
    need(m["donor_manifest"]["sha256"]==DONOR_MANIFEST_SHA
         and m["runtime_roles"]["donor_main"]["sha256"]==DONOR_MAIN_SHA,"immutable mature runtime donor")
    declared={row["path"]:row for row in m["files"]+m["dependencies"]}
    for name,row in m["runtime_roles"].items():
        need(declared.get(row["path"])==row,"runtime role must be in actual mounted source closure: "+name)
    checked(m["donor_manifest"]);return m,r
def own(m,name):return next(row for row in m["files"]if Path(row["path"]).name==name)
def memory_module(m):
    roles=m["runtime_roles"]
    need(roles["memory_stream"]["sha256"]=="79b1dcabe028a1e00dfb8ea6d34c2eca2247ac8235da93b29e9195ecff24617b"
         and roles["memory_evidence"]["sha256"]=="01f741b9863a9a1d81762af9c370724f4206b352c996cc132c0bde436f5063e2",
         "exact deployed pure namespace reader and its only flat dependency")
    evidence=module("evidence",roles["memory_evidence"])
    stream=module("_kivi_firstdecode_memory_stream",roles["memory_stream"])
    need(stream.c is evidence,"actual exact reader dependency, no namespace stub")
    return stream
def load(expected,*,memory_limit):
    m,r=source(expected);roles=m["runtime_roles"]
    need(type(memory_limit)is int and memory_limit in(8*1024**3,64*1024**3),
         "only CPU8 or model64 memory profile")
    memory=memory_module(m)
    before=memory.memory(expected_limit=memory_limit)
    cann=module("_kivi_firstdecode_cann_python",own(m,"cann_python.py"))
    cann_binding=cann.install(m,checked,r)
    donor=module("_kivi_firstdecode_original_bootstrap_entry",roles["donor_main"])
    _,original,adapter,bridge,oldprebind,oldconsumer,oldtests=donor.load_modules(DONOR_MANIFEST_SHA)
    mods=dict(original) # never replace entries/globals in the original donor context
    new={name:module("_kivi_firstdecode_runtime_"+name,roles[name])
         for name in("installer","producer","provenance","kernel","spans","book",
                      "bindings","assignment_capture","assignment_oracle","journal")}
    need(new["installer"].CRITICAL_SHA["kernel"]==KERNEL_SHA
         and roles["installer"]["sha256"]==INSTALLER_SHA
         and roles["producer"]["sha256"]==PRODUCER_SHA
         and roles["provenance"]["sha256"]==PROVENANCE_SHA
         and roles["kernel"]["sha256"]==KERNEL_SHA,"single current compiled algorithm identity")
    modules={name:module("_kivi_firstdecode_own_"+name,own(m,name+".py"))
             for name in("prebind","worker","runtime_owner","ownership","raw_journal","finish_after_native")}
    memory.consume_memory(memory.memory(expected_limit=memory_limit),expected_limit=memory_limit,
                          namespace_pid=before["process"]["pid"])
    modules["cann_python"]=cann
    modules["cann_python_binding"]=cann_binding
    modules["memory"]=memory
    modules["memory_before_runtime_imports"]=before
    return m,r,mods,adapter,new,modules
def publish(path,value):
    import os,time
    p=Path(path);need(p.is_absolute() and p.resolve()==p and p.parent.is_dir() and not p.exists()
                      and not p.is_symlink(),"exclusive actual host/guest output path")
    wire=json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()+b"\n"
    need(0<len(wire)<=8*1024**2,"bounded complete immutable JSON")
    tmp=p.with_name("."+p.name+".pending-"+str(time.time_ns()))
    with tmp.open("xb")as out:
        need(out.write(wire)==len(wire),"whole publication");out.flush();os.fsync(out.fileno())
    os.link(tmp,p)
    fd=os.open(p.parent,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)
    return ref(p)

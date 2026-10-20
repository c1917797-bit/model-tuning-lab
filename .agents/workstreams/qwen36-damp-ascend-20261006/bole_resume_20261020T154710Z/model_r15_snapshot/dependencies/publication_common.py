"""Source/input publication for the algorithm-specific packed3 entry. No runtime import by default."""
import hashlib,importlib.util,json,os,re,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
BASE=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit")
FIELDS=("key_codes","key_scales","key_minima","value_codes","value_scales","value_minima","key_residual","value_residual")
CASES=tuple((b,d) for b in (2,4) for d in ("float16","bfloat16"))
STAGES=("seal128","tail129","fork130","reuse256","reuse257")
def need(v,m):
    if not v:raise ValueError(m)
def digest(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for x in iter(lambda:f.read(65536),b""):h.update(x)
    return h.hexdigest()
def ref(p):
    p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=digest(p))
def checked(v,maximum=8*1024**2):
    need(type(v)is dict and set(v)=={"path","bytes","sha256"} and type(v["bytes"])is int and
         0<=v["bytes"]<=maximum and re.fullmatch("[0-9a-f]{64}",v["sha256"]),"exact bounded3Ref")
    p=Path(v["path"]);need(p.is_absolute() and p.resolve()==p and p.is_file() and not p.is_symlink(),"actual ordinary absolute Ref")
    need(p.stat().st_size==v["bytes"] and digest(p)==v["sha256"],"actual entire size/SHA")
    return p.read_bytes()
def source_check(expected):
    p=ROOT/"SOURCE_MANIFEST.json";need(digest(p)==expected,"reviewed source manifest")
    m=json.loads(p.read_bytes())
    need(m["schema"]=="kivi.packed3.numeric.sources/v1" and m["default_enabled"]is False,"numeric source scope")
    for v in list(m["sources"].values())+m["dependencies"]:checked(v)
    for name,v in m["sources"].items():
        if name.endswith(".py"):compile(checked(v),v["path"],"exec")
    return m
def module(name,v):
    checked(v);spec=importlib.util.spec_from_file_location(name,v["path"])
    obj=importlib.util.module_from_spec(spec);sys.modules[name]=obj;spec.loader.exec_module(obj)
    need(Path(obj.__file__).resolve()==Path(v["path"]) and digest(obj.__file__)==v["sha256"],"loaded source bytes")
    return obj
def publish(p,v):
    p=Path(p);raw=(json.dumps(v,sort_keys=True,allow_nan=False)+"\n").encode()
    return binary(p,[raw],len(raw))
def binary(p,chunks,total):
    p=Path(p);need(p.is_absolute() and p.parent.resolve()==p.parent and p.parent.is_dir() and
                  not p.exists() and not p.is_symlink(),"exclusive no-overwrite publication")
    fd,temp=tempfile.mkstemp(prefix="."+p.name+".pending-",dir=p.parent);h=hashlib.sha256();n=0
    with os.fdopen(fd,"wb") as f:
        for blob in chunks:
            need(type(blob)is bytes and len(blob)>0,"raw bytes, not serializer alias metadata")
            f.write(blob);h.update(blob);n+=len(blob)
        need(n==total,"entire raw byte extent");f.flush();os.fsync(f.fileno())
    os.link(temp,p,follow_symlinks=False)
    d=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(d)
    finally:os.close(d)
    # Keep original pending staging bytes, including failures. No experimental deletion.
    return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def output_dir(p):
    p=Path(p);need(p.is_absolute() and not p.exists() and not p.is_symlink() and p.parent.is_dir() and
      p.parent.resolve()==p.parent and (p.parent==BASE or BASE in p.parents) and
      re.fullmatch("[a-zA-Z0-9_-]+",p.name),"new owned lowbit output directory")
    p.mkdir();return p
def scopes():
    return dict(native_ready=False,model_ready=False,performance_ready=False,run_authority=False,
                released_cuda_parity=False,whole_176=False)
def check_terminal(v,sha):
    need(v["schema"]=="kivi.packed3.numeric.producer/v1" and v["status"]=="PACKED3_EXECUTED" and
      v["source_manifest_sha256"]==sha and v["frames"]==20 and v["output_rows"]==24 and
      len(v["case_results"])==4,"all four actual format cases; no partial terminal promotion")
    need([(x["bits"],x["dtype"]) for x in v["case_results"]]==list(CASES),"whole ordered cases")
    for case in v["case_results"]:
        need([x["stage"] for x in case["frames"]]==list(STAGES) and
          [x["length"] for x in case["frames"]]==[128,129,130,256,257] and
          [x["batch"] for x in case["frames"]]==[1,1,2,1,1],"all actual lifecycle/frame geometry")
    need(all(v[k]is False for k in scopes()),"no borrowed permission")
    return v

def inventory(root,cap):
    files=[];total=0
    def walk(p):
        nonlocal total
        for entry in sorted(os.scandir(p),key=lambda e:e.name):
            need(not entry.is_symlink(),"owned compile cache contains no links")
            if entry.is_dir(follow_symlinks=False):walk(Path(entry.path))
            else:
                need(entry.is_file(follow_symlinks=False),"regular compile cache only")
                v=ref(Path(entry.path));total+=v["bytes"];need(total<=cap,"owned compile cache cap")
                files.append(v)
    walk(Path(root))
    return dict(root=str(root),cap_bytes=cap,total_logical_bytes=total,files=files)
def device_proof(proof_ref,source_sha,prior_ref,canary_ref):
    v=json.loads(checked(proof_ref))
    need(v["schema"]=="kivi.packed3.owned-device-proof/v1" and v["source_manifest_sha256"]==source_sha
      and v["image"]=="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
      and type(v["physical_card"])is int and v["physical_card"]in (4,5,6,7)
      and type(v["logical_device"])is int and v["logical_device"]==0 and re.fullmatch("[0-9a-f]{64}",v["cid"]),"actual singleton owned identity")
    need(v["prior_cpu_result_ref"]==prior_ref and v["canary_result_ref"]==canary_ref,"same run actual prerequisites")
    for key in ("host_resource_ref","mapping_ref","source_gate_ref","clock_ref"):checked(v[key])
    # Byte/identity binding only. The existing owned host consumer checks each Ref's admission semantics.
    return v

def identity():
    def read():
        stat=Path("/proc/self/stat").read_text()
        return (stat.rsplit(")",1)[1].split()[19],Path("/proc/self/cgroup").read_text(),Path("/proc/self/cmdline").read_bytes())
    before=read();after=read();need(before==after,"live PID/start/cgroup/cmdline stable")
    need(before[2] and before[2].endswith(bytes([0])),"actual proc cmdline NUL bytes")
    return dict(pid=os.getpid(),start_ticks=int(before[0]),cgroup=before[1],
                cmdline_sha256=hashlib.sha256(before[2]).hexdigest(),argv=list(sys.argv))

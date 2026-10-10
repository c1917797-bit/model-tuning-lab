"""Exact source/TRAIN/mount preflight. No Docker, Torch, NPU or download."""
import argparse,hashlib,json,os,re,stat,sys
from pathlib import Path,PurePosixPath
HERE=Path(__file__).resolve().parent
TRAIN_HOST=Path("/cache/cch/qwen36-damp-20261006/calibration-inputs/source-v2")
TRAIN_GUEST="/cache/cch/qwen36-damp-20261006/calibration-inputs/source-v1"
TRAIN_INDEX=TRAIN_HOST/"SOURCE_INDEX.json"
BASE=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-calibration-capture-chain-v1-001")
INDEX_SHA="2f4e76f5f90eb6106118d71404a6e0acfbcb81a5f093302bf69dcb0c078388a9"
PLAN_SHA="572e1e328c1af4a56e884036cb3c76959f080d1b27de29cc2184bdbeb688f56f"
def require(v,msg):
    if not v:raise ValueError(msg)
def identity(st):
    return dict(dev=st.st_dev,ino=st.st_ino,mode=st.st_mode,bytes=st.st_size,
        mtime_ns=st.st_mtime_ns,ctime_ns=st.st_ctime_ns)
def ordinary(path,directory=None):
    p=Path(path)
    require(p.is_absolute() and ".." not in p.parts,"exact absolute host path")
    for q in (p,)+tuple(p.parents):
        require(not stat.S_ISLNK(q.lstat().st_mode),"symlink rejected: "+str(q))
    st=p.stat()
    require(stat.S_ISREG(st.st_mode) or stat.S_ISDIR(st.st_mode),"ordinary file/directory required: "+str(p))
    if directory is not None:require(stat.S_ISDIR(st.st_mode) is directory,"unexpected path type: "+str(p))
    return st
def file_ref(path):
    p=Path(path);before=ordinary(p,False);h=hashlib.sha256();count=0
    with p.open("rb") as f:
        require(identity(os.fstat(f.fileno()))==identity(before),"opened file changed: "+str(p))
        for b in iter(lambda:f.read(2**20),b""):h.update(b);count+=len(b)
        require(identity(os.fstat(f.fileno()))==identity(before),"file changed while hashing: "+str(p))
    require(identity(p.stat())==identity(before) and count==before.st_size,"file path changed after hashing: "+str(p))
    return dict(path=str(p),bytes=count,sha256=h.hexdigest())
def training(plan_path=BASE/"training_plan.json",index_path=TRAIN_INDEX,
             host_root=TRAIN_HOST,guest_root=TRAIN_GUEST,expected_plan_sha=PLAN_SHA,expected_index_sha=INDEX_SHA):
    rows=[];errors=[];result=dict(plan_ref=None,index_ref=None,host_root=str(host_root),guest_root=str(guest_root),
        artifact_count=0,total_bytes=0,rows=rows,errors=errors)
    try:
        pr=file_ref(plan_path);ir=file_ref(index_path)
        require(pr["sha256"]==expected_plan_sha and ir["sha256"]==expected_index_sha,"original plan/index whole-byte identity")
        plan=json.loads(Path(plan_path).read_bytes());index=json.loads(Path(index_path).read_bytes())
        require(plan["schema"]=="damp-training-source-plan/v1" and plan["root"]==guest_root and
            index["schema"]=="damp-training-source-index/v1" and index["provenance"]=="publisher-pinned-train-only" and
            index["download_scope"]=="no-final-evaluation","unchanged original TRAIN schemas/scope")
        ordinary(host_root,True)
        require(PurePosixPath(guest_root).is_absolute() and ".."not in PurePosixPath(guest_root).parts,"exact original guest root")
        require(len(plan["artifacts"])==len(index["artifacts"])==9,"all nine TRAIN artifacts, none dropped")
        result.update(plan_ref=pr,index_ref=ir,artifact_count=9)
        seen=set()
        for expected,actual in zip(plan["artifacts"],index["artifacts"]):
            rel=PurePosixPath(expected["repository"].replace("/","--"))/expected["revision"]/expected["path"]
            require(not rel.is_absolute() and ".."not in rel.parts and str(rel)not in seen,"unique exact TRAIN relative path")
            seen.add(str(rel));hp=Path(host_root)/Path(str(rel));gp=str(PurePosixPath(guest_root)/rel)
            row=dict(src=str(hp),dst=gp,expected_bytes=expected["size"],expected_sha256=expected["sha256"],
                repository=expected["repository"],revision=expected["revision"],split=expected["split"])
            try:
                require(all(actual[k]==value for k,value in expected.items()),"index differs from original PLAN")
                require(actual["artifact_path"]==str(hp),"actual index path is not host root-derived")
                require(expected["split"]=="train" and type(expected["size"])is int and expected["size"]>0,"TRAIN only real integer bytes")
                ref=file_ref(hp);row["actual_ref"]=ref
                require(ref["bytes"]==expected["size"] and ref["sha256"]==expected["sha256"],"actual TRAIN bytes/SHA mismatch")
                row["checked"]=True
            except (OSError,ValueError,KeyError,TypeError) as e:
                row.update(checked=False,error=repr(e));errors.append(dict(src=str(hp),dst=gp,error=repr(e)))
            rows.append(row);result["total_bytes"]+=expected["size"]
        require(result["total_bytes"]==index["total_bytes"]==110296287 and result["total_bytes"]<=plan["maximum_total_bytes"],
            "all nine original sizes and bounded total")
    except (OSError,ValueError,KeyError,TypeError) as e:errors.append(dict(src=str(host_root),dst=str(guest_root),error=repr(e)))
    result["passed"]=not errors and len(rows)==9 and all(r["checked"]for r in rows)
    return result
def inspect_mounts(mounts):
    rows=[];errors=[];destinations=set()
    require(type(mounts)is dict and mounts,"actual nonempty mount set")
    for dst,value in sorted(mounts.items()):
        row=dict(src=None,dst=dst,read_write=None)
        try:
            require(type(dst)is str and type(value)in(tuple,list) and len(value)==2,"actual typed mount")
            src,rw=value;row.update(src=src,read_write=rw)
            require(type(src)is str and type(rw)is bool and ","not in src and ","not in dst,"exact comma-free source/destination")
            dp=PurePosixPath(dst)
            require(dp.is_absolute() and ".."not in dp.parts and str(dp)==dst and dst not in destinations,"unique normalized absolute guest destination")
            destinations.add(dst);st=ordinary(src)
            row.update(exists=True,kind="directory"if stat.S_ISDIR(st.st_mode)else"file",identity=identity(st),checked=True)
        except (OSError,ValueError,TypeError) as e:
            row.update(exists=False,checked=False,error=repr(e));errors.append(dict(src=row["src"],dst=dst,error=repr(e)))
        rows.append(row)
    return rows,errors
def observe(mounts,phase,source_ref):
    rows,errors=inspect_mounts(mounts);train=training()
    require(mounts.get(TRAIN_GUEST)==(str(TRAIN_HOST),False),"only explicit actual-root to original-guest-root TRAIN RO mapping")
    errors+=train["errors"]
    return dict(schema="SKVQ_EXACT_MOUNT_TRAIN_PREFLIGHT_V1",phase=phase,current_source_ref=source_ref,
        mounts=rows,training=train,errors=errors,passed=not errors and train["passed"],
        no_container_created_by_preflight=True,no_NPU_access=True,no_download=True)
def consume(value,mounts,phase,source_ref):
    require(type(value)is dict and set(value)=={"schema","phase","current_source_ref","mounts","training","errors","passed",
        "no_container_created_by_preflight","no_NPU_access","no_download"},"complete exact preflight schema")
    current=observe(mounts,phase,source_ref)
    require(value["passed"]is True and current["passed"]is True,"all mounts and nine TRAIN actually passed")
    require({k:v for k,v in value.items()if k!="mounts"}=={k:v for k,v in current.items()if k!="mounts"},
        "exact source/phase/TRAIN/file-byte replay")
    require(len(value["mounts"])==len(current["mounts"]),"complete original mount rows")
    for old,new in zip(value["mounts"],current["mounts"]):
        require({k:v for k,v in old.items()if k!="identity"}=={k:v for k,v in new.items()if k!="identity"},
            "exact src/dst/type/RW/no-extra mount evidence")
        keys=("dev","ino","mode")if old["kind"]=="directory"else tuple(old["identity"])
        require(all(old["identity"][k]==new["identity"][k]for k in keys),"original physical mount identity")
    return value
def main():
    p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true");p.add_argument("--source-manifest-sha256");p.add_argument("--output",type=Path);a=p.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,no_NPU_access=True)));return
    sys.path.insert(0,str(HERE));import current_contract as C
    source=C.configure(a.source_manifest_sha256)
    require(a.output and a.output.is_absolute() and a.output.parent==HERE.parent and
        re.fullmatch("run-skvq-mount-preflight-014-[a-zA-Z0-9-]+",a.output.name) and
        not a.output.exists() and not a.output.is_symlink(),"explicit absent same-lowbit preflight root")
    ordinary(a.output.parent,True);a.output.mkdir()
    from MAIN_HOST import Control
    from io_contract import publish_json
    ctl=Control(a.output);results=[]
    for phase,npu in(("preflight",False),("tp4-capture",True)):
        v=observe(ctl.mounts(npu),phase,source)
        r=publish_json(a.output/(phase+"-MOUNT_PREFLIGHT.json"),v);results.append(r)
        require(v["passed"],"exact preflight refusal retained: "+json.dumps(v["errors"],sort_keys=True))
    print(json.dumps(dict(status="MOUNT_TRAIN_PREFLIGHT_ONLY",results=results,source_ref=source,native_ready=False,model_ready=False)))
if __name__=="__main__":main()

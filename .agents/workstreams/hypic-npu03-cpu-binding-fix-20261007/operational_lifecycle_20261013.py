#!/usr/bin/env python3
"""One authorized operational lifecycle campaign; no quality/performance scoring."""
import argparse, json, signal, time
from datetime import datetime, timezone
from pathlib import Path
import native_lifecycle as native
HERE=Path(__file__).resolve().parent
CONTRACT=HERE/"operational_lifecycle_20261013.json"
MODES=("disabled","uninstalled")
PREFIX="operational-lifecycle-20261013"
def root(mode):
    if mode not in MODES: raise ValueError("lifecycle mode must not enable treatment")
    return native.RAW/(PREFIX+"-"+mode)
def identity():
    frozen=json.loads(CONTRACT.read_text())
    old=json.loads(native.CONTRACT.read_text())
    if native.sha(native.CONTRACT)!=frozen["legacy_contract_sha256"]:
        raise ValueError("legacy contract drift")
    for name,digest in {**old["files"],**frozen["files"]}.items():
        if native.sha(HERE/name)!=digest: raise ValueError("support drift: "+name)
    for name,digest in old["package_assets"].items():
        if native.sha(native.PACKAGE/name)!=digest: raise ValueError("package drift")
    for row in json.loads((native.PACKAGE/"MANIFEST.json").read_text())["source_files"]:
        if native.sha(native.PACKAGE/row["path"])!=row["sha256"]: raise ValueError("source drift")
    return frozen,old
def configure(mode):
    root(mode)
    c,q=native.configure(mode)
    attempt="hotpath-cache10-"+PREFIX+"-"+mode
    q.ATTEMPT_ROOTS[attempt]=root(mode).name
    q.RESERVE_ATTEMPTS|={attempt}
    q.ATTEMPT,q.QROOT,q.EXPERIMENT=attempt,root(mode),PREFIX+"-"+mode
    return c,q
def spec_value(q):
    source,binds,env,command=q.spec(native.ARM)
    return dict(binds=sorted(binds),env=sorted(env),command=["bash","-lc",command],
        devices=source["HostConfig"]["Devices"],image=q.IMAGE,cpuset="112-191")
def hash_value(value):
    import hashlib
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def admit_time(frozen,now=None):
    now=now or datetime.now(timezone.utc)
    deadline=datetime.fromisoformat(frozen["deadline_utc"].replace("Z","+00:00"))
    if (deadline-now).total_seconds()<frozen["phase_alarm_seconds"]+frozen["cleanup_allowance_seconds"]:
        raise ValueError("insufficient remaining bounded lifecycle window")
def main():
    p=argparse.ArgumentParser();p.add_argument("--mode",choices=MODES,required=True)
    p.add_argument("--run",action="store_true");a=p.parse_args()
    frozen,old=identity()
    c,q=configure(a.mode)
    if q.QROOT.exists(): raise ValueError("immutable root exists; inspect same attempt")
    fp=q.preflight()
    sample=next(x for x in c.cases()[0] if x["index"]==59)
    if any(sample[k]!=v for k,v in old["sample"].items()): raise ValueError("input identity")
    if hash_value(spec_value(q))!=frozen["phase_spec_sha256"][a.mode]: raise ValueError("spec drift")
    if not a.run:
        print(json.dumps(dict(mode=a.mode,root=str(q.QROOT),source=native.COMMIT,device_work=False)))
        return 0
    admit_time(frozen)
    if a.mode=="uninstalled":
        from operational_lifecycle_audit_20261013 import evaluate
        evaluate("disabled")
    q.assert_lane_available()
    if q.inspect(q.name_for(native.ARM)) is not None: raise ValueError("owned service exists")
    for s in (signal.SIGTERM,signal.SIGINT,signal.SIGALRM): signal.signal(s,q.interrupt)
    q.QROOT.mkdir()
    q.write_json(q.QROOT/"contract.json",dict(frozen=frozen,mode=a.mode,
        preregistration_sha256=native.sha(CONTRACT),fingerprint=fp,
        git_commit=q.run("git","-C",str(HERE),"rev-parse","HEAD").stdout.strip()))
    cid,guard,error="",None,None
    signal.alarm(frozen["phase_alarm_seconds"])
    try:
        cid=q.create(native.ARM)
        q.write_json(q.QROOT/"container-inspect.json",q.inspect(q.name_for(native.ARM)))
        guard=q.ForeignProcessGuard(native.ARM,{},owned_container_id=cid);guard.start()
        q.start(native.ARM,cid,fp,guard)
        start=json.loads((q.QROOT/native.ARM/"service-start.json").read_text())
        guard.set_expected_workers(start["worker_pid_by_physical_npu"])
        value=native.guarded(q,sample,guard,cid,PREFIX+"-"+a.mode+"-smoke",1)
        q.write_json(q.QROOT/"smoke.json",value)
        guard.assert_clean()
    except Exception as exc: error=type(exc).__name__+": "+str(exc)
    finally:
        signal.alarm(0)
        try:
            if guard: guard.close()
        except Exception as exc: error=(error or "")+"; guard: "+str(exc)
        try:
            if cid:q.cleanup(native.ARM,cid)
        except Exception as exc: error=(error or "")+"; cleanup: "+str(exc)
        q.write_json(q.QROOT/"terminal.json",dict(completed=error is None,error=error,
            mode=a.mode,container_id=cid,quality_or_performance_claim=False))
    print(json.dumps(dict(mode=a.mode,completed=error is None,error=error,root=str(q.QROOT))))
    return int(error is not None)
if __name__=="__main__":raise SystemExit(main())

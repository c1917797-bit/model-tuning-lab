#!/usr/bin/env python3
"""Recovery-only disabled/uninstalled controls after a retained failed canary."""
import argparse, json, signal
from pathlib import Path
import native_lifecycle as native
import native_lifecycle_failure_audit as failed
HERE=Path(__file__).resolve().parent
CONTRACT=HERE/"native_recovery_contract.json"
MODES=("disabled","uninstalled")
def admit(mode, prior):
    if mode not in MODES: raise ValueError("recovery never enables the treatment")
    if prior.get("decision")!="FAILED_SEMANTIC_GUARD" or prior.get("canary_pass") is not False:
        raise ValueError("failed canary must remain failed")
    if not prior.get("exact_owned_release") or not prior.get("source_identity_request_payload_physical_isolation_release_valid"):
        raise ValueError("prior identity/isolation/release is incomplete")
def identity():
    manifest=json.loads(CONTRACT.read_text())
    for name,digest in manifest["files"].items():
        if native.sha(HERE/name)!=digest: raise ValueError("recovery support drift: "+name)
    if native.sha(failed.OUT)!=manifest["enabled_failure_audit_sha256"]:
        raise ValueError("enabled failure receipt drift")
    prior=failed.evaluate()
    if json.loads(failed.OUT.read_text())!=prior: raise ValueError("enabled failure changed")
    return manifest,prior
def environment(q):
    driver=Path("/usr/local/Ascend/driver/version.info")
    return dict(scope="prospective recovery control only; not historical backfill",
      os_arch=q.run("uname","-a").stdout.strip(),npu_before=q.run("npu-smi","info").stdout,
      driver_version_info=driver.read_text() if driver.is_file() else "unavailable",
      driver_version_sha256=native.sha(driver) if driver.is_file() else None,
      tokenizer_and_model_config_sha256={p.name:native.sha(p)
        for pattern in ["*tokenizer*","config.json","generation_config.json","vocab.json","merges.txt"]
        for p in q.MODEL_DIR.glob(pattern) if p.is_file()},
      model_weight_identity="frozen index SHA and shard size/mtime, not all-shard byte hashes",
      firmware="unavailable",clock_power_policy="unavailable",interconnect_topology="unavailable",
      compiler_operator_package="unavailable; pinned image only",cache_storage="/cache",
      current_container_versions="installed.json",build_flags="unchanged pinned image")
def main():
    parser=argparse.ArgumentParser();parser.add_argument("--mode",choices=MODES,required=True)
    parser.add_argument("--run",action="store_true");args=parser.parse_args()
    manifest,prior=identity();admit(args.mode,prior)
    c,q,item,fp,frozen=native.check(args.mode)
    if not args.run:
        print(json.dumps(dict(mode=args.mode,root=str(q.QROOT),recovery_only=True,
            enabled_decision=prior["decision"],source=native.COMMIT)))
        return 0
    if args.mode=="uninstalled":
        from native_recovery_audit import evaluate
        evaluate("disabled")
    q.assert_lane_available()
    if q.inspect(q.name_for(native.ARM)) is not None: raise RuntimeError("owned container exists")
    for signum in [signal.SIGTERM,signal.SIGINT,signal.SIGALRM]:signal.signal(signum,q.interrupt)
    q.QROOT.mkdir()
    q.write_json(q.QROOT/"recovery-admission.json",dict(
        manifest=manifest,manifest_sha256=native.sha(CONTRACT),mode=args.mode,
        original_enabled_decision=prior["decision"],recovery_only=True,
        original_progression_resumed=False,quality_or_performance_claim=False,
        git_commit=q.run("git","-C",str(HERE),"rev-parse","HEAD").stdout.strip()))
    q.write_json(q.QROOT/"environment.json",environment(q))
    q.write_json(q.QROOT/"contract.json",dict(frozen=frozen,mode=args.mode,
      preregistration_sha256=native.sha(native.CONTRACT),fingerprint=fp,
      sample={k:v for k,v in item.items() if k!="prompt"},
      git_commit=q.run("git","-C",str(HERE),"rev-parse","HEAD").stdout.strip()))
    cid,guard,error="",None,None
    signal.alarm(2400)
    try:
        cid=q.create(native.ARM)
        q.write_json(q.QROOT/"container-inspect.json",q.inspect(q.name_for(native.ARM)))
        guard=q.ForeignProcessGuard(native.ARM,{},owned_container_id=cid);guard.start()
        q.start(native.ARM,cid,fp,guard)
        start=json.loads((q.QROOT/native.ARM/"service-start.json").read_text())
        guard.set_expected_workers(start["worker_pid_by_physical_npu"])
        for name,maximum in [("warm1",1),("warm2",1),("target",2048)]:
            identifier=native.body_id(args.mode)+("" if name=="target" else "-"+name)
            value=native.guarded(q,item,guard,cid,identifier,maximum)
            q.write_json(q.QROOT/(name+".json"),value);q.status(native.ARM,"recovery-"+name+"-complete")
        guard.assert_clean()
    except Exception as exc:error=type(exc).__name__+": "+str(exc)
    finally:
        signal.alarm(0)
        try:
            if guard:guard.close()
        except Exception as exc:error=(error or "")+"; guard: "+str(exc)
        try:
            if cid:q.cleanup(native.ARM,cid)
        except Exception as exc:error=(error or "")+"; cleanup: "+str(exc)
        q.write_json(q.QROOT/"terminal.json",dict(completed=error is None,error=error,
            mode=args.mode,container_id=cid,quality_or_performance_claim=False,recovery_only=True))
    print(json.dumps(dict(mode=args.mode,completed=error is None,error=error,root=str(q.QROOT),
        recovery_only=True,enabled_canary_pass=False)))
    return int(error is not None)
if __name__=="__main__":raise SystemExit(main())

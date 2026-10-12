#!/usr/bin/env python3
"""Bounded native HYPIC delivery controls; no full-suite or performance claim."""
import argparse, concurrent.futures, hashlib, json, os, shlex, signal
from pathlib import Path
from r16_original_source_full_adapter import configure as base_configure
from r25retry2_state_diagnostic import request
HERE=Path(__file__).resolve().parent
RAW=Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007")
SOURCE="/cache/cch/hypic_vllm_ascend-hotproof-20261008"
COMMIT="4429e35177979c874bf053ab29789e4773f39b22"
PACKAGE=RAW/"native-delivery-package-20261012"
CONTRACT=HERE/"native_lifecycle_contract.json"
ARM="hypic-only"
MODES=("enabled","disabled","uninstalled")
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def root(mode): return RAW/("native-lifecycle-20261012-"+mode)
def body_id(mode): return "hypic-native-lifecycle-"+mode+"-s059"
def configure(mode):
    if mode not in MODES: raise ValueError("unknown lifecycle mode")
    c=base_configure(ARM);q=c.quality
    os.environ["HYPIC_QUALITY_PLUGIN_REPO"]=SOURCE
    os.environ["HYPIC_QUALITY_PLUGIN_COMMIT"]=COMMIT
    attempt="hotpath-cache10-native-lifecycle-20261012-"+mode
    q.ATTEMPT_ROOTS[attempt]=root(mode).name
    q.RESERVE_ATTEMPTS|={attempt}
    q.ATTEMPT,q.QROOT,q.EXPERIMENT=attempt,root(mode),"hypic-native-lifecycle-20261012-"+mode
    original_spec=q.spec
    def spec(arm):
        source,binds,env,command=original_spec(arm)
        old=SOURCE+":/source-hypic:ro"
        assert binds.count(old)==1 and command.count("exec vllm serve ")==1
        binds=[str(PACKAGE)+":/source-hypic:ro" if x==old else x for x in binds]
        binds.append(str(HERE)+":/lifecycle-control:ro")
        env=[("VLLM_ASCEND_HYPIC_ENABLE="+("1" if mode=="enabled" else "0"))
             if x.startswith("VLLM_ASCEND_HYPIC_ENABLE=") else x for x in env]
        env += ["PYTHONDONTWRITEBYTECODE=1","PIP_NO_INDEX=1"]
        command=command.replace("python3 -m pip install --no-deps -e /opt/hypic;",
             "python3 -m pip install --no-deps --no-build-isolation -e /opt/hypic;")
        probe="python3 -B /lifecycle-control/native_lifecycle_probe.py --expect "
        installed=probe+"installed --output /results/"+q.QROOT.name+"/installed.json; "
        if mode=="uninstalled":
            lifecycle=(installed+"python3 -m pip uninstall -y hypic-vllm-ascend-plugin; "+
              probe+"absent --output /results/"+q.QROOT.name+"/uninstalled.json; exec vllm serve ")
        else:
            lifecycle=installed+"exec bash /opt/hypic/run_with_native_plugin.sh vllm serve "
        command=command.replace("exec vllm serve ",lifecycle)
        return source,binds,env,command
    q.spec=spec
    if mode=="uninstalled":
        def attest(name,arm,cid,fp):
            item=q.inspect(name);q.owned(item,arm,cid)
            probe_path="/results/"+q.QROOT.name+"/absent-at-health.json"
            q.run("docker","exec",name,"python3","-B",
                  "/lifecycle-control/native_lifecycle_probe.py","--expect","absent","--output",probe_path)
            observed=json.loads((q.QROOT/"absent-at-health.json").read_text())
            receipt=dict(schema="hypic-uninstalled-serving-source/v1",container_id=cid,
                image=item["Image"],actual_binds=sorted(item["HostConfig"]["Binds"]),
                actual_command=item["Config"]["Cmd"],selected_source_commit=COMMIT,
                plugin_absent=True,probe=observed)
            q.write_json(q.QROOT/arm/"source-attestation.json",receipt)
            return sha(q.QROOT/arm/"source-attestation.json")
        q.attest_serving_source=attest
    return c,q
def check(mode):
    frozen=json.loads(CONTRACT.read_text())
    for name,digest in frozen["files"].items():
        if sha(HERE/name)!=digest: raise RuntimeError("controller/support drift: "+name)
    for name,digest in frozen["package_assets"].items():
        if sha(PACKAGE/name)!=digest: raise RuntimeError("package drift: "+name)
    c,q=configure(mode)
    if q.QROOT.exists(): raise RuntimeError("immutable root exists; inspect same run, never restart")
    fp=q.preflight()
    items,_=c.cases();item=next(x for x in items if x["index"]==59)
    if any(item[k]!=v for k,v in frozen["sample"].items()): raise RuntimeError("sample drift")
    for row in json.loads((PACKAGE/"MANIFEST.json").read_text())["source_files"]:
        if sha(PACKAGE/row["path"])!=row["sha256"]: raise RuntimeError("plugin byte drift")
    source,binds,env,command=q.spec(ARM)
    import re
    numbered=[x["PathOnHost"] for x in source["HostConfig"]["Devices"] if re.fullmatch(r"/dev/davinci\d+",x["PathOnHost"])]
    assert numbered==["/dev/davinci"+str(i) for i in range(4)]
    return c,q,item,fp,frozen
def guarded(q,item,guard,cid,identifier,maximum):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future=pool.submit(request,q,item,identifier,maximum)
        try:
            while True:
                try:
                    value=future.result(timeout=10);guard.assert_clean();return value
                except concurrent.futures.TimeoutError: guard.assert_clean()
        except BaseException:
            q.stop_owned_for_abort(ARM,cid);raise
def main():
    p=argparse.ArgumentParser();p.add_argument("--mode",choices=MODES,required=True)
    p.add_argument("--run",action="store_true");a=p.parse_args()
    c,q,item,fp,frozen=check(a.mode)
    if not a.run:
        _,binds,env,command=q.spec(ARM)
        print(json.dumps(dict(mode=a.mode,root=str(q.QROOT),command=command,env=env,binds=binds,
                              source=COMMIT,contract_sha256=sha(CONTRACT))))
        return 0
    # Enforce serial progression from independently audited prior phase, not a stale lock.
    if a.mode!="enabled":
        from native_lifecycle_audit import evaluate
        evaluate(MODES[MODES.index(a.mode)-1])
    q.assert_lane_available()
    if q.inspect(q.name_for(ARM)) is not None: raise RuntimeError("owned container exists")
    signal.signal(signal.SIGTERM,q.interrupt);signal.signal(signal.SIGINT,q.interrupt)
    signal.signal(signal.SIGALRM,q.interrupt)
    q.QROOT.mkdir()
    # New lifecycle identity only; never backfill these values into historical r19.
    driver=Path('/usr/local/Ascend/driver/version.info')
    tokenizers={p.name:sha(p) for pattern in ['*tokenizer*','config.json','generation_config.json','vocab.json','merges.txt']
                for p in q.MODEL_DIR.glob(pattern) if p.is_file()}
    q.write_json(q.QROOT/'environment.json',dict(
      scope='prospective lifecycle only',os_arch=q.run('uname','-a').stdout.strip(),
      npu_before=q.run('npu-smi','info').stdout,
      driver_version_info=driver.read_text() if driver.is_file() else 'unavailable',
      driver_version_sha256=sha(driver) if driver.is_file() else None,
      tokenizer_and_model_config_sha256=tokenizers,
      model_weight_identity='frozen index SHA and shard size/mtime, not all-shard byte hashes',
      firmware='unavailable',clock_power_policy='unavailable',interconnect_topology='unavailable',
      compiler_operator_package='unavailable; pinned image only',
      cann_image_reference='HYPIC_NATIVE_CPU_LIFECYCLE_20261012.md',
      current_container_versions='installed.json',cache_storage='/cache',
      build_flags='unchanged pinned official image; no rebuild'))
    q.write_json(q.QROOT/"contract.json",dict(frozen=frozen,mode=a.mode,
      preregistration_sha256=sha(CONTRACT),fingerprint=fp,
      sample={k:v for k,v in item.items() if k!="prompt"},
      git_commit=q.run("git","-C",str(HERE),"rev-parse","HEAD").stdout.strip()))
    cid,guard,error="",None,None
    signal.alarm(2400)
    try:
        cid=q.create(ARM);q.write_json(q.QROOT/"container-inspect.json",q.inspect(q.name_for(ARM)))
        guard=q.ForeignProcessGuard(ARM,{},owned_container_id=cid);guard.start()
        q.start(ARM,cid,fp,guard)
        start=json.loads((q.QROOT/ARM/"service-start.json").read_text())
        guard.set_expected_workers(start["worker_pid_by_physical_npu"])
        for name,maximum in [("warm1",1),("warm2",1),("target",2048)]:
            identifier=body_id(a.mode)+("" if name=="target" else "-"+name)
            value=guarded(q,item,guard,cid,identifier,maximum)
            q.write_json(q.QROOT/(name+".json"),value);q.status(ARM,"lifecycle-"+name+"-complete")
        guard.assert_clean()
    except Exception as exc: error=type(exc).__name__+": "+str(exc)
    finally:
        signal.alarm(0)
        try:
            if guard: guard.close()
        except Exception as exc: error=(error or "")+"; guard: "+str(exc)
        try:
            if cid: q.cleanup(ARM,cid)
        except Exception as exc: error=(error or "")+"; cleanup: "+str(exc)
        q.write_json(q.QROOT/"terminal.json",dict(completed=error is None,error=error,
            mode=a.mode,container_id=cid,quality_or_performance_claim=False))
    print(json.dumps(dict(mode=a.mode,completed=error is None,error=error,root=str(q.QROOT))))
    return int(error is not None)
if __name__=="__main__": raise SystemExit(main())

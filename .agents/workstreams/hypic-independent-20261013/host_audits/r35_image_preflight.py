"""Pinned-image CPU package/import/writer preflight; no model or NPU device."""
import argparse,ast,hashlib,importlib.metadata,importlib.util,inspect,json,os,sys,tempfile,threading
from pathlib import Path
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
def run(on_name,off_name):
    from graph_candidate import worker_loader,activation
    from graph_candidate.prefill_bridge import verify_support
    from graph_candidate.source_contract import verify_raw_function
    import evidence_io_r35.patch as delivery
    versions={n:importlib.metadata.version(n)for n in("vllm","vllm-ascend","torch","torch-npu")}
    assert versions["vllm"]=="0.23.0+empty"and versions["vllm-ascend"]=="0.23.0"
    assert versions["torch-npu"]=="2.10.0.post4"
    # Editable distributions may keep code outside site-packages; resolve the
    # actual top-level import without executing the native worker or model.
    spec=importlib.util.find_spec("vllm_ascend")
    assert spec is not None and spec.origin and spec.submodule_search_locations
    worker=Path(spec.origin).resolve().parent/"worker/model_runner_v1.py"
    assert hashlib.sha256(worker.read_bytes()).hexdigest()==worker_loader.WORKER_SHA256
    old_factory=activation.activate_graph_candidate
    modes=[]
    with tempfile.TemporaryDirectory(prefix="r35-image-")as tmp:
        raw=Path(tmp)/"raw";raw.mkdir()
        for name,flag in((off_name,"0"),(on_name,"1")):
            os.environ.update(INDEPENDENT_GRAPH_HYPIC="1",INDEPENDENT_GRAPH_MANIFEST=str(W/name),
                INDEPENDENT_GRAPH_RAW=str(raw),INDEPENDENT_EVIDENCE_IO_BUDGET=flag,INDEPENDENT_PREFIX_TERMINAL_ONLY="0")
            _,manifest,_=worker_loader._manifest(W/name)
            assert worker_loader._io_budget_enabled(manifest)is(flag=="1")
            stop=delivery.enable()
            assert worker_loader._finder in sys.meta_path
            stop()
            assert worker_loader._finder is None and worker_loader._scheduler_stop is None
            assert activation.activate_graph_candidate is old_factory
            modes.append({"flag":flag,"actual_own_loader_enable_stop":True,
                "native_worker_import_executed":False,"model_loaded":False})
        import independent_evidence_io_budget as module
        source=verify_support(module,manifest["source_sha256"]["independent_evidence_io_budget.py"])
        for name in("selected_step","interval_union_ns","make_budget"):
            verify_raw_function(module,source,getattr(module,name),name=name)
        for name,value in vars(module.EvidenceIOBudget).items():
            if inspect.isfunction(value):
                verify_raw_function(module,source,value,name=name,qualname="EvidenceIOBudget."+name)
        # Use the actual source emitter body with its original write/fsync/counters.
        tree=ast.parse(Path(worker_loader.__file__).read_bytes())
        writer=[n for n in ast.walk(tree)if isinstance(n,ast.FunctionDef)and n.name=="raw_emit"]
        assert len(writer)==1
        bind=ast.parse("""def bind(fd):
    policy=None
    manifest_hash="image-writer-fixture"
    limits={"max_events":100,"max_bytes":100000}
    count=size=0
    lock=threading.Lock()
    fsync=os.fsync
    def set_sync(value):
        nonlocal fsync
        fsync=value
    return None
""")
        fn=bind.body[0];fn.body.insert(-1,writer[0])
        fn.body[-1]=ast.parse("return raw_emit,lambda:(count,size),set_sync").body[0]
        ast.fix_missing_locations(bind);scope={"json":json,"os":os,"threading":threading}
        exec(compile(bind,"<actual-image-source-writer>","exec"),scope)
        p=Path(tmp)/"writer.jsonl";fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        try:
            original,counts,set_sync=scope["bind"](fd)
            budget=module.EvidenceIOBudget(fd,os.fsync,counts,resolve=lambda e:((0,1),("fixture",)))
            set_sync(budget.fsync);emit=budget.wrap(original)
            emit({"event":"layer","rank":0,"step":1})
            emit({"event":"compact_model_rows_completed","rank":0,"step":1})
        finally:os.close(fd)
        rows=[json.loads(x)for x in p.read_text().splitlines()]
        assert [x["event"]for x in rows]==["layer","compact_model_rows_completed","r35_evidence_io_budget_step"]
        assert rows[-1]["original_emit_calls"]==rows[-1]["original_fsync_calls"]==2
    return {"schema":"hypic-r35-pinned-image-preflight/v1","actual_image_python":sys.version.split()[0],
        "versions":versions,"actual_installed_native_worker_source_sha256":hashlib.sha256(worker.read_bytes()).hexdigest(),
        "manifest_off_on_and_owned_loader_install_restore":modes,"actual_observer_executable_source_guards":True,
        "actual_image_original_writer_and_fsync_control":True,"fourworker_activation_proven":False,
        "native_worker_registration_proven":False,"new_npu_work":False,"speed_or_quality_accepted":False,
        "scope":"Actual pinned-image package/module/importer installation and writer controls only; no NPU devices exposed, no native worker/model execution."}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--on",required=True);p.add_argument("--off",required=True)
    a=p.parse_args();print(json.dumps(run(a.on,a.off),sort_keys=True))

"""Actual pinned official-image CPU delivery and original-function controls; no NPU."""
import argparse,hashlib,importlib,importlib.metadata,importlib.util,inspect,json,os,sys,tempfile
from pathlib import Path
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
def run(on_name,off_name):
    import torch
    from graph_candidate import worker_loader as loader,activation
    from graph_candidate.prefill_bridge import verify_support
    from graph_candidate.source_contract import verify_raw_function
    from component_budget_r38.patch import enable
    import independent_component_cost_budget as module
    versions={n:importlib.metadata.version(n)for n in("vllm","vllm-ascend","torch","torch-npu")}
    if versions["vllm"]!="0.23.0+empty"or versions["vllm-ascend"]!="0.23.0"or versions["torch-npu"]!="2.10.0.post4":
        raise ValueError("pinned actual image distributions required")
    spec=importlib.util.find_spec("vllm_ascend")
    worker=Path(spec.origin).resolve().parent/"worker/model_runner_v1.py"
    if hashlib.sha256(worker.read_bytes()).hexdigest()!=loader.WORKER_SHA256:
        raise ValueError("actual native worker source drift")
    old_factory=activation.activate_graph_candidate;modes=[]
    with tempfile.TemporaryDirectory(prefix="r38-image-")as tmp:
        raw=Path(tmp)/"raw";raw.mkdir()
        for name,flag in((off_name,"0"),(on_name,"1")):
            os.environ.update(INDEPENDENT_GRAPH_HYPIC="1",INDEPENDENT_GRAPH_MANIFEST=str(W/name),
                INDEPENDENT_GRAPH_RAW=str(raw),INDEPENDENT_EVIDENCE_IO_BUDGET="0",
                INDEPENDENT_EVIDENCE_STEP_DURABILITY="1",INDEPENDENT_PREFIX_TERMINAL_ONLY="0",
                INDEPENDENT_COMPONENT_COST_BUDGET=flag)
            _,manifest,config=loader._manifest(W/name)
            assert loader._component_budget_enabled(manifest)is(flag=="1")
            assert not any(k in config for k in("r33_prefix_terminal_diagnostic","r33_prefix_terminal_only"))
            remove=enable()
            assert loader._finder in sys.meta_path
            remove();remove()
            assert loader._finder is None and loader._scheduler_stop is None
            assert activation.activate_graph_candidate is old_factory
            modes.append({"flag":flag,"actual_own_loader_install_restore":True,"native_worker_import_executed":False})
        source=verify_support(module,manifest["source_sha256"]["independent_component_cost_budget.py"])
        verify_raw_function(module,source,module.make_component_budget,name="make_component_budget")
        for name,value in vars(module.ComponentBudget).items():
            if inspect.isfunction(value):
                verify_raw_function(module,source,value,name=name,qualname="ComponentBudget."+name)
        bindings={n[:-3]:h for n,h in manifest["source_sha256"].items()if n.endswith(".py")and "/"not in n}
        owners=[]
        for mod,cls,name,group in module.SPECS:
            obj=importlib.import_module(mod);owner=obj if cls is None else getattr(obj,cls)
            owners.append((owner,name,inspect.getattr_static(owner,name)))
        rows=[];identity=[None]
        budget=module.ComponentBudget(rows.append,lambda e:identity[0])
        restore=budget.install(bindings,W)
        from independent_layer_finite_guard import LayerFiniteGuard
        guard=LayerFiniteGuard();guard.collect(torch.tensor([1.,2.]))
        assert guard.validate()==1 and budget.active is None and not rows
        identity[0]=((0,1),("image-fixture",))
        guard=LayerFiniteGuard();guard.collect(torch.tensor([1.,2.]),torch.tensor([3.]))
        assert guard.validate()==2
        original=[];event={"event":"compact_model_rows_completed","rank":0,"step":1,"request_ids":["image-fixture"]}
        budget.wrap_emit(original.append)(event)
        assert original==[event]and len(rows)==2
        assert rows[0]["groups"]["layer_finite_validate"]["calls"]==1
        assert rows[0]["root_interval_union_ns"]>0
        restore()
        assert all(inspect.getattr_static(o,n)is f for o,n,f in owners)
        # The exact original finite guard still rejects nonfinite tensors.
        bad=LayerFiniteGuard();bad.collect(torch.tensor([float("nan")]))
        try:bad.validate()
        except ValueError as error:assert str(error)=="nonfinite C1 layer before native commit"
        else:raise AssertionError("original finite failure missing")
        assert loader.WORKER not in sys.modules
    return {"schema":"hypic-r38-pinned-image-preflight/v1","versions":versions,
        "actual_native_worker_sha256":hashlib.sha256(worker.read_bytes()).hexdigest(),
        "manifest_off_on_actual_own_loader":modes,
        "four_original_source_verified_component_exports_install_restore":True,
        "actual_original_cpu_finite_function_both_contexts":True,"actual_original_nonfinite_rejection":True,
        "native_worker_import_executed":False,"model_loaded":False,"fourworker_activation_proven":False,
        "new_npu_work":False,"speed_or_quality_accepted":False,
        "scope":"Actual pinned image CPU delivery, exact original function slots and CPU finite checks only. No device/model/latency acceptance."}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--on",required=True);p.add_argument("--off",required=True)
    a=p.parse_args();print(json.dumps(run(a.on,a.off),sort_keys=True))

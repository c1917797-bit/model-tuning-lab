"""R38 loader switch, disabled launch and preserved actual writer controls."""
import ast,os,subprocess,sys
from pathlib import Path
import pytest
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from graph_candidate import worker_loader as loader
def manifest():
    return {"component_cost_budget":{"enabled":True,"profile":"selected-component-cost-v1"},
            "source_sha256":{"independent_component_cost_budget.py":"0"*64}}
def test_default_off():
    assert loader._component_budget_enabled({"source_sha256":{}})is False
def test_explicit_bound_switch(monkeypatch):
    monkeypatch.setenv("INDEPENDENT_COMPONENT_COST_BUDGET","1")
    assert loader._component_budget_enabled(manifest())is True
@pytest.mark.parametrize("value",["","true","2","-1"])
def test_invalid_switch_rejected(monkeypatch,value):
    monkeypatch.setenv("INDEPENDENT_COMPONENT_COST_BUDGET",value)
    with pytest.raises(ValueError):loader._component_budget_enabled(manifest())
def test_enabled_without_manifest_rejected(monkeypatch):
    monkeypatch.setenv("INDEPENDENT_COMPONENT_COST_BUDGET","1")
    with pytest.raises(ValueError):loader._component_budget_enabled({"source_sha256":{}})
def test_bound_on_without_explicit_enable_rejected():
    with pytest.raises(ValueError):loader._component_budget_enabled(manifest())
def test_missing_helper_and_wrong_profile_rejected(monkeypatch):
    monkeypatch.setenv("INDEPENDENT_COMPONENT_COST_BUDGET","1")
    for change in("source","profile"):
        m=manifest()
        if change=="source":m["source_sha256"]={}
        else:m["component_cost_budget"]["profile"]="other"
        with pytest.raises(ValueError):loader._component_budget_enabled(m)
def test_actual_disabled_entrypoint_has_no_inference_imports(monkeypatch):
    monkeypatch.delenv("INDEPENDENT_GRAPH_HYPIC",raising=False)
    monkeypatch.delenv("INDEPENDENT_COMPONENT_COST_BUDGET",raising=False)
    import component_budget_r38.patch as package
    assert callable(package.enable())
def test_actual_disabled_launcher_imports_no_algorithm():
    env={k:v for k,v in os.environ.items()if not k.startswith("INDEPENDENT_")}
    env["PYTHONDONTWRITEBYTECODE"]="1"
    code="import sys;assert not any(k.startswith(('graph_candidate','independent_','component_budget_r38.patch'))for k in sys.modules)"
    r=subprocess.run(["sh",str(W/"component_budget_r38/run_with_patch.sh"),sys.executable,"-B","-c",code],env=env,capture_output=True,text=True)
    assert r.returncode==0,r.stderr
def test_invalid_launcher_flag_never_executes_child():
    env=dict(os.environ,INDEPENDENT_COMPONENT_COST_BUDGET="bad")
    r=subprocess.run(["sh",str(W/"component_budget_r38/run_with_patch.sh"),sys.executable,"-c","print('unexpected-child')"],env=env,capture_output=True,text=True)
    assert r.returncode==64 and not r.stdout
def test_cleanup_does_not_replace_original_error():
    original=ValueError("original")
    class Broken:
        def stop(self):raise OSError("owned cleanup")
    assert loader._close_component(Broken(),original)is None
    with pytest.raises(OSError):loader._close_component(Broken())
def test_original_evidence_writer_ast_is_unchanged():
    rel=".agents/workstreams/hypic-independent-20261013/graph_candidate/worker_loader.py"
    old=subprocess.check_output(["git","show","4056062d515b696ee7a1cec7862a2303cfa1740f:"+rel],cwd=W)
    new=Path(loader.__file__).read_bytes()
    def writer(s):
        nodes=[n for n in ast.walk(ast.parse(s))if isinstance(n,ast.FunctionDef)and n.name=="raw_emit"]
        assert len(nodes)==1
        return ast.dump(nodes[0],include_attributes=False)
    assert writer(old)==writer(new)

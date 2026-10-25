"""Actual retained base launch consumption without Docker/NPU allocation."""
import copy,hashlib,json,sys
from pathlib import Path
import pytest
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits import r36_step_durability_controller as owner
def test_checker_refuses_distinct_validation_and_launch_manifest_slots():
    c=json.loads((W/"STEP_DURABILITY_R36_A1_R1_20261025_CONTRACT.json").read_bytes())
    assert c["cache_diagnostic"]["compact_manifest"]!=c["successor_manifest"]
    with pytest.raises(ValueError,match="manifest slots"):
        owner.check_contract(c,source_root=W,require_new_root=False)

def test_real_base_consumes_new_bootstrap_and_same_checked_manifest(tmp_path,monkeypatch):
    c=json.loads((W/"STEP_DURABILITY_R36_A1_R1_20261025_CONTRACT.json").read_bytes())
    c=copy.deepcopy(c);c["raw_root"]=str(tmp_path/"raw");c["model"]=str(tmp_path/"model")
    model=Path(c["model"]);model.mkdir();(model/"config.json").write_text("{}")
    c["model_config_sha256"]=hashlib.sha256(b"{}").hexdigest()
    c.pop("formal_token_artifact",None)
    c["cache_diagnostic"]["source_sha256"]={}
    c["cache_diagnostic"]["compact_manifest"]=c["successor_manifest"]
    checked={"graph_runtime":c["graph_runtime"],"controller_sha256":owner.sha(owner.__file__),
        "active_manifest_sha256":"fixture"}
    monkeypatch.setattr(owner,"check_contract",lambda *a,**kw:checked)
    empty={"utc":"fixture","raw":"","processes":[],"owners":[],"foreign":[]}
    monkeypatch.setattr(owner.base,"snapshot",lambda cid=None:dict(empty))
    monkeypatch.setattr(owner.base,"port_free",lambda port:None)
    captured=[]
    def command(argv,**kwargs):
        if argv==["git","rev-parse","HEAD"]:return "0"*40
        if argv[:3]==["ss","-H","-ltn"]:return ""
        if argv[:3]==["docker","image","inspect"]:return json.dumps([{"Config":{"Env":["PYTHONPATH=/inherited:"]}}])
        if argv[:2]==["docker","run"]:
            captured.append(list(argv))
            raise RuntimeError("stop before allocation: captured actual base-consumed argv")
        raise AssertionError("unexpected external command in launch-only control: "+str(argv))
    monkeypatch.setattr(owner.base,"command",command)
    with pytest.raises(SystemExit)as stopped:owner.run_contract(c,source_root=W)
    assert stopped.value.code==1
    assert len(captured)==1
    argv=captured[0]
    assert sum(x.startswith("PYTHONPATH=/probe/step_durability_r36:/probe:")for x in argv)==1
    assert argv.count("INDEPENDENT_GRAPH_MANIFEST=/probe/"+c["successor_manifest"])==1
    assert "INDEPENDENT_EVIDENCE_IO_BUDGET=0"in argv and "INDEPENDENT_EVIDENCE_STEP_DURABILITY=0"in argv
    assert "INDEPENDENT_PREFIX_TERMINAL_ONLY=0"in argv

"""Actual HOST contract and retained base-constructor tests; no device allocation."""
import copy,json,sys
from pathlib import Path
import pytest
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits import r37_formal_controller as owner
from host_audits import r37_formal_policy as policy
from host_audits import r37_formal_audit as auditor
from host_audits.r37_launch_capsule import capture_contract
def contract(g):
    return json.loads((W/("FORMAL_STEP_R37_"+g+"_R2_20261025_CONTRACT.json")).read_bytes())
@pytest.mark.parametrize("group",["G1","G3"])
def test_actual_frozen_contract(group):
    c=contract(group);r=owner.check_contract(c,source_root=W)
    assert r["source_bindings"]==454 and r["prerequisite"]["runtime_python_identical_to_R36"]
    assert r["policy"]["algorithm_on"]is(group=="G3")
@pytest.mark.parametrize("key,value",[
 ("max_output_tokens",64),("formal_performance",False),("formal_quality",True),
 ("enable_prefix_caching",True),("tp",2),("physical_npus",[4,5,6,7]),
 ("profile_diagnostic",{"requests":16}),("r37_step_durability",False),
 ("controller_sha256","0"*64),("request_timeout_seconds",900)])
def test_frozen_protocol_mutations(key,value):
    c=contract("G3");c[key]=value
    with pytest.raises((ValueError,KeyError)):owner.check_contract(c,source_root=W)
def test_checked_and_actual_manifest_slots_must_match():
    c=contract("G3");c["cache_diagnostic"]["compact_manifest"]="STEP_DURABILITY_R36_ON_MANIFEST_20261025.json"
    with pytest.raises(ValueError):owner.check_contract(c,source_root=W)
def test_no_historical_timing_prerequisite_substitution():
    c=contract("G3");c["r37_prerequisite"]["report"]="R30_FIRST_PAIR_DECISION_20261025.json"
    with pytest.raises(ValueError):owner.check_contract(c,source_root=W)
def test_no_r33_diagnostic_flags_or_runtime_python_change():
    for g in("G1","G3"):
        c=contract(g);m=policy.read(W,c["successor_manifest"]);cfg=policy.read(W,m["config"])
        assert "r33_prefix_terminal_diagnostic"not in cfg and "r33_prefix_terminal_only"not in cfg
        old=policy.read(W,"STEP_DURABILITY_R36_ON_MANIFEST_20261025.json")
        assert {k:v for k,v in m["source_sha256"].items()if k.endswith(".py")}=={k:v for k,v in old["source_sha256"].items()if k.endswith(".py")}
def test_actual_native_constructor_purity():
    c=contract("G1");r=capture_contract(c);argv=r["argv"]
    assert r["new_device_allocation"]is False and not r["automatic_python_environment"]
    assert not any(":/probe"in x for x in argv)
    assert "--no-enable-prefix-caching"in argv and "--enforce-eager"not in argv
def test_actual_treatment_constructor_and_automatic_environment():
    c=contract("G3");r=capture_contract(c);argv=r["argv"]
    env=auditor.retained.native._environment(argv)
    assert env["INDEPENDENT_EVIDENCE_STEP_DURABILITY"]=="1"
    assert env["INDEPENDENT_EVIDENCE_IO_BUDGET"]=="0" and env["INDEPENDENT_PREFIX_TERMINAL_ONLY"]=="0"
    assert env["INDEPENDENT_GRAPH_MANIFEST"]=="/probe/"+c["successor_manifest"]
    assert env["PYTHONPATH"].startswith("/probe/step_durability_r36:/probe:")
    assert "--profiler-config"not in argv
def test_audit_invalid_terminal_never_becomes_valid(tmp_path,monkeypatch):
    c=contract("G3")
    monkeypatch.setattr(auditor.policy,"check",lambda *a,**kw:{"policy":{"algorithm_on":True}})
    monkeypatch.setattr(auditor.retained,"audit_r18_base",lambda *a,**kw:(_ for _ in ()).throw(ValueError("bad original full40 terminal")))
    monkeypatch.chdir(W)
    with pytest.raises(ValueError,match="bad original full40"):auditor.audit(W/"FORMAL_STEP_R37_G3_R2_20261025_CONTRACT.json")
def test_controller_retains_actual_formal_workload_source():
    # There is no diagnostic workload substitution at this new delivery boundary.
    assert "workload_slot"not in Path(owner.__file__).read_text()
    assert "run_profile_workload"not in Path(owner.__file__).read_text()

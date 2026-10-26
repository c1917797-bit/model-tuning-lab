"""Actual retained builder and source/authority guards; HOST fixtures never allocate."""
import copy,hashlib,json,sys
from pathlib import Path
import pytest
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits import r40_formal_controller as owner
from host_audits.r40_launch_capsule import capture_contract
def native():
    return json.loads((W/"FORMAL_WARM_R40_G1_R1_20261026_CONTRACT.json").read_bytes())
def g3_fixture(tmp):
    c=native();old=json.loads((W/"FORMAL_STEP_R37_G3_R2_20261025_CONTRACT.json").read_bytes())
    for key in("performance_group","transfer_treatment","lazy_snapshot_treatment","r18_partitioned_acceptance",
               "c2_snapshot_acceptance","independent_acceptance","cache_diagnostic","graph_runtime"):
        c[key]=copy.deepcopy(old.get(key))
    common=c.pop("baseline_host_source_sha256")
    c["cache_diagnostic"]["source_sha256"]=common
    c["cache_diagnostic"]["compact_manifest"]="FORMAL_WARM_R40_G3_MANIFEST_20261026.json"
    c["successor_manifest"]="FORMAL_WARM_R40_G3_MANIFEST_20261026.json"
    c["r40_step_durability"]=True;c["r40_minimum_remaining_seconds"]=3600
    c["raw_root"]=str(tmp/"HOST-unallocated-g3-root");c["container_name"]="HOST-fixture-no-allocation"
    # Synthetic prerequisite is a HOST boundary-test fixture ONLY.
    # It is not a real native audit, cannot be published as a launch contract,
    # and the retained Docker boundary is intercepted in capture_contract.
    a={"formal_r40_full40_valid":True,"live_release_verified":True,"r40_launch_identity":{
        "group":"G1","host_sources":c["host_controller_source_sha256"],"study_source_map_sha256":c["study_source_map_sha256"]}}
    p=tmp/"HOST-fixture-not-device-audit.json";p.write_text(json.dumps(a))
    c["r40_previous_audit"]={"group":"G1","path":str(p),"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
    return c
def test_actual_native_source_policy_ready_no_device():
    r=owner.check_contract(native())
    assert r["configuration_valid"]and r["device_run"]is False and r["source_bindings"]==465
    assert r["host_source_bindings"]==32 and r["runtime_python"]==438
    assert r["controller_sha256"]==native()["host_controller_sha256"]
@pytest.mark.parametrize("key,value",[
 ("r40_target_warmup_count",0),("r40_target_warmup_count",True),("max_output_tokens",64),
 ("enable_thinking",True),("formal_performance",False),("formal_quality",True),
 ("enable_prefix_caching",True),("enforce_eager",True),("physical_npus",[4,5,6,7]),("tp",2),
 ("absolute_stop_utc","2026-10-26T07:00:00Z"),("r40_minimum_remaining_seconds",1),
 ("study_source_map_sha256","0"*64),("host_controller_sha256","0"*64),("performance_group","G4"),
 ("request_timeout_seconds",7200),("profile_diagnostic",{}),("cache_free_floor",0)])
def test_policy_rejects_axis_authority_source_or_ruler_drift(key,value):
    c=native();c[key]=value
    with pytest.raises((ValueError,KeyError,TypeError)):owner.check_contract(c)
def test_missing_explicit_timed_diagnostics_flag_reproduces_observed_HOST_rejection():
    c=native();del c["protocol_notes"]["timed_diagnostics"]
    with pytest.raises(ValueError,match="explicit timed mode"):owner.check_contract(c)
def test_descriptor_and_host_closure_tamper_rejected():
    c=native();c["r40_warm_descriptors"][0]["payload_sha256"]="0"*64
    with pytest.raises(ValueError):owner.check_contract(c)
    c=native();del c["host_controller_source_sha256"]["host_audits/r40_launch_capsule.py"]
    with pytest.raises(ValueError):owner.check_contract(c)
def test_G3_cannot_start_without_valid_released_same_source_native_predecessor(tmp_path):
    c=g3_fixture(tmp_path);c["r40_previous_audit"]=None
    with pytest.raises(ValueError,match="native predecessor"):owner.check_contract(c)
def test_actual_native_constructor_intercept_restores_real_owner_and_workload():
    refs=(owner.base.write,owner.base.snapshot,owner.workload_slot.run_formal_workload)
    cap=capture_contract(native());argv=cap["argv"]
    assert cap["new_device_allocation"]is False and cap["physical_admission_proven"]is False
    assert not any(x.startswith("INDEPENDENT_")or":/probe"in x for x in argv)
    assert "VLLM_LOGGING_LEVEL=INFO"in argv and "--profiler-config"not in argv
    assert (owner.base.write,owner.base.snapshot,owner.workload_slot.run_formal_workload)==refs
def test_actual_G3_builder_branch_with_explicit_HOST_fixture_predecessor_no_allocation(tmp_path):
    c=g3_fixture(tmp_path);cap=capture_contract(c);argv=cap["argv"]
    assert cap["new_device_allocation"]is False and cap["physical_admission_proven"]is False
    assert "INDEPENDENT_COMPONENT_COST_BUDGET=0"in argv
    assert "INDEPENDENT_EVIDENCE_STEP_DURABILITY=1"in argv
    assert "INDEPENDENT_EVIDENCE_IO_BUDGET=0"in argv and "INDEPENDENT_PREFIX_TERMINAL_ONLY=0"in argv
    assert len([x for x in argv if x.startswith("PYTHONPATH=/probe/component_budget_r38:/probe:")])==1
    assert "--no-enable-prefix-caching"in argv and "--enable-prefix-caching"not in argv
    assert "VLLM_LOGGING_LEVEL=INFO"in argv and "--profiler-config"not in argv

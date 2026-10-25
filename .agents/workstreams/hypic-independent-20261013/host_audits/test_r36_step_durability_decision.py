"""Preregistered screen thresholds and single-variable source/manifest guards."""
import copy,json,sys
from pathlib import Path
import pytest
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits.r36_step_durability_decision import decision,validate_matched

def actual():
    cs=[json.loads((W/("STEP_DURABILITY_R36_"+a+"_R2_20261025_CONTRACT.json")).read_bytes())for a in("A1","B1","A2")]
    ms=[json.loads((W/c["successor_manifest"]).read_bytes())for c in cs]
    cfg=[json.loads((W/m["config"]).read_bytes())for m in ms]
    return cs,ms,cfg

def test_frozen_screen_and_drift_thresholds():
    assert decision(100,90,100)["state"]=="SUPPORTED_BOUNDED_STEP_DURABILITY_EFFECT"
    assert decision(100,99,100)["state"]=="INSUFFICIENT_NET_GAIN_AT_SCREEN_THRESHOLD"
    assert decision(100,80,120)["state"]=="INCONCLUSIVE_CONTROL_DRIFT"
    result=decision(100,90,100)
    assert result["screen_gain_percent"]==result["drift_limit_percent"]==5
    assert not result["native_speed_gain_proven"]and result["r30_native_comparison_unchanged"]

@pytest.mark.parametrize("value",[0,-1,float("inf"),float("nan"),True])
def test_invalid_or_nonfinite_timing_rejected(value):
    with pytest.raises(ValueError):decision(100,value,100)

def test_actual_r2_contracts_and_one_metadata_switch():
    assert validate_matched(*actual())

@pytest.mark.parametrize("field",["max_output_tokens","host_controller_source_sha256","study_source_map_sha256"])
def test_changed_matching_identity_rejected(field):
    cs,ms,cfg=actual();cs[1][field]="changed"
    with pytest.raises(ValueError):validate_matched(cs,ms,cfg)

def test_changed_manifest_or_algorithm_config_rejected():
    cs,ms,cfg=actual();ms[1]["unrelated"]=True
    with pytest.raises(ValueError):validate_matched(cs,ms,cfg)
    cs,ms,cfg=actual();cfg[1]["r33_prefix_terminal_only"]=True
    with pytest.raises(ValueError):validate_matched(cs,ms,cfg)
    cs,ms,cfg=actual();ms[0]["step_durability"]={"enabled":True}
    with pytest.raises(ValueError):validate_matched(cs,ms,cfg)

def test_launch_slot_or_runtime_source_map_drift_rejected():
    cs,ms,cfg=actual();cs[1]["cache_diagnostic"]["compact_manifest"]="old"
    with pytest.raises(ValueError):validate_matched(cs,ms,cfg)
    cs,ms,cfg=actual();cs[1]["cache_diagnostic"]["source_sha256"]={}
    with pytest.raises(ValueError):validate_matched(cs,ms,cfg)

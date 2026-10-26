"""New predeclared R39 decision arithmetic and explicit warmup tradeoff controls."""
import math,sys
from pathlib import Path
import pytest
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits.r39_warmup_decision import calculate
def test_measured_effect_keeps_extra_warmup_cost_and_no_free_amortization():
    r=calculate(100,90,100,30)
    assert r["state"]=="SUPPORTED_BOUNDED_TARGET_WARMUP_COUNT_EFFECT"
    assert r["measured_unit_gain_percent"]==10 and r["control_drift_percent"]==0
    assert r["single_unit_including_extra_warmup_gain_percent"]==-20
    assert r["arithmetic_extra_cost_over_observed_unit_saving"]==3
def test_drift_vetoes_apparent_treatment_gain():
    r=calculate(90,70,110,30)
    assert r["state"]=="INCONCLUSIVE_CONTROL_DRIFT"
def test_below_fixed_gain_gate_is_not_accepted():
    assert calculate(100,96,100,30)["state"]=="INSUFFICIENT_TARGET_WARMUP_GAIN"
def test_negative_gain_has_no_finite_payback_claim():
    r=calculate(100,110,100,30)
    assert r["state"]=="INSUFFICIENT_TARGET_WARMUP_GAIN"
    assert r["arithmetic_extra_cost_over_observed_unit_saving"]is None
@pytest.mark.parametrize("bad",[0,-1,True,float("nan"),float("inf")])
def test_invalid_actual_duration_rejected(bad):
    with pytest.raises(ValueError):calculate(100,90,100,bad)

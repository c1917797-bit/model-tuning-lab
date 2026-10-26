"""New standalone decision arithmetic controls; actual two-arm raw replay pending."""
import sys
from pathlib import Path
import pytest
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits.r40_pair_decision import calculate
@pytest.mark.parametrize("tpot,ttft,expand",[(90,900,True),(90,1000,True),(100,900,False),(110,900,False),(90,1100,False),(110,1100,False)])
def test_primary_and_tail_both_required(tpot,ttft,expand):
    r=calculate({"weighted_tpot_ms":100,"ttft_p95_ms":1000},{"weighted_tpot_ms":tpot,"ttft_p95_ms":ttft})
    assert r["allow_repetition_matrix"]is expand
    assert r["delta_percent"]["weighted_tpot_ms"]==pytest.approx(tpot-100)
    assert r["first_pair_only"]and not r["full_goal_complete"]
@pytest.mark.parametrize("bad",[0,-1,float("nan"),float("inf"),True,None])
def test_bad_denominator_or_candidate_never_a_gain(bad):
    for arm in(0,1):
        rows=[{"weighted_tpot_ms":100,"ttft_p95_ms":1000},{"weighted_tpot_ms":90,"ttft_p95_ms":900}]
        rows[arm]["weighted_tpot_ms"]=bad
        with pytest.raises(ValueError):calculate(*rows)
def test_unit_and_metric_names_not_interchanged():
    with pytest.raises(ValueError):calculate({"tpot_p95_ms":100,"ttft_p95_ms":1000},{"weighted_tpot_ms":90,"ttft_p95_ms":900})

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

@pytest.mark.parametrize("marker",["absent",False])
def test_release_marker_readonly_schema_normalization_preserves_original_true(marker):
    from host_audits.r40_pair_decision import verify_replay
    original={"live_release_verified":True,"timing":{"weighted_tpot_ms":94.874},"raw_sha256":{"events":"abc"}}
    replay={"timing":{"weighted_tpot_ms":94.874},"raw_sha256":{"events":"abc"}}
    if marker!="absent":replay["live_release_verified"]=marker
    verify_replay(original,replay)
@pytest.mark.parametrize("case",["original_missing","original_false","replay_true","raw_changed"])
def test_release_marker_normalization_does_not_relax_actual_release_or_raw_proof(case):
    from host_audits.r40_pair_decision import verify_replay
    original={"live_release_verified":True,"raw_sha256":{"events":"abc"}}
    replay={"raw_sha256":{"events":"abc"}}
    if case=="original_missing":del original["live_release_verified"]
    elif case=="original_false":original["live_release_verified"]=False
    elif case=="replay_true":replay["live_release_verified"]=True
    else:replay["raw_sha256"]["events"]="changed"
    with pytest.raises(ValueError):verify_replay(original,replay)

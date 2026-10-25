"""R33 HOST decision boundary and actual configuration routing controls."""
import copy,json,sys
from pathlib import Path
import pytest
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits import r33_prefix_terminal_decision as d
@pytest.mark.parametrize("a,b,c,state",[
 (100,90,100,"SUPPORTED_BOUNDED_PREFIX_TERMINAL_EFFECT"),
 (100,98,100,"INSUFFICIENT_NET_GAIN_AT_SCREEN_THRESHOLD"),
 (100,90,120,"INCONCLUSIVE_CONTROL_DRIFT"),
 (100,120,100,"INSUFFICIENT_NET_GAIN_AT_SCREEN_THRESHOLD")])
def test_preregistered_screen_boundaries(a,b,c,state):
    assert d.decision(a,b,c)["state"]==state
@pytest.mark.parametrize("bad",[float("nan"),0])
def test_invalid_observation_rejected(bad):
    with pytest.raises(ValueError):d.decision(100,bad,100)
def test_actual_source_contract_config_one_prefix_switch(monkeypatch):
    # Synthetic timing fixture only; no NPU or saved-audit acceptance claim.
    cs={arm:json.loads((W/("PREFIX_TERMINAL_R33_"+arm+"_20261025_CONTRACT.json")).read_text())
        for arm in("A1","B1","A2")}
    def fixture(arm,path,definition):
        return cs[arm],{"diagnostic_makespan_seconds":90 if arm=="B1"else 100},{"fixture_only":True}
    monkeypatch.setattr(d,"load_arm",fixture)
    monkeypatch.chdir(W)
    result=d.audit_pair({arm:"fixture"for arm in cs})
    assert result["state"]=="SUPPORTED_BOUNDED_PREFIX_TERMINAL_EFFECT"
    cs["B1"]["profile_diagnostic"]["output_tokens"]=65
    with pytest.raises(ValueError,match="identity/protocol"):d.audit_pair({arm:"fixture"for arm in cs})

"""New renewal envelope guards only; old passed test suites are not repeated."""
import copy,json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from host_audits import r43_renewal_policy as p
W=p.W
C=json.loads((W/"PROFILE_R43_G1_R1_20261028_CONTRACT.json").read_bytes())
@pytest.mark.parametrize("key,value",[("absolute_stop_utc","2026-10-30T19:15:24Z"),("max_output_tokens",64),("enable_prefix_caching",True)])
def test_renewal_never_changes_ruler_or_authority(key,value):
 c=copy.deepcopy(C);c[key]=value
 with pytest.raises(ValueError):p.check(c)
def test_renewal_never_accepts_missing_source():
 c=copy.deepcopy(C);c["r43_host_source_sha256"].pop("host_audits/r43_profile_audit.py")
 with pytest.raises(ValueError):p.check(c)
def test_hypic_needs_actual_native_predecessor():
 with pytest.raises((ValueError,TypeError,KeyError)):p.check(dict(C,performance_group="G3"))
@pytest.mark.parametrize("low",["raw","cache"])
def test_separate_persistent_reservations_fail_closed(low):
 def space(path):
  bad=(Path(path)==p.RAW_PARENT)if low=="raw"else str(path)=="/cache"
  return SimpleNamespace(f_bavail=0 if bad else 100*1024**3,f_frsize=1)
 with patch.object(p.os,"statvfs",space),pytest.raises(RuntimeError):p.require_budget(C)
def test_expired_window_is_not_renewed_from_host_clock():
 from independent_execution_deadline import deadline_epoch
 with patch.object(p.time,"time",lambda:deadline_epoch(p.STOP)+1),pytest.raises(TimeoutError):p.require_budget(C)

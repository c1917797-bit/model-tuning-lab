"""New R42 admission controls; unchanged reviewed R41 trace controls are not rerun."""
import copy,json
from pathlib import Path
import pytest
from host_audits import r42_profile_policy as p
def c():return json.loads((p.W/"PROFILE_R42_G1_R1_20261026_CONTRACT.json").read_bytes())
def test_actual_one_flag_new_closure_and_old_failure_preserved():
 a=c();r=p.check(a)
 old=json.loads((p.W/"PROFILE_R41_G1_R1_20261026_CONTRACT.json").read_bytes())
 assert [k for k in a["r42_profiler"]if a["r42_profiler"][k]!=old["r41_profiler"][k]]==["torch_profiler_with_stack"]
 assert a["r42_profiler"]["torch_profiler_with_stack"]is False and r["runtime_python"]==438
 assert a["baseline_host_source_sha256"]==old["baseline_host_source_sha256"]
 for n,h in old["r41_host_source_sha256"].items():assert p.sha(p.W/n)==h
@pytest.mark.parametrize("defect",["closed_flag","storage","failure_proof"])
def test_r42_does_not_admit_old_flag_or_unbound_release(defect):
 a=c()
 if defect=="closed_flag":a["r42_profiler"]["torch_profiler_with_stack"]=True
 if defect=="storage":a["r42_minimum_cache_bytes"]=1
 if defect=="failure_proof":a["r42_failure_prerequisite"]={}
 with pytest.raises(ValueError):p.check(a)

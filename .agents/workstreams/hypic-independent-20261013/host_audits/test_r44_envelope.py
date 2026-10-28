"""Focused R44 change isolation, ownership metadata and restoration controls."""
import copy
from pathlib import Path
from unittest.mock import patch
import pytest
from host_audits import r44_profile_policy as p,r44_scope as scoped,r44_profile_controller as owner
from host_audits import r43_profile_controller as prior_owner,r43_profile_audit as prior_audit
from host_audits.r44_postprocess import validate_metadata
@pytest.fixture
def contract():return p.make_contract("G1")
def snapshot():
 return [(o,n,getattr(o,n))for o,n in[(p.prior,"check"),(p.prior,"require_budget"),(prior_owner,"check_contract"),(prior_owner,"receipt"),(prior_audit,"receipt"),(p.prior.prior,"PROFILE")]]
def unchanged(saved):assert all(getattr(o,n)is v for o,n,v in saved)
def test_exact_delta_and_parent_validation(contract):
 checked=p.check(contract);old=p.reference("G1")
 assert checked["runtime_python"]==438 and checked["source_bindings"]==465 and checked["host_source_bindings"]==32
 assert contract["r42_profiler"]==dict(old["r42_profiler"],max_iterations=2)
 assert {k for k in old if contract[k]!=old[k]}<=p.CHANGED
@pytest.mark.parametrize("key,value",[("max_output_tokens",512),("image","sha256:bad"),("r42_profiler",dict(p.PROFILE,max_iterations=1)),("r42_profiler",dict(p.PROFILE,torch_profiler_with_stack=True))])
def test_unrelated_or_wrong_cap_rejected(contract,key,value):
 contract[key]=value
 with pytest.raises(ValueError):p.check(contract)
def test_reversible_scope_and_parent_check_inside_scope(contract):
 saved=snapshot()
 with pytest.raises(RuntimeError,match="injected"):
  with scoped.scope(contract):
   assert p.prior.prior.PROFILE["max_iterations"]==2
   assert p.check(contract)["r44_profiler"]["max_iterations"]==2
   assert p.prior.prior.PROFILE["max_iterations"]==2
   assert prior_owner.receipt(contract)["r44_wrapper_identity"]==p.receipt(contract)
   raise RuntimeError("injected")
 unchanged(saved);assert not scoped._LOCK.locked()
def test_nested_scope_rejected_and_restored(contract):
 saved=snapshot()
 with scoped.scope(contract):
  with pytest.raises(RuntimeError,match="no nesting"):
   with scoped.scope(contract):pass
 unchanged(saved)
def test_controller_error_restores_all_bindings(contract):
 saved=snapshot()
 with patch.object(owner.policy,"require_budget",lambda c:80000),patch.object(owner.transport,"run_contract",side_effect=RuntimeError("preallocation fault")):
  local=snapshot()
  with pytest.raises(RuntimeError,match="preallocation fault"):owner.run_contract(contract)
  unchanged(local)
 unchanged(saved)
@pytest.mark.parametrize("bad",["missing","count7","wrongsource","notnative","notreleased","notrace"])
def test_predecessor_requires_real_matched_scope(contract,bad):
 report={"r44_diagnostic_transport_valid":True,"r44_host_source_sha256":contract["r44_host_source_sha256"],"r44_profiler":copy.deepcopy(p.PROFILE),"live_release_verified":True,"profiler":{"four_rank_trace_valid":True},"policy":{"group":"G1"}}
 if bad=="missing":report.pop("r44_diagnostic_transport_valid")
 if bad=="count7":report["r44_profiler"]["max_iterations"]=7
 if bad=="wrongsource":report["r44_host_source_sha256"]={}
 if bad=="notnative":report["policy"]["group"]="G3"
 if bad=="notreleased":report["live_release_verified"]=False
 if bad=="notrace":report["profiler"]["four_rank_trace_valid"]=False
 with pytest.raises(ValueError):p.check_previous(report,contract["r44_host_source_sha256"])
def metadata():
 workers={r:60+r for r in range(4)}
 rows={r:(Path("/tmp/rank%d_%d_20261028210924370_ascend_pt/profiler_info_%d.json"%(r,workers[r],r)),{"start_info":{"x":1},"end_info":{"x":1},"config":{"common_config":{"activities":["ProfilerActivity.CPU","ProfilerActivity.NPU"]}}})for r in workers}
 return rows,workers
def test_metadata_full_four():validate_metadata(*metadata())
@pytest.mark.parametrize("bad",["bothmissing","workerpid","end","activities"])
def test_metadata_not_partial_or_stale(bad):
 rows,workers=metadata()
 if bad=="bothmissing":rows.pop(3);workers.pop(3)
 if bad=="workerpid":workers[3]+=1
 if bad=="end":rows[3][1]["end_info"]={}
 if bad=="activities":rows[3][1]["config"]["common_config"]["activities"]=["ProfilerActivity.CPU"]
 with pytest.raises(ValueError):validate_metadata(rows,workers)

@pytest.mark.parametrize("mode,module,method,fault",[("parse","r43_offline_parse_manager","run",SystemExit(1)),("normalize","r43_trace_timestamp_copy","run",ValueError("copy fault")),("audit","r43_normalized_supplemental_audit","audit",RuntimeError("audit fault"))])
def test_postprocess_fault_restores_context(contract,tmp_path,mode,module,method,fault):
 import importlib,json
 from host_audits import r44_postprocess as post
 cp=tmp_path/"contract.json";cp.write_text(json.dumps(contract))
 pp=tmp_path/"plan.json";pp.write_text(json.dumps({"contract":{"path":str(cp)},"r44_wrapper_sha256":p.sha(post.__file__),"r44_source_sha256":contract["r44_host_source_sha256"]}))
 target=importlib.import_module("host_audits."+module);saved=snapshot()
 with patch.object(target,method,side_effect=fault):
  with pytest.raises(type(fault)):post.run(mode,pp,tmp_path/"out.json")
 unchanged(saved);assert not scoped._LOCK.locked()
 assert not(tmp_path/"out.json").exists()
@pytest.mark.parametrize("field",["r44_wrapper_sha256","r44_source_sha256"])
def test_cpu_wrapper_rejects_actual_source_drift(contract,field):
 from host_audits import r44_postprocess as post
 plan={"r44_wrapper_sha256":p.sha(post.__file__),"r44_source_sha256":contract["r44_host_source_sha256"]}
 plan[field]="stale"
 with pytest.raises(ValueError,match="actual R44 CPU wrapper closure"):post.check_wrapper(plan,contract)

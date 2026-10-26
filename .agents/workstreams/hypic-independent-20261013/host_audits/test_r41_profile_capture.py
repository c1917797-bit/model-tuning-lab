"""HOST corruption controls for official four-rank trace evidence and real control ordering."""
import json,math
from pathlib import Path
import pytest
from host_audits import r41_profile_trace as t
from host_audits import r41_profile_controller as c
def fixture(root):
 workers={i:59+i for i in range(4)}
 for rank,pid in workers.items():
  d=root/("rank"+str(rank)+"_"+str(pid)+"_20261026000000000_ascend_pt");(d/"ASCEND_PROFILER_OUTPUT").mkdir(parents=True)
  (d/("profiler_info_"+str(rank)+".json")).write_text(json.dumps({"rank_id":rank,"config":{"common_config":{"activities":["ProfilerActivity.CPU","ProfilerActivity.NPU"]}}}))
  ev=[{"ph":"M","name":"process_name","pid":pid,"args":{"name":"Python"}},
   {"ph":"M","name":"process_name","pid":1000+rank,"args":{"name":"Ascend Hardware"}},
   {"ph":"X","pid":pid,"name":"aten::copy_","ts":1,"dur":5},
   {"ph":"X","pid":1000+rank,"name":"kernel","ts":3,"dur":2}]
  (d/"ASCEND_PROFILER_OUTPUT/trace_view.json").write_text(json.dumps(ev))
 return workers
def test_four_rank_export_and_overlap_union(tmp_path):
 workers=fixture(tmp_path);r=t.audit_tree(tmp_path,workers)
 assert r["four_rank_trace_valid"]and set(r["ranks"])=={"0","1","2","3"}
 assert t.union([(1,5),(2,7),(9,10)])==7
@pytest.mark.parametrize("defect",["missing_rank","wrong_rank","duplicate_rank","wrong_pid","missing_trace","partial_trace","cpu_only","npu_only","nan","negative","bad_event","wrong_activities","symlink"])
def test_corrupt_trace_fail_closed(tmp_path,defect):
 workers=fixture(tmp_path);info=next(tmp_path.rglob("profiler_info_0.json"));q=info.parent/"ASCEND_PROFILER_OUTPUT/trace_view.json"
 if defect=="missing_rank":info.unlink()
 elif defect=="wrong_rank":
  j=json.loads(info.read_text());j["rank_id"]=5;info.write_text(json.dumps(j))
 elif defect=="duplicate_rank":
  z=tmp_path/"other_99_20261026000000000_ascend_pt";z.mkdir();(z/"profiler_info_0.json").write_bytes(info.read_bytes())
 elif defect=="wrong_pid":workers[0]=999
 elif defect=="missing_trace":q.unlink()
 elif defect=="partial_trace":q.write_text("[{")
 elif defect=="symlink":
  data=q.read_bytes();q.unlink();other=tmp_path/"outside.json";other.write_bytes(data);q.symlink_to(other)
 elif defect=="wrong_activities":
  j=json.loads(info.read_text());j["config"]["common_config"]["activities"]=["ProfilerActivity.CPU"];info.write_text(json.dumps(j))
 else:
  ev=json.loads(q.read_text())
  if defect=="cpu_only":ev=[e for e in ev if e.get("pid")==59]
  if defect=="npu_only":ev=[e for e in ev if e.get("pid")!=59]
  if defect=="nan":ev[-1]["dur"]=float("nan")
  if defect=="negative":ev[-1]["dur"]=-1
  if defect=="bad_event":ev.append(1)
  q.write_text(json.dumps(ev))
 with pytest.raises((ValueError,FileNotFoundError)):t.audit_tree(tmp_path,workers)
def test_storage_bound_without_big_fixture(tmp_path,monkeypatch):
 fixture(tmp_path);monkeypatch.setattr(t,"MAX_TOTAL",4)
 with pytest.raises(ValueError,match="storage"):t.inventory(tmp_path)
@pytest.mark.parametrize("fail",[False,True])
def test_profile_start_after_actual_begin_stop_even_unit_error(monkeypatch,fail):
 actions=[];state={"started":None}
 monkeypatch.setattr(c,"control",lambda port,path,guard:actions.append(path)or 200)
 def record(e):actions.append(e["event"])
 def original(*a,**kw):
  kw["record"]({"event":"warmup"});assert "/start_profile"not in actions
  kw["record"]({"event":"r40-begin"})
  assert actions.index("r40-begin")<actions.index("/start_profile")
  if fail:raise RuntimeError("retained real transport failed")
  kw["record"]({"event":"r40-end"});return {"valid":True}
 call=lambda:c.run_profile_unit(original,{},send_warmup=None,send_measured=None,guard=lambda:None,
  record=record,require_material_ready=None,expected_warm_descriptors=[],port=8233,state=state)
 if fail:
  with pytest.raises(RuntimeError,match="transport"):call()
 else:assert call()["r41_diagnostic_only"]
 assert actions.count("/start_profile")==1 and actions.count("/stop_profile")==1
 assert state["started"]is not None
def test_stop_control_error_is_not_success(monkeypatch):
 events=[]
 def control(port,path,guard):
  if path=="/stop_profile":raise TimeoutError("stop_control")
  return 200
 monkeypatch.setattr(c,"control",control)
 def original(*a,**kw):kw["record"]({"event":"r40-begin"});return {}
 with pytest.raises(TimeoutError,match="stop_control"):
  c.run_profile_unit(original,{},send_warmup=None,send_measured=None,guard=lambda:None,
   record=events.append,require_material_ready=None,expected_warm_descriptors=[],port=8233,state={"started":None})
 assert any(e["event"]=="r41-profile-control-failed"for e in events)
 assert not any(e["event"]=="r41-profile-stop"for e in events)

def prospective_contract():
 import copy
 from host_audits import r41_profile_policy as p
 w=Path(c.W);name,digest=p.REFERENCES["G1"];a=json.loads((w/name).read_bytes())
 a.update(raw_root="/cache/cch/hypic-independent-20261013/critical-path-r41-g1-r1-20261026",
  container_name="hypic-critical-path-r41-g1-r1-20261026",
  purpose="R41 bounded official profiler diagnostic; retained formal transport owner does not confer performance acceptance.",
  prospective_state="R41_DIAGNOSTIC_UNMEASURED",
  formal_launch_command="python3 -B -m host_audits.r41_profile_controller --contract PROFILE_R41_G1_R1_20261026_CONTRACT.json --run",
  formal_audit_command="python3 -B -m host_audits.r41_profile_audit --contract PROFILE_R41_G1_R1_20261026_CONTRACT.json --live-release --output /cache/cch/hypic-independent-20261013/r41-g1-r1-independent-audit-20261026.json",
  r41_role="BOUNDED_OFFICIAL_PREFILL_TIMELINE_DIAGNOSTIC_NOT_PERFORMANCE",r41_reference={"path":name,"sha256":digest},
  r41_host_source_sha256={n:p.sha(w/n)for n in p.FILES},r41_profiler=copy.deepcopy(p.PROFILE),
  r41_previous_audit=None,r41_attempt=1,r41_minimum_remaining_seconds=4500)
 a["r41_controller_sha256"]=a["r41_host_source_sha256"]["host_audits/r41_profile_controller.py"]
 return a
def test_actual_source_bound_offline_contract_no_device():
 from host_audits import r41_profile_policy as p
 out=p.check(prospective_contract())
 assert out["configuration_valid"]and not out["device_run"]and out["runtime_python"]==438
@pytest.mark.parametrize("key,value",[("max_output_tokens",64),("r41_profiler",{}),("host_controller_sha256","0"*64),
 ("r41_role","performance"),("formal_launch_command","wrong"),("r41_minimum_remaining_seconds",1)])
def test_frozen_math_owner_profile_budget_drift_rejected(key,value):
 from host_audits import r41_profile_policy as p
 a=prospective_contract();a[key]=value
 with pytest.raises(ValueError):p.check(a)

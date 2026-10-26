"""New R38 bounded workload, raw counter corruption and actual delivery controls."""
import copy,hashlib,json,sys,threading
from pathlib import Path
import pytest
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits import r38_component_controller as owner
from host_audits.r38_component_evidence import audit_components,GROUPS
def fixture():
    workers={r:100+r for r in range(4)};files={}
    for rank,pid in workers.items():
        base={"pid":pid,"manifest_sha256":"m","rank":rank,"step":7,"request_ids":["fixture"]}
        groups={g:{"calls":1,"inclusive_ns":10,"exclusive_observed_ns":10,"max_ns":10,"failures":0}for g in GROUPS}
        groups["c1_packed_prepare"].update(inclusive_ns=20,max_ns=20)
        groups["layer_finite_validate"].update(calls=2,inclusive_ns=20,exclusive_observed_ns=20)
        budget=dict(base,event="r38_component_budget_step",groups=groups,calls=5,root_interval_union_ns=50,
            probe_metadata_ns=3,original_function_arguments_results_exceptions_unchanged=True,
            original_evidence_unfiltered=True,r36_completion_fence_precedes_receipts=True)
        flush=dict(base,event="r38_component_budget_flush",first_receipt_emit_ns=5,
            extra_receipt_records=2,flush_record_own_write_time_unmeasured=True)
        rows=[dict(base,event="c1_layer_precommit_validated"),dict(base,event="c2_layer_precommit_validated"),
              dict(base,event="c1_prefix_terminal_route"),dict(base,event="compact_model_rows_completed"),
              dict(base,event="r36_evidence_step_durable"),budget,flush]
        files["compact-worker-"+str(pid)+".jsonl"]=("".join(json.dumps(x)+"\n"for x in rows)).encode()
    return files,workers
def change(files,fn):
    name=next(iter(files));rows=[json.loads(x)for x in files[name].splitlines()];fn(rows)
    files[name]=("".join(json.dumps(x)+"\n"for x in rows)).encode()
def test_fourrank_max_budget_does_not_sum_four_ranks_or_nested_inclusive():
    files,workers=fixture();r=audit_components(files,workers,"m")
    assert r["per_step_maxrank_root_union_ns"]==50
    assert r["group_conditional_budgets"]["c1_packed_prepare"]["per_step_maxrank_inclusive_ns"]==20
    assert r["group_conditional_budgets"]["c1_packed_prepare"]["per_step_maxrank_exclusive_ns"]==10
    assert r["extra_receipt_records"]==8 and r["second_receipt_write_unmeasured"]
@pytest.mark.parametrize("bad",[
    lambda r:r[5].__setitem__("root_interval_union_ns",51),
    lambda r:r[5].__setitem__("calls",4),
    lambda r:r[5]["groups"]["layer_finite_validate"].__setitem__("calls",1),
    lambda r:r[5]["groups"]["c1_packed_prepare"].__setitem__("failures",1),
    lambda r:r[5]["groups"]["c1_packed_prepare"].__setitem__("max_ns",21),
    lambda r:r[5].__setitem__("original_evidence_unfiltered",False),
    lambda r:r[6].__setitem__("extra_receipt_records",1),
    lambda r:r[6].__setitem__("flush_record_own_write_time_unmeasured",False),
    lambda r:r[6].__setitem__("request_ids",["foreign"]),
    lambda r:r[4].__setitem__("event","wrong-order"),
    lambda r:r[5].__setitem__("pid",999),
    lambda r:r.pop(),
    lambda r:r.append(copy.deepcopy(r[-1])),
    lambda r:[x.__setitem__("step",8)for x in r]])
def test_corrupt_counter_order_identity_and_rank_closure_fail(bad):
    files,workers=fixture();change(files,bad)
    with pytest.raises(ValueError):audit_components(files,workers,"m")
def artifact(tmp_path):
    cases=[{"index":i,"segment_end":24576,"token_ids":[i]*32768}for i in range(40)]
    data=json.dumps({"native_prefix":[1]*8192,"public_segment":[2]*16384,"requests":cases}).encode()
    p=tmp_path/"tokens.json";p.write_bytes(data)
    return {"path":str(p),"sha256":hashlib.sha256(data).hexdigest()}
def run(tmp_path,fail=False):
    spec=artifact(tmp_path);events=[];warm=[];calls=[];ready=[];lock=threading.Lock()
    def send(p):
        i=p["prompt"][0]
        with lock:calls.append(i)
        assert p["max_tokens"]==1024 and p["ignore_eos"]and p["stream"]
        if fail and i==4:raise RuntimeError("single original request failure")
        return {"request_id":"id-"+str(i),"completion_tokens":1024,
                "usage":{"prompt_tokens":32768},"finish_reason":"length"}
    r=owner.run_unit(spec,send_warmup=lambda p:warm.append(p)or{},
        send_measured=send,guard=lambda:None,record=events.append,
        require_material_ready=lambda:ready.append(True))
    return r,events,warm,calls,ready
def test_bounded16_actual_ruler_warm4_and_no_hidden_retry(tmp_path):
    r,events,warm,calls,ready=run(tmp_path)
    assert r["valid"]and r["formal_performance"]is False and r["summary"]is None
    assert len(warm)==4 and ready==[True]and sorted(calls)==list(range(16))
    assert len(r["results"])==16 and r["retries"]==0 and r["output_tokens"]==1024
    assert [e["event"]for e in events[:5]]==["warmup"]*4+["r38-begin"]
    assert events[-1]["event"]=="r38-end"and all(e.get("scored")is False for e in events)
def test_failure_kept_in_full16_without_retry_or_denominator_drop(tmp_path):
    r,events,warm,calls,ready=run(tmp_path,True)
    assert not r["valid"]and len(r["results"])==16 and sorted(calls)==list(range(16))
    assert r["results"][4]["ok"]is False and len([e for e in events if e["event"]=="r38-response"])==16
def test_input_hash_drift_precedes_any_warm_request(tmp_path):
    spec=artifact(tmp_path);spec["sha256"]="0"*64
    def forbidden(*a,**k):raise AssertionError("must not dispatch")
    with pytest.raises(ValueError,match="input drift"):
        owner.run_unit(spec,send_warmup=forbidden,send_measured=forbidden,guard=forbidden,
                       record=forbidden,require_material_ready=forbidden)

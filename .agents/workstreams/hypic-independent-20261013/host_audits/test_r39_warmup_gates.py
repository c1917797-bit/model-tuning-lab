"""New independent warmup receipt corruption and frozen contract controls."""
import copy,json,sys
from pathlib import Path
import pytest
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits.r39_warmup_evidence import audit_target_warmups
from host_audits import r39_warmup_controller as owner
def fixture(count=2):
    descriptors=[{"ordinal":i,"payload_sha256":str(i)*64}for i in range(2)]
    c={"r39_target_warmup_count":count,"r39_warm_descriptors":descriptors}
    journal=[{"event":"warmup"}for _ in range(4)];warm=[]
    for i in range(count):
        row={"ordinal":i,"descriptor":descriptors[i],"metrics":{"request_id":"warm"+str(i),
            "completion_tokens":1024,"usage":{"prompt_tokens":32768},"finish_reason":"length"},"elapsed_seconds":.5}
        journal.extend([{"event":"r39-target-warmup-begin","scored":False,"descriptor":descriptors[i]},
                        dict(row,event="r39-target-warmup",scored=False)]);warm.append(row)
    journal.extend([{"event":"r38-begin"},{"event":"r38-end"}])
    unit={"r39_target_warmup_count":count,"r39_warm_descriptors":descriptors,
          "r39_target_warmups":warm,"r39_target_warmup_seconds":count*.5,
          "results":[{"metrics":{"request_id":"measured"+str(i)}}for i in range(16)]}
    return journal,unit,c
@pytest.mark.parametrize("count",[0,2])
def test_explicit_original_preparations_and_extra_target_latency(count):
    j,u,c=fixture(count);r=audit_target_warmups(j,u,c)
    assert r["actual_target_warmup_count"]==count and r["extra_target_warmup_seconds"]==count*.5
@pytest.mark.parametrize("bad",[
 lambda j,u,c:u.__setitem__("r39_target_warmup_seconds",0),
 lambda j,u,c:j[4].__setitem__("scored",True),
 lambda j,u,c:j[5]["metrics"].__setitem__("completion_tokens",64),
 lambda j,u,c:j[5].__setitem__("descriptor",{}),
 lambda j,u,c:u["results"][0]["metrics"].__setitem__("request_id","warm0"),
 lambda j,u,c:j.append({"event":"r39-target-warmup-failed"}),
 lambda j,u,c:j.reverse()])
def test_incomplete_wrong_order_short_output_or_hidden_measured_overlap_rejected(bad):
    j,u,c=copy.deepcopy(fixture());bad(j,u,c)
    with pytest.raises(ValueError):audit_target_warmups(j,u,c)
def contract():
    return json.loads((W/"TARGET_WARMUP_R39_A1_R1_20261026_CONTRACT.json").read_bytes())
def test_actual_frozen_contract_source_checks_pass_without_allocating():
    c=contract();r=owner.check_contract(c)
    assert r["device_run"]is False and r["arm"]=="A1"and r["target_warmup_count"]==0
@pytest.mark.parametrize("key,value",[("r39_target_warmup_count",2),("tp",2),("formal_performance",True),("max_output_tokens",64)])
def test_wrong_single_variable_or_ruler_rejected(key,value):
    c=contract();c[key]=value
    with pytest.raises(ValueError):owner.check_contract(c)
def test_treatment_cannot_bypass_predecessor_valid_release():
    c=contract();c["r39_arm"]="B1";c["r39_target_warmup_count"]=2
    with pytest.raises(ValueError,match="predecessor"):owner.check_contract(c)
def test_payload_hash_tamper_rejected():
    c=contract();c["r39_warm_descriptors"][0]["payload_sha256"]="0"*64
    with pytest.raises(ValueError,match="descriptors"):owner.check_contract(c)

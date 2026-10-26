"""Adversarial HOST tests exercise the retained full40 client, not an imitation."""
import copy,hashlib,json,sys,threading,time
from pathlib import Path
import pytest
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits import r40_formal_warm_workload as owner
from host_audits.r40_formal_warm_evidence import audit_warmups
from host_audits.r39_target_warmups import warm_descriptors

def artifact(tmp):
    prefix=[10]*8192;public=[20]*16384;cases=[]
    for i in range(40):
        lo=9216+(i%7)*1024
        cases.append({"index":i,"segment_start":lo,"segment_end":lo+16384,
            "token_ids":prefix+[30+i]*(lo-8192)+public+[100+i]*(32768-lo-16384)})
    data=json.dumps({"native_prefix":prefix,"public_segment":public,"requests":cases}).encode()
    p=tmp/"tokens.json";p.write_bytes(data)
    return {"path":str(p),"sha256":hashlib.sha256(data).hexdigest()}
def execute(tmp,mode=None):
    spec=artifact(tmp);desc=warm_descriptors(spec);events=[];calls=[];lock=threading.Lock();active=peak=0
    def send(payload):
        nonlocal active,peak
        with lock:
            calls.append(payload);n=len(calls);active+=1;peak=max(active,peak)
        try:
            if mode=="fail_warm"and n==1:raise RuntimeError("original warm transport failure")
            if mode=="fail_measured"and n==5:raise RuntimeError("original measured failure")
            started=time.monotonic();time.sleep(0.002);ended=time.monotonic()
            rid="id"+str(n)
            if mode=="duplicate_warm"and n==2:rid="id1"
            if mode=="overlap"and n==3:rid="id1"
            return {"request_id":rid,"started":started,"first_content":started,"ended":ended,
                "completion_tokens":1024,"usage":{"prompt_tokens":32768},"finish_reason":"stop"if mode=="bad_warm"and n==1 else"length",
                "ttft_ms":0.,"duration_ms":(ended-started)*1000,"tpot_ms":(ended-started)*1000/1024,
                "tpot_denominator":"completion_tokens","text":"HOST synthetic transport"}
        finally:
            with lock:active-=1
    contract={"formal_token_artifact":spec,"r40_warm_descriptors":desc}
    unit=owner.run_unit(spec,send_warmup=lambda p:{},send_measured=send,guard=lambda:None,
        record=events.append,require_material_ready=lambda:None,expected_warm_descriptors=desc)
    return unit,events,calls,contract,peak
def test_retained_full40_and_actual_warm_exclusion_under_concurrency(tmp_path):
    u,j,c,contract,peak=execute(tmp_path)
    assert u["valid"]and len(c)==42 and len(u["results"])==40 and u["requests"]==40 and u["concurrency"]==16
    assert 1<peak<=16
    names=[e["event"]for e in j]
    assert names.count("warmup")==4 and names.count("r40-target-warmup")==2 and names.count("measured-response")==40
    assert all(p["max_tokens"]==1024 and len(p["prompt"])==32768 for p in c)
    assert c[0]["prompt"][8192]==100 and c[1]["prompt"][8192]==101
    assert min(names.index("measured-response"),len(names))>max(i for i,n in enumerate(names)if n=="r40-target-warmup")
    proof=audit_warmups(j,u,contract)
    assert proof["formal40_transport_lifecycle_valid"]and len(proof["measured_request_ids"])==40
    assert proof["measured_plus_target_warmup_seconds"]>proof["measured_makespan_seconds"]>0
@pytest.mark.parametrize("mode,match",[("fail_warm","original warm"),("duplicate_warm","duplicate"),("bad_warm","actual target32768"),("overlap","overlap")])
def test_transport_failures_and_identity_overlap_cannot_be_accepted(tmp_path,mode,match):
    with pytest.raises((ValueError,RuntimeError),match=match):execute(tmp_path,mode)
def test_measured_failure_retains_full_denominator_error_and_no_success_summary(tmp_path):
    u,j,c,contract,_=execute(tmp_path,"fail_measured")
    assert len(c)==42 and u["valid"]is False and len(u["results"])==40 and u["summary"]is None
    assert sum(r["ok"]is False for r in u["results"])==1
    assert u["r40_measured_makespan_seconds"]is None and u["r40_measured_plus_target_warmup_seconds"]is None
    with pytest.raises(ValueError):audit_warmups(j,u,contract)
def test_descriptor_drift_prevents_all_dispatch(tmp_path):
    spec=artifact(tmp_path);desc=warm_descriptors(spec);desc[0]["payload_sha256"]="0"*64
    def forbidden(*a,**k):raise AssertionError("no dispatch")
    with pytest.raises(ValueError,match="payload"):
        owner.run_unit(spec,send_warmup=forbidden,send_measured=forbidden,guard=forbidden,
            record=forbidden,require_material_ready=forbidden,expected_warm_descriptors=desc)
@pytest.fixture
def accepted(tmp_path):
    u,j,_,c,_=execute(tmp_path)
    return u,j,c
@pytest.mark.parametrize("case",["omit_prep","swap_prep","score_prep","omit_target","score_target","duplicate_target_id",
    "target_geometry","target_time_nan","target_cross_begin","omit_measured","duplicate_measured_index",
    "unscore_measured","measured_cross_end","combined_cost","extra_cost","measured_span","input_hash","descriptor","unit_record","failed_marker"])
def test_independent_raw_corruption_rejected(accepted,case):
    u,j,c=copy.deepcopy(accepted);names=[e["event"]for e in j]
    wi=names.index("r40-target-warmup");bi=names.index("r40-begin");ei=names.index("r40-end")
    mi=names.index("measured-response");pi=names.index("warmup")
    if case=="omit_prep":j.pop(pi)
    elif case=="swap_prep":j[pi]["ordinal"]=1
    elif case=="score_prep":j[pi]["scored"]=True
    elif case=="omit_target":j.pop(wi)
    elif case=="score_target":j[wi]["scored"]=True
    elif case=="duplicate_target_id":
        targets=[e for e in j if e["event"]=="r40-target-warmup"];targets[1]["metrics"]["request_id"]=targets[0]["metrics"]["request_id"]
        u["r40_target_warmups"][1]["metrics"]["request_id"]=targets[0]["metrics"]["request_id"]
    elif case=="target_geometry":j[wi]["metrics"]["usage"]["prompt_tokens"]=8448
    elif case=="target_time_nan":j[wi]["metrics"]["started"]=float("nan")
    elif case=="target_cross_begin":j[wi]["metrics"]["ended"]=j[bi]["started"]+1
    elif case=="omit_measured":j.pop(mi)
    elif case=="duplicate_measured_index":u["results"][1]["index"]=0
    elif case=="unscore_measured":j[mi]["scored"]=False
    elif case=="measured_cross_end":j[ei]["ended"]=0
    elif case=="combined_cost":u["r40_measured_plus_target_warmup_seconds"]=u["r40_measured_makespan_seconds"]
    elif case=="extra_cost":u["r40_target_warmup_seconds"]=0
    elif case=="measured_span":u["r40_measured_makespan_seconds"]=0
    elif case=="input_hash":u["input_sha256"]="0"*64
    elif case=="descriptor":c["r40_warm_descriptors"][0]["payload_sha256"]="0"*64
    elif case=="unit_record":u["r40_target_warmups"][0]["ordinal"]=1
    elif case=="failed_marker":j.insert(bi,{"event":"r40-target-warmup-failed"})
    with pytest.raises(ValueError):audit_warmups(j,u,c)

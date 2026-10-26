"""New explicit target warmup protocol tests; no inference/device launch."""
import copy,hashlib,json,sys,threading
from pathlib import Path
import pytest
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits import r39_target_warmups as owner
def artifact(tmp):
    prefix=[10]*8192;public=[20]*16384;cases=[]
    for i in range(40):
        lo=9216+(i%7)*1024;tail=32768-lo-16384
        cases.append({"index":i,"segment_start":lo,"segment_end":lo+16384,
            "token_ids":prefix+[30+i]*(lo-8192)+public+[100+i]*tail})
    data=json.dumps({"native_prefix":prefix,"public_segment":public,"requests":cases}).encode()
    p=tmp/"tokens.json";p.write_bytes(data)
    return {"path":str(p),"sha256":hashlib.sha256(data).hexdigest()}
def test_mutates_only_first_private_token_and_preserves_exact_target_geometry(tmp_path):
    spec=artifact(tmp_path);a=json.loads(Path(spec["path"]).read_bytes());warm=owner.prepare_warmups(spec)
    for i,w in enumerate(warm):
        original=a["requests"][i];tokens=w["payload"]["prompt"]
        assert [j for j,(x,y)in enumerate(zip(tokens,original["token_ids"]))if x!=y]==[8192]
        assert tokens[:8192]==a["native_prefix"]
        assert tokens[original["segment_start"]:original["segment_end"]]==a["public_segment"]
        assert len(tokens)==32768 and w["payload"]["max_tokens"]==1024
        assert w["replacement_token"]in original["token_ids"][original["segment_end"]:]
        assert w["payload_sha256"]==owner.digest(w["payload"])
def execute(tmp_path,count,fail=False,duplicate=False):
    spec=artifact(tmp_path);descs=owner.warm_descriptors(spec);events=[];calls=[];lock=threading.Lock()
    def send(payload):
        private=payload["prompt"][8192];warm=private>=100
        with lock:calls.append(private);n=len(calls)
        if fail and warm:raise RuntimeError("warm failed")
        return {"request_id":"duplicate"if duplicate else str(n),"completion_tokens":1024,
            "usage":{"prompt_tokens":32768},"finish_reason":"length"}
    r=owner.run_unit(spec,send_warmup=lambda p:{},send_measured=send,guard=lambda:None,
        record=events.append,require_material_ready=lambda:None,target_warmups=count,expected_warm_descriptors=descs)
    return r,events,calls
@pytest.mark.parametrize("count",[0,2])
def test_single_variable_only_extra_two_full_requests_before_measured_start(tmp_path,count):
    r,events,calls=execute(tmp_path,count)
    assert r["valid"]and len(r["results"])==16 and len(calls)==16+count
    assert len(r["r39_target_warmups"])==count
    assert len([e for e in events if e["event"]=="warmup"])==4
    names=[e["event"]for e in events]
    if count:assert max(i for i,n in enumerate(names)if n=="r39-target-warmup")<names.index("r38-begin")
    assert all(e["scored"]is False for e in events)
    assert r["r39_target_warmup_seconds"]>0 if count else r["r39_target_warmup_seconds"]==0
def test_warm_failure_aborts_before_any_measured_request_and_never_retries(tmp_path):
    with pytest.raises(RuntimeError,match="warm failed"):execute(tmp_path,2,fail=True)
def test_duplicate_warm_identity_rejected(tmp_path):
    with pytest.raises(ValueError,match="duplicate actual warm"):execute(tmp_path,2,duplicate=True)
def test_descriptor_tamper_fails_before_dispatch(tmp_path):
    spec=artifact(tmp_path);descs=owner.warm_descriptors(spec);descs[0]["payload_sha256"]="0"*64
    def no(*a,**k):raise AssertionError("dispatch forbidden")
    with pytest.raises(ValueError,match="payload identity"):
        owner.run_unit(spec,send_warmup=no,send_measured=no,guard=no,record=no,require_material_ready=no,
            target_warmups=2,expected_warm_descriptors=descs)
@pytest.mark.parametrize("value",[True,1,3,-1])
def test_invalid_count_rejected(tmp_path,value):
    def no(*a,**k):raise AssertionError("dispatch forbidden")
    with pytest.raises(ValueError,match="count0or2"):
        owner.run_unit({},send_warmup=no,send_measured=no,guard=no,record=no,require_material_ready=no,
            target_warmups=value,expected_warm_descriptors=[])

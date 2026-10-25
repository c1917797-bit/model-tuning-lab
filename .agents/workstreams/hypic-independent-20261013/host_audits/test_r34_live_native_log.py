import json,sys
from pathlib import Path
from types import SimpleNamespace
import pytest
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits.r34_live_native_log import take_owned_log
def setup(raw,foreign=False):
    cid="a"*64;(raw/"service-start.json").write_text(json.dumps({"container_id":cid}))
    meta={"Id":cid,"Image":"sha256:image","Config":{"Labels":{"model-tuning-lab.task":"task"}},
          "State":{"Running":True},"HostConfig":{"Devices":[{"PathOnHost":"/dev/davinci"+str(i)}for i in range(4)]}}
    if foreign:meta["Image"]="foreign"
    calls=[]
    backend=SimpleNamespace(TASK="task",inspect=lambda x:meta,
        command=lambda args,timeout:(calls.append(args)or"actual live log fixture"))
    return backend,calls
def test_old_terminal_artifact_absent_new_live_producer(tmp_path):
    b,calls=setup(tmp_path)
    with pytest.raises(FileNotFoundError):(tmp_path/"service.log").read_bytes()
    data,receipt=take_owned_log(tmp_path,{"image":"sha256:image"},backend=b)
    assert data==b"actual live log fixture"and receipt["bytes"]==len(data)and len(calls)==1
    assert not(tmp_path/"service.log").exists()
def test_foreign_container_refused_before_log_read(tmp_path):
    b,calls=setup(tmp_path,foreign=True)
    with pytest.raises(ValueError):take_owned_log(tmp_path,{"image":"sha256:image"},backend=b)
    assert not calls
def test_snapshot_exclusive_not_overwritten(tmp_path):
    b,calls=setup(tmp_path);take_owned_log(tmp_path,{"image":"sha256:image"},backend=b)
    with pytest.raises(FileExistsError):take_owned_log(tmp_path,{"image":"sha256:image"},backend=b)

def test_actual_control_unit_without_terminal_log(monkeypatch,tmp_path):
    import hashlib
    import independent_formal_warmups as warmups
    import host_audits.r30b_graph_formal_audit as parse_module
    from host_audits import r34_prefix_terminal_trial as owner
    from host_audits.test_r33_prefix_terminal import _fake_warm_files
    data=json.dumps({"requests":[{"index":i,"token_ids":[1]*32768}for i in range(16)]}).encode()
    path=tmp_path/"input.json";path.write_bytes(data);_fake_warm_files(tmp_path)
    assert not(tmp_path/"service.log").exists()
    backend,calls=setup(tmp_path)
    monkeypatch.setattr(owner.base,"inspect",backend.inspect)
    monkeypatch.setattr(owner.base,"command",backend.command)
    monkeypatch.setattr(owner.base,"TASK","task")
    monkeypatch.setattr(warmups,"build_warmups",lambda x:[])
    monkeypatch.setattr(warmups,"execute_warmups",lambda *a,**k:None)
    monkeypatch.setattr(parse_module,"parse_info_graph",lambda x:{"workers":{i:p for i,p in enumerate((11,12,13,14))}})
    records=[];sends=[]
    def send(payload):
        sends.append(payload)
        return {"id":"fixture"+str(len(sends)),"usage":{"prompt_tokens":32768,"completion_tokens":64}}
    unit=owner.run_unit({"path":str(path),"sha256":hashlib.sha256(data).hexdigest()},
        send_warmup=send,send_measured=None,guard=lambda:None,record=records.append,
        require_material_ready=lambda:None,raw=tmp_path,manifest="m",contract={"image":"sha256:image"})
    assert unit["valid"]and len(sends)==64 and len(calls)==1
    assert not(tmp_path/"service.log").exists()and(tmp_path/"r34-warm-native.log").exists()
    names=[x["event"]for x in records]
    assert names.index("r33-warm-proof")<names.index("r33-begin")<names.index("r33-response")

"""R33 actual math/owned-alias/warm-boundary controls; CPU only."""
import contextvars,hashlib,inspect,json,sys,types
from pathlib import Path
from types import SimpleNamespace
import pytest,torch
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from prefix_terminal_r33 import terminal_math,patch
import independent_recurrent_boundary as baseline
import independent_c1_short_prefix as prefix
import independent_c1_short_suffix as suffix
torch.set_num_threads(1)
@pytest.mark.parametrize("dtype",[torch.float64,torch.float32,torch.bfloat16])
@pytest.mark.parametrize("n",[1,8,39,64])
def test_actual_static_math_state(dtype,n):
    torch.manual_seed(n);q=torch.randn(1,n,4,128,dtype=dtype)
    args=(q,torch.randn_like(q),torch.randn(1,n,12,128,dtype=dtype),
          -torch.rand(1,n,12),torch.rand(1,n,12,dtype=dtype),torch.randn(1,12,128,128)*.01)
    before=[x.clone()for x in args];aobs=[];bobs=[]
    _,a=baseline.recurrent_boundary(*args,input_observer=lambda **x:aobs.append(x))
    out,b=terminal_math.terminal_boundary(*args,input_observer=lambda **x:bobs.append(x))
    assert out is None and torch.equal(a,b)
    assert all(torch.equal(x,y)for x,y in zip(before,args))
    assert len(aobs)==len(bobs)==1
    for k in aobs[0]:
        x=aobs[0][k];y=bobs[0][k]
        assert torch.equal(x,y)if isinstance(x,torch.Tensor)else x==y
def bindings():
    modules=[patch,terminal_math,baseline,prefix,suffix]
    return {m.__name__:hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()for m in modules}
@pytest.mark.parametrize("only",[False,True])
def test_owned_install_first_shape_and_rollback(monkeypatch,only):
    ctx=contextvars.ContextVar("r33_test",default=None)
    monkeypatch.setitem(sys.modules,"independent_compact_model_hook",SimpleNamespace(CURRENT_COMPACT_MODEL=ctx))
    token=ctx.set(SimpleNamespace(plans=[SimpleNamespace(rank=0,step=7,request_id="native-request")]))
    orig=prefix.recurrent_boundary;out=[];calls=[]
    stop=patch.install_prefix_terminal(enabled=True,terminal_only=only,emit=out.append,source_bindings=bindings())
    args=(torch.randn(1,8,4,128),torch.randn(1,8,4,128),torch.randn(1,8,12,128),
          -torch.rand(1,8,12),torch.rand(1,8,12),torch.zeros(1,12,128,128))
    try:
        stop.assert_ownership();assert suffix.recurrent_boundary is orig
        first,state=prefix.recurrent_boundary(*args,input_observer=lambda **x:calls.append(x))
        assert(first is None)is only and len(calls)==1
        prefix.recurrent_boundary(*args)
        rows=[e for e in out if e["event"]=="r33_prefix_terminal_observed"]
        assert[e["first_shape_already_validated"]for e in rows]==[False,True]
        assert len([e for e in out if e["event"]=="r33_prefix_terminal_first_shape_verified"])==1
    finally:stop();ctx.reset(token)
    assert prefix.recurrent_boundary is orig and suffix.recurrent_boundary is orig
def test_disabled_is_noop():
    orig=prefix.recurrent_boundary
    patch.install_prefix_terminal()()
    assert prefix.recurrent_boundary is orig
    with pytest.raises(ValueError):patch.install_prefix_terminal(terminal_only=True)
def test_source_drift_fails():
    b=bindings();b[terminal_math.__name__]="0"*64
    with pytest.raises(ValueError):patch.install_prefix_terminal(enabled=True,emit=lambda x:None,source_bindings=b)
def test_actual_ast_only_discards_output():
    import ast
    assert patch._output_only_ast(baseline.recurrent_boundary)==ast.dump(ast.parse(inspect.getsource(terminal_math.terminal_boundary)),include_attributes=False)
def test_cold_observer_cannot_be_timing_evidence():
    from host_audits.r33_prefix_terminal_evidence import audit_observed
    # No installation/shadow cannot be repaired by declaring warm requests.
    with pytest.raises(ValueError):audit_observed([],["api"],{0:1,1:2,2:3,3:4},"m",False,{"shapes":{}})
def test_missing_39_rejected_before_timer(tmp_path):
    from host_audits.r33_prefix_terminal_evidence import pre_timing_proof
    d=tmp_path/"diagnostics";d.mkdir()
    for pid in(1,2,3,4):(d/("compact-worker-"+str(pid)+".jsonl")).write_text('{}\n')
    with pytest.raises(ValueError,match="length8/39"):pre_timing_proof(tmp_path,{0:1,1:2,2:3,3:4},"m")

def _fake_warm_files(raw,only=False,include39=True):
    import hashlib,json
    d=raw/"diagnostics";d.mkdir(parents=True,exist_ok=True);events=[]
    for rank,pid in enumerate((11,12,13,14)):
        rows=[{"event":"r33_prefix_terminal_installed","pid":pid,"terminal_only":only,
            "prefix_only":True,"suffix_unchanged":True,"state_math_changed":False}]
        for n in([8,39]if include39 else[8]):
            shape=[[[1,n,4,128],"torch.bfloat16","npu:"+str(rank)]]
            sig=hashlib.sha256(json.dumps(shape,separators=(",",":")).encode()).hexdigest()
            rows.append({"event":"r33_prefix_terminal_first_shape_verified","rank":rank,"pid":pid,
                "manifest_sha256":"m","passed":True,"full_terminal_state":True,"length":n,
                "device":"npu:"+str(rank),"shapes":shape,"shape_sha256":sig,"terminal_only":only})
        (d/("compact-worker-"+str(pid)+".jsonl")).write_text("".join(json.dumps(x)+"\n"for x in rows))
        events.extend(rows)
    return events
def test_actual_warm_prefix_and_cold_rejection(tmp_path):
    from host_audits.r33_prefix_terminal_evidence import pre_timing_proof,audit_observed
    events=_fake_warm_files(tmp_path);workers={i:p for i,p in enumerate((11,12,13,14))}
    proof=pre_timing_proof(tmp_path,workers,"m")
    for rank,pid in workers.items():
        sig=next(e["shape_sha256"]for e in events if e.get("rank")==rank and e.get("length")==39)
        events.extend([{"event":"compact_gdn_body_composed","request_id":"api-0-fixed"},
          {"event":"r33_prefix_terminal_observed","rank":rank,"pid":pid,"manifest_sha256":"m",
           "phase":"prefix","length":39,"terminal_only":False,"output_matmul_dispatch_sites_skipped":0,
           "shape_sha256":sig,"first_shape_already_validated":True,"request_ids":["api-0-fixed"]}])
    assert audit_observed(events,["api"],workers,"m",False,proof)["timed_wave_observations"]==4
    next(e for e in events if e.get("event")=="r33_prefix_terminal_observed")["first_shape_already_validated"]=False
    with pytest.raises(ValueError,match="not proven"):audit_observed(events,["api"],workers,"m",False,proof)
@pytest.mark.parametrize("warm_ok",[True,False])
def test_fixed48warm_then_proof_then16_and_no_timer_on_missing_shape(monkeypatch,tmp_path,warm_ok):
    from host_audits import r33_prefix_terminal_trial as owner
    import independent_formal_warmups as warmups
    import host_audits.r30b_graph_formal_audit as info
    data=json.dumps({"requests":[{"index":i,"token_ids":[1]*32768}for i in range(16)]}).encode()
    p=tmp_path/"input.json";p.write_bytes(data);_fake_warm_files(tmp_path,include39=warm_ok)
    (tmp_path/"service.log").write_bytes(b"fixture")
    monkeypatch.setattr(warmups,"build_warmups",lambda x:[])
    monkeypatch.setattr(warmups,"execute_warmups",lambda *a,**k:None)
    monkeypatch.setattr(info,"parse_info_graph",lambda x:{"workers":{i:p for i,p in enumerate((11,12,13,14))}})
    records=[];calls=[]
    def send(payload):
        calls.append(payload["max_tokens"])
        return {"id":"api"+str(len(calls)),"usage":{"prompt_tokens":32768,"completion_tokens":64}}
    args=dict(send_warmup=send,send_measured=None,guard=lambda:None,record=records.append,
        require_material_ready=lambda:None,raw=tmp_path,manifest="m")
    artifact={"path":str(p),"sha256":hashlib.sha256(data).hexdigest()}
    if warm_ok:
        r=owner.run_unit(artifact,**args)
        names=[x["event"]for x in records]
        assert len(calls)==64 and len(r["private_warmup_results"])==48
        assert names.index("r33-warm-proof")<names.index("r33-begin")<names.index("r33-response")
    else:
        with pytest.raises(ValueError,match="length8/39"):owner.run_unit(artifact,**args)
        assert len(calls)==48 and not any(x["event"]=="r33-begin"for x in records)

def test_bridge_passes_nested_package_bindings_to_actual_installer(monkeypatch):
    from graph_candidate import activation,worker_loader,source_contract
    modules=[patch,terminal_math,baseline,prefix,suffix,activation]
    full={m.__name__:hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()for m in modules}
    manifest={"source_sha256":{n.replace(".","/")+".py":h for n,h in full.items()}}
    cfg={"r33_prefix_terminal_diagnostic":True,"r33_prefix_terminal_only":False}
    monkeypatch.setenv("INDEPENDENT_PREFIX_TERMINAL_ONLY","0")
    monkeypatch.setattr(worker_loader,"_manifest",lambda p:(p,manifest,cfg))
    old_verify=source_contract.verify_raw_function
    def fixture_verify(module,src,fn,**kw):
        if module is activation:return
        return old_verify(module,src,fn,**kw)
    monkeypatch.setattr(source_contract,"verify_raw_function",fixture_verify)
    delegated=[]
    def fixture_base(config,**kwargs):
        assert not any(k.startswith("r33_")for k in config)
        delegated.append(kwargs["source_bindings"]);return lambda:None
    monkeypatch.setattr(activation,"activate_graph_candidate",fixture_base)
    original=prefix.recurrent_boundary
    restore=patch.install_activation_bridge("fixture-only")
    # The unchanged worker loader deliberately sends only top-level bindings.
    top={n:h for n,h in full.items()if "."not in n}
    stop=activation.activate_graph_candidate(cfg,enabled=True,emit=lambda x:None,source_bindings=top)
    assert prefix.recurrent_boundary is not original and delegated==[top]
    stop();restore()
    assert prefix.recurrent_boundary is original

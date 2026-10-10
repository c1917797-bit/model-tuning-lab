"""DEFAULT OFF source-bound pre-QKnorm/RoPE projection tap. No Torch import.
Exact instance-owned Session.bind/restore; return original projection unchanged.
"""
import inspect,json,os,sys,traceback
from pathlib import Path
BASE=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-calibration-capture-chain-v1-001")
ORDER=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-tp4-qkv-loader-order-v1-001")
sys.path.insert(0,str(BASE));sys.path.insert(0,str(ORDER))
from io_contract import require,reference,sha_file,publish_json,publish_bytes,record_failure
from post_rope_live import tensor_description,receiver
from raw_sink import channel_stats
import loader_bridge_current as loader_bridge
from loader_order import actual,LINEAR_MODULE,LINEAR_SHA
ENV="QWEN36_SKVQ_PROJECTION_CAPTURE_ENABLE"
HERE=Path(__file__).resolve().parent
def source_lock():
    import current_contract as C
    return C.source()
def active_frame(donor,outer):
    frame=inspect.currentframe();found=False
    try:
        frame=frame.f_back
        while frame is not None:
            if frame.f_code is donor.__code__ and frame.f_locals.get("self") is outer:
                require(not found,"no nested actual same projection caller");found=True
            frame=frame.f_back
        require(found,"actual source-pinned Qwen donor is projection caller")
    finally:del frame
def capture_projection(session,logical,outer,returned,source):
    key=(session.active,logical)
    require(session.in_forward and session.active is not None and not session.poisoned and not session.closed,
      "actual armed same-token eager forward")
    require(key not in session._skvq_projection_pending and key not in session._skvq_projection_seen,
      "one original projection before each actual cache event")
    directory=session.sink.path/("projection-sample-%03d-layer-%02d"%(session.active,int(logical.split(".")[2])))
    directory.mkdir() # exact owned exclusive evidence root
    torch=sys.modules.get("torch")
    descriptions={"return_type":type(returned).__name__,"tuple_length":len(returned) if type(returned) is tuple else None}
    if type(returned) is tuple and returned and torch is not None and isinstance(returned[0],torch.Tensor):
        descriptions["qkv"]=tensor_description(returned[0])
    pre=publish_json(directory/"RAW_PRE.json",{"schema":"SKVQ_PREPROJECTION_RAW_PRE_V1",
      "sample_id":session.active,"logical_layer":logical,"rank":session.w.rank,
      "actual_input_ref":session.input_ref,"token_ids_sha256":session.inputs["samples"][session.active]["token_ids_sha256"],
      "source_lock_ref":source,"returned_before_first_shape_assertion":descriptions,"snapshots_are_not_live_alias_evidence":True})
    try:
        donor,_=receiver(outer,outer.attn);active_frame(donor,outer)
        require(type(returned) is tuple and len(returned)==2 and returned[1] is None,"actual unchanged ordinary projection tuple")
        qkv=returned[0]
        require(torch is not None and isinstance(qkv,torch.Tensor) and qkv.device.type=="npu" and
          tuple(qkv.shape)==(4096,3584) and qkv.dtype in (torch.float16,torch.bfloat16) and qkv.is_contiguous(),
          "actual source-bound TP4 qgate3072/K256/V256 contiguous projection")
        order=actual(outer,session.w.rank)
        require(order["local_projection_offsets"]=={"k":3072,"v":3328},"exact actual legacy loader offsets")
        k=qkv[:,3072:3328];v=qkv[:,3328:3584]
        live={"qkv":tensor_description(qkv),"k":tensor_description(k),"v":tensor_description(v)}
        views_pre=publish_json(directory/"LIVE_VIEWS.json",{"schema":"SKVQ_PREPROJECTION_LIVE_VIEWS_V1",
          "raw_pre":pre,"actual_qkv_legacy_order":order,"live":live,"caller_is_actual_donor":True,
          "boundary":"original qkv_proj return before fused QKnorm/RoPE","q_gate_not_mixed_into_KV":True})
        kc=k.detach().to(device="cpu").contiguous().clone()
        raw=kc.view(torch.uint8).numpy().tobytes()
        require(len(raw)==2*2**20,"whole actual preprojection K")
        kref=publish_bytes(directory/"k_pre.a16",raw)
        statistics=channel_stats(kc.reshape(4096,1,256))
        vc=v.detach().to(device="cpu").contiguous().clone()
        vraw=vc.view(torch.uint8).numpy().tobytes()
        import hashlib
        vhash=hashlib.sha256(vraw).hexdigest()
        require(live=={"qkv":tensor_description(qkv),"k":tensor_description(k),"v":tensor_description(v)},
          "live original typed view remained unchanged during snapshots")
        r=publish_json(directory/"PREPROJECTION.json",{"schema":"SKVQ_PREPROJECTION_EVENT_V1",
          "sample_id":session.active,"logical_layer":logical,"rank":session.w.rank,"raw_pre":pre,"live_views_ref":views_pre,
          "k_ref":kref,"dtype":str(k.dtype),"k_shape":[4096,256],"k_statistics":statistics,
          "original_projection_v_snapshot_sha256":vhash,"original_projection_v_snapshot_bytes":len(vraw),
          "projection_v_snapshot_not_persisted_duplicate":True,"original_projection_return_unmodified":True,
          "Q_pre_and_gate_not_captured":True,"norm_weights_teacher_o_proj_pending":True,"native_ready":False})
        del kc,vc,raw,vraw
        session._skvq_projection_pending[key]=r
    except BaseException as e:
        record_failure(directory/"FAILED.json",{"status":"PROJECTION_CAPTURE_FAILED","raw_pre":pre,
          "primary":{"type":type(e).__name__,"message":str(e),"traceback":traceback.format_exc()}},e);raise
    return returned
def install_rpc(target,input_path,root,current_manifest_sha256):
    require(os.environ.get(ENV)=="1","additional explicit projection capture opt-in")
    import current_contract as C
    C.configure(current_manifest_sha256) # Actual worker process, not a parent Python global.
    source=source_lock()
    import spawn_startup as startup
    spawn_before=startup.before_worker(source)
    result=loader_bridge.install_rpc(target,input_path,root)
    w=loader_bridge.original.actual_worker(target);s=w._skvq_capture_session
    require(type(s) is loader_bridge.original.Session,"exact source-bound owned capture Session")
    s._skvq_projection_pending={};s._skvq_projection_seen=set()
    try:
        linear=sys.modules[LINEAR_MODULE];require(sha_file(linear.__file__)==LINEAR_SHA,"actual unchanged projection class source")
        for logical,(outer,_) in s.registry.items():
            p=outer.qkv_proj;original=p.forward
            require(inspect.ismethod(original) and original.__self__ is p and
              original.__func__ is linear.QKVParallelLinear.forward and
              Path(inspect.getsourcefile(original.__func__)).resolve()==Path(linear.__file__).resolve(),
              "actual source-defined unmodified original projection forward")
            def make(name,owner,old):
                def forward(projection,*args,**kwargs):
                    returned=old(*args,**kwargs)
                    return capture_projection(s,name,owner,returned,source)
                return forward
            s.bind(p,"forward",make(logical,outer,original))
        oldcapture=s.sink.capture
        def capture(sink,sample,logical,proof,query,key,value):
            identity=(sample,logical);require(identity in s._skvq_projection_pending,"actual projection before cache event")
            pref=s._skvq_projection_pending[identity];data=json.loads(Path(pref["path"]).read_text())
            require(reference(pref["path"])==pref,"immutable preprojection evidence")
            proof["actual_preprojection_ref"]=pref
            proof["projection_capture_source_lock_ref"]=source
            result=oldcapture(sample,logical,proof,query,key,value)
            event=json.loads(Path(result["path"]).read_text())
            require(event["snapshots"]["v"]["ref"]["sha256"]==data["original_projection_v_snapshot_sha256"] and
              event["snapshots"]["v"]["ref"]["bytes"]==data["original_projection_v_snapshot_bytes"],
              "entire actual preprojection V equals captured fused V, not inferred from function name")
            del s._skvq_projection_pending[identity];s._skvq_projection_seen.add(identity)
            return result
        s.bind(s.sink,"capture",capture)
        result["preprojection_source_lock_ref"]=source
        result["extra_k_raw_bytes_per_rank"]=8*2**30
        result["extra_K_raw_required_total"]=32*2**30
        result["author_kmeans_alpha_pending"]=True
        result["spawn_install_ref"]=startup.installed(w,s,source,spawn_before)
        return result
    except BaseException:
        s.restore();raise

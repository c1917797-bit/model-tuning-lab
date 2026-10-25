"""Real-source writer/durability failure and completion-boundary controls."""
import ast,hashlib,inspect,json,os,sys,threading
from pathlib import Path
from types import SimpleNamespace
import pytest
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from independent_evidence_step_durability import StepDurability,selected_step

def bind_writer(fd):
    source=(W/"graph_candidate/worker_loader.py").read_bytes()
    nodes=[n for n in ast.walk(ast.parse(source))if isinstance(n,ast.FunctionDef)and n.name=="raw_emit"]
    assert len(nodes)==1
    tree=ast.parse("""def bind(fd):
    policy=None
    manifest_hash="fixture"
    limits={"max_events":100000,"max_bytes":134217728}
    count=size=0
    lock=threading.Lock()
    fsync=os.fsync
    def set_sync(value):
        nonlocal fsync
        fsync=value
    return None
""")
    fn=tree.body[0];fn.body.insert(-1,nodes[0]);fn.body[-1]=ast.parse("return raw_emit,lambda:(count,size),set_sync").body[0]
    ast.fix_missing_locations(tree);scope={"threading":threading,"os":os,"json":json}
    exec(compile(tree,"<actual-production-writer>","exec"),scope)
    return scope["bind"](fd)

class Harness:
    def __init__(self,path,*,resolve=None,sync=None,**limits):
        self.path=path;self.fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);self.snapshots=[]
        self.raw,self.counts,set_sync=bind_writer(self.fd)
        def real_sync(fd):
            self.snapshots.append(path.read_bytes())
            return os.fsync(fd)
        self.p=StepDurability(self.fd,sync or real_sync,self.counts,
            resolve=resolve or(lambda e:None if e.get("outside")else((0,e.get("step",1)),("r",))),**limits)
        set_sync(self.p.fsync);self.emit=self.p.wrap(self.raw)
    def rows(self):return [json.loads(x)for x in self.path.read_text().splitlines()]
    def close_fd(self):os.close(self.fd)

def test_actual_bytes_order_and_completion_fence_before_return(tmp_path):
    h=Harness(tmp_path/"events")
    try:
        original=[{"event":"one"},{"event":"two"},{"event":"compact_model_rows_completed"}]
        for event in original[:2]:h.emit(event)
        assert not h.snapshots and h.counts()[0]==2
        h.emit(original[-1])
        assert len(h.snapshots)==2 and h.p.fsync_completed==2
        assert json.loads(h.snapshots[0].splitlines()[-1])["event"]=="compact_model_rows_completed"
        assert json.loads(h.snapshots[1].splitlines()[-1])["event"]=="r36_evidence_step_durable"
        rows=h.rows();assert [x["event"]for x in rows[:3]]==[x["event"]for x in original]
        receipt=rows[-1];assert receipt["original_written_events"]==receipt["original_fsync_requests"]==3
        assert receipt["deferred_fsync_requests"]==2 and receipt["callback_returns_after_receipt_fsync"]is True
        assert receipt["original_end_bytes"]==len(h.snapshots[0])and receipt["original_start_bytes"]==0
        assert h.counts()==(4,len(h.snapshots[1]))and h.p.active is None
        h.p.close();h.p.close();assert len(h.snapshots)==2
    finally:h.close_fd()

def test_original_event_bytes_identical_to_unmodified_writer(tmp_path):
    h=Harness(tmp_path/"candidate");p=tmp_path/"original";fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    try:
        raw,_,_=bind_writer(fd)
        for event in({"event":"x","value":[1,2]},{"event":"compact_model_rows_completed"}):
            raw(event);h.emit(event)
        assert b"".join(h.path.read_bytes().splitlines(keepends=True)[:-1])==p.read_bytes()
    finally:os.close(fd);h.close_fd()

@pytest.mark.parametrize("failure_call",[1,2])
def test_failed_completion_or_receipt_fsync_cannot_return_success(tmp_path,failure_call):
    error=OSError("injected durability failure");calls=[]
    def sync(fd):
        calls.append(fd)
        if len(calls)==failure_call:raise error
        os.fsync(fd)
    h=Harness(tmp_path/"events",sync=sync)
    try:
        h.emit({"event":"one"})
        with pytest.raises(OSError)as raised:h.emit({"event":"compact_model_rows_completed"})
        assert raised.value is error and h.p.failed
        if failure_call==1:assert all(x["event"]!="r36_evidence_step_durable"for x in h.rows())
        with pytest.raises(RuntimeError):h.emit({"event":"later","step":2})
        h.p.close()
    finally:h.close_fd()

def test_original_write_error_identity_and_cleanup_failure_note(tmp_path,monkeypatch):
    h=Harness(tmp_path/"events");error=OSError("original write failure");cleanup=OSError("cleanup")
    monkeypatch.setattr(os,"write",lambda fd,data:(_ for _ in()).throw(error))
    h.p.original_fsync=lambda fd:(_ for _ in()).throw(cleanup)
    try:
        with pytest.raises(OSError)as raised:h.emit({"event":"one"})
        assert raised.value is error and h.p.cleanup_error is cleanup and h.p.failed
        if hasattr(error,"__notes__"):assert "cleanup" in error.__notes__[0]
        assert h.path.read_bytes()==b""
    finally:h.close_fd()

def test_short_write_is_original_failure_not_success(tmp_path,monkeypatch):
    h=Harness(tmp_path/"events");monkeypatch.setattr(os,"write",lambda fd,data:0)
    try:
        with pytest.raises(OSError,match="short graph evidence write"):h.emit({"event":"one"})
        assert h.p.failed and not h.rows()
    finally:h.close_fd()

def test_outside_context_keeps_per_event_sync(tmp_path):
    h=Harness(tmp_path/"events")
    try:
        h.emit({"event":"public","outside":True});h.emit({"event":"native","outside":True})
        assert len(h.snapshots)==h.counts()[0]==2 and not h.p.sealed
        h.p.close();assert len(h.snapshots)==2
    finally:h.close_fd()

@pytest.mark.parametrize("next_event",[{"event":"abandoned","outside":True},{"event":"overlap","step":2}])
def test_abandoned_or_changed_context_flushes_and_fails(tmp_path,next_event):
    h=Harness(tmp_path/"events")
    try:
        h.emit({"event":"first"})
        with pytest.raises(ValueError):h.emit(next_event)
        assert len(h.rows())==1 and len(h.snapshots)==1 and h.p.failed
    finally:h.close_fd()

def test_bound_rejects_before_next_raw_write_and_flushes_prefix(tmp_path):
    h=Harness(tmp_path/"events",max_events=1)
    try:
        h.emit({"event":"first"})
        with pytest.raises(ValueError,match="event bound"):h.emit({"event":"next"})
        assert len(h.rows())==1 and len(h.snapshots)==1
    finally:h.close_fd()

def test_byte_bound_flushes_failed_prefix_without_completion(tmp_path):
    h=Harness(tmp_path/"events",max_bytes=1)
    try:
        with pytest.raises(ValueError,match="bytes"):h.emit({"event":"first"})
        assert len(h.rows())==len(h.snapshots)==1 and h.p.failed
    finally:h.close_fd()

def test_close_unfinished_step_never_emits_valid_seal(tmp_path):
    h=Harness(tmp_path/"events")
    try:
        h.emit({"event":"first"})
        with pytest.raises(ValueError,match="uncompleted"):h.p.close()
        assert len(h.snapshots)==1 and len(h.rows())==1 and h.p.closed
        h.p.close()
    finally:h.close_fd()

def test_foreign_fd_never_delegated(tmp_path):
    h=Harness(tmp_path/"events")
    try:
        with pytest.raises(ValueError,match="owned"):h.p.fsync(h.fd+1)
        assert not h.snapshots
    finally:h.close_fd()

def test_sealed_key_cannot_reopen_and_next_unique_step_valid(tmp_path):
    h=Harness(tmp_path/"events")
    try:
        h.emit({"event":"compact_model_rows_completed","step":1})
        h.emit({"event":"compact_model_rows_completed","step":2})
        assert len(h.p.sealed)==2 and len(h.snapshots)==4
        with pytest.raises(ValueError,match="seal"):h.emit({"event":"late","step":1})
    finally:h.close_fd()

def test_recursive_writer_fails_without_nested_record(tmp_path):
    h=Harness(tmp_path/"events")
    try:
        def recursive(event):return emit({"event":"nested"})
        emit=h.p.wrap(recursive)
        with pytest.raises(RuntimeError,match="recursive"):emit({"event":"outer"})
        assert not h.rows()and h.p.failed
    finally:h.close_fd()

def test_thread_overlap_rejected_before_second_record(tmp_path):
    h=Harness(tmp_path/"events");errors=[]
    try:
        h.emit({"event":"first"})
        def other():
            try:h.emit({"event":"other"})
            except BaseException as e:errors.append(e)
        thread=threading.Thread(target=other);thread.start();thread.join()
        assert len(errors)==1 and isinstance(errors[0],ValueError)and len(h.rows())==1
        assert h.p.failed and len(h.snapshots)==1
    finally:h.close_fd()

def test_missing_original_write_or_fsync_cannot_seal(tmp_path):
    h=Harness(tmp_path/"events")
    try:
        with pytest.raises(ValueError,match="complete write"):h.p.wrap(lambda event:None)({"event":"first"})
        assert h.p.failed and not h.rows()
    finally:h.close_fd()

def test_actual_context_resolver_and_identity_negative_controls(monkeypatch):
    selection=SimpleNamespace(plans=(SimpleNamespace(rank=2,step=7,request_id="r"),))
    context=SimpleNamespace(get=lambda:selection)
    monkeypatch.setitem(sys.modules,"independent_compact_model_hook",SimpleNamespace(CURRENT_COMPACT_MODEL=context))
    assert selected_step({"rank":2,"step":7})==((2,7),("r",))
    with pytest.raises(ValueError):selected_step({"rank":1,"step":7})
    selection.plans=(SimpleNamespace(rank=True,step=7,request_id="r"),)
    with pytest.raises(ValueError):selected_step({})

def test_default_disabled_and_manifest_binding(monkeypatch):
    from graph_candidate.worker_loader import _step_durability_enabled
    monkeypatch.delenv("INDEPENDENT_EVIDENCE_STEP_DURABILITY",raising=False)
    assert _step_durability_enabled({})is False
    mf={"step_durability":{"enabled":True,"profile":"selected-model-step-durability-v1"},
        "source_sha256":{"independent_evidence_step_durability.py":"bound"}}
    with pytest.raises(ValueError):_step_durability_enabled(mf)
    monkeypatch.setenv("INDEPENDENT_EVIDENCE_STEP_DURABILITY","1")
    with pytest.raises(ValueError):_step_durability_enabled({})
    assert _step_durability_enabled(mf)is True
    monkeypatch.setenv("INDEPENDENT_EVIDENCE_STEP_DURABILITY","true")
    with pytest.raises(ValueError):_step_durability_enabled(mf)

def test_default_loader_imports_no_durability_module():
    import subprocess
    env=dict(os.environ);env.pop("INDEPENDENT_GRAPH_HYPIC",None)
    p=subprocess.run([sys.executable,"-B","-c",
        "import sys;import graph_candidate.worker_loader as w;w.enable();assert 'independent_evidence_step_durability' not in sys.modules"],
        cwd=W,env=env,capture_output=True,text=True)
    assert p.returncode==0,p.stderr

def test_executable_source_guards_and_tamper(monkeypatch):
    import independent_evidence_step_durability as module
    from graph_candidate.prefill_bridge import verify_support
    from graph_candidate.source_contract import verify_raw_function
    source=verify_support(module,hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest())
    for name in("selected_step","make_durability"):
        verify_raw_function(module,source,getattr(module,name),name=name)
    for name,value in vars(module.StepDurability).items():
        if inspect.isfunction(value):verify_raw_function(module,source,value,name=name,qualname="StepDurability."+name)
    monkeypatch.setattr(module.StepDurability,"fsync",lambda self,fd:None)
    with pytest.raises(ValueError):
        verify_raw_function(module,source,module.StepDurability.fsync,name="fsync",qualname="StepDurability.fsync")

def test_close_failure_does_not_replace_original_loader_error():
    from graph_candidate.worker_loader import _close_durability
    error=OSError("original")
    policy=SimpleNamespace(close=lambda:(_ for _ in()).throw(ValueError("close")))
    assert _close_durability(policy,error)is None
    if hasattr(error,"__notes__"):assert "close" in error.__notes__[0]
    with pytest.raises(ValueError):_close_durability(policy)

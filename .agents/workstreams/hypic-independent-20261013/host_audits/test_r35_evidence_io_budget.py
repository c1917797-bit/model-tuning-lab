import ast,hashlib,importlib.util,json,os,sys
from pathlib import Path
from types import SimpleNamespace
import pytest
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from independent_evidence_io_budget import EvidenceIOBudget,selected_step,interval_union_ns

def writer(path):
    fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);state=[0,0];syncs=[]
    def sync(value):syncs.append(value);return os.fsync(value)
    budget=EvidenceIOBudget(fd,sync,lambda:tuple(state),
        resolve=lambda e:None if e.get("outside")else((e.get("rank",0),e.get("step",1)),("r",)))
    def raw(event):
        if event.get("event")=="filtered":return
        data=(json.dumps(event,sort_keys=True)+"\n").encode()
        os.write(fd,data);budget.fsync(fd);state[0]+=1;state[1]+=len(data)
    return fd,state,syncs,budget,raw

def test_original_rows_and_fsync_kept_extra_row_is_not_recursive(tmp_path):
    p=tmp_path/"events";fd,state,syncs,b,raw=writer(p)
    try:
        emit=b.wrap(raw);emit({"event":"layer","rank":0,"step":1})
        emit({"event":"compact_model_rows_completed","rank":0,"step":1})
    finally:os.close(fd)
    rows=[json.loads(x)for x in p.read_text().splitlines()]
    assert [x["event"]for x in rows]==["layer","compact_model_rows_completed","r35_evidence_io_budget_step"]
    report=rows[-1];assert report["original_emit_calls"]==2
    assert report["original_fsync_calls"]==report["original_written_events"]==2
    assert len(syncs)==state[0]==3
    assert report["fsync_interval_union_ns"]<=report["emit_interval_union_ns"]
    assert not b.buckets and len(b.sealed)==1

def test_outside_context_original_writer_only(tmp_path):
    p=tmp_path/"events";fd,state,syncs,b,raw=writer(p)
    try:b.wrap(raw)({"event":"native","outside":True})
    finally:os.close(fd)
    assert state[0]==len(syncs)==1 and b.events==0 and not b.sealed

def test_original_error_object_propagates(tmp_path):
    p=tmp_path/"events";fd,state,syncs,b,raw=writer(p);error=OSError("original failure")
    def failing(event):raise error
    try:
        with pytest.raises(OSError)as raised:b.wrap(failing)({"event":"failure"})
        assert raised.value is error and b.buckets[(0,1)]["failed"]==1
    finally:os.close(fd)

def test_filtered_event_not_claimed_written(tmp_path):
    p=tmp_path/"events";fd,state,syncs,b,raw=writer(p)
    try:
        emit=b.wrap(raw);emit({"event":"filtered"});emit({"event":"compact_model_rows_completed"})
    finally:os.close(fd)
    report=json.loads(p.read_text().splitlines()[-1])
    assert report["original_emit_calls"]==2 and report["original_filtered_calls"]==1
    assert report["original_written_events"]==report["original_fsync_calls"]==1

def test_foreign_fd_refused_before_delegate(tmp_path):
    fd,state,syncs,b,raw=writer(tmp_path/"events")
    try:
        with pytest.raises(ValueError):b.fsync(fd+1)
        assert not syncs
    finally:os.close(fd)

def test_bound_refuses_next_event_before_original_callback(tmp_path):
    fd,state,syncs,b,raw=writer(tmp_path/"events");b.max_events=1
    try:
        emit=b.wrap(raw);emit({"event":"first"})
        with pytest.raises(ValueError):emit({"event":"second"})
        assert state[0]==len(syncs)==1
    finally:os.close(fd)

def test_step_seal_cannot_be_reentered_and_next_step_separate(tmp_path):
    p=tmp_path/"events";fd,state,syncs,b,raw=writer(p)
    try:
        emit=b.wrap(raw);emit({"event":"compact_model_rows_completed","step":1})
        with pytest.raises(ValueError):emit({"event":"late","step":1})
        emit({"event":"compact_model_rows_completed","step":2})
    finally:os.close(fd)
    reports=[json.loads(x)for x in p.read_text().splitlines()if"r35_evidence_io_budget_step"in x]
    assert [x["step"]for x in reports]==[1,2]and all(x["original_emit_calls"]==1 for x in reports)

def test_recursive_callback_refused_without_extra_raw_write(tmp_path):
    fd,state,syncs,b,raw=writer(tmp_path/"events")
    try:
        def recursive(event):return emit({"event":"nested"})
        emit=b.wrap(recursive)
        with pytest.raises(RuntimeError):emit({"event":"outer"})
        assert not syncs and state[0]==0
    finally:os.close(fd)

def test_union_counts_overlapping_threads_once():
    assert interval_union_ns([(1,5),(2,6),(8,9)])==6

def test_real_context_resolver_does_not_import_runtime(monkeypatch):
    class Context:
        def get(self):return SimpleNamespace(plans=(SimpleNamespace(rank=2,step=7,request_id="r"),))
    monkeypatch.setitem(sys.modules,"independent_compact_model_hook",SimpleNamespace(CURRENT_COMPACT_MODEL=Context()))
    assert selected_step({"event":"layer","rank":2,"step":7})==((2,7),("r",))
    with pytest.raises(ValueError):selected_step({"rank":1,"step":7})

def _source_writer(old):
    import subprocess
    if old:
        data=subprocess.check_output(["git","show","719557121d87dc7b4ad6184b76e695aa76c32650:.agents/workstreams/hypic-independent-20261013/graph_candidate/worker_loader.py"],cwd=W)
        assert hashlib.sha256(data).hexdigest()=="eb3c6f79b4a49287a274ca25e28cc3e363fde3f4b8de099c7a641d04ce481ade"
        name="emit"
    else:
        data=(W/"graph_candidate/worker_loader.py").read_bytes();name="raw_emit"
    nodes=[n for n in ast.walk(ast.parse(data))if isinstance(n,ast.FunctionDef)and n.name==name]
    assert len(nodes)==1
    return nodes[0]

def _bind_actual_writer(node,fd):
    import copy,threading
    tree=ast.parse("""def bind(fd):
    policy=None
    manifest_hash="fixed-fixture"
    limits={"max_events":100,"max_bytes":100000}
    count=size=0
    lock=threading.Lock()
    fsync=os.fsync
    def set_sync(value):
        nonlocal fsync
        fsync=value
    return None
""")
    fn=tree.body[0];fn.body.insert(-1,copy.deepcopy(node))
    fn.body[-1]=ast.parse("return "+node.name+", lambda: (count,size), set_sync").body[0]
    ast.fix_missing_locations(tree);space={"threading":threading,"os":os,"json":json}
    exec(compile(tree,"<actual-source-writer-control>","exec"),space)
    return space["bind"](fd)

def test_default_off_production_raw_writer_body_matches_frozen_original(tmp_path):
    old=_source_writer(True);new=_source_writer(False)
    class Normalize(ast.NodeTransformer):
        def visit_Call(self,node):
            self.generic_visit(node)
            if isinstance(node.func,ast.Name)and node.func.id=="fsync":
                node.func=ast.Attribute(ast.Name("os",ast.Load()),"fsync",ast.Load())
            return node
    new=Normalize().visit(new);new.name="emit"
    assert ast.dump(old,include_attributes=False)==ast.dump(new,include_attributes=False)
    for label,node in(("old",old),("new",_source_writer(False))):
        fd=os.open(tmp_path/label,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        try:
            emit,counts,_=_bind_actual_writer(node,fd)
            emit({"event":"layer","rank":0,"step":1});emit({"event":"compact_model_rows_completed","rank":0,"step":1})
            assert counts()[0]==2
        finally:os.close(fd)
    assert(tmp_path/"old").read_bytes()==(tmp_path/"new").read_bytes()

def test_actual_production_writer_with_observer_keeps_original_rows(tmp_path):
    p=tmp_path/"enabled";fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    try:
        raw,counts,set_sync=_bind_actual_writer(_source_writer(False),fd)
        b=EvidenceIOBudget(fd,os.fsync,counts,resolve=lambda e:((0,1),("r",)))
        set_sync(b.fsync);emit=b.wrap(raw)
        emit({"event":"layer","rank":0,"step":1});emit({"event":"compact_model_rows_completed","rank":0,"step":1})
    finally:os.close(fd)
    rows=[json.loads(x)for x in p.read_text().splitlines()]
    assert [x["event"]for x in rows]==["layer","compact_model_rows_completed","r35_evidence_io_budget_step"]
    assert all(x["manifest_sha256"]=="fixed-fixture"for x in rows)
    assert rows[-1]["original_fsync_calls"]==rows[-1]["original_written_events"]==2

def test_actual_loader_disabled_does_not_import_observer():
    import subprocess
    env=dict(os.environ);env.pop("INDEPENDENT_GRAPH_HYPIC",None)
    p=subprocess.run([sys.executable,"-B","-c",
        "import sys;import graph_candidate.worker_loader as w;w.enable();assert 'independent_evidence_io_budget' not in sys.modules"],
        cwd=W,env=env,capture_output=True,text=True)
    assert p.returncode==0,p.stderr

def test_actual_loader_observer_requires_manifest_and_explicit_flag(monkeypatch):
    from graph_candidate.worker_loader import _io_budget_enabled
    monkeypatch.delenv("INDEPENDENT_EVIDENCE_IO_BUDGET",raising=False)
    assert _io_budget_enabled({})is False
    bound={"evidence_io_budget":{"enabled":True,"profile":"owned-evidence-io-budget-v1"},
        "source_sha256":{"independent_evidence_io_budget.py":"fixture"}}
    with pytest.raises(ValueError):_io_budget_enabled(bound)
    monkeypatch.setenv("INDEPENDENT_EVIDENCE_IO_BUDGET","1")
    with pytest.raises(ValueError):_io_budget_enabled({})
    assert _io_budget_enabled(bound)is True
    monkeypatch.setenv("INDEPENDENT_EVIDENCE_IO_BUDGET","true")
    with pytest.raises(ValueError):_io_budget_enabled(bound)

def test_actual_observer_executable_source_guards_and_tamper(monkeypatch):
    import inspect,independent_evidence_io_budget as module
    from graph_candidate.prefill_bridge import verify_support
    from graph_candidate.source_contract import verify_raw_function
    source=verify_support(module,hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest())
    for name in("selected_step","interval_union_ns","make_budget"):
        verify_raw_function(module,source,getattr(module,name),name=name)
    for name,value in vars(module.EvidenceIOBudget).items():
        if inspect.isfunction(value):verify_raw_function(module,source,value,name=name,qualname="EvidenceIOBudget."+name)
    monkeypatch.setattr(module.EvidenceIOBudget,"fsync",lambda self,fd:None)
    with pytest.raises(ValueError):
        verify_raw_function(module,source,module.EvidenceIOBudget.fsync,name="fsync",qualname="EvidenceIOBudget.fsync")

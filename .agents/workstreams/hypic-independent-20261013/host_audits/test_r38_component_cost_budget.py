"""Component observer ownership, exception, interval and original-writer controls."""
import ast,contextlib,hashlib,json,os,sys,threading,types
from pathlib import Path
import pytest
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from independent_component_cost_budget import ComponentBudget,GROUPS,SPECS
class Clock:
    def __init__(self):self.n=0
    def __call__(self):self.n+=10;return self.n
def make(**kw):
    rows=[];identity=[((0,7),("cmpl-aa-0-dead",))]
    b=ComponentBudget(rows.append,lambda e:identity[0],clock=Clock(),**kw)
    return b,rows,identity
def completion(rank=0,step=7,ids=None):
    return {"event":"compact_model_rows_completed","rank":rank,"step":step,
            "request_ids":["cmpl-aa-0-dead"]if ids is None else ids}
def test_no_target_changes_at_import_or_construction():
    b,rows,_=make()
    assert b.slots==[] and not rows and b.active is None
def test_outside_selected_context_preserves_arguments_and_result():
    b,rows,ids=make();ids[0]=None;result=object();calls=[]
    def original(*a,**k):calls.append((a,k));return result
    assert b.timed(GROUPS[0],original,1,x=2)is result
    assert calls==[((1,),{"x":2})]and b.active is None and not rows
def test_nested_intervals_do_not_double_add_parent_and_child():
    b,rows,_=make();result=object()
    assert b.timed(GROUPS[0],lambda:b.timed(GROUPS[1],lambda:result))is result
    original=[];emit=b.wrap_emit(lambda e:original.append(e))
    emit(completion())
    a=rows[0];parent=a["groups"][GROUPS[0]];child=a["groups"][GROUPS[1]]
    assert parent["calls"]==child["calls"]==1
    assert parent["inclusive_ns"]>=child["inclusive_ns"]>0
    assert a["root_interval_union_ns"]==parent["inclusive_ns"]
    assert parent["exclusive_observed_ns"]==parent["inclusive_ns"]-child["inclusive_ns"]
    assert rows[1]["event"]=="r38_component_budget_flush"and len(original)==1
    b.close();b.close()
def test_original_exception_identity_survives_timing_cleanup_failure():
    rows=[];sentinel=ValueError("original failure");n=[0]
    def clock():
        n[0]+=1
        if n[0]==3:raise OSError("timing cleanup failed")
        return n[0]
    b=ComponentBudget(rows.append,lambda e:((0,7),("a",)),clock=clock)
    with pytest.raises(ValueError)as caught:
        b.timed(GROUPS[0],lambda:(_ for _ in ()).throw(sentinel))
    assert caught.value is sentinel and b.failed and not rows
def test_completion_identity_and_original_return_preserved():
    b,rows,_=make();b.timed(GROUPS[0],lambda:None);value=object();events=[]
    def original(e):events.append(e);return value
    done=completion();assert b.wrap_emit(original)(done)is value
    assert events==[done]and events[0]is done and len(rows)==2
def test_noncompletion_events_not_filtered_or_reordered():
    b,rows,_=make();events=[];value=object()
    def original(e):events.append(e);return value
    f=b.wrap_emit(original)
    for i in range(5):assert f({"event":"original","i":i})is value
    assert events==[{"event":"original","i":i}for i in range(5)]and not rows
@pytest.mark.parametrize("changed",[None,((1,7),("cmpl-aa-0-dead",)),((0,8),("cmpl-aa-0-dead",)),((0,7),("different",))])
def test_selected_context_change_during_component_rejected(changed):
    b,rows,ids=make()
    with pytest.raises(ValueError,match="context changed"):
        b.timed(GROUPS[0],lambda:ids.__setitem__(0,changed))
    assert b.failed and not rows
def test_wrong_completion_cannot_commit_original_or_receipts():
    b,rows,_=make();b.timed(GROUPS[0],lambda:None);events=[]
    with pytest.raises(ValueError):b.wrap_emit(events.append)(completion(ids=["other"]))
    assert not events and not rows and b.failed
def test_call_limit_stops_before_next_original():
    b,rows,_=make(max_calls=1);called=[]
    b.timed(GROUPS[0],lambda:called.append(1))
    with pytest.raises(ValueError):b.timed(GROUPS[0],lambda:called.append(2))
    assert called==[1]and not rows
def test_recursive_target_rejected():
    b,rows,_=make()
    with pytest.raises(RuntimeError):b.timed(GROUPS[0],lambda:b.timed(GROUPS[0],lambda:None))
    assert b.failed and not rows
def test_unsealed_close_and_late_step_fail():
    b,rows,_=make();b.timed(GROUPS[0],lambda:None)
    with pytest.raises(ValueError):b.close()
    b,rows,_=make();b.timed(GROUPS[0],lambda:None);b.wrap_emit(lambda e:None)(completion())
    with pytest.raises(ValueError):b.timed(GROUPS[0],lambda:None)
def test_step_bound():
    b,rows,ids=make(max_steps=1);b.timed(GROUPS[0],lambda:None);b.wrap_emit(lambda e:None)(completion())
    ids[0]=((0,8),("cmpl-aa-0-dead",))
    with pytest.raises(ValueError):b.timed(GROUPS[0],lambda:None)
def test_receipt_failure_is_not_a_successful_component_seal():
    failure=OSError("owned receipt failed")
    b=ComponentBudget(lambda e:(_ for _ in ()).throw(failure),lambda e:((0,7),("cmpl-aa-0-dead",)),clock=Clock())
    b.timed(GROUPS[0],lambda:None);original=[]
    with pytest.raises(OSError)as caught:b.wrap_emit(original.append)(completion())
    assert caught.value is failure and len(original)==1 and not b.sealed and b.failed
def fake_modules(tmp_path,monkeypatch):
    bindings={}
    for module_name,class_name,name,group in SPECS:
        code=("def "+name+"(*args,**kwargs):\n    return (args,kwargs)\n"if class_name is None else
              "class "+class_name+":\n    def "+name+"(self,*args,**kwargs):\n        return (args,kwargs)\n")
        path=tmp_path/(module_name+".py");path.write_text(code)
        module=types.ModuleType(module_name);module.__file__=str(path)
        exec(compile(code,str(path),"exec"),module.__dict__)
        monkeypatch.setitem(sys.modules,module_name,module)
        bindings[module_name]=hashlib.sha256(path.read_bytes()).hexdigest()
    return bindings
def test_source_owned_install_calls_original_and_restores(tmp_path,monkeypatch):
    bindings=fake_modules(tmp_path,monkeypatch);b,rows,_=make()
    owners=[(sys.modules[m]if c is None else getattr(sys.modules[m],c),n)for m,c,n,g in SPECS]
    originals=[getattr(o,n)for o,n in owners]
    stop=b.install(bindings,tmp_path)
    for o,n in owners:
        f=getattr(o,n);assert hasattr(f,"__wrapped__")
        result=f(1,k=2)if isinstance(o,types.ModuleType)else f(o(),1,k=2)
        assert result==((1,),{"k":2})
    b.wrap_emit(lambda e:None)(completion());stop();stop()
    assert all(getattr(o,n)is f for(o,n),f in zip(owners,originals))
def test_unknown_target_is_not_overwritten_on_uninstall(tmp_path,monkeypatch):
    bindings=fake_modules(tmp_path,monkeypatch);b,rows,_=make();b.install(bindings,tmp_path)
    module=sys.modules[SPECS[0][0]];foreign=lambda:None
    setattr(module,SPECS[0][2],foreign)
    with pytest.raises(RuntimeError):b.stop()
    assert getattr(module,SPECS[0][2])is foreign
def test_source_drift_rejected_before_any_target_change(tmp_path,monkeypatch):
    bindings=fake_modules(tmp_path,monkeypatch);module=sys.modules[SPECS[0][0]]
    original=getattr(module,SPECS[0][2]);bindings[SPECS[0][0]]="0"*64
    b,rows,_=make()
    with pytest.raises(ValueError):b.install(bindings,tmp_path)
    assert getattr(module,SPECS[0][2])is original and not b.slots
def real_writer(fd):
    # Compile the actual unmodified source writer body; preserve its counters,
    # complete writes, serialization, lock and per-record fsync requests.
    path=W/"graph_candidate/worker_loader.py"
    tree=ast.parse(path.read_bytes())
    writer=[n for n in ast.walk(tree)if isinstance(n,ast.FunctionDef)and n.name=="raw_emit"]
    assert len(writer)==1
    wrapper=ast.parse("""def bind(fd):
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
    fn=wrapper.body[0];fn.body.insert(-1,writer[0])
    fn.body[-1]=ast.parse("return raw_emit,lambda:(count,size),set_sync").body[0]
    ast.fix_missing_locations(wrapper);scope={"json":json,"os":os,"threading":threading}
    exec(compile(wrapper,"<actual-r38-original-writer>","exec"),scope)
    return scope["bind"](fd)
def test_actual_original_writer_and_r36_fence_survive_component_receipts(tmp_path):
    from independent_evidence_step_durability import StepDurability
    from host_audits.r36_durability_evidence import audit_durable_files
    path=tmp_path/"worker.jsonl";fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    try:
        raw,counts,set_sync=real_writer(fd);identity=lambda e:((0,7),("cmpl-aa-0-dead",))
        durable=StepDurability(fd,os.fsync,counts,resolve=identity);set_sync(durable.fsync)
        budget=ComponentBudget(raw,identity,clock=Clock());emit=budget.wrap_emit(durable.wrap(raw))
        emit({"event":"layer","rank":0,"step":7})
        budget.timed(GROUPS[0],lambda:budget.timed(GROUPS[1],lambda:None))
        emit(completion());budget.close();durable.close()
        assert counts()[0]==5 and durable.fsync_completed==4
    finally:os.close(fd)
    rows=[json.loads(x)for x in path.read_text().splitlines()]
    assert[x["event"]for x in rows]==["layer","compact_model_rows_completed","r36_evidence_step_durable","r38_component_budget_step","r38_component_budget_flush"]
    assert rows[2]["original_written_events"]==2
    workers={rank:os.getpid()+rank for rank in range(4)}
    assert len({len(str(pid))for pid in workers.values()})==1
    files={}
    for rank,pid in workers.items():
        copied=[dict(row,pid=pid,rank=rank)for row in rows]
        data=("".join(json.dumps(row,sort_keys=True)+"\n"for row in copied)).encode()
        files["compact-worker-"+str(pid)+".jsonl"]=data
    checked=audit_durable_files(files,["cmpl-aa"],workers,"fixture",enabled=True)
    assert checked["actual_completed_model_steps"]==checked["durable_fences"]==4

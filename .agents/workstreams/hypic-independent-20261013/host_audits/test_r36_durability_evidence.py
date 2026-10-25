"""Independent durable-byte/fence rejection controls; fixtures are synthetic."""
import copy,json,sys
from pathlib import Path
import pytest
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits.r36_durability_evidence import audit_durable_files
WORKERS={r:10+r for r in range(4)}
def encode(rows):return b"".join((json.dumps(e,sort_keys=True)+"\n").encode()for e in rows)
def fixture(enabled):
    files={}
    for rank,pid in WORKERS.items():
        def event(kind,**extra):return dict(event=kind,pid=pid,manifest_sha256="m",**extra)
        rows=[event("install"),event("layer",rank=rank,step=5),
              event("compact_model_rows_completed",rank=rank,step=5,request_ids=["cmpl-measured-0-x"])]
        if enabled:
            before=len(encode(rows[:1]));end=len(encode(rows))
            rows.append(event("r36_evidence_step_durable",rank=rank,step=5,request_ids=["cmpl-measured-0-x"],
                original_start_count=1,original_end_count=3,original_start_bytes=before,original_end_bytes=end,
                original_written_events=2,original_written_bytes=end-before,original_fsync_requests=2,
                deferred_fsync_requests=1,completion_fsync_calls=1,receipt_fsync_calls=1,
                completion_fsync_returned_before_receipt=True,callback_returns_after_receipt_fsync=True))
        files["compact-worker-"+str(pid)+".jsonl"]=encode(rows)
    return files
def run(files,enabled=True,ids=None):
    return audit_durable_files(files,["cmpl-measured"]if ids is None else ids,WORKERS,"m",enabled=enabled)
def replace_first(files,change):
    out=copy.deepcopy(files);name="compact-worker-10.jsonl";rows=[json.loads(x)for x in out[name].splitlines()]
    change(rows);out[name]=encode(rows);return out

def test_enabled_fences_cover_every_rank_and_original_byte_range():
    report=run(fixture(True))
    assert report["selected_step_durability_valid"]and report["durable_fences"]==4
    assert report["actual_completed_model_steps"]==4
    assert all(r["original_written_events"]==r["original_fsync_requests"]==2 for r in report["ranks"])
    assert all(r["source_completion_and_receipt_fsync_calls"]==2 for r in report["ranks"])
    assert not report["speed_gain_inferred"]and not report["fsync_syscall_trace_proven"]

def test_disabled_control_has_original_models_and_no_fences():
    report=run(fixture(False),False)
    assert not report["enabled"]and report["durable_fences"]==0
    assert report["actual_completed_model_steps"]==4
    with pytest.raises(ValueError):run(fixture(True),False)

@pytest.mark.parametrize("field,value",[
 ("original_start_count",0),("original_end_count",2),("original_start_bytes",0),
 ("original_end_bytes",999999),("original_written_events",3),("original_written_bytes",1),
 ("original_fsync_requests",True),("deferred_fsync_requests",2),("completion_fsync_calls",0),
 ("receipt_fsync_calls",0),("callback_returns_after_receipt_fsync",False),
 ("completion_fsync_returned_before_receipt",False),("request_ids",["other"])])
def test_tampered_fence_never_accepted(field,value):
    files=replace_first(fixture(True),lambda rows:rows[-1].update({field:value}))
    with pytest.raises(ValueError):run(files)

def test_missing_duplicate_or_nonadjacent_fence_rejected():
    for change in (lambda rows:rows.pop(),lambda rows:rows.append(dict(rows[-1])),
                   lambda rows:rows.insert(-1,dict(rows[0]))):
        with pytest.raises(ValueError):run(replace_first(fixture(True),change))

def test_foreign_worker_file_or_raw_identity_rejected():
    files=fixture(True);files["compact-worker-999.jsonl"]=files.pop("compact-worker-10.jsonl")
    with pytest.raises(ValueError):run(files)
    files=replace_first(fixture(True),lambda rows:rows[1].update(pid=999))
    with pytest.raises(ValueError):run(files)
    files=replace_first(fixture(True),lambda rows:rows[1].update(manifest_sha256="wrong"))
    with pytest.raises(ValueError):run(files)

def test_timing_observer_or_nested_model_rejected():
    files=replace_first(fixture(False),lambda rows:rows.append(dict(rows[1],event="r35_evidence_io_budget_step")))
    with pytest.raises(ValueError):run(files,False)
    files=replace_first(fixture(True),lambda rows:rows[1].update(event="compact_model_rows_completed",request_ids=["cmpl-measured-0-x"]))
    with pytest.raises(ValueError):run(files)

def test_duplicate_missing_or_ambiguous_http_identity_rejected():
    with pytest.raises(ValueError):run(fixture(True),ids=["cmpl-measured","cmpl-measured"])
    with pytest.raises(ValueError):run(fixture(True),ids=["absent"])
    files=replace_first(fixture(False),lambda rows:rows.append(dict(rows[-1],step=6,request_ids=["cmpl-measured-0-y"])))
    with pytest.raises(ValueError):run(files,False)

def test_incomplete_jsonl_or_missing_worker_cannot_pass():
    files=fixture(True);files["compact-worker-10.jsonl"]=files["compact-worker-10.jsonl"].rstrip(b"\n")
    with pytest.raises(ValueError):run(files)
    files=fixture(True);files.pop("compact-worker-10.jsonl")
    with pytest.raises(ValueError):run(files)

def test_actual_controller_and_auditor_cli_import():
    import subprocess
    for file in("r36_step_durability_controller.py","r36_step_durability_audit.py"):
        p=subprocess.run([sys.executable,"-B",str(W/"host_audits"/file),"--help"],
            cwd=W,capture_output=True,text=True)
        assert p.returncode==0,p.stderr

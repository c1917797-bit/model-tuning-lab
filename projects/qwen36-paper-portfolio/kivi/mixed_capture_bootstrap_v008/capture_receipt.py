"""Metadata-only capture closure. No tensor reads/oracles/controller/deletion.
This permits only a following capture stage, never numerical/model/perf admission.
"""
import hashlib
from pathlib import Path
CLIENT_SHA="3d570bd09afce0b4218e13d4f4ea788fcb9f1f98adce5deda7a62984ce7f6796"
OBSERVER_SHA="cd957ae3b6e2303a0890e00dd3be178e473a1488636d4cb141f15c6649d5189b"
POINTS={"mixed-intake","k128-before","k128-after","reuse-first-decode","long-tail"}
CAPS={"holder0":256,"holder1":1024,"holder2":2,"replacement":2}
def need(v,m):
    if not v:raise ValueError(m)
def indices(rank_stage_refs,*,stage,plan_ref,identities,document):
    need(type(stage) is int and stage in range(16) and len(rank_stage_refs)==4
         and set(identities)=={"0","1","2","3"},"one declared stage/all4 actual workers")
    rows=[];declared=None
    for rank,ref in enumerate(rank_stage_refs):
        row=document(ref)
        need(row["schema"]=="kivi.actual-mixed-numeric-stage-index/v1"
             and row["stage"]==stage and row["rank"]==rank and row["identity"]==identities[str(rank)]
             and row["plan_ref"]==plan_ref and row["observer_source_sha256"]==OBSERVER_SHA
             and set(row["points"])==POINTS and set(row["declared"])==set(CAPS)
             and all(row[k] is False for k in ("model_ready","performance_ready","run_authority")),
             "original complete rank capture index; not independent verdict")
        need(len(set(row["declared"].values()))==4,"four actual distinct owner IDs")
        if declared is None:declared=row["declared"]
        need(row["declared"]==declared,"all4 ranks same stage owners")
        owners=set(declared.values())
        need(all(set(row[k])==owners for k in ("native_retirements","retirement_refs",
             "append_history_refs","original_prefill_refs")),"all four full capture and native retirement indices")
        for label,rid in declared.items():
            need(len(row["append_history_refs"][rid])==CAPS[label]-1
                 and row["native_retirements"][rid]["length"]==32768+CAPS[label]-1
                 and set(row["retirement_refs"][rid])=={"update_ref","retire_ref"},
                 "full owner extent captured before phase advancement")
        for p in row["points"].values():
            need(p.get("complete_point_ref") and p.get("packed_frame_ref"),"all five immutable complete point Refs")
        rows.append(row)
    return rows
def seal(client_report_ref,*,plan_ref,identities,document,publish):
    report=document(client_report_ref);stage=report["stage"]
    need(report["schema"]=="kivi.actual-mixed-stage-client/v1"
         and report["status"]=="RAW_STAGE_PENDING_INDEPENDENT_CONSUMPTION"
         and report["primary"] is None and report["capture_plan_ref"]==plan_ref,
         "actual HTTP and native stage capture finished without primary failure")
    need(set(report["responses"])==set(CAPS) and all(report["responses"][k]["ok"] is True
         and report["responses"][k]["completion_tokens"]==cap for k,cap in CAPS.items()),
         "all actual capped HTTP replies; no shorter stage")
    refs=report["rank_stage_refs"]
    rows=indices(refs,stage=stage,plan_ref=plan_ref,identities=identities,document=document)
    body=dict(schema="kivi.actual-mixed-capture-stage-sealed/v2",status="RAW_CAPTURE_SEALED_NUMERIC_PENDING",
        stage=stage,plan_ref=plan_ref,client_report_ref=client_report_ref,rank_stage_refs=refs,
        identities=identities,declared=rows[0]["declared"],
        capture_writer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        client_source_sha256=CLIENT_SHA,numeric_consumed=False,raw_payload_read=False,
        retained_all_raw=True,model_ready=False,performance_ready=False,run_authority=False,cleanup_authority=False)
    return publish("MATRIX-s%02d-CAPTURE-SEALED"%stage,body)
def validate(ref,*,stage,plan_ref,identities,document):
    body=document(ref)
    need(body["schema"]=="kivi.actual-mixed-capture-stage-sealed/v2"
         and body["status"]=="RAW_CAPTURE_SEALED_NUMERIC_PENDING" and body["stage"]==stage
         and body["plan_ref"]==plan_ref and body["identities"]==identities
         and body["capture_writer_sha256"]==hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
         and body["client_source_sha256"]==CLIENT_SHA and body["retained_all_raw"] is True
         and all(body[k] is False for k in ("numeric_consumed","raw_payload_read","model_ready",
             "performance_ready","run_authority","cleanup_authority")),
         "capture-only exact metadata producer; no CPU verdict allowed during NPU lease")
    rows=indices(body["rank_stage_refs"],stage=stage,plan_ref=plan_ref,identities=identities,document=document)
    need(body["declared"]==rows[0]["declared"],"same declared stage")
    return body

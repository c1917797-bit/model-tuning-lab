import copy,sys
from pathlib import Path
import pytest
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits.r35_io_evidence import audit_io_records

def fixture():
    workers={r:100+r for r in range(4)};events=[]
    for rank,pid in workers.items():
        base={"rank":rank,"pid":pid,"step":10,"manifest_sha256":"m"}
        for kind in("compact_gdn_body_composed","compact_c2_queries_completed"):
            events.append(dict(base,event=kind))
        events.append(dict(base,event="compact_model_rows_completed",request_ids=["api-native"]))
        events.append(dict(base,event="r35_evidence_io_budget_step",request_ids=["api-native"],
            original_emit_calls=3,original_written_events=3,original_written_bytes=1000,
            original_filtered_calls=0,original_fsync_calls=3,emit_interval_union_ns=300,
            emit_interval_sum_ns=300,fsync_interval_union_ns=150,fsync_interval_sum_ns=150,
            selected_envelope_ns=1000,observed_threads=1,original_fsync_preserved=True,
            extra_budget_row_intended=1,extra_budget_row_excluded_from_observation=True,
            groups={k:{"calls":1,"emit_ns":100,"fsync_ns":50}for k in
                ("compact_gdn_body_composed","compact_c2_queries_completed","compact_model_rows_completed")}))
    return events,workers

def test_valid_cohort_uses_maximum_rank_not_fourrank_sum():
    events,workers=fixture();out=audit_io_records(events,["api"],workers,"m")
    assert out["maximum_rank_emit_step_unions_ns"]==300
    assert out["maximum_rank_fsync_step_unions_ns"]==150
    assert out["whole_service_saving_inferred"]is False

def test_missing_actual_worker_budget_rejected():
    events,workers=fixture();events=events[:-1]
    with pytest.raises(ValueError):audit_io_records(events,["api"],workers,"m")

@pytest.mark.parametrize("change",["duplicate","fsync","source","raw_count","interval","ambiguous_id"])
def test_false_or_unreconciled_budget_rejected(change):
    events,workers=fixture();row=events[-1]
    if change=="duplicate":events.append(copy.deepcopy(row))
    elif change=="fsync":row["original_fsync_calls"]=2
    elif change=="source":row["manifest_sha256"]="foreign"
    elif change=="raw_count":events.pop(-2)
    elif change=="interval":row["fsync_interval_union_ns"]=301
    elif change=="ambiguous_id":
        for e in events:
            if "request_ids"in e:e["request_ids"].append("api-second")
    with pytest.raises(ValueError):audit_io_records(events,["api"],workers,"m")

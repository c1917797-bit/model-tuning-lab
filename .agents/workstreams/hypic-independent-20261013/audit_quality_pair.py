"""Descriptive full paired quality, no invented lossless acceptance threshold."""
from audit_full_quality_cohort import audit_full_quality_cohort
def audit_quality_pair(rows,baseline_unit,baseline_journal,hypic_unit,hypic_journal,*,score,batch_samples=8):
    baseline=audit_full_quality_cohort(rows,baseline_unit,baseline_journal,score=score,batch_samples=batch_samples)
    hypic=audit_full_quality_cohort(rows,hypic_unit,hypic_journal,score=score,batch_samples=batch_samples)
    b={(x["repetition"],x["index"]):x for x in baseline_unit["results"]}
    h={(x["repetition"],x["index"]):x for x in hypic_unit["results"]}
    rounds=[];changes=[]
    for repetition in (1,2,3):
        wins=losses=ties=bc=hc=0
        for index in range(127):
            key=(repetition,index);before=b[key];after=h[key]
            delta=int(after["correct"])-int(before["correct"])
            bc+=before["correct"];hc+=after["correct"]
            wins+=delta>0;losses+=delta<0;ties+=delta==0
            if delta:changes.append({"repetition":repetition,"index":index,"sample_id":rows[index]["sample_id"],
                "baseline_correct":before["correct"],"hypic_correct":after["correct"],
                "baseline_request_id":before["request_id"],"hypic_request_id":after["request_id"]})
        rounds.append({"repetition":repetition,"requests":127,"baseline_correct":bc,"hypic_correct":hc,
            "wins":wins,"losses":losses,"ties":ties,"delta_pp":100*(hc-bc)/127})
    majorities=[]
    for index,row in enumerate(rows):
        bc=sum(b[(r,index)]["correct"] for r in (1,2,3));hc=sum(h[(r,index)]["correct"]for r in (1,2,3))
        majorities.append({"index":index,"sample_id":row["sample_id"],"baseline_correct_rounds":bc,
            "hypic_correct_rounds":hc,"baseline_majority":bc>=2,"hypic_majority":hc>=2})
    return {"complete_paired_cohort":True,"requests_per_arm":381,"baseline":baseline,"hypic":hypic,
        "correct_delta":hypic["correct"]-baseline["correct"],
        "accuracy_delta_pp":100*(hypic["correct"]-baseline["correct"])/381,
        "truncation_delta":hypic["truncated"]-baseline["truncated"],"rounds":rounds,"changed_cases":changes,
        "sample_majorities":majorities,"quality_acceptance":"NOT_DECIDED",
        "scope":"descriptive exact127x3 paired rescoring only; no lossless requirement and no task-quality/deployment approval; same-source/protocol/mechanism/isolation/release require independent terminal audits"}

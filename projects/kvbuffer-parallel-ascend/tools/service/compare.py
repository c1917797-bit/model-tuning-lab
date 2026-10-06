"""Fail-closed one-pair screen validator; no final acceptance or quality claim."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
from contract import (COMMON, LAYERS, PROTOCOL, budget, digest, prompt_ids, require,
                      sha, summarize, write_new)

def audit_arm(root, arm, report):
    files=sorted(root.glob("service-rank*-pid*.jsonl"))
    require(len(files)==4,"exact four worker evidence files required, not just coordinator")
    all_rows={}
    expected=Counter(digest(prompt_ids(i)) for i in range(40))
    identities=None;stats=[]
    for path in files:
        rows=[json.loads(line) for line in path.read_text().splitlines()]
        require(rows and all(r.get("arm")==arm and r.get("event")!="failed" for r in rows),"worker failure")
        ranks={r["rank"] for r in rows}
        require(len(ranks)==1 and next(iter(ranks)) not in all_rows,"unique rank evidence")
        rank=next(iter(ranks));require(rank in range(4),"rank outside TP4")
        all_rows[rank]=rows
        proofs=[r for r in rows if r["event"]=="worker_proof"]
        require(len(proofs)==1,"exact real worker proof required")
        proof=proofs[0];bindings=proof["layers"]
        require(len(bindings)==48 and {r["layer"] for r in bindings}==set(LAYERS) and
                len({r["prefix"] for r in bindings})==48 and proof["physical_device"]==rank+4,
                "actual48 receiver/physical proof incomplete")
        budget(arm,proof["base_slots"])
        require(proof["budget"]==budget(arm) and proof["common"]==COMMON,"observed budget/common differs")
        require(proof["service_sources"]==json.loads((root/"ARM.json").read_text())["service_sources"],
                "actual worker scripts not bound to arm launch")
        started=[r for r in rows if r["event"]=="request_started"]
        require(len(started)==42 and len({r["request_id"] for r in started})==42,
                "exact two warmups plus40 benchmark runtime requests required")
        require(all(r["prompt_tokens"]==32768 for r in started),"native prompt length changed")
        actual=Counter(r["prompt_ids_sha256"] for r in started if r["max_tokens"]==1024)
        require(actual==expected and sum(r["max_tokens"]==1 for r in started)==2,
                "full40 exact prompt coverage absent")
        current=sorted((r["request_id"],r["prompt_ids_sha256"],r["max_tokens"]) for r in started)
        if identities is None:identities=current
        require(current==identities,"four ranks disagree on request/prompt identity")
        turns=[r for r in rows if r["event"]=="successful_turn"]
        require(turns and all(r["native_arguments_unmodified"] and r["storage_pointers_unchanged"] for r in turns) and
                sum(r["num_decodes"] for r in turns)==40*1023 and
                sum(r["num_prefills"] for r in turns)==42,"complete scheduled request lifecycle missing")
        require([r["turn"] for r in turns]==list(range(1,len(turns)+1)),"missing/repeated runner turns")
        pure=sum(r["num_decodes"] for r in turns if r["pure_decode"])
        mixed=sum(r["num_decodes"] for r in turns if r["mixed"])
        require(pure>0,"candidate has no pure-decode opportunity in real workload")
        if arm=="candidate":
            require(proof["candidate_successful_turn_has_frozen_seen48_gate"] is True and
                    all(r["candidate_layers_admitted"]==48 for r in turns) and
                    sum(r["native_prefill_resets"] for r in turns)==42,
                    "candidate real48 dispatch/reset evidence missing")
        stats.append(dict(rank=rank,turns=len(turns),pure_decode_tokens=pure,
                          mixed_native_decode_tokens=mixed,
                          observer_cpu_pre_seconds=sum(r["observer_pre_seconds"] for r in turns),
                          observer_cpu_post_before_emit_seconds=sum(r["observer_post_before_emit_seconds"] for r in turns),
                          event_io_seconds_lower_bound=turns[-1]["prior_evidence_io_seconds_total"],
                          event_io_bound_note="last successful-turn record write excluded; throughput includes all I/O"))
    require(set(all_rows)==set(range(4)),"TP4 ranks incomplete")
    if arm=="candidate":
        events=[json.loads(line) for line in (root/"candidate-evidence.jsonl").read_text().splitlines()]
        require(not any(r["event"]=="candidate_dispatch_failed" for r in events),"candidate dispatch failure")
        verified=[r for r in events if r["event"]=="worker_dispatch_verified"]
        require(len(verified)==4 and {r["rank"] for r in verified}==set(range(4)),"candidate native admission absent")
        pid_rank={r["pid"]:r["rank"] for r in verified}
        require(len(pid_rank)==4,"candidate worker PID proof not unique")
        materialized=[r for r in events if r["event"]=="aux_materialized_for_fallback"]
        require(all(r["pid"] in pid_rank for r in materialized),"unbound worker materialization PID")
        for rank,rows in all_rows.items():
            planned=sum(r.get("materialized_slots_per_layer",0) for r in rows)*48
            # Native multiprocessing need not populate RANK environment. The
            # explicit worker_dispatch_verified PID->TP rank proof owns the event.
            actual=sum(r["selected_slots"] for r in materialized if pid_rank[r["pid"]]==rank)
            require(planned==actual,"mixed fallback materialization count differs from successful turns")
    return dict(worker_stats=sorted(stats,key=lambda x:x["rank"]),
                evidence_files=[dict(path=str(p),sha256=sha(p)) for p in files])

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("dense-arm","candidate-arm","dense-client","candidate-client","output"):
        p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args();require(not a.output.exists(),"new pair report only")
    require(Path("/kvbuffer-results") in a.output.resolve().parents,"external pair report required")
    result=dict(schema="kvbp.same-eager-pair/v1",status="running",
                scope="P1-screen-not-final-three-round-common-optimized-or-task-accuracy-acceptance",
                quality_evaluated=False,graph_service_validated=False,rounds=1)
    try:
        arms={k:json.loads((root/"ARM.json").read_text()) for k,root in
              (("dense",a.dense_arm),("candidate",a.candidate_arm))}
        reports={k:json.loads((root/"REPORT.json").read_text()) for k,root in
                 (("dense",a.dense_client),("candidate",a.candidate_client))}
        for k in ("dense","candidate"):
            arm,report=arms[k],reports[k]
            require(arm["arm"]==k and arm["common"]==COMMON and arm["prepare_only"] is False,
                    "live matched common config required")
            require(report["arm"]==k and report["protocol"]==PROTOCOL and
                    report["status"]=="screen_complete" and
                    report["arm_sha256"]==sha((a.dense_arm if k=="dense" else a.candidate_arm)/"ARM.json"),
                    "exact client/arm binding required")
            require(report["metrics"]==summarize(report["responses"],"received-SSE-token-ID-deltas"),
                    "report metrics not reproducible")
        for key in ("common","image_id","model_config_sha256","native_gate_sha256",
                    "library_sha256","plugin_sha256","sources","completion_sources","common_runtime_env","service_sources","evidence_observer"):
            require(arms["dense"][key]==arms["candidate"][key],"unmatched configuration: "+key)
        dense,candidate=reports["dense"]["metrics"],reports["candidate"]["metrics"]
        result.update(status="matched_screen_complete",
                      dense=dense,candidate=candidate,
                      output_throughput_gain_pct=100*(candidate["output_tokens_per_second"]/dense["output_tokens_per_second"]-1),
                      ttft_reduction_pct=100*(1-candidate["mean_ttft_seconds"]/dense["mean_ttft_seconds"]),
                      tpot_reduction_pct=100*(1-candidate["mean_tpot_seconds"]/dense["mean_tpot_seconds"]),
                      dense_evidence=audit_arm(a.dense_arm,"dense",reports["dense"]),
                      candidate_evidence=audit_arm(a.candidate_arm,"candidate",reports["candidate"]),
                      not_validated=["graph-service","matched-common-optimized-dense-final-three-round",
                                     "LongBench-v2-max2048-normal-EOS","GSM8K-max2048-normal-EOS"])
    except BaseException as error:
        result.update(status="failed",error=repr(error));raise
    finally:write_new(a.output,result)
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":main()

"""One predeclared mixed stage using existing HTTP transport and original Refs.
No service/controller creation, weight reload, CPU consumer, cleanup or admission.
The MAIN-owned host invokes this16 times while keeping its one server alive.
"""
import hashlib,json,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
TRANSPORT_SHA="ba53f2774a5b43c257c4a6b9db9e56c37ebc44619d8ee55c0d599cb15b89580e"
OBSERVER_SHA="cd957ae3b6e2303a0890e00dd3be178e473a1488636d4cb141f15c6649d5189b"
LIFE_SHA="efd5c30941b978dad26f9ec2aa7b5e7eb66b308edef502712704bc19dc7cd867"
CAPS={"holder0":256,"holder1":1024,"holder2":2,"replacement":2}
def need(v,m):
    if not v:raise ValueError(m)
def paths(root,identities,stage,label):
    need(type(stage) is int and stage in range(16) and set(identities)=={"0","1","2","3"},"all4 actual namespace identities")
    # Exact observed adapter.Collector.publish filename formula (984a5c8).
    return [Path(root)/("r%d-p%d-s%d-MATRIX-s%02d-r%d-%s.json"%(r,identities[str(r)]["pid"],
        identities[str(r)]["start_ticks"],stage,r,label)) for r in range(4)]
def wait_original(expected_paths,*,read,make_ref,deadline,futures):
    while True:
        need(time.monotonic()<deadline,"existing caller deadline, no retry/extension")
        for future in futures:
            if future.done():need(future.result()["ok"] is True,"actual HTTP failure remains failed")
        if all(p.is_file() for p in expected_paths):
            refs=[make_ref(p) for p in expected_paths]
            return refs,[read(ref) for ref in refs]
        time.sleep(.05)
def collect(stage,capture_plan_ref,*,life,transport,root,diagnostic_root,identities,port,deadline):
    life.source_pin(life.raw,LIFE_SHA);life.source_pin(transport.request,TRANSPORT_SHA)
    need(type(port) is int and 1024<port<65536 and type(deadline) in (int,float)
         and deadline>time.monotonic(),"existing loopback server and original bounded host deadline")
    root=Path(root);diagnostic_root=Path(diagnostic_root)
    need(all(p.is_absolute() and p.resolve()==p and p.is_dir() and not p.is_symlink()
         and Path("/cache/cch") in p.parents for p in (root,diagnostic_root)),"existing exact owned task roots")
    capture=life.raw(capture_plan_ref);plan=life.raw(capture["ingress_plan_ref"]);spec=capture["stages"][stage]
    need(capture["schema"]=="kivi.actual-mixed-staged-input/v1" and capture["same_lease_required"] is True
         and len(capture["stages"])==16 and len(plan["rows"])==64 and spec["stage"]==stage,
         "whole immutable diagnostic owner plan, not matched throughput")
    chosen={role:next(row for row in plan["rows"] if row["declared_passed_id"]==rid)
            for role,rid in spec["declared"].items()}
    need(set(chosen)==set(CAPS) and all(row["max_tokens"]==CAPS[role] and row["ignore_eos"] is True
         for role,row in chosen.items()),"exact preregistered caps; no shortened replacement")
    observed=[];responses={};final_refs=None;primary=None
    def wait(label,owner=None):
        refs,rows=wait_original(paths(diagnostic_root,identities,stage,label),read=life.raw,make_ref=transport.ref,
            deadline=deadline,futures=list(responses.values()))
        for rank,row in enumerate(rows):
            need(row["stage"]==stage and row["rank"]==rank and row["identity"]==identities[str(rank)]
                 and row["plan_ref"]==capture_plan_ref and row["observer_source_sha256"]==OBSERVER_SHA,
                 "actual complete all4 original stage publication")
            if label!="STAGE-FINAL":
                need(row["schema"]=="kivi.actual-mixed-stage-progress/v1" and row["label"]==label
                     and row["request_id"]==spec["declared"][owner],"source-bound actual request transition")
                if label.endswith("DECODE-READY"):need(len(row["all16_actual_FA_output_returns"])==16,"all16 actual outputs returned")
            else:need(row["schema"]=="kivi.actual-mixed-numeric-stage-index/v1","actual four-owner native retirement index")
        observed.append(dict(label=label,refs=refs));return refs
    try:
        with ThreadPoolExecutor(max_workers=4) as pool:
            responses["holder0"]=pool.submit(transport.request,root,port,chosen["holder0"])
            wait("HOLDER0-DECODE-READY","holder0")
            responses["holder1"]=pool.submit(transport.request,root,port,chosen["holder1"])
            wait("HOLDER1-DECODE-READY","holder1")
            responses["holder2"]=pool.submit(transport.request,root,port,chosen["holder2"])
            wait("HOLDER0-RETIRED","holder0")
            responses["replacement"]=pool.submit(transport.request,root,port,chosen["replacement"])
            final_refs=wait("STAGE-FINAL")
            actual={role:future.result() for role,future in responses.items()}
        need(all(row["ok"] and row["completion_tokens"]==CAPS[role] for role,row in actual.items()),
             "all actual HTTP tokens, not scalar completion")
        for role,row in actual.items():transport.replay(row,chosen[role],root)
    except BaseException as error:
        primary=repr(error);raise
    finally:
        report=dict(schema="kivi.actual-mixed-stage-client/v1",stage=stage,capture_plan_ref=capture_plan_ref,
            observed=observed,rank_stage_refs=final_refs,primary=primary,
            responses={k:v.result() for k,v in responses.items() if v.done() and not v.cancelled() and v.exception() is None},
            status="RAW_STAGE_PENDING_INDEPENDENT_CONSUMPTION" if primary is None else "FAILED",
            model_ready=False,performance_ready=False,run_authority=False)
        transport.publish(root/("STAGE-%02d-HTTP-REPORT.json"%stage),report)
    return report


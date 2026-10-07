"""Missing-case union for ORIGINAL MA070e timeout. Stdlib; no fake shard PASS."""
import argparse, hashlib, importlib.util, json, math, sys
from pathlib import Path
REPO=Path("/opt/host/vnf/austinov/model-tuning-lab")
OLD=REPO/"projects/damp-ascend/tools/selected_row_dispatch_v1"
OLD_PIN="61cec4646d5721c7c793aa85e842c507edc34c0d8566abc72bf5f789c476844d"
OP="exec-000000000000070e"
PEER="lgw_a6109c51076a4a2c9d2674ca5a8704a0"
GROUPS={4:(1,8,9,16),5:(2,7,10,15),6:(3,6,11,14),7:(4,5,12,13)}
KINDS=("adjacent","guard_gaps")
VARS=("SR1_perHv_permutations","power2_perHv_permutations")
OWN=("validator.py","run.py","test_completion.py","READY.md")
HERE=Path(__file__).resolve().parent
def need(ok,msg):
    if not ok:raise ValueError(msg)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def unique(pairs):
    result={}
    for k,v in pairs:
        need(k not in result,"duplicate JSON field");result[k]=v
    return result
def decode(raw):
    return json.loads(raw,object_pairs_hook=unique,
        parse_constant=lambda x:(_ for _ in ()).throw(ValueError("nonfinite JSON "+x)))
def bytes_ref(ref):
    need(type(ref) is dict and set(ref)=={"path","sha256"},"exact Ref")
    p=Path(ref["path"]);need(p.is_absolute() and p.is_file(),"absolute actual evidence file")
    raw=p.read_bytes();need(digest(raw)==ref["sha256"],"actual Ref hash: "+str(p))
    return raw
def json_ref(ref):return decode(bytes_ref(ref))
def context():
    raw=(OLD/"PACKET.json").read_bytes();need(digest(raw)==OLD_PIN,"frozen selected packet")
    packet=decode(raw)
    for n,h in packet["sources"].items():need(digest((OLD/n).read_bytes())==h,"frozen own source "+n)
    sys.path.insert(0,str(OLD))
    spec=importlib.util.spec_from_file_location("_completion_frozen_selected",OLD/"selected_contract.py")
    c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
    c.packet(OLD_PIN)
    need(c.BATCH_GROUPS==GROUPS,"original balanced groups")
    return c
def source_manifest(ref,c):
    m=json_ref(ref)
    need(m.get("schema")=="damp-selected-row-completion-source/v1" and
        m.get("default_enabled") is False and m.get("npu_executed") is False and
        m.get("deadline_utc")=="2026-10-07T08:48:03Z" and
        m.get("frozen_sources")==c.source_snapshot() and
        set(m.get("sources",{}))==set(OWN),"new4+old52 exact closure/deadline")
    for n,h in m["sources"].items():need(digest((HERE/n).read_bytes())==h,"NEW source drift "+n)
    return {**c.source_snapshot(),**{str(HERE/n):h for n,h in m["sources"].items()},
        ref["path"]:ref["sha256"]}
def expected(card=None):
    ts=GROUPS[card] if card is not None else range(1,17)
    return {(t,k,v) for t in ts for k in KINDS for v in VARS}
def key(case):return case.get("batch"),case.get("shared_arena_layout"),case.get("variant")
def true_guards(g):
    return type(g) is dict and bool(g) and all(v is True for v in g.values())
def valid_case(c,metadata):
    t=c.get("batch");need(type(t) is int and 1<=t<=16 and key(c) in expected(),"true case key")
    need(c.get("status")=="passed" and c.get("stage")=="graph_restricted" and
        c.get("graph_numerical_status")=="passed" and c.get("warmups")==3 and
        c.get("identical_repeats")==8 and c.get("changed_replays")==160 and
        len(c.get("steps",[]))==160,"whole160/8/warm3; no partial resumption")
    for i,s in enumerate(c["steps"]):
        need(s.get("step")==i+1 and s.get("passed") is True and
            len(s.get("indices",[]))==t and len(set(s["indices"]))==t and
            all(type(x) is int and 0<=x<t+3 for x in s["indices"]) and
            true_guards(s.get("guards")) and len(s.get("paths",[]))==3,"all true-T feedback guards")
        for p in s["paths"]:
            need(p.get("passed") is True and true_guards(p.get("guards")),"all graph/eager paths")
            metrics=p.get("metrics",{})
            need(set(metrics)=={"selected_state","complete_state","output"},"whole state/output metrics")
            for n,m in metrics.items():
                z=m.get("max_head_relative_l2")
                need(m.get("finite") is True and type(z) in (float,int) and math.isfinite(z) and
                    0<=z<=({"output":.00303}.get(n,1e-5)),"unchanged finite/error gates")
    negatives=c.get("invalid_dynamic_cases",[])
    need(len(negatives)==len(metadata(t,t+3)) and
        {n.get("name") for n in negatives}=={n[0] for n in metadata(t,t+3)} and
        all(n.get("passed") is True and len(n.get("paths",[]))==3 and
            all(p.get("passed") is True and true_guards(p.get("guards")) for p in n["paths"])
            for n in negatives),"all dynamic negatives+no-write")
    overlaps=c.get("actual_overlap_rejections",[])
    need(len(overlaps)==15 and len({x.get("label") for x in overlaps})==15 and
        all(true_guards(x.get("guards")) and "DATA byte intervals overlap" in x.get("rejection","")
            for x in overlaps),"all15 real overlaps/no-write")
    audits=[c.get("shared_arena_audit",{}),c.get("shared_arena_audit_after_negatives",{})]
    need(all(a.get("layout")==key(c)[1] and len(a.get("arenas",[]))==count and
        type(a.get("guarded_observations")) is int and a["guarded_observations"]>480
        for a,count in zip(audits,(4,5))),"full raw/conv/gap guard arenas before/after negatives")
    need(c.get("actual_token_metadata",{}).get("tokens")==t,"actual metadata width")
    return key(c)
def checkpoint(report,journal_raw,path):
    """Only reuse actual whole checkpoint. Extra/truncated tail stays original evidence."""
    j=report.get("evidence_journal",{});n=j.get("events")
    need(j.get("path")==path and type(n) is int and n>0,"actual checkpoint journal Ref")
    lines=journal_raw.splitlines(keepends=True)
    need(len(lines)>=n and all(x.endswith(b"\n") for x in lines[:n]),"complete checkpoint event prefix")
    prefix=b"".join(lines[:n]);need(digest(prefix)==j.get("sha256"),"checkpoint prefix bytes")
    result={"checks":[],"cases":[]}
    for seq,line in enumerate(lines[:n]):
        e=decode(line);need(e.get("schema")=="damp-selected-row-journal/v1" and
            e.get("seq")==seq and e.get("checks_start")==len(result["checks"]),"journal exact order")
        for k in e["header_remove"]:result.pop(k,None)
        result.update(e["header_set"]);result["checks"].extend(e["checks_append"])
        for row in e["cases"]:
            i=row["index"];need(type(i) is int and 0<=i<=len(result["cases"]),"case append index")
            if i==len(result["cases"]):result["cases"].append({"steps":[]})
            steps=result["cases"][i]["steps"]
            need(row["steps_start"]==len(steps),"step append offset")
            result["cases"][i]={**row["meta"],"steps":steps+row["steps_append"]}
    result["evidence_journal"]={"path":path,"sha256":digest(prefix),"events":n,
        "schema":"damp-selected-row-journal/v1"}
    need(result==report,"lossless ORIGINAL checkpoint, not synthesized PASS")
    return {"complete_prefix_bytes":len(prefix),"extra_original_tail_bytes":len(journal_raw)-len(prefix),
        "extra_original_tail_sha256":digest(journal_raw[len(prefix):])}
def terminal(ref,op,args,*,success):
    d=json_ref(ref);d=d.get("structuredContent",d);o=d.get("operation",{})
    result=o.get("result",{});r=result.get("record",{})
    need(d.get("schema")=="agentweb.operation/v1" and d.get("kind")=="exec" and
        d.get("operationId")==op and d.get("terminal") is True and d.get("status")=="completed" and
        o.get("routeDecision")=="peer_direct" and o.get("targetPeerId")==PEER and
        result.get("found") is True and result.get("ok") is True and result.get("state")=="completed" and
        r.get("id")==op and r.get("state")=="completed" and result.get("lane")=="job" and
        r.get("lane")=="job" and r.get("cancelled") is False and r.get("timedOut") is False and
        r.get("command")=="/usr/bin/python3" and r.get("cwd")==str(REPO) and
        r.get("args")==args and type(r.get("stdout")) is str and type(r.get("stderr")) is str,
        "MAIN original direct raw terminal/argv, never fabricated outer PASS")
    need(type(r.get("exitCode")) is int and
        ((success and r["exitCode"]==0 and r.get("error") is None and
          d.get("error") is None and d.get("succeeded") is True) or
         (not success and r["exitCode"]!=0 and r.get("error")=="exit code" and
          d.get("error")=="exit code" and d.get("succeeded") is False)),"real terminal outcome")
    return r
def original(authority_ref,c):
    a=json_ref(authority_ref)
    need(a.get("schema")=="damp-selected-row-completion-original/v1","MAIN original completion authority")
    args=a["original_args"]
    need(args[:2]==["-B",str(OLD/"controller.py")] and args.count("--packet-sha256")==1 and
        args[args.index("--packet-sha256")+1]==OLD_PIN,"original selected dispatch argv")
    terminal(a["terminal"],OP,args,success=False)
    failure=json_ref(a["failure"])
    need(failure.get("original_error")==
        "ValueError('single bounded phase timeout; no automatic retry')" and
        failure.get("automatic_retry") is False,"ONLY actual bounded timeout, no numeric retry")
    after=json_ref(a["source_after"])
    need(after.get("files")==c.source_snapshot() and type(after.get("observed_at_unix_ns")) is int,
        "MAIN actual source-after52 read audit; unavailable remains blocked")
    admission=json_ref(a["admission"]);plan=json_ref(a["execution_plan"]);stops=json_ref(a["stop_retain"])
    entries=plan.get("shards",[]);by_card={e.get("physical_card"):e for e in entries}
    need(len(entries)==4 and set(by_card)==set(GROUPS) and
        len(admission.get("cards",{}))==4 and len(stops)==4,"original four owned jobs")
    by_id={x.get("id"):x for x in stops};need(len(by_id)==4,"four stop IDs")
    release=json_ref(a["post_release"])
    host=c.load("_completion_frozen_host",c.PROJECT/"tools/allT_dispatch_controller_v1/controller.py")
    rows=host.parse_processes(release["snapshot"]["npu_smi"])
    need(host.protected_fingerprint(rows)==release["protected"] and
        all(not rows[x] for x in range(4,8)),"original release/protected fingerprint")
    sys.path.insert(0,str(c.BASE))
    metadata=c.load("_completion_meta",c.BASE/"metadata_contract.py").metadata_cases
    completed={};descriptors={}
    need(set(a["reports"])==set(a["journals"])==set(map(str,GROUPS)),"all four raw report/journal Refs")
    for card,group in GROUPS.items():
        r=json_ref(a["reports"][str(card)]);jraw=bytes_ref(a["journals"][str(card)])
        checkpoint(r,jraw,a["journals"][str(card)]["path"])
        need(r.get("schema")=="damp_all_batch_restricted_shared_graph_gate_v1" and
            r.get("execution_packet")=="damp-selected-row-dispatch-v1" and
            r.get("physical_card")==card and r.get("batches")==list(group) and
            r.get("npu_executed") is True and r.get("limits")=={"state":1e-5,"output":.00303} and
            r.get("namespace")==c.NAMESPACE and
            r.get("bindings",{}).get("selected_row_packet")=={"path":str(OLD/"PACKET.json"),"sha256":OLD_PIN} and
            all(r.get("bindings",{}).get(k)==v for k,v in {
                "source_manifest_sha256":"a115f00eb371476ad96c440fca53db2c383e2f5f11c9b62e80214543754c1958",
                "runtime_manifest_sha256":"1755f39069b18b10aaabfb7ff341e6879ba741af3cbb72703b64ffe1070f38d5",
                "library_sha256":"a802d2584f6342acd198406a94c4a4cb3dd0e9cd6cc360569e58f3f117ac0ade",
                "build_receipt_sha256":"a9c8a6824f3f0948d4395eabcc731a0b4e0da6a7f94d6053d3159cf008e23d36"}.items()) and
            r.get("versions",{}).get("actual_runtime_soc")=="Ascend910B4" and
            r.get("general_sr_supported") is False and
            r.get("serving_ready") is False and r.get("sources_before")==c.source_snapshot() and
            not any(x.get("passed") is False for x in r.get("checks",[])),"source-bound partial scope/checks")
        need(after["observed_at_unix_ns"]>=r["created_ns"],"source-after nonfuture ordering")
        c.OLD.validate_native_anchors(r);c.validate_equivalence(r)
        cid=admission["cards"][str(card)]["container_id"];stop=by_id.get(cid,{})
        need(by_card[card]["batches"]==list(group) and
            by_card[card]["container_name"]==admission["cards"][str(card)]["container_name"]==
                stop.get("name") and stop.get("status") in ("created","exited") and
            stop.get("deleted") is False,"exact original stopped/retained owner")
        descriptors[card]=r
        for case in r.get("cases",[]):
            if (case.get("status")!="passed" or case.get("graph_numerical_status")!="passed" or
                len(case.get("actual_overlap_rejections",[]))!=15 or
                not case.get("shared_arena_audit_after_negatives")):continue
            k=valid_case(case,metadata);need(k in expected(card) and k not in completed,"unique original case")
            completed[k]={"origin":"original_timeout","report":a["reports"][str(card)],"case":case}
    return {"authority_ref":authority_ref,"authority":a,"reports":descriptors,"completed":completed,
        "missing":sorted(expected()-set(completed)),"metadata":metadata}
def selected_keys(keys,base,card):
    need(type(keys) is list and bool(keys),"explicit nonempty true case list")
    chosen=[tuple(x) for x in keys]
    need(len(set(chosen))==len(chosen) and all(k in expected(card) and k in base["missing"]
        for k in chosen),"ONLY ORIGINAL genuinely unfinished case keys; never rerun valid cases")
    return chosen
def union(base,new_descriptors,c,source_ref):
    """Original failed operation remains failed. NEW status is a coverage union only."""
    frozen=source_manifest(source_ref,c);seen=dict(base["completed"]);orig_ref=base["authority_ref"]
    for descriptor in new_descriptors:
        r=json_ref(descriptor["report"]);record=terminal(descriptor["terminal"],
            descriptor["operation_id"],descriptor["original_args"],success=True)
        markers=[line for line in record["stdout"].splitlines() if line.startswith("MAIN_DAMP_MISSING_CASE_ARM ")]
        need(len(markers)==1 and decode(markers[0].split(" ",1)[1])=={
            "reportRef":descriptor["report"],"journalRef":descriptor["journal"],
            "childExecutionRef":descriptor["child_execution"]},"actual MAIN sole outer marker must bind original child Refs")
        child=json_ref(descriptor["child_execution"])
        need(child.get("exit_code")==0 and child.get("automatic_retry") is False,
            "actual new child, not only outer exit0")
        streams={stem:bytes_ref({"path":child[stem],"sha256":child[stem+"_sha256"]})
            for stem in ("stdout","stderr")}
        results=[]
        for line in streams["stdout"].decode("utf-8",errors="replace").splitlines():
            try:value=decode(line)
            except (ValueError,TypeError):continue
            if type(value) is dict and value.get("schema")=="damp-selected-row-completion-result/v1":results.append(value)
        need(len(results)==1 and results[0].get("status")=="missing_cases_pass" and
            results[0].get("report")==descriptor["report"]["path"] and results[0].get("cases")==len(r["cases"]) and
            results[0].get("npu_executed") is True,"sole actual numeric child marker")
        argv=child["argv"];runner=str(HERE/"run.py")
        proof=r.get("device_proof",{}).get("content",{});cid=proof.get("container_id")
        need(argv[:2] in (["docker","exec"],["/usr/bin/docker","exec"]) and type(cid) is str and
            argv.count(cid)==1 and proof.get("physical_npu_ids")==[r["physical_card"]] and
            proof.get("logical_to_physical")=={"0":r["physical_card"]} and proof.get("privileged") is False and
            proof.get("exclusive_resource_check_passed") is True and argv.count(runner)==1 and
            argv.index(cid)<argv.index(runner) and argv[argv.index(runner):]==r["argv"],
            "actual docker child runner argv; host/image identities not conflated")
        need(r.get("schema")=="damp-selected-row-missing-cases/v1" and
            r.get("status")=="missing_cases_pass" and r.get("original_authority")==orig_ref and
            r.get("completion_source_manifest")==source_ref and
            r.get("sources_before")==frozen==r.get("sources_after") and
            r.get("npu_executed") is True and r.get("graph_supported") is True and
            r.get("shared_arena_supported") is True and r.get("general_sr_supported") is False and
            r.get("serving_ready") is False and r.get("limits")=={"state":1e-5,"output":.00303} and
            r.get("namespace")==c.NAMESPACE and not r.get("secondary_errors") and
            not any(x.get("passed") is False for x in r.get("checks",[])),"complete fresh NEW scope/source/checks")
        report_map=r.get("loaded_libraries_final",{})
        need(report_map.get(r["bindings"]["library"])==r["bindings"]["library_sha256"],
            "actual final loaded candidate map")
        chosen=selected_keys(r["selected_case_keys"],base,r["physical_card"])
        need(len(r["cases"])==len(chosen) and {key(x) for x in r["cases"]}==set(chosen),"exact planned subset")
        checkpoint(r,bytes_ref(descriptor["journal"]),descriptor["journal"]["path"])
        for case in r["cases"]:
            k=valid_case(case,base["metadata"]);need(k not in seen,"duplicate cannot fill union")
            seen[k]={"origin":"new_missing_case","report":descriptor["report"],"case":case}
    need(set(seen)==expected(),"exact64 union; missing/partial never accepted")
    return {"schema":"damp-selected-row-coverage-union/v1","status":"restricted_union64_complete",
        "cases":64,"feedback_turns":10240,"selected_row_pairs":192,"native_split_anchors":24,
        "original_operation_status":"failed_bounded_timeout_preserved",
        "origins":[{"key":list(k),"origin":v["origin"],"report":v["report"]} for k,v in sorted(seen.items())],
        "general_sr_supported":False,"final192_supported":False,"serving_ready":False,
        "performance_claim":False,"task_accuracy_claim":False}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--plan",action="store_true")
    p.add_argument("--aggregate",action="store_true")
    for n in ("original-authority","completion-source-manifest"):
        p.add_argument("--"+n,type=Path,required=True);p.add_argument("--"+n+"-sha256",required=True)
    p.add_argument("--new-runs",type=Path);p.add_argument("--new-runs-sha256")
    a=p.parse_args();need(a.plan != a.aggregate,"explicit plan OR aggregate, default OFF")
    c=context();s={"path":str(a.completion_source_manifest),"sha256":a.completion_source_manifest_sha256}
    source_manifest(s,c)
    b=original({"path":str(a.original_authority),"sha256":a.original_authority_sha256},c)
    if a.aggregate:
        need(a.new_runs is not None and a.new_runs_sha256,"actual MAIN new Run descriptors required")
        result=union(b,json_ref({"path":str(a.new_runs),"sha256":a.new_runs_sha256}),c,s)
    else:result={"schema":"damp-selected-row-missing-plan/v1","original_operation_failed":True,
        "completed":len(b["completed"]),"missing":b["missing"],"by_physical_card":{
            str(card):[list(k) for k in b["missing"] if k in expected(card)] for card in GROUPS},
        "deadline_utc":"2026-10-07T08:48:03Z","npu_executed":False,"launchable":False}
    print(json.dumps(result,allow_nan=False,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())

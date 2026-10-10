"""Independent raw scalar lifecycle replay for the frozen mixed installer.
No imports of candidate Book, mixed adapter, producer, kernel, or tensor math.
This component NEVER grants model/performance/run authority.
"""
import hashlib
import inspect
import json
from pathlib import Path

INSTALLER_SHA="08162fb4582e449c66d99c3eb48ae483d9c83892ed5d8c8ca5b022665af6a8ee"
BINDINGS_SHA="55f4e7c514ad089571aedbadf74e257c8bd660832183f46b22c4571a728e8ba7"
ORACLE_SHA="f288191487869fe752fea8713742bff2e6245c30d9ed790243b8868520f0e333"
RUNNER_SHA="94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968"
LABELS=("warmup0","warmup1")+tuple("request%02d"%i for i in range(40))

def need(v,m):
    if not v: raise ValueError(m)

def canonical(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()

def source_pin(obj,sha):
    path=Path(inspect.getfile(inspect.unwrap(obj)))
    need(path.is_absolute() and path.resolve()==path and not path.is_symlink()
         and hashlib.sha256(path.read_bytes()).hexdigest()==sha,"exact independent source identity")

def raw(ref,cap=8*1024**2):
    need(type(ref) is dict and set(ref)=={"path","bytes","sha256"},"exact3 original Ref")
    path=Path(ref["path"])
    need(path.is_absolute() and path.resolve()==path and path.is_file() and not path.is_symlink()
         and type(ref["bytes"]) is int and 0<ref["bytes"]<=cap,"bounded ordinary original")
    before=path.stat(); data=path.read_bytes(); after=path.stat()
    need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==
         (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)
         and len(data)==ref["bytes"] and hashlib.sha256(data).hexdigest()==ref["sha256"],
         "stable complete original bytes/SHA")
    return json.loads(data)

def input_contract(plan_ref,bindings,oracle):
    source_pin(bindings.declaration,BINDINGS_SHA)
    source_pin(oracle.validate_assignment,ORACLE_SHA)
    plan=raw(plan_ref); expected=bindings.declaration(plan,oracle)
    need([r["client_label"] for r in plan["rows"]]==list(LABELS),"exact2 warmups then40 queued measured declarations")
    need(len(expected)==42,"all42 distinct declared engine IDs")
    result={}
    for i,row in enumerate(plan["rows"]):
        rid=row["declared_passed_id"]; n=1 if i<2 else 1024
        need(row["max_tokens"]==n and row["ignore_eos"] is True
             and len(expected[rid]["prompt"])==32768,"actual32768 fixed output input contract")
        index=i if i<2 else i-2
        original=[1000+j%257 for j in range(16384)]+[2000+(index*131+j*17)%4093 for j in range(16384)]
        need(expected[rid]["prompt"]==original,"whole original matched32768 prompt, not length-only input")
        result[rid]={"prompt":32768,"outputs":n,"label":LABELS[i]}
    return result

def _unique(values,why):
    need(type(values) is list and all(type(v) is str and v for v in values)
         and len(values)==len(set(values)),why)
    return set(values)

def consume_rank(bundle_ref,expected,plan_ref,ingress_verifier):
    bundle=raw(bundle_ref)
    need(bundle["schema"]=="kivi.actual-packed-qwen-journal/v1"
         and type(bundle["rank"]) is int and bundle["rank"] in range(4),"actual rank journal")
    rank=bundle["rank"]; ident=bundle["identity"]
    owner=raw(bundle["owner_ref"]); event=raw(bundle["event_ref"])
    layers={name for name,row in event["layers"].items() if row["kind"]=="FA"}
    need(event["rank"]==rank and event["identity"]==ident and len(event["layers"])==64 and len(layers)==16
         and owner["rank_bindings"][str(rank)]==ident,"actual all64/FA16 and owner PID/start/cgroup")
    need(owner["declared_ingress_plan_ref"]==plan_ref
         and owner["declared_passed_request_ids"]==list(expected)
         and owner["prompt_lengths"]=={r:32768 for r in expected},"same immutable whole input declaration")
    live={}; slot_epochs={}; ever=set(); ingressed=set(); retired=set(); awaiting={}
    stats={rid:{"prefill_tokens":0,"decode_tokens":0,"k_seals":[],"slot":None,"slot_epoch":None}
           for rid in expected}
    frame=None; frame_ref=None; returned=set(); epoch=0; frames=0; updates=0; outputs=0
    mixed=0; peak=0; reuse=0; final_empty=False; saw_update=False
    native_after=set(); batch_after=set(); schedule=hashlib.sha256(); mixed_refs=[]

    def commit():
        nonlocal frame,frame_ref,returned,frames
        if frame is None: return
        need(returned==layers,"all16 actual output returns before next native boundary")
        for rid,c,n in zip(frame["req_ids"],frame["computed_tokens"],frame["scheduled_counts"]):
            live[rid]["length"]=c+n
            s=stats[rid]
            if c<32768:s["prefill_tokens"]+=n
            else:
                s["decode_tokens"]+=n
                if (c+1)%128==0:s["k_seals"].append(c+1)
        frames+=1; frame=None;frame_ref=None;returned=set()

    for chunk_ref in bundle["journal_chunks"]:
        chunk=raw(chunk_ref)
        need(chunk["schema"]=="kivi.actual-packed-qwen-journal-chunk/v1" and chunk["rank"]==rank
             and chunk["identity"]==ident and type(chunk["events"]) is list and 0<len(chunk["events"])<=128,
             "whole bounded actual journal chunk")
        for ref in chunk["events"]:
            row=raw(ref)
            need(row["rank"]==rank and row["identity"]==ident,"same process on every original event")
            kind=row["schema"]
            if kind in ("kivi.actual-packed-qwen-update/v1","kivi.actual-packed-qwen-frame/v1"):commit()
            if kind=="kivi.actual-packed-qwen-update/v1":
                need(not awaiting and row["runner_source_sha256"]==RUNNER_SHA,"all releases before next update; exact runner")
                newcomers=ingress_verifier(row["new_ingress_refs"],owner,rank,ident,ingressed)
                before=_unique(row["requests_before"],"unique actual requests before")
                native_after=_unique(row["requests_after"],"unique actual requests after")
                batch_after=_unique(row["batch_after"],"unique actual batch after")
                finished=_unique(row["finished_req_ids"],"unique actual scheduler finished IDs")
                need(newcomers<=native_after and newcomers<=batch_after and not newcomers&before
                     and not newcomers&ingressed and newcomers<=set(expected),"actual new native owner transition")
                ingressed.update(newcomers)
                for rid in sorted(finished & set(expected)):
                    need(rid in live and rid not in native_after and rid not in batch_after and rid not in retired,
                         "real committed native retirement, not HTTP DONE")
                    state=live.pop(rid); goal=32768+expected[rid]["outputs"]-1
                    need(state["length"]==goal,"complete fixed outputs: prefill token1 plus output_count-1 decode")
                    awaiting[rid]=(state["slot"],state["epoch"]);retired.add(rid)
                need(set(live)<=native_after,"no silent removal/preemption")
                saw_update=True;updates+=1
                final_empty=(retired==set(expected) and not native_after and not batch_after)
                schedule.update(canonical(["update",sorted(newcomers),sorted(finished),sorted(native_after),sorted(batch_after)]))
            elif kind=="kivi.actual-packed-qwen-retire/v1":
                rid=row["request_id"]
                need(rid in awaiting and awaiting[rid]==(row["slot"],row["epoch"])
                     and row["actual_native_finished"] is True,"exact native finish followed by real compact release")
                del awaiting[rid]
                schedule.update(canonical(["release",rid,row["slot"],row["epoch"]]))
            elif kind=="kivi.actual-packed-qwen-frame/v1":
                need(saw_update and not awaiting and type(row["epoch"]) is int and row["epoch"]==epoch+1,
                     "one source prepare epoch after native update/release")
                ids=row["req_ids"]; ridset=_unique(ids,"unique actual ordered IDs")
                counts=row["scheduled_counts"]; computed=row["computed_tokens"]; starts=row["query_start_loc"]
                need(1<=len(ids)<=16 and ridset<=ingressed and ridset<=native_after
                     and ridset==batch_after and not ridset&retired,"whole actual native batch")
                need(len(counts)==len(computed)==len(ids) and len(starts)==len(ids)+1 and starts[0]==0
                     and all(type(v) is int and v>0 for v in counts)
                     and all(type(v) is int and v>=0 for v in computed+starts)
                     and type(row["total_tokens"]) is int and row["total_tokens"]<=40960
                     and starts[-1]==sum(counts)==row["total_tokens"]==len(row["positions"])
                     and row["req_id_to_index"]=={r:i for i,r in enumerate(ids)},"exact native whole query partition")
                kinds=[]
                for i,(rid,c,n) in enumerate(zip(ids,computed,counts)):
                    need(starts[i+1]-starts[i]==n and row["positions"][starts[i]:starts[i+1]]==list(range(c,c+n)),
                         "actual whole token positions; no offset/gap")
                    pre=c<32768; kinds.append("prefill" if pre else "decode")
                    need((pre and c+n<=32768) or (not pre and n==1 and c<32768+expected[rid]["outputs"]-1),
                         "one append, no prefill/decode crossing or extra sampled-token append")
                    if rid not in live:
                        need(c==0 and rid not in ever,"new real owner once, no prefix/recompute")
                        occupied={s["slot"] for s in live.values()}
                        available=[s for s in range(16) if s not in occupied]
                        need(available,"real compact16 capacity")
                        slot=available[0]; se=slot_epochs.get(slot,0)+1
                        if se>1:reuse+=1
                        slot_epochs[slot]=se;live[rid]={"slot":slot,"epoch":se,"length":0};ever.add(rid)
                        stats[rid].update(slot=slot,slot_epoch=se)
                    need(live[rid]["length"]==c,"independent monotone committed owner length")
                actual_kind=kinds[0] if len(set(kinds))==1 else "mixed"
                need(row["kind"]==actual_kind,"independent mixed classification, never candidate label")
                if actual_kind=="mixed":
                    mixed+=1
                    if len(mixed_refs)<16:mixed_refs.append(ref)
                peak=max(peak,len(live));epoch=row["epoch"];frame=row;frame_ref=ref
                saw_update=False
                schedule.update(canonical(["frame",epoch,ids,counts,computed,starts,row["positions"],actual_kind]))
            elif kind=="kivi.actual-packed-qwen-output/v1":
                need(frame is not None and row["frame_ref"]==frame_ref and row["epoch"]==epoch
                     and row["source_sha256"]==INSTALLER_SHA and row["layer"] in layers and row["layer"] not in returned,
                     "same-frame unique actual source-bound layer return")
                pre=[r for r,c in zip(frame["req_ids"],frame["computed_tokens"]) if c<32768]
                dec=[r for r,c in zip(frame["req_ids"],frame["computed_tokens"]) if c>=32768]
                calls=(1 if not dec else len(pre))
                need(row["kind"]==frame["kind"] and row["original_attention_calls"]==calls
                     and row["output_substituted"] is bool(dec)
                     and row["original_cache_update_suppressed"] is (bool(dec) and not pre)
                     and row["native_cache_write_request_ids"]==pre and row["packed_decode_request_ids"]==dec
                     and row["graph_checked"] is False,"exact native prefill/packed decode disjoint ownership")
                d=row["output"]
                need(d["shape"]==[frame["total_tokens"],1536] and d["logical_bytes"]==frame["total_tokens"]*1536*2
                     and d["dtype"] in ("torch.float16","torch.bfloat16") and d["device"].startswith("npu:"),
                     "whole actual output scalar geometry")
                returned.add(row["layer"]);outputs+=1
            else:raise ValueError("unknown original journal event")
    need(frame is None and not awaiting and not live and ingressed==ever==retired==set(expected)
         and final_empty,"complete all42 native final empty drain, not shutdown inference")
    need(mixed>0 and reuse>0,"actual mixed frame and distinct-owner same-slot epoch reuse required")
    for rid,s in stats.items():
        n=expected[rid]["outputs"]-1
        need(s["prefill_tokens"]==32768 and s["decode_tokens"]==n
             and s["k_seals"]==list(range(32896,32768+n+1,128)),"all original prefill/1023 append/K128 boundaries")
    final=raw(bundle["final_ref"])
    need(final["schema"]=="kivi.actual-packed-qwen-installer-final/v1" and final["rank"]==rank
         and final["identity"]==ident and final["source_sha256"]==INSTALLER_SHA
         and final["owner_ref"]==bundle["owner_ref"] and final["event_ref"]==bundle["event_ref"]
         and final["finished"]==sorted(retired) and final["graph_checked"] is False
         and final["allocation_replaced"] is False,"actual immutable installer final")
    return dict(rank=rank,identity=ident,bundle_ref=bundle_ref,owner_ref=bundle["owner_ref"],event_ref=bundle["event_ref"],
        frames=frames,updates=updates,output_rows=outputs,mixed_frames=mixed,mixed_frame_refs=mixed_refs,
        compact_peak_live=peak,slot_reuses=reuse,request_stats=stats,schedule_sha256=schedule.hexdigest(),
        finished=sorted(retired),native_final_empty=True,scalar_lifecycle_checked=True,
        tensor_numeric_checked=False,writer_bytes_checked=False,gdn_content_checked=False,
        model_ready=False,performance_ready=False,run_authority=False)

def consume(rank_bundle_refs,plan_ref,*,bindings,oracle):
    expected=input_contract(plan_ref,bindings,oracle)
    source_pin(bindings.Verifier,BINDINGS_SHA)
    need(type(rank_bundle_refs) is list and len(rank_bundle_refs)==4,"all4 complete original bundles")
    rows=[consume_rank(ref,expected,plan_ref,bindings.Verifier(oracle)) for ref in rank_bundle_refs]
    need([r["rank"] for r in rows]==list(range(4))
         and len({(r["identity"]["pid"],r["identity"]["start_ticks"]) for r in rows})==4,
         "ordered all4 distinct actual workers")
    need(all(r["schedule_sha256"]==rows[0]["schedule_sha256"] and r["request_stats"]==rows[0]["request_stats"]
             and r["frames"]==rows[0]["frames"] and r["output_rows"]==rows[0]["output_rows"] for r in rows),
         "all4 same entire request partition/retirement schedule, not equal counts alone")
    return dict(schema="kivi.actual-mixed1024-lifecycle-consumed/v1",ranks=rows,plan_ref=plan_ref,
        scope="independent original scalar journal only; no tensor comparison or whole-host authority",
        scalar_lifecycle_checked=True,model_ready=False,performance_ready=False,run_authority=False)


"""Bounded catalog capacity/rebuild diagnostic, never substitutes full127x3."""
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib
from independent_quality_workload import read_bound
from independent_quality_client import quality_payload,validate_response
from independent_quality_ruler import load_ruler
from independent_segment_catalog import SegmentCatalog

def catalog_canary_plan(rows,*,selection="capacity"):
    if selection not in ("capacity","first_batch_regression"):
        raise ValueError("explicit frozen diagnostic selection required")
    if len(rows)!=127 or [r["index"] for r in rows]!=list(range(127)) or len({r["sample_id"] for r in rows})!=127:
        raise ValueError("exact frozen127 sample inventory required")
    for r in rows:
        s=r["segment"]
        if type(s["start"])is not int or type(s["end"])is not int or not 0<=s["start"]<s["end"]<=len(r["token_ids"]) or s["end"]-s["start"]<=8:
            raise ValueError("valid frozen segment geometry required")
    if selection=="first_batch_regression":
        chosen=list(range(8));seen={r["segment"]["tokens_sha256"]for r in rows[:8]}
        if len(seen)!=8:raise ValueError("exact first failed batch requires eight distinct segments")
        ordered=rows[8:]
    else:
        first=max(rows,key=lambda r:(len(r["token_ids"]),-r["index"]))
        chosen=[first["index"]];seen={first["segment"]["tokens_sha256"]}
        ordered=sorted(rows,key=lambda r:(-(r["segment"]["end"]-r["segment"]["start"]),r["index"]))
    for r in ordered:
        if r["segment"]["tokens_sha256"]not in seen:
            chosen.append(r["index"]);seen.add(r["segment"]["tokens_sha256"])
        if len(chosen)==16:break
    if len(chosen)!=16:raise ValueError("sixteen distinct public segments required for capacity Canary")
    return {"initial_indexes":tuple(chosen),"batches":(tuple(chosen[:8]),tuple(chosen[8:])),
            "rebuild_candidates":tuple(chosen[:8]),"private_requests":17}

def run_catalog_canary(spec,*,send,guard,record,require_material_ready,choose_rebuild):
    required={"inputs","catalog","ruler_path","batch_samples","canary_indexes"}
    if not required<=set(spec) or set(spec)-required-{"canary_selection"} or spec["batch_samples"]!=8 or type(spec["batch_samples"])is not int:
        raise ValueError("explicit bounded catalog Canary contract required")
    inputs=read_bound(spec["inputs"]);catalog=read_bound(spec["catalog"])
    if inputs.get("schema")!="hypic-quality-inputs/v1" or catalog.get("schema")!="hypic-public-catalog/v1":
        raise ValueError("quality source schema mismatch")
    if inputs.get("generation")!={"max_tokens":1024,"temperature":0,"seed":0,"ignore_eos":False,"enable_thinking":False} or inputs.get("repetitions")!=3:
        raise ValueError("same naturalEOS/nonthinking1024 ruler required")
    rows=inputs["requests"];plan=catalog_canary_plan(rows,selection=spec.get("canary_selection","capacity"))
    if tuple(spec["canary_indexes"])!=plan["initial_indexes"] or any(type(x)is not int for x in spec["canary_indexes"]):
        raise ValueError("predeclared diagnostic sample selection drift")
    if any(len(r["token_ids"])+1024>40960 for r in rows):raise ValueError("model context capacity exceeded")
    stage=SegmentCatalog(catalog["public_segments"]);ruler=load_ruler(spec["ruler_path"])
    for r in rows:
        seg=r["segment"]
        if tuple(r["token_ids"][seg["start"]:seg["end"]])!=stage.tokens(seg["tokens_sha256"]):
            raise ValueError("catalog membership mismatch")
    results=[]
    for phase in range(3):
        guard()
        if phase<2:indexes=plan["batches"][phase]
        else:
            candidates=tuple({"index":i,"tokens_sha256":rows[i]["segment"]["tokens_sha256"]} for i in plan["rebuild_candidates"])
            selected=choose_rebuild(candidates)
            if type(selected)is not int or selected not in plan["rebuild_candidates"]:
                raise ValueError("rebuild must select an actually nonready first-batch material")
            indexes=(selected,)
            record({"event":"catalog-canary-rebuild-selected","scored":False,"index":selected,
                    "segment_sha256":rows[selected]["segment"]["tokens_sha256"]})
        record({"event":"catalog-canary-phase-start","scored":False,"phase":phase,"indexes":list(indexes)})
        for i in indexes:
            row=rows[i];digest=row["segment"]["tokens_sha256"];tokens=stage.tokens(digest)
            guard();response=send({"model":"qwen3.5","prompt":list(tokens),"temperature":0,"seed":0,
                                  "max_tokens":1,"ignore_eos":False,"stream":False});guard()
            record({"event":"catalog-canary-producer","scored":False,"phase":phase,"index":i,
                    "segment_sha256":digest,"response":response})
            if not response.get("id") or response.get("usage",{}).get("prompt_tokens")!=len(tokens):
                raise ValueError("producer transport identity/usage mismatch")
            require_material_ready(digest)
        # Prove entire batch remains available, not only the newest producer.
        for i in indexes:require_material_ready(rows[i]["segment"]["tokens_sha256"])
        def one(index):
            row=rows[index];item={"index":index,"sample_id":row["sample_id"],"phase":phase,
                "segment_sha256":row["segment"]["tokens_sha256"],"attempts":1,"retries":0}
            try:
                guard();response=send(quality_payload(row));guard()
                rid,text,finish,count=validate_response(response,row)
                prediction,correct=ruler["score_case"]("longbenchv2",text,row["reference"])
                item.update(ok=True,request_id=rid,response_text=text,response_sha256=hashlib.sha256(text.encode()).hexdigest(),
                    prediction=prediction,correct=bool(correct),finish_reason=finish,completion_tokens=count)
            except Exception as exc:item.update(ok=False,correct=False,error={"type":type(exc).__name__,"message":str(exc)})
            return item
        unit=[]
        with ThreadPoolExecutor(max_workers=len(indexes))as executor:
            for future in as_completed([executor.submit(one,i) for i in indexes]):
                item=future.result();record(dict(item,event="catalog-canary-response",scored=False));unit.append(item)
        results.extend(unit)
        if any(x["ok"]is not True for x in unit):raise ValueError("Canary failures retained; do not start full quality")
    if len(results)!=17:raise ValueError("complete17-response diagnostic required")
    return {"requests":17,"successful":17,"results":results,"full_quality":False,
            "initial_indexes":list(plan["initial_indexes"]),"scope":"bounded8+8+1 catalog capacity/rebuild Canary only; full127x3 perarm remains"}

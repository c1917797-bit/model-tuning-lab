"""Actual complete capture statistics -> named TP-local256 inputs. No teacher import."""
import json,math,sys
from pathlib import Path
from common import need,reference,bound,donor,CAPTURE,CAPTURE_BINDINGS,CLOCK,CUT,LAYERS,model_payload_identity
def features(value):
    need(type(value)is dict and set(value)==set(LAYERS),"all16 FA statistics")
    result={}
    for layer in LAYERS:
        x=value[layer];mn=x["min"];mx=x["max"]
        need(type(mn)is list and type(mx)is list and len(mn)==len(mx)==1024,"original global1024 range")
        need(all(type(a)in(int,float)and type(b)in(int,float)and math.isfinite(a)and math.isfinite(b)and a<=b for a,b in zip(mn,mx)),"finite actual extrema")
        result[layer]=dict(min=mn,max=mx,absmax=[max(abs(a),abs(b))for a,b in zip(mn,mx)],
          feature_rows=[[a,b]for a,b in zip(mn,mx)],feature_shape=[1024,2])
    return result
def split_rank(global_features,rank):
    need(type(rank)is int and 0<=rank<4,"actual TP rank")
    value=features(global_features);result={}
    for layer,x in value.items():
        mn=x["min"][rank*256:(rank+1)*256];mx=x["max"][rank*256:(rank+1)*256]
        result[layer]=dict(min=mn,max=mx,absmax=[max(abs(a),abs(b))for a,b in zip(mn,mx)],feature_rows=[[a,b]for a,b in zip(mn,mx)],feature_shape=[256,2])
    return result
def inputs(whole_ref):
    whole=bound(whole_ref)
    need(whole["schema"]=="skvq.current72h.preprojection.whole/v1"and whole["status"]=="FULL_CAPTURE_PREPROJECTION_ORIGINAL_CONSUMED_NOT_CALIBRATED"and
      whole["source_ref"]==CAPTURE and whole["whole_capture_consumed"]is True and whole["actual_capture_only"]is True and whole["native_ready"]is False and whole["model_ready"]is False,"actual014 full256 whole capture, not CPU-only/failed predecessor/source fixture")
    bound(CAPTURE);oldroot=Path(CAPTURE["path"]).parent
    c=donor("current_contract",str(oldroot/"current_contract.py"),CAPTURE_BINDINGS["current_contract.py"]["sha256"])
    if c.EXPECTED is None:c.configure(CAPTURE["sha256"])
    else:need(c.EXPECTED==CAPTURE["sha256"],"one unchanged capture source context")
    need(c.source()==CAPTURE,"complete installed actual capture source")
    loader=donor("_skvq_default_original",str(oldroot/"consume_whole.py"),CAPTURE_BINDINGS["consume_whole.py"]["sha256"])
    host=bound(whole["host_result_ref"],limit=64*2**20);root=Path(whole["host_result_ref"]["path"]).parent
    loader.original(bound(whole["original_ref"]),loader.host_argv(root,CAPTURE["sha256"]))
    need(host["status"]=="FULL_NATIVE_BASELINE_CAPTURE_CONSUMED_NOT_CALIBRATED"and host["source_lock"]==CAPTURE and host["primary"]is None and host["secondary"]==[],"actual current successful host original")
    payload_identity=model_payload_identity(host["actual_payload"])
    terminal=whole["terminal_consumer"]
    need(terminal["host_result"]==whole["host_result_ref"]and terminal["current_source_ref"]==CAPTURE and terminal["actual23"]is True and
      terminal["status"]=="FULL_BASELINE_RAW_CAPTURE_HOST_CONSUMED_NOT_AUTHOR_CALIBRATION","complete actual owned/CPU/raw prior consumer")
    consumed=bound(terminal["full_raw_consumer"]);baseline_ref=consumed["baseline_receipt_ref"];projection_ref=consumed["preprojection_consumed_ref"]
    baseline=bound(baseline_ref);projection=bound(projection_ref)
    bridge=donor("_skvq_default_capture_combine",str(oldroot/"consume_stage.py"),CAPTURE_BINDINGS["consume_stage.py"]["sha256"])
    bridge.combine(baseline,projection,CAPTURE,baseline_ref,projection_ref)
    need(host["result"]["consumer"]==terminal["full_raw_consumer"]and consumed["current_source_ref"]==CAPTURE,"same captured raw aggregate Ref")
    producer=bound(baseline["producer_ref"]);dtype=None;seen=set()
    need(producer["current_source_ref"]==CAPTURE and len(producer["rank_results"])==4,"actual same-source all4 capture")
    for rrref in producer["rank_results"]:
        rr=bound(rrref);rank=rr["rank"];need(type(rank)is int and 0<=rank<4 and len(rr["events"])==4096,"all4 complete rank events")
        for eref in rr["events"]:
            e=bound(eref);key=(rank,e["sample_id"],e["logical_layer"])
            need(key not in seen and e["rank"]==rank and e["logical_layer"]in LAYERS and type(e["sample_id"])is int and 0<=e["sample_id"]<256,"complete unique event metadata")
            seen.add(key);order=e["actual_same_input_post_rope_evidence"]["actual_qkv_legacy_order"]
            need(order["global_kv_channel_indices"]==list(range(rank*256,(rank+1)*256)),"true source-bound contiguous TP channels, no global truncation")
            actual=e["snapshots"]["v"]["dtype"];dtype=dtype or actual
            need(dtype==actual and dtype in("torch.float16","torch.bfloat16"),"same actual original A16 dtype")
    need(seen=={(r,s,l)for r in range(4)for s in range(256)for l in LAYERS},"all16384 original event identities")
    k=features(projection["preprojection_K_features"])
    v=features({l:baseline["full_global_kv_channel_minmax"][l]["v"]for l in LAYERS})
    return dict(capture_whole_ref=whole_ref,capture_producer_ref=baseline["producer_ref"],baseline_receipt_ref=baseline_ref,
      projection_consumed_ref=projection_ref,v_consumed_ref=baseline_ref,dtype=dtype,model_identity=payload_identity,host_result_ref=whole["host_result_ref"],
      sides={"k":k,"v":v},dataset="existing9 TRAIN MATH/APPS/ARC seed42 256x4096; not WikiText exact",
      adaptation="named Qwen16FA TP-local256 grouping from pre-QKnorm/RoPE K statistics and actual-original V; not author global1024 equivalence")

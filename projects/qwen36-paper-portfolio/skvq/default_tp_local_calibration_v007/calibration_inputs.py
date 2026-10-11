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
    from whole_precheck import envelope,precheck
    envelope(whole) # old failed/success-looking legacy schemas reject before child
    precheck(whole_ref) # clean actual isolated child replays new whole, no flat module swap
    host=bound(whole["original_capture_host_result_ref"],limit=64*2**20)
    need(host["source_lock"]==CAPTURE and host["status"]=="FAILED"and
      host["primary"]is not None and host["secondary"]==[],"preserved original014 failure, never upgraded")
    payload=bound(whole["after_release_payload_ref"])
    need(payload["payload"]==host["actual_payload"]and
      payload["original_host_before_ref"]==whole["original_capture_host_result_ref"]and
      payload["every_indexed_shard_whole_bytes_rehashed"]is True and
      payload["old_before_after_success_not_claimed"]is True,"old before plus actual derived after full payload")
    payload_identity=model_payload_identity(host["actual_payload"])
    consumed=bound(whole["full_raw_consumer_ref"])
    need(consumed["current_source_ref"]==CAPTURE and
      consumed["derived_identity_consumer_source_ref"]==whole["source_ref"]and
      consumed["original_failed_whole_ref"]==whole["original_failed_whole_ref"]and
      consumed["original_failed_whole_preserved"]is True and
      consumed["after_release_full_payload_ref"]==whole["after_release_payload_ref"],
      "original raw producer separated from actual new whole authority")
    baseline_ref=consumed["baseline_receipt_ref"];projection_ref=consumed["preprojection_consumed_ref"]
    baseline=bound(baseline_ref);projection=bound(projection_ref)
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
      projection_consumed_ref=projection_ref,v_consumed_ref=baseline_ref,dtype=dtype,model_identity=payload_identity,host_result_ref=whole["original_capture_host_result_ref"],
      sides={"k":k,"v":v},dataset="existing9 TRAIN MATH/APPS/ARC seed42 256x4096; not WikiText exact",
      adaptation="named Qwen16FA TP-local256 grouping from pre-QKnorm/RoPE K statistics and actual-original V; not author global1024 equivalence")

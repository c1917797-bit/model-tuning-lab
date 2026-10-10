"""Independent CPU-only preprojection K raw/minmax and V equality consumer.
Does not import projection_tap/candidate/Torch; source preparation UNEXECUTED.
"""
import argparse,json,os,sys
from pathlib import Path
BOUNDARY=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-calibration-boundary-v1-001")
sys.path.insert(0,str(BOUNDARY))
from contracts import require,reference,load_bound,publish,device_free,producer_and_receipt,v_events,inside_root,LAYERS
HERE=Path(__file__).resolve().parent
def source_lock():
    import current_contract as C
    return C.source()
def views(v):
    require(v["schema"]=="SKVQ_PREPROJECTION_LIVE_VIEWS_V1" and v["caller_is_actual_donor"] is True and
      v["boundary"]=="original qkv_proj return before fused QKnorm/RoPE" and v["q_gate_not_mixed_into_KV"] is True,
      "actual original projection boundary")
    d=v["live"];q=d["qkv"]
    require(q["shape"]==[4096,3584] and q["stride"]==[3584,1] and q["element_size"]==2 and
      q["numel"]==4096*3584 and q["dtype"] in ("torch.float16","torch.bfloat16") and
      q["device"].startswith("npu"),"actual contiguous packed projection")
    for name,offset in (("k",3072),("v",3328)):
        x=d[name]
        require(x["shape"]==[4096,256] and x["stride"]==[3584,1] and x["dtype"]==q["dtype"] and
          x["device"]==q["device"] and x["element_size"]==2 and x["numel"]==4096*256 and
          x["storage_data_ptr"]==q["storage_data_ptr"] and x["storage_nbytes"]==q["storage_nbytes"] and
          x["storage_offset_elements"]==q["storage_offset_elements"]+offset and
          x["data_ptr"]==q["data_ptr"]+2*offset,"real declared strided K/V slice storage/offset, not clone aliases")
    return q["dtype"]
def consume(root,baseline):
    source=source_lock();root=Path(root)
    producer,receipt,pref,bref=producer_and_receipt(root,baseline)
    import numpy as np
    bounds={};rawk=0;checked=0;seen=set()
    for (rank,sample,layer),eref,item in v_events(root,producer):
        event=load_bound(eref);proof=event["actual_same_input_post_rope_evidence"]
        require(proof["projection_capture_source_lock_ref"]==source,"same deployed projection source lock ref")
        pr=proof["actual_preprojection_ref"];inside_root(pr["path"],root);p=load_bound(pr)
        require(p["schema"]=="SKVQ_PREPROJECTION_EVENT_V1" and
          (p["rank"],p["sample_id"],p["logical_layer"])==(rank,sample,layer) and
          p["k_shape"]==[4096,256] and p["original_projection_return_unmodified"] is True and
          p["Q_pre_and_gate_not_captured"] is True and p["norm_weights_teacher_o_proj_pending"] is True,
          "actual unique same-model projection event and honest absent objective inputs")
        key=(rank,sample,layer);require(key not in seen,"no duplicate projection");seen.add(key)
        for ref in (p["raw_pre"],p["live_views_ref"],p["k_ref"]):inside_root(ref["path"],root)
        pre=load_bound(p["raw_pre"]);lv=load_bound(p["live_views_ref"]);dtype=views(lv)
        require(lv["raw_pre"]==p["raw_pre"] and pre["source_lock_ref"]==source and
          (pre["rank"],pre["sample_id"],pre["logical_layer"])==(rank,sample,layer) and
          pre["actual_input_ref"]==producer["input_ref"] and
          pre["token_ids_sha256"]==proof["actual_input"]["token_ids_sha256"] and
          pre["returned_before_first_shape_assertion"]["qkv"]==lv["live"]["qkv"] and
          pre["snapshots_are_not_live_alias_evidence"] is True,"original before-assert raw/caller/token descriptor evidence")
        order=proof["actual_qkv_legacy_order"]
        require(lv["actual_qkv_legacy_order"]==order and order["local_projection_offsets"]=={"k":3072,"v":3328} and
          order["global_kv_channel_indices"]==list(range(rank*256,(rank+1)*256)),"actual source-bound global head mapping")
        kr=p["k_ref"];require(reference(kr["path"])==kr and kr["bytes"]==2*2**20 and p["dtype"]==dtype,"whole original K raw")
        require(reference(item["ref"]["path"])==item["ref"] and
          item["ref"]["sha256"]==p["original_projection_v_snapshot_sha256"] and
          item["ref"]["bytes"]==p["original_projection_v_snapshot_bytes"]==2*2**20,
          "entire independently hashed post-fused V equals original projection snapshot for this actual input")
        b=Path(kr["path"]).read_bytes()
        if dtype=="torch.float16":a=np.frombuffer(b,dtype="<f2").astype(np.float64)
        else:a=(np.frombuffer(b,dtype="<u2").astype(np.uint32)<<16).view("<f4").astype(np.float64)
        require(a.size==4096*256 and bool(np.isfinite(a).all()),"every original projection K value finite")
        a=a.reshape(4096,256);mn=a.min(axis=0);mx=a.max(axis=0);s=p["k_statistics"]
        require(s["count"]==4096 and np.array_equal(mn,np.array(s["min"])) and
          np.array_equal(mx,np.array(s["max"])),"all4096x256 independent exact pre-normalization K statistics")
        group=(layer,rank)
        if group not in bounds:bounds[group]=[mn,mx]
        else:bounds[group]=[np.minimum(bounds[group][0],mn),np.maximum(bounds[group][1],mx)]
        checked+=1;rawk+=len(b);del a,b,mn,mx
    require(checked==16384 and rawk==32*2**30 and len(seen)==16384,"all256x16FAx4TP preprojection K events")
    global_features={}
    for layer in LAYERS:
        mn=[float(x) for r in range(4) for x in bounds[(layer,r)][0]]
        mx=[float(x) for r in range(4) for x in bounds[(layer,r)][1]]
        global_features[layer]={"min":mn,"max":mx,"absmax":[max(abs(a),abs(b)) for a,b in zip(mn,mx)],
          "feature_rows":[[a,b] for a,b in zip(mn,mx)],"feature_shape":[1024,2]}
    require(reference(root/"PRODUCER_RESULT.json")==pref,"actual immutable complete baseline")
    return {"schema":"SKVQ_PREPROJECTION_RAW_CONSUMED_V1",
      "status":"ALL_ACTUAL_PREPROJECTION_K_AND_V_EQUIVALENCE_CONSUMED_NOT_AUTHOR_CALIBRATION",
      "producer_ref":pref,"baseline_receipt_ref":bref,"projection_source_lock_ref":source,
      "preprojection_K_features":global_features,"events":checked,"preprojection_K_raw_bytes":rawk,
      "actual_original_V_equivalence_verified_for_captured_inputs_only":True,
      "Q_pre_gate_norm_weights_teacher_o_proj_pending":True,"exact_author_raw_source_pending":True,
      "KMeans_permutation_alpha_not_run":True,"native_ready":False,"model_ready":False}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root",required=True);ap.add_argument("--baseline-receipt",required=True);ap.add_argument("--output",required=True);a=ap.parse_args()
    require(os.environ.get("QWEN36_SKVQ_PROJECTION_CONSUME_ENABLE")=="1","DEFAULT OFF independent projection consumer opt-in")
    device_free();root=Path(a.root);dest=Path(a.output)
    require(dest.parent==root and dest.name=="PREPROJECTION_CONSUMED.json","exact owned no-overwrite output")
    print(json.dumps(publish(dest,consume(root,a.baseline_receipt)),sort_keys=True))
if __name__=="__main__":main()

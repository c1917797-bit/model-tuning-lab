"""Independent CPU-only raw capture/statistic consumer. No candidate/Torch import.
Hashes every full Q/K/V event; consumes actual recorded source/call/token identities.
This is NOT quantization, native algorithm PASS, memory gain or E2E acceptance.
"""
import argparse,hashlib,json,math,sys
from pathlib import Path
from io_contract import require,reference,sha_file,publish_json
from consume_inputs import consume as consume_input_bytes
PINS=json.loads((Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-calibration-capture-chain-v1-001")/"source_pins.json").read_text())
from tp_provider_current import consume_identity
from consume_text_input_current import consume as consume_text,runtime_sources as input_runtime_sources
LAYERS=tuple("model.layers."+str(i)+".self_attn" for i in range(3,64,4))
def tensor(p,dtype,shape):
    import numpy as np
    b=Path(p).read_bytes();require(len(b)==math.prod(shape)*2,"full actual A16 byte count")
    if dtype=="torch.float16":x=np.frombuffer(b,dtype="<f2").astype(np.float64)
    elif dtype=="torch.bfloat16":
        x=(np.frombuffer(b,dtype="<u2").astype(np.uint32)<<16).view("<f4").astype(np.float64)
    else:raise ValueError("A16 dtype only")
    require(bool(np.isfinite(x).all()),"all actual QKV finite")
    return x.reshape(shape)
def stats(x,s):
    import numpy as np
    a=x.reshape(4096,256);require(s["count"]==4096,"actual all-token statistics")
    require(np.array_equal(a.min(axis=0),np.array(s["min"])) and
      np.array_equal(a.max(axis=0),np.array(s["max"])),"independent decoded exact min/max over full4096")
    # Reduction-order upper bound for FP64 diagnostic sums, not an SKVQ
    # accuracy threshold. Original A16 raw remains available for author search.
    for value,expected in ((a,np.array(s["sum_fp64"])),(a*a,np.array(s["sumsq_fp64"]))):
        calculated=value.sum(axis=0)
        bound=4096*np.finfo(np.float64).eps*np.abs(value).sum(axis=0)
        require(bool((np.abs(calculated-expected)<=bound).all()),"independent FP64 statistic reduction bound")
def consume(root):
    root=Path(root);producer=json.loads((root/"PRODUCER_RESULT.json").read_text())
    pref=reference(root/"PRODUCER_RESULT.json")
    require(producer["schema"]=="SKVQ_CAPTURE_PRODUCER_RESULT_V1" and
      producer["status"]=="ALL256_CAPTURED_PENDING_INDEPENDENT_CONSUMER" and
      producer["primary"] is None and producer["actual_native_baseline_capture_only"] is True and
      producer["author_calibration_not_run"] is True,"actual full producer terminal, not failed/subset")
    require(len(producer["secondary"])==4 and
      all(not r.get("primary") and not r.get("secondary") and r.get("closed") is True for r in producer["secondary"]),"all4 restored owned sessions")
    input_ref=producer["input_ref"];require(reference(input_ref["path"])==input_ref,"actual frozen input")
    input_result=consume_input_bytes(input_ref["path"])
    inputs=json.loads(Path(input_ref["path"]).read_text());install=json.loads((root/"INSTALL.json").read_text())
    require(len(install)==4 and {r["rank"] for r in install}==set(range(4)),"actual4 rank closure")
    install_by_rank={r["rank"]:r for r in install}
    native_input_runtime=input_runtime_sources(producer["current_source_ref"])
    global_stats={}
    hashes=[];checked=0;identities=[]
    for rank in range(4):
        rrpath=root/("rank-"+str(rank))/"RANK_RESULT.json";rrref=reference(rrpath)
        require(rrref in producer["rank_results"],"actual independent rank terminal ref")
        rr=json.loads(rrpath.read_text())
        require(rr["rank"]==rank and rr["status"]=="ALL_RANK_RAW_CAPTURED_NOT_CALIBRATED" and len(rr["events"])==4096 and
          rr["restore"]=={"all_owned_instance_hooks_restored":True,"GDN48_untouched":True,"secondary":[]},"all256x16 exact lifecycle")
        identity=rr["identity"];consume_identity(identity,rank);identities.append(identity)
        require(identity==install_by_rank[rank]["identity"] and identity["public_TP_rank"]==rank,"actual source-bound worker identity")
        for name in ("tp","world"):
            g=identity["groups"][name]
            require(g["global_rank"]==rank and g["rank_in_group"]==rank and g["members"]==list(range(4)) and g["world_size"]==4,"realTP4 public rank/group closure")
        for name in ("pp","dp","pcp","dcp"):
            require(identity["groups"][name]["members"]==[rank] and identity["groups"][name]["world_size"]==1,"actual no pipeline/context/data sharding")
        seen=set();native_input_refs={}
        for eref in rr["events"]:
            require(reference(eref["path"])==eref,"actual full event byte binding")
            event=json.loads(Path(eref["path"]).read_text());sample=event["sample_id"];logical=event["logical_layer"]
            require(type(sample) is int and 0<=sample<256 and logical in LAYERS and event["rank"]==rank and
              (sample,logical) not in seen,"one unique real input/layer/rank event")
            seen.add((sample,logical))
            pre_ref=event["raw_pre"];require(reference(pre_ref["path"])==pre_ref,"pre-copy immutable raw evidence")
            pre=json.loads(Path(pre_ref["path"]).read_text())
            require(pre["sample_id"]==sample and pre["logical_layer"]==logical and pre["rank"]==rank and
              pre["snapshot_clones_are_not_live_alias_proof"] is True,"live descriptors distinct from snapshot clones")
            proof=event["actual_same_input_post_rope_evidence"]
            consume_identity(proof["rank"],rank)
            require(pre["proof"]==proof and proof["rank"]["public_TP_rank"]==rank and
              proof["post_rope"]["caller_line"]==81 and proof["post_rope"]["actual_receiver_function_bound"] is True,
              "actual copied donor call source proof")
            require(proof["actual_input"]["input_ref"]==input_ref and proof["actual_input"]["sample_id"]==sample and
              proof["actual_input"]["token_ids_sha256"]==inputs["samples"][sample]["token_ids_sha256"] and
              proof["actual_input"]["actual_forward_tokens_equals_frozen_sample"] is True and
              proof["actual_input"]["actual_positions_zero_to4095"] is True,"actual full same-token model forward binding")
            from io_contract import sample_ids
            text_ref=proof["actual_input"]["native_text_input_provenance_ref"]
            if sample not in native_input_refs:
                consume_text(text_ref,producer["current_source_ref"],input_ref,sample,rank,identity,
                  sample_ids(input_ref["path"],sample),inputs["samples"][sample]["token_ids_sha256"],
                  runtime=native_input_runtime)
                native_input_refs[sample]=text_ref
            else:require(native_input_refs[sample]==text_ref,"all16 FA share one exact original input provenance")
            actual_sources=proof["runtime_source_bindings"]
            require(actual_sources==install_by_rank[rank]["sources"],"stable actual deployed source modules")
            for pin in PINS["sources"]:
                require(actual_sources[pin["module"]]["sha256"]==pin["sha256"] and
                  sha_file(pin["snapshot"])==pin["sha256"],"actual runtime/copy source byte provenance")
            for side,heads in (("q",6),("k",1),("v",1)):
                item=event["snapshots"][side];r=item["ref"]
                require(reference(r["path"])==r and r["bytes"]==4096*heads*256*2 and
                  item["shape"]==[4096,heads,256] and item["snapshot_contiguous_independent_clone"] is True,
                  "all original precision full QKV bytes")
                live=pre["live_alias_descriptors_before_copy"][side]
                require(item["live_tensor"]==live,"snapshot referenced saved pre-copy live descriptor")
                aliases=proof["post_rope"]["live_tensors"][side]
                a=aliases["qwen_live_output"];b=aliases["pre_cache_input"]
                require(aliases["live_storage_alias_observed"] is True and a["data_ptr"]==b["data_ptr"]==live["data_ptr"] and
                  a["storage_data_ptr"]==b["storage_data_ptr"]==live["storage_data_ptr"] and
                  a["storage_offset_elements"]==b["storage_offset_elements"]==live["storage_offset_elements"],
                  "actual saved caller/native typed view alias, not cloned pointer")
                x=tensor(r["path"],item["dtype"],item["shape"])
                if side in ("k","v"):
                    stats(x,item["statistics"])
                    key=(logical,side,rank);mn=x.reshape(4096,256).min(axis=0);mx=x.reshape(4096,256).max(axis=0)
                    if key not in global_stats:global_stats[key]=[mn,mx]
                    else:
                        import numpy as np
                        global_stats[key]=[np.minimum(global_stats[key][0],mn),np.maximum(global_stats[key][1],mx)]
                hashes.append(r);del x
            checked+=1
        require(seen=={(s,l) for s in range(256) for l in LAYERS},"full256x16 no missing events")
    require(len({(r["pid"],r["pid_start_ticks"]) for r in identities})==4,"four distinct real workers")
    joined={}
    for logical in LAYERS:
        joined[logical]={}
        for side in ("k","v"):
            joined[logical][side]={name:[float(x) for rank in range(4) for x in global_stats[(logical,side,rank)][i]]
              for i,name in enumerate(("min","max"))}
            require(len(joined[logical][side]["min"])==1024,"true full1024 globalKV channel rank join")
    require(checked==16384 and reference(root/"PRODUCER_RESULT.json")==pref,"all4x256x16 immutable terminal")
    return {"schema":"SKVQ_CAPTURE_RAW_CONSUMED_V1","status":"FULL_NATIVE_BASELINE_RAW_CAPTURE_CONSUMED_NOT_CALIBRATED",
      "producer_ref":pref,"inputs_consumed":input_result,"events":checked,"qkv_bytes":sum(r["bytes"] for r in hashes),
      "tp_rank_order_channel_minmax":joined,"global_QKV_head_order_verified":False,"all4_rank_full_QKV_original_precision_bytes_consumed":True,
      "author_kmeans_alpha_search_pending":True,"compact_allocator_and_service_candidate_pending":True,
      "native_ready":False,"model_ready":False}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--root",required=True);p.add_argument("--output",required=True);a=p.parse_args()
    require("torch" not in sys.modules and not list(Path("/dev").glob("davinci*")) and
      not any(Path("/dev",x).exists() for x in ("devmm_svm","hisi_hdc")),"independent Devices[] CPU-only consumer")
    print(json.dumps(publish_json(a.output,consume(a.root)),sort_keys=True))
if __name__=="__main__":main()

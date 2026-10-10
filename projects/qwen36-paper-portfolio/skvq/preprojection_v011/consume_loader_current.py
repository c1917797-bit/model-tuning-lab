"""Independent full baseline raw + actual legacy loader order consumer. No Torch.
Source/TP order proof is not SKVQ quantization, native correctness or E2E PASS.
"""
import argparse,hashlib,json,sys
from pathlib import Path
BASE=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-calibration-capture-chain-v1-001")
if hashlib.sha256((BASE/"SOURCE_MANIFEST.sha256").read_bytes()).hexdigest()!="ecc5065c34b63029e44ba2be227d725c67f6437b2023aeb0e8a9916d3dbab711":raise ValueError("immutable001 source manifest")
sys.path.insert(0,str(BASE))
from io_contract import require,reference,publish_json,sha_file
from consume_capture import consume as full_baseline_raw
from order_oracle_current import consume_four,consume_record,consume_install_raw,SHA
SNAPSHOT="/cache/cch/qwen36-paper-preparation-20261007/lowbit/source-public-linear-660-20261008-1106-001/linear.py"
def consume(root):
    import current_contract as C
    source=C.source();root=Path(root);require(sha_file(SNAPSHOT)==SHA,"actual copied official linear bytes")
    result=full_baseline_raw(root) # every full raw Q/K/V, stats, token/source/lifecycle
    installs=json.loads((root/"INSTALL.json").read_text());rankrecords={}
    for item in installs:
        rank=item["rank"];ref=item["actual_qkv_legacy_order_ref"]
        require(reference(ref["path"])==ref,"actual recorded loaded-parameter source/origin")
        v=json.loads(Path(ref["path"]).read_text())
        require(v["schema"]=="SKVQ_QKV_LOADER_RANK_RAW_V1" and v["rank"]==rank and v["identity"]==item["identity"],"same real captured rank process")
        require(set(v["records"])=={"model.layers."+str(i)+".self_attn" for i in range(3,64,4)},"all16 actual FA loader records")
        require(v["current_source_ref"]==source,"actual current class/loader proof source")
        raw_ref=v["raw_before_qualification_ref"]
        require(reference(raw_ref["path"])==raw_ref,"immutable all16 original projection raw before gate")
        consume_install_raw(json.loads(Path(raw_ref["path"]).read_text()),rank,item["identity"],v["records"],source)
        rankrecords[rank]=v["records"]
    for logical in rankrecords[0]:
        consume_four({r:rankrecords[r][logical] for r in range(4)})
    events=0
    for rank in range(4):
        rr=json.loads((root/("rank-"+str(rank))/"RANK_RESULT.json").read_text())
        for eref in rr["events"]:
            require(reference(eref["path"])==eref,"actual frozen event ref")
            e=json.loads(Path(eref["path"]).read_text());logical=e["logical_layer"]
            record=e["actual_same_input_post_rope_evidence"]["actual_qkv_legacy_order"]
            require(record==rankrecords[rank][logical],"actual callback ran before every native cache writer; not install-only")
            consume_record(record,rank);events+=1
    require(events==16384,"full all176? NO: this is256inputsx16FAx4ranks baseline capture, not native matrix")
    result["status"]="FULL_BASELINE_CAPTURE_AND_ACTUAL_LEGACY_KV_CHANNEL_ORDER_CONSUMED_NOT_CALIBRATED"
    result["global_QKV_head_order_verified_from_actual_bound_loader"]=True
    result["full_global_kv_channel_minmax"]=result.pop("tp_rank_order_channel_minmax")
    result["global_QKV_head_order_verified"]=True
    result["actual_weight_publisher_identity_pending"]=True
    result["author_kmeans_alpha_search_pending"]=True
    return result
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--root",required=True);p.add_argument("--output",required=True);a=p.parse_args()
    require("torch" not in sys.modules and not list(Path("/dev").glob("davinci*")) and
      not any(Path("/dev",x).exists() for x in ("devmm_svm","hisi_hdc")),"independent Devices[] CPU-only")
    print(json.dumps(publish_json(a.output,consume(a.root)),sort_keys=True))
if __name__=="__main__":main()

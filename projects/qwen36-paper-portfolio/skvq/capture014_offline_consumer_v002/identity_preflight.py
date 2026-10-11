"""Small readonly real014 identity preflight. No QKV tensor reads or framework."""
import argparse,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import offline_contract as D
from capture_identity import pair,exact
def inspect_pairs(source):
    C,loader,projection,stage=D.original_modules(source)
    from tp_provider_current import consume_identity
    import order_oracle_derived as order
    root=D.RAW_ROOT/"run-skvq-capture-projection-001-main"
    install_ref=D.ref(root/"INSTALL.json");installs=D.obj(install_ref)
    producer_ref=D.ref(root/"PRODUCER_RESULT.json");producer=D.obj(producer_ref)
    D.need(exact(installs,producer["worker_install_results"]),"original producer and actual INSTALL are identical")
    D.need(type(installs)is list and len(installs)==4 and
      {r["rank"]for r in installs}==set(range(4)),"complete original four ranks")
    result=[]
    for rank in range(4):
        item=next(x for x in installs if x["rank"]==rank)
        lr=item["actual_qkv_legacy_order_ref"]
        D.need(Path(lr["path"])==root/("rank-"+str(rank))/"QKV_LOADER_ORDER.json",
          "original exact rank loader path; no guest alias or alternate run")
        v=D.obj(lr)
        D.need(v["schema"]=="SKVQ_QKV_LOADER_RANK_RAW_V1"and v["rank"]==rank and
          v["current_source_ref"]==D.CAPTURE,"actual original loader schema/rank/source")
        observed=pair(v["identity"],item["identity"],rank,consume_identity)
        D.need(set(v["records"])=={"model.layers."+str(i)+".self_attn"for i in range(3,64,4)},
          "original all16 actual FA loader records")
        rr=v["raw_before_qualification_ref"]
        D.need(Path(rr["path"])==root/("QKV_INSTALL-rank-%d-RAW.json"%rank),
          "original exact raw before-qualification path")
        raw=D.obj(rr)
        order.consume_install_raw(raw,rank,item["identity"],v["records"],D.CAPTURE,
          loader_identity=v["identity"])
        result.append(dict(rank=rank,install_ref=install_ref,loader_ref=lr,raw_before_qualification_ref=rr,
          ordered_observation=observed,source_ref=D.CAPTURE))
    for logical in v["records"]:
        order.consume_four({r:D.obj(next(x for x in installs if x["rank"]==r)["actual_qkv_legacy_order_ref"])["records"][logical]for r in range(4)})
    D.need(D.ref(root/"INSTALL.json")==install_ref and D.ref(root/"PRODUCER_RESULT.json")==producer_ref,
      "original metadata immutable through preflight")
    return dict(schema="skvq.capture014.ordered-identity-preflight/v1",
      status="ALL4_ORDERED_STABLE_IDENTITY_CHECKED_NOT_RAW_WHOLE",source_ref=D.CAPTURE,
      consumer_source_ref=source,producer_ref=producer_ref,install_ref=install_ref,ranks=result,
      raw_tensors_read=False,whole_capture_consumed=False,native_ready=False,model_ready=False)
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--execute",action="store_true")
    ap.add_argument("--source-manifest-sha256");ap.add_argument("--output");a=ap.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,whole_capture_consumed=False)));return
    D.cpu_only();source=D.source(a.source_manifest_sha256)
    D.need(a.output and not Path(a.output).exists(),"new absent preflight evidence file")
    print(json.dumps(D.publish(a.output,inspect_pairs(source)),sort_keys=True))
if __name__=="__main__":main()

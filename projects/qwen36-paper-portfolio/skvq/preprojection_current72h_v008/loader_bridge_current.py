"""Owned session successor callback. Original capture001 sources remain immutable.
MAIN must replace only CLI install_rpc import with this install_rpc in a private
successor; generic capture001/consumer do not acquire global-order PASS.
"""
import hashlib,json,sys
from pathlib import Path
BASE=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-calibration-capture-chain-v1-001")
PINS={"runtime_capture.py":"c1133ea708b1345d61d6ee8e836fc44412cf9ebcc87573ca5baf14ce1ffde49c",
"tp_provider.py":"b91e0e673db50a8091dae52d992f02da7b5b2f0ed01c55eeabb6729abc43c9c7"}
for name,sha in PINS.items():
    if hashlib.sha256((BASE/name).read_bytes()).hexdigest()!=sha:raise ValueError("frozen001 source mismatch")
sys.path.insert(0,str(BASE))
import runtime_capture_current as original
from loader_order import actual
from order_oracle import consume_record
def install_rpc(target,input_path,root):
    w=original.actual_worker(target);original.deployed_sources();original.check_config(w)
    _,registry,_=original.registry_for(w);identity=original.RankProvider()()
    rank=identity["public_TP_rank"];records={}
    for logical,(outer,_) in registry.items():
        record=actual(outer,rank);consume_record(record,rank);records[logical]=record
    result=original.install_rpc(target,input_path,root);session=w._skvq_capture_session
    oldprovider=session.provider
    def provider(logical,query,key,value,metadata):
        record=actual(session.registry[logical][0],rank)
        original.require(record==records[logical],"actual loaded parameter/source/TP order unchanged")
        proof=oldprovider(logical,query,key,value,metadata);proof["actual_qkv_legacy_order"]=record
        return proof
    session.provider=provider
    ref=original.publish_json(session.sink.path/"QKV_LOADER_ORDER.json",{
      "schema":"SKVQ_QKV_LOADER_RANK_RAW_V1","rank":rank,"identity":identity,"records":records,
      "actual_callback_install_pending_until_first_event":True,"native_ready":False})
    result["actual_qkv_legacy_order_ref"]=ref
    return result

"""Actual complete old raw/order oracle plus independent original preprojection.
Default OFF. No candidate/calibration/Torch computation is used as reference.
"""
import argparse,importlib.util,json,os,sys
from pathlib import Path
import current_contract as C
HERE=Path(__file__).resolve().parent
BASE=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-calibration-capture-chain-v1-001")
ORDER=BASE.parent/"skvq-tp4-qkv-loader-order-v1-001"
PROJECTION=BASE.parent/"skvq-preprojection-capture-adapter-v1-001"
BOUNDARY=BASE.parent/"skvq-calibration-boundary-v1-001"
def donor(name,path):
    path=Path(path);ref=C.reference(path)
    manifest=json.loads(Path(C.source()["path"]).read_bytes())
    C.require(ref in manifest["dependencies"],"explicit independent donor in current full closure")
    old=sys.modules.get(name)
    if old is not None:
        C.require(Path(old.__file__).resolve()==path.resolve() and C.reference(old.__file__)==ref,"cached donor exact origin")
        return old
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    try:spec.loader.exec_module(module)
    except BaseException:
        # Do not remove an unknown module or silently swap math identity.
        raise
    C.require(C.reference(path)==ref,"stable loaded donor source")
    return module
def validators():
    for path in (BASE,ORDER,BOUNDARY,PROJECTION):
        if str(path)not in sys.path:sys.path.insert(0,str(path))
    donor("io_contract",BASE/"io_contract.py")
    donor("consume_inputs",BASE/"consume_inputs.py")
    donor("consume_capture",BASE/"consume_capture.py")
    donor("order_oracle",ORDER/"order_oracle.py")
    baseline=donor("consume_loader_order",ORDER/"consume_loader_order.py")
    contracts=donor("contracts",BOUNDARY/"contracts.py")
    import consume_projection_current as projection
    return baseline,projection,contracts
def cohort(producer,source):
    import spawn_startup as startup
    startup.consume_producer(producer,source)
    import rpc_extension as rpc
    for result in producer["worker_install_results"]:rpc.consume_install(result,source)
    C.require(producer["current_source_ref"]==source and producer["current_clock"]["protocol_ref"]==C.CLOCK and
        producer["current_clock"]["portfolio_cutoff_epoch"]==C.CUT and
        producer["portfolio_deadline_utc"]=="2026-10-12T07:00:25Z","actual current producer, not old expired capture")
def combine(baseline,projection,source,baseline_ref,projection_ref):
    C.require(baseline["schema"]=="SKVQ_CAPTURE_RAW_CONSUMED_V1" and
        baseline["status"]=="FULL_BASELINE_CAPTURE_AND_ACTUAL_LEGACY_KV_CHANNEL_ORDER_CONSUMED_NOT_CALIBRATED" and
        baseline["events"]==16384 and baseline["qkv_bytes"]==256*C.GIB and
        baseline["global_QKV_head_order_verified_from_actual_bound_loader"]is True and
        baseline["global_QKV_head_order_verified"]is True and
        baseline["native_ready"]is False and baseline["model_ready"]is False,"complete original raw/order consumer")
    C.require(projection["schema"]=="SKVQ_PREPROJECTION_RAW_CONSUMED_V1" and
        projection["status"]=="ALL_ACTUAL_PREPROJECTION_K_AND_V_EQUIVALENCE_CONSUMED_NOT_AUTHOR_CALIBRATION" and
        projection["producer_ref"]==baseline["producer_ref"] and projection["baseline_receipt_ref"]==baseline_ref and
        projection["events"]==16384 and projection["preprojection_K_raw_bytes"]==32*C.GIB and
        projection["actual_original_V_equivalence_verified_for_captured_inputs_only"]is True and
        projection["native_ready"]is False and projection["model_ready"]is False,"all original preprojection, same cohort; no postRoPE substitution")
    result=dict(baseline)
    result.update(current_source_ref=source,current_clock=C.clock(),baseline_receipt_ref=baseline_ref,
        preprojection_consumed_ref=projection_ref,preprojection_K_raw_bytes=32*C.GIB,
        actual_original_V_equivalence_verified_for_captured_inputs_only=True,
        actual_teacher_Q_pre_gate_norm_weights_o_proj_pending=True,
        author_clustering_pending=True,TP_local_clustering_is_new_unrun_adaptation=True,
        quantized_native_gate_pending=True,whole_operation_authority_pending=True)
    return result
def run(root,output):
    source=C.source();root=Path(root);output=Path(output)
    C.require(root.is_absolute() and root.resolve()==root and root.is_dir() and
        root.name=="run-skvq-capture-projection-001-main" and output==root.parent/"CAPTURE_CONSUMED.json",
        "actual capture and exact host-owned aggregate output")
    before=C.reference(root/"PRODUCER_RESULT.json")
    cohort(json.loads(Path(before["path"]).read_bytes()),source)
    baseline,projection,contracts=validators();contracts.device_free()
    value=baseline.consume(root)
    br=contracts.publish(root/"BASELINE_CONSUMED.json",value)
    pv=projection.consume(root,br["path"])
    pr=contracts.publish(root/"PREPROJECTION_CONSUMED.json",pv)
    C.require(C.reference(root/"PRODUCER_RESULT.json")==before,"immutable full producer through both actual independent calls")
    result=combine(value,pv,source,br,pr)
    C.require(C.source()==source,"source immutable after whole raw consumption")
    return contracts.publish(output,result)
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--execute",action="store_true")
    ap.add_argument("--source-manifest-sha256");ap.add_argument("--root");ap.add_argument("--output");a=ap.parse_args()
    if not a.execute:print(json.dumps({"default_enabled":False,"native_ready":False,"model_ready":False}));return
    C.configure(a.source_manifest_sha256)
    C.require(os.environ.get("QWEN36_SKVQ_PROJECTION_CONSUME_ENABLE")=="1","explicit Devices[] independent opt-in")
    print(json.dumps(run(a.root,a.output),sort_keys=True))
if __name__=="__main__":main()

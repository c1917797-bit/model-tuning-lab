"""Strict current original-operation + terminal/owned/raw consumer, not algorithm PASS."""
import argparse,json,sys
from pathlib import Path
import current_contract as C
def original(value,argv):
    C.require(value["schema"]=="agentweb.operation/v1","real original agentweb operation")
    op=value["operation"];record=op["result"]["record"]
    C.require(value["terminal"]is True and value["status"]=="completed"and value["succeeded"]is True and value["error"]is None and
        op["ok"]is True and op["result"]["state"]=="completed"and op["routeDecision"]=="peer_direct" and op["targetPeerId"]=="lgw_a6109c51076a4a2c9d2674ca5a8704a0",
        "exact ma direct original successful terminal; not running/unknown/transport")
    actual=[record["command"]]+record["args"]
    C.require(actual==argv and record["exitCode"]==0 and record.get("error")is None and
        record.get("timedOut")is False and record.get("cancelled")is False,"actual original exact entry argv and exit; no retry authority")
    return record
def host_argv(root,sha):
    return ["/usr/bin/env","MAIN_SKVQ_HOST_ENABLE=1","/usr/bin/prlimit","--cpu=7200:7200","--",
        "/usr/bin/python3","-B",str(C.ROOT/"MAIN_HOST.py"),"--execute","--source-manifest-sha256",sha,"--output",str(root)]
def consume(root,original_ref):
    source=C.source();root=Path(root);C.checked(original_ref)
    record=original(json.loads(Path(original_ref["path"]).read_bytes()),host_argv(root,source["sha256"]))
    from consume_host import consume as host_consume
    terminal=host_consume(root)
    C.require(terminal["status"]=="FULL_BASELINE_RAW_CAPTURE_HOST_CONSUMED_NOT_AUTHOR_CALIBRATION",
        "all actual host/raw/preprojection/cleanup independently consumed")
    C.require(C.source()==source,"current full closure unchanged after original")
    return {"schema":"skvq.current72h.preprojection.whole/v1","status":"FULL_CAPTURE_PREPROJECTION_ORIGINAL_CONSUMED_NOT_CALIBRATED",
        "source_ref":source,"original_ref":original_ref,"host_result_ref":terminal["host_result"],
        "terminal_consumer":terminal,"source_only_not_ready":False,
        "actual_capture_only":True,"author_sources_clustering_clip_search_pending":True,
        "quantized_176_matrix_pending":True,"native_ready":False,"model_ready":False,"performance_ready":False,
        "whole_capture_consumed":True,"clock":C.clock()}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--execute",action="store_true");ap.add_argument("--source-manifest-sha256")
    ap.add_argument("--root");ap.add_argument("--original-ref-json");ap.add_argument("--output");a=ap.parse_args()
    if not a.execute:print(json.dumps({"default_enabled":False,"model_ready":False}));return
    C.configure(a.source_manifest_sha256)
    r=json.loads(Path(a.original_ref_json).read_bytes())
    from consume_host import publish_json # Installs the exact BASE donor path before standalone CLI import.
    print(json.dumps(publish_json(a.output,consume(a.root,r)),sort_keys=True))
if __name__=="__main__":main()

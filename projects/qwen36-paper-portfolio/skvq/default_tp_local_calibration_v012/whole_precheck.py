"""Clean isolated replay of the frozen derived014 whole. No raw math rerun.
No parent namespace injection, module deletion, fake original, or new authority.
"""
import argparse,importlib.util,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import common as C
def envelope(value):
    C.need(type(value)is dict and value.get("schema")=="skvq.capture014.offline.whole/v1"and
      value.get("status")=="RELEASED014_ALL256_RAW_DERIVED_CPU_WHOLE_CONSUMED_NOT_CALIBRATED"and
      value.get("source_ref")==C.DERIVED and value.get("producer_source_ref")==C.CAPTURE and
      value.get("original_failed_whole_ref")==C.FAILED_ORIGINAL and
      value.get("original_failed_whole_preserved")is True and value.get("original_failed_whole_succeeded")is False and
      value.get("whole_operation_consumed")is True and value.get("Devices_empty")is True and
      value.get("CPU_QUEUE_no_peer_admission")is True and value.get("events")==16384 and
      type(value.get("events"))is int and type(value.get("qkv_bytes"))is int and value.get("qkv_bytes")==256*2**30 and
      type(value.get("preprojection_K_raw_bytes"))is int and value.get("preprojection_K_raw_bytes")==32*2**30 and value.get("clock")==C.CLOCK and
      value.get("portfolio_cutoff_epoch")==C.CUT and value.get("author_calibration_pending")is True and
      value.get("author_global_grouping_equivalent")is False and
      all(value.get(k)is False for k in("native_ready","model_ready","performance_ready","task_ready")),
      "actual new derived whole/old FAILED separate, all256/raw coverage; never old success or fixture")
    return value
def command(whole_ref,source_sha):
    return [sys.executable,"-I","-B",str(HERE/"whole_precheck.py"),"--execute",
      "--source-manifest-sha256",source_sha,"--whole-ref-inline",
      json.dumps(whole_ref,sort_keys=True,separators=(",",":"),allow_nan=False)]
def precheck(whole_ref):
    whole=envelope(C.bound(whole_ref))
    source=C.reference(HERE/"SOURCE_MANIFEST.json");manifest=C.bound(source)
    row=next(r for r in manifest["files"]if Path(r["path"]).name=="whole_precheck.py")
    C.need(C.reference(HERE/"whole_precheck.py")==row,"actual own fresh child precheck source bytes")
    argv=command(whole_ref,source["sha256"])
    result=subprocess.run(argv,capture_output=True,timeout=120)
    C.need(result.returncode==0,"actual clean derived whole replay failed: "+result.stderr.decode("utf-8",errors="replace")[-8192:])
    C.need(len(result.stdout)<=8*2**20 and json.loads(result.stdout)==whole,
      "clean child actually reconsumed whole exactly; no new certificate/namespace mutation")
    return whole
def replay(whole_ref,expected):
    C.source(expected)
    whole=envelope(C.bound(whole_ref));manifest=C.bound(C.DERIVED)
    C.need(manifest["schema"]=="skvq.capture014.offline.sources/v1"and
      manifest["producer_source_ref"]==C.CAPTURE and manifest["default_enabled"]is False,
      "frozen separate derived consumer, not altered original014")
    rows={Path(r["path"]).name:r for r in manifest["files"]}
    C.need(not any(n in sys.modules for n in("cpu_host","consume_cpu_whole","offline_contract")),
      "fresh isolated namespace required; no reuse or module delete")
    root=Path(C.DERIVED["path"]).parent;sys.path.insert(0,str(root))
    D=C.donor("offline_contract",rows["offline_contract.py"]["path"],rows["offline_contract.py"]["sha256"])
    C.need(D.source(C.DERIVED["sha256"])==C.DERIVED,"installed complete derived source authority")
    from control_ast import derived_reader
    reader=derived_reader(rows["consume_cpu_whole.py"])
    hostmod=sys.modules.get("cpu_host")
    C.need(hostmod is not None and C.reference(hostmod.__file__)==rows["cpu_host.py"],
      "actual derived CPU host module, never calibration host basename")
    value=reader.consume(Path(whole["host_result_ref"]["path"]).parent,whole["original_ref"],C.DERIVED["sha256"])
    C.need(value==whole and C.bound(whole_ref)==whole,"actual original plus child/release/fullraw replay is immutable")
    return value
def main():
    p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true")
    p.add_argument("--source-manifest-sha256");p.add_argument("--whole-ref-inline");a=p.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,no_NPU=True,model_ready=False)));return
    C.need(a.source_manifest_sha256 and a.whole_ref_inline and len(a.whole_ref_inline)<=65536,
      "explicit bounded whole3Ref and current own source")
    value=replay(json.loads(a.whole_ref_inline),a.source_manifest_sha256)
    print(json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False))
if __name__=="__main__":main()

"""Default OFF complete compiled/source-bound stdlib tests, no native imports."""
import argparse,hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--execute",action="store_true")
    ap.add_argument("--source-manifest-sha256");a=ap.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,NPU_initialized=False)));return
    import writer_contract as C
    row=C.ref(HERE/"SOURCE_MANIFEST.json");C.need(row["sha256"]==a.source_manifest_sha256,"actual source SHA")
    body=C.obj(row);C.need(body["schema"]=="skvq.actual-writer-bridge.sources/v1"and body["default_enabled"]is False,"default OFF source")
    rows=body["files"]+body["dependencies"];seen=set()
    for r in rows:
        C.checked(r);C.need(r["path"]not in seen,"unique full source");seen.add(r["path"])
        if r["path"].endswith(".py"):compile(Path(r["path"]).read_bytes(),r["path"],"exec")
    C.need(len(seen)==body["source_count"],"actual full source count")
    import test_writer_bridge as tests
    C.need(tests.main()==0,"actual full17 software; no fixture authority")
    import test_writer_host as host_tests
    C.need(host_tests.main()==0,"actual full12 host/whole software; no runtime authority")
    import test_contract_chain as chain_tests
    C.need(chain_tests.main()==0,"actual4 current source/CLI/mount chain regressions")
    C.need("torch"not in sys.modules and"torch_npu"not in sys.modules,"no native import")
    print(json.dumps(dict(status="SOFTWARE_ONLY",source_ref=row,actual_tests=33,
      NPU_initialized=False,native_ready=False,model_ready=False)))
if __name__=="__main__":main()

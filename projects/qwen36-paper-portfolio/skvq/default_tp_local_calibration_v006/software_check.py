"""Full source/author-byte audit and forty-three stdlib tests; no native imports."""
import argparse,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import common as C
def main():
    p=argparse.ArgumentParser();p.add_argument("--source-manifest-sha256",required=True);a=p.parse_args()
    source=C.source(a.source_manifest_sha256)
    bundle=json.loads((HERE/"author_sources.json").read_bytes())
    import hashlib
    for r in bundle["files"]:
        raw=r["text"].encode();C.need(len(raw)==r["bytes"]and hashlib.sha256(raw).hexdigest()==r["sha256"],"all6 original author byte identities")
        if r["name"].endswith(".py"):compile(raw,r["name"],"exec")
    spec=importlib.util.spec_from_file_location("_skvq_default_source_tests",HERE/"test_default.py")
    tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
    C.need(tests.main()==0,"actual retained23 source/producer/oracle/PT/writer seam tests")
    import test_cpu_host
    C.need(test_cpu_host.main()==0,"actual12 source-derived CPU host/whole/entry cross-stage regressions")
    import test_module_snapshots
    C.need(test_module_snapshots.main()==0,"complete8 actual byte-snapshot/runtime/whole cross-module regressions")
    C.need("torch"not in sys.modules and "torch_npu"not in sys.modules,"software no framework import")
    C.need(C.source(a.source_manifest_sha256)==source,"unchanged complete source after software")
    print(json.dumps(dict(status="SOFTWARE_ONLY",source_ref=source,tests=43,native_ready=False,model_ready=False)))
if __name__=="__main__":main()

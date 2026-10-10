"""Actual aggregate source/CLI/math regression entry. No native import."""
import argparse,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import contract as C
def run(sha):
    source=C.source(sha)
    import test_reader,test_host
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(x)for x in(test_reader,test_host)])
    r=unittest.TextTestRunner(verbosity=2).run(suite)
    C.need(r.testsRun==29 and r.wasSuccessful(),"complete29 actual source/host/reader software, not compile/NPU authority")
    return dict(status="READER_SOFTWARE_ONLY",source_ref=source,tests=29,source_count=C.obj(source)["source_count"],**C.scopes())
def main():
    p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true");p.add_argument("--source-manifest-sha256");a=p.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,**C.scopes())));return
    print(json.dumps(run(a.source_manifest_sha256),sort_keys=True))
if __name__=="__main__":main()

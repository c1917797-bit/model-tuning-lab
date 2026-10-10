"""Current full-source audit and fifty real stdlib regressions, no hardware."""
import argparse,ast,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import current_contract as C
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--source-manifest-sha256",required=True);a=ap.parse_args()
    source=C.configure(a.source_manifest_sha256);m=json.loads(Path(source["path"]).read_bytes())
    for row in m["files"]+m["dependencies"]:
        if row["path"].endswith(".py"):compile(Path(row["path"]).read_bytes(),row["path"],"exec")
    C.require("torch"not in sys.modules and "torch_npu"not in sys.modules,"software does not import runtime")
    spec=importlib.util.spec_from_file_location("skvq_current_tests",HERE/"test_aggregate.py")
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    sys.argv=[str(HERE/"test_aggregate.py")]
    rc=module.main()
    C.require(rc==0,"actual retained38 software; no fixture promotion")
    spec=importlib.util.spec_from_file_location("skvq_input_dependency_tests",HERE/"test_input_dependency.py")
    dependency=importlib.util.module_from_spec(spec);spec.loader.exec_module(dependency)
    C.require(dependency.main()==0,"actual complete12 dependency/child/CPU-only regressions; not package import proof")
    C.require(C.source()==source,"full source unchanged after software")
    print(json.dumps({"status":"SOFTWARE_ONLY","tests":50,"source_ref":source,
        "source_count":m["source_count"],"native_ready":False,"model_ready":False}))
if __name__=="__main__":main()

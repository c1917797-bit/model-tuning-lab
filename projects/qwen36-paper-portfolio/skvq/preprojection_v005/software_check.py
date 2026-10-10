"""Current full-source audit and thirty-eight real stdlib regressions, no hardware."""
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
    C.require(rc==0,"actual full38 software; no fixture promotion")
    C.require(C.source()==source,"full source unchanged after software")
    print(json.dumps({"status":"SOFTWARE_ONLY","tests":38,"source_ref":source,
        "source_count":m["source_count"],"native_ready":False,"model_ready":False}))
if __name__=="__main__":main()

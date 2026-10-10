"""Current full-source audit and one-hundred-forty-seven real stdlib regressions, no hardware."""
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
    spec=importlib.util.spec_from_file_location("skvq_n1_format_tests",HERE/"test_n1_format.py")
    formats=importlib.util.module_from_spec(spec);spec.loader.exec_module(formats)
    C.require(formats.main()==0,"complete8 actual source-policy/producer/consumer regressions; no N1 admission")
    import test_spawn_startup as startup # Actual importable source name also used by real spawn child.
    C.require(startup.main()==0,"complete10 actual source-body/spawn/RPC/consumer regressions; no native runtime admission")
    import test_rpc_extension as rpc
    C.require(rpc.main()==0,"complete12 safe named RPC original-body/delegate/consumer regressions; no native authority")
    import test_native_tp as native_tp
    C.require(native_tp.main([])==0,"complete16 exact native replacement/device/source/consumer regressions; no runtime authority")
    import test_native_qkv as native_qkv
    C.require(native_qkv.main([])==0,"complete18 actual class/constructor/raw/source/independent consumer regressions; no worker values")
    import test_text_input as text_input
    C.require(text_input.main([])==0,"complete17 original preprocess/embedding/root/raw/independent consumer regressions; no native authority")
    import test_process_cmdline as proc_cmdline
    C.require(proc_cmdline.main([])==0,"complete16 exact original process-byte/producer/consumer regressions; not native authority")
    C.require(C.source()==source,"full source unchanged after software")
    print(json.dumps({"status":"SOFTWARE_ONLY","tests":147,"source_ref":source,
        "source_count":m["source_count"],"native_ready":False,"model_ready":False}))
if __name__=="__main__":main()

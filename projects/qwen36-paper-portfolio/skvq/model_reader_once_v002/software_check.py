"""Actual installed full-closure +11 source/CLI cross-module software tests.
No Torch/NPU/container operation. This does not consume missing predecessor data.
"""
import argparse,hashlib,json,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bridge_contract as B
def main():
    p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true");p.add_argument("--source-manifest-sha256")
    p.add_argument("--output");a=p.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,**B.false_scopes())));return
    began=time.monotonic();C,source,m=B.source(a.source_manifest_sha256)
    B.need("torch"not in sys.modules and"torch_npu"not in sys.modules,"real stdlib only full source test")
    import test_model_bridge as T
    T.setup(False);result=T.run()
    B.need(result.wasSuccessful()and result.testsRun==11 and not result.skipped,"all actual11 current source regressions")
    B.need("torch"not in sys.modules and"torch_npu"not in sys.modules,"no native hardware import by source regression")
    value=dict(schema="skvq.model-reader.software/v1",status="SOFTWARE_ONLY",source_ref=source,
      actual_tests=result.testsRun,actual_source_files=m["source_count"],elapsed_seconds=time.monotonic()-began,
      no_Torch=True,no_Docker=True,no_NPU=True,actual_predecessor_data_required=True,**B.false_scopes())
    B.need(Path(a.output).parent.is_dir()and not Path(a.output).exists(),"one absent software sink")
    print(json.dumps(C.publish(a.output,value),sort_keys=True))
if __name__=="__main__":main()


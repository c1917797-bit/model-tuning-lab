"""DefaultOFF complete aggregate source/tests entry. No Torch/Docker/model."""
import argparse,json,os,sys,unittest
from pathlib import Path
import source_contract as c
TESTS=("test_allocation","test_no_pa","test_ann_aggregate","test_replay","test_gdn_metadata","test_gdn_state","test_model_workload","test_formal_stats","test_wire","test_component_handoff","test_fp32_model_adapter","test_identity_n1")
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--source-audit-only",action="store_true")
 p.add_argument("--source-manifest-sha256");p.add_argument("--packet-audit-only",action="store_true");a=p.parse_args()
 if not a.source_audit_only and not a.packet_audit_only:
  print(json.dumps(dict(status="disabled",ready=False,npu_executed=False,model_executed=False)));return
 source,files=(c.packet_source if a.packet_audit_only else c.source)(str(c.ROOT/"SOURCE_MANIFEST.json"),a.source_manifest_sha256)
 for name in files:
  if name.endswith(".py"):compile((c.ROOT/name).read_text(),str(c.ROOT/name),"exec")
 import importlib
 suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(importlib.import_module(n)) for n in TESTS)
 result=unittest.TextTestRunner(verbosity=2).run(suite);c.require(result.wasSuccessful(),"whole proposed-source stdlib tests")
 c.require(not any(k=="torch" or k.startswith(("torch.","torch_npu","vllm")) for k in sys.modules),"no runtime imports by software preparation")
 print(json.dumps(dict(status="source-prepared",source=source,tests=result.testsRun,
  source_count=len(files)+len(c.PINS)+len(c.HOST_DEPENDENCIES),all_runtime_pins_verified=not a.packet_audit_only,ready=False,native_component="pending",
  actual_TP4_FULL_model="pending",paired1024="pending",final2048="actual task inputs/scorer missing")))
if __name__=="__main__":main()

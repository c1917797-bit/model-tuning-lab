"""Complete same660 Devices[] Python3.12 source/file suite; default OFF.
No framework import/model/HAL permission. Exact original reader factory retained.
"""
import argparse,importlib.util,json,sys,unittest
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true")
 p.add_argument("--source-manifest-sha256");p.add_argument("--output",type=Path);a=p.parse_args()
 if not a.execute:print(json.dumps(dict(enabled=False,NPU=False,model_ready=False)));return
 here=Path(__file__).resolve().parent
 def load(n,path):
  s=importlib.util.spec_from_file_location(n,path);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
 l=load("_mixed_software_loader",here/"loader.py");m,ref=l.source(a.source_manifest_sha256)
 l.need(sys.version_info[:2]==(3,12),"same660 actual Python3.12 full native source-body tests")
 import os
 l.need(os.name=="posix"and not any(k.startswith("KIVI_")and k.endswith("_FIXTURE")for k in os.environ),
  "actual mounted source closure, no local fixture path redirection")
 memory=l.memory_module(m);before=memory.memory(expected_limit=8*1024**3)
 def dep(sha):
  rows={r["path"]:r for r in m["dependencies"]if r["sha256"]==sha}
  l.need(len(rows)==1,"unique exact software archive "+sha);r=next(iter(rows.values()));l.checked(r);return Path(r["path"])
 tests=load("_mixed_host_software_tests",here/"test_host.py")
 tests.BASE=dep("0c35d88c4ebe3bf98fde9c3f7f95d8658a7f4c1e577688afa7b0127974426a16").parent
 tests.SCANNER=dep("44e5ccfdad173e6b9eebc025260e489893d672c316c6aac3f8bf68a5e03c16ad")
 names=["test_next","test_owner_ref3","test_runtime_boundary","test_mixed_abi_consumer",
  "test_publication_wire","test_framework_closure","test_explicit_handoff","test_capture_admission","test_consumer_namespace"]
 modules=[load("_mixed_software_"+n,here/(n+".py"))for n in names]
 modules[1].SCHEDULER_ARCHIVE=dep(modules[1].SCHEDULER_SHA)
 modules[7].BASE=tests.BASE
 # Execute the original strict factory FIRST, before provider suites load fixed
 # flat aliases. No sys.modules clearing or weakened original namespace guard.
 closure=modules[5];l.need(closure.ARCHIVE is None,"actual complete factory required");closure.original_reader()
 suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(x)for x in[modules[-1],tests]+modules[:-1])
 l.need(suite.countTestCases()==m["software_tests_declared"]==191,"all178 previous plus13 source namespace regressions")
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 after=memory.memory(expected_limit=8*1024**3)
 memory.consume_memory(after,expected_limit=8*1024**3,namespace_pid=before["process"]["pid"])
 absent=not any(n.split(".")[0]in("torch","torch_npu","triton","vllm")for n in sys.modules)
 l.need(absent,"source-only software cannot leave framework/model imports")
 receipt=dict(schema="kivi.actual-mixed-host-software/v1",source=ref,successful=result.wasSuccessful(),
  tests=suite.countTestCases(),python_version=list(sys.version_info[:3]),execution_profile="same660-Devices[]-CPU8",
  no_framework_import=absent,memory_before=before,memory_after=after,NPU=False,model_ready=False,
  performance_ready=False,run_authority=False,candidate_math_changed=False,
  frozen_core_same_image_status="requires separate original evidence")
 l.publish(a.output,receipt)
 return 0 if result.wasSuccessful()else 1
if __name__=="__main__":raise SystemExit(main())

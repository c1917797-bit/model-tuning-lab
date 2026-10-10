"""Bounded source+190 focused stdlib regressions. DEFAULT-OFF; no Torch/NPU."""
import argparse,importlib.util,json,sys,time,traceback,unittest
from pathlib import Path
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 p.add_argument("--source-manifest-sha256");p.add_argument("--output",type=Path);a=p.parse_args()
 if not a.execute:print(json.dumps(dict(enabled=False,NPU=False,model_ready=False)));return 0
 here=Path(__file__).resolve().parent
 spec=importlib.util.spec_from_file_location("_kivi_firstdecode_software_loader",here/"loader.py")
 l=importlib.util.module_from_spec(spec);sys.modules[spec.name]=l;spec.loader.exec_module(l)
 m,source=l.source(a.source_manifest_sha256)
 l.need(sys.version_info[:2]==(3,12),"full native-source tests require actual same660 Python3.12 Devices[] CPU stage")
 memory=l.memory_module(m);memory_before=memory.memory(expected_limit=8*1024**3)
 memory.consume_memory(memory_before,expected_limit=8*1024**3)
 started=time.monotonic();before=set(sys.modules)
 test=l.module("_kivi_firstdecode_focused_tests",l.own(m,"test_firstdecode.py"))
 suite=unittest.defaultTestLoader.loadTestsFromModule(test)
 config_test=l.module("_kivi_firstdecode_config_tests",l.own(m,"test_native_config.py"))
 suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(config_test))
 runtime_test=l.module("_kivi_firstdecode_runtime_boundary_tests",l.own(m,"test_runtime_boundary.py"))
 suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(runtime_test))
 publication_test=l.module("_kivi_firstdecode_publication_tests",l.own(m,"test_raw_publication.py"))
 suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(publication_test))
 closure_test=l.module("_kivi_firstdecode_framework_closure_tests",l.own(m,"test_framework_closure.py"))
 suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(closure_test))
 # The real strict reader must own its fixed aliases before extension fixtures.
 # Do not clear/replace ambient modules or weaken the original source loader.
 closure_test.original_reader()
 for name in("test_provider.py","test_provider_integration.py"):
  provider_test=l.module("_kivi_firstdecode_"+name.replace(".","_"),l.own(m,name))
  suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(provider_test))
 count=suite.countTestCases();l.need(count==m["software_tests_declared"]==190,"complete registered190, no skip subset")
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 no_framework=not any(x in("torch","torch_npu","triton","numpy")or x.startswith(("torch.","torch_npu.","triton.","numpy."))for x in set(sys.modules)-before)
 memory_after=memory.memory(expected_limit=8*1024**3)
 memory.consume_memory(memory_after,expected_limit=8*1024**3,namespace_pid=memory_before["process"]["pid"])
 value=dict(schema="kivi.actual-firstdecode-software/v1",source=source,tests=count,
  python_version=list(sys.version_info[:3]),execution_profile="same660-Devices[]-CPU8",
  memory_before=memory_before,memory_after=memory_after,
  successful=result.wasSuccessful()and no_framework,NPU=False,model_ready=False,performance_ready=False,
  elapsed_seconds=time.monotonic()-started,no_framework_import=no_framework,
  scope="source closure/compile + actual own finish-wrapper/CLI/source negatives; not initialized model")
 l.publish(a.output,value);l.need(value["successful"],"full focused software failed");return 0
if __name__=="__main__":raise SystemExit(main())

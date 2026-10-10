"""Bounded source+58 focused stdlib regressions. DEFAULT-OFF; no Torch/NPU."""
import argparse,importlib.util,json,sys,time,traceback,unittest
from pathlib import Path
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 p.add_argument("--source-manifest-sha256");p.add_argument("--output",type=Path);a=p.parse_args()
 if not a.execute:print(json.dumps(dict(enabled=False,NPU=False,model_ready=False)));return 0
 here=Path(__file__).resolve().parent
 spec=importlib.util.spec_from_file_location("_kivi_firstdecode_software_loader",here/"loader.py")
 l=importlib.util.module_from_spec(spec);sys.modules[spec.name]=l;spec.loader.exec_module(l)
 m,source=l.source(a.source_manifest_sha256);started=time.monotonic();before=set(sys.modules)
 test=l.module("_kivi_firstdecode_focused_tests",l.own(m,"test_firstdecode.py"))
 suite=unittest.defaultTestLoader.loadTestsFromModule(test)
 config_test=l.module("_kivi_firstdecode_config_tests",l.own(m,"test_native_config.py"))
 suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(config_test))
 count=suite.countTestCases();l.need(count==m["software_tests_declared"]==58,"complete registered58, no skip subset")
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 no_framework=not any(x in("torch","torch_npu","triton","numpy")or x.startswith(("torch.","torch_npu.","triton.","numpy."))for x in set(sys.modules)-before)
 value=dict(schema="kivi.actual-firstdecode-software/v1",source=source,tests=count,
  successful=result.wasSuccessful()and no_framework,NPU=False,model_ready=False,performance_ready=False,
  elapsed_seconds=time.monotonic()-started,no_framework_import=no_framework,
  scope="source closure/compile + actual own finish-wrapper/CLI/source negatives; not initialized model")
 l.publish(a.output,value);l.need(value["successful"],"full focused software failed");return 0
if __name__=="__main__":raise SystemExit(main())

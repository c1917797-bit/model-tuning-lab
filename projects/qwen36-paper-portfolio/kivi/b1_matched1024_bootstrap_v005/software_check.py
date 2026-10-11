"""Complete new66 stdlib/source-body regressions. Same660 CPU8 gate or explicit local fixture mode."""
import argparse,hashlib,importlib.util,json,os,sys,time,unittest
from pathlib import Path
def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 p.add_argument("--source-manifest-sha256");p.add_argument("--output",type=Path)
 p.add_argument("--local",action="store_true");p.add_argument("--producer-archive",type=Path)
 p.add_argument("--reviewed-deps",type=Path);p.add_argument("--oracle-archive",type=Path);p.add_argument("--driver-archive",type=Path);a=p.parse_args(argv)
 if not a.execute:print(json.dumps(dict(enabled=False,NPU=False)));return 0
 here=Path(__file__).resolve().parent;sys.path.insert(0,str(here))
 import screen_contract as c,transport
 source=c.ref(here/"SOURCE_MANIFEST.json")
 c.need(source["sha256"]==a.source_manifest_sha256,"exact own complete source MF")
 m=c.read(source)
 for ref in m["files"]:
  actual=here/Path(ref["path"]).name
  c.need(c.ref(actual)==dict(ref,path=str(actual)),"all actual own bytes")
 c.need(sys.version_info[:2]==(3,12),"actual3.12 native source-body projections")
 before=set(sys.modules);memory=None;mb=None
 if a.local:
  c.need(a.producer_archive is not None and a.reviewed_deps is not None and a.oracle_archive is not None and a.driver_archive is not None,
   "explicit local source archive mapping, no remote fixture guessing")
  original=c.ref(a.producer_archive/"SOURCE_MANIFEST.json")
  c.need(original["bytes"]==c.PRODUCER["bytes"]and original["sha256"]==c.PRODUCER["sha256"],"exact original018 archive")
  os.environ["KIVI_SCREEN_PRODUCER_ARCHIVE"]=str(a.producer_archive)
  os.environ["KIVI_SCREEN_REVIEWED_DEPS"]=str(a.reviewed_deps)
  os.environ["KIVI_SCREEN_ORACLE_ARCHIVE"]=str(a.oracle_archive)
  os.environ["KIVI_SCREEN_DRIVER_ARCHIVE"]=str(a.driver_archive)
 else:
  spec=importlib.util.spec_from_file_location("_kivi_screen_software_loader",here/"loader.py")
  l=importlib.util.module_from_spec(spec);sys.modules[spec.name]=l;spec.loader.exec_module(l)
  l.source(a.source_manifest_sha256);memory=l.memory_module(m);mb=memory.memory(expected_limit=8*c.GIB)
  memory.consume_memory(mb,expected_limit=8*c.GIB)
  os.environ["KIVI_SCREEN_PRODUCER_ARCHIVE"]=str(Path(c.PRODUCER["path"]).parent)
  # Tests must resolve every inherited source by SHA in the original actual018 MF.
  os.environ["KIVI_SCREEN_ORACLE_ARCHIVE"]=m["runtime_roles"]["assignment_oracle"]["path"]
  os.environ["KIVI_SCREEN_REVIEWED_DEPS"]=str(Path(m["runtime_roles"]["bindings"]["path"]).parent)
 started=time.monotonic();suite=unittest.TestSuite()
 for name in("test_screen","test_runtime"):
  spec=importlib.util.spec_from_file_location(name,here/(name+".py"));module=importlib.util.module_from_spec(spec)
  sys.modules[name]=module;spec.loader.exec_module(module)
  suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
 count=suite.countTestCases();c.need(count==m["software_tests_declared"]==66,"complete new66, not inherited190")
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 no_framework=not any(n in("torch","torch_npu","triton","numpy")or n.startswith(("torch.","torch_npu.","triton.","numpy."))
  for n in set(sys.modules)-before)
 after=None if memory is None else memory.memory(expected_limit=8*c.GIB)
 if memory is not None:memory.consume_memory(after,expected_limit=8*c.GIB,namespace_pid=mb["process"]["pid"])
 report=dict(schema="kivi.actual-firstdecode-software/v1",source=source,tests=count,
  python_version=list(sys.version_info[:3]),execution_profile="local-source-fixtures"if a.local else"same660-Devices[]-CPU8",
  memory_before=mb,memory_after=after,successful=result.wasSuccessful()and no_framework,
  elapsed_seconds=time.monotonic()-started,no_framework_import=no_framework,NPU=False,model_ready=False,performance_ready=False,
  scope="new66 pure/source-body/file-chain tests; original018 full190 and actual full64 remain independent mandatory prerequisite")
 c.need(a.output is not None and not a.output.exists(),"exclusive original test report")
 print(json.dumps(transport.publish(a.output,report)));return 0 if report["successful"]else 1
if __name__=="__main__":raise SystemExit(main())

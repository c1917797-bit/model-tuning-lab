"""Complete C16 adapter regressions, using original mixed installer tests too.
Local/Devices[] only. No model/registry/Triton/device imports.
"""
import argparse,hashlib,importlib.util,json,os,sys,time,unittest
from pathlib import Path
PINS={"runner-94d75.py":"94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968",
 "attention_v1.py":"80005aba42bcf61247cc0d91502a0f1338194a4b38dd82bc521f6d3c84958390",
 "callback.py":"291eb417eaecf97b4199072ae62012180c18af44b5a5d2c5c92c1060e3d38f5e",
 "book.py":"c0882fa2868fa0b7e784bd031da3053d75a210362f4c955a5c93a0158fc63fa9"}
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true")
 p.add_argument("--source-manifest-sha256");p.add_argument("--output",type=Path)
 p.add_argument("--local",action="store_true");p.add_argument("--reviewed-deps",type=Path);a=p.parse_args(argv)
 if not a.execute:print(json.dumps(dict(enabled=False,NPU=False)));return 0
 here=Path(__file__).resolve().parent;sys.path.insert(0,str(here))
 import screen_contract as c,transport
 source=c.ref(here/"SOURCE_MANIFEST.json");c.need(source["sha256"]==a.source_manifest_sha256,"exact own current source")
 m=c.read(source)
 for row in m["files"]:
  actual=here/Path(row["path"]).name
  c.need(c.ref(actual)==dict(row,path=str(actual)),"complete current source byte audit")
 c.need(sys.version_info[:2]==(3,12),"same native source-body Python3.12")
 before=set(sys.modules);memory=None;mb=None
 if not a.local:
  spec=importlib.util.spec_from_file_location("_kivi_c16_software_loader",here/"loader.py")
  loader=importlib.util.module_from_spec(spec);sys.modules[spec.name]=loader;spec.loader.exec_module(loader)
  loader.source(a.source_manifest_sha256);memory=loader.memory_module(m)
  mb=memory.memory(expected_limit=8*c.GIB);memory.consume_memory(mb,expected_limit=8*c.GIB)
 class Sources:
  def __truediv__(self,name):
   digest=PINS[name]
   if name=="book.py":path=here/name
   elif a.local:
    c.need(a.reviewed_deps is not None,"explicit exact local reviewed source archive")
    path=a.reviewed_deps/name
   else:
    rows=[r for r in m["dependencies"]if r["sha256"]==digest]
    c.need(len(rows)==1,"unique actual unchanged native source dependency");path=Path(rows[0]["path"])
   c.need(hashlib.sha256(path.read_bytes()).hexdigest()==digest,"native source byte identity "+name)
   return path
 started=time.monotonic();suite=unittest.TestSuite()
 for name in("test_consumer_namespace","test_c16","test_installer_modes"):
  spec=importlib.util.spec_from_file_location(name,here/(name+".py"));mod=importlib.util.module_from_spec(spec)
  sys.modules[name]=mod;spec.loader.exec_module(mod)
  if name=="test_installer_modes":mod.DEPS=Sources()
  suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(mod))
 count=suite.countTestCases();c.need(count==m["software_tests_declared"]==48,"all33 previous plus13 namespace and2 actual frontend pin regressions")
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 no_framework=not any(n in("torch","torch_npu","triton","numpy")or n.startswith(("torch.","torch_npu.","triton.","numpy."))
  for n in set(sys.modules)-before)
 after=None if memory is None else memory.memory(expected_limit=8*c.GIB)
 if memory is not None:memory.consume_memory(after,expected_limit=8*c.GIB,namespace_pid=mb["process"]["pid"])
 value=dict(schema="kivi.actual-firstdecode-software/v1",source=source,tests=count,
  python_version=list(sys.version_info[:3]),execution_profile="local-source-fixtures"if a.local else"same660-Devices[]-CPU8",
  memory_before=mb,memory_after=after,successful=result.wasSuccessful()and no_framework,
  elapsed_seconds=time.monotonic()-started,no_framework_import=no_framework,NPU=False,model_ready=False,performance_ready=False,
  scope="C16 transport/actual-source-body/file-chain; original018190 and selected mixed numerical proof remain separate gates")
 c.need(a.output is not None and not a.output.exists(),"exclusive complete original software receipt")
 print(json.dumps(transport.publish(a.output,value)));return 0 if value["successful"]else 1
if __name__=="__main__":raise SystemExit(main())

"""Complete23 actual-source and real-file dual-source reader regressions; no device."""
import argparse,hashlib,importlib.util,io,json,sys,time,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import source_pair as p
def main(argv=None):
 a=argparse.ArgumentParser();a.add_argument("--execute",action="store_true");a.add_argument("--source-manifest-sha256")
 for n in("dense-archive","candidate-archive","reader-archive","output"):a.add_argument("--"+n,type=Path)
 x=a.parse_args(argv)
 if not x.execute:print(json.dumps(dict(enabled=False,NPU=False)));return 0
 if x.source_manifest_sha256:p.source(x.source_manifest_sha256)
 else:p.need(all(getattr(x,k)is not None for k in("dense_archive","candidate_archive","reader_archive")),"explicit local exact source archives")
 for name,ref in(("dense_archive",p.DENSE),("candidate_archive",p.CANDIDATE),("reader_archive",p.DENSE_READER)):
  root=getattr(x,name)or Path(ref["path"]).parent
  p.bytes_of(ref,lambda r:root/"SOURCE_MANIFEST.json");setattr(x,name,root)
 s=importlib.util.spec_from_file_location("_cost003_pair_tests",Path(__file__).resolve().parent/"test_pair_sources.py")
 t=importlib.util.module_from_spec(s);sys.modules[s.name]=t;s.loader.exec_module(t)
 t.OLD=x.dense_archive;t.NEW=x.candidate_archive;t.READER=x.reader_archive
 before=set(sys.modules);start=time.monotonic();suite=unittest.defaultTestLoader.loadTestsFromModule(t)
 p.need(suite.countTestCases()==23,"complete23 reader regression")
 out=io.StringIO();r=unittest.TextTestRunner(stream=out,verbosity=2).run(suite)
 clean=not any(n.split(".")[0]in("torch","torch_npu","triton","numpy")for n in set(sys.modules)-before)
 v=dict(schema="kivi.cost129-dual-source-reader-tests/v1",tests=r.testsRun,successful=r.wasSuccessful()and clean,
  errors=len(r.errors),failures=len(r.failures),skipped=len(r.skipped),seconds=time.monotonic()-start,
  python=list(sys.version_info[:3]),output=out.getvalue(),no_framework=clean,NPU=False,actual_remote_records=False)
 p.need(x.output is not None and not x.output.exists(),"exclusive test output")
 with x.output.open("x",encoding="utf8",newline="\n")as f:json.dump(v,f,indent=2);f.write("\n")
 print(json.dumps(v));return 0 if v["successful"]else 1
if __name__=="__main__":raise SystemExit(main())

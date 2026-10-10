"""Default OFF. CPU-only consumer after exact producer and raw CPU8 cleanup."""
import argparse, hashlib, importlib.util, json, os, sys, time, traceback, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def publish(path,value):
 # Exclusive non-overwrite publication; failed writes are retained.
 b=json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()+b"\n"
 if len(b)>1024**2:raise ValueError("whole consumer output cap1MiB")
 with path.open("xb")as f:
  if f.write(b)!=len(b):raise ValueError("short whole write")
  f.flush();os.fsync(f.fileno())
 return dict(path=str(path),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 p.add_argument("--mode",choices=["software","raw","consume"]);p.add_argument("--source-manifest-sha256")
 p.add_argument("--output",type=Path);p.add_argument("--producer-archive",type=Path)
 p.add_argument("--reviewed-deps",type=Path)
 for k in("result","terminal","raw-result","raw-terminal","raw-owned","raw-cleanup","raw-child","raw-owner-result","raw-phase-output"):p.add_argument("--"+k,type=Path)
 for k in("result-sha256","terminal-sha256","raw-result-sha256","raw-terminal-sha256",
           "peer","operation","expected-command","expected-args","raw-peer","raw-operation","raw-expected-command","raw-expected-args"):
  p.add_argument("--"+k)
 p.add_argument("--raw-wall-seconds",type=int,default=5400)
 a=p.parse_args(argv)
 if not a.execute:print(json.dumps(dict(default_enabled=False,NPU=False,model_ready=False,performance_ready=False)));return 0
 if not a.mode or not a.output or not a.output.is_absolute()or a.output.exists():raise ValueError("mode/new nonoverwriting output")
 mf=HERE/"SOURCE_MANIFEST.json";b=mf.read_bytes()
 if hashlib.sha256(b).hexdigest()!=a.source_manifest_sha256:raise ValueError("exact own MF")
 m=json.loads(b)
 for name,r in m["files"].items():
  q=HERE/name
  if q.stat().st_size!=r["bytes"]or hashlib.sha256(q.read_bytes()).hexdigest()!=r["sha256"]:raise ValueError("own source drift "+name)
  if name.endswith(".py"):compile(q.read_bytes(),str(q),"exec")
 core=load(HERE/"consume_whole.py","_kivi_firstdecode_independent_whole")
 report=dict(schema="kivi.actual-firstdecode-whole-entry/v1",source=core.ref(mf),successful=False,primary=None,
  model_ready=False,performance_ready=False,run_authority=False,whole176=False,NPU=False)
 started=time.monotonic()
 try:
  if a.mode=="software":
   core.need(a.producer_archive is not None,"exact local unchanged producer archive required")
   tests=load(HERE/"test_whole.py","_kivi_firstdecode_whole_tests")
   core.need(a.reviewed_deps is not None,"exact local readonly infrastructure archive required")
   tests.PRODUCER_ARCHIVE=a.producer_archive;tests.REVIEWED_DEPS=a.reviewed_deps;tests.CORE=core
   driver_tests=load(HERE/"test_driver_consumer.py","_kivi_whole012_driver_tests")
   driver_tests.CORE=core;driver_tests.PRODUCER_ARCHIVE=a.producer_archive;driver_tests.COMMON=tests
   explicit_tests=load(HERE/"test_explicit_consumer.py","_kivi_whole017_explicit_tests")
   explicit_tests.CORE=core;explicit_tests.PRODUCER_ARCHIVE=a.producer_archive;explicit_tests.COMMON=tests
   suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(tests),
    unittest.defaultTestLoader.loadTestsFromModule(driver_tests),unittest.defaultTestLoader.loadTestsFromModule(explicit_tests)])
   core.need(suite.countTestCases()==m["software_tests"],"complete software count")
   result=unittest.TextTestRunner(verbosity=2).run(suite)
   report.update(tests=suite.countTestCases(),software_only=True,producer_archive=str(a.producer_archive))
   core.need(result.wasSuccessful(),"whole consumer software failed")
  elif a.mode=="raw":
   for k in("result","terminal","result_sha256","terminal_sha256","peer","operation","expected_command","expected_args","raw_phase_output"):
    core.need(getattr(a,k)is not None,"actual completed producer and new raw phase "+k)
   ctx=core.Context(m["producer_source"])
   runner=load(HERE/"raw_cpu8.py","_kivi_firstdecode_original_CPU8_delegate")
   report["raw_owner_result"]=runner.run(a,ctx,core,started)
  else:
   core.need(a.raw_wall_seconds==5400,"full64 independent raw5400; no short-budget sampling")
   for k in("result","terminal","raw_result","raw_terminal","raw_owned","raw_cleanup","raw_child","raw_owner_result"):
    core.need(getattr(a,k)is not None,"required actual original "+k)
   ctx=core.Context(m["producer_source"])
   report["consumed"]=core.consume(a,ctx)
  report["successful"]=True
 except BaseException as e:
  report["primary"]=repr(e);report["traceback"]=traceback.format_exc()
  if a.result and a.result_sha256:
   try:
    rr=core.ref(a.result);core.need(rr["sha256"]==a.result_sha256,"original failed result SHA")
    r=core.obj(rr);report["original_first_fault"]=dict(result=rr,primary=r.get("primary"),secondary=r.get("secondary"),status=r.get("status"),
     worker_first_fault=r.get("worker_first_fault"),worker_first_fault_refs=r.get("worker_first_fault_refs"))
   except BaseException as secondary:report["first_fault_read_secondary"]=repr(secondary)
 finally:
  report["elapsed_seconds"]=time.monotonic()-started
  print(json.dumps(publish(a.output,report)),flush=True)
 return 0 if report["successful"]else 1
if __name__=="__main__":raise SystemExit(main())



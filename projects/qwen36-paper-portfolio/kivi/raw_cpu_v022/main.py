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
def failed_raw_parent(a,m):
 # producer_only may refuse before raw runner creates its new packet. Preserve
 # that original refusal without starting a container or claiming a lease.
 if a.output.parent.is_dir():return
 parent=a.output.parent;lowbit=Path(m["producer_source"]["path"]).parent.parent
 if not(a.mode=="raw"and a.raw_phase_output==parent and parent.is_absolute()
  and parent.parent==lowbit and lowbit.is_dir()and lowbit.resolve()==lowbit
  and parent.name.startswith("run-kivi-firstdecode-independent-raw-")
  and ".."not in parent.parts and not parent.exists()and not parent.is_symlink()):
  raise ValueError("failed raw publication requires exact new lowbit packet")
 parent.mkdir()
def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 p.add_argument("--mode",choices=["software","raw","consume"]);p.add_argument("--source-manifest-sha256")
 p.add_argument("--output",type=Path);p.add_argument("--producer-archive",type=Path)
 p.add_argument("--reviewed-deps",type=Path);p.add_argument("--actual-archive",type=Path)
 p.add_argument("--observation-archive",type=Path)
 p.add_argument("--peer-source-archive",type=Path)
 for k in("result","terminal","raw-result","raw-terminal","raw-owned","raw-cleanup","raw-child","raw-owner-result","raw-phase-output"):p.add_argument("--"+k,type=Path)
 for k in("result-sha256","terminal-sha256","raw-result-sha256","raw-terminal-sha256",
           "peer","operation","expected-command","expected-args","raw-peer","raw-operation","raw-expected-command","raw-expected-args"):
  p.add_argument("--"+k)
 p.add_argument("--base-whole",type=Path);p.add_argument("--joint-peer-plan",type=Path)
 p.add_argument("--raw-host-cpu",type=int);p.add_argument("--cpu-only-raw",action="store_true")
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
 if not a.base_whole:raise ValueError("exact frozen017 whole source root required")
 base=a.base_whole/"SOURCE_MANIFEST.json";bb=base.read_bytes()
 if hashlib.sha256(bb).hexdigest()!=m["base_whole"]["sha256"]or len(bb)!=m["base_whole"]["bytes"]:raise ValueError("frozen017 whole MF")
 bm=json.loads(bb)
 for name,r in bm["files"].items():
  q=a.base_whole/name
  if q.stat().st_size!=r["bytes"]or hashlib.sha256(q.read_bytes()).hexdigest()!=r["sha256"]:raise ValueError("inherited017 source drift "+name)
 sys.path.insert(0,str(HERE))
 core=load(HERE/"delegate.py","_kivi_firstdecode_independent_whole")
 core.initialize(a.base_whole)
 report=dict(schema="kivi.actual-firstdecode-whole-entry/v1",source=core.ref(mf),successful=False,primary=None,
  model_ready=False,performance_ready=False,run_authority=False,whole176=False,NPU=False)
 started=time.monotonic()
 try:
  if a.mode=="software":
   core.need(a.producer_archive is not None,"exact local unchanged producer archive required")
   tests=load(a.base_whole/"test_whole.py","_kivi_firstdecode_whole_tests")
   core.need(a.reviewed_deps is not None,"exact local readonly infrastructure archive required")
   inherited=load(a.base_whole/"consume_whole.py","_kivi_frozen017_inherited_tests")
   tests.PRODUCER_ARCHIVE=a.producer_archive;tests.REVIEWED_DEPS=a.reviewed_deps;tests.CORE=inherited;tests.ACTUAL_ARCHIVE=a.actual_archive;tests.OBSERVATION_ARCHIVE=a.observation_archive
   driver_tests=load(a.base_whole/"test_driver_consumer.py","_kivi_whole012_driver_tests")
   driver_tests.CORE=inherited;driver_tests.PRODUCER_ARCHIVE=a.producer_archive;driver_tests.COMMON=tests
   explicit_tests=load(a.base_whole/"test_explicit_consumer.py","_kivi_whole017_explicit_tests")
   explicit_tests.CORE=inherited;explicit_tests.PRODUCER_ARCHIVE=a.producer_archive;explicit_tests.COMMON=tests
   joint_tests=load(HERE/"test_cpu_raw.py","_kivi_raw_joint_tests")
   core.need(a.peer_source_archive is not None,"actual reviewed peer source archive for software")
   peer_mf=a.peer_source_archive/"SOURCE_MANIFEST.json";pb=peer_mf.read_bytes();profile=m["reviewed_peer_profile"]
   core.need(profile is not None and len(pb)==profile["source"]["bytes"]and hashlib.sha256(pb).hexdigest()==profile["source"]["sha256"],
    "actual reviewed peer MF byte identity for software")
   for key in("host_source","resources_source"):
    row=profile[key];q=a.peer_source_archive/Path(row["path"]).name
    core.need(q.stat().st_size==row["bytes"]and hashlib.sha256(q.read_bytes()).hexdigest()==row["sha256"],"actual peer software method source "+key)
   joint_tests.PRODUCER_ARCHIVE=a.producer_archive
   joint_tests.PEER_ARCHIVE=a.peer_source_archive
   joint_tests.BASE_WHOLE=a.base_whole;joint_tests.REVIEWED_DEPS=a.reviewed_deps
   suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(joint_tests),unittest.defaultTestLoader.loadTestsFromModule(tests),
    unittest.defaultTestLoader.loadTestsFromModule(driver_tests),unittest.defaultTestLoader.loadTestsFromModule(explicit_tests)])
   core.need(suite.countTestCases()==m["software_tests"],"complete software count")
   result=unittest.TextTestRunner(verbosity=2).run(suite)
   report.update(tests=suite.countTestCases(),software_only=True,producer_archive=str(a.producer_archive))
   core.need(result.wasSuccessful(),"whole consumer software failed")
  elif a.mode=="raw":
   for k in("result","terminal","result_sha256","terminal_sha256","peer","operation","expected_command","expected_args","raw_phase_output"):
    core.need(getattr(a,k)is not None,"actual completed producer and new raw phase "+k)
   core.need(a.cpu_only_raw and a.joint_peer_plan is not None and a.raw_host_cpu is not None,"explicit CPU-only raw mode and actual resource-plan inputs")
   ctx=core.Context(m["producer_source"])
   runner=load(HERE/"raw_cpu8.py","_kivi_firstdecode_original_CPU8_delegate")
   report["raw_owner_result"]=runner.run(a,ctx,core,started)
  else:
   core.need(a.raw_wall_seconds==5400,"full64 independent raw5400; no short-budget sampling")
   for k in("result","terminal","raw_result","raw_terminal","raw_owned","raw_cleanup","raw_child","raw_owner_result"):
    core.need(getattr(a,k)is not None,"required actual original "+k)
   ctx=core.Context(m["producer_source"])
   ctx=core.cpu_context(ctx,core.obj(core.ref(a.raw_owned)),core.obj(core.ref(a.raw_owner_result)))
   report["consumed"]=core.consume(a,ctx)
  report["successful"]=True
 except BaseException as e:
  report["primary"]=repr(e);report["traceback"]=traceback.format_exc()
  if "QUEUE_RAW:"in repr(e):report["scheduling_status"]="QUEUE_RAW_NO_DEVICE_LEASE"
  if a.result and a.result_sha256:
   try:
    rr=core.ref(a.result);core.need(rr["sha256"]==a.result_sha256,"original failed result SHA")
    r=core.obj(rr);report["original_first_fault"]=dict(result=rr,primary=r.get("primary"),secondary=r.get("secondary"),status=r.get("status"),
     worker_first_fault=r.get("worker_first_fault"),worker_first_fault_refs=r.get("worker_first_fault_refs"))
   except BaseException as secondary:report["first_fault_read_secondary"]=repr(secondary)
 finally:
  report["elapsed_seconds"]=time.monotonic()-started
  if not report["successful"]:failed_raw_parent(a,m)
  print(json.dumps(publish(a.output,report)),flush=True)
 return 0 if report["successful"]else 1
if __name__=="__main__":raise SystemExit(main())

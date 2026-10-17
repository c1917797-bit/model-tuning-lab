"""One real Devices[] measurement child; not the DL model or its math suite."""
import argparse,hashlib,importlib.util,json,os,sys,time,traceback,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
def checked(r):
 assert type(r)is dict and set(r)=={'path','bytes','sha256'};p=Path(r['path']);assert p.is_absolute()and p.is_file()and not any(q.is_symlink()for q in(p,*p.parents));b=p.read_bytes();assert(len(b),hashlib.sha256(b).hexdigest())==(r['bytes'],r['sha256']);return p
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 sr=json.loads(a.source_ref);m=json.loads(checked(sr).read_bytes());assert m['schema']=='deltalog.measurement-source/v22'and m['prepared_only']is False and m['root']==str(P)
 for r in m['files'].values():checked(r)
 assert sys.platform=='linux'and not list(Path('/dev').glob('davinci*'))and os.environ['ASCEND_RT_VISIBLE_DEVICES']==''
 start=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19]
 identity=dict(source=sr,pid=os.getpid(),start_ticks=start,cgroup=Path('/proc/self/cgroup').read_text(),pid_namespace=os.readlink('/proc/self/ns/pid'))
 with(a.output/'CHILD_IDENTITY.json').open('x',encoding='utf8')as f:json.dump(identity,f);f.flush();os.fsync(f.fileno())
 until=time.monotonic()+20
 while not(a.output/'MAIN_ARM.json').exists():
  if time.monotonic()>=until:raise TimeoutError('host PID/start/CID namespace join20s')
  time.sleep(.05)
 arm=json.loads((a.output/'MAIN_ARM.json').read_bytes());assert arm==dict(source=sr,guest_pid=identity['pid'],start_ticks=start)
 primary=None;report=None
 try:
  import test_measurement_contract as M,test_readonly_binder_guard as G
  suite=unittest.TestSuite([M.Controls('test_global_mock_breaks_real_symlink_resolution_narrow_mock_preserves'),M.Controls('test_current_mm_HWM_parser_contract_not_arbitrary_threshold_change'),G.GuardControls('test_exact_program_exe_and_stable_process_identity')])
  result=unittest.TextTestRunner(verbosity=2).run(suite);assert result.wasSuccessful()and result.testsRun==3 and not result.skipped
  import diagnose_measurement_r22 as D
  argv=sys.argv;sys.argv=[str(P/'diagnose_measurement_r22.py'),'--execute','--output',str(a.output/'MEASUREMENT.json')]
  try:assert D.main()==0
  finally:sys.argv=argv
  report=json.loads((a.output/'MEASUREMENT.json').read_bytes())
 except BaseException as e:primary=repr(e);report=dict(traceback=traceback.format_exc())
 value=dict(schema='deltalog.measurement-only-complete/v22',source=sr,primary=primary,report=report,Devices=[],NPU=False,qualified=False,old_R21_failure_unchanged=True,measurement_contract_changed=False)
 with(a.output/'ATTRIBUTION.json').open('x',encoding='utf8',newline='\n')as f:json.dump(value,f,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
 return 0 if primary is None else 3
if __name__=='__main__':raise SystemExit(main())

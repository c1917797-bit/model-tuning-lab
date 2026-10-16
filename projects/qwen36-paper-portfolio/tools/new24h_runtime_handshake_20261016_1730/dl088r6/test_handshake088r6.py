import ast,importlib.util,json,sys,tempfile,threading,time,types,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
from storage_watch088r6 import Watch

class ArmWritten(Exception):pass
class NoProof(Exception):pass

def actual_wait(namespace):
 tree=ast.parse((P/'host.py').read_text(encoding='utf-8'))
 node=next(n for n in ast.walk(tree)if isinstance(n,ast.FunctionDef)and n.name=='wait_ge')
 module=ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[]))
 exec(compile(module,str(P/'host.py')+'#actual-wait-ge','exec'),namespace)
 return namespace['wait_ge']

class Tests(unittest.TestCase):
 def route(self,proof=True,exit_code=None,checker=None):
  entered=threading.Event();release=threading.Event();events=[]
  def slow(root):entered.set();release.wait(3)
  def checked(root):
   entered.set()
   if checker is not None:return checker(root)
   return slow(root)
  check=checked
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);child=root/'result';child.mkdir();(child/'DEVICE.json').write_text('{}')
   cid='a'*64;pr={'path':'/actual/PLAN.json','bytes':1,'sha256':'b'*64}
   dv=dict(stat='1 (python) '+' '.join(['0']*19+['123']),pid=1,logical=0,physical=5,visible='0',plan=pr,canary=[4.,5.],cgroup=cid)
   owned=dict(physical=5,namespace_pids=[12,1],start_ticks=123,cgroup=cid,argv=['exact'])
   count=[0]
   def observe(*args,**kwargs):
    count[0]+=1
    if count[0]>2:raise NoProof('no fabricated ownership')
    return dict(owned_process_proofs=[owned]if proof and count[0]>1 else[])
   lane=types.SimpleNamespace(create=lambda stage:child,active=cid,output=root,plan_ref=pr,expected_child_argv=['exact'],observe=observe,a=types.SimpleNamespace(run_root=root))
   lane.inspect=lambda cid:({},dict(State=dict(Running=exit_code is None,ExitCode=exit_code)))
   def write(p,value):
    events.append((p.name,value))
    if p.name=='MAIN_ARM.json':raise ArmWritten()
   def need(v,msg):
    if not v:raise ValueError(msg)
   ns=dict(time=time,storage=types.SimpleNamespace(check=check),a=types.SimpleNamespace(output=root,physical_device=5),write=write,need=need,obj=lambda r:dv,ref=lambda p:{},terminal=types.SimpleNamespace(files=lambda p:{},recover=lambda *a:None),runroot=root)
   call=actual_wait(ns);started=time.monotonic()
   try:
    with self.assertRaises(ValueError if checker is not None or exit_code is not None else ArmWritten if proof else NoProof):call(lane,'numeric')
    if exit_code is None:self.assertTrue(entered.wait(1))
    if proof and exit_code is None and checker is None:
     self.assertLess(time.monotonic()-started,1.5);self.assertFalse(release.is_set())
     self.assertEqual([n for n,v in events],['ACTUAL_OWNER.json','MAIN_ARM.json'])
    else:self.assertNotIn('MAIN_ARM.json',[n for n,v in events])
    if exit_code is not None:
     self.assertEqual(events[0][0],'unarmed-child-exit.json');self.assertEqual(events[0][1]['state']['ExitCode'],exit_code)
   finally:
    release.set()
    if hasattr(lane,'storage_watch'):lane.storage_watch.close(time.monotonic()+2)
 def test_real_wait_slow_storage_and_stale_empty_smi_then_real_proof(self):self.route()
 def test_real_wait_no_smi_proof_never_arm(self):self.route(proof=False)
 def test_real_wait_unarmed_original_child_failure_retained(self):self.route(exit_code=1)
 def test_real_wait_storage_failure_never_arm(self):
  def fail(root):raise ValueError('actual storage fullcheck refused')
  with self.assertRaisesRegex(ValueError,'actual storage fullcheck refused'):
   # close re-raises the same sticky failure, outside route's assertion.
   self.route(checker=fail)
 def test_storage_exception_sticky(self):
  done=threading.Event()
  def fail(root):done.set();raise ValueError('closed mutation actual guard')
  w=Watch(fail,'/read-only');w.start();self.assertTrue(done.wait(1))
  for _ in range(2):
   with self.assertRaisesRegex(ValueError,'closed mutation'):w.check()
  with self.assertRaisesRegex(ValueError,'closed mutation'):w.close(time.monotonic()+1)
 def test_join_bounded_and_daemon(self):
  release=threading.Event();entered=threading.Event()
  def wait(root):entered.set();release.wait(2)
  w=Watch(wait,'/read-only');w.start();self.assertTrue(entered.wait(1));self.assertTrue(w._thread.daemon)
  try:
   with self.assertRaisesRegex(ValueError,'original cleanup deadline'):w.close(time.monotonic()+.01)
  finally:release.set();w.close(time.monotonic()+1)
 def test_producer_math_and_original_storage_all_bytes(self):
  old=P.parent/'deltalog-sameinitial-native-contract-new24h-088-repair5'
  for n in ('producer.py','consumer088.py','capture088.py','oracle.py','preregister.py','storage061.py','storage_bridge121.py','sealed_storage069.py'):
   self.assertEqual((P/n).read_bytes(),(old/n).read_bytes(),n)

if __name__=='__main__':unittest.main()

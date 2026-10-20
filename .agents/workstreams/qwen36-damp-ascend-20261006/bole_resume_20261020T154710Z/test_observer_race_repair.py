"""CPU-only observer race classification, never a device-admission proof."""
import errno,json,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
import observer_race_repair as R
import sourceio as C

class Tests(unittest.TestCase):
 def scenario(self,*,fresh=(),kind='protected',alive=False,error_path='/proc/999999999/stat'):
  td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);root=Path(td.name)
  class Controller:
   def observe(self,label,initial=False,cleanup=False):
    self.observed+=1
    if self.observed==1:
     C.write(root/'smi-1.json',dict(stdout='stale'))
     if kind=='foreign':raise ValueError('real foreign PID/UDA/start/program conflict')
     raise FileNotFoundError(errno.ENOENT,'gone',error_path)
    return dict(original_observer_reexecuted=True,initial=initial,cleanup=cleanup)
   def call(self,label,argv,cleanup=False):
    self.calls.append((label,argv,cleanup))
    q=C.write(root/'refresh.json',dict(stdout='fresh'))
    return C.obj(q),q
  def rows(text):return [(0,0,999999999)]if text=='stale'else list(fresh)
  S=types.SimpleNamespace(Controller=Controller,SMI='/usr/local/sbin/npu-smi')
  R.install(S,C);obj=Controller();obj.out=root;obj.observed=0;obj.calls=[]
  obj.h=types.SimpleNamespace(legacy=lambda:types.SimpleNamespace(process_rows=rows))
  return obj,root
 def test_proved_exit_keeps_stale_and_fresh_and_reexecutes_original_once(self):
  obj,root=self.scenario()
  with patch.object(R,'alive',return_value=False):
   result=obj.observe('startup',initial=True)
  self.assertEqual(result,dict(original_observer_reexecuted=True,initial=True,cleanup=False))
  self.assertEqual(obj.observed,2);self.assertEqual(len(obj.calls),1)
  proofs=list(root.glob('protected-pid-race-*.json'));self.assertEqual(len(proofs),1)
  value=json.loads(proofs[0].read_bytes());self.assertEqual(value['retry_count'],1)
  self.assertTrue(C.checked(value['stale_smi']).exists());self.assertTrue(C.checked(value['fresh_smi']).exists())
 def test_snapshot_still_reports_pid_is_rejected(self):
  obj,root=self.scenario(fresh=[(0,0,999999999)])
  with patch.object(R,'alive',return_value=False),self.assertRaisesRegex(ValueError,'both prove'):
   obj.observe('startup')
  self.assertEqual(obj.observed,1);self.assertFalse(list(root.glob('protected-pid-race-*.json')))
 def test_reused_or_live_proc_identity_is_rejected(self):
  obj,root=self.scenario()
  with patch.object(R,'alive',return_value=True),self.assertRaisesRegex(ValueError,'both prove'):
   obj.observe('startup')
  self.assertEqual(obj.observed,1)
 def test_real_foreign_target_conflict_never_retried(self):
  obj,root=self.scenario(kind='foreign')
  with self.assertRaisesRegex(ValueError,'real foreign'):obj.observe('startup')
  self.assertEqual(obj.observed,1);self.assertEqual(obj.calls,[])
 def test_unrelated_missing_file_never_retried(self):
  obj,root=self.scenario(error_path='/tmp/not-a-proc-source')
  with self.assertRaises(FileNotFoundError):obj.observe('startup')
  self.assertEqual(obj.observed,1);self.assertEqual(obj.calls,[])
if __name__=='__main__':unittest.main()


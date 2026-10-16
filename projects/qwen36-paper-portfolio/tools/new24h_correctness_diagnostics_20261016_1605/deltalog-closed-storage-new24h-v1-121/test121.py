import copy,importlib.util,json,subprocess,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import sealed121 as S
class Tests(unittest.TestCase):
 def plan(self):return dict(target_source_ref=dict(path='/actual/source',bytes=1,sha256='0'*64),phases=[dict(cid='a'*64),dict(cid='b'*64)])
 def states(self):return[dict(Id=c*64,State=dict(Status='exited',Running=False,Pid=0,OOMKilled=False,ExitCode=e),ExecIDs=None)for c,e in(('a',0),('b',137))]
 def test_exact_interrupted_not_numeric_success(self):S.states_check(self.states(),self.plan())
 def test_rejects_live_oom_exec_wrong_exit_and_cid(self):
  for field,value in [('Pid',1),('Running',True),('OOMKilled',True),('ExitCode',0)]:
   v=self.states();v[1]['State'][field]=value
   with self.assertRaises(ValueError):S.states_check(v,self.plan())
  for change in('cid','exec','missing'):
   v=self.states()
   if change=='cid':v[1]['Id']='c'*64
   elif change=='exec':v[1]['ExecIDs']=['unknown']
   else:v.pop()
   with self.assertRaises(ValueError):S.states_check(v,self.plan())
 def test_actual_canonical_function_two_phase_inverse_and_no_writer_call(self):
  path=P/'canonical119.py';m=S.load(S.ref(path),'_test121_real119');q=S.scoped(m,self.plan())
  def paths(*args):return types.SimpleNamespace(iterdir=lambda:[])if args==('/proc',)else Path(*args)
  with patch.dict(q.no_writers.__globals__,Path=paths):v=q.no_writers()
  self.assertTrue(v['no_original_commands']);self.assertEqual(v['processes_examined'],0)
  self.assertEqual(q.inspect_all.__code__,m.inspect_all.__code__)
 def test_exact_ref_missing_or_mutation_rejected(self):
  r=S.ref(P/'canonical119.py');r['sha256']='0'*64
  with self.assertRaises(ValueError):S.read(r)
  with self.assertRaises(ValueError):S.ref(P/'no-such-file')
 def test_cold_real_cli_default_off(self):
  x=subprocess.run([sys.executable,'-I','-B',str(P/'sealed121.py')],capture_output=True,text=True,timeout=10);self.assertEqual(x.returncode,0);self.assertFalse(json.loads(x.stdout)['enabled'])
 def test_cold_ON_unknown_actual_source_ref_refused(self):
  x=subprocess.run([sys.executable,'-I','-B',str(P/'sealed121.py'),'--execute','--mode','bind','--source-ref','{}'],capture_output=True,text=True,timeout=10);self.assertNotEqual(x.returncode,0);self.assertNotIn('docker',x.stdout)
 def test_exact_actual_snapshot_not_old_seal12(self):
  v=S.observed();self.assertTrue(v['latest_ledger']['ref']['path'].endswith('STORAGE_LEDGER061.14.json'));self.assertEqual(v['latest_ledger']['ref']['sha256'],'a332cf4fb73f311d51db7b9c414a35f850c7192055200db57738086220bc0487');self.assertEqual(len(v['phase_refs']),10)
  failed=[x['projection']for x in v['phase_refs']if x['phase']=='numeric16'and x['relative_path']=='RESULT.json'][0]
  self.assertEqual(failed['primary'],"ValueError('foreign physical4..7 process/cgroup')");self.assertTrue(failed['secondary']);self.assertIsNone(failed['independent_consumer'])
 def test_missing_or_changed_baseline_cannot_bind_new_generation(self):
  p=dict(schema='deltalog.closed-storage-plan/v121',prior_source_ref=S.PRIOR,target_template_ref=S.TARGET_TEMPLATE,baseline_ledger_ref=dict(path='/not14',bytes=1,sha256='0'*64))
  with patch.object(S,'read',return_value=p):
   with self.assertRaisesRegex(ValueError,'highest14'):S.verify_plan({})
if __name__=='__main__':unittest.main()

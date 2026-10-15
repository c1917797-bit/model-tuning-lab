import ast,copy,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
import bridge_io as C,entry as E,host as H
class Tests(unittest.TestCase):
 def test_actual_entry_argv_exact_source_and_no_original_consumer(self):
  m=dict(files={'diagnose.py':C.ref(P/'diagnose.py')},original_source_ref={'source':'source-only'},original_producer_ref={'producer':'source-only'})
  a=E.diagnostic_argv(m,P)
  self.assertEqual(a[:5],[sys.executable,'-I','-B',str(P/'diagnose.py'),'--execute'])
  self.assertEqual(json.loads(a[a.index('--source-ref')+1]),m['original_source_ref'])
  self.assertEqual(json.loads(a[a.index('--producer-ref')+1]),m['original_producer_ref'])
  self.assertNotIn('consume_pair.py',' '.join(a))
  m['files']['diagnose.py']=dict(m['files']['diagnose.py'],sha256='0'*64)
  with self.assertRaises(ValueError):E.diagnostic_argv(m,P)
 def test_actual_entry_accepts_failed_predicates_only_as_diagnostic(self):
  m=dict(original_source_ref={'a':1},original_producer_ref={'b':2})
  v=dict(schema='deltalog.saved-sidecar-predicate-diagnostic/v1',source=m['original_source_ref'],producer=m['original_producer_ref'],diagnostic_complete=True,rows=[{'original_predicate_pass':False}]*57)
  v.update({k:False for k in('NPU_reexecuted','numeric16_qualified','numeric160_qualified','model_ready','performance_ready','task_ready')})
  E.validate_diagnosis(m,v)
  for k in('model_ready','numeric16_qualified'):
   bad=dict(v);bad[k]=True
   with self.assertRaises(ValueError):E.validate_diagnosis(m,bad)
  bad=dict(v,producer={'wrong':1})
  with self.assertRaises(ValueError):E.validate_diagnosis(m,bad)
 def test_exact_codec_load_and_install_precede_raw_load(self):
  t=ast.parse((P/'diagnose.py').read_text());calls=[(x.lineno,ast.unparse(x))for x in ast.walk(t)if isinstance(x,ast.Call)]
  install=[n for n,s in calls if s=='codec.install(torch)'];loads=[n for n,s in calls if s.startswith('torch.load(')]
  self.assertTrue(install and loads);self.assertLess(install[0],min(loads))
 def test_actual_target_closure_mounts_all_newfiles_and_rawrefs(self):
  t=ast.parse((P/'host.py').read_text());f=next(x for x in t.body if isinstance(x,ast.FunctionDef)and x.name=='target_closure')
  text=ast.unparse(f)
  self.assertIn("m['files'].values()",text);self.assertIn("m['recovery_refs']",text)
  self.assertIn("m['files']['diagnose.py']",(P/'entry.py').read_text())
 def test_real_isolated_entry_and_diagnostic_OFF(self):
  for n in('entry.py','diagnose.py'):
   r=subprocess.run([sys.executable,'-I','-B',str(P/n)],capture_output=True,text=True,timeout=20)
   self.assertEqual(r.returncode,0,r.stderr);self.assertIn('disabled',r.stdout)
if __name__=='__main__':unittest.main()

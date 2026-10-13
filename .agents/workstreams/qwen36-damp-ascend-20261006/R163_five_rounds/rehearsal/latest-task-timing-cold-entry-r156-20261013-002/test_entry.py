import importlib.util,json,subprocess,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
def mod():
 s=importlib.util.spec_from_file_location('_timing_cold_control',P/'entry.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Controls(unittest.TestCase):
 def test01_real_defaultOFF_process(self):
  r=subprocess.run([sys.executable,'-I','-B',str(P/'entry.py')],capture_output=True,text=True);self.assertEqual(r.returncode,0);self.assertEqual(json.loads(r.stdout),dict(enabled=False,actual_ETA='unmeasured'))
 def test02_real_original_modules_and_full_source_cold(self):
  r=mod().ref(P/'SOURCE_MANIFEST.json');c=subprocess.run([sys.executable,'-I','-B',str(P/'entry.py'),'--entry-source-sha256',r['sha256'],'--cold-source-only'],capture_output=True,text=True);self.assertEqual(c.returncode,0,c.stderr);v=json.loads(c.stdout);self.assertEqual(v['status'],'ACTUAL_ORIGINAL_TIMING_COLD_LOADED');self.assertFalse(v['full_start_admitted']);self.assertEqual(v['actual_ETA'],'unmeasured')
 def test03_exact_full_original_args_preserved(self):
  M=mod();a=['--estimate','--source-sha256','TASK_SHA','--dense-ref-json','D','--candidate-ref-json','C','--inputs-ref-json','I','--overhead-seconds','1800','--safety-factor','2','--output','O'];self.assertIs(M.validate_args(a),a)
 def test04_missing_complete_smoke_inputs(self):
  with self.assertRaises(ValueError):mod().validate_args(['--estimate','--source-sha256','S'])
 def test05_duplicate_original_flag(self):
  with self.assertRaises(ValueError):mod().validate_args(['--source-sha256','S','--source-sha256','T'])
 def test06_flag_value_cannot_be_another_flag(self):
  with self.assertRaises(ValueError):mod().validate_args(['--dense-ref-json','--output','O'])
 def test07_unknown_injected_flag(self):
  with self.assertRaises(ValueError):mod().validate_args(['--admitted','true'])
 def test08_wrong_new_pin_cold_rejected(self):
  c=subprocess.run([sys.executable,'-I','-B',str(P/'entry.py'),'--entry-source-sha256','0'*64,'--cold-source-only'],capture_output=True,text=True);self.assertNotEqual(c.returncode,0);self.assertIn('new cold-entry source pin',c.stderr)
 def test09_foreign_loaded_modules_rejected(self):
  M=mod();old=sys.modules.get('core');sys.modules['core']=object()
  try:
   with self.assertRaisesRegex(ValueError,'foreign preloaded'):M.boot(M.ref(P/'SOURCE_MANIFEST.json')['sha256'])
  finally:
   if old is None:sys.modules.pop('core',None)
   else:sys.modules['core']=old
 def test10_no_windows_actual_estimate(self):
  c=subprocess.run([sys.executable,'-I','-B',str(P/'entry.py'),'--entry-source-sha256',mod().ref(P/'SOURCE_MANIFEST.json')['sha256'],'--estimate','--source-sha256','S','--dense-ref-json','D','--candidate-ref-json','C','--inputs-ref-json','I','--overhead-seconds','1800','--output','O'],capture_output=True,text=True);self.assertNotEqual(c.returncode,0);self.assertIn('actual ETA requires Linux original window/reports',c.stderr)
if __name__=='__main__':unittest.main()

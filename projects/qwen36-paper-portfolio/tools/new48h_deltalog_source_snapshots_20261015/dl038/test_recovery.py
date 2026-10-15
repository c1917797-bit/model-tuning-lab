import ast,pathlib,subprocess,sys,unittest
from top_child_diagnostic import departed
P=pathlib.Path(__file__).resolve().parent
class Controls(unittest.TestCase):
 def test_original035_consumer_no_math_copy(self):
  text=(P/'entry.py').read_text();self.assertIn("consumer=original['files']['consume_pair.py']",text);self.assertNotIn('R.advance',text);self.assertIn("len(producer['records'])==40",text)
 def test_original_failure_preserved(self):
  text=(P/'entry.py').read_text();self.assertIn("failed['primary']is not None",text);self.assertIn('numeric160_qualified=False',text);self.assertIn('numeric16_qualified=False',text)
 def test_original_budget_and_cpu_only(self):
  text=(P/'host.py').read_text();self.assertIn("choices=('cpu',)",text);self.assertIn('a.lease_seconds=720',text);self.assertIn('time.monotonic()+90',text);self.assertIn("'--memory=8g'",text)
 def test_transient_departure_preserved(self):self.assertFalse(departed(12,10,10,{10},{10},[dict(status='missing')]*2,set(),set())['protected_boundary_waived'])
 def test_live_unreadable_reject(self):
  for status in('live','permission','reused'):
   with self.assertRaises(ValueError):departed(12,10,10,{10},{10},[dict(status=status)]*2,set(),set())
 def test_cold_default_off_real_cli(self):
  r=subprocess.run([sys.executable,'-I','-B',str(P/'host.py')],capture_output=True,text=True);self.assertEqual(r.returncode,0);self.assertIn('disabled',r.stdout)
 def test_py_parse(self):
  for p in P.glob('*.py'):ast.parse(p.read_bytes())
if __name__=='__main__':unittest.main()

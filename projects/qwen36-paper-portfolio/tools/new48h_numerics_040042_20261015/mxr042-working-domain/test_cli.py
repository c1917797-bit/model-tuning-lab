import importlib.util,subprocess,sys,json,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
class CLI(unittest.TestCase):
 def test_default_off_all(self):
  for name in('select_frames.py','closure.py','replay.py','consume.py'):
   v=subprocess.run([sys.executable,'-I','-B',str(P/name)],capture_output=True,text=True,check=True)
   self.assertEqual(json.loads(v.stdout),dict(enabled=False,NPU=False))
 def test_wrong_report_source_before_IO(self):
  s=importlib.util.spec_from_file_location('_selection',P/'select_frames.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
  with self.assertRaisesRegex(ValueError,'pin'):m.select(dict(sha256='wrong'))
if __name__=='__main__':unittest.main()

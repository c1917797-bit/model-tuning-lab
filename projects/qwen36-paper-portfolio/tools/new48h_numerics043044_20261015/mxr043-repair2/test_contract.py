"""Six new controls; no historical test count and no device imports."""
import ast,importlib.util,json,os,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
def load(n):
 s=importlib.util.spec_from_file_location('_once007_'+n[:-3],P/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Contract(unittest.TestCase):
 def test_default_off(self):
  before=set(__import__('sys').modules);w=load('worker.py')
  with unittest.mock.patch.dict(os.environ,{'MXR_ONCE_CORRECTNESS_ENABLE':'0'}):self.assertIsNone(w.install())
  self.assertFalse(any(x=='torch'or x.startswith(('torch.','torch_npu','vllm'))for x in set(__import__('sys').modules)-before))
 def test_arm_absent(self):
  with tempfile.TemporaryDirectory()as d:self.assertIsNone(load('worker.py').read_arm(Path(d),'owned'))
 def test_arm_actual(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'ARM.json').write_text(json.dumps(dict(schema='mxr.capture.arm/v1',run_id='owned')))
   self.assertEqual(load('worker.py').read_arm(p,'owned')['run_id'],'owned')
 def test_arm_wrong_run(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'ARM.json').write_text(json.dumps(dict(schema='mxr.capture.arm/v1',run_id='foreign')))
   with self.assertRaises(ValueError):load('worker.py').read_arm(p,'owned')
 def test_arm_extra_or_malformed(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'ARM.json').write_text('{"schema":"mxr.capture.arm/v1","run_id":"owned","extra":true}')
   with self.assertRaises(ValueError):load('worker.py').read_arm(p,'owned')
   (p/'ARM.json').write_text('{broken')
   with self.assertRaises(ValueError):load('worker.py').read_arm(p,'owned')
 def test_once_route(self):
  t=ast.parse((P/'worker.py').read_text());text=ast.unparse(t)
  self.assertIn('safe_eager.eager = observed',text);self.assertNotIn('chunk.solve_tril =',text)
  self.assertIn("runtime['counts']['candidate'] - before == 1",text)
  self.assertIn("read_arm(root, run_id)",text)
if __name__=='__main__':
 import unittest.mock
 unittest.main()

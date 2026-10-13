"""Private binding code/data controls; no live closure or resource approval."""
import ast,hashlib,importlib.util,json,os,subprocess,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('_mxr035_controls',P/'binding.py');B=importlib.util.module_from_spec(s);s.loader.exec_module(B)
ROOT36=Path(os.environ.get('MXR036_TEST_ROOT',str(P.parent/'mxr-r156-diag16-numeric-binding-20261013-039')))
class Controls(unittest.TestCase):
 def test01_defaults(self):
  for path in(P/'host.py',ROOT36/'host.py'):
   r=subprocess.run([sys.executable,'-I','-B',str(path)],capture_output=True,text=True,timeout=5);self.assertEqual(r.returncode,0,r.stderr);self.assertFalse(json.loads(r.stdout)['enabled'])
 def test02_actual030_function_code_preserved(self):
  p=Path(os.environ['MXR035_DONOR030']);ref=dict(path=str(p),bytes=9447,sha256='9afe435ff2c1c18c22b33b56398777f3ab1d37a3e3223bfd8c944c99232cd136');raw=B.load(ref,'_mxr035_plain030');v=B.view('build',P,ref)
  self.assertEqual(raw.main.__code__,v.main.__code__);self.assertEqual(v.P,P);self.assertEqual((v.START,v.CUT,v.PHASE),(1791916056,1792002456,450))
 def test03_actual031_function_code_preserved(self):
  p=Path(os.environ['MXR035_DONOR031']);ref=dict(path=str(p),bytes=11330,sha256='63687e5c1ba0ed33b3adc14e16cc767817a3384edde392d8c319a60a990858f4');raw=B.load(ref,'_mxr035_plain031');v=B.view('numeric',ROOT36,ref)
  for name in('main','devices','configure','verify'):self.assertEqual(getattr(raw,name).__code__,getattr(v,name).__code__)
  self.assertEqual(v.devices(None),{});self.assertEqual(v.devices(5)['/dev/davinci5'],'/dev/davinci0');self.assertEqual((v.CUT,v.PHASE),(1792002456,300))
 def test04_exact_donor_not_arbitrary(self):
  p=Path(os.environ['MXR035_DONOR030'])
  with self.assertRaises(ValueError):B.load(dict(path=str(p),bytes=9447,sha256='0'*64),'foreign')
 def test05_source_includes_actual_software_cut_boundary(self):
  text=(P/'binding.py').read_text();self.assertIn("name=='_mxr026_exact023_preparer'",text);self.assertIn('C=result[2]',text);self.assertIn('C.CUTOFF==1791922930',text);self.assertIn('C.CUTOFF=CUT',text);self.assertNotIn('class Joint',text);self.assertNotIn('class Owned',text)
 def test06_synthetic_meta_shared_C_clock_and_owner(self):
  for stage,phase in(('build',450),('numeric',300)):
   C=types.SimpleNamespace(CUTOFF=B.CUT,PHASE=phase,CLEANUP=90,labels=lambda:None,create_argv=lambda:None,inspect_owned=lambda:None);joint=type('Joint',(),{'__init__':lambda self:None});env=dict(Joint=joint,controller=lambda unused:None);joint.__init__.__globals__['C']=C;env['controller'].__globals__['C']=C
   A=types.SimpleNamespace(load=lambda *unused:None,prepare=lambda *unused:({},None,[],C,env,None,None))
   with patch.object(B,'load',return_value=A):v=B.view(stage,P,None)
   result=v.prepare(None,0);self.assertIs(result[3],C);self.assertIn('mxr-r156-diag16-',C.OWNER);self.assertEqual(C.ROOT,P)
 def test07_bounds_failclosed(self):
  C=types.SimpleNamespace(CUTOFF=1791922930,PHASE=300,CLEANUP=90);A=types.SimpleNamespace(load=lambda *unused:None,prepare=lambda *unused:({},None,[],C,{},None,None))
  with patch.object(B,'load',return_value=A):v=B.view('numeric',ROOT36,None)
  with self.assertRaises(ValueError):v.prepare(None,0)
 def test08_AST_no_runtime(self):
  for path in(P/'binding.py',P/'host.py',P/'test_binding.py',ROOT36/'host.py'):ast.parse(path.read_bytes(),str(path))
  self.assertNotIn('torch',sys.modules);self.assertNotIn('torch_npu',sys.modules)
if __name__=='__main__':unittest.main(verbosity=2)

"""Fresh process/control source regression. No fake hardware qualification."""
import ast,hashlib,importlib.util,json,subprocess,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
def load(p,name):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
class Entry(unittest.TestCase):
 def test01_all_compile(self):
  for p in P.glob('*.py'):compile(p.read_bytes(),str(p),'exec',dont_inherit=True)
 def test02_host_cold_OFF(self):
  r=subprocess.run([sys.executable,'-I','-B',str(P/'host.py')],capture_output=True,text=True);self.assertEqual(r.returncode,0);self.assertEqual(json.loads(r.stdout),dict(default_enabled=False,NPU=False))
 def test03_guest_cold_OFF(self):
  r=subprocess.run([sys.executable,'-I','-B',str(P/'guest.py')],capture_output=True,text=True);self.assertEqual(r.returncode,0);self.assertEqual(json.loads(r.stdout),dict(default_enabled=False,NPU=False))
 def test04_consume_cold_OFF(self):
  r=subprocess.run([sys.executable,'-I','-B',str(P/'consume.py')],capture_output=True,text=True);self.assertEqual(r.returncode,0);self.assertEqual(json.loads(r.stdout),dict(default_enabled=False,NPU=False))
 def test05_missing_source_rejected(self):
  for n in('host.py','guest.py','consume.py'):
   r=subprocess.run([sys.executable,'-I','-B',str(P/n),'--execute'],capture_output=True,text=True);self.assertNotEqual(r.returncode,0);self.assertNotIn('torch_npu',r.stderr)
 def test06_foreign_module_rejected(self):
  C=load(P/'common.py','_vector_test_common');r=C.ref(P/'writer.py');sys.modules['_forbidden_vector']=object()
  try:
   with self.assertRaises(ValueError):C.load('_forbidden_vector',r)
  finally:sys.modules.pop('_forbidden_vector',None)
 def test07_size_and_hash_strict(self):
  C=load(P/'common.py','_vector_ref_controls');r=C.ref(P/'writer.py')
  for bad in(dict(r,bytes=r['bytes']+1),dict(r,sha256='0'*64),dict(r,bytes=True)):
   with self.assertRaises(ValueError):C.checked(bad)
 def test08_real_original_controller_inverse(self):
  base=Path('C:/Users/Huawei/AppData/Local/Temp/kivi-writer-atomic-predicate-r156-20261013-001');A=load(base/'controller_adapter.py','_vector_actual_adapter');raw=Path('C:/Users/Huawei/AppData/Local/Temp/kivi-direct-fp32-graph-owner-20261012-002/actual-donors/host_once.py').read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),A.HOST_SHA);tree=A.controller_tree(raw);self.assertIn('COHORT_SHARED',ast.unparse(tree));self.assertIn('self.co.cohort.released',ast.unparse(tree))
 def test09_original_gate_body_not_copied_or_rewritten(self):
  p=Path('C:/Users/Huawei/AppData/Local/Temp/skvq-r118-preparation/writer-native-v1-003/gate.py');self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),'45e02c54d580607091b06a8109f59baf3aa19a74125eef5b5d9845c4f93404a7');tree=ast.parse((P/'guest.py').read_bytes());self.assertEqual(sum(isinstance(n,ast.Call)and ast.unparse(n.func)=='G.run'for n in ast.walk(tree)),1)
if __name__=='__main__':unittest.main()

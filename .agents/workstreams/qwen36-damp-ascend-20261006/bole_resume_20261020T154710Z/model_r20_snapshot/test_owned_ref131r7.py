"""Actual025 full Ref implementation vs real strict sourceio, CPU only."""
import ast,hashlib,json,re,tempfile,types,unittest,__future__
from pathlib import Path
import sourceio as C,owned_ref131r7 as R
P=Path(__file__).parent
def actual():
 path=P/'evidence/original025_model_contract.py'
 tree=ast.parse(path.read_bytes());names={'require','ordinary','sha','bound','ref','obj'}
 ns={'Path':Path,'hashlib':hashlib,'re':re,'json':json}
 exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in names],type_ignores=[]),str(path),'exec',flags=__future__.annotations.compiler_flag),ns)
 return types.SimpleNamespace(**ns)
class Tests(unittest.TestCase):
 def test_actual_ref2_rejected_by_strict_reader_then_exact_ref3_reads(self):
  c=actual()
  with tempfile.TemporaryDirectory()as td:
   p=Path(td)/'MTP-LOAD.json';p.write_bytes(b'{"actual":1}\n')
   old=c.ref(p);self.assertEqual(set(old),{'path','sha256'})
   with self.assertRaises(ValueError):C.obj(old)
   before=p.read_bytes();r=R.file_ref(C,c,p)
   self.assertEqual(set(r),{'path','bytes','sha256'});self.assertEqual(r['bytes'],len(before))
   self.assertEqual(C.obj(r),{'actual':1});self.assertEqual(p.read_bytes(),before)
   self.assertEqual(c.ref(p),old) # original controller function/protocol not patched.
 def test_path_hash_keys_and_mutation_reject(self):
  c=actual()
  with tempfile.TemporaryDirectory()as td:
   p=Path(td)/'r.json';p.write_bytes(b'{}\n');old=c.ref(p)
   for bad,path in [(dict(old,bytes=3),p),({'path':old['path'],'sha256':'0'*64},p),(old,p.with_name('wrong')),(tuple(old.items()),p)]:
    with self.assertRaises(ValueError):R.upgrade(C,bad,path)
   p.write_bytes(b'{"changed":true}\n')
   with self.assertRaises(ValueError):R.upgrade(C,old,p)
 def test_complete_host_has_no_c_ref_to_strict_reader_leak(self):
  tree=ast.parse((P/'host090.py').read_bytes())
  self.assertFalse(any(isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and isinstance(n.func.value,ast.Name)and n.func.value.id=='c'and n.func.attr=='ref'for n in ast.walk(tree)))
  # Original owner stdout/write protocol remains c.write (Ref2), not replaced.
  self.assertIn("rr=c.write(a.output/'RESULT.json'",(P/'host090.py').read_text())
 def test_model_bundle_exact_ref3_fields_reach_actual_strict_reader(self):
  c=actual()
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);p=root/'HTTP_RESULT.json';p.write_bytes(b'{"rows":[]}\n')
   r=R.file_ref(C,c,p);bundle=C.write(root/'bundle.json',dict(http=r,journal=[r],ranks=[dict(receipt=r,raw=r)]))
   b=C.obj(bundle)
   for x in [b['http'],*b['journal'],b['ranks'][0]['receipt'],b['ranks'][0]['raw']]:self.assertEqual(C.obj(x),{'rows':[]})

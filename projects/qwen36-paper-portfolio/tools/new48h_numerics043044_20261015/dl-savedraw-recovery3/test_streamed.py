import ast,hashlib,importlib.util,pathlib,sys,tempfile,unittest
from unittest.mock import patch
P=pathlib.Path(__file__).resolve().parent
def functions():
 tree=ast.parse((P/'host.py').read_bytes());names={'need','sha','validate_ref_streamed','checked'};nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in names];ns=dict(Path=pathlib.Path,hashlib=hashlib);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(P/'host.py'),'exec'),ns);return ns
class Streamed(unittest.TestCase):
 def setUp(self):self.ns=functions()
 def test_raw_does_not_read_bytes(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d)/'raw.pt';p.write_bytes(b'raw-tensor'*65536);r=dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
   with patch.object(pathlib.Path,'read_bytes',side_effect=AssertionError('opaque raw whole allocation forbidden')):self.assertEqual(self.ns['validate_ref_streamed'](r),p)
 def test_wrong_size_hash_reject(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d)/'raw.pt';p.write_bytes(b'abc');r=dict(path=str(p),bytes=3,sha256=hashlib.sha256(b'abc').hexdigest())
   for bad in(dict(r,bytes=4),dict(r,sha256='0'*64)):
    with self.assertRaises(ValueError):self.ns['validate_ref_streamed'](bad)
 def test_json_returns_actual_bytes(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d)/'x.json';p.write_bytes(b'{"x":1}');r=dict(path=str(p),bytes=7,sha256=hashlib.sha256(p.read_bytes()).hexdigest());self.assertEqual(self.ns['checked'](r),b'{"x":1}')
 def test_exact_three_validation_loops(self):
  s=(P/'host.py').read_text();self.assertIn('for f in refs:validate_ref_streamed(f)',s);self.assertIn('[validate_ref_streamed(r)for r in refs]',s);self.assertIn('for r in refs:validate_ref_streamed(r)',s)
if __name__=='__main__':unittest.main()

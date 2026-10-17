"""Real embedded header and unchanged actual plugin predicate, stdlib only."""
import ast,base64,copy,hashlib,json,types,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
EXPECTED=(13720,'4055d6b9d3a96face0efb5d68aafb68900a1d9c78c6a877ae21381688dd8b529')


def decoded(layout):
 out={}
 for name,record in layout.items():
  b=base64.b64decode(record['base64'],validate=True)
  if (len(b),hashlib.sha256(b).hexdigest())!=(record['bytes'],record['sha256']):raise ValueError('embedded source exact bytes/SHA/base64 '+name)
  out[name]=b
 return out


def actual_predicate(header):
 tree=ast.parse((P/'native_observer_plugin101r12.py').read_bytes())
 found=[n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='need'and len(n.args)==2 and isinstance(n.args[1],ast.Constant)and n.args[1].value=='actual exact ACL enum ND2 source']
 if len(found)!=1:raise ValueError('sole unchanged actual header guard')
 return eval(compile(ast.Expression(found[0].args[0]),str(P/'native_observer_plugin101r12.py')+'::actualheader','eval'),
             {'__builtins__':{},'hashlib':hashlib,'header':header,'F':types.SimpleNamespace(ACL_SHA=EXPECTED[1])})


class LayoutSnapshot(unittest.TestCase):
 def layout(self):return json.loads((P/'LAYOUT_SOURCE_EVIDENCE101R12.json').read_bytes())
 def test_actual_header_exact_SHA_ND2_and_all_embedded_sources(self):
  b=decoded(self.layout());self.assertEqual(set(b),{'acl_base_rt.h','module_loader.py','torch_npu_exports.py','torch_npu_init.py'})
  h=b['acl_base_rt.h'];self.assertEqual((len(h),hashlib.sha256(h).hexdigest()),EXPECTED)
  self.assertTrue(actual_predicate(h));self.assertIn(b'ACL_FORMAT_FRACTAL_NZ = 29,',h)
 def test_old_extra_LF_and_wrong_SHA_refused(self):
  h=decoded(self.layout())['acl_base_rt.h'];self.assertFalse(actual_predicate(h+b'\n'))
  self.assertFalse(actual_predicate(b'X'+h[1:]))
 def test_semantically_changed_ND_refused_even_self_consistent_snapshot(self):
  m=self.layout();h=decoded(m)['acl_base_rt.h'];self.assertEqual(h.count(b'ACL_FORMAT_ND = 2,'),1)
  bad=h.replace(b'ACL_FORMAT_ND = 2,',b'ACL_FORMAT_ND = 3,');m['acl_base_rt.h']=dict(base64=base64.b64encode(bad).decode(),bytes=len(bad),sha256=hashlib.sha256(bad).hexdigest())
  self.assertEqual(decoded(m)['acl_base_rt.h'],bad);self.assertFalse(actual_predicate(bad))
 def test_any_embedded_size_hash_or_base64_mismatch_refused(self):
  for name in self.layout():
   for key,value in (('bytes',0),('sha256','0'*64),('base64','!invalid')):
    m=copy.deepcopy(self.layout());m[name][key]=value
    with self.assertRaises(ValueError):decoded(m)


if __name__=='__main__':unittest.main()

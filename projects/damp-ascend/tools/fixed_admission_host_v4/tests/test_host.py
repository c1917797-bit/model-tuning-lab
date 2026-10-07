"""HOST fixtures + actual frozen-source AST identity. No Torch/model/container."""
import ast
from collections import Counter
import importlib.util
import json
from pathlib import Path
import sys
import unittest
HERE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("damp_host_v4_test",HERE/"run.py")
H=importlib.util.module_from_spec(spec);sys.modules[spec.name]=H;spec.loader.exec_module(H)
class Host(unittest.TestCase):
 def test_order_only_ignored(self):
  a=[{"Destination":"/a","Source":"/x","RW":False},{"Destination":"/b","Source":"/y","RW":True}]
  self.assertEqual(H.mounts_multiset(a),H.mounts_multiset(list(reversed(a))))
 def test_allfields_change_rejected(self):
  a=[{"Destination":"/a","Source":"/x","RW":False}]
  for b in ([{"Destination":"/a","Source":"/z","RW":False}],
            [{"Destination":"/a","Source":"/x","RW":True}],
            [{"Destination":"/a","Source":"/x","RW":False,"extra":1}]):
   self.assertNotEqual(H.mounts_multiset(a),H.mounts_multiset(b))
 def test_duplicates_preserved(self):
  a={"Destination":"/a","Source":"/x","RW":False}
  self.assertNotEqual(H.mounts_multiset([a]),H.mounts_multiset([a,a]))
 def test_invalid_mounts_rejected(self):
  for x in (None,{},["/a"],[{"Source":"/x"}]):
   with self.assertRaises(ValueError):H.mounts_multiset(x)
 def test_original_guards_AST_unchanged(self):
  original=ast.parse((H.V3/"run.py").read_bytes())
  candidate=ast.parse((HERE/"run.py").read_bytes())
  a=next(n for n in original.body if isinstance(n,ast.FunctionDef) and n.name=="previous_released")
  b=next(n for n in candidate.body if isinstance(n,ast.FunctionDef) and n.name=="previous_released")
  def without_mounts(n):
   out=[]
   for x in n.body:
    if isinstance(x,ast.Expr) and isinstance(x.value,ast.Call):
     call=x.value
     if isinstance(call.func,ast.Name) and call.func.id=="raw_mounts_before_predicates":continue
     if any(isinstance(y,ast.Constant) and isinstance(y.value,str) and y.value.startswith("previous C1 mounts") for y in call.args):continue
    out.append(ast.dump(x,include_attributes=False))
   return out
  self.assertEqual(without_mounts(a),without_mounts(b))
 def test_raw_capture_precedes_actual_predicates(self):
  tree=ast.parse((HERE/"run.py").read_bytes())
  n=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="previous_released")
  names=[]
  for x in n.body:
   if isinstance(x,ast.Assign) and isinstance(x.value,ast.Call) and getattr(x.value.func,"id",None)=="inspect":names.append("inspect")
   if isinstance(x,ast.Expr) and isinstance(x.value,ast.Call):names.append(getattr(x.value.func,"id",None))
  first=names.index("inspect")
  self.assertEqual(names[first+1],"raw_mounts_before_predicates")
  self.assertEqual(names[first+2],"require")
 def test_capped20min_not_extension(self):
  self.assertEqual(H.tightened_deadline(100,2800,monotonic=101,wall_time=H.ABSOLUTE_DEADLINE_EPOCH-4000),1300)
  self.assertEqual(H.tightened_deadline(100,200,monotonic=101,wall_time=H.ABSOLUTE_DEADLINE_EPOCH-4000),200)
 def test_absolute_deadline_preserved(self):
  self.assertEqual(H.tightened_deadline(100,2800,monotonic=101,wall_time=H.ABSOLUTE_DEADLINE_EPOCH-300),401)
  self.assertEqual(H.CLEANUP_RESERVE,90)
  self.assertEqual(H.CAP_SECONDS,1200)
if __name__=="__main__":unittest.main()

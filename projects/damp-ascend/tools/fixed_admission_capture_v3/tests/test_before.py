"""Actual frozen guard AST plus no-Torch behavior fixtures; not native evidence."""
import ast
import hashlib
import importlib.util
import io
import os
from pathlib import Path
import sys
import types
import unittest
HERE=Path(__file__).resolve().parents[1]
if str(HERE) not in sys.path:sys.path.insert(0,str(HERE))
import v3_before as B
from v3_contract import V2,OBSERVER_SHA,RUNTIME
class Vec:
 def __init__(self,v):self.v=v
 def __getitem__(self,k):return Vec(self.v[k])
 def tolist(self):return self.v
class OriginalGuard(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  source=(V2/"v2_observer.py").read_bytes()
  assert hashlib.sha256(source).hexdigest()==OBSERVER_SHA
  tree=ast.parse(source)
  begin=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=="begin")
  selected=[]
  for node in begin.body:
   if isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id in
      ("starts","computed","n") for x in node.targets):selected.append(node)
   if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and any(
      isinstance(x,ast.Constant) and x.value=="native admission shape/time differs from fixed protocol"
      for x in node.value.args):selected.append(node)
  assert len(selected)==4
  function=ast.FunctionDef(name="actual_guard",args=ast.arguments(posonlyargs=[],
   args=[ast.arg(arg="self"),ast.arg(arg="runner"),ast.arg(arg="batch")],
   vararg=None,kwonlyargs=[],kw_defaults=[],kwarg=None,defaults=[]),
   body=selected,decorator_list=[])
  module=ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[]))
  namespace={"require":B.require};exec(compile(module,str(V2/"v2_observer.py"),"exec"),namespace)
  cls.guard=staticmethod(namespace["actual_guard"])
 def check(self,turn,starts,computed):
  observer=types.SimpleNamespace(turn=turn)
  runner=types.SimpleNamespace(gdn_query_start_loc=types.SimpleNamespace(cpu=Vec(starts)))
  batch=types.SimpleNamespace(num_computed_tokens_cpu_tensor=Vec(computed))
  return self.guard(observer,runner,batch)
 def test_prefill_exact(self):self.check(0,[0,1024],[0])
 def test_decode_exact(self):self.check(1,[0,1],[1024]);self.check(32,[0,1],[1055])
 def test_wrong_start_still_rejected(self):
  with self.assertRaisesRegex(ValueError,"shape/time"):self.check(0,[0,1],[0])
 def test_wrong_computed_still_rejected(self):
  with self.assertRaisesRegex(ValueError,"shape/time"):self.check(1,[0,1],[1023])
class Wrapper(unittest.TestCase):
 def runner(self,n=1):return types.SimpleNamespace(input_batch=types.SimpleNamespace(num_reqs=n))
 def test_save_before_original_return_identity(self):
  calls=[];output=object();runner=self.runner()
  wrapped=B.wrap_original(lambda *a,**k:calls.append("native") or output,
   lambda *a:calls.append("record") or {"turn":0},
   lambda x:calls.append("save"))
  self.assertIs(wrapped(runner),output);self.assertEqual(calls,["record","save","native"])
 def test_original_exception_identity_preserved(self):
  error=ValueError("native admission shape/time differs from fixed protocol");calls=[]
  def native(*a,**k):calls.append("native");raise error
  wrapped=B.wrap_original(native,lambda *a:{"turn":0},lambda x:calls.append("independent-save"))
  try:wrapped(self.runner())
  except ValueError as e:self.assertIs(e,error)
  else:self.fail("original exception swallowed")
  self.assertEqual(calls,["independent-save","native"])
 def test_evidence_failure_fail_before_any_writer(self):
  calls=[]
  def save(x):raise OSError("raw write failed")
  wrapped=B.wrap_original(lambda *a:calls.append("native"),lambda *a:{},save)
  with self.assertRaises(OSError):wrapped(self.runner())
  self.assertEqual(calls,[])
 def test_dummy_no_evidence_or_native_changes(self):
  output=object()
  wrapped=B.wrap_original(lambda *a:output,lambda *a:self.fail("dummy record"),lambda *a:self.fail("dummy save"))
  self.assertIs(wrapped(self.runner(0)),output)
 def test_optional_unavailable_not_synthetic(self):
  x=B.optional(lambda:(_ for _ in ()).throw(AttributeError("missing")))
  self.assertFalse(x["available"]);self.assertNotIn("value",x)
 def test_independent_exclusive_fsync(self):
  calls=[]
  class File(io.BytesIO):
   def __enter__(self):return self
   def __exit__(self,*a):pass
   def fileno(self):return 18
  file=File();old_open=Path.open;old_sync=B.os.fsync
  try:
   def open_(self,mode,**kwargs):
    calls.append((mode,kwargs));return file
   Path.open=open_;B.os.fsync=lambda n:calls.append(("fsync",n))
   B.exclusive_json("/never-created",{"schema":"fixture","turn":0})
  finally:Path.open=old_open;B.os.fsync=old_sync
  self.assertEqual(calls,[("xb",{"buffering":0}),("fsync",18)])
  self.assertIn(b'"turn":0',file.getvalue())
 def test_size_cap_before_open(self):
  old=Path.open
  try:
   Path.open=lambda *a,**k:self.fail("opened oversized record")
   with self.assertRaises(ValueError):B.exclusive_json("/never-created",{"x":"a"*B.MAX_RECORD_BYTES})
  finally:Path.open=old
 def test_default_off_no_runtime_import_or_write(self):
  path=HERE/"damp_fixed_v3.py"
  namespace={};exec(compile(path.read_bytes(),str(path),"exec"),namespace)
  before=set(sys.modules);old=os.environ.pop("DAMP_ADMISSION_TRACE_ENABLE",None)
  try:self.assertIsNone(namespace["register"]())
  finally:
   if old is not None:os.environ["DAMP_ADMISSION_TRACE_ENABLE"]=old
  self.assertEqual(set(sys.modules),before)
 def test_runtime_paths_are_actual(self):
  self.assertIn("/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn_attn_builder.py",RUNTIME)
  self.assertEqual(len(RUNTIME),3)
if __name__=="__main__":unittest.main()

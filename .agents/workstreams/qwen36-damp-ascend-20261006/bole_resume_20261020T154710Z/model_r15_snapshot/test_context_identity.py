"""Actual stdlib and complete actual enter body; no backend initialization."""
import contextlib,functools,json,subprocess,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
import context_adapter as A,context_identity as I,sourceio as C
P=Path(__file__).resolve().parent

def validate(fn):return I.enter_source(C,fn,C.ref(A.__file__),C.ref(contextlib.__file__))
def cell(value):return (lambda:value).__closure__[0]

class Tests(unittest.TestCase):
 def test_actual_one_layer_stdlib_contextmanager_identity(self):
  proof=validate(A.enter);self.assertEqual(proof['depth'],1)
  self.assertEqual(Path(A.enter.__code__.co_filename).resolve(),Path(contextlib.__file__).resolve())
  self.assertEqual(Path(A.enter.__wrapped__.__code__.co_filename).resolve(),Path(A.__file__).resolve())
 def test_wrong_wrapper_and_wrong_closure_reject(self):
  original=A.enter
  @functools.wraps(original)
  def unknown(*args,**kwargs):return original(*args,**kwargs)
  with patch.object(A,'enter',unknown):
   with self.assertRaisesRegex(ValueError,'contextmanager'):validate(unknown)
  bad=types.FunctionType(original.__code__,original.__globals__,closure=(cell(lambda:None),))
  functools.update_wrapper(bad,original.__wrapped__)
  with patch.object(A,'enter',bad),patch.object(A,'_SOURCE_ENTER_WRAPPER',bad):
   with self.assertRaisesRegex(ValueError,'closure'):validate(bad)
 def test_inner_mutation_and_stdlib_factory_mutation_reject(self):
  original=A.enter.__wrapped__.__code__
  def other(original_context,*,num_tokens,source_ref):yield None
  try:
   A.enter.__wrapped__.__code__=other.__code__
   with self.assertRaisesRegex(ValueError,'body'):validate(A.enter)
  finally:A.enter.__wrapped__.__code__=original
  with patch.object(contextlib,'contextmanager',lambda f:f):
   with self.assertRaisesRegex(ValueError,'factory'):validate(A.enter)
  with patch.object(contextlib._GeneratorContextManager,'__enter__',lambda self:None):
   with self.assertRaisesRegex(ValueError,'manager method'):validate(A.enter)
 def test_cold_I_actual_install_to_first_native_boundary(self):
  result=subprocess.run([sys.executable,'-I','-B',str(P/'context_install_probe.py')],capture_output=True,text=True,timeout=25)
  self.assertEqual(result.returncode,0,result.stderr)
  self.assertTrue(json.loads(result.stdout)['actual_install_source_frontdoor_pass'])

if __name__=='__main__':unittest.main()

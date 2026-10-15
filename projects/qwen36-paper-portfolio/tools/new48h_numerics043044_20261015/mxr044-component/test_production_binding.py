"""Software-only actual-target and production contract regressions, no device imports."""
import ast,contextvars,functools,json,subprocess,sys,unittest
from pathlib import Path
import production_binding as B
P=Path(__file__).resolve().parent
class Production005(unittest.TestCase):
 def fixture(self):
  counts={'core':0};prefix=contextvars.ContextVar('test_prefix',default=None)
  def native(self):return prefix.get()
  original_core=native
  @functools.wraps(native)
  def algorithm(self):
   counts['core']+=1
   token=prefix.set(self.prefix)
   try:return original_core(self)
   finally:prefix.reset(token)
  class Ascend:pass
  class Target:prefix='real.layer'
  Ascend._forward_core=algorithm;Target._forward_core=native
  return Target,Ascend,algorithm,counts
 def test_copied_target_is_exact_algorithm_no_outer_wrapper(self):
  T,A,f,c=self.fixture();self.assertIsNone(T()._forward_core())
  b=B.bind_target(T,A,f,c);self.assertIs(T._forward_core,f)
  self.assertEqual(T()._forward_core(),'real.layer');self.assertEqual(c['core'],1)
 def test_diagnostic_outer_and_production_same_math(self):
  T,A,f,c=self.fixture()
  @functools.wraps(f)
  def capture(self):return f(self)
  T._forward_core=capture
  diagnostic=T()._forward_core();T._forward_core=inspect_native=__import__('inspect').unwrap(f)
  B.bind_target(T,A,f,c);self.assertEqual(T()._forward_core(),diagnostic)
 def test_wrong_origin_and_counts_rejected(self):
  T,A,f,c=self.fixture()
  with self.assertRaises(ValueError):B.bind_target(T,A,f,{})
  T._forward_core=lambda self:None
  with self.assertRaises(ValueError):B.bind_target(T,A,f,c)
 def test_partial_evidence_and_missing_worker_failclosed(self):
  import admission
  with self.assertRaises(ValueError):B.startup_gate([],{}, {})
  with self.assertRaises(ValueError):admission.checked(dict(path='relative',bytes=0,sha256='0'*64))
  self.assertIn("NOT old007/009",(P/'admission.py').read_text())
 def test_defaultoff_current_entrypoints(self):
  # This source-only runtime packet intentionally does NOT clone the PF owner.
  # Original005 host_pair/whole_consume pre-timing integration remains untested.
  for file in ('admission.py','plan_cli.py','qualification_probe.py'):
   r=subprocess.run([sys.executable,'-I','-B',str(P/file)],capture_output=True,text=True,timeout=10)
   self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(r.stdout),dict(enabled=False,NPU=False))
  import common_precision
  self.assertIsNone(common_precision.register())
if __name__=='__main__':unittest.main()

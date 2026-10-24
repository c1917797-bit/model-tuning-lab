"""V5-specific replacement for the old 'host/create unchanged' expectation."""
import importlib.util,json,resource,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
WS=HERE.parent
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
class Tests(unittest.TestCase):
 def test_exact_new_CPU_seams_whole_inverse_and_missing_actual_ticket(self):
  F=load(HERE/'formal_runtime.py','formal_composer')
  base=HERE/'formal-source-set-v5'/'specific-control'
  b=F.render(base);F.inverse(b)
  old=F._F.render(base)
  expected=dict(old['files'])
  marker=' observer_race_repair.install(S,C)'
  expected['owned_substrate.py']=F.once(expected['owned_substrate.py'].decode(),marker,marker+"\n raw(current['files']['cpu_release_policy.py'])\n import cpu_release_policy as CPU_RELEASE\n CPU_RELEASE.install(S,C,current)").encode()
  with F.isolated():
   load(HERE/'cpu_precreate_policy.py','cpu_precreate_policy')
   A=load(HERE/'adapt_cpu_precreate.py','_V5exact_test_adapter')
   expected,d=A.adapt(expected)
   self.assertEqual(A.inverse(expected,d)['host_service.py'],old['files']['host_service.py'])
   self.assertEqual(A.inverse(expected,d)['owned_create.py'],old['files']['owned_create.py'])
  for n in('host_service.py','owned_create.py','owned_substrate.py','cpu_precreate_policy.py'):
   self.assertEqual(b['files'][n],expected[n],n)
  allowed={'formal_composer.py','performance_prerequisite.py','short8_source_pin.py','cpu_release_policy.py','cpu_precreate_policy.py','adapt_cpu_precreate.py','owned_substrate.py','host_service.py','owned_create.py'}
  for n in set(old['files'])-allowed:self.assertEqual(b['files'][n],old['files'][n],n)
  self.assertEqual(b['manifest']['cpu_precreate_intent'],A.manifest({})['cpu_precreate_intent'])
  V=F.module(F.ref(WS/'bole32k_fixed1024_performance_prepare_v1_20261023/whole_v2/formal_validator.py'),'_V5actual_original_ticket_guard')
  with self.assertRaises(ValueError):V.execution_window(b['manifest'],clock=True,require_phase=True)
  for n,raw in b['files'].items():
   if n.endswith('.py'):compile(raw,n,'exec')
if __name__=='__main__':
 resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
 resource.setrlimit(resource.RLIMIT_CPU,(90,90))
 unittest.main()

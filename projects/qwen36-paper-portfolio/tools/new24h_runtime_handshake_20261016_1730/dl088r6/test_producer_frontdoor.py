"""Execute the actual guest main until its first torch import; no fake PASS receipts."""
import builtins,copy,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class BeforeTorch(Exception):pass
class Frontdoor(unittest.TestCase):
 def exercise(self,change=None):
  G=load('_actual_guest_frontdoor',P/'producer.py');gate=load('_actual_preregister_frontdoor',P/'preregister.py')
  sr={'path':'/software/source','bytes':1,'sha256':'a'*64};ar={'authority':'software'};lr={'lifecycle':'software'}
  owner=dict(schema='deltalog.diagnostic-owned-host/v035',target_source=sr,stage='numeric',steps=16,stopped_retained=True,primary=None,secondary=[],bridge_primitive_gate_pass=False,model_ready=False,result='result',independent_consumer='consumer')
  consumer=dict(schema='deltalog.eager-component-operational-consumption/v088',source=sr,actual_result='result',validation_contract=dict(schema='deltalog.eager-sameinitial-native-operational/v088'),diagnostic_capture_complete=True,domain_checks_pass=True,complete_proof=False,original_strict_result_preserved=dict(pass_gate=False))
  if change:change(owner,consumer)
  plan=dict(source=sr,authority=ar,lifecycle=lr,physical=5,logical=0,steps=160,graph=False,smoke='owner')
  objects={'plan':plan,'owner':owner,'consumer':consumer};m=dict(allowed_steps=[16,160],files={'preregister.py':'gate'})
  original_import=builtins.__import__;seen=[]
  def importing(name,*a,**kw):
   if name in ('torch','torch_npu'):
    seen.append(name);raise BeforeTorch('actual main reached first backend import')
   return original_import(name,*a,**kw)
  def loader(ref,name):
   self.assertEqual(ref,'gate');return gate
  with tempfile.TemporaryDirectory()as td:
   argv=[str(P/'producer.py'),'--execute','--source-ref',json.dumps(sr),'--authority-ref',json.dumps(ar),'--lifecycle-ref',json.dumps(lr),'--plan-ref',json.dumps('plan'),'--output',str(Path(td)/'output'),'--steps','160']
   with patch.object(G.C,'source',return_value=m),patch.object(G.C,'window'),patch.object(G.C,'obj',side_effect=lambda r:objects[r]),patch.object(G.C,'load',side_effect=loader),patch.object(sys,'argv',argv),patch('builtins.__import__',side_effect=importing):
    try:G.main()
    except BeforeTorch:return True,seen
    except (ValueError,KeyError):return False,seen
   self.fail('frontdoor unexpectedly completed')
 def test_actual_guest_new_domain_accepts_before_torch(self):
  passed,seen=self.exercise();self.assertTrue(passed);self.assertEqual(seen,['torch'])
 def test_actual_guest_negative_contracts_never_import_torch(self):
  changes=[lambda o,c:o.update(primary='original failure'),lambda o,c:o.update(target_source={'wrong':True}),lambda o,c:o.update(schema='old-schema'),lambda o,c:c.pop('domain_checks_pass'),lambda o,c:o.update(bridge_primitive_gate_pass=True),lambda o,c:o.update(model_ready=True),lambda o,c:c.update(complete_proof=True),lambda o,c:c.update(domain_checks_pass=False),lambda o,c:c.update(actual_result='other-result'),lambda o,c:c.update(source={'wrong':True}),lambda o,c:o.update(stopped_retained=False)]
  for change in changes:
   with self.subTest(change=change):
    passed,seen=self.exercise(change);self.assertFalse(passed);self.assertEqual(seen,[])
 def test_host_and_guest_call_same_registered_api(self):
  import ast
  for name in ('host.py','producer.py'):
   tree=ast.parse((P/name).read_text());calls=[x for x in ast.walk(tree)if isinstance(x,ast.Call)and isinstance(x.func,ast.Attribute)and x.func.attr=='admit_smoke']
   self.assertEqual(len(calls),1,name)
 def test_producer_inverse_only_admission_changed(self):
  import inverse088
  self.assertTrue(inverse088.verify('producer.py'))
if __name__=='__main__':unittest.main()

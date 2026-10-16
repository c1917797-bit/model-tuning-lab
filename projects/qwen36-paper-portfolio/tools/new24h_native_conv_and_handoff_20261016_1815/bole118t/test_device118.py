import ast,json,subprocess,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import abi_device118 as A
class Tests(unittest.TestCase):
 def test_arm_refusal_precedes_any_gdn_import(self):
  class C:
   @staticmethod
   def need(v,s):
    if not v:raise ValueError(s)
  with self.assertRaisesRegex(ValueError,'ARM'):A.record(None,C,None,arm_verified=False)
  tree=ast.parse((P/'guest116.py').read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main');calls=[n for n in ast.walk(fn)if isinstance(n,ast.Call)]
  self.assertTrue(any(isinstance(n.func,ast.Name)and n.func.id=='execute'for n in calls))
  text=(P/'guest116.py').read_text(encoding='utf8');self.assertLess(text.index("'exact host ARM'"),text.index('result=execute('));self.assertNotIn('import vllm_ascend.ops.gdn',(P/'cpu116.py').read_text(encoding='utf8'))
 def test_typed_receiver_does_not_make_conv_qualification(self):
  sr={'software':'source'};v=dict(schema='bole.actual-device-conv-ABI/v118',source=sr,NPUallocated=True,NPU=True,actual_MAIN_ARM=True,logical=0,physical=4,operator_executed=False,qualified=False,calibration_pending=True,actual_schema_family={'':'software fixture'})
  self.assertIs(A.validate(v,sr),v)
  for k,value in(('operator_executed',True),('qualified',True),('physical',5),('NPUallocated',False)):
   with self.assertRaises(ValueError):A.validate(dict(v,**{k:value}),sr)
  with self.assertRaises(ValueError):A.validate(v,{'wrong':'source'})
 def test_actual_cold_I_default_off_all_entrypoints(self):
  for n in('run116.py','bind116.py','cpu116.py','owner116.py','guest116.py','consume116.py','ticket116.py'):
   r=subprocess.run([sys.executable,'-I','-B',str(P/n)],capture_output=True,text=True,timeout=10);self.assertEqual(r.returncode,0,(n,r.stderr));self.assertFalse(json.loads(r.stdout)['NPU'])
if __name__=='__main__':unittest.main()

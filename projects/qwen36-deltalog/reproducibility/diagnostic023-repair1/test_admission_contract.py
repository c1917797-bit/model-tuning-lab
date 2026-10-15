"""Synthetic negative contract tests, never actual022 qualification."""
import copy,unittest
from qwen36_deltalog_service import admission as A
class Tests(unittest.TestCase):
 def fixture(self):
  sr={'path':'/fixture/source','bytes':1,'sha256':'fixture'};lib={'path':'/fixture/library','bytes':2,'sha256':'fixture'}
  c=dict(schema='deltalog.composite-component-qualification/v022',source=sr,strict324=True,original_numeric325=True,strict137_join={'actual_tensor_join':True},strict325_composed=True,old002_failure_unchanged=True,original019_strict_pass=False,model_ready=False,performance_ready=False,task_ready=False,graph=False,PDC=False,library=lib,operator_schema='fixture::decode')
  return c,sr,lib
 def test_typed_component_contract_only(self):
  c,s,l=self.fixture();self.assertIs(A.certificate(c,s,l,'fixture::decode'),c)
 def test_component_cannot_be_promoted_or_boolean_join(self):
  for key,value in(('model_ready',True),('original019_strict_pass',True),('strict137_join',True),('strict137_join',{'actual_tensor_join':False}),('strict324',False)):
   c,s,l=self.fixture();c[key]=value
   with self.assertRaises((RuntimeError,TypeError)):A.certificate(c,s,l,'fixture::decode')
if __name__=='__main__':unittest.main()

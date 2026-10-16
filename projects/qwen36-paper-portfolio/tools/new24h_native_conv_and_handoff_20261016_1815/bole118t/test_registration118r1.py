import ast,hashlib,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import registration118 as R
class Tests(unittest.TestCase):
 def test_no_ARM_rejects_before_native_import(self):
  class C:
   @staticmethod
   def need(v,s):
    if not v:raise ValueError(s)
  with self.assertRaisesRegex(ValueError,'MAIN_ARM'):R.actual(None,C,arm_verified=False)
 def test_real_installed_lazy_registration_and_call_order(self):
  tree=ast.parse((P/'evidence/registration-utils.py').read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='enable_custom_op');imports={a.name for n in ast.walk(fn)if isinstance(n,ast.Import)for a in n.names};self.assertIn('vllm_ascend.vllm_ascend_C',imports);self.assertIn('vllm_ascend.meta_registration',imports)
  self.assertTrue(any(isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='bootstrap_custom_op_env'for n in ast.walk(fn)))
  device=(P/'abi_device118.py').read_text(encoding='utf8');self.assertLess(device.index('registration118.actual('),device.index("importlib.import_module('vllm_ascend.ops.gdn')"))
  reg=(P/'registration118.py').read_text(encoding='utf8');self.assertIn('utils.enable_custom_op()is True',reg);self.assertIn('ExtensionFileLoader',reg);self.assertIn("Path('/proc/self/maps')",reg)
 def test_actual_three_source_snapshots_exact(self):
  for name,size,digest in(('utils.py',67646,'575b45d684eabdb7ac3195d33de48bd5f3233081f78886c08be92a4a2fd2fc02'),('platform.py',62514,'30c75952f784c4d047d7202dd7f68c8fc7c22bb975853a5048fb51ffcbe1f2a8'),('worker.py',48290,'c392da56095b255d47fe5ad7ffdfbedd269fe69851690e89a8d2ed44c073f6c3')):
   b=(P/'evidence'/('registration-'+name)).read_bytes();self.assertEqual(len(b),size);self.assertEqual(hashlib.sha256(b).hexdigest(),digest)
if __name__=='__main__':unittest.main()

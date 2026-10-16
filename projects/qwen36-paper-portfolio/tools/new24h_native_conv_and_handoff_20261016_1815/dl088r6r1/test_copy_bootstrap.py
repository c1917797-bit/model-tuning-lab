import ast,hashlib,importlib.util,pathlib,unittest
P=pathlib.Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def test_official_patch_exact_and_910b_batch_bindings(self):
  b=(P/'dependencies/native_patch_mamba_utils.py').read_bytes();self.assertEqual((len(b),hashlib.sha256(b).hexdigest()),(12252,'a8862c3509f698c05cdeba5aa408a28e506349eff97801b28161569b8e3c9778'))
  t=ast.parse(b);branch=next(n for n in t.body if isinstance(n,ast.If)and ast.unparse(n.test)=='_can_launch_triton_batch_memcpy()');self.assertEqual([ast.unparse(n)for n in branch.body],['mamba_utils.batch_memcpy_kernel = batch_memcpy_kernel','mamba_utils.batch_memcpy = _batch_memcpy_triton','mamba_utils.postprocess_mamba_fused_kernel = postprocess_mamba_fused_kernel'])
  f=next(n for n in t.body if isinstance(n,ast.FunctionDef)and n.name=='_batch_memcpy_triton');self.assertIn('BLOCK_SIZE = 8192',ast.unparse(f))
 def test_official_kernel_pointer_casts_are_outside_loop(self):
  b=(P/'dependencies/native_ascend_batch_memcpy.py').read_bytes();self.assertEqual((len(b),hashlib.sha256(b).hexdigest()),(1089,'c434b023102d1804eec0eb63b6d62b0f9343cb831e6ef82f6151efcdf96c5965'))
  f=next(n for n in ast.parse(b).body if isinstance(n,ast.FunctionDef));loop=next(n for n in f.body if isinstance(n,ast.For));self.assertFalse(any(isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='to'for n in ast.walk(loop)))
  self.assertEqual(sum(isinstance(n,ast.Assign)and '.to(tl.pointer_type(tl.uint8))'in ast.unparse(n)for n in f.body),2)
 def test_actual_producer_order_and_durable_markers(self):
  t=(P/'producer.py').read_text();self.assertLess(t.index('COPY.install(mu,out,execute=True)'),t.index('V.install_fixture(torch,gdn,mu,emit)'));self.assertIn("COPY.marker(out,'copy-before-",t);self.assertIn("COPY.marker(out,'copy-after-",t)
  b=(P/'copy_bootstrap.py').read_text();self.assertIn('os.fsync(fd)',b);self.assertNotIn("import_module('vllm_ascend.patch.worker",b);self.assertIn("old.__globals__['batch_memcpy']is not mu.batch_memcpy",b)
 def test_default_off_no_import_or_files(self):
  s=importlib.util.spec_from_file_location('_copy_bootstrap_cpu_control',P/'copy_bootstrap.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
  with self.assertRaisesRegex(RuntimeError,'OFF'):m.install(object(),P)
 def test_cpu_import_must_run_before_cpu_stage_pass(self):
  t=(P/'entry.py').read_text();self.assertLess(t.index('actual=subprocess.run'),t.index("actual_copy_import=C.ref"));self.assertIn("actual.returncode==0",t)
  call=next(n for n in ast.walk(ast.parse(t))if isinstance(n,ast.Call)and ast.unparse(n.func)=='subprocess.run');self.assertEqual([x.value for x in call.args[0].elts[1:3]],['-I','-B']);self.assertIn('MAIN_DL_COPY_IMPORT ',t)
if __name__=='__main__':unittest.main()

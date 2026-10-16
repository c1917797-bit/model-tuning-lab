import ast,importlib.util,json,math,pathlib,struct,subprocess,sys,unittest
P=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(P));import verify_inverse as V
class Tests(unittest.TestCase):
 def test_real_manifest_builder_guest_Meta_schema_chain(self):
  m=json.loads((P/'kernel/SOURCE_MANIFEST.json').read_bytes())
  text=(P/'kernel/build_pair.py').read_text(encoding='utf8');self.assertIn(repr(m['schema']),text)
  result='deltalog-split-scale-actual-build/v051'
  for n in('kernel/build_pair.py','build_owner/guest.py','meta_abi.py'):
   tree=ast.parse((P/n).read_text(encoding='utf8'));strings=[x.value for x in ast.walk(tree)if isinstance(x,ast.Constant)and isinstance(x.value,str)]
   self.assertIn(result,strings)
 def test_exact_power2_all_finite_BF16_codes(self):
  for code in range(65536):
   x=struct.unpack('<f',struct.pack('<I',code<<16))[0]
   if not math.isfinite(x):continue
   y=x/16.;self.assertEqual(struct.unpack('<f',struct.pack('<f',y))[0],y)
 def test_subnormal_split_prediction_and_nondecreasing_overflow_headroom(self):
  f=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
  scale=f(128**-.5);term=f(2.**-140*.0625);self.assertEqual(term/2.**-149,32.)
  out=f(f(128*term)*f(scale*16));self.assertEqual(out/2.**-149,5793.)
  self.assertLess(.0625,scale)
  total=f(128*f(1e37*.0625));self.assertTrue(math.isfinite(f(total*f(scale*16))))
 def test_actual_all14_source_inverse(self):self.assertEqual(len(V.verify(P)),14)
 def test_exported_fixed_D128_scale_and_original_ABI(self):
  for arm in('split_scale_v051','split_scale_sidecar_v051'):
   cpp=next((P/'kernel'/arm/'op_extension').glob('*_torch.cpp')).read_text(encoding='utf8')
   self.assertIn('1.0f / std::sqrt(static_cast<float>(kHeadDim))',cpp)
   self.assertIn('constexpr int64_t kHeadDim = 128;',cpp)
   h=next((P/'kernel'/arm/'op_kernel').glob(arm.join(('qwen36_gdn_deltalog_decode_','.h')))).read_text(encoding='utf8')
   self.assertIn('0.0625f : scale_',h);self.assertEqual(h.count('Muls(attnUb_, attnUb_, scale_ * 16.0f, rows);'),1)
 def test_debug_observes_after_finalscale(self):
  h=(P/'kernel/split_scale_sidecar_v051/op_kernel/qwen36_gdn_deltalog_decode_split_scale_sidecar_v051.h').read_text(encoding='utf8')
  i=h.index('    __aicore__ inline void StoreOutput');s=h[i:h.index('    __aicore__ inline void StoreBase',i)]
  self.assertLess(s.index('scale_ * 16.0f'),s.index('DataCopy(precastGm_'));self.assertLess(s.index('DataCopy(precastGm_'),s.index('Cast(local, attnUb_'))
 def test_real_defaultOFF_build_Meta_and_owner(self):
  for n in('kernel/build_pair.py','meta_abi.py','build_owner/guest.py','build_owner/host.py'):
   r=subprocess.run([sys.executable,'-I','-B',str(P/n)],capture_output=True,text=True,timeout=20)
   self.assertEqual(r.returncode,0,r.stderr);self.assertTrue('disabled'in r.stdout or '"enabled": false'in r.stdout)
 def test_production_guest_and_host_expect_both_actual_arms(self):
  for n in('build_owner/guest.py','build_owner/host.py'):
   s=(P/n).read_text(encoding='utf8');self.assertIn("['split_scale_v051','split_scale_sidecar_v051']",s)
if __name__=='__main__':unittest.main()

"""Fifteen cold source/API controls; synthetic algebra is not a NPU verdict."""
import ast,hashlib,importlib.util,json,os,re,subprocess,sys,tempfile,types,unittest
from unittest.mock import patch
from pathlib import Path
P=Path(__file__).resolve().parent
def module(name):
 s=importlib.util.spec_from_file_location('_mxr034_test_'+name,P/(name+'.py'));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
D=module('derive');B=module('build');A=module('adapter');N=module('numeric')
AUTHOR=Path(os.environ.get('MXR025_AUTHOR_READONLY','C:/Users/Huawei/AppData/Local/Temp/mxr-official-readback-r131-20261013-001'if os.name=='nt'else'/cache/cch/paper-sources/mxr-tri-inverse-20260918/extracted/megagdn-pto-d357fd38608f99ddf9b9fb2d217b2e731ecd3a72'))
RELAY=Path(os.environ.get('MXR025_PTO_READONLY','C:/Users/Huawei/AppData/Local/Temp/mxr-r148-author-relay'if os.name=='nt'else'/cache/cch/paper-sources/mxr-tri-inverse-20260918/pto-isa-01666f3b386f296c95e6e05825fe63b8e6bb4ef4'))
BASE=Path(os.environ.get('MXR034_DERIVE028_READONLY','C:/Users/Huawei/AppData/Local/Temp/mxr-r118-y16-compensated-candidate-20261013-028/derive.py'if os.name=='nt'else D.BASE['path']))
def ref(path):
 raw=path.read_bytes();return dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def generated():return D.sources((AUTHOR/'kernels/pto/tri_inverse_impl.cpp').read_bytes(),(AUTHOR/'kernels/pto/tri_inverse.cpp').read_bytes(),ref(BASE))[0]
class Controls(unittest.TestCase):
 def test01_whole_source_inverse_and_generated(self):
  for n,b in generated().items():self.assertEqual(b,(P/n).read_bytes())
 def test02_original_author_bytes_immutable(self):
  x=(AUTHOR/'kernels/pto/tri_inverse_impl.cpp').read_bytes();e=(AUTHOR/'kernels/pto/tri_inverse.cpp').read_bytes()
  with self.assertRaisesRegex(ValueError,'exact original'):D.sources(x+b'\n',e,ref(BASE))
 def test03_only_observed_diagonal16_refinement(self):
  text=(P/'tri_inverse_y16_impl.cpp').read_text();self.assertIn('RefineDiag16 && MatrixSize == 64',D.NEWTON);self.assertEqual(D.NEWTON.count('TMATMUL('),2);self.assertEqual(D.NEWTON.count('TMATMUL_ACC('),3);self.assertNotIn('MXR_Y16_RESIDUAL_BEGIN',text);self.assertNotIn('MXR_Y16_ADD_LOW_BEGIN',text);self.assertIn('M_neg_l1_tile, a_l0_tile[0]',D.NEWTON)
 def test04_actual_PTO_accumulator_alias(self):
  raw=json.loads((RELAY/'TMatmul-EXACT.json').read_bytes())['content'].encode()if(RELAY/'TMatmul-EXACT.json').is_file()else(RELAY/'include/pto/npu/a2a3/TMatmul.hpp').read_bytes();self.assertEqual(len(raw),10965);self.assertEqual(hashlib.sha256(raw).hexdigest(),'e4ec288b101cf2a8ec0a5a175fcd27a2fb285d2c9b40cc4a63f6af088db2c896');text=raw.decode();a=text.index('PTO_INTERNAL void TMATMUL_ACC_IMPL(TileRes &cOutMatrix');b=text.index('// Convenience overload',a);self.assertEqual(text[a:b].count('cInMatrix'),1);self.assertIn('false, false, false>(cOutMatrix.data()',text[a:b])
 def test05_existing_half_cast_and_L1_budget(self):
  path=RELAY/('common.hpp'if(RELAY/'common.hpp').is_file()else'include/pto/npu/a2a3/common.hpp');raw=path.read_bytes()
  if os.name=='nt'and hashlib.sha256(raw).hexdigest()=='0f2c60f3587586ef363372128a6ccab10f0278c2b22db391d4b2ee3d7c46d276':raw=raw[:-1]
  self.assertEqual(len(raw),6360);self.assertEqual(hashlib.sha256(raw).hexdigest(),'2fc27d34fc0b5884170446e980aeef36af00826a48d88591e2b69e7cb62ad8c6');self.assertIn(b'QuantMode_t::F322F16',raw);self.assertEqual(7*64*64*2,57344);self.assertLess(57344,65536)
 def test06_new_pipe_tokens_balance(self):
  tokens=set()
  for op,src,dst,event in re.findall(r'(set|wait)_flag\((PIPE_\w+), (PIPE_\w+), (event_\d)\)',D.NEWTON):
   key=(src,dst,event)
   if op=='set':self.assertNotIn(key,tokens);tokens.add(key)
   else:self.assertIn(key,tokens);tokens.remove(key)
  self.assertEqual(tokens,set())
 def test07_original_compile_flags(self):
  raw=(RELAY/'compile.py').read_bytes()if(RELAY/'compile.py').is_file()else(AUTHOR/'megagdn_pto/compile.py').read_bytes();self.assertEqual(B.flags(raw,'/actual/author','/actual/pto'),['-fPIC','-shared','-xcce','-DMEMORY_BASE','-O2','-std=c++17','-I/actual/author/kernels/pto/include','-I/actual/pto/include','--npu-arch=dav-2201'])
 def test08_original_dual_ABI_and_tail(self):
  entry=(P/'tri_inverse_y16.cpp').read_text();self.assertEqual(entry.count('<<<blockDim, nullptr, stream>>>'),2)
  old=(AUTHOR/'kernels/pto/tri_inverse_impl.cpp').read_text();new=(P/'tri_inverse_y16_impl.cpp').read_text()
  for op in('TSTORE(','TLOAD(','TFILLPAD('):self.assertEqual(new.count(op),old.count(op))
  self.assertIn('1 /* NumTilesPerCubeIter */, false>',new);self.assertIn('1 /* NumTilesPerCubeIter */, true>',new)
 def test09_cold_no_runtime(self):
  for n in('derive.py','build.py','numeric.py'):
   code="import runpy,sys;sys.argv=[%r];runpy.run_path(%r,run_name='__main__');assert 'torch'not in sys.modules and 'torch_npu'not in sys.modules"%(str(P/n),str(P/n));r=subprocess.run([sys.executable,'-I','-B','-c',code],capture_output=True,text=True,timeout=5);self.assertEqual(r.returncode,0,r.stderr);self.assertFalse(json.loads(r.stdout)['enabled'])
 def test10_build_ref_required_before_library(self):
  with self.assertRaises(ValueError):A.checked(None)
  with self.assertRaises(ValueError):N.checked(dict(path=str(P),bytes=True,sha256='0'*64))
 def test11_original_raw_before_numeric_rejection(self):
  text=(P/'numeric.py').read_text();a=text.index("with rawpath.open('xb')");b=text.index("if mode=='control'",a);self.assertLess(text[a:b].index('torch.save('),text[a:b].index('O.metrics('));self.assertIn('raw_outputs=raw_outputs',text)
 def test12_four_ranks_three_repeats_originalgold(self):
  text=(P/'numeric.py').read_text();self.assertIn("plan['rank_order']==[2,0,1,3]",text);self.assertIn('range(3)',text);self.assertIn('E0,_=O.fp64_reference(torch,actual_A,cu.tolist())',text);self.assertIn('control_whole_bitwise_old=True',text);self.assertIn('whole original rank2 real workspace failure reproduction',text)
 def test13_new_window_and_cold_AST(self):
  self.assertEqual((B.CUT,N.CUT),(1792002456,1792002456))
  for n in('derive.py','build.py','adapter.py','numeric.py','test_candidate.py'):ast.parse((P/n).read_bytes(),str(P/n))
  self.assertNotIn('torch',sys.modules);self.assertNotIn('torch_npu',sys.modules)
  # Execute the REAL adapter.instances body with immutable fixture files.
  # Only CDLL/original solve are stubs: source/window/header/ABI checks still run.
  class Solve:
   def __init__(self,*unused):self.lib=types.SimpleNamespace(call_kernel=types.SimpleNamespace(argtypes=[None]*9));self.identity={'fixture':'software-only'}
   def launch(self,*unused):pass
   def eager(self,*unused):pass
  old=types.SimpleNamespace(MXRSolve=Solve)
  lib=types.SimpleNamespace(call_mxr_y16_control=types.SimpleNamespace(),call_mxr_y16_compensated=types.SimpleNamespace())
  with tempfile.TemporaryDirectory(prefix='mxr037-adapter-',dir=os.environ.get('MXR025_SOFTWARE_RW'))as folder:
   source=Path(folder)/'source.json';build=Path(folder)/'build.json';leaf=ref(P/'adapter.py')
   m=dict(schema='mxr.y16.compensated-source/v1',root=str(P),default_enabled=False,window=dict(start=1791916056,cutoff=1792002456),files={'adapter.py':leaf},dependencies={'old_binary':leaf},author_root='/software-only-author')
   def invoke(window,build_source=None):
    m['window']=window;source.write_text(json.dumps(m),encoding='utf8');sr=ref(source);headers={'adapter':leaf}
    b=dict(schema='mxr.y16.compensated-build/v1',source=sr if build_source is None else build_source,status='compiled_no_device',NPU=False,Devices=[],error=None,secondary=[],header_refs_before=headers,header_refs_after=headers,library=leaf)
    build.write_text(json.dumps(b),encoding='utf8')
    return A.instances(None,sr,ref(build),'software-only-device')
   with patch.dict(os.environ,MXR_Y16_EXPERIMENT_ENABLE='1'),patch.object(A,'load_old',return_value=old)as load_old,patch.object(A.ctypes,'CDLL',return_value=lib)as cdll:
    values=invoke(dict(start=1791916056,cutoff=1792002456));self.assertEqual(len(values),3);self.assertEqual(load_old.call_count,1);self.assertEqual(cdll.call_count,1)
    self.assertIs(values[1].launch.__func__,Solve.launch);self.assertIs(values[2].eager.__func__,Solve.eager)
    for wrong in(dict(start=1791879730,cutoff=1791922930),dict(start=1791916057,cutoff=1792002456),dict(start=1791916056,cutoff=1792002457)):
     with self.assertRaisesRegex(ValueError,'source-qualified'):invoke(wrong)
    with self.assertRaisesRegex(ValueError,'source-qualified'):invoke(dict(start=1791916056,cutoff=1792002456),{'foreign':True})
    self.assertEqual(load_old.call_count,1);self.assertEqual(cdll.call_count,1)
   with patch.dict(os.environ,MXR_Y16_EXPERIMENT_ENABLE='0'):
    with self.assertRaisesRegex(ValueError,'opt-in'):A.instances(None,None,None,None)
  inverse=(P/'adapter.py').read_bytes().replace(b'dict(start=1791916056,cutoff=1792002456)',b'dict(start=1791879730,cutoff=1791922930)');self.assertEqual(len(inverse),3092);self.assertEqual(hashlib.sha256(inverse).hexdigest(),'79f0cb8c3803079843ae3af6f5071ae2f91346a7d517eabde442743c2f99f5c7')
 def test14_synthetic_Newton_identity_not_hardware(self):
  # Exact 2x2 unit-lower example; no simulated Ascend arithmetic or data PASS.
  x=.1; a=.125; residual=-a-x; corrected=x+residual
  self.assertEqual(corrected,-a);self.assertLess(abs(corrected+a),abs(x+a))
 def test15_full_source_gate_and_foreign_kernel(self):
  m=dict(schema='mxr.y16.compensated-source/v1',root=str(P),default_enabled=False,window=dict(start=1791916056,cutoff=1792002456),files={n:ref(P/n)for n in('derive.py','tri_inverse_y16_impl.cpp','tri_inverse_y16.cpp')},dependencies=dict(author_impl=ref(AUTHOR/'kernels/pto/tri_inverse_impl.cpp'),author_entry=ref(AUTHOR/'kernels/pto/tri_inverse.cpp'),derive028=ref(BASE)))
  with tempfile.TemporaryDirectory(prefix='mxr034-controls-',dir=os.environ.get('MXR025_SOFTWARE_RW'))as folder:
   p=Path(folder)/'fixture.json';p.write_text(json.dumps(m),encoding='utf8');self.assertEqual(B.source(ref(p)),m);q=Path(folder)/'foreign.cpp';q.write_bytes((P/'tri_inverse_y16.cpp').read_bytes()+b'\n');m['files']['tri_inverse_y16.cpp']=ref(q);p.write_text(json.dumps(m),encoding='utf8')
   with self.assertRaisesRegex(ValueError,'full actual source derivation'):B.source(ref(p))
if __name__=='__main__':unittest.main(verbosity=2)

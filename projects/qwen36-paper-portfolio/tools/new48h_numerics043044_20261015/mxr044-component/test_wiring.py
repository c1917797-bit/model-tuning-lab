import importlib.util,sys,types,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
def load(name):
 s=importlib.util.spec_from_file_location(name,P/(name+'.py'));m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
class Tensor:
 def __init__(self,shape):self.shape=shape;self.ndim=len(shape);self._version=1;self.device='same'
 def is_contiguous(self):return True
 def __len__(self):return self.shape[0]
 def data_ptr(self):return id(self)
class Wiring(unittest.TestCase):
 def test_actual_receiver_passes_verified_cpu_tuple_no_D2H(self):
  R=load('eager_receiver');M=load('block_refine');saved=M.eager;calls=[];device=types.SimpleNamespace(type='npu')
  class T(Tensor):
   def __init__(self,shape,dtype):super().__init__(shape);self.dtype=dtype;self.device=device
   def numel(self):
    import math
    return math.prod(self.shape)
   def element_size(self):return 4
   def cpu(self):raise AssertionError('forbidden device readback')
  A=T((1,129,12,64),'f32');cu=T((2,),'i32');indices=T((3,2),'i32');torch=types.SimpleNamespace(float32='f32',bfloat16='bf16',int32='i32',int64='i64');solver=types.SimpleNamespace(minus_identity=T((64,64),'f16'))
  proof=dict(host_boundaries=(0,129),validated_length=129,qualified_length=129,chunks=3,cu_pointer=cu.data_ptr(),index_pointer=indices.data_ptr())
  def native(A,cu_seqlens=None,chunk_indices_bt=None,output_dtype=None):raise AssertionError('unexpected fallback')
  M.eager=lambda *args:calls.append(args)or'candidate'
  try:
   solve,counts=R.make_receiver(native,torch,lambda d:solver,lambda d:types.SimpleNamespace(max_bytes=512*1024**2),lambda d:'backend',lambda:True,lambda *args:proof,lambda:False,enabled=True)
   self.assertEqual(solve(A,cu,indices,'bf16'),'candidate');self.assertEqual(calls[0][-1],(0,129));self.assertEqual(counts,dict(candidate=1,native=0))
  finally:M.eager=saved
 def test_actual_cpu_association_bounds_and_reuse(self):
  C=load('metadata_certificate');A=load('metadata_association');assoc=A.Associations()
  class Meta:pass
  m=Meta();m.cu_seqlens_host=(0,64,129);m.chunk_indices_chunk64_host=(0,0,1,0,1,1);m.chunk_indices_chunk64=Tensor((3,2));cu=Tensor((3,));assoc.produced(m);assoc.attach(m,cu)
  self.assertTrue(assoc.verified(m,cu,'layer'));cert=C.certificate(m,cu,129,'layer',[129]);a=Tensor((1,129,12,64));proof=C.consume(cert,a,cu,m.chunk_indices_chunk64,None);self.assertEqual(proof['host_boundaries'],(0,64,129));self.assertFalse(assoc.verified(m,cu,'layer'))
  cu._version+=1;self.assertIsNone(C.consume(cert,a,cu,m.chunk_indices_chunk64,None))
  with self.assertRaises(ValueError):assoc.produced(m)
 def test_pair_common_policy_symmetry_and_missing_worker(self):
  C=load('common_precision');source={'sha256':'source'};d=C.environment({},'dense','/d',source);a=C.environment({},'candidate','/a',source)
  for key in('MXR_COMMON_PRECISION044_ENABLE','MXR_COMMON_PRECISION044_SOURCE_REF'):self.assertEqual(d[key],a[key])
  self.assertIn('mxr_common_precision044',d['VLLM_PLUGINS']);self.assertIn('mxr_common_precision044',a['VLLM_PLUGINS']);self.assertNotIn('mxr_block_refinement044',d['VLLM_PLUGINS']);self.assertIn('mxr_block_refinement044',a['VLLM_PLUGINS'])
  wanted={'dense':[1,2,3,4],'candidate':[5,6,7,8]};rows=[dict(source=source,arm=arm,pid=pid,allow_hf32=False,schema='mxr.common-HF32OFF/v044')for arm,ids in wanted.items()for pid in ids]
  self.assertTrue(C.pair_gate(rows,wanted,source)['common_HF32OFF_all4_both_arms'])
  with self.assertRaises(ValueError):C.pair_gate(rows[:-1],wanted,source)
  rows[-1]['allow_hf32']=True
  with self.assertRaises(ValueError):C.pair_gate(rows,wanted,source)
 def test_common_policy_actual_function_readback(self):
  C=load('common_precision');t=types.SimpleNamespace(npu=types.SimpleNamespace(matmul=types.SimpleNamespace(allow_hf32=True)));self.assertFalse(C.apply(t)['allow_hf32']);self.assertIs(t.npu.matmul.allow_hf32,False)
  with self.assertRaises(ValueError):C.apply(types.SimpleNamespace())
if __name__=='__main__':unittest.main()

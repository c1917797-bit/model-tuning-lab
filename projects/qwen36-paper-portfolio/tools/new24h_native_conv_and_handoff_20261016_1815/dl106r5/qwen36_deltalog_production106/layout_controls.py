"""CPU metadata controls only; not actual arena evidence or device admission."""
def snapshot(t):
 return dict(shape=list(t.shape),stride=list(t.stride()),storage_offset=t.storage_offset(),data_ptr=t.data_ptr(),storage_ptr=t.untyped_storage().data_ptr(),dtype=str(t.dtype),device=str(t.device),contiguous=t.is_contiguous())
def check_layout(t):
 s=snapshot(t)
 if s['dtype']!='torch.float32'or len(s['shape'])!=4 or s['shape'][1:]!=[12,128,128]:raise ValueError('nativeFP32 value-key arena shape')
 if not s['contiguous']or s['stride']!=[196608,16384,128,1]:raise ValueError('B010 has no state stride ABI; reject padding/transposed inner')
 return s
def metadata(decode,prefill,sequence,slots):
 if any(type(i)is not int or not 0<=i<slots for i in decode+prefill):raise ValueError('slot bounds')
 if len(set(decode))!=len(decode)or len(set(prefill))!=len(prefill):raise ValueError('duplicate concurrent slot')
 if set(decode)&set(prefill):raise ValueError('mixed prefill/decode temporal overlap')
 if sequence!=[0]+[1]*len(decode):raise ValueError('actual native individual lengths, not cumulative')
 return True
def identity_same(a,b):
 return all(a[k]==b[k]for k in('data_ptr','storage_ptr','storage_offset','shape','stride','dtype','device'))
if __name__=='__main__':
 import unittest,torch
 class Tests(unittest.TestCase):
  def test_dense_and_nonzero_offset(self):
   x=torch.zeros((5,12,128,128));check_layout(x);v=x[1:4];check_layout(v);self.assertGreater(v.storage_offset(),0)
   self.assertFalse(identity_same(snapshot(x[:3]),snapshot(v)));self.assertEqual(x[:3].untyped_storage().data_ptr(),v.untyped_storage().data_ptr())
  def test_padded_and_transposed_rejected(self):
   x=torch.empty(3*(196608+64));p=x.as_strided((3,12,128,128),(196672,16384,128,1))
   for t in(p,torch.zeros((3,12,128,128)).transpose(-1,-2)):
    with self.assertRaises(ValueError):check_layout(t)
  def test_mixed_disjoint_and_bad_metadata(self):
   metadata([0,2],[1],[0,1,1],3)
   for d,p,s in[([0,0],[],[0,1,1]),([0],[0],[0,1]),([3],[],[0,1]),([0,2],[],[0,1,2])]:
    with self.assertRaises(ValueError):metadata(d,p,s,3)
  def test_copy_edges_existing_actual_source(self):
   import importlib.util,pathlib
   p=pathlib.Path('C:/Users/Huawei/AppData/Local/Temp/deltalog-fresh-provider-new48h-20261014-001/qwen36_deltalog_fresh/transform.py')
   sp=importlib.util.spec_from_file_location('_existing_transform',p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
   self.assertEqual(m.copy_edge(1000,800,768,1800,2600,768,3),(1,2))
   for edges in[[(0,1),(1,2)],[(0,2),(1,2)],[(0,1),(1,0)]]:
    with self.assertRaises(ValueError):m.validate_edges(edges)
 unittest.main()

"""Discriminating software controls; no tensors/NPU/authority qualification."""
import ast,copy,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import numeric_prefix_2k as N
import render_numeric_2k as R
class Controls(unittest.TestCase):
 def test_native24_private25_boundary(self):
  for L in(2048,2174,2175,2176,3069,3070):
   g=N.shape(L);self.assertEqual(g['publication_kernel_pages'],(L+129)//128)
   self.assertEqual(g['scratch_kernel_pages'],(L+130)//128)
  g=N.shape(3070);self.assertEqual((g['publication_kernel_pages'],g['scratch_kernel_pages']),(24,25))
  self.assertEqual(N.publication_indices(3070,list(range(24)),[0,2]),[3070,3071])
  for value in(131,2047,3071,True):
   with self.assertRaises(ValueError):N.shape(value)
  with self.assertRaises(ValueError):N.publication_indices(3070,list(range(23)),[0,2])
  with self.assertRaises(ValueError):N.publication_indices(3070,list(range(24)),[0,1,2])
 def test_full2048_prefix_and_sibling_reference_discriminate(self):
  keys=[0.0]*2048;values=[0.0]*2048;values[-1]=100.0
  got=N.scalar_branch_reference(keys,values,[0,0,0],[1,3,7],[0,0,0])
  self.assertAlmostEqual(got[0],101/2049);self.assertAlmostEqual(got[1],104/2050);self.assertAlmostEqual(got[2],108/2050)
  wrong=N.scalar_branch_reference(keys[:131],values[:131],[0,0,0],[1,3,7],[0,0,0])
  self.assertNotEqual(got,wrong);self.assertNotEqual(got[1],got[2])
 def test_exact_capture_budget_and_no_guessed_fit(self):
  b=N.added_capture_budget(3070)
  self.assertEqual(b['extra_logical_bytes'],52584000);self.assertFalse(b['fit_proven']);self.assertFalse(b['runtime_admitted'])
  self.assertTrue(b['missing_actual_byte_measurements'])
  self.assertIn('failed_frame_bytes',b['missing_actual_byte_measurements'])
  self.assertEqual(b['max_single_CPU_digest_payload_bytes'],1638400)
  self.assertEqual(b['minimum_CPU_digest_tensor_plus_bytes_copy_bytes'],3276800)
  self.assertTrue(b['CPU_digest_peak_RSS_measurement_pending'])
  with self.assertRaises(ValueError):N.added_capture_budget(3070,base_logical_bytes=384*2**20)
  with self.assertRaises(ValueError):N.added_capture_budget(3070,base_logical_bytes=0,actual_wire_bytes=2**30,
    retained_first_bytes=1,checkpoint_bytes=1,combined_metadata_bytes=1,failed_frame_bytes=0)
  with self.assertRaises(ValueError):N.added_capture_budget(3070,base_logical_bytes=0,actual_wire_bytes=0,
    retained_first_bytes=0,checkpoint_bytes=0,combined_metadata_bytes=0,failed_frame_bytes=2**30+1)
  with self.assertRaises(ValueError):N.added_capture_budget(3070,base_logical_bytes=False)
  with self.assertRaises(ValueError):N.require_runtime_admission(None,{'passed':True},None)
 def test_all_five_actual_delegate_digests_required(self):
  expected={n:dict(dtype=n,shape=[1],bytes=1,sha256='unchanged',finite=True)
   for n in('query','key','value','atten_mask','block_table')}
  proof=dict(converted_before=copy.deepcopy(expected),converted_after=copy.deepcopy(expected))
  N.delegate_digests(proof,expected)
  for name in('atten_mask','block_table'):
   bad=copy.deepcopy(proof);del bad['converted_after'][name]
   with self.assertRaises(ValueError):N.delegate_digests(bad,expected)
   bad=copy.deepcopy(proof);bad['converted_after'][name]['sha256']='actual-delegate-mutation'
   with self.assertRaises(ValueError):N.delegate_digests(bad,expected)
   bad=copy.deepcopy(proof);bad['converted_before'][name]['sha256']='not-retained-before'
   bad['converted_after'][name]['sha256']='not-retained-before'
   with self.assertRaises(ValueError):N.delegate_digests(bad,expected)
  node=ast.parse('class Captured:\n'+R.OBSERVER_METHODS)
  for name in('fa_converted','fa_returned'):
   fn=next(x for x in node.body[0].body if isinstance(x,ast.FunctionDef)and x.name==name)
   fields=[x for x in ast.walk(fn)if isinstance(x,ast.Tuple)]
   self.assertTrue(any([v.value for v in x.elts if isinstance(v,ast.Constant)]==
    ['query','key','value','atten_mask','block_table']for x in fields))
 def test_dynamic_owner_and_fixed_native_pages(self):
  def f(L,v):
   owner=dict(request='r',generation=1,slot=0,length=L,version=v)
   return dict(owner=owner,ordinal=v,generation=1,staged=dict(processed_nodes=[0,2]),
    publication=dict(processed_nodes=[0,2],next_length=L+2,next_version=v+1))
  a=f(2048,0);b=f(2050,1);self.assertEqual(N.frame_domain(a)['length'],2048)
  rows=[dict(layer=i,physical_pages=list(range(24)),ownership={'actual':'same'})for i in range(3,64,4)]
  a['after_FA']=copy.deepcopy(rows);b['before_FA']=copy.deepcopy(rows);N.fixed_pages(a,b)
  b['before_FA'][0]['physical_pages'].append(24)
  with self.assertRaises(ValueError):N.fixed_pages(a,b)
  bad=f(2049,0)
  with self.assertRaises(ValueError):N.frame_domain(bad)
 def test_real_source_adapter_inverse_and_original_oracle_bytes(self):
  before=R.read_actual();b=R.adapt(before);self.assertEqual(R.inverse(b),before)
  self.assertEqual(set(b['delta']),{'fastpath_numeric_consumer.py','fastpath_numeric_observer.py','service_bridge.py','service_fia.py','numeric_prefix_2k.py'})
  text=b['files']['fastpath_numeric_consumer.py'].decode()
  self.assertIn('PREFIX.scratch',text);self.assertIn('PREFIX.require_runtime_admission',text)
  for name in('generalized_attention','actual_readers','selected_conv_write','cpu_digest_source','actual_cpu_digest'):
   old=next(n for n in ast.parse(before['fastpath_numeric_consumer.py']).body if isinstance(n,ast.FunctionDef)and n.name==name)
   new=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)and n.name==name)
   self.assertEqual(ast.dump(old,include_attributes=False),ast.dump(new,include_attributes=False))
  # GDN sequential oracle and its scalar/norm tolerances are not adapted.
  self.assertNotIn('oracle112.py',b['delta']);self.assertNotIn('independent_model.py',b['delta']);self.assertNotIn('g2_numeric.py',b['delta'])
  s=b['files']['service_fia.py'].decode()
  self.assertIn('fa_operands(probe[1],kwargs,self.record)',s)
  self.assertIn('fa_converted(probe[1],converted)',s);self.assertIn('fa_returned(probe[1],converted)',s)
  self.assertIn('fa_completed(probe[1],self.record)',s)
if __name__=='__main__':unittest.main()

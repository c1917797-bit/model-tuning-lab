import dataclasses,unittest
import torch as t
import native_seams as N
import tree_metadata111 as M
import treeconv118 as V

class Tests(unittest.TestCase):
 def test_true_native_orientation_and_alias(self):
  a=t.arange(2*12*128*128,dtype=t.float32).reshape(2,12,128,128)
  v=N.gdn_canonical_view(t,a,layout='slot,H,Dv,Dk')
  self.assertEqual(float(v[1,3,7,9]),float(a[1,3,9,7]))
  v[1,3,7,9]=-9;self.assertEqual(float(a[1,3,9,7]),-9)
  with self.assertRaises(ValueError):N.gdn_canonical_view(t,a,layout='guessed')
 def fixture(self):
  tree=N.NodeRows('actual-request',4,1,127,(11,13,17)).metadata(M.Tree)
  owners=(V.Owner('actual-request',4,1,127,0),)
  arena=t.arange(4*3*2560,dtype=t.float32).reshape(4,3,2560).bfloat16()
  inputs=t.arange(3*2560,dtype=t.float32).reshape(3,2560).bfloat16()
  return V.prepare(t,tree,owners,arena,inputs,width=4),arena
 def test_actual12arg_frontdoor_ancestor_not_flatten(self):
  trial,arena=self.fixture();original=arena.clone();w=t.ones((2560,4),dtype=t.bfloat16)
  args,kw=N.conv_call_arguments(t,trial,w,None,activation=True)
  self.assertEqual(len(args)+len(kw),12)
  self.assertEqual(kw['query_start_loc_opt'].tolist(),[0,1,2,3]);self.assertEqual(kw['cache_indices_opt'].tolist(),[0,1,2])
  self.assertTrue(t.equal(kw['conv_state'][1],kw['conv_state'][2]))
  self.assertTrue(t.equal(kw['conv_state'][1,-1],trial.inputs[0]))
  self.assertFalse(t.equal(kw['conv_state'][2,-1],trial.inputs[1]))
  self.assertTrue(t.equal(arena,original));self.assertTrue(t.isnan(args[0]).all())
  with self.assertRaises(ValueError):N.conv_call_arguments(t,trial,w,t.zeros(2560),activation=True)
 def test_positions_generation_and_partial_path(self):
  tree=N.NodeRows('r',7,3,127,(11,13,17)).metadata(M.Tree)
  self.assertEqual(tree.positions,(127,128,128));self.assertEqual(tree.commit_path(0,2,actual_generation=7,actual_slot=3),(0,2))
  self.assertEqual(tree.commit_path(0,None,actual_generation=7,actual_slot=3),())
  with self.assertRaises(ValueError):tree.commit_path(0,2,actual_generation=8,actual_slot=3)
  with self.assertRaises(ValueError):dataclasses.replace(N.NodeRows('r',7,3,127,(11,13,17)),parents=(-1,0,1)).metadata(M.Tree)
 def test_no_cpu_or_missing_ARM_as_native_proof(self):
  trial,_=self.fixture()
  with self.assertRaisesRegex(ValueError,'device/ARM'):
   N.native_tree_conv(t,None,None,None,None,trial,t.ones((2560,4),dtype=t.bfloat16),None,activation=False,op=None,actual_abi=None)

if __name__=='__main__':unittest.main()

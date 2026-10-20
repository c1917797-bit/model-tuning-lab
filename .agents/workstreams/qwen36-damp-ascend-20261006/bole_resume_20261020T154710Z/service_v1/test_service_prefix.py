"""CPU preparation of the actual unchanged component helpers at new prefixes."""
import unittest,torch
import adapter as A,treeconv118 as V,tree_metadata111 as M,native_seams as N

class Tests(unittest.TestCase):
 def test_actual_tree_convolution_preparer_accepts_each_bounded_service_prefix(self):
  arena=torch.arange(4*3*2560,dtype=torch.float32).reshape(4,3,2560).to(torch.bfloat16)
  inputs=torch.arange(3*2560,dtype=torch.float32).reshape(3,2560).to(torch.bfloat16)
  before=arena.clone()
  for length in range(131,136):
   tree=N.NodeRows('service',1,2,length,(4,5,6)).metadata(M.Tree)
   owner=V.Owner('service',1,2,length,0)
   trial=V.prepare(torch,tree,(owner,),arena,inputs,width=4,node_budget=3)
   self.assertEqual(trial.owners,(owner,));self.assertTrue(torch.equal(trial.initial[0],arena[2]))
   self.assertTrue(torch.equal(trial.histories[0],arena[2]))
   self.assertTrue(torch.equal(trial.histories[1],torch.cat((arena[2,1:],inputs[:1]))))
   self.assertTrue(torch.equal(trial.histories[2],trial.histories[1]))
   self.assertTrue(torch.equal(arena,before))
 def test_actual_paged_preparer_builds_owned_prefix_and_sibling_mask_at_each_length(self):
  q=torch.zeros(3,6,256,dtype=torch.bfloat16)
  k=torch.ones(3,1,256,dtype=torch.bfloat16);v=2*k
  kc=torch.arange(2*128*256,dtype=torch.float32).reshape(2,128,1,256).to(torch.bfloat16)
  vc=-kc;table=(1,0)
  for length in range(131,136):
   owner=A.Owner('service',1,0,length,0)
   trial=A.prepare(torch,owner,q,k,v,kc,vc,table)
   self.assertEqual(trial['scratch_k'].shape,(2,128,1,256))
   self.assertEqual(trial['mask'].shape,(3,length+3))
   expected=torch.ones(3,length+3,dtype=torch.bool)
   expected[:,:length+1]=False;expected[1,length+1]=False;expected[2,length+2]=False
   self.assertTrue(torch.equal(trial['mask'],expected))
   source=torch.cat((kc[1],kc[0]))[:length]
   self.assertTrue(torch.equal(trial['scratch_k'].reshape(-1,1,256)[:length],source))
   self.assertTrue(torch.equal(kc,trial['anchor_k']))

if __name__=='__main__':unittest.main()

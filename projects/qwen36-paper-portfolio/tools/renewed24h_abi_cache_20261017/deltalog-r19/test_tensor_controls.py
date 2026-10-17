"""Real independent consumer CPU controls, not fake NPU observations."""
import copy,pathlib,unittest
import tensor_consumer as C
class Tests(unittest.TestCase):
 def state(self,torch):
  return dict(base=torch.zeros(1,12,128,128),k_log=torch.zeros(1,4,7,128,dtype=torch.bfloat16),u_log=torch.zeros(1,12,7,128),lambda_log=torch.zeros(1,12,16),decay=torch.zeros(1,12,16),length=torch.zeros(1,12,16,dtype=torch.int32))
 def prefill(self):
  import torch
  R=C.module();before=self.state(torch);after=self.state(torch);after['base'][0,:,0,0]=.5
  q=torch.zeros(1,1,4,128,dtype=torch.bfloat16);q[:,:,:,0]=1;k=q.clone();v=torch.zeros(1,1,12,128,dtype=torch.bfloat16);v[:,:,:,0]=1
  expected=torch.zeros(1,1,12,128,dtype=torch.bfloat16);expected[:,:,:,0]=.5*128**-.5
  i=dict(q=q,k=k,v=v,g=torch.zeros(1,1,12),beta=torch.full((1,1,12),.5,dtype=torch.bfloat16),initial_state=torch.zeros(1,12,128,128),cu_seqlens=torch.tensor([0,1]),use_qk_l2norm_in_kernel=True)
  raw=dict(actual_NPU=True,actual_ids=[7],has_initial=[False],before=before,after=after,chunks=[dict(inputs=i,output=expected,final_state=after['base'].transpose(-1,-2).clone())],core_output=expected.reshape(1,1536))
  return torch,R,raw
 def test_known_basis_prefill_independent(self):
  torch,R,r=self.prefill();state,metrics=C.prefill(torch,R,r,None);self.assertTrue(metrics['passed']);self.assertEqual(float(state[0,0,0]),.5)
 def test_wrong_returned_core_rejected(self):
  torch,R,r=self.prefill();r['core_output']=r['core_output'].clone();r['core_output'].zero_()
  with self.assertRaises(ValueError):C.prefill(torch,R,r,None)
 def test_new_request_cannot_use_nonzero_native_initial(self):
  torch,R,r=self.prefill();r['chunks'][0]['inputs']['initial_state'].fill_(1)
  with self.assertRaises(ValueError):C.prefill(torch,R,r,None)
 def test_cannot_seed_independent_from_candidate(self):
  torch,R,r=self.prefill();r['has_initial']=[True]
  with self.assertRaises(ValueError):C.prefill(torch,R,r,None)
 def test_merge7_to0_and_wrong_output_metrics(self):
  import torch
  torch.set_num_threads(1);R=C.module();before=self.state(torch);before['length'][:,:,0]=7;after=self.state(torch);inputs=dict(query=torch.zeros(1,4,128,dtype=torch.bfloat16),key=torch.zeros(1,4,128,dtype=torch.bfloat16),value=torch.zeros(1,12,128,dtype=torch.bfloat16),g=torch.zeros(1,12),beta=torch.full((1,12),.5,dtype=torch.bfloat16))
  inputs['query'][:,:,0]=1;inputs['key'][:,:,0]=1;inputs['value'][:,:,0]=1;after['base'][0,:,0,0]=.5;out=torch.zeros(1,12,128,dtype=torch.bfloat16);out[:,:,0]=.5*128**-.5
  raw=dict(actual_NPU=True,actual_ids=[7],before=before,after=after,inputs=inputs,input_after=copy.deepcopy(inputs),pointer_before={'x':1},pointer_after={'x':1},output=out,native_output=out.clone(),native_before=before['base'].clone(),native_after=after['base'].clone(),scale=128**-.5)
  from test_model_precast import attach
  previous=torch.zeros(12,128,128,dtype=torch.float64);attach(raw,previous)
  state,m=C.decode(torch,R,raw,previous,7);self.assertTrue(m['passed']);self.assertEqual(m['length_after'],0)
  raw['output']=out*2
  with self.assertRaises(ValueError):C.decode(torch,R,raw,torch.zeros_like(state),7)
if __name__=='__main__':unittest.main()

"""Real CPU oracle arithmetic/negative controls, NOT NPU or model evidence."""
import copy,unittest
import tensor_consumer as C

class Controls(unittest.TestCase):
 def fixture(self):
  import torch
  from test_tensor_controls import Tests
  R=C.module();before=Tests().state(torch);after=Tests().state(torch);after['base'][0,:,0,0]=.5;before['length'][:,:,0]=7
  inputs=dict(query=torch.zeros(1,4,128,dtype=torch.bfloat16),key=torch.zeros(1,4,128,dtype=torch.bfloat16),value=torch.zeros(1,12,128,dtype=torch.bfloat16),g=torch.zeros(1,12),beta=torch.full((1,12),.5,dtype=torch.bfloat16))
  for name in('query','key','value'):inputs[name][:,:,0]=1
  out=torch.zeros(1,12,128,dtype=torch.bfloat16);out[:,:,0]=.5*128**-.5
  raw=dict(actual_NPU=True,actual_ids=[7],before=before,after=after,inputs=inputs,input_after=copy.deepcopy(inputs),pointer_before={'x':1},pointer_after={'x':1},output=out,native_output=out.clone(),native_after=after['base'].clone(),scale=128**-.5)
  previous=torch.zeros(12,128,128,dtype=torch.float64)
  from test_model_precast import attach
  return torch,R,attach(raw,previous),previous
 def test_exact013_double_round_midpoint_controls(self):
  import torch
  self.assertTrue(C.direct_module().controls(torch)['double_round_negative_control'])
 def test_correct_BF16_rounding_not_false_uncast_failure(self):
  import torch
  truth=torch.full((12,128),1+2**-8+2**-30,dtype=torch.float64);D=C.direct_module();actual=D.round_bf16(torch,truth)
  result=C.readout(torch,actual,truth);self.assertEqual(result['output_error'],0);self.assertGreater(result['uncast_CPU64_output_error'],.00303);self.assertEqual(result['independent_CPU64_BF16_floor'],result['uncast_CPU64_output_error'])
  self.assertFalse(torch.equal(actual,truth.float().bfloat16()))
 def test_wrong_output_dtype_shape_head_rejected(self):
  import torch
  truth=torch.ones(12,128,dtype=torch.float64)
  for bad in(torch.ones(12,128),torch.ones(1,12,128,dtype=torch.bfloat16),torch.ones(4,128,dtype=torch.bfloat16)):
   with self.assertRaises(ValueError):C.readout(torch,bad,truth)
 def test_nonfinite_or_reference_overflow_rejected(self):
  import torch
  truth=torch.ones(12,128,dtype=torch.float64);actual=torch.ones(12,128,dtype=torch.bfloat16)
  for bad in(float('nan'),float('inf'),float(2**128)):
   wrong=truth.clone();wrong[0,0]=bad
   with self.assertRaises(ValueError):C.readout(torch,actual,wrong)
 def test_decode_wrong_scale_hard_source_contract(self):
  torch,R,raw,prev=self.fixture()
  for bad in(1.,True,float('nan')):
   wrong=copy.deepcopy(raw);wrong['scale']=bad
   with self.assertRaisesRegex(ValueError,'fixed source scale'):C.decode(torch,R,wrong,prev,7)
 def test_decode_wrong_head_input_rejected(self):
  torch,R,raw,prev=self.fixture();raw['inputs']['query']=raw['inputs']['query'][:,:3]
  with self.assertRaisesRegex(ValueError,'Hq4/Hv12'):C.decode(torch,R,raw,prev,7)
 def test_decode_wrong_slot_join_rejected(self):
  torch,R,raw,prev=self.fixture();raw['actual_ids']=[8]
  with self.assertRaisesRegex(ValueError,'slot to compact0'):C.decode(torch,R,raw,prev,7)
 def test_decode_wrong_actual_output_and_state_still_fail(self):
  torch,R,raw,prev=self.fixture();raw['output']=raw['output']*2
  with self.assertRaises(ValueError):C.decode(torch,R,raw,prev,7)
  torch,R,raw,prev=self.fixture();raw['after']['base'][0,0,0,0]=1
  with self.assertRaises(ValueError):C.decode(torch,R,raw,prev,7)
  torch,R,raw,prev=self.fixture();raw['native_output'][0,0,0]=float('nan')
  with self.assertRaisesRegex(ValueError,'native-peer'):C.decode(torch,R,raw,prev,7)
  torch,R,raw,prev=self.fixture();raw['before']['base'][0,0,1,1]=float('nan')
  with self.assertRaisesRegex(ValueError,'active restored-before'):C.decode(torch,R,raw,prev,7)
 def test_explicit_report_contract_not_old_unknown_PASS(self):
  self.assertEqual(C.VALIDATION_CONTRACT['direct_round_sha256'],C.DIRECT_SHA);self.assertEqual(C.VALIDATION_CONTRACT['output_limit'],.00303);self.assertEqual(C.VALIDATION_CONTRACT['state_limit'],7.92e-7);self.assertTrue(C.VALIDATION_CONTRACT['uncast_metrics_diagnostic_only'])
 def test_bridge_actual_binding_rejects_old_template_or_future_source(self):
  import bind_source as B
  from unittest.mock import patch
  reviewed=dict(root='/actual035repair1',files={'final':'pins'},validation_contract={'new':'contract'});ref={'software-only':'actual-existing-ref'};m=dict(reviewed_domain_template_ref={'software-only':'template'},reviewed_domain_files=reviewed['files'],expected_bound_bridge_ref=None)
  bm=dict(reviewed,prepared_template=m['reviewed_domain_template_ref'],prepared_only=False)
  with patch.object(B.O,'obj',return_value=reviewed):
   B.bind_actual_bridge(m,ref,bm);self.assertEqual(m['expected_bound_bridge_ref'],ref)
   for wrong in(dict(bm,prepared_only=True),dict(bm,prepared_template={'old':'035'}),dict(bm,files={'old':'pins'})):
    with self.assertRaises(ValueError):B.bind_actual_bridge(dict(m),ref,wrong)
if __name__=='__main__':unittest.main()

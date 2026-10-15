"""CPU software ABI control of REAL collector and consumers, NOT NPU evidence."""
import copy,tempfile,types,unittest
from pathlib import Path
import torch
import sidecar_capture as S,sidecar_audit as A,precast as P
import oracle as R,direct_round as D,domain_consumer as C,bridge_io
REQUIRED={'before','debug_before','after','debug_after','production_output','debug_output','actual_precast_FP32','production_debug_bitwise','inputs_unchanged','sidecar_redzones_pass','sidecar_guards_before','sidecar_guards_after','pointers_before','pointers_after','debug_pointers_before','debug_pointers_after'}
class CPUProxy:
 """No fake sys.modules/backend: CPU torch with explicit synchronization no-op."""
 npu=types.SimpleNamespace(synchronize=lambda:None)
 def __getattr__(self,n):return getattr(torch,n)
class Contract(unittest.TestCase):
 def run_fixture(self,root):
  states=dict(base=torch.zeros(6,12,128,128),k_log=torch.zeros(6,4,7,128,dtype=torch.bfloat16),u_log=torch.zeros(6,12,7,128),lambda_log=torch.zeros(6,12,16),decay=torch.zeros(6,12,16),length=torch.zeros(6,12,16,dtype=torch.int32))
  inp=dict(query=torch.zeros(1,4,128,dtype=torch.bfloat16),key=torch.zeros(1,4,128,dtype=torch.bfloat16),value=torch.zeros(1,12,128,dtype=torch.bfloat16),g=torch.zeros(1,12),beta=torch.zeros(1,12,dtype=torch.bfloat16),actual_seq_lengths=torch.tensor([0,1],dtype=torch.int32),ssm_state_indices=torch.tensor([0],dtype=torch.int32),scale=128**-.5)
  args=[inp[n]for n in('query','key','value','g','beta')]+[states[n]for n in S.FIELDS]+[inp['actual_seq_lengths'],inp['ssm_state_indices']]
  def production(*args):return torch.zeros((1,12,128),dtype=torch.bfloat16)
  def diagnostic(*args):args[-1].zero_();return production(*args[:-1])
  collector=S.Capture(CPUProxy(),production,diagnostic)
  def sink(name,value):
   path=root/name
   with path.open('xb')as stream:torch.save(value,stream)
   return bridge_io.ref(path)
  collector.sink=sink;z=collector(*args);rr=collector.take('mixed');actual=torch.load(rr['path'],weights_only=False)
  raw=dict(state=states,ids=torch.tensor([0,1]),candidate_output=torch.cat((z,torch.zeros(64,12,128,dtype=torch.bfloat16))),native_output=torch.cat((z,torch.zeros(64,12,128,dtype=torch.bfloat16))),native_state=states['base'].clone(),captures=dict(decode=[dict(before=states,inputs=inp,output=z,actual_sidecar043=rr)]))
  return collector,actual,raw
 def test_actual_collector_to_both_consumers(self):
  with tempfile.TemporaryDirectory()as d:
   collector,s,raw=self.run_fixture(Path(d));self.assertEqual(set(s),REQUIRED)
   self.assertTrue(A.audit(torch,R,P,s)['passed'])
   self.assertTrue(all(x['request_pass']for x in C.per_request_metrics(torch,R,raw,D)))
   for a,b in zip(s['before'],s['debug_before']):self.assertEqual(a.dtype,b.dtype);self.assertTrue(P.bits(torch,a,b));self.assertNotEqual(a.data_ptr(),b.data_ptr())
   self.assertEqual(collector.pending,None);self.assertEqual(len(collector.mixed_records),1)
 def test_original_missing_field_and_corrupted_before_rejected(self):
  with tempfile.TemporaryDirectory()as d:
   collector,s,raw=self.run_fixture(Path(d));bad=copy.deepcopy(s);del bad['debug_before']
   with self.assertRaises(KeyError):A.audit(torch,R,P,bad)
   path=Path(d)/'missing.pt';torch.save(bad,path);raw['captures']['decode'][0]['actual_sidecar043']=bridge_io.ref(path)
   with self.assertRaises(KeyError):C.per_request_metrics(torch,R,raw,D)
   s['debug_before'][5][0,0,0,0]=1.
   with self.assertRaises(ValueError):A.audit(torch,R,P,s)
 def test_all_record_fields_are_required_by_source_contract(self):
  with tempfile.TemporaryDirectory()as d:
   _,s,raw=self.run_fixture(Path(d))
   self.assertTrue(REQUIRED<=set(s));self.assertEqual(s['before'][0].device.type,'cpu')
   # Software fixture is explicitly not a device/registration qualification.
   self.assertIsInstance(s['actual_precast_FP32'],torch.Tensor)
if __name__=='__main__':unittest.main()

import ast,importlib.util,pathlib,sys,unittest
P=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import regression,consumer
class Controls(unittest.TestCase):
 def test_strict_state_negative(self):
  import torch
  s=dict(base=torch.zeros((4,12,128,128)),k_log=torch.zeros((4,4,7,128),dtype=torch.bfloat16),u_log=torch.zeros((4,12,7,128)),lambda_log=torch.zeros((4,12,16)),decay=torch.zeros((4,12,16)),length=torch.zeros((4,12,16),dtype=torch.int32))
  for t in s.values():t[-2:]=13
  s['u_log'][0,0,6,0]=float('nan')
  clone=lambda:{k:t.clone()for k,t in s.items()}
  a=clone();self.assertTrue(all(regression.strict_state(torch,s,a,[0]).values()))
  a['u_log'][1,0,0,0]=-0.;self.assertFalse(regression.strict_state(torch,s,a,[0])['inactive_bytes'])
  a=clone();a['decay'][0,0,1]=1.;self.assertFalse(regression.strict_state(torch,s,a,[0])['metadata_padding_bytes'])
  a=clone();a['base'][-1,0,0,0]=0.;self.assertFalse(regression.strict_state(torch,s,a,[0])['guards'])
 def test_active_lambda_and_inactive_NaN(self):
  import torch,oracle
  s=dict(base=torch.zeros((4,12,128,128)),k_log=torch.zeros((4,4,7,128),dtype=torch.bfloat16),u_log=torch.zeros((4,12,7,128)),lambda_log=torch.zeros((4,12,16)),decay=torch.zeros((4,12,16)),length=torch.zeros((4,12,16),dtype=torch.int32))
  for t in s.values():t[-2:]=13
  s['u_log'][1,0,6,0]=float('nan');s['length'][0,:,0]=1
  a={k:v.clone()for k,v in s.items()};a['lambda_log'][0,:,1]=.25;a['length'][0,:,0]=2
  self.assertTrue(all(regression.strict_state(torch,s,a,[0]).values()))
  for fn in (regression.byte_invariants,consumer.byte_transition_invariants):
   self.assertTrue(all(fn(torch,oracle,s,a,[0]).values()))
  a['lambda_log'][0,:,7]=.25;self.assertFalse(regression.strict_state(torch,s,a,[0])['metadata_padding_bytes']);a['lambda_log'][0,:,7]=0.
  a['u_log'][1,0,0,0]=-0.
  for fn in (regression.byte_invariants,consumer.byte_transition_invariants):self.assertFalse(fn(torch,oracle,s,a,[0])['untouched_bitwise'])
 def test_pointer_negatives(self):
  import torch
  t=torch.zeros((2,12,128));m=regression.identity(t);m['device']='npu:0'
  self.assertTrue(consumer.pointer_binding(m,t))
  for key,bad in [('storage_offset',-1),('data_ptr',m['data_ptr']+4),('dtype','torch.bfloat16'),('storage_nbytes',1),('stride',[0,128,1])]:
   x=dict(m);x[key]=bad;self.assertFalse(consumer.pointer_binding(x,t),key)
 def test_AST(self):
  for f in P.glob('*.py'):ast.parse(f.read_bytes())
 def test_no_full_NPU_loop(self):
  s=(P/'producer.py').read_text(encoding='utf8');self.assertNotIn("for phase,batch,steps",s);self.assertIn("regression_run(",s)
  h=(P/'host.py').read_text(encoding='utf8');self.assertIn("cp['debug_meta_ref']",h)
if __name__=='__main__':unittest.main()

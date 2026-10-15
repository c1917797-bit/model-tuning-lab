import importlib.util,pathlib,sys,subprocess,unittest,copy,json
P=pathlib.Path(__file__).resolve().parent
def load(n):
 s=importlib.util.spec_from_file_location(n,P/(n+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Contract(unittest.TestCase):
 def test_direct_integer_RNE(self):
  import torch
  D=load('direct_round');D.controls(torch)
  x=torch.tensor([1+2**-8-2**-30],dtype=torch.float64);r=D.round_bf16(torch,x)
  self.assertGreater(float((r.double()-x).abs().max()/x.abs().max()),.00303)
  self.assertEqual(float(r[0]),1.)
 def fixture(self):
  import torch
  R=load('oracle');D=load('direct_round');torch.manual_seed(2610154301)
  st=dict(base=torch.randn(6,12,128,128)*.005,k_log=torch.zeros(6,4,7,128,dtype=torch.bfloat16),u_log=torch.zeros(6,12,7,128),lambda_log=torch.zeros(6,12,16),decay=torch.zeros(6,12,16),length=torch.zeros(6,12,16,dtype=torch.int32))
  i=dict(query=torch.randn(1,4,128).bfloat16(),key=(torch.randn(1,4,128)*.01).bfloat16(),value=torch.randn(1,12,128).bfloat16(),g=torch.full((1,12),-.01),beta=torch.full((1,12),.3),ssm_state_indices=torch.tensor([0]),actual_seq_lengths=torch.tensor([0,1]),scale=128**-.5)
  after,o=R.advance(torch,R.restore(torch,st,0),i,0);out=D.round_bf16(torch,o);post=copy.deepcopy(st);post['base'][0]=after.float()
  native=post['base'].clone()
  raw=dict(state=post,ids=torch.tensor([0,1]),candidate_output=torch.cat([out.unsqueeze(0),torch.zeros(64,12,128,dtype=torch.bfloat16)]),native_output=torch.cat([out.unsqueeze(0),torch.zeros(64,12,128,dtype=torch.bfloat16)]),native_state=native,captures=dict(decode=[dict(before=st,inputs=i,output=out.unsqueeze(0))]))
  return torch,R,D,raw
 def test_wrongscale_head_slot_input(self):
  torch,R,D,raw=self.fixture();C=load('domain_consumer')
  self.assertTrue(all(x['request_pass'] for x in C.original_per_request_metrics(torch,R,raw,D)))
  bad=copy.deepcopy(raw);bad['captures']['decode'][0]['inputs']['scale']*=2
  with self.assertRaises(ValueError):C.original_per_request_metrics(torch,R,bad,D)
  bad=copy.deepcopy(raw);bad['captures']['decode'][0]['inputs']['ssm_state_indices'][0]=2
  with self.assertRaises(ValueError):C.original_per_request_metrics(torch,R,bad,D)
  bad=copy.deepcopy(raw);bad['captures']['decode'][0]['output'][0]=bad['captures']['decode'][0]['output'][0].roll(1,0)
  self.assertFalse(C.original_per_request_metrics(torch,R,bad,D)[0]['request_pass'])
  bad=copy.deepcopy(raw);bad['captures']['decode'][0]['output']=bad['captures']['decode'][0]['output'].double()
  with self.assertRaises(ValueError):C.original_per_request_metrics(torch,R,bad,D)
  bad=copy.deepcopy(raw);bad['captures']['decode'][0]['output']=bad['captures']['decode'][0]['output'][:,:,:1]
  with self.assertRaises(ValueError):C.original_per_request_metrics(torch,R,bad,D)
  bad=copy.deepcopy(raw);bad['captures']['decode'][0]['inputs']['query']*=2
  self.assertFalse(C.original_per_request_metrics(torch,R,bad,D)[0]['request_pass'])
 def test_native_ABI_and_seed_threeway(self):
  s=(P/'domain_consumer.py').read_text();self.assertIn("[0]+[1]*batch",s);self.assertNotIn("== list(range(batch+1))",s)
  for n in('domain_consumer.py','qwen36_deltalog_fresh/native_fixture.py','qwen36_deltalog_fresh/capture_evidence.py'):
   s=(P/n).read_text();self.assertIn('2610154301',s);self.assertNotIn('260815533',s)
 def test_new_schema_scope(self):
  s=(P/'preregister.py').read_text();self.assertIn('deltalog.diagnostic-consumption/v043',s);self.assertIn('actual-FP32-precast-per-request-empirical/v043',s)
 def test_real_cold_defaultoff(self):
  for n in('host.py','consume_pair.py','domain_entry.py','entry.py','producer.py','consume.py','bind_composite.py','run031.py'):
   r=subprocess.run([sys.executable,'-I','-B',str(P/n)],capture_output=True,text=True);self.assertEqual(r.returncode,0,(n,r.stderr));self.assertIn('disabled',r.stdout)
if __name__=='__main__':unittest.main()


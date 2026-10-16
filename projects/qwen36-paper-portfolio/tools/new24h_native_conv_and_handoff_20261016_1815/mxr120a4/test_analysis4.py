import importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
def load(n):
 s=importlib.util.spec_from_file_location('_A4_test_'+n,P/(n+'.py'));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
R=load('reader');D=load('direct_rne')
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  import torch
  torch.set_num_threads(1);cls.t=torch
 def test_01_direct_midpoints_signedzero_subnormal_overflow(self):
  t=self.t;x=t.tensor([1+2**-8+2**-30,1+2**-8-2**-30,1+2**-8,-1-2**-8-2**-30,-1-2**-8+2**-30,-1-2**-8,0.,-0.,2**-134,2**-134+2**-150,2**-133,-2**-133,2**128,-2**128],dtype=t.float64);v=D.round_bf16(t,x)
  want=t.tensor([1+2**-7,1,1,-1-2**-7,-1,-1,0,-0.,0,2**-133,2**-133,-2**-133,float('inf'),-float('inf')],dtype=t.float64);self.assertTrue(t.equal(v.double(),want));self.assertEqual(v.view(t.int16)[7].item(),-32768);self.assertNotEqual(v[0].item(),x[0].float().bfloat16().item())
 def test_02_wrong_precision_rejects(self):
  with self.assertRaises(ValueError):D.round_bf16(self.t,self.t.ones(1,dtype=self.t.float32))
 def test_03_error_vector_cancellation_same_denominator(self):
  t=self.t;r=R.vector_terms(t,t.tensor([1.]),t.tensor([2.]),t.tensor([1.]));self.assertEqual(r['total_norm'],0);self.assertEqual(r['cosine'],-1);self.assertEqual(r['actual_minus_operational_norm'],1);self.assertTrue(r['not_additive_error_budget'])
 def test_04_zero_reference_and_nonfinite_not_hidden(self):
  t=self.t;r=R.vector_terms(t,t.zeros(2),t.ones(2),t.zeros(2));self.assertIsNone(r['total_relative']);self.assertEqual(r['total_norm'],0)
  with self.assertRaises(ValueError):R.vector_terms(t,t.tensor([float('nan')]),t.zeros(1),t.zeros(1))
 def test_05_missing_wrong_hash_bytes_refuses(self):
  with tempfile.TemporaryDirectory()as folder:
   p=Path(folder)/'x';p.write_bytes(b'x');r=R.ref(p);self.assertEqual(R.checked(r),p)
   for field,value in(('bytes',2),('sha256','0'*64),('path',(Path(folder)/'absent').as_posix())):
    with self.assertRaises(ValueError):R.checked(dict(r,**{field:value}))
 def test_06_first_B_vs_later_H_and_signedzero(self):
  t=self.t
  def arm():return dict(B=t.zeros((1,2048,12,64),dtype=t.bfloat16),W=t.zeros((1,2048,12,128),dtype=t.bfloat16),U=t.zeros((1,2048,12,128),dtype=t.bfloat16),Hentry=t.zeros((1,12,32,128,128),dtype=t.bfloat16),Vnew=t.zeros((1,12,2048,128),dtype=t.bfloat16))
  a={n:arm()for n in('saved_candidate','native','cpu64_cast')};a['native']['B'][0,64,0,0]=-0.;a['native']['Hentry'][0,0,2,0,0]=1;r=R.pair_first(t,a)['saved_candidate__native'];self.assertEqual(r['B'],1);self.assertEqual(r['Hentry'],2)
 def test_07_actual_cli_OFF_and_ON_missing_source(self):
  p=P/'reader.py';r=subprocess.run([sys.executable,'-I','-B',str(p)],capture_output=True,text=True,timeout=10);self.assertEqual(r.returncode,0)
  r=subprocess.run([sys.executable,'-I','-B',str(p),'--execute','--source-ref',json.dumps(dict(path=(P/'missing').as_posix(),bytes=0,sha256='0'*64)),'--output','/unused'],capture_output=True,text=True,timeout=10);self.assertNotEqual(r.returncode,0);self.assertIn('exact ordinary immutable input',r.stderr);self.assertNotIn('torch_npu',r.stderr)
 def test_08_real_owned_alias_command_and_budget(self):
  path=P/'owned'/'owned_analysis.py'if sys.platform!='linux'else Path(json.loads((P/'SOURCE_MANIFEST.json').read_bytes())['owner_module_ref']['path']);s=importlib.util.spec_from_file_location('_A4_actual_owner',path);o=importlib.util.module_from_spec(s);s.loader.exec_module(o);m=json.loads((path.parent/'SOURCE_MANIFEST.json').read_bytes());a=o.child_command(m,m['actual_stage_ref']);self.assertEqual(a[:2],['-I','-B']);self.assertEqual(a[-1],'/adakv-results/ANALYSIS120A4.json');self.assertEqual(o.CAP,2**30);self.assertEqual(m['resource']['guest_bytes'],8*2**30);self.assertFalse(m['qualified'])
  from unittest.mock import patch
  cases=m['exact_actual_cases'];raw=[dict(arm=n,raw=dict(path='/software-only/'+str(i)+'/'+n,bytes=1,sha256='0'*64))for i,n in enumerate(('saved_candidate','native','cpu64_cast'))];prior=dict(counterfactual=dict(positive_g_and_safe_exp={},variants={}))
  d=dict(schema='mxr.fixed-actual-A-G-B-RNE-vector-analysis/v120-analysis4',source=m['analysis4_source_ref'],actual_stage_ref=m['actual_stage_ref'],actual_A3_report_ref=m['actual_A3_report_ref'],qualification=False,model=False,performance=False,task=False,NPU=False,old_failures_preserved=True,cases=[dict(case=c,actual_raw_refs=raw,same_actual_A_G=True,saved_candidate_anchor_bitwise=True,canonical_A3_anchor_bitwise=True,positive_g_and_safe_exp={},old_actual_registered_metrics={})for c in cases]);software=dict(source={},tests=8,passed=True,NPU=False)
  def metadata(r):
   if r==m['guest_source']:return dict(cases=cases)
   if r==m['actual_stage_ref']:return dict(result=dict(cases=[dict(result=dict(rows=raw))for c in cases]))
   if r==m['actual_A3_report_ref']:return dict(cases=[prior for c in cases])
   raise AssertionError('unexpected metadata read')
  with patch.object(o,'obj',side_effect=metadata):
   o.receive_report(d,m,{},software)
   d['cases'][0]['canonical_A3_anchor_bitwise']=False
   with self.assertRaises(ValueError):o.receive_report(d,m,{},software)
if __name__=='__main__':unittest.main()

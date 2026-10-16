import importlib.util,json,subprocess,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('_CF120_test',P/'counterfactual.py');D=importlib.util.module_from_spec(s);s.loader.exec_module(D)


class Controls(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  import torch
  cls.t=torch;torch.set_num_threads(1);m=json.loads((P/'SOURCE_MANIFEST.json').read_bytes());r=m['original_reference_ref']
  if sys.platform!='linux':
   local=D.ref(P.parent/'mxr-two-residual-model-new24h-098-repair5/boundary_oracle.py');D.need((r['bytes'],r['sha256'])==(local['bytes'],local['sha256']),'exact local original source relocation');r=local
  cls.O=D.load(r,'_CF120_untouched_original');cls.H=D.load(D.ref(P/'reference_inputs.py'),'_CF120_hook');cls.m=m
  if sys.platform=='linux':gm=D.obj(m['guest_source_ref']);mr=gm['original_metrics']
  else:
   gm=json.loads((P.parent/'mxr-r5-prefill-counterfactual-new24h-120-repair2/SOURCE_MANIFEST.json').read_bytes());mr=D.ref(P.parent/'mxr-r118-capture-20261013-001/consume_capture.py');D.need(mr['sha256']==gm['original_metrics']['sha256'],'exact original metric source')
  cls.M=D.load(mr,'_CF120_original_metric')
 def fixture(self):
  t=self.t;gen=t.Generator().manual_seed(1200301);q=(t.randn((1,2048,4,128),generator=gen)*.03).to(t.bfloat16);v=(t.randn((1,2048,12,128),generator=gen)*.02).to(t.bfloat16)
  return dict(q=q,k=q.clone(),v=v,g=t.full((1,2048,12),-.002),beta=t.full((1,2048,12),.1,dtype=t.bfloat16),initial_state=t.full((1,12,128,128),.0001),cu_seqlens=t.tensor([0,2048],dtype=t.int32),scale=128**-.5,already_normalized=True)
 def actual(self,base):
  t=self.t;A=t.cat([r['A32'].transpose(0,1)for r in base['trace']],0).unsqueeze(0).float();G=t.cat([r['g_cumsum'].transpose(0,1)for r in base['trace']],0).unsqueeze(0).float();return A,G
 def test_01_cold_I_off_help(self):
  for flags in([],['--help']):
   p=subprocess.run([sys.executable,'-I','-B',str(P/'counterfactual.py'),*flags],capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr)
 def test_02_actual_nonzero2K_original_baseline_identity_and_hooks(self):
  t=self.t;x=self.fixture();base=self.O.evaluate(t,x);A,G=self.actual(base);D.validate_operands(t,x,A,G)
  got=self.H.evaluate(t,x);self.assertTrue(D.exact_baseline(t,base,got)['all_trace_fields_bitwise'])
  for a,g in((A,None),(None,G),(A,G)):
   # Feeding exactly the canonical operands cannot change any tensor.
   v=self.H.evaluate(t,x,actual_A=a,actual_G=g);self.assertTrue(D.exact_baseline(t,base,v)['all_trace_fields_bitwise'])
  pack=lambda key:t.cat([r[key].transpose(0,1)for r in base['trace']],0).unsqueeze(0).bfloat16()
  row=dict(A=A,G=G,B=pack('B'),W=pack('W'),U=pack('U'),Hentry=t.stack([r['Hstart']for r in base['trace']],dim=1).unsqueeze(0).bfloat16(),Vnew=t.cat([r['vnew']for r in base['trace']],dim=1).unsqueeze(0).bfloat16(),output=base['output'].bfloat16(),state=base['state'].float())
  report=D.evaluate_case(t,self.O,self.H,self.M,x,A,G,{name:row for name in('saved_candidate','native','cpu64_cast')})
  self.assertEqual(set(report['variants']),set(D.VARIANTS));self.assertFalse(report['qualification']);self.assertTrue(report['baseline_identity']['all_trace_fields_bitwise']);self.assertEqual(len(report['variants']['actual_A_and_G']['chunks']),32)
  self.assertEqual(report['variants']['actual_A_and_G']['effect_vs_original_baseline']['state']['max_abs'],0)
  self.assertLess(len(json.dumps(report)),2**20)
 def test_03_A_only_and_G_only_are_independent_inputs(self):
  t=self.t;x=self.fixture();base=self.O.evaluate(t,x);A,G=self.actual(base)
  alteredA=A.clone();alteredA[0,1,0,0]+=.03
  a=self.H.evaluate(t,x,actual_A=alteredA)
  self.assertNotEqual(D.fp(t,a['trace'][0]['B']),D.fp(t,base['trace'][0]['B']));self.assertEqual(D.fp(t,a['trace'][0]['g_cumsum']),D.fp(t,base['trace'][0]['g_cumsum']))
  alteredG=G.clone();alteredG[:,1:64]-=.02
  g=self.H.evaluate(t,x,actual_G=alteredG)
  self.assertNotEqual(D.fp(t,g['trace'][0]['g_cumsum']),D.fp(t,base['trace'][0]['g_cumsum']));self.assertNotEqual(D.fp(t,g['trace'][0]['A32']),D.fp(t,base['trace'][0]['A32']))
  both=self.H.evaluate(t,x,actual_A=alteredA,actual_G=alteredG)
  self.assertEqual(D.fp(t,both['trace'][0]['A32']),D.fp(t,a['trace'][0]['A32']));self.assertEqual(D.fp(t,both['trace'][0]['g_cumsum']),D.fp(t,g['trace'][0]['g_cumsum']))
 def test_04_positive_gate_and_safe_exp_support_detected(self):
  t=self.t;x=self.fixture();base=self.O.evaluate(t,x);A,G=self.actual(base);normal=D.positive_stats(t,x,A,G,base)
  self.assertEqual(normal['input_g_positive'],0);self.assertEqual(normal['actual_G_lower_positive_diff'],0)
  G=G.clone();G[0,1,0]=G[0,0,0]+1;A=A.clone();A[0,1,0,0]=.5;x=dict(x,g=x['g'].clone());x['g'][0,1,0]=1
  r=D.positive_stats(t,x,A,G,base);self.assertGreater(r['input_g_positive'],0);self.assertGreater(r['actual_G_lower_positive_diff'],0);self.assertGreater(r['actual_A_nonzero_where_actual_lower_diff_positive'],0);self.assertTrue(r['no_safe_exp_formula_change_applied'])
 def test_05_wrong_dtype_shape_and_upper_factor_reject(self):
  t=self.t;x=self.fixture();base=self.O.evaluate(t,x);A,G=self.actual(base)
  bad=A.clone();bad[0,0,0,0]=1
  for a,g in((A.double(),G),(A,G.double()),(A[:,:1024],G),(bad,G)):
   with self.assertRaises(ValueError):D.validate_operands(t,x,a,g)
 def test_06_state_FP32_before_BF16_amplification_is_visible(self):
  t=self.t;a=t.tensor([1+2**-8-2**-23],dtype=t.float32);b=t.tensor([1+2**-8+2**-23],dtype=t.float32)
  before=D.metric(t,a,b);after=D.metric(t,a.bfloat16(),b.bfloat16());self.assertGreater(after['max_abs'],before['max_abs']);self.assertFalse(after['bitwise'])


if __name__=='__main__':unittest.main()

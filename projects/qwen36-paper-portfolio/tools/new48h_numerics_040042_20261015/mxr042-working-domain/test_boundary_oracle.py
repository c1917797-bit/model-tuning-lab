import importlib.util,pathlib,unittest
import torch
P=pathlib.Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('_independent_chunk028',P/'boundary_oracle.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
torch.set_num_threads(1)
def inputs(cu):
 gen=torch.Generator().manual_seed(281015);T=cu[-1];H=2;D=4
 return dict(q=(torch.randn((1,T,1,D),generator=gen)*.2).bfloat16(),k=(torch.randn((1,T,1,D),generator=gen)*.2).bfloat16(),v=(torch.randn((1,T,H,D),generator=gen)*.2).bfloat16(),g=-torch.rand((1,T,H),generator=gen)*.03,beta=torch.rand((1,T,H),generator=gen).bfloat16(),initial_state=torch.randn((len(cu)-1,H,D,D),generator=gen)*.1,cu_seqlens=torch.tensor(cu),already_normalized=True,scale=.5)
def recurrence(x):
 q=x['q'].double().repeat_interleave(2,2);k=x['k'].double().repeat_interleave(2,2);v=x['v'].double();out=torch.empty_like(v);final=[]
 for j,(a,z)in enumerate(zip(x['cu_seqlens'].tolist(),x['cu_seqlens'].tolist()[1:])):
  st=x['initial_state'][j].double().clone()
  for t in range(a,z):
   st=st*torch.exp(x['g'][0,t].double())[:,None,None]
   pred=torch.einsum('hkv,hk->hv',st,k[0,t]);delta=(v[0,t]-pred)*x['beta'][0,t].double()[:,None];st=st+k[0,t,:,:,None]*delta[:,None,:]
   out[0,t]=torch.einsum('hk,hkv->hv',q[0,t]*.5,st)
  final.append(st)
 return out,torch.stack(final)
class Tests(unittest.TestCase):
 def test_exact_math_chunk_equations_independent_token_recurrence(self):
  for cu in ([0,1],[0,7],[0,64],[0,65],[0,129],[0,3,132]):
   x=inputs(cu);o,s=recurrence(x);y=M.evaluate(torch,x,storage_boundaries=False);self.assertTrue(torch.allclose(o,y['output'],atol=1e-13,rtol=1e-12));self.assertTrue(torch.allclose(s,y['state'],atol=1e-13,rtol=1e-12))
 def test_real_storage_boundaries_differ_from_unrounded_recurrence(self):
  x=inputs([0,65]);o,st=recurrence(x);y=M.evaluate(torch,x);self.assertFalse(torch.equal(o,y['output']));self.assertFalse(torch.equal(st,y['state']));self.assertFalse(y['numerical_qualification_granted']);self.assertFalse(y['actual_exp_qualified'])
 def test_rounding_input_state_is_visible_even_one_token(self):
  x=inputs([0,1]);a=M.evaluate(torch,x);x['initial_state']=x['initial_state'].bfloat16().float();b=M.evaluate(torch,x);self.assertTrue(torch.equal(a['output'],b['output']));self.assertTrue(torch.equal(a['state'],b['state']))
 def test_wrong_inverse_sign_has_falsifiable_effect(self):
  x=inputs([0,7]);y=M.evaluate(torch,x);t=y['trace'][0];eye=torch.eye(7,dtype=torch.float64).expand(2,7,7);wrong=torch.linalg.solve_triangular(eye-t['A32'],eye,upper=False,unitriangular=True);self.assertFalse(torch.allclose(wrong,t['inverse_FP64']))
 def test_no_raw_candidate_or_native_outputs_consumed(self):
  x=inputs([0,7]);a=M.evaluate(torch,x);x.update(candidate_output='poison',saved_solve_output='poison',native_state='poison');b=M.evaluate(torch,x);self.assertTrue(torch.equal(a['output'],b['output']));self.assertTrue(torch.equal(a['state'],b['state']))
 def test_reject_unproven_normalization_or_chunk(self):
  x=inputs([0,7]);x['already_normalized']=False
  with self.assertRaises(ValueError):M.evaluate(torch,x)
  x['already_normalized']=True
  with self.assertRaises(ValueError):M.evaluate(torch,x,chunk_size=32)
 def test_prefill_native_precision_domain_counterexample(self):
  for T in (64,129):
   x=inputs([0,T])
   for n in('q','k','v','g','beta'):x[n].zero_()
   x['initial_state'].fill_(1.003);o,ref=recurrence(x);y=M.evaluate(torch,x)
   expected=x['initial_state'].bfloat16().float().double();self.assertTrue(torch.equal(y['state'],expected))
   err=float((y['state']-ref).norm()/ref.norm());self.assertGreater(err,7.92e-7);self.assertGreater(err,.002)
   self.assertTrue(torch.equal(o,y['output']))
 def test_fixed_native_normalization_not_default_F_normalize(self):
  x=inputs([0,64]);x['q'].fill_(1e-5);x['k'].zero_();y=M.postnormalize(torch,x)
  self.assertFalse(torch.equal(y['q'],torch.nn.functional.normalize(x['q'].float(),dim=-1).bfloat16()));self.assertTrue(bool((y['k']==0).all()))
  with self.assertRaises(ValueError):M.postnormalize(torch,x,source_eps=1e-5)
if __name__=='__main__':unittest.main()

import ast,copy,hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
OWN=None
def owner_file(name):
 if OWN is None:raise ValueError('source-bound owned manifest required')
 r=OWN['files'][name];p=Path(r['path']);b=p.read_bytes()
 if not p.is_absolute()or p.is_symlink()or len(b)!=r['bytes']or hashlib.sha256(b).hexdigest()!=r['sha256']:raise ValueError('exact owned test readset')
 return p
def load(n,f):
 s=importlib.util.spec_from_file_location(n,P/f);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
V=load('_097_variant','two_residual097.py')
class Controls(unittest.TestCase):
 def test_independent_exact_equation(self):
  import torch
  torch.set_num_threads(1);torch.manual_seed(971);A=torch.tril(torch.randn(2,64,64,dtype=torch.float64)*.02,diagonal=-1);M=torch.eye(64,dtype=torch.float64)+A;I=torch.eye(64,dtype=torch.float64).expand_as(A);truth=torch.linalg.solve_triangular(M,I,upper=False,unitriangular=True);X=truth+torch.randn_like(A)*1e-4
  E0=I-M@X;X1=X+X@E0;E1=I-M@X1;X2=X1+X1@E1;E2=I-M@X2
  self.assertLess(float((E1-E0@E0).abs().max()),2e-15);self.assertLess(float((E2-E1@E1).abs().max()),2e-15);self.assertLess(float(E2.norm()),float(E1.norm()))
 def test_real_tiling_trace_and_same_first_round(self):
  import torch
  torch.set_num_threads(1);torch.manual_seed(972);A=torch.zeros((1,128,12,64),dtype=torch.float32);A.copy_(torch.tril(torch.randn(2,12,64,64)*.01,diagonal=-1).permute(0,2,1,3).reshape_as(A));eye=torch.eye(64).expand(24,64,64);ap=A.view(2,64,12,64).permute(0,2,1,3).reshape(24,64,64);xp=torch.linalg.solve_triangular(eye+ap,eye,upper=False,unitriangular=True)+1e-3;X0=xp.reshape(2,12,64,64).permute(0,2,1,3).reshape_as(A).contiguous();_,groups=V.plan([0,128],128);trace=[];out=V._correct_blocks(torch,A,X0,groups,torch.zeros_like(A,dtype=torch.bfloat16),V.allocate(torch,A),trace)
  self.assertEqual(len(trace),1);g=trace[0];M=ap+torch.eye(64);r=torch.eye(64)-torch.bmm(M,xp);expected=xp+torch.bmm(xp,r);self.assertTrue(torch.equal(g['X1'],expected));self.assertTrue(torch.equal(g['X0'],xp));self.assertFalse(g['X1'].data_ptr()==g['X2'].data_ptr());self.assertEqual(out.shape,A.shape)
 def test_wrong_boundaries_refused(self):
  for boundaries in([1,64],[0,129],[0,-1,128]):
   with self.assertRaises(ValueError):V.plan(boundaries,128)
 def test_production_has_no_D2H_or_sync(self):
  t=ast.parse((P/'two_residual097.py').read_bytes());e=next(n for n in t.body if isinstance(n,ast.FunctionDef)and n.name=='eager');calls=[n.func.attr for n in ast.walk(e)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)];self.assertFalse(set(calls)&{'cpu','item','synchronize','double'})
 def test_single_factor_and_original_source_ref(self):
  m=json.loads((P/'SOURCE_MANIFEST.json').read_bytes());r=m['original_block_source'];self.assertEqual(hashlib.sha256((P/'original_block_refine.py').read_bytes()).hexdigest(),r['sha256'])
  self.assertEqual(m['arms'],['saved_candidate','refined_two']);self.assertFalse(m['qualified']);self.assertEqual(m['budgets']['raw_bytes'],256*2**20)
 def test_old_anchor_precedes_variant(self):
  s=(P/'guest_core.py').read_text();self.assertIn("ARMS=('saved_candidate','refined_two')",s);self.assertIn("actual recomputed044 oldB bitwise before newvariant",s);self.assertIn("pool=life.KeepalivePool(512*1024**2,2)",s)
 def test_real_owner_stage_receiver(self):
  s=importlib.util.spec_from_file_location('_097_owner_receiver',owner_file('owner097.py'));O=importlib.util.module_from_spec(s);s.loader.exec_module(O)
  with tempfile.TemporaryDirectory()as td:
   p=Path(td)/'raw';p.write_bytes(b'actual');r=O.ref(p);v=dict(schema='mxr.two-residual-stage/v097',source={},authority={},plan={},primary=None,NPU=True,qualified=False,old_failures_unchanged=True,result=dict(rows=[dict(arm=n,raw=r)for n in('saved_candidate','refined_two')],raw_bytes=2*r['bytes'],whole_correctness_qualified=False,candidate_anchor_bitwise=True,same_actual_A_G=True,intermediate_Hend_FP32_API_available=False));O.receive(v,{},{},{})
   for change in(lambda x:x['result']['rows'].reverse(),lambda x:x['result'].update(candidate_anchor_bitwise=False),lambda x:x.update(schema='mxr.prefill-three-arm-stage/v084')):
    a=copy.deepcopy(v);change(a)
    with self.assertRaises(ValueError):O.receive(a,{},{},{})
 def test_actual_preflight_producer_consumer_contract(self):
  entry=owner_file('cpu_entry097.py').read_text();host=owner_file('owned_cpu097.py').read_text();self.assertIn("schema='mxr.two-residual-mounted-preflight/v097'",entry);self.assertIn("d['schema']=='mxr.two-residual-mounted-preflight/v097'",host);self.assertIn("d['actual_math_controls_pass']is True",host);self.assertIn("d['math_control_cases']==own['math_control_cases']",host)
def run_controls(owned_source):
 global OWN
 OWN=owned_source
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(Controls);n=suite.countTestCases();r=unittest.TextTestRunner(verbosity=2).run(suite)
 if not r.wasSuccessful():raise ValueError('097 software controls failed')
 return n
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--owned-source',required=True,type=Path);a=p.parse_args();run_controls(json.loads(a.owned_source.read_bytes()))

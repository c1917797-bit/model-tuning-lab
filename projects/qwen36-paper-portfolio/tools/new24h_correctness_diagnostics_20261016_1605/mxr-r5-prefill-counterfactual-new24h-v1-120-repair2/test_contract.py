import importlib.util,subprocess,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('_084_test_guest',P/'guest_core.py');G=importlib.util.module_from_spec(s);s.loader.exec_module(G)
class Contracts(unittest.TestCase):
 def test_default_off_cold_I(self):
  for leaf in('guest_core.py','consume.py'):
   r=subprocess.run([sys.executable,'-I','-B',str(P/leaf)],capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr);self.assertIn('"enabled":false',r.stdout)
 def test_no_torch_or_native_import_at_load(self):
  r=subprocess.run([sys.executable,'-I','-B','-c',"import importlib.util,sys;s=importlib.util.spec_from_file_location('g',"+repr(str(P/'guest_core.py'))+");m=importlib.util.module_from_spec(s);s.loader.exec_module(m);assert not any(x=='torch' or x=='acl' or x.startswith('vllm') for x in sys.modules)"],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
 def test_anchor_first_other_arms_blocked(self):
  import torch
  saved=dict(output=torch.tensor([1.]),final_state=torch.tensor([2.]));calls=[]
  def call(arm):calls.append(arm);return dict(output=torch.tensor([9.]),state=torch.tensor([2.]))
  with self.assertRaisesRegex(ValueError,'bitwise anchor'):G.anchored_arms(torch,saved,call)
  self.assertEqual(calls,['saved_candidate'])
 def test_anchor_and_order(self):
  import torch
  saved=dict(output=torch.tensor([1.]),final_state=torch.tensor([2.]));calls=[]
  def call(arm):calls.append(arm);return dict(output=saved['output'].clone(),state=saved['final_state'].clone())
  self.assertEqual(list(G.anchored_arms(torch,saved,call)),list(G.ARMS));self.assertEqual(calls,list(G.ARMS))
 def test_signedzero_anchor_rejects(self):
  import torch
  saved=dict(output=torch.tensor([0.]),final_state=torch.tensor([2.]))
  with self.assertRaises(ValueError):G.anchored_arms(torch,saved,lambda arm:dict(output=torch.tensor([-0.]),state=saved['final_state']))
 def test_dtype_anchor_rejects(self):
  import torch
  saved=dict(output=torch.tensor([1.]),final_state=torch.tensor([2.]))
  with self.assertRaises(ValueError):G.anchored_arms(torch,saved,lambda arm:dict(output=saved['output'].double(),state=saved['final_state']))
 def test_actualA_not_reconstructed_source(self):
  code=(P/'guest_core.py').read_text();self.assertIn("equal(torch,A,savedA)",code);self.assertIn("O.fp64_reference(torch,A,cu.tolist())",code)
  self.assertNotIn('torch.linalg',code);self.assertIn('variant.eager(solver',code);self.assertIn('actual X2 B full bitwise',code)
 def test_report_explicit_intermediate_scope(self):
  self.assertIn('intermediate_Hend_FP32_API_available=False',(P/'guest_core.py').read_text());self.assertIn('whole_correctness_qualified=False',(P/'guest_core.py').read_text())
 def test_complete_case_cardinality_before_reference_load(self):
  s=importlib.util.spec_from_file_location('_120_actualconsumer',P/'consume.py');C=importlib.util.module_from_spec(s);s.loader.exec_module(C)
  m=dict(cases=[dict(case_id='a'),dict(case_id='b')]);stage=dict(schema='mxr.prefill-three-arm-stage/v084',source={},primary=None,NPU=True,result=dict(cases=[],raw_bytes=0))
  with self.assertRaisesRegex(ValueError,'cardinality'):C.consume(None,m,stage)
 def test_actual_compiler_and_self_source_root(self):
  for p in P.glob('*.py'):compile(p.read_bytes(),str(p),'exec')
  m=__import__('json').loads((P/'SOURCE_MANIFEST.json').read_bytes());self.assertEqual(m['retained_model_source'],G.MODEL);self.assertEqual(m['cases'][0]['raw'],G.RAW);self.assertEqual(m['schema'],'mxr.r5-prefill-counterfactual-source/v120')
  self.assertEqual([c['case_id']for c in m['cases'][:2]],['rank0-layer0','rank0-layer4']);self.assertFalse(m['qualified'])
 def test_original_X2_and_three_native_arm_seams(self):
  import ast
  tree=ast.parse((P/'guest_core.py').read_bytes());f=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='execute');s=ast.unparse(f)
  self.assertIn('variant.eager(solver',s);self.assertIn('trace=None',s);self.assertIn('value = original_solve(*a, **kw)',s);self.assertIn("inverse.to(torch.bfloat16).to(v['A'].device)",s);self.assertNotIn('range(3)',s)
  consumer=(P/'consume.py').read_text();self.assertIn('registered_working=registered',consumer);self.assertIn('CPU64_cast_is_operational_not_exact_nearest=True',consumer)
  import copy,tempfile
  own=__import__('json').loads((P/'SOURCE_MANIFEST.json').read_bytes());calls=[];seen=[]
  def build():calls.append('construct');return dict(binding=G.runtime_identity(own))
  def read(torch,model,case):return dict(case_id=case['case_id'])
  def run(torch,source,model,g,context,saved,out,runtime):seen.append(runtime);return dict(raw_bytes=0)
  with tempfile.TemporaryDirectory()as td:r=G.replay_frames(None,own,None,None,None,Path(td),builder=build,reader=read,runner=run)
  self.assertEqual(calls,['construct']);self.assertEqual(len(seen),3);self.assertTrue(all(v is seen[0]for v in seen));self.assertEqual(len(r['cases']),3)
  f=G.RuntimeFactory(own);value=f.construct(lambda:dict(binding=G.runtime_identity(own)));self.assertIs(f.take(own),value)
  with self.assertRaisesRegex(ValueError,'reentrant/repeated'):f.construct(lambda:dict(binding=G.runtime_identity(own)))
  bad=copy.deepcopy(own);bad['variant_ref']['sha256']='0'*64
  with self.assertRaisesRegex(ValueError,'same runtime source/DSO'):f.take(bad)
  for key in('actual037_prerequisite','component044','common_precision'):
   wrong=copy.deepcopy(own);wrong[key]['sha256']='0'*64
   with self.assertRaisesRegex(ValueError,'same runtime source/DSO'):f.take(wrong)
  f=G.RuntimeFactory(own)
  with self.assertRaisesRegex(ValueError,'reentrant/repeated'):f.construct(lambda:f.construct(lambda:dict(binding=G.runtime_identity(own))))
  f=G.RuntimeFactory(own)
  with self.assertRaisesRegex(ValueError,'exact source/DSO'):f.construct(lambda:dict(binding=G.runtime_identity(bad)))
  self.assertEqual((P/'guest_core.py').read_text().count('adapter.instances('),1)
  self.assertNotIn('sys.modules.pop',(P/'guest_core.py').read_text());self.assertNotIn('sys.modules.clear',(P/'guest_core.py').read_text())

 def test_multi_case_actual_consumer_original_predicate_preserved(self):
  import ast
  source=(P/'consume.py').read_text();tree=ast.parse(source);f=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='consume_case');s=ast.unparse(f)
  self.assertIn("candidate['actual_X2']",s);self.assertIn("G.equal(torch, candidate['output'], saved['output'])",s);self.assertIn("O.metrics(torch, row['state'], working['state'])",s)
  self.assertIn('model,g,context,refs=readset(m)',(P/'guest_core.py').read_text());self.assertIn("for case,result in zip(m['cases'],cases):",source)
if __name__=='__main__':unittest.main()

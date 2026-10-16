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
  self.assertNotIn('boundary_oracle',code);self.assertNotIn('torch.linalg',code)
 def test_report_explicit_intermediate_scope(self):
  self.assertIn('intermediate_Hend_FP32_API_available=False',(P/'guest_core.py').read_text());self.assertIn('whole_correctness_qualified=False',(P/'guest_core.py').read_text())
if __name__=='__main__':unittest.main()

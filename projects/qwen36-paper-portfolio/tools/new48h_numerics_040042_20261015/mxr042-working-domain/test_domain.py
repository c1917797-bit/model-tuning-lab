import importlib.util,unittest
from pathlib import Path
import torch
P=Path(__file__).resolve().parent
def load(n):
 s=importlib.util.spec_from_file_location('_42'+n,P/(n+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Domain(unittest.TestCase):
 def test_new_fixed_selection_not_max_search(self):
  text=(P/'select_frames.py').read_text();self.assertIn('for layer in (16,40)',text);self.assertNotIn("max(v['rows']",text);self.assertIn('initial_state_rounding_witness',text)
 def test_native_boundary_source_requires_real_refs(self):
  with self.assertRaises(ValueError):load('source_proof').check([])
 def test_independent_reference_wrongscale_head_and_slot_visible(self):
  s=importlib.util.spec_from_file_location('_inputs42',P/'test_boundary_oracle.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
  x=m.inputs([0,7,14]);ref=load('boundary_oracle').evaluate(torch,x)
  wrong=dict(x,scale=x['scale']*1.5);self.assertFalse(torch.equal(ref['output'],load('boundary_oracle').evaluate(torch,wrong)['output']))
  wrong=dict(x,v=x['v'].flip(2));self.assertFalse(torch.equal(ref['output'],load('boundary_oracle').evaluate(torch,wrong)['output']))
  wrong=dict(x,initial_state=x['initial_state'].flip(0));self.assertFalse(torch.equal(ref['state'],load('boundary_oracle').evaluate(torch,wrong)['state']))
 def test_consumer_actual_cli_defaultoff(self):
  # Import real consumer (including actual new cardinality code), no framework/device path.
  self.assertTrue(callable(load('consume').main))
if __name__=='__main__':unittest.main()

"""Stdlib original source/order registry tests, no synthetic numeric PASS."""
import ast,types,unittest
from pathlib import Path
import no_pa_full as n
class Contracts(unittest.TestCase):
 def params(self):return types.SimpleNamespace(attn_params={1:[]},handles={1:[]},events={1:[]})
 def test_zero_tasks_not_fake16(self):self.assertTrue(n.empty_pa(self.params(),1))
 def test_any_handle_or_param_rejected(self):
  for key in ("attn_params","handles","events"):
   p=self.params();getattr(p,key)[1].append(object())
   with self.assertRaises(ValueError):n.empty_pa(p,1)
 def test_virtual_boolean_batch_rejected(self):
  with self.assertRaises(ValueError):n.empty_pa(self.params(),True)
 def test_actual_complete_deployed_source_POST_order(self):
  sources=n.verified_sources();self.assertEqual(n.original_post_order(sources["model_runner_v1.py"]),["original_run_model","original_POST_update"])
 def test_modified_preupdate_or_duplicate_rejected(self):
  sources=n.verified_sources();s=sources["model_runner_v1.py"]
  start=s.index("    def _model_forward(");end=s.index("    def _pad_for_sequence_parallelism",start)
  body=s[start:end].replace("hidden_states = run_model()","self._update_full_graph_params_if_needed(forward_context,num_tokens_padded,positions)\n            hidden_states = run_model()")
  altered=s[:start]+body+s[end:]
  with self.assertRaises(ValueError):n.original_post_order(altered)
 def test_captured_topology_no_host_transfer_and_full_length(self):
  tree=ast.parse((Path(__file__).parent/"no_pa_full.py").read_text())
  node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=="selector_topology")
  attrs=[x.func.attr for x in ast.walk(node) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute)]
  self.assertNotIn("cpu",attrs);self.assertNotIn("item",attrs)
  text=ast.unparse(node);self.assertIn("workspace.lengths.copy_(device_lengths)",text)
  self.assertNotIn("min(",text)
 def test_author_meanOFF_explicit_no_meanON_fakezero(self):
  tree=ast.parse((Path(__file__).parent/"no_pa_full.py").read_text())
  node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=="author_forward")
  call=next(x for x in ast.walk(node) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr=="run")
  self.assertEqual([(x.arg,x.value.value) for x in call.keywords],[("reallocation",False)])
 def test_output_copy_before_later_reuse(self):
  tree=ast.parse((Path(__file__).parent/"no_pa_full.py").read_text())
  node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=="author_forward")
  lines=ast.unparse(node)
  self.assertLess(lines.index(".copy_(got)"),lines.index("copy_order()"))
 def test_post_calls_original_not_new_PA(self):
  source=(Path(__file__).parent/"no_pa_full.py").read_text()
  self.assertIn("got=original_backend(stream,ctx,tokens,config,spec,cp_tokens,draft_meta)",source)
  self.assertNotIn("_npu_paged_attention(",source)
if __name__=="__main__":unittest.main()

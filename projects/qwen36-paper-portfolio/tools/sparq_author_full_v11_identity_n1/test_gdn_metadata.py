"""Stdlib domain/unit negatives only: no simulated device/model PASS."""
import ast,copy,unittest
from pathlib import Path
import gdn_metadata as m,gdn_state as s,gdn_source as src
class Metadata(unittest.TestCase):
 def raw(self):
  return dict(schema="sparq.GDN-actual-metadata-snapshot/v1",spec_sequence_masks=None,num_spec_decodes=0,
   num_spec_decode_tokens=0,num_decodes=1,num_prefills=1,num_decode_tokens=1,num_actual_tokens=4,
   mamba_cache_mode="none",use_context_parallel=False,non_spec_query_start_loc=[0,1,4],
   non_spec_state_indices_tensor=[2,5],prefill_state_indices=[5],prefill_query_start_loc=[0,3],
   conv=dict(branch="prefill",query_start_loc=[0,1,4],cache_indices=[[2],[5]]))
 def test_mixed_actual_tail(self):
  got=m.plan(self.raw(),9,9);self.assertEqual(got["written_slots"],{"conv":[2,5],"recurrent":[2,5]})
 def test_graph_zero_length_tail_not_writer(self):
  x=self.raw();x.update(num_prefills=0,num_actual_tokens=1,non_spec_query_start_loc=[0,1,1],
   non_spec_state_indices_tensor=[2,-1],prefill_state_indices=None,prefill_query_start_loc=None)
  x["conv"]=dict(branch="decode",query_start_loc=[0,1,1],cache_indices=[2,-1])
  got=m.plan(x,9,9);self.assertEqual(got["written_slots"],{"conv":[2],"recurrent":[2]})
  self.assertEqual(got["zero_length_rows"],[1])
 def test_invalid_live_sentinel_rejected(self):
  x=self.raw();x["non_spec_state_indices_tensor"][0]=-1;x["conv"]["cache_indices"][0]=[-1]
  with self.assertRaises(ValueError):m.plan(x,9,9)
 def test_real_conv_metadata_cannot_use_virtual_ledger_slot(self):
  x=self.raw();x["conv"]["cache_indices"]=[[99],[5]]
  with self.assertRaises(ValueError):m.plan(x,9,9)
 def test_prefill_tail_disagreement_rejected(self):
  x=self.raw();x["prefill_state_indices"]=[6]
  with self.assertRaises(ValueError):m.plan(x,9,9)
 def test_cache_align_or_spec_not_implicitly_admitted(self):
  for k,v in (("mamba_cache_mode","align"),("use_context_parallel",True),("spec_sequence_masks",[])):
   x=self.raw();x[k]=v
   with self.assertRaises(ValueError):m.plan(x,9,9)
 def test_padded_page_stride_source_supported(self):
  x=dict(shape=[3,2,4],stride=[16,4,1],dtype="torch.bfloat16",device="npu:0",pointer=1024,
   storage_pointer=1024,storage_offset=0,storage_bytes=80,native_format_value=0)
  self.assertEqual(s.identity(x),16)
  x["stride"]=[4,4,1]
  with self.assertRaises(ValueError):s.identity(x)
 def test_source_pins_are_exact_public_six_plus_manifest(self):
  self.assertEqual(len(src.PINS),7);self.assertEqual(len(src.RUNTIME_PINS),6)
  for path,digest in src.PINS.items():self.assertEqual(len(digest),64)
 def test_no_algorithm_monkeypatch_in_state_observer(self):
  tree=ast.parse(Path(__file__).with_name("gdn_observer.py").read_text())
  assigned=[]
  for node in ast.walk(tree):
   if isinstance(node,(ast.Assign,ast.AnnAssign)):
    assigned.extend(t.attr for t in (node.targets if isinstance(node,ast.Assign) else [node.target]) if isinstance(t,ast.Attribute))
  self.assertNotIn("forward",assigned);self.assertNotIn("_forward_core",assigned);self.assertNotIn("kv_cache",assigned)
if __name__=="__main__":unittest.main()

"""Source/control tests only. Real graph/copy/format/metrics remain pending."""
import os,types,unittest,tempfile
from pathlib import Path
from unittest.mock import patch
import actual_replay as r
TEST_TMP_PARENT=Path("/cache/cch/qwen36-paper-preparation-20261007/sparse")
class ReplayChecks(unittest.TestCase):
 def test_exclusive_binary_complete_publication(self):
  with tempfile.TemporaryDirectory(dir=TEST_TMP_PARENT,prefix="fullv2-atomic-test-") as name:
   p=Path(name)/"raw.bin";ref=r.atomic_bytes(p,b"complete")
   self.assertEqual(p.read_bytes(),b"complete");self.assertEqual(ref["size_bytes"],8)
   with self.assertRaises(FileExistsError):r.atomic_bytes(p,b"overwrite")
   self.assertEqual(p.read_bytes(),b"complete")
   self.assertEqual(len(list(Path(name).glob(".*.pending-*"))),1)
 def test_final_never_exists_during_write_phase(self):
  with tempfile.TemporaryDirectory(dir=TEST_TMP_PARENT,prefix="fullv2-atomic-test-") as name:
   p=Path(name)/"raw.bin";real=os.link;seen=[]
   def link(src,dst,**kwargs):
    seen.append((not p.exists(),Path(src).read_bytes()));return real(src,dst,**kwargs)
   with patch.object(os,"link",side_effect=link):r.atomic_bytes(p,b"not-empty")
   self.assertEqual(seen,[(True,b"not-empty")])
 def test_original_acl_call_not_substitute_graph(self):
  class Tensor:
   def data_ptr(self):return 123
  graph=object();output=object();descriptor=types.SimpleNamespace(num_tokens=1,uniform=True)
  class Descriptor:
   num_tokens=1;uniform=True
  descriptor=Descriptor();entry=types.SimpleNamespace(aclgraph=graph,output=output,input_addresses=[123])
  class Wrapper:
   __module__="actual_fake_acl_for_control_test"
   def __init__(self):self.runtime_mode="FULL";self.concrete_aclgraph_entries={descriptor:entry}
   def __call__(self,*args,**kwargs):self.called=True;return output
  Wrapper.__call__.__module__=Wrapper.__module__
  acl=types.SimpleNamespace(__name__=Wrapper.__module__,ACLGraphWrapper=Wrapper)
  state=types.SimpleNamespace(Mode=types.SimpleNamespace(FULL="FULL"),t=types.SimpleNamespace(Tensor=Tensor),replay_calls=[])
  ctx=types.SimpleNamespace(batch_descriptor=descriptor,cudagraph_runtime_mode="FULL",capturing=False)
  original=r.wrap_original_acl(acl,lambda:ctx,lambda:state);wrapper=Wrapper()
  self.assertIs(wrapper(Tensor()),output);self.assertTrue(wrapper.called);self.assertEqual(len(state.replay_calls),1)
  self.assertIs(Wrapper.__call__.__wrapped__,original)
 def test_capture_is_not_counted_as_real_existing_replay(self):
  source=Path(r.__file__).read_text()
  self.assertIn('entry is not None and entry.aclgraph is not None',source)
  self.assertIn('need(not ctx.capturing',source)
  self.assertIn('got=original(wrapper,*args,**kwargs)',source)
  self.assertNotIn("NPUGraph(",source)
 def test_snapshot_semantics_no_type_restriction_or_global_capture_cpu(self):
  source=Path(r.__file__).read_text()
  self.assertIn("self.npu.get_npu_format(g.value)==2",source)
  self.assertNotIn("type(self.npu.get_npu_format",source)
  self.assertIn("self.q.copy_(q)",source);self.assertIn("self.saved_epoch.copy_(self.epoch)",source)
  self.assertIn("count==self.last_counter+1",source)
  for method in ("before","after"):
   part=source.split(" def "+method+"(")[1].split("\n def ")[0]
   self.assertNotIn(".cpu()",part);self.assertNotIn(".item()",part)
if __name__=="__main__":unittest.main()

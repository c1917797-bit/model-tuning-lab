"""Real043 Store -> host primitive reader -> nested anchor/blob closure."""
import importlib.util,tempfile,unittest
from pathlib import Path
import bind_recovery as B
class RawMetadata(unittest.TestCase):
 def test_actual_lossless_nested_anchor_and_blob_closure(self):
  import torch
  p=Path(__file__).resolve().parent.parent/'deltalog-mixed-precast-new48h-20261015-043-repair3/raw_codec.py'
  s=importlib.util.spec_from_file_location('review_actual043codec',p);R=importlib.util.module_from_spec(s);s.loader.exec_module(R)
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);store=R.Store(torch,root,4*1024**2)
   anchor=store.write(root/'initial.pt',dict(state=torch.tensor([1.,-0.])))
   raw=store.write(root/'raw.pt',dict(deep=[dict(initial_anchor_ref=anchor)],value=torch.tensor([2.])))
   refs={raw['path']:raw}
   def add(r):B.H.validate_ref_streamed(r);refs[r['path']]=r
   B.metadata_closure(refs,add,root)
   self.assertIn(anchor['path'],refs);self.assertTrue(any(Path(p).parent==root/'tensor-blobs'for p in refs))
   blob=next(p for p in refs if Path(p).parent==root/'tensor-blobs');Path(blob).write_bytes(b'corrupt')
   refs.clear();refs[raw['path']]=raw
   with self.assertRaises(ValueError):B.metadata_closure(refs,add,root)
if __name__=='__main__':unittest.main()

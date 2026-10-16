"""Real streamed files and original-bind interface controls; no fake evidence."""
import importlib.util,json,tempfile,types,unittest
from pathlib import Path
import model_readset101 as R
IO=R.IO
class Replay:
 def __init__(self,refs):self.refs=tuple(refs);self.parents=tuple(sorted({str(Path(r['path']).parent)for r in refs}))
 def __len__(self):return len(self.refs)
 def __iter__(self):yield from self.refs
class Controls(unittest.TestCase):
 def fixture(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);p=Path(t.name).resolve();(p/'a').mkdir();(p/'b').mkdir()
  (p/'a/x').write_bytes(b'x');(p/'a/y').write_bytes(b'yy');(p/'b/z').write_bytes(b'zzz')
  refs=[IO.ref(p/'a/x'),IO.ref(p/'a/y'),IO.ref(p/'b/z')];return p,refs
 def test_replay_complete_twice_not_generator(self):
  p,refs=self.fixture();r=R.Readset([refs[0]],Replay(refs[1:]));self.assertEqual(list(r),list(r));self.assertEqual(r.verify()['entries'],3);self.assertEqual(len(r.parent_anchors()),2)
 def test_consumed_generator_rejected(self):
  p,refs=self.fixture()
  with self.assertRaises(ValueError):R.Readset([],iter(refs))
 def test_omitted_parent_rejected(self):
  p,refs=self.fixture();s=Replay(refs);s.parents=s.parents[:1];r=R.Readset([],s)
  with self.assertRaises(ValueError):r.parent_anchors()
 def test_count_mismatch_rejected(self):
  p,refs=self.fixture();r=R.Readset([],Replay(refs));r._length=2
  with self.assertRaises(ValueError):r.verify()
 def test_second_pass_mutated_blob_rejected(self):
  p,refs=self.fixture();r=R.Readset([],Replay(refs));r.parent_anchors();(p/'a/y').write_bytes(b'xx')
  with self.assertRaises(ValueError):r.verify()
 def test_same_size_wrong_sha_rejected(self):
  p,refs=self.fixture();refs[0]['sha256']='0'*64
  with self.assertRaises(ValueError):R.Readset([],Replay(refs)).parent_anchors()
 def test_original_bind_interface_exact_parents_and_full_fence(self):
  p,refs=self.fixture();readset=R.Readset([],Replay(refs));calls=[]
  class H:
   DONOR=p/'donor'
   @staticmethod
   def bind(sr,pr,anchors):
    calls.append(tuple(anchors));parents={Path(r['path']).parent for r in anchors}|{H.DONOR};parents={q for q in parents if not any(w!=q and w in q.parents for w in parents)}
    h=types.SimpleNamespace(HERE=p,_READ_MOUNTS={str(q):(str(q),False)for q in parents},frozen_directory=lambda root,digest:dict(original=True))
    return h,[]
  h,pairs=R.bind_original(H,{},None,readset);self.assertEqual(len(calls),1);self.assertEqual(len(calls[0]),2);self.assertTrue(h.frozen_directory(p,'unused')['original'])
  (p/'a/y').write_bytes(b'xx')
  with self.assertRaises(ValueError):h.frozen_directory(p,'unused')
 def test_whole_index_streams_without_read_bytes(self):
  from unittest.mock import patch
  p,refs=self.fixture()
  with patch.object(Path,'read_bytes',side_effect=AssertionError('whole-file read forbidden')):self.assertEqual(IO.obj_file(refs[0]),p/'a/x')
if __name__=='__main__':unittest.main()

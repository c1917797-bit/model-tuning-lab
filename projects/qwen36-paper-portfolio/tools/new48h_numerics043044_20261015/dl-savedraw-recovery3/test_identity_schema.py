"""Exact raw schema locations, not broad guest-path prefix exemptions."""
import copy,importlib.util,tempfile,unittest
from pathlib import Path
import bind_recovery as B
class IdentitySchema(unittest.TestCase):
 def test_all_raw_rows_exact_field_join_not_aggregate_count(self):
  producer=dict(records=[dict(kind='mixed',raw=dict(path='/raw/%d.pt'%i,bytes=1,sha256=str(i)))for i in range(32)])
  rows=[]
  for item in producer['records']:
   for phase in('before','after'):
    for key,suffix in(('module_file',('module_file',)),('metadata_source',('controls','metadata_source'))):rows.append(dict(raw_ref=item['raw'],record_json_path=['captures','prefill',0,'native_call',phase,*suffix],identity=B.RUNTIME_IDENTITIES[key]))
  self.assertTrue(B.validate_runtime_identities(rows,producer))
  for wrong in(rows[:-1],rows[:-1]+[rows[0]]):
   with self.assertRaises(ValueError):B.validate_runtime_identities(wrong,producer)
  wrong=copy.deepcopy(rows);wrong[0]['raw_ref']=producer['records'][1]['raw']
  with self.assertRaises(ValueError):B.validate_runtime_identities(wrong,producer)
 def test_exact_before_after_only_and_corruption_refused(self):
  r=B.RUNTIME_IDENTITIES['module_file'];path=('captures','prefill',0,'native_call','before','module_file')
  self.assertTrue(B.runtime_identity(r,path));self.assertTrue(B.runtime_identity(r,path[:4]+('after',)+path[5:]))
  for p in(('arbitrary',),('captures','decode',0,'native_call','before','module_file'),('captures','prefill',0,'native_call','before','not_module_file')):self.assertFalse(B.runtime_identity(r,p))
  with self.assertRaises(ValueError):B.runtime_identity(dict(r,sha256='0'*64),path)
  with self.assertRaises(ValueError):B.runtime_identity(dict(r,path='/vllm-workspace/other.py'),path)
 def test_real_codec_metadata_closure_preserves_identity_without_host_read(self):
  import torch
  p=Path(__file__).resolve().parent.parent/'deltalog-mixed-precast-new48h-20261015-043-repair3/raw_codec.py';s=importlib.util.spec_from_file_location('actual043_schema_codec',p);R=importlib.util.module_from_spec(s);s.loader.exec_module(R)
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);store=R.Store(torch,root,4*1024**2)
   identity=copy.deepcopy(B.RUNTIME_IDENTITIES['module_file']);payload=dict(captures=dict(prefill=[dict(native_call=dict(before=dict(module_file=identity),after=dict(module_file=identity)))]),value=torch.tensor([1.]))
   rr=store.write(root/'mixed.pt',payload);before=(root/'mixed.pt').read_bytes();refs={rr['path']:rr}
   def add(r):B.H.validate_ref_streamed(r);refs[r['path']]=r
   evidence=B.metadata_closure(refs,add,root);self.assertEqual(len(evidence),2);self.assertNotIn(identity['path'],refs);self.assertEqual(before,(root/'mixed.pt').read_bytes())
   wrong=store.write(root/'bad.pt',dict(arbitrary=identity));refs={wrong['path']:wrong}
   with self.assertRaises(ValueError):B.metadata_closure(refs,add,root)
if __name__=='__main__':unittest.main()

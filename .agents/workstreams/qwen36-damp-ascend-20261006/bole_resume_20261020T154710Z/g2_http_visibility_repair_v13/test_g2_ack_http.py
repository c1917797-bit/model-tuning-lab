"""Synthetic CPU protocol controls; no actual HTTP, tokenizer, or model qualification."""
import contextlib,json,tempfile,unittest
from pathlib import Path
import sourceio as C
import g1_contract as G1
import service_client as SC
import g2_http_visibility_v13 as H
P=Path(__file__).resolve().parent
class SyntheticTokenizer:
 vocab_size=1000
 def encode(self,text,add_special_tokens=False):
  if text!='Explain how trees grow. '*256 or add_special_tokens is not False:raise AssertionError('unchanged actual client tokenizer call')
  return list(range(300))
class SyntheticResponse:
 status=200
 def __init__(self,wire,reads):self.wire=wire;self.reads=reads
 def __enter__(self):return self
 def __exit__(self,*args):return False
 def read(self,n):
  if n!=8*2**20+1:raise AssertionError('original exact bounded wire read')
  self.reads.append(n);return self.wire[:n]
class SyntheticHTTP:
 def __init__(self,mode=None):self.mode=mode;self.requests=[];self.reads=[]
 def __call__(self,request,timeout):
  if timeout!=600:raise AssertionError('original bounded actual HTTP timeout')
  index=len(self.requests)
  if index>=3:raise AssertionError('only two frozen requests and barrier')
  label=('tree-1','tree-2','retirement-barrier')[index];count=(4,4,1)[index]
  body=json.loads(request.data);header='bole-g2-131-'+label
  expected=dict(model='qwen36-mxr-eager',prompt=list(range(131)),max_tokens=count,temperature=0,top_p=1,n=1,stream=False,ignore_eos=True,return_token_ids=True)
  if body!=expected or request.full_url!='http://127.0.0.1:8230/v1/completions' or request.get_method()!='POST' or request.get_header('X-request-id')!=header:raise AssertionError('unchanged real client request semantics')
  self.requests.append(dict(label=label,header=header,body=body))
  token_ids=list(range(500,500+count))
  value=dict(id='cmpl-'+header,choices=[dict(token_ids=token_ids)],usage=dict(prompt_tokens=131,completion_tokens=count))
  if self.mode=='bad_header':value['id']='cmpl-unrelated-request'
  if self.mode=='bad_tokens':value['choices'][0]['token_ids']=token_ids[:-1]
  wire=b'x'*(8*2**20+1)if self.mode=='too_large'else json.dumps(value,sort_keys=True).encode()
  return SyntheticResponse(wire,self.reads)
@contextlib.contextmanager
def synthetic_channel(mode=None):
 location='/adakv-results'if Path('/adakv-results').is_dir()else None
 with tempfile.TemporaryDirectory(prefix='bole-http-v13-',dir=location)as tmp:
  base=Path(tmp);root=base/'channel';root.mkdir(mode=0o700)
  marker=root/'LIVE-CHANNEL.marker';marker.write_bytes(b'existing shared-channel data\n')
  if G1.SCOPE['max_output_tokens']!=4:raise AssertionError('fixed output4 profile only')
  scope=base/'SYNTHETIC_SOURCE.json';C.write(scope,dict(prepared_only=False,service_experiment=G1.SCOPE,synthetic_CPU_protocol_fixture=True))
  sr=C.ref(scope);mock=SyntheticHTTP(mode)
  yield root,sr,mock,marker
class HTTPVisibilityControls(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.before=C.checked(H.HOST_REF).read_text()
  cls.after=(P/'host_service.py').read_text()
  cls.finalizer=(P/'g2_finalize.py').read_text()
 def test_exact_host_two_anchor_inverse(self):
  self.assertEqual(H.patch_host(self.before),self.after)
  proof=H.audit_host(self.before,self.after)
  self.assertTrue(proof['whole_file_inverse']);self.assertTrue(proof['whole_AST_inverse'])
  self.assertTrue(proof['all_other_host_text_unchanged']);self.assertFalse(proof['new_mounts_or_RW_aliases'])
  self.assertFalse(proof['actual_HTTP_or_NPU_executed']);self.assertFalse(proof['numerical_model_qualification'])
  self.assertEqual(len(proof['changes']),2)
 def test_missing_duplicate_or_undeclared_source_edit_rejected(self):
  for bad in(self.before+'\n# unreviewed\n',self.before.replace(H.OLD_CLIENT,'MISSING',1),self.before+'\n'+H.OLD_HTTP):
   with self.subTest(kind=bad[-50:]):
    with self.assertRaises(ValueError):H.patch_host(bad)
  for bad in(self.after+'\n# unreviewed\n',self.after.replace(H.NEW_CLIENT,H.OLD_CLIENT,1),self.after+'\n'+H.NEW_HTTP):
   with self.subTest(kind=bad[-50:]):
    with self.assertRaises(ValueError):H.audit_host(self.before,bad)
 def test_original_client_really_writes_five_channel_files(self):
  with synthetic_channel()as(root,sr,mock,marker):
   result=SC.run(sr,root,SyntheticTokenizer(),open_url=mock)
   self.assertEqual(marker.read_bytes(),b'existing shared-channel data\n')
   expected={'INPUTS.json','HTTP-tree-1.json','HTTP-tree-2.json','HTTP-retirement-barrier.json','HTTP_RESULT.json'}
   self.assertEqual({p.name for p in root.glob('*.json')},expected)
   self.assertEqual(len(mock.requests),3);self.assertEqual(mock.reads,[8*2**20+1]*3)
   self.assertEqual(result,C.obj(C.ref(root/'HTTP_RESULT.json')));self.assertEqual(result['source'],sr)
   self.assertFalse(result['whole_model_qualified']);self.assertFalse(result['scheduler_committed'])
   self.assertEqual([r['label']for r in result['rows']],['tree-1','tree-2','retirement-barrier'])
   for row,count in zip(result['rows'],(4,4,1)):
    self.assertEqual(row['response'],C.ref(root/('HTTP-'+row['label']+'.json')))
    self.assertEqual(len(C.obj(row['response'])['choices'][0]['token_ids']),count)
    self.assertEqual(row['http_status'],200)
   inputs=C.obj(C.ref(root/'INPUTS.json'));self.assertEqual(inputs['source'],sr);self.assertEqual(inputs['token_ids'],list(range(131)));self.assertEqual(inputs['input_tokens'],131)
 def test_actual_source_owned_metadata_selector_covers_all_five(self):
  with synthetic_channel()as(root,sr,mock,marker):
   SC.run(sr,root,SyntheticTokenizer(),open_url=mock)
   selected=H.metadata_selector(self.finalizer,root,C)
   five={str(root/n)for n in('INPUTS.json','HTTP-tree-1.json','HTTP-tree-2.json','HTTP-retirement-barrier.json','HTTP_RESULT.json')}
   self.assertEqual(set(selected),five)
   for path,r in selected.items():self.assertEqual(r,C.ref(path));C.checked(r)
   C.write(root/'EXTRA_METADATA.json',dict(synthetic=True))
   selected_more=H.metadata_selector(self.finalizer,root,C)
   self.assertEqual(set(selected_more),five|{str(root/'EXTRA_METADATA.json')})
   self.assertEqual(sum(r['bytes']for r in selected_more.values()),sum(r['bytes']for r in selected.values())+C.ref(root/'EXTRA_METADATA.json')['bytes'])
 def test_original_header_identity_gate_still_rejects(self):
  with synthetic_channel('bad_header')as(root,sr,mock,marker):
   with self.assertRaises(ValueError):SC.run(sr,root,SyntheticTokenizer(),open_url=mock)
   self.assertTrue((root/'HTTP-FAILURE.json').is_file());self.assertFalse((root/'HTTP_RESULT.json').exists())
   self.assertEqual(len(mock.requests),1);self.assertEqual(C.obj(C.ref(root/'HTTP-FAILURE.json'))['source'],sr)
 def test_original_generated_token_count_gate_still_rejects(self):
  with synthetic_channel('bad_tokens')as(root,sr,mock,marker):
   with self.assertRaises(ValueError):SC.run(sr,root,SyntheticTokenizer(),open_url=mock)
   self.assertTrue((root/'HTTP-FAILURE.json').is_file());self.assertFalse((root/'HTTP_RESULT.json').exists())
   self.assertEqual(len(mock.requests),1)
 def test_original_actual_wire_bound_still_rejects(self):
  with synthetic_channel('too_large')as(root,sr,mock,marker):
   with self.assertRaises(ValueError):SC.run(sr,root,SyntheticTokenizer(),open_url=mock)
   self.assertTrue((root/'HTTP-FAILURE.json').is_file());self.assertFalse((root/'HTTP-tree-1.json').exists());self.assertFalse((root/'HTTP_RESULT.json').exists())
   self.assertEqual(mock.reads,[8*2**20+1])
 def test_selector_cannot_run_modified_finalizer_source(self):
  with synthetic_channel()as(root,sr,mock,marker):
   with self.assertRaises(ValueError):H.metadata_selector(self.finalizer+'\n# undeclared\n',root,C)
if __name__=='__main__':unittest.main()

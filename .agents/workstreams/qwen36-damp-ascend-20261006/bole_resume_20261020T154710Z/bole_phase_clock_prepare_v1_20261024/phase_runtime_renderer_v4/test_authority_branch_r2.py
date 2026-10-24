"""Actual V4 producer/render/materialize controls; no approval files or runtime launch.
One exact parent render is cached after its inverse. Test authority read_ref is
an in-memory fixture and output roots are temporary; original validators run.
"""
import copy,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
Q=load(HERE/'runtime_lossless_imports.py','runtime_lossless_imports')
P=load(HERE/'qualification_source_producer.py','_actual_public_producer')
AUTH=dict(path='/SOFTWARE_FIXTURE_ONLY/no-issued-authority',bytes=1,sha256='a'*64)
REVIEW=dict(path='/SOFTWARE_FIXTURE_ONLY/no-issued-review',bytes=1,sha256='b'*64)
ORIGINAL=Q.module
CACHE=None
PARENT_CALLS=[]
CHECKED=[]
MUTATE=lambda a,r,m:None
def module(raw,path,name):
 global CACHE
 mod=ORIGINAL(raw,path,name)
 if name=='_actual_cache_phase_parent':
  original=mod.render
  def parent(**kw):
   global CACHE
   PARENT_CALLS.append(copy.deepcopy(kw))
   if kw.get('authority_ref')is not None:raise ValueError('new review incorrectly delegated to historical parent')
   if CACHE is None:CACHE=original(**kw)
   return dict(CACHE,files=dict(CACHE['files']),manifest=copy.deepcopy(CACHE['manifest']))
  mod.render=parent
 elif name=='_phase_shape_only':
  original_read=mod.read_ref
  original_window=mod.execution_window
  def window(m,*,clock,require_phase):
   if m.get('qualification_authority_ref')is None:return original_window(m,clock=clock,require_phase=require_phase)
   authority=dict(schema=mod.AUTH_SCHEMA,approved=True,start_epoch=1792828303,cutoff_epoch=1792914703,scope=copy.deepcopy(mod.SCOPE),MAIN_review_ref=REVIEW)
   review=dict(schema=mod.REVIEW_SCHEMA,approved=True,scope=copy.deepcopy(mod.SCOPE),source_root=m['root'],output_root=m['output_root'],files=copy.deepcopy(m['files']),parent_preparation_readset=copy.deepcopy(m['qualification_parent_preparation_readset']),historical_short_source=copy.deepcopy(m['qualification_historical_short_source']),short2k_helper_refs=copy.deepcopy(m['short2k_helper_refs']))
   MUTATE(authority,review,m)
   def read(r,*a,**k):
    if r==AUTH:return json.dumps(authority).encode()
    if r==REVIEW:return json.dumps(review).encode()
    raise ValueError('unknown synthetic Ref; no actual approval read or issued')
   mod.read_ref=read
   try:
    result=original_window(m,clock=clock,require_phase=require_phase)
    CHECKED.append(dict(root=m['root'],output=m['output_root'],authority=m['qualification_authority_ref'],clock=clock,require_phase=require_phase))
    return result
   finally:mod.read_ref=original_read
  mod.execution_window=window
 return mod
Q.module=module
class ActualProducer(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  baseline=Q.render(permit_materialized=False);Q.inverse(baseline)
  assert len(baseline['files'])==472
  cls.original_root,cls.original_out=Q.ROOT,Q.OUT
 def setUp(self):
  global MUTATE
  self.tmp=tempfile.TemporaryDirectory(prefix='bole-phase-V4-software-')
  Q.ROOT=Path(self.tmp.name)/'source';Q.OUT=Path(self.tmp.name)/'output'
  MUTATE=lambda a,r,m:None;CHECKED.clear();PARENT_CALLS.clear()
  sys.modules['runtime_lossless_imports']=Q
 def tearDown(self):
  Q.ROOT,Q.OUT=self.original_root,self.original_out;self.tmp.cleanup()
 def mapping(self,authority=AUTH):
  return P.prepare_mapping(HERE,authority)
 def test_real_prepare_mapping_new_authority_only_after_rebase(self):
  b=self.mapping();Q.inverse(b)
  self.assertEqual(b['manifest']['qualification_authority_ref'],AUTH)
  self.assertEqual(len(CHECKED),1);self.assertEqual(CHECKED[0]['root'],str(Q.ROOT))
  self.assertFalse(CHECKED[0]['clock']);self.assertTrue(all(x['authority_ref']is None for x in PARENT_CALLS))
 def test_real_materialize_all_files_and_metadata(self):
  result=P.materialize(HERE,AUTH)
  self.assertTrue(result['prepared_only']);self.assertFalse(result['bound_source_created'])
  m=json.loads(Path(result['prepared_template']['path']).read_bytes())
  ledger=json.loads(Path(result['inverse_delta']['path']).read_bytes())
  self.assertEqual(len(m['files']),472);self.assertEqual(len(ledger),7)
  for n,r in m['files'].items():
   p=Q.ROOT/n;b=p.read_bytes()
   self.assertEqual(r,dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
  self.assertFalse((Q.ROOT/'SOURCE_BOUND.json').exists());self.assertFalse(Q.OUT.exists())
  self.assertEqual(m['qualification_authority_ref'],AUTH)
 def test_repeat_materialize_refuses_overwrite(self):
  P.materialize(HERE,AUTH)
  with self.assertRaises(FileExistsError):P.materialize(HERE,AUTH)
 def reject(self,fn):
  global MUTATE
  MUTATE=fn
  with self.assertRaises(ValueError):self.mapping()
  self.assertFalse(Q.ROOT.exists())
 def test_wrong_review_root(self):self.reject(lambda a,r,m:r.update(source_root=CACHE['manifest']['root']))
 def test_wrong_review_output(self):self.reject(lambda a,r,m:r.update(output_root=CACHE['manifest']['output_root']))
 def test_wrong_review_source_bytes(self):self.reject(lambda a,r,m:r['files']['host_service.py'].update(sha256='0'*64))
 def test_wrong_review_helper(self):self.reject(lambda a,r,m:r['short2k_helper_refs'].pop('phase_helper'))
 def test_wrong_review_parent(self):self.reject(lambda a,r,m:r.update(parent_preparation_readset={}))
 def test_wrong_scope(self):self.reject(lambda a,r,m:a['scope'].update(output_tokens=1024))
 def test_unapproved(self):self.reject(lambda a,r,m:a.update(approved=False))
 def test_wrong_authority_schema(self):self.reject(lambda a,r,m:a.update(schema='wrong'))
 def test_missing_review_ref(self):self.reject(lambda a,r,m:a.update(MAIN_review_ref=None))
 def test_unknown_authority_ref(self):
  with self.assertRaises(ValueError):self.mapping(dict(AUTH,sha256='c'*64))
 def test_default_unbound_stays_unbound(self):
  b=self.mapping(None)
  self.assertIsNone(b['manifest']['qualification_authority_ref']);self.assertEqual(CHECKED,[])
  self.assertFalse(b['source_bound']);self.assertFalse(b['execution_ready'])
if __name__=='__main__':unittest.main()

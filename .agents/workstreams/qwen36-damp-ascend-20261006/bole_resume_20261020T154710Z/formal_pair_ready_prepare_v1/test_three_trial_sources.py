"""Software-only tests of actual six-source rendering and existing three-pair entry."""
import copy,importlib.util,json,shutil,unittest,uuid
from pathlib import Path
import three_trial_sources as S
import checked_pair_math as M
import test_pair_math as OLD
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.base=S.P/('three-trial-test-'+uuid.uuid4().hex)
  cls.ref=S.materialize(cls.base);cls.value=S.validate(cls.ref)
  cls.pairs,cls.data=OLD.Tests().fixture()
  for i,pair in enumerate(cls.pairs):
   for mode,arm in(('OFF','native_ar'),('ON','bole')):
    ident=pair[mode]['identity'];source=cls.value['trials'][i]['arms'][arm]
    ident['source_ref']=source
    key='actual-six-fixture-command-'+str(i)+mode
    ident['server_command_ref']=key
    cls.data[key]=dict(cls.data['cmd'+mode],source=source)
 @classmethod
 def tearDownClass(cls):
  assert cls.base.parent==S.P and cls.base.name.startswith('three-trial-test-')
  shutil.rmtree(cls.base)
 def reader(self,r):return S.obj(r)if type(r)is dict else self.data[r]
 def test_real_source_set_and_existing_math(self):
  # Execute the actual rendered observer fixed_request, not a caller recipe.
  m=S.obj(self.value['trials'][0]['arms']['bole'])
  t=Path(m['files']['formal_token_client.py']['path']).read_text()
  node=next(n for n in __import__('ast').parse(t).body if isinstance(n,__import__('ast').FunctionDef)and n.name=='fixed_request')
  env={'MODEL':'qwen36-mxr-eager','need':S.need}
  exec(compile(__import__('ast').Module(body=[node],type_ignores=[]),'actual-rendered-observer','exec'),env)
  body=env['fixed_request']([1]*131)
  self.assertEqual(body,self.pairs[0]['ON']['observation']['request'])
  result=M.checked_math(self.pairs,obj=self.reader,source_set_ref=self.ref)
  self.assertEqual(len(result['source_pair']),3)
  self.assertTrue(result['all_three_E2E_at_least_1_10'])
  self.assertFalse(result['formal_qualification'])
 def test_wrong_trial_and_duplicate_request_rejected(self):
  for fault in ('source','duplicate','overlap','tokens','threshold'):
   pairs=copy.deepcopy(self.pairs)
   if fault=='source':pairs[1]['ON']['identity']['source_ref']=self.value['trials'][0]['arms']['bole']
   if fault=='duplicate':pairs[1]['ON']['observation']['request_id']=pairs[0]['ON']['observation']['request_id']
   if fault=='overlap':pairs[1]['ON']['observation']['request_start_monotonic_ns']=1
   if fault=='tokens':pairs[1]['ON']['observation']['ordered_token_ids'].pop()
   if fault=='threshold':pairs[1]['OFF']['observation'].update(T_total_ns=1099,TPOT_numerator_ns=999)
   # The exact six-source gate is independently exercised above; reuse its
   # successful read-only value only for downstream arithmetic fault isolation.
   original=S.validate
   try:
    S.validate=lambda r:self.value if r==self.ref else original(r)
    with self.subTest(fault=fault),self.assertRaises(ValueError):M.checked_math(pairs,obj=self.reader,source_set_ref=self.ref)
   finally:S.validate=original
 def test_renderer_entire_bytes_and_manifest_not_recipe(self):
  trials=S.render(self.base,permit_materialized=True)
  self.assertTrue(S.verify_equivalence(trials))
  for fault in ('math','output','added'):
   b=copy.deepcopy(trials)
   if fault=='math':b[1]['arms']['bole']['files']['strict_token_timing.py']+=b'\n# altered'
   if fault=='output':b[1]['arms']['bole']['files']['contract090.py']=b[1]['arms']['bole']['files']['contract090.py'].replace(b'OUTPUT_POSIX=',b'OUTPUT_POSIX_EXTRA=',1)
   if fault=='added':b[2]['arms']['native_ar']['files']['foreign.py']=b'pass'
   with self.subTest(fault=fault),self.assertRaises(ValueError):S.verify_equivalence(b)
  actual=S.obj(self.value['trials'][1]['arms']['bole'])
  actual['common']['HF32']=True
  path=Path(self.value['trials'][1]['arms']['bole']['path'])
  original=path.read_bytes()
  try:
   path.write_bytes(json.dumps(actual).encode())
   with self.assertRaises(ValueError):S.validate(self.ref)
   bad=copy.deepcopy(self.value);bad['trials'][1]['arms']['bole']=S.ref(path)
   badpath=self.base/'REHASHED_BAD_MANIFEST_SET.json'
   with badpath.open('xb')as stream:stream.write(json.dumps(bad).encode())
   with self.assertRaisesRegex(ValueError,'complete actual renderer manifest equality'):S.validate(S.ref(badpath))
  finally:path.write_bytes(original)
if __name__=='__main__':unittest.main()

"""Software provenance/ABI controls only; no actual recovery/model PASS."""
import copy,hashlib,importlib.util,json,os,subprocess,sys,tempfile,types,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import io128 as C,receiver128 as R,reader_transform128 as T
OLD=Path(os.environ['SOURCE128_MODEL_PREDECESSOR'])
def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Controls(unittest.TestCase):
 def test_real_original_reader_whole_inverse(self):
  raw=(OLD/'plugin/qwen36_deltalog_service/split_qualification.py').read_bytes();text=T.transform(raw);self.assertEqual(T.inverse(text),raw)
  edits=json.loads((P/'READER_EDITS128.json').read_bytes())['edits']
  for line in raw.decode().splitlines():
   if not any(line in a.splitlines()for a,_ in edits):self.assertIn(line,text.splitlines())
  with self.assertRaises(ValueError):T.transform(raw+b'\n')
 def fixture(self):
  before=list(sys.path);sys.path.insert(0,str(OLD))
  try:f=load(OLD/'test_domain_admission.py','_128_original101_fixture');m,o=f.fixture()
  finally:sys.path[:]=before
  old=o['owner'];old.update(primary="independent consumer ValueError('actual GE child failed; preserved logs/raw')",diagnostic_capture_complete=False,independent_consumer=None)
  o['old']['primary']="ValueError('independent raw numerical/bitwise gate')"
  rs={'label':'actual-distinct-recovery-source-fixture'}
  stage=dict(schema='deltalog.anchor-consumer-CPU-recovery/v127',source=rs,producer_source=m['bridge024_source_ref'],actual_original_producer=old['result'],preserved_original_strict={'label':'old'},domain={'label':'domain'},pass_gate=True,diagnostic_capture_complete=True,domain_checks_pass=True,old_failure_unchanged=True,NPU=False,NPU_reexecuted=False,model_ready=False,model_admitted=False,performance_ready=False)
  proof=dict(consumer_source=rs,recovery_owner={'label':'separate-recovery-owner'},stage_ref={'label':'separate-stage'},receiver_source={'label':'current128-reader'})
  raw=(OLD/'plugin/qwen36_deltalog_service/split_qualification.py').read_bytes();ns={'__name__':'_software_domain_tail','__file__':str(OLD/'plugin/qwen36_deltalog_service/split_qualification.py')};exec(compile(T.transform(raw),'<actual-derived101-source>','exec'),ns)
  class Reader:
   need=staticmethod(C.need)
   @staticmethod
   def obj(r):return o[r['label']]
   @staticmethod
   def obj_file(r):return None
  ns['C']=Reader;ns['META']=f.META;ns['RECOVERY']=lambda reader,context:(old,o['producer'],stage,proof)
  return ns,m,o,stage
 def test_unchanged_full_domain_tail_retains_failed_original(self):
  ns,m,o,s=self.fixture();v=ns['consume'](m)
  self.assertTrue(v['diagnostic_smoke_admitted']);self.assertFalse(v['model_ready']);self.assertIsNotNone(o['owner']['primary']);self.assertIsNone(o['owner']['independent_consumer']);self.assertFalse(o['old']['pass_gate']);self.assertNotIn('owner',v)
 def test_old_state_sidecar_rows_contract_remain_hard(self):
  for kind in ('state','sidecar','missing','contract','history'):
   ns,m,o,s=self.fixture()
   if kind=='state':o['domain']['rows'][0]['prefill']['flush_CPU64_relative_l2']=7.93e-7
   elif kind=='sidecar':o['domain']['sidecar_results'][0]['audit']['passed']=False
   elif kind=='missing':o['domain']['rows'].pop()
   elif kind=='contract':o['domain']['validation_contract']=dict(o['domain']['validation_contract'],seed=0)
   else:o['domain']['rows'][0]['cross_history']['candidate_vs_native']=float('nan')
   with self.assertRaises(ValueError):ns['consume'](m)
 def test_new_CPU_stage_is_not_old_pair(self):
  ns,m,o,s=self.fixture();s['schema']='deltalog.eager-component-operational-consumption/v088'
  with self.assertRaises(ValueError):ns['consume'](m)
 def test_pending_recovery_no_IO(self):
  class NoIO:
   need=staticmethod(C.need)
   @staticmethod
   def obj(r):raise AssertionError('no future Ref read')
  with self.assertRaisesRegex(ValueError,'pending'):R.admit(NoIO,{},None,{})
  plan=dict(schema='deltalog.recovered-component-model-input/v128',receiver_source_ref={},old_model_template_ref=R.OLD_TEMPLATE,recovery_template_ref=R.R2_TEMPLATE,actual_fault_ref=R.FAULT)
  with self.assertRaisesRegex(ValueError,'future recovery'):R.load_recovery(NoIO,{},plan,{})
 def test_real_old_fault_category_uses_exact_original_bundle(self):
  data=json.loads((P/'FAULT_FIXTURE128.json').read_bytes());self.assertEqual(data['bundle_ref'],R.FAULT)
  e=data['bundle'];self.assertIn('TimeoutExpired',e['small_documents']['logs']['stderr']);self.assertIsNotNone(e['small_documents']['owner']['primary']);self.assertTrue(e['small_documents']['numeric_cleanup']['resource_release_verified']);self.assertTrue(e['small_documents']['consumer_cleanup']['resource_release_verified'])
  helper=load(Path(os.environ['SOURCE128_RECOVERY_PREDECESSOR'])/'provenance127.py','_128_actual_fault_predicate')
  docs={json.dumps(e['refs'][k],sort_keys=True):v for k,v in e['small_documents'].items()}
  for x in e['inspect'].values():docs[json.dumps(x['ref'],sort_keys=True)]=x['projection']
  docs[json.dumps(e['refs']['source'],sort_keys=True)]=dict(files={'raw_reader_entry.py':dict(path=e['refs']['source']['path'].rsplit('/',1)[0]+'/raw_reader_entry.py')})
  docs[json.dumps(e['refs']['producer'],sort_keys=True)]=dict(source=e['refs']['source'],primary=None,steps=160,NPU=True,graph=False,records=[dict(raw=dict(path='main-%d'%j))for j in range(328)],actual_sidecar_records=[dict(path='side-%d'%j)for j in range(351)])
  helper.validate(e,lambda r:docs[json.dumps(r,sort_keys=True)])
  docs[json.dumps(e['refs']['logs'],sort_keys=True)]['stderr']=e['small_documents']['logs']['stderr'].replace('TimeoutExpired','ValueError')
  with self.assertRaises(ValueError):helper.validate(e,lambda r:docs[json.dumps(r,sort_keys=True)])
 def test_real_IO_bad_hash_or_missing_ref(self):
  with tempfile.TemporaryDirectory()as td:
   f=Path(td)/'data';f.write_bytes(b'actual');r=C.ref(f);self.assertEqual(C.obj_file(r),f)
   with self.assertRaises(ValueError):C.obj_file(dict(r,sha256='0'*64))
   f.unlink()
   with self.assertRaises(ValueError):C.obj_file(r)
 def test_actual_I_ON_missing_future_refs(self):
  r=subprocess.run([sys.executable,'-I','-B',str(P/'bind128.py'),'--execute'],capture_output=True,text=True)
  self.assertNotEqual(r.returncode,0);self.assertIn('actual required input pending',r.stderr)
 def test_ambient_transform_alias_cannot_replace_source(self):
  prior=sys.modules.get('reader_transform128');sys.modules['reader_transform128']=types.SimpleNamespace(transform=lambda _:(_ for _ in()).throw(AssertionError('ambient alias')))
  try:
   fresh=load(P/'receiver128.py','_128_fresh_exact_module');raw=(OLD/'plugin/qwen36_deltalog_service/split_qualification.py').read_bytes();self.assertEqual(T.inverse(fresh.transform(raw)),raw)
  finally:
   if prior is None:sys.modules.pop('reader_transform128',None)
   else:sys.modules['reader_transform128']=prior
 def test_exact_model_overlay_inverse_and_closure(self):
  b=(P/'bind_model128.py').read_text(encoding='utf8');ed=json.loads((P/'MODEL_OVERLAY_EDITS128.json').read_bytes())
  for old,new in reversed(ed['binder']['edits']):self.assertEqual(b.count(new),1);b=b.replace(new,old)
  self.assertEqual(b.encode(),(OLD/'bind_source.py').read_bytes())
  d=(P/'domain_qualification128.py').read_text(encoding='utf8');d=d.replace(ed['domain']['replacement_closure'],ed['domain']['original_closure'])
  self.assertEqual(d.encode(),(OLD/'domain_qualification.py').read_bytes())
  self.assertIn('return api(m).closure(C,m)',(P/'domain_qualification128.py').read_text())
if __name__=='__main__':unittest.main()

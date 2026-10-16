import ast,copy,importlib.util,json,subprocess,sys,tempfile,types,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import bridge_io as C,storage_bridge093 as S
class Tests(unittest.TestCase):
 def test_real_ON_cold_missing_and_wrong_refs(self):
  args=[sys.executable,'-I','-B',str(P/'run052.py'),'--execute','--phase','bind','--template-ref','{}']
  for extra,text in(([],'actual121 evidence mandatory'),(['--storage-seal-evidence-ref','null'],'exact source-bound121 evidence path'),(['--storage-seal-evidence-ref',json.dumps(dict(S.EVIDENCE093,sha256='0'*64))],'exact source-bound121 evidence path')):
   p=subprocess.run(args+extra,capture_output=True,text=True,timeout=15);self.assertNotEqual(p.returncode,0);self.assertIn(text,p.stderr)
  p=subprocess.run(args+['--storage-seal-evidence-ref',json.dumps(S.EVIDENCE093)],capture_output=True,text=True,timeout=15);self.assertNotEqual(p.returncode,0);self.assertIn('exact source-bound121 evidence path',p.stderr)
  # Old093 evidence must not be repackaged as a119 qualification.
 def test_accept_existing_never_calls_seal(self):
  original=S.api;calls=[];good=copy.deepcopy(S.GENERATION8)
  fake=types.SimpleNamespace(ROOT=Path('/root'),validate=lambda *x:(dict(source_manifest_ref=S.SOURCE093),{},list(range(6))),ref=lambda p:good,old=lambda:types.SimpleNamespace(generations=lambda root:[Path('/root/STORAGE_LEDGER061.8.json')]),chain=lambda *x:good,seal_generation=lambda *x:(_ for _ in()).throw(AssertionError('must never create9')))
  S.api=lambda *x:fake
  try:
   self.assertEqual(S.accept_existing(C,{},S.EVIDENCE093,{}),S.GENERATION8)
   good['sha256']='0'*64
   with self.assertRaises(ValueError):S.accept_existing(C,{},S.EVIDENCE093,{})
  finally:S.api=original
 def test_math_raw_and_coverage_byte_unchanged(self):
  import declared_baselines088r6r1 as F
  proof=F.historical_R1()
  names=('producer.py','run_consumer088.py','consumer088.py','capture088.py','collection_policy.py','raw_codec.py','oracle.py','precast.py','direct_round.py','preregister.py','qwen36_deltalog_fresh/native_fixture.py','qwen36_deltalog_fresh/provider.py','qwen36_deltalog_fresh/primitives.py','qwen36_deltalog_fresh/runtime_helpers.py')
  for n in names:self.assertEqual(F.fingerprint(P/n),proof['files'][n],n)
 def test_manifest_ro_and_no_new_seal_source(self):
  m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());self.assertEqual(m['storage093_source_ref'],S.SOURCE093);self.assertIsNone(m['storage_seal_evidence_ref']);self.assertIsNone(m['storage_seal_generation_ref'])
  for r in m['files'].values():
   if r['path'].startswith(m['root']+'/'):
    p=P/r['path'][len(m['root'])+1:];self.assertEqual(C.ref(p)['sha256'],r['sha256'])
  text=(P/'bind052.py').read_text();self.assertIn('seal093.accept_existing',text);self.assertNotIn('seal_generation(',text)
  for n in('host.py','run052.py','storage_bridge093.py','bind052.py'):ast.parse((P/n).read_bytes())
if __name__=='__main__':unittest.main()

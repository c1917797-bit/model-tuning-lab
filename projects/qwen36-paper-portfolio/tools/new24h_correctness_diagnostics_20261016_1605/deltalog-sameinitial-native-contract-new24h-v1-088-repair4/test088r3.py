import ast,hashlib,importlib.util,json,subprocess,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;O=P.parent/'deltalog-sameinitial-native-contract-new24h-088-repair2';sys.path.insert(0,str(P));import storage_bridge119 as S,bridge_io as C,preregister as G
class Tests(unittest.TestCase):
 def test_all_math_and_consumer_bytes_identical(self):
  old=json.loads((O/'SOURCE_TEMPLATE.json').read_bytes());new=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes())
  changed={'bind052.py','host.py','run052.py','test088r2.py'}
  for n,r in old['files'].items():
   if n in changed:continue
   self.assertEqual((new['files'][n]['bytes'],new['files'][n]['sha256']),(r['bytes'],r['sha256']),n)
 def test_actual_cold_ON_requires119_before_anybind(self):
  a=[sys.executable,'-I','-B',str(P/'run052.py'),'--execute','--phase','bind','--template-ref','{}']
  for extra,error in (([],'actual119 evidence required'),(['--storage-seal-evidence-ref','{}'],'exact119 evidence path')):
   r=subprocess.run(a+extra,capture_output=True,text=True,timeout=15);self.assertNotEqual(r.returncode,0);self.assertIn(error,r.stderr)
 def test_storage_chain_calls_before_reserve(self):
  text=(P/'host.py').read_text();self.assertIn('storage_bridge119.install(C,m,storage);storage.reserve',text)
  self.assertIn('storage_bridge119.readset(C,m)',text);self.assertIn('seal.final_verify(',text)
  helper=(P/'storage_bridge119.py').read_text();self.assertIn('S.validate(er,SOURCE119)',helper);self.assertIn("'STORAGE_LEDGER061.12.json'",helper);self.assertIn('closed_stat(S,p)',helper)
 def test_same_source_smoke_not_reused(self):
  oldsource={'software':'actual-old-source'};newsource={'software':'new-source'}
  with self.assertRaisesRegex(ValueError,'same031'):
   G.admit_smoke(dict(schema='deltalog.diagnostic-owned-host/v035',target_source=oldsource),newsource,{})
 def test_actual_cli_default_OFF_and_unchanged_fullscope(self):
  for n in('run031.py','run052.py','entry.py'):
   r=subprocess.run([sys.executable,'-I','-B',str(P/n)],capture_output=True,text=True,timeout=15);self.assertEqual(r.returncode,0,r.stderr)
  m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());old=json.loads((O/'SOURCE_TEMPLATE.json').read_bytes());self.assertEqual(m['validation_contract'],old['validation_contract']);self.assertEqual(m['resources'],old['resources'])
if __name__=='__main__':unittest.main()

import ast,copy,hashlib,importlib.util,json,subprocess,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import preregister as G,collection_policy as K,bridge_io as C
from test_collection_contract import complete
class Contract(unittest.TestCase):
 def test_16_and_160_exact_counts(self):
  for steps,records,sidecars in((16,40,63),(160,328,351)):
   r=complete(steps);self.assertEqual(len(r['records']),records);self.assertEqual(len(r['actual_sidecar_records']),sidecars);self.assertTrue(K.require_complete(C,r,r['source']))
   r['graph']=True
   with self.assertRaises(ValueError):K.require_complete(C,r,r['source'])
 def test_new_smoke_gate_rejects_old_or_unfinished(self):
  sr={'source':'software-only'};o=dict(schema='deltalog.diagnostic-owned-host/v035',target_source=sr,stage='numeric',steps=16,stopped_retained=True,primary=None,secondary=[],bridge_primitive_gate_pass=False,model_ready=False,result={'producer':'software-only'})
  c=dict(schema='deltalog.eager-component-operational-consumption/v088',source=sr,actual_result=o['result'],validation_contract=dict(schema='deltalog.eager-sameinitial-native-operational/v088'),diagnostic_capture_complete=True,domain_checks_pass=True,complete_proof=False,original_strict_result_preserved=dict(pass_gate=False))
  self.assertTrue(G.admit_smoke(o,sr,c)['diagnostic160_admitted'])
  for key,value in(('schema','deltalog.diagnostic-consumption/v043'),('domain_checks_pass',False),('complete_proof',True)):
   bad=copy.deepcopy(c);bad[key]=value
   with self.assertRaises(ValueError):G.admit_smoke(o,sr,bad)
 def test_actual_cold_I_ON_producer_frontdoor(self):
  r=subprocess.run([sys.executable,'-I','-B',str(P/'test_producer_frontdoor.py'),'-v'],capture_output=True,text=True,timeout=30)
  self.assertEqual(r.returncode,0,r.stderr);self.assertIn('Ran 4 tests',r.stderr)
 def test_all_local_readset_exact_and_default_off(self):
  m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());root=m['root'];self.assertIsNone(m['storage_seal_evidence_ref'])
  for r in m['files'].values():
   if r['path'].startswith(root+'/'):
    q=P/r['path'][len(root)+1:];b=q.read_bytes();self.assertEqual((len(b),hashlib.sha256(b).hexdigest()),(r['bytes'],r['sha256']))
  for name in('run052.py','producer.py','run_consumer088.py'):
   r=subprocess.run([sys.executable,'-I','-B',str(P/name)],capture_output=True,text=True,timeout=10)
   self.assertEqual(r.returncode,0,r.stderr);self.assertIn('disabled',r.stdout)
if __name__=='__main__':unittest.main()

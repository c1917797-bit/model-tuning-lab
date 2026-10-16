import copy,importlib.util,json,subprocess,sys,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import qualification106 as Q
class Receiver(unittest.TestCase):
 def test_actual_model_gate_rejects_old101_and_pending101R1(self):
  T=P.parent;old=json.loads((P/'dependencies/old101_SOURCE_TEMPLATE.json').read_bytes());newpath=Path(Q.MODEL_TEMPLATE['path'])if sys.platform=='linux'else T/'deltalog-real-worker-new24h-101-repair5/SOURCE_TEMPLATE.json';new=json.loads(newpath.read_bytes())
  old['prepared_only']=False;old['prepared_template']=dict(path=old['root']+'/SOURCE_TEMPLATE.json',bytes=183458,sha256='4a2482d0a0203971ae278156a876e0a5f8af8b1ad6ee2f4ecda2a6ac0d9e394b')
  actual={'negative-only':'actual old source metadata'};m=dict(model_source_ref=actual)
  for bad in(old,dict(new,prepared_template=Q.MODEL_TEMPLATE)):
   with patch.object(Q,'obj',side_effect=lambda r:bad if r==actual else new):
    with self.assertRaisesRegex(ValueError,'reviewed101'):Q.model_gate(m)
 def test_exact_source_and_unchanged_observerfree_shape_API(self):
  m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());B=Path(Q.MODEL_TEMPLATE['path']).parent if sys.platform=='linux'else P.parent/'deltalog-real-worker-new24h-101-repair5';b=(B/'SOURCE_TEMPLATE.json').read_bytes();import hashlib
  self.assertEqual((len(b),hashlib.sha256(b).hexdigest()),(Q.MODEL_TEMPLATE['bytes'],Q.MODEL_TEMPLATE['sha256']))
  self.assertEqual(m['observed_model_scope'],dict(prefill_tokens=[2048],max_sequences=1,actual_model_decode_steps=9,requests=2))
  for n,r in json.loads((P/'dependencies/DONOR106_FILES.json').read_bytes()).items():
   if n not in('qualification106.py','test106.py'):
    v=(P/n).read_bytes();self.assertEqual((len(v),hashlib.sha256(v).hexdigest()),(r['bytes'],r['sha256']),n)
  r=subprocess.run([sys.executable,'-I','-B',str(P/'bind106.py'),'--execute','--template-ref','{}'],capture_output=True,text=True,timeout=15)
  self.assertNotEqual(r.returncode,0);self.assertIn('actual reviewed106 template',r.stderr)
if __name__=='__main__':unittest.main()

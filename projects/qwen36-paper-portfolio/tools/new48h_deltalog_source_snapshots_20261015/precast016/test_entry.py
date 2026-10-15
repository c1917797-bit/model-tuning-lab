"""Actual local CLI/AST/read-closure tests; no numerical PASS fixtures."""
import ast,hashlib,json,subprocess,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
class Entry(unittest.TestCase):
 def test_actual_native_length_call_and_negative(self):
  def verify(text):
   calls=[n for n in ast.walk(ast.parse(text)) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='native_step']
   if len(calls)!=1 or len(calls[0].args)!=3 or not isinstance(calls[0].args[2],ast.Name) or calls[0].args[2].id!='native_seq':raise ValueError('native control must use per-sequence lengths')
  text=(P/'producer.py').read_text();verify(text)
  with self.assertRaises(ValueError):verify(text.replace('h.native_step(native,inp,native_seq)','h.native_step(native,inp,seq)'))
  self.assertIn("raw['native_sequence']",(P/'consumer.py').read_text())
 def test_all_modules_parse(self):
  for f in P.glob('*.py'):ast.parse(f.read_text(),filename=str(f))
 def test_actual_default_off(self):
  for n in('producer.py','consumer.py','entry.py'):
   r=subprocess.run([sys.executable,'-I','-B',str(P/n)],capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(r.stdout.strip(),'disabled')
 def test_actual_cli_help(self):
  for n in('producer.py','consumer.py','entry.py'):
   r=subprocess.run([sys.executable,'-I','-B',str(P/n),'--execute','--help'],capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr);self.assertIn('--source-ref',r.stdout)
 def test_source_bytes(self):
  m=json.loads((P/'SOURCE_MANIFEST.json').read_bytes())
  for name,r in m['files'].items():
   b=(P/name).read_bytes();self.assertEqual(len(b),r['bytes']);self.assertEqual(hashlib.sha256(b).hexdigest(),r['sha256'])
  self.assertFalse(m['default_enabled']);self.assertEqual(m['numeric_ref']['sha256'],'14a327bde2ac2186016c1a740595b2fe50ea3be405be9428cf3616c8c0f0cc96');self.assertFalse(m['admission_status']['lifecycle_NPU_executed'])
if __name__=='__main__':unittest.main()

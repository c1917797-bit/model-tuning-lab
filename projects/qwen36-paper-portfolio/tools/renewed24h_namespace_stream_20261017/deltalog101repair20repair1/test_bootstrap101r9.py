import ast,hashlib,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
class Bootstrap(unittest.TestCase):
 def test_fresh_isolated_actual_package(self):
  # Real delivered package/source, not a stub; local path projection only.
  with tempfile.TemporaryDirectory() as td:
   q=Path(td);pm=json.loads((P/'plugin/SOURCE_TEMPLATE.json').read_bytes())
   for n in pm['files']:
    b=(P/'plugin'/n).read_bytes();target=q/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b);pm['files'][n]=dict(path=str(target.resolve()),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
   f=q/'plugin.json';f.write_text(json.dumps(pm),encoding='utf8');b=f.read_bytes();r=dict(path=str(f.resolve()),bytes=len(b),sha256=hashlib.sha256(b).hexdigest());own=P/'entry.py';b=own.read_bytes();m=dict(root=str(P),files={},plugin_template_ref=r,donor008_host_ref=dict(path=str(own),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()));mp=q/'m.json';mp.write_text(json.dumps(m),encoding='utf8')
   code="import sys,json;from pathlib import Path;assert sys.flags.isolated;assert not any('qwen36_deltalog_service'==x for x in sys.modules);sys.path.insert(0,sys.argv[1]);import bootstrap101r9 as B;m=json.loads(Path(sys.argv[2]).read_bytes());B.install(m,sys.argv[1]);print(json.dumps(B.package_proof(m)))"
   v=subprocess.run([sys.executable,'-I','-B','-c',code,str(P),str(mp)],capture_output=True,text=True,env=dict(os.environ,PYTHONPATH='MUST_BE_IGNORED'),timeout=30);self.assertEqual(v.returncode,0,v.stderr);p=json.loads(v.stdout);self.assertTrue(p['isolated']);self.assertEqual(Path(p['file']),q/'qwen36_deltalog_service/__init__.py')
 def test_both_entrypoints_before_package_import(self):
  e=(P/'entry.py').read_text();t=(P/'trace_plugin.py').read_text();self.assertLess(e.index('BOOT.install(m,P)'),e.index('o=overlay();o.environment_original'));self.assertLess(t.index('BOOT.install('),t.index('from qwen36_deltalog_service import runtime'));self.assertIn('WORKER',e);self.assertNotIn("os.environ['PYTHONPATH']",e)
 def test_bad_source_ref_rejected(self):
  import bootstrap101r9 as B
  with self.assertRaises(ValueError):B.checked(dict(path=str(P/'entry.py'),bytes=0,sha256='0'*64))

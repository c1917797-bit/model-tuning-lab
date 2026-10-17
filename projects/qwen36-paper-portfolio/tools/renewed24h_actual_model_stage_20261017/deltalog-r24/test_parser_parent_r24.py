"""Real probe.main pre-backend path; never a fake HAL/operator positive."""
import ast,hashlib,json,pathlib,subprocess,sys,tempfile,unittest
P=pathlib.Path(__file__).resolve().parent
class Parent(unittest.TestCase):
 def build(self,root):
  def put(name,b):p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
  files={}
  for runtime_leaf in('probe.py','parser_payload101r24.py'):files[runtime_leaf]=put(runtime_leaf,(P/runtime_leaf).read_bytes())
  for bootstrap_leaf in('owner_overlay.py','bootstrap101r9.py'):files[bootstrap_leaf]=put(bootstrap_leaf,(P/'software_fixtures'/(bootstrap_leaf+'.txt')).read_bytes())
  worker=put('worker/host.py',b'# source-only worker-root fixture\n')
  package=put('component/SOURCE.json',b'{"files":{}}\n')
  plugin=put('payload/firstdecode_plugin.py',(P/'software_fixtures/firstdecode_plugin.py.txt').read_bytes())
  payload=put('payload/SOURCE.json',(json.dumps(dict(root=str(root/'payload'),files={'firstdecode_plugin.py':plugin},software_fixture=True,qualified=False))+'\n').encode())
  entry="import types\nfrom pathlib import Path\nWORKER=Path("+repr(str(root/'worker'))+");LOW=Path('/source-fixture-only')\ndef overlay():return types.SimpleNamespace(environment=lambda base,*a:dict(base),native_argv=lambda *a:[])\n"
  er=put('frontend_fixture.py',entry.encode())
  m=dict(schema='deltalog.service023-owned-overlay/v025',root=str(root),default_enabled=False,window=dict(start=1792226600,cutoff=1792313000),files=files,entry017_ref=er,donor008_host_ref=worker,plugin_source=package,composite_source_ref=package,runtime_identity=dict(run_id='software-only-no-admission'),firstdecode_contract=dict(payload_source=payload),prepared_only=True,software_fixture=True,model_numeric_qualified=False)
  sr=put('SOURCE_MANIFEST.json',(json.dumps(m)+'\n').encode());return sr,m
 def test_actual_fresh_I_probe_main_reaches_sourcequalified_parent_before_Torch(self):
  with tempfile.TemporaryDirectory()as td:
   root=pathlib.Path(td);sr,m=self.build(root);out=root/'out';out.mkdir()
   code="""import builtins,json,pathlib,sys
sys.path.insert(0,ROOT)
import probe,owner_overlay as O
actual_current=O.current
def fixture_domain(m):
 assert m['software_fixture'] is True and m['prepared_only'] is True and m['model_numeric_qualified'] is False
 return {'software_frontdoor_only':True,'qualified':False}
O.model_gate=fixture_domain
class BeforeBackend(Exception):pass
original_import=builtins.__import__
def stop_backend(name,*a,**k):
 if name=='torch':
  f=sys.modules['firstdecode_plugin'];p=O.obj(MODEL['firstdecode_contract']['payload_source'])
  assert pathlib.Path(f.__file__).resolve()==O.obj_file(p['files']['firstdecode_plugin.py']).resolve()
  from importlib.metadata import EntryPoint
  callback=EntryPoint(name='deltalog_service025_trace',value=EP_VALUE,group='vllm.general_plugins').load()
  assert callback is f.register and callback.__globals__ is f.__dict__
  assert f.validate_registration.__globals__ is f.__dict__
  assert f._registration_state=='disabled' and f._collector is None
  assert 'torch' not in sys.modules and 'torch_npu' not in sys.modules
  assert __import__('os').environ['DL_FIRST_REAL_DECODE_DIAGNOSTIC_ENABLE']=='1'
  raise BeforeBackend('actual probe.main source path reached before backend; no HAL or registration claimed')
 return original_import(name,*a,**k)
builtins.__import__=stop_backend
__import__('os').environ['ASCEND_RT_VISIBLE_DEVICES']='0,1,2,3'
sys.argv=['probe.py','--execute','--mode','parser','--source-ref',json.dumps(SR),'--output',OUTPUT]
try:probe.main()
except BeforeBackend as e:print(str(e))
else:raise AssertionError('must stop before real Torch/HAL')
"""
   ep=(P/'deltalog_service025_trace-0.0.25.dist-info/entry_points.txt').read_text();self.assertEqual(ep.strip(),'[vllm.general_plugins]\ndeltalog_service025_trace = firstdecode_plugin:register')
   prefix='ROOT='+repr(str(root))+';SR='+repr(sr)+';MODEL='+repr(m)+';OUTPUT='+repr(str(out/'CANARY.json'))+';EP_VALUE='+repr(ep.split(' = ')[1].strip())+'\n'
   z=subprocess.run([sys.executable,'-I','-B','-c',prefix+code],capture_output=True,text=True,timeout=15);self.assertEqual(z.returncode,0,z.stderr);self.assertIn('actual probe.main source path reached before backend',z.stdout)
 def test_original_parent_import_actual_statement_fails_without_payload_root(self):
  tree=ast.parse((P/'software_fixtures/probe_r23.py.txt').read_bytes());node=next(n for n in ast.walk(tree)if isinstance(n,ast.Import)and any(a.name=='firstdecode_plugin'for a in n.names));body=ast.unparse(node)
  with tempfile.TemporaryDirectory()as td:
   code="import sys;sys.path.insert(0,"+repr(td)+");assert 'firstdecode_plugin' not in sys.modules\n"+body
   z=subprocess.run([sys.executable,'-I','-B','-c',code],capture_output=True,text=True,timeout=10);self.assertNotEqual(z.returncode,0);self.assertIn("No module named 'firstdecode_plugin'",z.stderr)
 def test_declared_hash_or_ambient_payload_refused_and_whole_parent_inverse(self):
  inverse=json.loads((P/'PROBE_INVERSE.json').read_bytes());self.assertEqual((P/'probe.py').read_bytes(),inverse['after_utf8'].encode());self.assertEqual(hashlib.sha256(inverse['before_utf8'].encode()).hexdigest(),inverse['before']['sha256'])
  with tempfile.TemporaryDirectory()as td:
   root=pathlib.Path(td);sr,m=self.build(root)
   code="import json,sys,types;sys.path.insert(0,ROOT);import owner_overlay as O,parser_payload101r24 as H;m=O.current(SR);f=types.ModuleType('firstdecode_plugin');f.__file__='/unreviewed/plugin.py';sys.modules['firstdecode_plugin']=f\ntry:H.prepare(O,m,ROOT)\nexcept ValueError as e:assert 'namespace' in str(e);assert sys.modules['firstdecode_plugin'] is f;print('foreign rejected before backend')\nelse:raise AssertionError('foreign accepted')"
   z=subprocess.run([sys.executable,'-I','-B','-c','ROOT='+repr(str(root))+';SR='+repr(sr)+'\n'+code],capture_output=True,text=True,timeout=10);self.assertEqual(z.returncode,0,z.stderr)
   code2="import json,sys,types;sys.path.insert(0,ROOT);import owner_overlay as O,parser_payload101r24 as H;m=O.current(SR);p=O.obj(m['firstdecode_contract']['payload_source']);f=types.ModuleType('firstdecode_plugin');f.__file__=p['files']['firstdecode_plugin.py']['path'];exec(compile('def register():pass\\ndef validate_registration(*a):pass\\n',f.__file__,'exec'),f.__dict__);sys.modules['firstdecode_plugin']=f\ntry:H.prepare(O,m,ROOT)\nexcept ValueError as e:assert 'function identity' in str(e);print('same path wrong function rejected')\nelse:raise AssertionError('fake accepted')"
   z=subprocess.run([sys.executable,'-I','-B','-c','ROOT='+repr(str(root))+';SR='+repr(sr)+'\n'+code2],capture_output=True,text=True,timeout=10);self.assertEqual(z.returncode,0,z.stderr)
   (root/'payload/firstdecode_plugin.py').write_bytes(b'# mutated\n')
   z=subprocess.run([sys.executable,'-I','-B','-c','ROOT='+repr(str(root))+';SR='+repr(sr)+"\nimport sys;sys.path.insert(0,ROOT);import owner_overlay as O,parser_payload101r24 as H;H.prepare(O,O.current(SR),ROOT)"],capture_output=True,text=True,timeout=10);self.assertNotEqual(z.returncode,0);self.assertIn('exact source Ref',z.stderr)
if __name__=='__main__':unittest.main()

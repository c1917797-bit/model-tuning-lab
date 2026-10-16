import ast,importlib.util,pathlib,subprocess,sys,unittest
P=pathlib.Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def test_all_real_cli_cold_off(self):
  for name in('host.py','entry.py','producer.py','consume.py','bind_composite.py'):
   p=subprocess.run([sys.executable,'-I','-B',str(P/name)],capture_output=True,text=True);self.assertEqual(p.returncode,0,(name,p.stderr))
 def test_exact_installed_flush_extract_cpu_live_dead(self):
  import torch,types
  src=P/'dependencies/primitives021.py'
  import hashlib
  self.assertEqual(hashlib.sha256(src.read_bytes()).hexdigest(),'1b9a2e53ce137f319ca5939be6e21fa293735edd363cdc37f7b438626e985470')
  fn=next(x for x in ast.parse(src.read_bytes()).body if isinstance(x,ast.FunctionDef)and x.name=='_flush_slots');ns=dict(Any=object,CAPACITY=7,VALUE_HEADS=12,KEY_HEADS=4,_audit=lambda *a,**k:None)
  exec(compile(ast.Module(body=[fn],type_ignores=[]),str(src),'exec'),ns)
  base=torch.ones(3,12,128,128);aux=dict(k_log=torch.full((3,4,7,128),float('nan'),dtype=torch.bfloat16),u_log=torch.full((3,12,7,128),float('nan')),lambda_log=torch.zeros(3,12,16),decay=torch.zeros(3,12,16),length=torch.zeros(3,12,16,dtype=torch.int32));layer=types.SimpleNamespace(kv_cache=[None,base],prefix='CPU-boundary-only')
  ns['_flush_slots'](torch,layer,aux,torch.tensor([0]),'test');self.assertTrue(bool((base==1).all()))
  aux['length'][0,:,0]=1
  with self.assertRaises(RuntimeError):ns['_flush_slots'](torch,layer,aux,torch.tensor([0]),'liveNaN')
 def test_source_ast_and_no_old013_gate(self):
  for p in P.rglob('*.py'):ast.parse(p.read_bytes())
  text=(P/'qwen36_deltalog_fresh/provider.py').read_text();self.assertNotIn('direct-CPU64-RNE-readout/v013',text)
  tree=ast.parse(text);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='source_admission')
  imp=next(n for n in ast.walk(fn)if isinstance(n,ast.ImportFrom)and n.module=='historical022056')
  self.assertEqual([(a.name,a.asname)for a in imp.names],[('admit','historical_admit')])
  call=next(n for n in ast.walk(fn)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='historical_admit')
  self.assertEqual(ast.dump(call),ast.dump(ast.parse("historical_admit(api,m['composite_source_ref'],lifecycle_ref)",mode='eval').body))
  import historical022056 as H
  raw=(P/'dependencies/old022_composite.py').read_bytes();original=raw.decode();node=next(n for n in ast.parse(original).body if isinstance(n,ast.FunctionDef)and n.name=='admit_receipt')
  body=''.join(original.splitlines(True)[node.lineno-1:node.end_lineno]);self.assertEqual(body.count(H.OLD),1)
  captured=[]
  import unittest.mock as mock
  real_compile=compile
  def recording(source,*args,**kwargs):
   if isinstance(source,str)and source.startswith('def admit_receipt('):captured.append(source)
   return real_compile(source,*args,**kwargs)
  with mock.patch('builtins.compile',recording):H.derive(raw,{})
  self.assertEqual(captured,[body.replace(H.OLD,H.NEW)])
  self.assertEqual(captured[0].replace(H.NEW,H.OLD),body)
  self.assertIn("if m.get('prepared_only',True)",text)
if __name__=='__main__':unittest.main()

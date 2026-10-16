import ast,copy,importlib.util,json,subprocess,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
O=load(P/'owned_cpu.py','owner083');E=load(P/'cpu_entry.py','entry083')
D=Path('C:/Users/Huawei/AppData/Local/Temp/deltalog-state-drift-cpu-new24h-20261016-074-repair2/owned_cpu.py')
class Tests(unittest.TestCase):
 def test_off(self):
  for n in('owned_cpu.py','cpu_entry.py'):
   p=subprocess.run([sys.executable,'-I','-B',str(P/n)],capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr);self.assertFalse(json.loads(p.stdout)['enabled'])
 def test_donor_safety_unchanged(self):
  old=ast.parse(D.read_bytes());new=ast.parse((P/'owned_cpu.py').read_bytes())
  for name in('docker_argv','create_argv','inspect_owned','output_scan','closure'):
   a=next(x for x in old.body if getattr(x,'name',None)==name);b=next(x for x in new.body if getattr(x,'name',None)==name);self.assertEqual(ast.dump(a),ast.dump(b))
 def test_go_wrapper(self):
  self.assertEqual(O.docker_argv(['/usr/bin/docker','ps']),['/usr/bin/prlimit','--as=unlimited','--','/usr/bin/docker','ps'])
  with self.assertRaises(ValueError):O.docker_argv(['/bin/docker','ps'])
 def test_actual_create_argv(self):
  argv=O.create_argv(7,{'/src':('/src',False),'/out':('/adakv-results',True)},{'ASCEND_RT_VISIBLE_DEVICES':''},'own',['-I','-B','/src/cpu_entry.py'])
  self.assertIn('--read-only',argv);self.assertIn('--network',argv);self.assertNotIn('--device',argv);self.assertIn('type=bind,src=/src,dst=/src,readonly',argv)
 def test_stage_real_receiver(self):
  d=dict(schema='deltalog.native-prefill-cpu-preflight/v083',source={'s':1},guest_source={'g':1},producer={'p':1},primary=None,extract_pass=True,qualification=False,NPU_reexecuted=False,bootstrap_invoked=False)
  O.receive_preflight(d,{'s':1},{'g':1},{'p':1})
  for k,v in [('source',{}),('guest_source',{}),('producer',{}),('primary','actual failure'),('extract_pass',False),('qualification',True),('bootstrap_invoked',True)]:
   b=copy.deepcopy(d);b[k]=v
   with self.assertRaises(ValueError):O.receive_preflight(b,{'s':1},{'g':1},{'p':1})
 def test_import_guard(self):
  E.import_guard('import',('torch',))
  for name in('acl','torch_npu','vllm','vllm_ascend','vllm.foo','vllm_ascend.foo'):
   with self.assertRaises(ValueError):E.import_guard('import',(name,))
if __name__=='__main__':unittest.main()

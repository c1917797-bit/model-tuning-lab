import ast,json,subprocess,sys,unittest,tempfile,textwrap,time,types
from pathlib import Path
P=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def test_official_source_dependency_order(self):
  runtime=(P/'plugin/qwen36_deltalog_service/runtime.py').read_text();observer=(P/'native_observer_plugin101r12.py').read_text()
  for text in(runtime,observer):
   self.assertLess(text.index('from vllm_ascend.utils import enable_custom_op'),text.index('import vllm_ascend.ops.gdn'))
   self.assertLess(text.index('import vllm_ascend.ops.gdn'),text.index('from vllm_ascend.worker'))
  tree=ast.parse(observer)
  self.assertFalse(any(isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='enable_custom_op'for n in ast.walk(tree)))
 def test_new_process_actual003_order_after_canary(self):
  text=(P/'parser_cold101r17.py').read_text()
  for a,b in [('cann=guest.installed_cann','import torch\n'),('import torch\n','import torch_npu'),('import torch_npu',"api=importlib.import_module"),("api=importlib.import_module",'args=proof.parse')]:self.assertLess(text.index(a),text.index(b))
  self.assertIn('engine_constructed=False',text);probe=(P/'probe.py').read_text()
  self.assertLess(probe.index('canaries.append'),probe.index('cold_argv='));self.assertLess(probe.index('cold_argv='),probe.index('guest=E.private(o)'))
  self.assertIn('180.-(time.monotonic()-parser_started)',probe);self.assertIn('if timeout_error is not None:raise timeout_error',probe)
 def test_fresh_cold_default_off(self):
  r=subprocess.run([sys.executable,'-I','-B',str(P/'parser_cold101r17.py')],capture_output=True,text=True,timeout=10)
  self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(r.stdout.strip(),'disabled')
 def test_native_math_and_failclosed_collector_retained(self):
  s=(P/'native_observer_plugin101r12.py').read_text();self.assertIn('F.install(N,get_forward_context',s)
  self.assertIn("SERVICE023_ENABLE')=='0'",s);self.assertNotIn('runtime.register(',s)
  self.assertIn("cold.returncode==0",(P/'probe.py').read_text())
 def test_actual_timeout_body_preserves_child_stdout_before_rethrow(self):
  text=(P/'probe.py').read_text();begin=text.index('  import subprocess,time\n');end=text.index('  O.need(cold.returncode==0',begin)
  body=textwrap.dedent(text[begin:end])
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);child=root/'cold.py';child.write_text("import time;print('child-start',flush=True);time.sleep(2)\n")
   def need(v,message):
    if not v:raise ValueError(message)
   ns=dict(O=types.SimpleNamespace(obj_file=lambda r:child,need=need),m={'files':{'parser_cold101r17.py':{}}},a=types.SimpleNamespace(output=root/'CANARY.json'),sr={},sys=sys,json=json,parser_started=time.monotonic()-179.7)
   with self.assertRaises(subprocess.TimeoutExpired):exec(compile(body,str(P/'probe.py')+'#actual-timeout-body','exec'),ns)
   receipt=json.loads((root/'FRESH_ENTRY_PARSER_TERMINAL.json').read_bytes())
   self.assertTrue(receipt['timed_out']);self.assertIn('child-start',receipt['stdout']);self.assertIsNone(receipt['returncode']);self.assertLessEqual(receipt['timeout_seconds'],.3)

import ast,copy,importlib.util,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import screen_binding as B
import pair_consume as PC
def report():
 return dict(config=dict(input_tokens=32768,prefix_tokens=16384,output_tokens=1024,requests=40,concurrency=16,warmup_requests=2,ignore_eos=True),summary=dict(benchmark_duration_s=40,failed=0,successful=40,fixed_output_verified=True,output_tokens_per_second=1024),results=[dict(index=i,ok=True,output_tokens=1024,requested_output_tokens=1024,ttft_ms=100,duration_s=1)for i in range(40)])
class Tests(unittest.TestCase):
 def test_source_compiles(self):
  for f in P.rglob('*.py'):compile(f.read_bytes(),str(f),'exec')
 def test_runtime_default_off(self):
  from qwen36_deltalog_screen.runtime import enabled,register
  self.assertFalse(enabled());self.assertIsNone(register())
 def test_same_sync_common_cli(self):
  import server_entry as E
  a=E.command(8230);self.assertIn('--no-async-scheduling',a);self.assertIn('--enforce-eager',a);self.assertEqual(a[a.index('--mamba-cache-mode')+1],'none');self.assertIn('--safetensors-load-strategy',a)
 def test_pair_full40_fixed1024(self):
  r=report();self.assertEqual(PC.arm(r)['throughput'],1024);r['results'][0]['output_tokens']=1023
  with self.assertRaises(ValueError):PC.arm(r)
 def test_pair_wrong_ids_and_nan_rejected(self):
  r=report();r['results'][0]['index']=100
  with self.assertRaises(ValueError):PC.arm(r)
  r=report();r['results'][0]['ttft_ms']=float('nan')
  with self.assertRaises(ValueError):PC.arm(r)
 def test_missing032_qualification_not_ready(self):
  import screen_admission as A
  with self.assertRaises((RuntimeError,KeyError)):A.qualify({}, {})
 def test_no_tensor_observer_in_hot_sources(self):
  for file,names in(('qwen36_deltalog_screen/runtime.py',('_route',)),('qwen36_deltalog_screen/primitives.py',('_flush_slots',))):
   tree=ast.parse((P/file).read_text())
   for fn in [n for n in ast.walk(tree)if isinstance(n,ast.FunctionDef)and n.name in names]:
    for node in ast.walk(fn):
     if isinstance(node,ast.Call)and isinstance(node.func,ast.Attribute):self.assertNotIn(node.func.attr,('item','cpu','tolist','synchronize','save'))
from test_receiver import ReceiverControls
from test_validation_edges import NumericControls,PublicationControls
if __name__=='__main__':unittest.main()

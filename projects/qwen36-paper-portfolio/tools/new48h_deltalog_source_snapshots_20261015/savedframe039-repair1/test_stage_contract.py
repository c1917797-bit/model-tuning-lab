"""Actual entry-produced JSON consumed by actual host CPU predicate AST."""
import ast,copy,importlib.util,json,os,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class StageContract(unittest.TestCase):
 def test_real_entry_output_original_host_predicates(self):
  G=load('_actual039r1entry',P/'entry.py');sr={'source':'software-only'};ar={'authority':'actual-contract-fixture'};lr={'lifecycle':'same-input'};orig={'original':'source'};raw={'raw':'selected'}
  owner=dict(schema='deltalog.diagnostic-owned-host/v035',target_source=orig,primary='old failure retained',stopped_retained=True,secondary=[],steps=160)
  prod=dict(source=orig,primary=None,steps=160,NPU=True,records=[dict(kind='mixed',batch=16,step=80,raw=raw)])
  m=dict(original_failed_owner_ref='owner',original_producer_ref='producer',original_source_ref=orig,selected_raw_ref=raw,files={'diagnose.py':'diagnose'})
  with tempfile.TemporaryDirectory()as td:
   out=Path(td)/'result';argv=[str(P/'entry.py'),'--execute','--stage','cpu-preflight','--source-ref',json.dumps(sr),'--authority-ref',json.dumps(ar),'--lifecycle-ref',json.dumps(lr),'--output',str(out)]
   with patch.object(sys,'argv',argv),patch.dict(os.environ,{'TORCH_DEVICE_BACKEND_AUTOLOAD':'0','ASCEND_RT_VISIBLE_DEVICES':''}),patch.object(G.C,'source',return_value=m),patch.object(G.C,'window'),patch.object(G.C,'obj',side_effect=lambda r:{'owner':owner,'producer':prod}[r]),patch.object(G.C,'load',return_value=types.SimpleNamespace(run=lambda *a:{'diagnostic':'software-only-no-raw'})):G.main()
   v=json.loads((out/'STAGE_RESULT.json').read_bytes());self.assertEqual(v['lifecycle'],lr);self.assertEqual(v['source'],sr);self.assertFalse(v['qualification'])
   tree=ast.parse((P/'host.py').read_text());needs=[n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='need'and len(n.args)>1 and isinstance(n.args[1],ast.Constant)and n.args[1].value in('actual source complete gate','actual current authority gate')]
   self.assertEqual(len(needs),2)
   def accept(value):
    return all(eval(compile(ast.Expression(n.args[0]),str(P/'host.py'),'eval'),dict(v=value,sr=sr,ar=ar,stage='native',self=types.SimpleNamespace()))for n in needs)
   self.assertTrue(accept(v))
   for key in('source','authority'):
    wrong=dict(v);wrong[key]={'wrong':True};self.assertFalse(accept(wrong))
   wrong=dict(v,pass_gate=False);self.assertFalse(accept(wrong))
if __name__=='__main__':unittest.main()

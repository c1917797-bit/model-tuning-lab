"""Local pair binding/source fixtures; not runtime or qualification evidence."""
import ast,importlib.util,types,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('provider009',P/'cap48_provider.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Tests(unittest.TestCase):
 def test_source_bound_pair_and_common_command(self):
  S=types.ModuleType('actual_source_fixture');S.__file__=str(P/'actual_loader/safety_host.py');S.MEM=64*1024**3;S.RESERVE=8*1024**3+512*1024**2;S.HOST_MEM=512*1024**2
  tree=ast.parse(Path(S.__file__).read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('create_argv','validate_inspect')];exec(compile(ast.Module(body=nodes,type_ignores=[]),'fixture','exec'),vars(S))
  c=types.SimpleNamespace(GIB=1024**3);H=types.SimpleNamespace();pairs=[]
  result=m.bind_pair_load(lambda:(c,S,H,pairs))();self.assertIs(result[1],S);self.assertEqual(S.MEM,48*c.GIB);self.assertEqual(S.RESERVE,8*c.GIB);self.assertEqual(H._cap48_source_bound_contract['model_initial_GiB'],56.5)
  command=m.bind_pair_command(lambda port:['serve','model','--port',str(port)])
  d=command(8030);a=command(8031);self.assertEqual(d[4:],a[4:]);self.assertIn('lazy',d);self.assertIn('{"enable_multithread_load":false}',a)
 def test_reject_duplicate_load_option(self):
  with self.assertRaises(ValueError):m.explicit_lazy_argv(['serve','--load-format','auto'])
if __name__=='__main__':unittest.main()

import ast,sys,unittest
from pathlib import Path
P=Path(__file__).parent;sys.path.insert(0,str(P))
import projection_consumer as C
class Tests(unittest.TestCase):
 def fixture(self):
  rows=[dict(call=c,kind='out_proj',layer=0,stage=s)for c in(0,2)for s in('projection.forward.entry','projection.forward.return')]
  calls=[(c,'projection.forward',e)for c in(0,2)for e in('call','return')]
  return dict(rows=rows,projection_trace=dict(schema='bole.root-projection-internal-trace/v1',qualified=False,calls=calls,active={})),[dict(key=['out_proj',0,'projection.forward.return'],bitwise_equal=False)]
 def test_independent_root_comparison_keeps_failure_diagnostic(self):
  w,comparisons=self.fixture();r=C.consume(w,comparisons);self.assertFalse(r['qualified']);self.assertIs(r['first_difference'],comparisons[0])
 def test_missing_root_or_duplicate_boundary_refuses(self):
  w,c=self.fixture();w['rows'].pop()
  with self.assertRaises(ValueError):C.consume(w,c)
  w,c=self.fixture();w['rows'].append(w['rows'][0])
  with self.assertRaises(ValueError):C.consume(w,c)
 def test_real_witness_and_consumer_actual_integration(self):
  s=(P/'root_repeat_witness.py').read_text();tree=ast.parse(s)
  fn=next(x for x in ast.walk(tree)if isinstance(x,ast.FunctionDef)and x.name=='_trace')
  self.assertTrue(any(isinstance(x,ast.Call)and ast.unparse(x.func)=='self.projection.event'for x in ast.walk(fn)))
  self.assertIn('value[\'projection_trace\']=self.projection.finish()',s)
  self.assertIn("<=512*2**10",s);self.assertIn("self.used+n<=TENSOR_CAP",s)
  self.assertIn('projection=projection_consume(w,comparisons)',(P/'root_repeat_consumer.py').read_text())
if __name__=='__main__':unittest.main()

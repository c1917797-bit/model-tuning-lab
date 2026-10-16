import ast,copy,sys,threading,types,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import storage_watch088r6 as W
def actual_finally(clock):
 tree=ast.parse((P/'host.py').read_text(encoding='utf-8'));node=next(n for n in ast.walk(tree)if isinstance(n,ast.Try)and n.finalbody and isinstance(n.finalbody[0],ast.Assign)and any(isinstance(t,ast.Name)and t.id=='cleanup_deadline'for t in n.finalbody[0].targets))
 f=ast.FunctionDef(name='invoke',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='lane'),ast.arg(arg='secondary')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=copy.deepcopy(node.finalbody),decorator_list=[]);ns=dict(time=types.SimpleNamespace(monotonic=lambda:clock[0]));exec(compile(ast.fix_missing_locations(ast.Module(body=[f],type_ignores=[])),str(P/'host.py')+'#actual-cleanup-finally','exec'),ns);return ns['invoke']
class Tests(unittest.TestCase):
 def exercise(self,fail=False):
  clock=[0.];entered=threading.Event();release=threading.Event();done=threading.Event();calls=[];order=[]
  def check(root):
   calls.append(root);entered.set();release.wait(2);done.set()
   if fail:raise ValueError('original closed mutation retained')
  class Observed(W.Watch):
   def request_stop(self):order.append('request_stop');return super().request_stop()
   def close(self,deadline):order.append(('join',deadline));return super().close(deadline)
  w=Observed(check,'/readonly',interval=0);w.start();self.assertTrue(entered.wait(1))
  def cleanup():
   order.append('cleanup');self.assertTrue(w._stop.is_set());clock[0]=60.;release.set();self.assertTrue(done.wait(1))
  lane=types.SimpleNamespace(storage_watch=w,cleanup=cleanup);secondary=[]
  try:
   with patch.object(W,'time',types.SimpleNamespace(monotonic=lambda:clock[0])):actual_finally(clock)(lane,secondary)
   self.assertEqual(order[:2],['request_stop','cleanup']);self.assertIn(('join',90.),order);self.assertEqual(len(calls),1);self.assertFalse(w._thread.is_alive())
   if fail:self.assertEqual(secondary,["storage monitor ValueError('original closed mutation retained')"])
   else:self.assertEqual(secondary,[])
  finally:release.set();w.request_stop();w._thread.join(1)
 def test_actual_finally_stops_before_cleanup_no_late_scan(self):self.exercise()
 def test_current_inflight_exception_not_dropped_by_stop(self):self.exercise(fail=True)
 def test_prior42_retained(self):
  names=['test088r1','test088r2','test088r3','test_typed_readset088r4','test_storage088r5','test_handshake088r6','test_overlay088r6','test_declared_baselines088r6r1'];self.assertEqual(unittest.defaultTestLoader.loadTestsFromNames(names).countTestCases(),42)
if __name__=='__main__':unittest.main()

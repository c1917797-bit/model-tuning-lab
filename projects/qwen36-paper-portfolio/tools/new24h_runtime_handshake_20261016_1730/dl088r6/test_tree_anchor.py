"""Same-snapshot ancestry only; no resource or release credit for retired IDs."""
import importlib.util,pathlib,types,unittest
from unittest import mock
P=pathlib.Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('actual_tree_guard',P/'top_guard.py');T=importlib.util.module_from_spec(s);s.loader.exec_module(T)
class Tree(unittest.TestCase):
 def test_order_and_cycle_unknown_duplicate_refuse(self):
  self.assertEqual(T.tree_order([38,31,37],{31:1,37:31,38:37},31),[31,37,38])
  for pids,parents in[([31,37,37],{31:1,37:31}),([31,37],{31:1,37:999}),([31,37,38],{31:1,37:38,38:37}),([31,37],{31:37,37:31})]:
   with self.assertRaises(ValueError):T.tree_order(pids,parents,31)
 def confirm(self,pid,parent,anchors,forbidden=set(),reader=None):
  return T.confirm(pid,parent,31,forbidden,anchors,dict(status='missing',pid=pid),reader or(lambda p:dict(status='missing',pid=p)),lambda:{31},lambda x:None,pause=lambda _:None)
 def test_retired_parent_anchors_only_same_snapshot_child(self):
  anchors={31};live_owned=[]
  self.assertIsNone(self.confirm(37,31,anchors));anchors.add(37)
  self.assertIsNone(self.confirm(38,37,anchors));self.assertEqual(live_owned,[])
  # A NEW observation starts only with inspected init; old retired parent
  # cannot authorize a child absent from that snapshot's validated chain.
  with self.assertRaises(ValueError):self.confirm(38,37,{31})
 def test_forbidden_unknown_permission_reused_and_live_refuse(self):
  for forbidden in({38},{31,38}):
   with self.assertRaises(ValueError):self.confirm(38,37,{31,37},forbidden)
  with self.assertRaises(ValueError):self.confirm(31,1,{1})
  with self.assertRaises(PermissionError):self.confirm(38,37,{31,37},reader=lambda _:(_ for _ in()).throw(PermissionError('live unreadable')))
  for row in(dict(status='partial'),dict(status='present',start_ticks=9,cgroup='foreign'),dict(status='present',start_ticks=10,cgroup='owned')):
   with self.assertRaises(ValueError):self.confirm(38,37,{31,37},reader=lambda p,row=row:row)
 def test_classify_actual_live_foreign_and_reuse_reject(self):
  m=types.SimpleNamespace(DOCKER='docker',save=lambda *x:None)
  lane=types.SimpleNamespace(active='own',a=types.SimpleNamespace(run_root=P),call=lambda *a:dict(exit_code=0,stdout='31 1 python\n'),h=types.SimpleNamespace(gate_process=lambda p:dict(start_ticks=2,cgroup='own')))
  first=dict(status='present',pid=38,ppid=37,start_ticks=1,state='R',cgroup='foreign')
  with mock.patch.object(T,'snapshot',return_value=first):
   with self.assertRaises(ValueError):T.classify(lane,38,37,31,{31,37},set(),m)
  first=dict(first,cgroup='own')
  with mock.patch.object(T,'snapshot',return_value=first):
   with self.assertRaisesRegex(ValueError,'reused'):T.classify(lane,38,37,31,{31,37},set(),m)
 def test_mechanical_scope_inverse(self):
  import patch_scope
  raw=(P/'scope_adapter.py').read_bytes();changed=patch_scope.transform(raw)
  self.assertIn('parent_anchors.add(pid)',changed);self.assertIn('if proof is None:',changed)
  self.assertNotIn('owned.append(None)',changed);self.assertEqual(changed.replace(patch_scope.AFTER,patch_scope.BEFORE),raw.decode())
if __name__=='__main__':unittest.main()


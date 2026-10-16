import copy,hashlib,importlib.util,json,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
def module():
 s=importlib.util.spec_from_file_location('_actual092guard',P/'top_guard092.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
G=module();FIRST=json.loads((P/'evidence/FIRST_TRANSITION.json').read_bytes())['first'];PID=535517;PPID=535486;INIT=525713
class Controls(unittest.TestCase):
 def run_case(self,frames=None,first=None,forbidden=(),parents=(PPID,),top=(),deadline=None):
  ticks=[0.];records=[];seq=iter(frames or [FIRST,dict(status='missing',pid=PID),dict(status='missing',pid=PID),dict(status='missing',pid=PID)])
  def read(pid):return copy.deepcopy(next(seq,FIRST))
  def pause(s):ticks[0]+=s
  G.confirm(PID,PPID,INIT,set(forbidden),set(parents),copy.deepcopy(first or FIRST),read,lambda:set(top),records.append,pause=pause,clock=lambda:ticks[0],remaining_deadline=deadline,owned_cgroup='d342c233c4821cb8840a542cc472ab65a7d54b844f8c9c9084675a6a8c871c6c')
  return records,ticks[0]
 def test_actual_complete_original_parent_chain(self):
  raw=(P/'evidence/ACTUAL_PROTECTED_OWNERSHIP.json').read_bytes();self.assertEqual(len(raw),52153);self.assertEqual(hashlib.sha256(raw).hexdigest(),'da0d9827ac5a47c5e86a9c1d75e4d815c2c652e537f57e7fa05eaee284366f0d')
  v=json.loads(raw);text=v['actual_owned_top']['stdout'];ppids={int(x.split()[0]):int(x.split()[1])for x in text.splitlines()if x.split()and x.split()[0].isdigit()}
  order=G.tree_order(list(ppids),ppids,INIT);self.assertLess(order.index(PPID),order.index(PID));self.assertEqual(ppids[PID],PPID);self.assertEqual(ppids[PPID],535460);self.assertEqual(ppids[535460],INIT)
  proofs={r['pid']:r for r in v['owned']};self.assertTrue(all(p in proofs for p in (PPID,535460,INIT)))
 def test_actual_R_transition_eventually_missing(self):
  receipts,elapsed=self.run_case();self.assertLess(elapsed,2);self.assertEqual(receipts[-1]['classification'],'original-top-child-confirmed-departed');self.assertFalse(receipts[-1]['protected_boundary_waived']);self.assertEqual(receipts[-1]['proc_frames'][0]['state'],'R')
 def test_persistent_present_refused(self):
  with self.assertRaisesRegex(ValueError,'timeout|consecutive'):self.run_case([FIRST]*101)
 def test_start_tick_reuse_refused(self):
  v=copy.deepcopy(FIRST);v['start_ticks']+=1
  with self.assertRaises(ValueError):self.run_case([v])
 def test_foreign_cgroup_refused(self):
  v=copy.deepcopy(FIRST);v['cgroup']='1:memory:/foreign\n'
  with self.assertRaises(ValueError):self.run_case([v])
 def test_live_nonempty_root_refused(self):
  v=copy.deepcopy(FIRST);v['proc_fields']['cmdline']['bytes']=12
  with self.assertRaises(ValueError):self.run_case(first=v)
 def test_partial_error_refused(self):
  for status in ('partial','error'):
   with self.assertRaises(ValueError):self.run_case([dict(status=status,pid=PID)])
 def test_protected_refused(self):
  with self.assertRaises(ValueError):self.run_case(forbidden=[PID])
 def test_unknown_parent_refused(self):
  with self.assertRaises(ValueError):self.run_case(parents=[])
 def test_init_refused(self):
  with self.assertRaises(ValueError):G.confirm(INIT,PPID,INIT,set(),{PPID},FIRST,None,None,lambda x:None)
 def test_fresh_top_present_refused(self):
  with self.assertRaises(ValueError):self.run_case(top=[PID])
 def test_final_reappearance_refused(self):
  miss=dict(status='missing',pid=PID)
  with self.assertRaises(ValueError):self.run_case([miss,miss,FIRST])
 def test_missing_then_present_refused(self):
  with self.assertRaises(ValueError):self.run_case([dict(status='missing',pid=PID),FIRST])
 def test_deadline_never_extended(self):
  with self.assertRaises(ValueError):self.run_case([FIRST]*101,deadline=.03)
 def test_complete_tree_unknown_cycle_refused(self):
  for ppids in ({INIT:1,PID:999},{INIT:1,PID:PPID,PPID:PID}):
   with self.assertRaises(ValueError):G.tree_order(list(ppids),ppids,INIT)
def run_controls():
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(Controls);n=suite.countTestCases();result=unittest.TextTestRunner(verbosity=2).run(suite)
 if not result.wasSuccessful():raise ValueError('actual092 guard controls failed')
 return n
if __name__=='__main__':run_controls()

import importlib.util,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('budget_under_test',P/'model_snapshot_budget.py');B=importlib.util.module_from_spec(s);s.loader.exec_module(B)
class Budget(unittest.TestCase):
 def args(self):
  closed=[dict(leaf='/p/n16',frozen_bytes=1*B.G),dict(leaf='/p/n160',frozen_bytes=9*B.G)]
  rows=[dict(leaf=x['leaf'],stage='numeric',budget_bytes=33*B.G)for x in closed]
  return closed,rows
 def test_capacity_closed_only(self):
  c,r=self.args();self.assertEqual(B.adjusted(16*B.G,76*B.G,c,r,0,0),52*B.G)
  self.assertEqual(B.adjusted(44*B.G,104*B.G,c,r,28*B.G,1*B.G),52*B.G)
 def test_one_combined_not_64(self):
  c,r=self.args()
  with self.assertRaisesRegex(ValueError,'one32'):B.adjusted(44*B.G,104*B.G,c,r,28*B.G,5*B.G)
 def test_wrong_role_not_closed(self):
  c,r=self.args();r[0]['stage']='cpu'
  with self.assertRaises(ValueError):B.adjusted(16*B.G,76*B.G,c,r,0,0)
 def test_partition_prevents_two_allowances(self):
  c,r=self.args()
  for payload,opt in((31*B.G,0),(0,3*B.G)):
   with self.assertRaisesRegex(ValueError,'partitions'):B.adjusted(47*B.G,107*B.G,c,r,payload,opt)
 def test_control_write_terminal_reserve(self):
  lease=B.Lease.__new__(B.Lease);lease.opt=Path('/opt/owned');lease.extra_opt=None;lease.terminal=False;lease.opt_bytes=lambda:B.OPT_CAP-B.TERMINAL_RESERVE
  with patch.object(B,'LEAF',Path('C:/not-an-actual-payload')):
   with self.assertRaises(ValueError):lease.prewrite(Path('/opt/owned/RESULT.json'),1)
   lease.terminal=True;lease.prewrite(Path('/opt/owned/RESULT.json'),1)
 def test_missing_phase(self):
  c,r=self.args()
  with self.assertRaises(ValueError):B.adjusted(16*B.G,76*B.G,c[:1],r,0,0)
 def test_failclosed_walk(self):
  with tempfile.TemporaryDirectory()as d:
   with patch.object(B.os,'scandir',side_effect=PermissionError('denied')):
    with self.assertRaises(PermissionError):B.scan(d)
 def test_alias_rejected(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'x').write_bytes(b'x')
   with patch.object(B.stat,'S_ISREG',return_value=False):
    with self.assertRaises(ValueError):B.scan(p)
if __name__=='__main__':unittest.main()

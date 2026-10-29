import unittest
from decimal import Decimal as D
from pathlib import Path
import tempfile
from host_audits import r44_pair_work_budget as w
class ScientificControls(unittest.TestCase):
 def test_decimal_epoch_precision(self):
  self.assertEqual(w.decimal("1793228659321281.125\t")-w.decimal("1793228659321281"),D(".125"))
 def test_nonfinite_negative(self):
  for x in ("NaN","Infinity","-Infinity"):
   with self.assertRaises(ValueError):w.decimal(x)
  with self.assertRaises(ValueError):w.span("1","-.1")
  with self.assertRaises(ValueError):w.decimal(True)
 def test_overlap_union(self):
  self.assertEqual(w.length([(D(0),D(4)),(D(2),D(6))]),D(6))
 def test_sync_coincidence_union_not_sum(self):
  self.assertEqual(w.intersection([(D(0),D(4)),(D(2),D(6))],[(D(3),D(5))]),D(2))
 def test_real_geometry_transposed_or_plain(self):
  self.assertEqual(w.matmul_flops("16392,5120;4096,5120","16392,4096"),2*16392*5120*4096)
  self.assertEqual(w.matmul_flops("2,3;3,4","2,4"),48)
 def test_official_quoted_shapes(self):
  self.assertEqual(w.matmul_flops('"16392,5120;4096,5120"','"16392,4096"'),2*16392*5120*4096)
 def test_unknown_geometry_not_invented(self):
  for a,b in (("2,3;5,7","2,4"),("2,3;4,3","3,4"),("1,2,3;1,3,4","1,2,4"),("2,-3;4,3","2,4")):self.assertIsNone(w.matmul_flops(a,b))
 def test_control_wait_not_compute_and_no_crossrank_sum(self):
  events=[{"ph":"M","pid":1,"name":"process_name","args":{"name":"Ascend Hardware"}},{"ph":"M","pid":2,"name":"process_name","args":{"name":"CANN"}},{"ph":"M","pid":3,"name":"process_name","args":{"name":"Overlap Analysis"}},
   {"ph":"X","pid":1,"name":"MatMul","ts":0,"dur":2},{"ph":"X","pid":1,"name":"EVENT_WAIT","ts":2,"dur":8},{"ph":"X","pid":1,"name":"unknown_kernel","ts":10,"dur":2},{"ph":"X","pid":2,"name":"aclrtSynchronizeStream","ts":1,"dur":10},{"ph":"X","pid":3,"name":"Computing","ts":0,"dur":99}]
  with tempfile.TemporaryDirectory()as d:
   p=Path(d)/"trace.json";p.write_text(w.json.dumps(events));r=w.trace_work(p)
  self.assertEqual(r["non_control_hardware_union_us"],"4");self.assertEqual(r["observed_non_control_gaps_us"],"8");self.assertEqual(r["sync_coincident_with_observed_gaps_us"],"8");self.assertEqual(r["all_hardware_union_us"],"12")
 def test_typed_exact_ids_and_fanout_retained(self):
  rows=[{"ph":"s","id":2**60+1,"cat":"a","name":"n"},{"ph":"f","id":2**60+1,"cat":"a","name":"n"},{"ph":"f","id":2**60+1,"cat":"a","name":"n"},{"ph":"f","id":str(2**60+1),"cat":"a","name":"n"}]
  r=w.layout.flow_summary(rows)["categories"]["a"];self.assertEqual(r["fan_out"],1);self.assertEqual(r["missing_start"],1);self.assertEqual(r["keys"],2)
if __name__=="__main__":unittest.main()

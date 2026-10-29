import unittest,tempfile,json
from pathlib import Path
from decimal import Decimal as D
from host_audits import r44_phase_gap as p
class PhaseControls(unittest.TestCase):
 def test_disjoint_conservation_nested_priority(self):
  r=p.gap_coverage([(D(0),D(10))],[(D(0),D(9))],[(D(1),D(6))],[(D(2),D(3))],[(D(5),D(8))])
  self.assertEqual(r,{"gdn_with_nested_guard_op_span":"1","gdn_other_recorded_scope":"4","other_registered_custom_op":"2","other_recorded_main_thread_scope":"2","no_recorded_main_thread_scope":"1"})
 def test_duplicate_spans_not_added(self):
  self.assertEqual(p.gap_coverage([(D(0),D(2)),(D(1),D(3))],[],[(D(0),D(3)),(D(0),D(3))],[],[]),{"gdn_other_recorded_scope":"3"})
 def test_boundary_zero_gap(self):
  self.assertEqual(p.gap_coverage([(D(1),D(1))],[],[],[],[]),{})
 def test_anchor_count_and_order(self):
  self.assertEqual(p.forward_windows([{"ts":"2"},{"ts":"1"}],D(3)),[(D(1),D(2)),(D(2),D(3))])
  with self.assertRaises(ValueError):p.forward_windows([{"ts":1}],D(3))
  with self.assertRaises(ValueError):p.forward_windows([{"ts":1},{"ts":1}],D(3))
 def test_csv_hardware_exact_id_epoch(self):
  row={"Name":"aclnnEmbedding_GatherV2","Type":"GatherV2","Task ID":str(2**60+1),"Stream ID":"2","Start Time(us)":"1793228659321281.125\t","Output Shapes":'"40960,5120"'}
  key,rows=p.csv_embedding(row,D("1793228659321281"))
  event={"name":row["Name"],"ts":D(".125"),"args":{"Task Id":2**60+1,"Physic Stream Id":2}}
  self.assertEqual(key,p.hardware_key(event));self.assertEqual(rows,40960)
 def test_unknown_shape_not_labeled_embedding(self):
  with self.assertRaises(ValueError):p.csv_embedding({"Type":"GatherV2","Output Shapes":'"40960,13"'},D(0))
 def test_worker_row_conservation_and_layers(self):
  events=[{"event":"compact_model_rows_completed","rank":0,"step":2054,"original_rows":40960,"retained_rows":24584,"request_ids":["a","b","c"]}]
  for q,n,kind in(("a",1,"mixed_native_gdn_completed"),("b",16392,"compact_gdn_body_composed"),("c",8191,"mixed_native_gdn_completed")):
   events.extend({"event":kind,"rank":0,"step":2054,"request_id":q,"retained_rows":n,"layer":str(i)}for i in range(48))
  with tempfile.TemporaryDirectory()as d:
   f=Path(d)/"worker.jsonl";f.write_text("\n".join(json.dumps(e)for e in events))
   out=p.worker_steps(f,p.layout.sha(f),0,[2054]);self.assertEqual(out["selected_steps"][2054]["request_layers"]["a"]["retained_rows"],1)
   events.pop();f.write_text("\n".join(json.dumps(e)for e in events))
   with self.assertRaises(ValueError):p.worker_steps(f,p.layout.sha(f),0,[2054])
if __name__=="__main__":unittest.main()

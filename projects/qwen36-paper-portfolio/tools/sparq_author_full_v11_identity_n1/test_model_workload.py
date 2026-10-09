"""Stdlib only. Workload plan/source link is not runtime coverage."""
import unittest
import model_workload as m
class Plan(unittest.TestCase):
 def test_whole_batch_cohorts(self):
  cells=m.cohorts();self.assertEqual(len(cells),47);self.assertEqual(m.count(),407)
  self.assertEqual({b for b,k in cells if k=="initial"},set(range(1,17)))
  self.assertEqual({b for b,k in cells if k=="reuse"},set(range(1,17)))
  self.assertEqual({b for b,k in cells if k=="mixed"},set(range(2,17)))
 def test_observed_response_id_not_guessed_base(self):
  state=dict(actual_engine_request_id="observed-post-assign-ID",assignment_ref={"path":"actual-callback"},assignment_frontend_ref={"path":"frontend"})
  self.assertEqual(m.engine_id(state),"observed-post-assign-ID")
  with self.assertRaises(ValueError):m.engine_id("cmpl-observed-real-id")
 def test_missing_response_id_rejected(self):
  with self.assertRaises(ValueError):m.engine_id(None)
if __name__=="__main__":unittest.main()

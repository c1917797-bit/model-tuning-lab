import unittest
from independent_quality_schedule import quality_schedule
class QualityScheduleTests(unittest.TestCase):
    def rows(self):
        return [{"index":i,"sample_id":str(i),"segment":{"tokens_sha256":str(i//2)}} for i in range(127)]
    def test_full_denominator_and_shared_material(self):
        units=quality_schedule(self.rows())
        self.assertEqual(sum(u["scored_requests"] for u in units),381)
        for repetition in range(1,4):
            self.assertEqual([i for u in units if u["repetition"]==repetition for i in u["sample_indexes"]],list(range(127)))
        self.assertEqual(len(units[0]["producer_digests"]),5)
    def test_missing_sample_and_unbounded_batch_rejected(self):
        with self.assertRaises(ValueError):quality_schedule(self.rows()[:-1])
        with self.assertRaises(ValueError):quality_schedule(self.rows(),batch_samples=0)
if __name__=="__main__":unittest.main()

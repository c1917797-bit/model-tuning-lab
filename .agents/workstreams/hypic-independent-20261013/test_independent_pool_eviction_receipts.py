import unittest,torch
from independent_public_pool import PublicPool
class EvictionReceiptTests(unittest.TestCase):
    def test_actual_evicted_generation_only(self):
        receipts=[];pool=PublicPool(16,on_eviction=receipts.append)
        first=pool.publish("A",{"x":torch.ones(4)})
        second=pool.publish("B",{"x":torch.ones(4)})
        self.assertEqual(receipts,[{"key":"A","generation":first,"size_bytes":16}])
        self.assertNotIn("A",pool.entries);self.assertEqual(pool.entries["B"]["generation"],second)
    def test_pinned_failure_has_no_false_eviction(self):
        receipts=[];pool=PublicPool(16,on_eviction=receipts.append)
        pool.publish("A",{"x":torch.ones(4)})
        with pool.acquire_private("A"):
            with self.assertRaises(BufferError):pool.publish("B",{"x":torch.ones(4)})
        self.assertEqual(receipts,[]);self.assertIn("A",pool.entries)
if __name__=="__main__":unittest.main()

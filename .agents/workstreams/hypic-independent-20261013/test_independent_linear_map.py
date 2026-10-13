import unittest
from independent_request_map import freeze_request_slices
from independent_linear_map import freeze_prefill_linear_slices
class LinearMapTests(unittest.TestCase):
    def reqs(self):
        return freeze_request_slices(['a','b'],[0,128],[4,3],[0,4,7],rank=1,step=3)
    def test_association(self):
        out=freeze_prefill_linear_slices(self.reqs(),[0,4,7],[2,5],[False,True],state_capacity=8)
        self.assertEqual([(x.request_id,x.state_slot) for x in out],[('a',2),('b',5)])
    def test_alias_rejected(self):
        with self.assertRaises(ValueError):
            freeze_prefill_linear_slices(self.reqs(),[0,4,7],[2,2],[False,True],state_capacity=8)
    def test_wrong_order_rejected(self):
        with self.assertRaises(ValueError):
            freeze_prefill_linear_slices(self.reqs(),[0,3,7],[2,5],[False,True],state_capacity=8)
    def test_initial_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            freeze_prefill_linear_slices(self.reqs(),[0,4,7],[2,5],[False,False],state_capacity=8)
    def test_spec_rejected(self):
        with self.assertRaises(ValueError):
            freeze_prefill_linear_slices(self.reqs(),[0,4,7],[2,5],[False,True],state_capacity=8,speculative=True)
if __name__=='__main__':unittest.main()

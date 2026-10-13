import unittest
from independent_request_map import freeze_request_slices
class RequestMapTests(unittest.TestCase):
    def test_snapshot_survives_async_list_mutation(self):
        ids=['a','b'];computed=[0,12];scheduled=[8,1]
        out=freeze_request_slices(ids,computed,scheduled,[0,8,9],rank=2,step=4)
        ids.reverse();computed[0]=99
        self.assertEqual(out[0].request_id,'a');self.assertEqual(out[0].computed_tokens,0)
        self.assertEqual((out[1].token_start,out[1].token_end),(8,9))
    def test_duplicate_or_wrong_boundary_rejected(self):
        for ids,starts in [(['a','a'],[0,8,9]),(['a','b'],[0,7,9])]:
            with self.assertRaises(ValueError):freeze_request_slices(ids,[0,12],[8,1],starts,rank=0,step=1)
if __name__=='__main__':unittest.main()

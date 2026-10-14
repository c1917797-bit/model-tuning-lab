import unittest
import torch
from independent_request_map import RequestSlice
from independent_segment_selection import SegmentSelection
from independent_c2_query_plan import plan_c2_queries
from independent_compact_rows import compact_decoder_rows


class CompactRowsTests(unittest.TestCase):
    def fixture(self):
        plans=[]
        for row in range(2):
            req=RequestSlice(str(row),1,3,0,12,row,12*row,12*(row+1))
            plans.append(plan_c2_queries(req,SegmentSelection(2,10,False,'x'),seam_tokens=3,public_length=8))
        return plans

    def test_two_requests_preserve_hidden_residual_and_position_correspondence(self):
        hidden=torch.arange(72).reshape(24,3).float();residual=-hidden
        positions=torch.arange(12).repeat(2)
        plans=self.fixture();h,r,p,spans=compact_decoder_rows(hidden,residual,positions,plans)
        rows=list(plans[0].packed_rows()+plans[1].packed_rows())
        torch.testing.assert_close(h,hidden[rows]);torch.testing.assert_close(r,-h)
        self.assertEqual(p.tolist(),positions[rows].tolist())
        self.assertEqual(spans,((0,7),(7,14)))
        h.zero_();self.assertEqual(float(hidden[-1,-1]),71.)

    def test_multimodal_or_wrong_batch_positions_rejected(self):
        hidden=torch.zeros(24,3);positions=torch.arange(12).repeat(2)
        positions[13]=99
        with self.assertRaises(ValueError):
            compact_decoder_rows(hidden,None,positions,self.fixture())
        with self.assertRaises(ValueError):
            compact_decoder_rows(hidden,None,torch.arange(12).repeat(2),tuple(reversed(self.fixture())))


if __name__=='__main__':unittest.main()

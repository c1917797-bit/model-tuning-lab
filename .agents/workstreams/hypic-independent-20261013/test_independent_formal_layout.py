import unittest
from independent_formal_layout import formal_layout
from independent_request_map import RequestSlice
from independent_segment_selection import SegmentSelection
from independent_mixed_query_plan import plan_mixed_queries, NativeQueryPlan

class FormalLayoutTests(unittest.TestCase):
    def test_full_40_denominator_and_pdc_endpoints(self):
        seen=set()
        for index in range(40):
            x=formal_layout(index);seen.add(x.bridge)
            self.assertEqual(x.native_prefix+x.bridge+16384+x.tail,32768)
            self.assertEqual(x.pic_start,8192+x.bridge)
            for rank in range(4):
                req=RequestSlice(str(index),rank,1,8192,24576,0,0,24576)
                seg=SegmentSelection(x.pic_start,x.pic_end,False,"frozen")
                p=plan_mixed_queries([req],{str(index):seg},{str(index)},seam_tokens=8,public_length=16384)[0]
                self.assertNotIsInstance(p,NativeQueryPlan)
                self.assertEqual(p.skipped_tokens,16376)
        self.assertEqual(seen,set(range(1024,7169,512)))
    def test_invalid_index(self):
        for index in (-1,True,1.0,"0"):
            with self.assertRaises(ValueError):formal_layout(index)

if __name__=="__main__":unittest.main()

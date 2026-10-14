import unittest
from dataclasses import replace
from independent_request_map import RequestSlice
from independent_segment_selection import SegmentSelection
from independent_c2_query_plan import plan_c2_queries


class QueryPlanTests(unittest.TestCase):
    def test_formal_shape_retains_causal_endpoints(self):
        req=RequestSlice('r',2,7,0,32768,0,0,32768)
        seg=SegmentSelection(4096,20480,False,'frozen')
        p=plan_c2_queries(req,seg,seam_tokens=8,public_length=16384)
        self.assertEqual(p.skipped_tokens,16376)
        self.assertEqual(len(p.retained_offsets),16392)
        self.assertEqual(p.windows[0].kv_end,4104)
        self.assertEqual(p.windows[1].kv_end,32768)
        for w in p.windows:
            endpoints=range(w.kv_end-(w.query_end-w.query_start),w.kv_end)
            self.assertEqual(tuple(endpoints),tuple(range(w.query_start,w.query_end)))

    def test_pdc_prefix_keeps_logical_positions_and_batch_rows(self):
        req=RequestSlice('r',3,9,1024,32,1,100,132)
        seg=SegmentSelection(1030,1046,False,'frozen')
        p=plan_c2_queries(req,seg,seam_tokens=8,public_length=16)
        self.assertEqual(p.absolute_positions(),tuple(range(1024,1038))+tuple(range(1046,1056)))
        self.assertEqual(p.packed_rows(),tuple(range(100,114))+tuple(range(122,132)))

    def test_no_suffix_has_only_one_window(self):
        req=RequestSlice('r',0,1,0,20,0,0,20)
        p=plan_c2_queries(req,SegmentSelection(4,20,False,'x'),seam_tokens=8,public_length=16)
        self.assertEqual(len(p.windows),1)
        self.assertEqual(p.windows[0].kv_end,12)

    def test_partial_body_and_overlapping_pdc_rejected(self):
        req=RequestSlice('r',0,1,0,20,0,0,20)
        seg=SegmentSelection(4,20,False,'x')
        for bad in (replace(req,scheduled_tokens=19,token_end=19),
                    replace(req,computed_tokens=5)):
            with self.assertRaises(ValueError):
                plan_c2_queries(bad,seg,seam_tokens=8,public_length=16)

    def test_identity_and_empty_seam_rejected(self):
        req=RequestSlice('r',0,1,0,20,0,0,20)
        seg=SegmentSelection(4,20,False,'x')
        for seam in (0,16,True):
            with self.assertRaises(ValueError):
                plan_c2_queries(req,seg,seam_tokens=seam,public_length=16)
        with self.assertRaises(ValueError):
            plan_c2_queries(replace(req,token_end=21),seg,seam_tokens=8,public_length=16)


if __name__=='__main__': unittest.main()

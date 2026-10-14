"""Formal-scale PDC/PIC admission controls, not device activation evidence."""
import unittest
from independent_request_map import RequestSlice
from independent_segment_selection import SegmentSelection
from independent_mixed_query_plan import NativeQueryPlan, plan_mixed_queries

class FormalPDCCoexistence(unittest.TestCase):
    def test_hit_before_segment_allows_pic_with_absolute_endpoints(self):
        for rank in range(4):
            for offset in (1024,4096,7168):
                computed=offset
                req=RequestSlice("r",rank,1,computed,32768-computed,0,0,32768-computed)
                seg=SegmentSelection(offset,offset+16384,False,"frozen")
                p=plan_mixed_queries([req],{"r":seg},{"r"},seam_tokens=8,public_length=16384)[0]
                self.assertNotIsInstance(p,NativeQueryPlan)
                self.assertEqual(p.skipped_tokens,16376)
                for w in p.windows:
                    self.assertEqual(w.kv_end-(w.query_end-w.query_start),computed+w.query_start)
    def test_8192_actual_hit_overlapping_relocations_is_native_not_hot(self):
        for rank in range(4):
            for offset in (1024,4096,7168):
                req=RequestSlice("r",rank,1,8192,24576,0,0,24576)
                seg=SegmentSelection(offset,offset+16384,False,"frozen")
                p=plan_mixed_queries([req],{"r":seg},{"r"},seam_tokens=8,public_length=16384)[0]
                self.assertIsInstance(p,NativeQueryPlan)
                self.assertEqual(p.reason,"pdc-overlap")
                self.assertEqual(p.skipped_tokens,0)
                self.assertEqual(p.absolute_positions(),tuple(range(8192,32768)))

if __name__=="__main__":unittest.main()

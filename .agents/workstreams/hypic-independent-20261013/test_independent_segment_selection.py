import unittest
from independent_segment_selection import select_segment,require_full_scheduled_segment
from independent_request_map import freeze_request_slices
class SegmentSelectionTests(unittest.TestCase):
    def test_canonical_exact(self):
        self.assertTrue(select_segment([1,2,3],[1,2,3],canonical_public=True).public)
        with self.assertRaises(ValueError):select_segment([0,1,2,3],[1,2,3],canonical_public=True)
    def test_relocation(self):
        a=select_segment([9,1,2,3,8],[1,2,3])
        b=select_segment([9,8,1,2,3,7],[1,2,3])
        self.assertEqual((a.start,b.start),(1,2))
        self.assertEqual(a.tokens_sha256,b.tokens_sha256)
    def test_ambiguous_and_missing(self):
        for prompt in ([1,2,1,2],[3,4]):
            with self.assertRaises(ValueError):select_segment(prompt,[1,2])
    def test_prefix_overlap_and_partial_rejected(self):
        s=select_segment([9,1,2,3,8],[1,2,3])
        for computed,scheduled in [(2,3),(0,3)]:
            r=freeze_request_slices(['a'],[computed],[scheduled],[0,scheduled],rank=0,step=1)[0]
            with self.assertRaises(ValueError):require_full_scheduled_segment(s,r)
        r=freeze_request_slices(['a'],[0],[5],[0,5],rank=0,step=1)[0]
        self.assertEqual(require_full_scheduled_segment(s,r),(1,4))
if __name__=='__main__':unittest.main()

import unittest
from dataclasses import replace
from independent_request_map import RequestSlice
from independent_segment_selection import SegmentSelection
from independent_mixed_query_plan import plan_mixed_queries,NativeQueryPlan


class MixedPlanTests(unittest.TestCase):
    def batch(self):
        return (RequestSlice('decode',0,9,100,1,0,0,1),
                RequestSlice('hot',0,9,0,32,1,1,33),
                RequestSlice('chunk',0,9,0,8,2,33,41))
    def test_hot_decode_partial_share_exact_packed_rows(self):
        ps=plan_mixed_queries(self.batch(),
            {'hot':SegmentSelection(8,24,False,'h'),
             'chunk':SegmentSelection(4,20,False,'c')},
            {'hot','chunk'},seam_tokens=8,public_length=16)
        self.assertEqual([p.skipped_tokens for p in ps],[0,8,0])
        self.assertEqual([ps[0].reason,ps[2].reason],['decode','partial-body'])
        rows=tuple(x for p in ps for x in p.packed_rows())
        self.assertEqual(rows,tuple(range(17))+tuple(range(25,41)))
        self.assertEqual(len(rows),len(set(rows)))
    def test_cold_material_preserves_all_rows(self):
        ps=plan_mixed_queries(self.batch(),
            {'hot':SegmentSelection(8,24,False,'h')},set(),
            seam_tokens=8,public_length=16)
        self.assertTrue(all(isinstance(p,NativeQueryPlan) for p in ps))
        self.assertEqual(ps[1].reason,'cold-material')
        self.assertEqual(tuple(x for p in ps for x in p.packed_rows()),tuple(range(41)))
    def test_pdc_before_segment_can_prune_but_overlap_stays_native(self):
        req=RequestSlice('r',2,4,4,28,0,0,28)
        seg=SegmentSelection(8,24,False,'x')
        p=plan_mixed_queries((req,),{'r':seg},{'r'},seam_tokens=8,public_length=16)[0]
        self.assertEqual(p.skipped_tokens,8)
        p=plan_mixed_queries((replace(req,computed_tokens=9),),
            {'r':seg},{'r'},seam_tokens=8,public_length=16)[0]
        self.assertEqual((p.skipped_tokens,p.reason),(0,'pdc-overlap'))
    def test_wrong_step_alias_and_extra_identity_fail(self):
        reqs=self.batch()
        for bad in ((reqs[0],replace(reqs[1],step=10),reqs[2]),
                    (reqs[0],replace(reqs[1],token_start=0),reqs[2]),
                    (reqs[0],replace(reqs[1],request_id='decode'),reqs[2])):
            with self.assertRaises(ValueError):
                plan_mixed_queries(bad,{},set(),seam_tokens=8,public_length=16)
        with self.assertRaises(ValueError):
            plan_mixed_queries(reqs,{}, {'foreign'},seam_tokens=8,public_length=16)


if __name__=='__main__': unittest.main()

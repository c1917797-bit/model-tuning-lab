import unittest
from dataclasses import replace
from independent_request_map import RequestSlice
from independent_cache_map import CacheSlice
from independent_segment_selection import SegmentSelection
from independent_c2_query_plan import plan_c2_queries
from independent_c2_cache_binding import bind_c2_cache


class CacheBindingTests(unittest.TestCase):
    def fixture(self,computed=0):
        req=RequestSlice('r',1,4,computed,12,0,0,12)
        seg=SegmentSelection(computed+2,computed+10,False,'x')
        plan=plan_c2_queries(req,seg,seam_tokens=3,public_length=8)
        ids=(9,3,7,5)
        slots=tuple(ids[p//4]*4+p%4 for p in range(computed,computed+12))
        return plan,CacheSlice('r',1,4,2,0,4,ids,slots)

    def test_relocated_noncontiguous_blocks_keep_windows(self):
        p,c=self.fixture()
        b=bind_c2_cache(p,c,writable_slots=c.slots)
        self.assertEqual(b.body_slots,c.slots[5:10])
        self.assertEqual(b.windows[0].write_slots,c.slots[:5])
        self.assertEqual(b.windows[0].kv_end,5)
        self.assertEqual(b.windows[0].block_ids,(9,3))
        self.assertEqual(b.windows[1].kv_end,12)

    def test_pdc_partial_block_append_is_allowed(self):
        p,c=self.fixture(2)
        b=bind_c2_cache(p,c,writable_slots=c.slots)
        self.assertEqual(b.windows[0].logical_positions,tuple(range(2,7)))
        self.assertNotIn(36,b.body_slots)

    def test_read_association_without_lease_cannot_write(self):
        p,c=self.fixture()
        with self.assertRaises(ValueError):bind_c2_cache(p,c,writable_slots=())

    def test_rank_step_group_map_drift_rejected(self):
        p,c=self.fixture()
        for bad in (replace(c,rank=3),replace(c,step=5),
                    replace(c,slots=(0,)+c.slots[1:]),replace(c,group=-1)):
            with self.assertRaises(ValueError):bind_c2_cache(p,bad,writable_slots=c.slots)

    def test_shared_block_alias_cannot_be_licensed(self):
        p,c=self.fixture()
        ids=(9,9,7,5)
        slots=tuple(ids[i//4]*4+i%4 for i in range(12))
        bad=replace(c,block_ids=ids,slots=slots)
        with self.assertRaises(ValueError):bind_c2_cache(p,bad,writable_slots=slots)


if __name__=='__main__':unittest.main()

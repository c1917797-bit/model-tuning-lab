"""Executable host sand-table at formal token shapes; no device/quality claim."""
import unittest
from independent_request_map import RequestSlice
from independent_segment_selection import SegmentSelection
from independent_mixed_query_plan import plan_mixed_queries,NativeQueryPlan
from independent_cache_map import CacheSlice
from independent_c2_cache_binding import bind_c2_cache


class FormalMixedSandTable(unittest.TestCase):
    def test_four_rank_c16_pdc_chunk_and_relocation_matrix(self):
        for rank in range(4):
            for placement in (1024,4096,7168):
                for computed in (0,512,placement,placement+1):
                    requests=[];selections={};ready=set();cursor=0;expected=[]
                    for row in range(16):
                        rid=f'r{rank}-{row}'
                        if row<4:
                            count=1;prefix=100;mode='decode'
                        elif row%3==0:
                            count=32768-computed;prefix=computed;mode='hot'
                        elif row%3==1:
                            count=128;prefix=0;mode='chunk'
                        else:
                            count=32768-computed;prefix=computed;mode='cold'
                        req=RequestSlice(rid,rank,11,prefix,count,row,cursor,cursor+count)
                        requests.append(req)
                        if row>=4:
                            selections[rid]=SegmentSelection(placement,placement+16384,False,'frozen')
                            if mode!='cold':ready.add(rid)
                        can_skip=(mode=='hot' and prefix<=placement and
                                  prefix+count>=placement+16384)
                        omitted=set(range(cursor+placement+8-prefix,
                                          cursor+placement+16384-prefix)) if can_skip else set()
                        expected.extend(x for x in range(cursor,cursor+count) if x not in omitted)
                        cursor+=count
                    plans=plan_mixed_queries(requests,selections,ready,
                                              seam_tokens=8,public_length=16384)
                    actual=tuple(x for plan in plans for x in plan.packed_rows())
                    self.assertEqual(actual,tuple(expected))
                    self.assertEqual(len(actual),len(set(actual)))
                    self.assertTrue(all(req.token_end-1 in actual for req in requests))
                    for req,plan in zip(requests,plans):
                        self.assertEqual(plan.skipped_tokens,0 if isinstance(plan,NativeQueryPlan) else 16376)
                        for window in plan.windows:
                            n=window.query_end-window.query_start
                            self.assertEqual(window.kv_end-n,req.computed_tokens+window.query_start)
    def test_formal_native_and_hot_cache_windows_do_not_write_pdc_prefix(self):
        reqs=(RequestSlice('d',0,4,2048,1,0,0,1),
              RequestSlice('h',0,4,1024,31744,1,1,31745))
        plans=plan_mixed_queries(reqs,{'h':SegmentSelection(4096,20480,False,'f')},
                                {'h'},seam_tokens=8,public_length=16384)
        for i,(req,plan) in enumerate(zip(reqs,plans)):
            block_size=128;end=req.computed_tokens+req.scheduled_tokens
            ids=tuple(range(1000+i*400,1000+i*400+(end+127)//128))
            slots=tuple(ids[x//128]*128+x%128 for x in range(req.computed_tokens,end))
            cache=CacheSlice(req.request_id,req.rank,req.step,0,i,128,ids,slots)
            bound=bind_c2_cache(plan,cache,writable_slots=slots)
            prefix={ids[x//128]*128+x%128 for x in range(req.computed_tokens)}
            writes=set(bound.body_slots)
            for window in bound.windows:writes.update(window.write_slots)
            self.assertTrue(writes.isdisjoint(prefix))
            self.assertEqual(writes,set(slots))
            self.assertEqual(len(bound.body_slots),plan.skipped_tokens)
            with self.assertRaises(ValueError):bind_c2_cache(plan,cache,writable_slots=slots[:-1])

if __name__=='__main__':unittest.main()

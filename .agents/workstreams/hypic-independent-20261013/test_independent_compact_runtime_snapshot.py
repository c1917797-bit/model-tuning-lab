import unittest
from dataclasses import replace
from independent_request_map import RequestSlice
from independent_cache_map import CacheSlice
from independent_compact_runtime_snapshot import freeze_compact_runtime


class SnapshotTests(unittest.TestCase):
    def fixture(self):
        requests=(RequestSlice('a',0,3,2,2,0,0,2),RequestSlice('b',0,3,2,2,1,2,4))
        caches=(CacheSlice('a',0,3,0,0,2,(1,3),(6,7)),
                CacheSlice('b',0,3,0,1,2,(1,4),(8,9)))
        return requests,caches
    def test_shared_readonly_prefix_and_unique_new_writes(self):
        r,c=self.fixture()
        s=freeze_compact_runtime(r,c,((0,('layer',)),),(1,3),prompt_logprobs=False)
        self.assertEqual(s.writable_kv_slots,(('a',0,(6,7)),('b',0,(8,9))))
    def test_cross_request_write_into_other_prefix_rejected(self):
        r,c=self.fixture()
        bad=(c[0],replace(c[1],slots=(2,3)))
        with self.assertRaises(ValueError):
            freeze_compact_runtime(r,bad,((0,('layer',)),),(1,3),prompt_logprobs=False)
    def test_sampler_and_step_drift_rejected(self):
        r,c=self.fixture()
        with self.assertRaises(ValueError):
            freeze_compact_runtime(r,c,((0,('layer',)),),(0,3),prompt_logprobs=False)
        with self.assertRaises(ValueError):
            freeze_compact_runtime(r,(c[0],replace(c[1],step=4)),((0,('layer',)),),(1,3),prompt_logprobs=False)


if __name__=='__main__':unittest.main()

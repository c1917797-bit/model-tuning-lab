import random,unittest
from independent_segment_selection import select_segment,token_digest
from independent_segment_catalog import SegmentCatalog
class CatalogTests(unittest.TestCase):
    def test_distinct_digest_routes_and_ambiguity(self):
        a=tuple(range(16));b=tuple(range(100,120))
        c=SegmentCatalog([a,b])
        s=c.select_one((99,)+b+(999,))
        self.assertEqual(c.tokens(s.tokens_sha256),b)
        with self.assertRaises(ValueError):c.select_one(a+(99,)+b)
        with self.assertRaises(ValueError):c.select_one(a+(99,)+a+(99,)+b)
        with self.assertRaises(ValueError):SegmentCatalog([a,a])
    def test_exact_match_against_small_dense_oracle(self):
        rng=random.Random(0)
        for _ in range(200):
            p=tuple(rng.randrange(3) for i in range(30));b=tuple(rng.randrange(3) for i in range(5))
            matches=[i for i in range(26) if p[i:i+5]==b]
            if len(matches)==1:self.assertEqual(select_segment(p,b).start,matches[0])
            else:
                with self.assertRaises(ValueError):select_segment(p,b)
    def test_overlapping_repetitions_rejected(self):
        with self.assertRaises(ValueError):select_segment((1,)*20,(1,)*16)
if __name__=="__main__":unittest.main()

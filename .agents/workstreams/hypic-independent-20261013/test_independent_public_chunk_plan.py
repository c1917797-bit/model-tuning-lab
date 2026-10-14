import unittest
from independent_public_chunk_plan import public_chunk,ProducerCoverage
class PublicChunkTests(unittest.TestCase):
    def test_actual15360_1280_public_tail_geometry(self):
        a=public_chunk(0,15360,16384);b=public_chunk(15360,1280,16384)
        self.assertEqual((a.body_start,a.body_end),(8,15360))
        self.assertEqual((b.body_start,b.body_end),(0,1024))
        self.assertEqual((b.conv_tail_start,b.conv_tail_end),(1021,1024))
        self.assertEqual((a.body_end-a.body_start)+(b.body_end-b.body_start),16376)
        coverage=ProducerCoverage("request","identity")
        self.assertFalse(coverage.accept("request","identity",a))
        self.assertTrue(coverage.accept("request","identity",b))
        with self.assertRaises(ValueError):coverage.accept("request","identity",b)
    def test_gap_and_wrong_producer_rejected(self):
        coverage=ProducerCoverage("r","i")
        with self.assertRaises(ValueError):coverage.accept("r","i",public_chunk(64,64,1024))
        with self.assertRaises(ValueError):coverage.accept("other","i",public_chunk(0,64,1024))
    def test_seam_spans_early_chunk(self):
        a=public_chunk(0,4,64);b=public_chunk(4,60,64)
        self.assertEqual(a.body_end-a.body_start,0)
        self.assertEqual((b.body_start,b.body_end),(4,60))
if __name__=="__main__":unittest.main()

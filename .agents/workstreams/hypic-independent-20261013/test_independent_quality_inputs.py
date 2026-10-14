import unittest
from independent_quality_inputs import context_segment,quality_generation
class QualityInputTests(unittest.TestCase):
    def test_exact_context_rows_and_trim(self):
        ids=list(range(40));offsets=[(i,i+1) for i in range(40)]
        selection,segment=context_segment(ids,offsets,3,38,max_tokens=32)
        self.assertEqual((selection["start"],selection["end"]),(3,35))
        self.assertEqual(segment,tuple(ids[3:35]))
    def test_short_and_offset_mismatch_rejected(self):
        with self.assertRaises(ValueError):context_segment([1],[(0,1)],0,1)
        with self.assertRaises(ValueError):context_segment([1,2],[(0,1)],0,1)
    def test_mode_rulers(self):
        self.assertEqual(quality_generation()["max_tokens"],1024)
        self.assertEqual(quality_generation(True)["max_tokens"],2048)
        self.assertFalse(quality_generation()["ignore_eos"])
        with self.assertRaises(ValueError):quality_generation(1)
if __name__=="__main__":unittest.main()

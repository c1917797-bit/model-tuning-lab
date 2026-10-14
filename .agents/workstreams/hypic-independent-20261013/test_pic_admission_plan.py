import unittest
from independent_pic_admission_plan import cap_pic_chunk

class PICAdmission(unittest.TestCase):
    def plan(self,c,n,a=9216,b=25600,ready=True):
        return cap_pic_chunk(computed=c,proposed=n,prompt_tokens=32768,segment_start=a,segment_end=b,ready=ready)
    def test_actual_failed_geometry(self):
        self.assertEqual(self.plan(0,16381),9216)
        self.assertEqual(self.plan(0,24570,a=15360,b=31744),15360)
        self.assertEqual(self.plan(9216,16384),0)
        self.assertEqual(self.plan(9216,16385),16385)
    def test_full40_c16_sandtable(self):
        # Planning only; not real c16 execution or scheduler integration.
        for index in range(40):
            start=9216+(index%7)*1024;end=start+16384;computed=0
            for budget in (8191,16381,24570,40960):
                n=self.plan(computed,budget,start,end)
                self.assertFalse(computed<end and computed+n>start and computed+n<end+1)
                computed+=n
                if computed>=end+1:break
            self.assertGreaterEqual(computed,end+1)
    def test_cold_and_finished_native(self):
        self.assertEqual(self.plan(0,16381,ready=False),16381)
        self.assertEqual(self.plan(30000,1000),1000)
    def test_no_fake_already_computed_skip(self):
        with self.assertRaises(ValueError):self.plan(16381,16387)
    def test_native1536_boundaries(self):
        for start in range(9216,15361,1024):
            n=cap_pic_chunk(computed=0,proposed=24576,prompt_tokens=32768,
                segment_start=start,segment_end=start+16384,ready=True,block_size=1536)
            self.assertLessEqual(n,start)
            self.assertEqual(n%1536,0)
            full=cap_pic_chunk(computed=n,proposed=32768-n,prompt_tokens=32768,
                segment_start=start,segment_end=start+16384,ready=True,block_size=1536)
            self.assertEqual(n+full,32768)
    def test_block_identity_rejected(self):
        with self.assertRaises(ValueError):
            cap_pic_chunk(computed=0,proposed=100,prompt_tokens=32768,
                segment_start=9216,segment_end=25600,ready=True,block_size=0)
if __name__=="__main__":unittest.main()

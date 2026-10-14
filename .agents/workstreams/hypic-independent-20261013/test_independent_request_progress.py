import unittest
from types import SimpleNamespace
from independent_request_progress import RequestProgressLedger
def req(computed,scheduled,step=1):
    return SimpleNamespace(request_id="r",rank=0,step=step,
                           computed_tokens=computed,scheduled_tokens=scheduled)
class ProgressTests(unittest.TestCase):
    def test_first_cached_prefix_vs_later_chunk(self):
        p=RequestProgressLedger()
        a=p.observe([req(0,4096)])[0]
        b=p.observe([req(4096,24576,2)])[0]
        self.assertTrue(a["first_observed"]);self.assertFalse(b["first_observed"])
        q=RequestProgressLedger().observe([req(8192,24576)])[0]
        self.assertTrue(q["first_observed"]);self.assertEqual(q["computed_tokens"],8192)
    def test_decode_not_flooding_receipts(self):
        p=RequestProgressLedger();p.observe([req(0,32768)])
        self.assertEqual(p.observe([req(32768,1,2)]),())
    def test_first_decode_still_recorded(self):
        self.assertTrue(RequestProgressLedger().observe([req(32768,1)])[0]["first_observed"])
if __name__=="__main__":unittest.main()

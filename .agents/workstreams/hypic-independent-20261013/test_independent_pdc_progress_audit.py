import unittest
from independent_pdc_progress_audit import audit_initial_prefix
class PDCProgressAuditTests(unittest.TestCase):
    def events(self):
        return [{"event":"native_request_progress","request_id":"r","rank":r,
                 "pid":100+r,"step":2,"first_observed":True,
                 "computed_tokens":8192,"scheduled_tokens":24576} for r in range(4)]
    def test_all_four_first_cached_progress(self):
        self.assertEqual(audit_initial_prefix(self.events(),"r",pic_start=9216)["ranks"],4)
    def test_later_chunk_not_pdc(self):
        e=self.events()
        for x in e:x["first_observed"]=False
        with self.assertRaises(ValueError):audit_initial_prefix(e,"r",pic_start=9216)
    def test_missing_rank_or_earlier_zero_prefix_rejected(self):
        with self.assertRaises(ValueError):audit_initial_prefix(self.events()[:-1],"r",pic_start=9216)
        e=self.events();e.append(dict(e[0],step=1,first_observed=False,computed_tokens=0))
        with self.assertRaises(ValueError):audit_initial_prefix(e,"r",pic_start=9216)
    def test_decode_or_overlap_not_accepted(self):
        for bad in (dict(computed_tokens=10000),dict(scheduled_tokens=1)):
            e=self.events();e[0].update(bad)
            with self.assertRaises(ValueError):audit_initial_prefix(e,"r",pic_start=9216)
if __name__=="__main__":unittest.main()

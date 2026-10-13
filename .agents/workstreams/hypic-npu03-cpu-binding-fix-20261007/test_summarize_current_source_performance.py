import copy
import math
import unittest
import summarize_current_source_performance as s

def fixture():
    values = {("no-cache","screen"):10,("no-cache","repeat2"):20,("no-cache","repeat3"):30,
              ("hypic-only","screen"):5,("hypic-only","repeat2"):15,("hypic-only","repeat3"):25}
    return [{"arm":a,"phase":p,"metrics":{k:values[(a,p)] for k in s.METRICS}}
            for a,p in s.ORDER]

class SummaryTests(unittest.TestCase):
    def test_values_mean_sd_median(self):
        r=s.summarize(fixture())["statistics"]["no-cache"]["tpot_weighted_ms"]
        self.assertEqual(r,{"values":[10,20,30],"mean":20,"sample_sd":10,
                            "median":20,"min":10,"max":30})
    def test_pairs_are_phase_matched_not_execution_adjacent(self):
        r=s.summarize(fixture())["paired_relative_change_pct"]
        self.assertEqual(r[0]["tpot_weighted_ms"],-50)
        self.assertEqual(r[1]["tpot_weighted_ms"],-25)
        self.assertAlmostEqual(r[2]["tpot_weighted_ms"],-100/6)
    def test_median_ratio_not_mean_ratio(self):
        r=s.summarize(fixture())
        self.assertEqual(r["median_relative_change_pct"]["tpot_weighted_ms"],-25)
        self.assertNotEqual(sum(x["tpot_weighted_ms"] for x in r["paired_relative_change_pct"])/3,-25)
    def test_missing_or_reordered_phase(self):
        for f in (fixture()[:-1],list(reversed(fixture()))):
            with self.assertRaises(ValueError):s.summarize(f)
    def test_invalid_metrics(self):
        for v in (0,-1,True,float("nan"),float("inf"),"10"):
            f=fixture();f[0]["metrics"]["tpot_weighted_ms"]=v
            with self.assertRaises(ValueError):s.summarize(f)

if __name__=="__main__":unittest.main()

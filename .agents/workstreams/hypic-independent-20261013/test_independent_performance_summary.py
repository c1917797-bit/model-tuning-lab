import unittest
from independent_performance_summary import summarize_phase,summarize_three_rounds,summarize_matched_groups
class PerformanceSummaryTests(unittest.TestCase):
    def records(self):
        return [{"index":i,"ok":True,"metrics":{"request_id":"r"+str(i),
          "completion_tokens":1024,"usage":{"prompt_tokens":32768},
          "finish_reason":"length","tpot_denominator":"completion_tokens",
          "ttft_ms":1000+i,"duration_ms":1000+i+1024*60,"tpot_ms":60.}} for i in range(40)]
    def test_three_round_protocol_not_speed_acceptance(self):
        r=summarize_three_rounds({i:self.records() for i in (1,2,3)})
        self.assertEqual(r["weighted_tpot_median_ms"],60.)
    def test_failed_or_missing_request_not_dropped(self):
        with self.assertRaises(ValueError):summarize_phase(self.records()[:-1])
        r=self.records();r[3]["ok"]=False
        with self.assertRaises(ValueError):summarize_phase(r)
    def test_duplicate_id_and_wrong_ruler_rejected(self):
        for field,value in (("request_id","r0"),("tpot_ms",61.),("completion_tokens",1000)):
            r=self.records();r[1]["metrics"][field]=value
            with self.assertRaises(ValueError):summarize_phase(r)
    def phases(self):
        identity={"image":"fixed","model_config_sha256":"model",
            "algorithm_manifest_sha256":"source","payload_digest":"inputs",
            "tp":4,"physical_npus":[0,1,2,3],"cpu_set":"112-191",
            "input_tokens":32768,"output_tokens":1024,"concurrency":16,
            "decode_graph":"NONE"}
        return {(g,r):{"identity":dict(identity),"pdc_enabled":g in ("G2","G4"),
                       "hypic_enabled":g in ("G3","G4"),"records":self.records()}
                for g in ("G1","G2","G3","G4") for r in (1,2,3)}
    def test_all12_matched_groups(self):
        self.assertEqual(len(summarize_matched_groups(self.phases())["groups"]),4)
    def test_source_drift_or_missing_round_rejected(self):
        p=self.phases();p[("G4",3)]["identity"]["payload_digest"]="other"
        with self.assertRaises(ValueError):summarize_matched_groups(p)
        p=self.phases();p.pop(("G1",2))
        with self.assertRaises(ValueError):summarize_matched_groups(p)
if __name__=="__main__":unittest.main()

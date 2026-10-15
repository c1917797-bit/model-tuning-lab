import unittest
from independent_quality_evidence_policy import QualityEvidencePolicy
class EvidencePolicyTests(unittest.TestCase):
    def test_default_full_unchanged(self):
        x={"event":"mixed_native_gdn_completed","request_id":"r"}
        self.assertEqual(QualityEvidencePolicy().select(x),x)
    def test_all381_hot_and_producer_material_retained(self):
        p=QualityEvidencePolicy("quality-hot")
        events=[]
        for i in range(381):
            for layer in range(48):events.append({"event":"compact_gdn_body_composed","request_id":str(i),"layer":str(layer)})
            for layer in range(16):events.append({"event":"compact_c2_queries_completed","request_id":str(i),"layer":str(layer)})
        for kind in ("compact_public_state_published","compact_public_kv_published","compact_public_material_evicted","native_request_progress","quality-scored-response","device_failure"):
            events.append({"event":kind})
        self.assertTrue(all(p.select(x) is not None for x in events))
        self.assertEqual(len(events),381*64+6)
    def test_explicit_omission_counts_no_silent_truncation(self):
        p=QualityEvidencePolicy("quality-hot")
        for i in range(10000):
            self.assertIsNone(p.select({"event":"mixed_native_gdn_completed"}))
        x=p.select({"event":"compact_gdn_body_composed"})
        self.assertEqual(x["omitted_nonhot_counts"],{"mixed_native_gdn_completed":10000})
        self.assertEqual(p.descriptor()["profile"],"quality-hot")
    def test_shadow_batch_and_matching_commits_preserved(self):
        p=QualityEvidencePolicy("quality-hot")
        c={"rank":0,"step":4,"layer":"layer"}
        shadow=dict(c,event="native_decode_batch_shadow_checked",requests=["a","b"],passed=False)
        self.assertIsNotNone(p.select(shadow)) # Failures must remain visible.
        self.assertIsNotNone(p.select(dict(c,event="native_decode_batch_completed",requests=["a","b"],slots=[2,5])))
        for rid,slot in (("a",2),("b",5)):
            self.assertIsNotNone(p.select(dict(c,event="mixed_native_gdn_completed",request_id=rid,slot=slot)))
        self.assertIsNone(p.select(dict(c,event="mixed_native_gdn_completed",request_id="other",slot=9)))
    def test_sampled_drift_fails_closed(self):
        p=QualityEvidencePolicy("quality-hot");c={"rank":0,"step":1,"layer":"l"}
        p.select(dict(c,event="native_decode_batch_shadow_checked",requests=["a"]))
        with self.assertRaises(ValueError):p.select(dict(c,event="native_decode_batch_completed",requests=["b"],slots=[0]))
        with self.assertRaises(ValueError):p.select(dict(c,event="mixed_native_gdn_completed",request_id="a",slot=0))
    def test_bounds_and_profile(self):
        with self.assertRaises(ValueError):QualityEvidencePolicy("silent-drop")
        p=QualityEvidencePolicy("quality-hot",max_shadow_groups=1)
        p.select({"event":"native_decode_batch_shadow_checked","rank":0,"step":1,"layer":"a","requests":["a"]})
        with self.assertRaises(ValueError):p.select({"event":"native_decode_batch_shadow_checked","rank":0,"step":1,"layer":"b","requests":["b"]})
if __name__=="__main__":unittest.main()

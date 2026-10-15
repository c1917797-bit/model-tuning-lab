import copy
import unittest
from audit_full40_hot_coverage import audit_full40_hot

class Full40(unittest.TestCase):
    def setUp(self):
        self.ids=["cmpl-"+str(i) for i in range(40)];self.events=[]
        for rank in range(4):
            base={"rank":rank,"pid":100+rank,"manifest_sha256":"f"}
            for kind,n in [("compact_public_state_published",48),("compact_public_kv_published",16)]:
                for i in range(n):self.events.append(dict(base,event=kind,layer=kind+str(i)))
            self.events.append(dict(base,event="compact_model_rows_completed",step=1,request_ids=[x+"-internal" for x in self.ids],original_rows=40*32768,retained_rows=40*16392))
            for rid in self.ids:
                rb=dict(base,request_id=rid+"-internal",step=1)
                self.events.append(dict(rb,event="native_request_progress",scheduled_tokens=32768))
                for kind,pub,field,n in [
                    ("compact_gdn_body_composed","compact_public_state_published","skipped_body_tokens",48),
                    ("compact_c2_queries_completed","compact_public_kv_published","skipped_body_queries",16)]:
                    for i in range(n):self.events.append(dict(rb,event=kind,layer=pub+str(i),retained_rows=16392,finite=True,**{field:16376}))
    def test_mixed_full_denominator(self):
        self.assertTrue(audit_full40_hot(self.events,self.ids,manifest_sha256="f")["accepted_hot_coverage"])
    def test_missing_layer_retains_denominator(self):
        e=self.events[:-1];r=audit_full40_hot(e,self.ids,manifest_sha256="f")
        self.assertFalse(r["accepted_hot_coverage"]);self.assertEqual(r["denominator"],40);self.assertIn(self.ids[-1],r["missing"])
    def test_reject_drift_and_wrong_skip(self):
        for field,value in [("manifest_sha256","wrong"),("skipped_body_queries",1),("retained_rows",1),("pid",999)]:
            e=copy.deepcopy(self.events);e[-1][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):audit_full40_hot(e,self.ids,manifest_sha256="f")
    def test_profile16_is_explicitly_separate(self):
        from audit_full40_hot_coverage import audit_profile16_hot
        result=audit_profile16_hot(self.events,self.ids[:16],manifest_sha256="f")
        self.assertTrue(result["accepted_hot_coverage"])
        self.assertEqual(result["denominator"],16)
        self.assertIn("never formal full40",result["scope"])
        with self.assertRaises(ValueError):audit_full40_hot(self.events,self.ids[:16],manifest_sha256="f")
    def test_profile16_missing_layer_not_hidden(self):
        from audit_full40_hot_coverage import audit_profile16_hot
        e=[x for x in self.events if not (x.get("request_id")==self.ids[15]+"-internal" and x.get("rank")==3 and x.get("event")=="compact_c2_queries_completed")]
        result=audit_profile16_hot(e,self.ids[:16],manifest_sha256="f")
        self.assertFalse(result["accepted_hot_coverage"])
        self.assertEqual(result["denominator"],16)
        self.assertIn(self.ids[15],result["missing"])
    def test_no_partial_denominator(self):
        with self.assertRaises(ValueError):audit_full40_hot(self.events,self.ids[:-1],manifest_sha256="f")
if __name__=="__main__":unittest.main()

import unittest
from audit_compact_mechanism import audit_mechanism


class MechanismAuditTests(unittest.TestCase):
    def fixture(self):
        a=dict(public_state_per_rank=48,public_kv_per_rank=16,private_requests=2,
               original_rows=80,model_retained_rows=24,skipped_body_rows=56)
        events=[]
        for rank in range(4):
            common=dict(rank=rank,pid=100+rank,manifest_sha256='frozen')
            for prefix,n,kind in [('l',48,'compact_public_state_published'),('f',16,'compact_public_kv_published')]:
                for layer in range(n):events.append(dict(common,event=kind,layer=prefix+str(layer)))
            for rid in ('a','b'):
                events.append(dict(common,event='compact_model_rows_completed',request_ids=[rid],step=2,
                                   original_rows=80,retained_rows=24))
                for prefix,n,kind in [('l',48,'compact_gdn_body_composed'),('f',16,'compact_c2_queries_completed')]:
                    for layer in range(n):events.append(dict(common,event=kind,request_id=rid,step=2,
                        layer=prefix+str(layer),retained_rows=24,skipped_body_tokens=56,
                        skipped_body_queries=56,finite=True))
        return events,a
    def test_complete_coverage_and_missing_single_layer(self):
        e,a=self.fixture();self.assertEqual(audit_mechanism(e,a,manifest_sha256='frozen')['requests'],['a','b'])
        with self.assertRaises(ValueError):audit_mechanism(e[:-1],a,manifest_sha256='frozen')
    def test_native_fallback_or_wrong_step_cannot_pass(self):
        e,a=self.fixture();e[-1]['skipped_body_queries']=0
        with self.assertRaises(ValueError):audit_mechanism(e,a,manifest_sha256='frozen')
        e,a=self.fixture();e[-1]['step']=3
        with self.assertRaises(ValueError):audit_mechanism(e,a,manifest_sha256='frozen')
    def test_duplicate_receipt_and_source_drift_rejected(self):
        e,a=self.fixture()
        with self.assertRaises(ValueError):audit_mechanism(e+[e[-1]],a,manifest_sha256='frozen')
        with self.assertRaises(ValueError):audit_mechanism(e,a,manifest_sha256='wrong')


if __name__=='__main__':unittest.main()

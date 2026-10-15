import unittest
from audit_c1_pdc_observed import audit_pdc_observed

class PdcObservedTests(unittest.TestCase):
    def fixture(self):
        m={f"a{i}":f"a{i}-0" for i in range(16)};w={r:r+50 for r in range(4)}
        starts={rid:9216 for rid in m.values()}
        rows=[dict(event="native_request_progress",request_id=rid,rank=r,pid=pid,
                   computed_tokens=7680,scheduled_tokens=1536,step=1,first_observed=True,
                   manifest_sha256="m") for rid in m.values() for r,pid in w.items()]
        caps=[dict(event="pic_scheduler_boundary_capped",request_id="a0-0",
                   native_block_size=1536,pic_start=9216,pic_end=25600,manifest_sha256="m")]
        return rows,caps,m,w,starts
    def test_conditional_absence_not_missing_hit(self):
        r=audit_pdc_observed(*self.fixture(),manifest_sha256="m")
        self.assertEqual(len(r["requests"]),16)
        self.assertEqual(r["requests_with_conditional_cap"],1)
    def test_missing_block(self):
        e,c,m,w,s=self.fixture()
        with self.assertRaises(ValueError):audit_pdc_observed(e,[],m,w,s,manifest_sha256="m")
    def test_no_hit_missing_rank_source(self):
        for change in ("hit","rank","source"):
            e,c,m,w,s=self.fixture()
            if change=="hit":e[0]["computed_tokens"]=0
            elif change=="rank":e.pop()
            else:e[0]["manifest_sha256"]="wrong"
            with self.assertRaises(ValueError):audit_pdc_observed(e,c,m,w,s,manifest_sha256="m")

    def test_bound_input_and_negative_controls(self):
        import hashlib,json
        from unittest.mock import patch
        from audit_c1_pdc_observed import bind_pic_starts
        e,c,m,w,s=self.fixture()
        tokens=[1]*8192+[3]*1024+[2]*16384+[4]*7168
        artifact={"native_prefix":[1]*8192,"public_segment":[2]*16384,
                  "requests":[{"index":i,"token_ids":tokens,"segment_start":9216,
                               "segment_end":25600} for i in range(16)]}
        data=json.dumps(artifact).encode();digest=hashlib.sha256(data).hexdigest()
        results=[{"index":i,"response":{"id":f"a{i}"}} for i in range(16)]
        with patch("pathlib.Path.read_bytes",return_value=data):
            self.assertEqual(bind_pic_starts("fixture",digest,results,m),s)
            with self.assertRaises(ValueError):bind_pic_starts("fixture","wrong",results,m)
            with self.assertRaises(ValueError):bind_pic_starts("fixture",digest,results[:-1],m)
            with self.assertRaises(ValueError):bind_pic_starts("fixture",digest,results,{})
        artifact["requests"][0]["segment_start"]=8192
        bad=json.dumps(artifact).encode()
        with patch("pathlib.Path.read_bytes",return_value=bad):
            with self.assertRaises(ValueError):
                bind_pic_starts("fixture",hashlib.sha256(bad).hexdigest(),results,m)
    def test_conflicting_block_geometry_mapping(self):
        for change in ("block","geometry","mapping"):
            e,c,m,w,s=self.fixture()
            if change=="block":c[0]["native_block_size"]=1
            elif change=="geometry":c[0]["pic_start"]=10240
            else:m.pop("a15")
            with self.assertRaises(ValueError):audit_pdc_observed(e,c,m,w,s,manifest_sha256="m")

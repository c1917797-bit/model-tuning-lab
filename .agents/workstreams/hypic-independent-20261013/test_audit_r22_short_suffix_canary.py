import copy,unittest
from audit_r22_short_suffix_canary import audit_routes
class RouteAuditTests(unittest.TestCase):
    def fixture(self):
        workers={i:50+i for i in range(4)};rows=[]
        for r,pid in workers.items():
            base=dict(rank=r,pid=pid,manifest_sha256="a"*64)
            rows.append(dict(base,event="compact_hypic_hooks_installed",c1_short_suffix_recurrent=True))
            b=dict(base,request_id="api-0-runtime",step=10,layer="layer0")
            rows.append(dict(b,event="c1_short_suffix_recurrent_route",rows=56,packed_start=3,packed_end=59,
                             source_start=15467,source_end=15523,window="suffix",
                             branch="independent_recurrent_le64",output_and_terminal=True,actual_slot_commit="not_started"))
            rows.append(dict(b,event="compact_gdn_body_composed"))
        return rows,workers
    def test_complete(self):
        e,w=self.fixture();r=audit_routes(e,w,"a"*64,target_api="api")
        self.assertEqual(r["covered_ranks"],list(range(4)));self.assertEqual(r["row_counts"],[56])
        self.assertEqual(r["failed_sample_short_route_ranks"],list(range(4)))
    def test_pid_only_install_joins_independently_verified_workers(self):
        e,w=self.fixture()
        for x in e:
            if x["event"]=="compact_hypic_hooks_installed":x.pop("rank")
        self.assertEqual(audit_routes(e,w,"a"*64)["covered_ranks"],list(range(4)))
    def test_missing_completion_and_rank_rejected(self):
        e,w=self.fixture()
        for x in (e[:-1],e[:-3]):
            with self.assertRaises(ValueError):audit_routes(x,w,"a"*64)
    def test_identity_and_geometry_controls(self):
        e,w=self.fixture()
        for k,v in (("pid",999),("manifest_sha256","b"*64),("rows",65),("rows",True),
                    ("output_and_terminal",False),("packed_end",60),("actual_slot_commit","done")):
            bad=copy.deepcopy(e);bad[1][k]=v
            with self.subTest(k=k,v=v),self.assertRaises(ValueError):audit_routes(bad,w,"a"*64)
    def test_order_and_duplicate_rejected(self):
        e,w=self.fixture()
        for bad in ([e[0],e[2],e[1]]+e[3:],e+[e[1]],e+[e[2]]):
            with self.assertRaises(ValueError):audit_routes(bad,w,"a"*64)
    def test_flag_absent_rejected(self):
        e,w=self.fixture();e[0].pop("c1_short_suffix_recurrent")
        with self.assertRaises(ValueError):audit_routes(e,w,"a"*64)
if __name__=="__main__":unittest.main()

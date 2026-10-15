import copy,unittest
from audit_c1_short_prefix import audit_prefix_routes
class PrefixRouteAuditTests(unittest.TestCase):
    def fixture(self):
        e=[dict(event="compact_hypic_hooks_installed",pid=10+i,manifest_sha256="a"*64,
            c1_packed_wave=True,c1_short_prefix_terminal_policy="canonical_recurrent_le64") for i in range(4)]
        common=dict(rank=0,pid=10,step=9,layer="layer",manifest_sha256="a"*64,actual_slot_commit="not_started")
        e.extend(dict(common,event="c1_prefix_terminal_route",policy="canonical_recurrent_le64",
            request_id=rid,job=j,window="prefix",source_start=0,source_end=n,
            packed_start=j*100,packed_end=j*100+n,rows=n,
            branch="independent_recurrent_le64" if n<=64 else "official_chunk64")
            for rid,j,n in (("r",0,8),("s",1,65)))
        e.append(dict(common,event="c1_packed_wave_shadow_checked",group_requests=["r","s"]))
        return e
    def test_mixed_branches(self):
        r=audit_prefix_routes(self.fixture(),manifest_sha256="a"*64)
        self.assertEqual((r["routes"],r["recurrent_routes"],r["chunk_routes"]),(2,1,1))
    def test_mutations(self):
        for mutate in (lambda e:e[4].update(branch="official_chunk64"),
            lambda e:e[4].update(source_end=9),lambda e:e[4].update(manifest_sha256="b"*64),
            lambda e:e[4].update(actual_slot_commit="completed"),lambda e:e.pop(4),
            lambda e:e.append(copy.deepcopy(e[4])),lambda e:e.pop(),
            lambda e:e[0].update(c1_short_prefix_terminal_policy="chunk64")):
            e=self.fixture();mutate(e)
            with self.assertRaises(ValueError):audit_prefix_routes(e,manifest_sha256="a"*64)
    def test_full_coverage_not_inferred(self):
        with self.assertRaises(ValueError):
            audit_prefix_routes(self.fixture(),manifest_sha256="a"*64,required_layers=["layer"])
if __name__=="__main__":unittest.main()

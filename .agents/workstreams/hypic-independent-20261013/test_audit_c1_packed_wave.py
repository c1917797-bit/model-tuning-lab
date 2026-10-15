import copy,unittest
from audit_c1_packed_wave import audit_packed_c1

class PackedAuditTests(unittest.TestCase):
    def fixture(self):
        workers={r:100+r for r in range(4)};layers=[str(i) for i in range(48)];events=[]
        for r,pid in workers.items():
            common=dict(rank=r,pid=pid,manifest_sha256="m")
            events.append(dict(common,event="compact_hypic_hooks_installed",default_disabled=True,
                c1_packed_wave=True,native_decode_batch=True,c1_layer_completion_barrier=True,
                c1_layer_shadow_validation=True))
            for layer in layers:
                base=dict(common,layer=layer,step=4)
                events.append(dict(base,event="compact_public_state_published",generation=1))
                for rid in ("a","b","native"):
                    metrics=[dict(tensor=t,passed=True,max_abs=0.,rms=0.,max_scaled=0.)
                             for t in ("output","state","conv")]
                    events.append(dict(base,event="c1_packed_wave_shadow_checked",request_id=rid,
                        group_requests=["a","b","native"],atol=.01,rtol=.003,passed=True,
                        private_buffers=True,actual_slot_commit="not_started",metrics=metrics))
                events.append(dict(base,event="c1_packed_wave_prepared",requests=["a","b","native"],
                    windows=5,packed_tokens=100,shared_wy_preparations=1,state_passes=3,
                    actual_slot_commit="not_started"))
                events.append(dict(base,event="c1_layer_precommit_validated",requests=["a","b","native"],
                    tensors=9,finite=True,actual_slot_commit="not_started"))
                for slot,rid in enumerate(("a","b","native")):
                    events.append(dict(base,event="mixed_native_gdn_completed" if rid=="native" else "compact_gdn_body_composed",
                        request_id=rid,slot=slot,generation=None if rid=="native" else 1,
                        skipped_body_tokens=0 if rid=="native" else 16376,finite=True))
        return events,workers,layers
    def run_audit(self,e,w,l,**kw):
        return audit_packed_c1(e,w,manifest_sha256="m",linear_layers=l,requests=["a","b"],**kw)
    def test_full_fourrank_join(self):
        e,w,l=self.fixture();result=self.run_audit(e,w,l)
        self.assertEqual(result["packed_groups"],192);self.assertEqual(result["shadow_requests"],576)
    def test_negative_mutations(self):
        original,w,l=self.fixture()
        changes=[
            lambda e:e[0].update(c1_packed_wave=False),
            lambda e:e[2].update(pid=999),
            lambda e:e[2].update(step=5),
            lambda e:e[2].update(manifest_sha256="other"),
            lambda e:e[2]["metrics"][0].update(max_scaled=float("nan")),
            lambda e:e[2]["metrics"][0].update(max_scaled=1.01),
            lambda e:e[2].update(group_requests=["a"]),
            lambda e:e.pop(3),
            lambda e:e[5].update(shared_wy_preparations=2),
            lambda e:e[5].update(windows=99),
            lambda e:e[6].update(requests=["a","b"]),
            lambda e:e[6].update(finite=False),
            lambda e:e[8].update(slot=0),
            lambda e:e[7].update(skipped_body_tokens=1),
            lambda e:e[7].update(generation=2),
            lambda e:e[5].update(state_passes=True),
            lambda e:e.insert(6,e.pop(7)),
            lambda e:e.append(copy.deepcopy(e[5])),
        ]
        for mutate in changes:
            e=copy.deepcopy(original);mutate(e)
            with self.assertRaises(ValueError):self.run_audit(e,w,l)
    def test_disabled_marker_absence(self):
        e,w,l=self.fixture();e=[x for x in e if x["event"]=="compact_hypic_hooks_installed"]
        for x in e:x["c1_packed_wave"]=False
        self.assertTrue(self.run_audit(e,w,l,enabled=False)["packed_disabled_verified"])
        e.append({"event":"c1_packed_wave_prepared"})
        with self.assertRaises(ValueError):self.run_audit(e,w,l,enabled=False)

if __name__=="__main__":unittest.main()

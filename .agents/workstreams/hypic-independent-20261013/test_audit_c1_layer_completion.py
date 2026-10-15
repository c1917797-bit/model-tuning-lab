import copy,unittest
from audit_c1_layer_completion import audit_c1_completion


class AuditControls(unittest.TestCase):
    def fixture(self):
        workers={r:40+r for r in range(4)};events=[]
        for r,pid in workers.items():
            common={"rank":r,"pid":pid,"manifest_sha256":"m"}
            events.append(dict(common,event="compact_hypic_hooks_installed",
                default_disabled=True,c1_layer_completion_barrier=True,c1_layer_shadow_validation=True))
            for n in range(48):
                base=dict(common,layer=str(n),step=5)
                events.append(dict(base,event="compact_public_state_published"))
                metrics=[dict(tensor=t,passed=True,max_abs=0.,rms=0.,max_scaled=0.) for t in ("output","state","conv")]
                events.append(dict(base,event="c1_layer_completion_shadow_checked",request_id="hot",atol=.01,rtol=.003,passed=True,metrics=metrics))
                events.append(dict(base,event="c1_layer_precommit_validated",requests=["hot","native"],tensors=6,finite=True,actual_slot_commit="not_started"))
                events.append(dict(base,event="compact_gdn_body_composed",request_id="hot",skipped_body_tokens=16376,finite=True))
                events.append(dict(base,event="mixed_native_gdn_completed",request_id="native",skipped_body_tokens=0,finite=True))
        return events,workers
    def test_complete_join(self):
        e,w=self.fixture();r=audit_c1_completion(e,w,manifest_sha256="m")
        self.assertEqual(r["serialized_shadow_groups"],192);self.assertEqual(r["precommit_groups"],192)
    def test_mutations_fail_closed(self):
        source,w=self.fixture()
        for mutate in (
            lambda e:e[2].update(passed=False),
            lambda e:e[2]["metrics"][0].update(max_scaled=float("nan")),
            lambda e:e[3].update(requests=["hot"]),
            lambda e:e[3].update(finite=False),
            lambda e:e[3].update(pid=999),
            lambda e:e[2].update(step=6),
            lambda e:e.pop(2),
            lambda e:e.insert(3,e.pop(4)),
            lambda e:e.append(copy.deepcopy(e[3])),
        ):
            e=copy.deepcopy(source);mutate(e)
            with self.assertRaises(ValueError):audit_c1_completion(e,w,manifest_sha256="m")
    def test_disabled_requires_absence_and_explicit_flags(self):
        e,w=self.fixture();e=[x for x in e if x["event"]=="compact_hypic_hooks_installed"]
        for x in e:x.update(c1_layer_completion_barrier=False,c1_layer_shadow_validation=False)
        self.assertTrue(audit_c1_completion(e,w,manifest_sha256="m",enabled=False,require_shadow=False)["c1_completion_disabled_verified"])
        e.append(dict(event="c1_layer_precommit_validated"))
        with self.assertRaises(ValueError):audit_c1_completion(e,w,manifest_sha256="m",enabled=False,require_shadow=False)

if __name__=="__main__":unittest.main()

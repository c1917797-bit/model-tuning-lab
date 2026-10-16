import copy,unittest
from audit_r18_partition_performance import audit_timed_partition
class TimedPartitionTests(unittest.TestCase):
    def fixture(self):
        events=[]
        for r in range(4):
            b=dict(rank=r,pid=100+r,step=1,layer="layer",manifest_sha256="m")
            events.extend([dict(b,event="compact_hypic_hooks_installed",c1_partitioned_render=True,
                c1_performance_mode=True,c1_first_divergence=False,c1_layer_shadow_validation=False),
                dict(b,event="c1_packed_wave_prepared",requests=["r"],state_schedule="partitioned",
                    state_passes=2,windows=2,packed_tokens=65,state_window_visits=2,state_token_visits=65,
                    actual_slot_commit="not_started"),
                dict(b,event="compact_gdn_body_composed",request_id="r",finite=True)])
        return events
    def test_enabled(self):self.assertEqual(audit_timed_partition(self.fixture(),"m",enabled=True)["completed"],4)
    def test_native(self):self.assertFalse(audit_timed_partition([],"m",enabled=False)["enabled"])
    def bad(self,fn):
        e=self.fixture();fn(e)
        with self.assertRaises(ValueError):audit_timed_partition(e,"m",enabled=True)
    def test_double_visit(self):self.bad(lambda e:e[1].update(state_token_visits=130))
    def test_wrong_step(self):self.bad(lambda e:e[2].update(step=2))
    def test_wrong_source(self):self.bad(lambda e:e[1].update(manifest_sha256="bad"))
    def test_probe_forbidden(self):self.bad(lambda e:e.append(dict(event="prompt_snapshot_opportunity")))
    def test_shadow_forbidden(self):self.bad(lambda e:e.append(dict(event="c1_packed_wave_shadow_checked")))
    def test_missing_worker(self):self.bad(lambda e:e.__delitem__(slice(0,3)))
    def test_native_rejects_algorithm(self):
        with self.assertRaises(ValueError):audit_timed_partition(self.fixture(),"m",enabled=False)
    def test_nonboolean_mode(self):self.bad(lambda e:e[0].update(c1_partitioned_render=1))
if __name__=="__main__":unittest.main()

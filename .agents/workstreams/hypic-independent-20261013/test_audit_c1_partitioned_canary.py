import copy,unittest
from audit_c1_partitioned_canary import audit_partition_rows
class PartitionAuditTests(unittest.TestCase):
    def fixture(self):
        workers={r:100+r for r in range(4)};events=[]
        for r,pid in workers.items():
            for layer in range(48):
                base=dict(rank=r,pid=pid,manifest_sha256="m",step=1,layer=str(layer))
                events.append(dict(base,event="c1_packed_wave_prepared",requests=["a","b"],
                    windows=4,packed_tokens=129,state_window_visits=4,state_token_visits=129,
                    state_passes=2,state_schedule="partitioned",actual_slot_commit="not_started"))
                for rid in ("a","b"):
                    events.append(dict(base,event="compact_gdn_body_composed",request_id=rid,finite=True))
                events.append(dict(base,event="c1_packed_wave_shadow_checked",request_id="a",
                    passed=True,private_buffers=True,actual_slot_commit="not_started",atol=.01,rtol=.003,
                    metrics=[dict(tensor=k,max_abs=.001,rms=.0001,max_scaled=.5,passed=True) for k in ("output","state","conv")]))
        return events,workers
    def test_complete(self):
        e,w=self.fixture();self.assertEqual(audit_partition_rows(e,w,"m")["groups"],192)
    def bad(self,mutate):
        e,w=self.fixture();mutate(e,w)
        with self.assertRaises(ValueError):audit_partition_rows(e,w,"m")
    def test_double_visits(self):self.bad(lambda e,w:e[0].update(state_token_visits=258))
    def test_wrong_pid(self):self.bad(lambda e,w:e[1].update(pid=999))
    def test_wrong_step(self):self.bad(lambda e,w:e[1].update(step=2))
    def test_wrong_source(self):self.bad(lambda e,w:e[0].update(manifest_sha256="old"))
    def test_failed_residual(self):self.bad(lambda e,w:e[3]["metrics"][0].update(max_scaled=1.1))
    def test_nan_residual(self):self.bad(lambda e,w:e[3]["metrics"][0].update(rms=float("nan")))
    def test_missing_shadow(self):self.bad(lambda e,w:e.pop(3))
    def test_duplicate_group(self):self.bad(lambda e,w:e.append(copy.deepcopy(e[0])))
    def test_boolean_count(self):self.bad(lambda e,w:e[0].update(windows=True))
    def test_boolean_dispatch(self):self.bad(lambda e,w:e[0].update(state_passes=True))
    def test_impossible_dispatch(self):self.bad(lambda e,w:e[0].update(state_passes=3))
    def test_missing_worker(self):self.bad(lambda e,w:w.pop(3))
if __name__=="__main__":unittest.main()

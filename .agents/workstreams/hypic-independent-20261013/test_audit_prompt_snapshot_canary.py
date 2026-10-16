import copy,unittest
from audit_prompt_snapshot_canary import audit_probe_rows
class Tests(unittest.TestCase):
    def fixture(self):
        workers={r:100+r for r in range(4)};events=[]
        for rank,pid in workers.items():
            for step in (9,10):
                events.append(dict(event="prompt_snapshot_opportunity",rank=rank,pid=pid,
                    manifest_sha256="m",step=step,request_ids=["req"],computed_tokens=[32768],
                    scheduled_tokens=[1],omitted_decode_ids=["req"],retained_prefill_ids=[],
                    omitted_prompt_tokens=32768,order=["original","prefill_only"],
                    measurements={"original":{"wall_ns":20,"thread_cpu_ns":15},
                                  "prefill_only":{"wall_ns":3,"thread_cpu_ns":2}}))
        return events,workers
    def test_complete_fourrank(self):
        e,w=self.fixture();r=audit_probe_rows(e,w,"m",{"req"})
        self.assertEqual(r[0]["original_thread_cpu_ns"],30)
        self.assertEqual(r[3]["steps"],[9,10])
    def reject(self,mutate):
        e,w=self.fixture();mutate(e)
        with self.assertRaises(ValueError):audit_probe_rows(e,w,"m",{"req"})
    def test_missing(self):self.reject(lambda e:e.pop())
    def test_duplicate_step(self):self.reject(lambda e:e[1].update(step=9))
    def test_wrong_source(self):self.reject(lambda e:e[0].update(manifest_sha256="wrong"))
    def test_wrong_pid(self):self.reject(lambda e:e[0].update(pid=999))
    def test_unknown_request(self):self.reject(lambda e:e[0].update(request_ids=["foreign"]))
    def test_prefill_not_decode(self):self.reject(lambda e:e[0].update(computed_tokens=[32767]))
    def test_wrong_denominator(self):self.reject(lambda e:e[0].update(omitted_prompt_tokens=1))
    def test_negative_clock(self):self.reject(lambda e:e[0]["measurements"]["original"].update(wall_ns=-1))
    def test_boolean_clock(self):self.reject(lambda e:e[0]["measurements"]["original"].update(wall_ns=True))
if __name__=="__main__":unittest.main()

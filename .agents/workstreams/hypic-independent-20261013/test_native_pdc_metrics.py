import unittest
from unittest.mock import patch
from native_pdc_metrics import parse_metrics,audit_delta,observe_full40,wait_boundary
import formal_pdc_metrics_tp4 as wrapper

def metrics(done=4,hits=0,queries=0,running=0,waiting=0,error=0):
    rows=[]
    for n,v in [("prefix_cache_queries_total",queries),("prefix_cache_hits_total",hits),
                ("num_requests_running",running),("num_requests_waiting",waiting)]:
        rows.append(f'vllm:{n}{{engine="0",model_name="qwen3.5"}} {v}')
    for reason in ("stop","length","abort","error","repetition"):
        val=done if reason=="length"else(error if reason=="error"else 0)
        rows.append(f'vllm:request_success_total{{engine="0",finished_reason="{reason}",model_name="qwen3.5"}} {val}')
    return "\n".join(rows)

class MetricsTest(unittest.TestCase):
    def test_parse_exact_official_labels(self):
        self.assertEqual(parse_metrics(metrics())["success"]["length"],4)
    def test_delta_excludes_warmups(self):
        x=audit_delta(metrics(hits=1024,queries=2048),metrics(44,hits=308224,queries=1312768))
        self.assertEqual(x["cached_tokens"],307200)
        self.assertEqual(x["measured_successes"],40)
    def test_zero_actual_hits_rejected(self):
        with self.assertRaises(ValueError):audit_delta(metrics(),metrics(44,queries=100))
    def test_counter_reset_rejected(self):
        with self.assertRaises(ValueError):audit_delta(metrics(hits=100,queries=200),metrics(44,hits=5,queries=10))
    def test_hits_exceed_queries_rejected(self):
        with self.assertRaises(ValueError):audit_delta(metrics(),metrics(44,hits=20,queries=10))
    def test_wrong_denominator(self):
        with self.assertRaises(ValueError):audit_delta(metrics(),metrics(43,hits=10,queries=20))
    def test_active_boundary(self):
        with self.assertRaises(ValueError):audit_delta(metrics(running=1),metrics(44,hits=10,queries=20))
    def test_error_boundary(self):
        with self.assertRaises(ValueError):audit_delta(metrics(error=1),metrics(44,hits=10,queries=20))
    def test_missing_series(self):
        with self.assertRaises(ValueError):parse_metrics("\n".join(metrics().splitlines()[1:]))
    def test_duplicate_series(self):
        s=metrics()
        with self.assertRaises(ValueError):parse_metrics(s+"\n"+s.splitlines()[0])
    def test_wrong_engine(self):
        with self.assertRaises(ValueError):parse_metrics(metrics().replace('engine="0"','engine="1"'))
    def test_wrong_model(self):
        with self.assertRaises(ValueError):parse_metrics(metrics().replace('model_name="qwen3.5"','model_name="other"'))
    def test_nonfinite_or_negative(self):
        for v in ("NaN","Inf","-1","1.5"):
            s=metrics().replace('queries_total{engine="0",model_name="qwen3.5"} 0',
                'queries_total{engine="0",model_name="qwen3.5"} '+v)
            with self.subTest(v=v),self.assertRaises(ValueError):parse_metrics(s)
    def test_metric_budget(self):
        with self.assertRaises(ValueError):parse_metrics("x"*2097153)
    def test_no_observation_inside_original_call(self):
        order=[];snapshots=iter([metrics(),metrics(44,hits=10,queries=20)])
        def fetch():order.append("fetch");return next(snapshots)
        def original(*args,**kwargs):order.append("measured");return {"valid":True}
        saved=[]
        result=observe_full40(original,(),{},fetch=fetch,guard=lambda:None,
                             save=saved.append,identity={"source":"test"})
        self.assertTrue(result["valid"])
        self.assertEqual(order,["fetch","measured","fetch"])
        self.assertTrue(saved[0]["audit"]["aggregate_native_pdc_verified"])
    def test_failure_receipt_retained(self):
        saved=[]
        def original():raise RuntimeError("measured failure")
        with self.assertRaises(RuntimeError):
            observe_full40(original,(),{},fetch=lambda:metrics(),guard=lambda:None,
                          save=saved.append,identity={})
        self.assertEqual(saved[0]["error"]["type"],"RuntimeError")
        self.assertNotIn("after",saved[0])
    def test_unexpected_foreign_request(self):
        with self.assertRaises(ValueError):
            wait_boundary(4,fetch=lambda:metrics(5),guard=lambda:None)
    def test_observation_wait_bounded(self):
        times=iter([0,61])
        with self.assertRaises(TimeoutError):
            wait_boundary(4,fetch=lambda:metrics(3),guard=lambda:None,clock=lambda:next(times))
    def test_default_contract_cannot_start(self):
        with self.assertRaises(ValueError):wrapper.check_contract({})
    def test_host_function_restored_on_controller_failure(self):
        original=wrapper.workload.run_full40
        with patch.object(wrapper,"check_contract"),patch.object(wrapper.controller,"run_contract",
                side_effect=RuntimeError("abort")):
            with self.assertRaises(RuntimeError):wrapper.run({}, "unused")
        self.assertIs(wrapper.workload.run_full40,original)
if __name__=="__main__":unittest.main()

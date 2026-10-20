"""Synthetic unit fixtures only. No measured data or formal acceptance report."""
import unittest
from fractions import Fraction as F
from unittest.mock import patch
import consume_formal as C


def reference(label):
 return dict(path="/unit-only/"+label,bytes=1,sha256={"record":"1","clock":"2","body":"3","raw":"4","frozen":"5","a":"6","b":"7"}.get(label,"8")*64)


def synthetic_stream():
 body=dict(prompt=[17,23,31],max_tokens=1024,ignore_eos=True,stream=True,
           return_token_ids=True,n=1,temperature=0,top_p=1)
 tokens=[11]*500+[12]*524
 record=dict(schema="bole.formal-stream-request/v1",phase="measured",request_key="unit-only",
  engine_request_id="unit-only-engine",response_id="unit-only-response",request_body=reference("body"),
  raw_stream=reference("raw"),clock=reference("clock"),submit_ns=10,end_ns=60,http_status=200,
  error=None,done_received=True,finish_reason="length",prompt_token_ids=[17,23,31],
  final_output_token_ids=tokens,usage=dict(completion_tokens=1024,prompt_tokens=3),events=[
   dict(ordinal=0,received_ns=11,response_id="unit-only-response",choice_index=0,token_ids=[]),
   dict(ordinal=1,received_ns=20,response_id="unit-only-response",choice_index=0,token_ids=tokens[:500]),
   dict(ordinal=2,received_ns=40,response_id="unit-only-response",choice_index=0,token_ids=tokens[500:])])
 expected=dict(request_key="unit-only",prompt_token_ids=[17,23,31],request_body=reference("frozen"))
 return record,expected,body


def check_stream(record,expected,body,actual_body=None):
 def read(ref):
  if ref["path"].endswith("record"):return record
  if ref["path"].endswith("body"):return body if actual_body is None else actual_body
  return body
 with patch.object(C,"obj",side_effect=read),patch.object(C,"checked",return_value=None):
  return C.stream_request(reference("record"),expected,"measured",reference("clock"))


class LossTests(unittest.TestCase):
 def test_both_exact_one_percent_boundary(self):
  self.assertTrue(C.losses(F(1),F(99,100))["passed"])
 def test_pp_pass_does_not_hide_relative_failure(self):
  r=C.losses(F(9,10),F(89,100));self.assertFalse(r["passed"])
  self.assertEqual(r["pp_loss"]["decimal"],1.)
 def test_relative_boundary_exact_no_rounding(self):
  self.assertTrue(C.losses(F(9,10),F(891,1000))["passed"])
  self.assertFalse(C.losses(F(9,10),F(890999,1000000))["passed"])
 def test_zero_baseline_undefined_not_invented_zero(self):
  result=C.losses(F(0),F(0));self.assertFalse(result["passed"])
  self.assertIsNone(result["relative_loss_percent"])
 def test_improvement_has_zero_positive_loss(self):
  self.assertTrue(C.losses(F(8,10),F(9,10))["passed"])


class PairTests(unittest.TestCase):
 @staticmethod
 def metric(ns):return dict(throughput=F(1024*10**9,ns),output_tokens=1024,elapsed_ns=ns)
 def test_three_exact_threshold_pairs(self):
  pair=(self.metric(11*10**9),self.metric(10*10**9))
  self.assertTrue(C.pair_summary([pair]*3)["prospective_all_three_pairs_pass"])
 def test_favorable_pooled_ratio_cannot_hide_failed_pair(self):
  pairs=[(self.metric(12*10**9),self.metric(6*10**9)),(self.metric(12*10**9),self.metric(8*10**9)),(self.metric(12*10**9),self.metric(12*10**9))]
  result=C.pair_summary(pairs)
  self.assertGreater(result["pooled_token_count_time_ratio"]["decimal"],1.1)
  self.assertFalse(result["prospective_all_three_pairs_pass"])
 def test_exact_three_rounds_required(self):
  with self.assertRaises(ValueError):C.pair_summary([])
 def test_peak_handles_end_then_submit_same_time(self):
  self.assertEqual(C.peak_inflight([(1,6),(2,4),(4,8)]),2)


class StreamTests(unittest.TestCase):
 def test_ttft_ignores_empty_chunk_tpot_uses_actual_delta_endpoints(self):
  record,expected,body=synthetic_stream();r=check_stream(record,expected,body)
  self.assertEqual(r["ttft_ns"],F(10));self.assertEqual(r["tpot_ns"],F(20,1023))
  self.assertEqual(r["first_chunk_tokens"],500)
 def test_four_token_service_rejected(self):
  record,expected,body=synthetic_stream();body["max_tokens"]=4
  with self.assertRaises(ValueError):check_stream(record,expected,body)
 def test_short_output_rejected_even_with_full_length_claim(self):
  record,expected,body=synthetic_stream();record["events"][2]["token_ids"]=[]
  with self.assertRaises(ValueError):check_stream(record,expected,body)
 def test_partial_stream_rejected(self):
  record,expected,body=synthetic_stream();record["done_received"]=False
  with self.assertRaises(ValueError):check_stream(record,expected,body)
 def test_nonmonotonic_stream_rejected(self):
  record,expected,body=synthetic_stream();record["events"][2]["received_ns"]=19
  with self.assertRaises(ValueError):check_stream(record,expected,body)
 def test_extra_sampling_difference_caught(self):
  record,expected,body=synthetic_stream();changed=dict(body,frequency_penalty=1)
  with self.assertRaises(ValueError):check_stream(record,expected,body,changed)


class ScoreTests(unittest.TestCase):
 def fixture(self):
  outputs={"good":reference("a"),"truncated_failure":reference("b")}
  cases={key:dict(metric_weight=dict(n=1,d=1))for key in outputs}
  items=[dict(case_id=key,output=ref,value=dict(n=int(key=="good"),d=1))for key,ref in outputs.items()]
  return outputs,cases,items
 def test_failed_truncated_case_kept_in_denominator(self):
  outputs,cases,items=self.fixture();self.assertEqual(C.weighted_task_score(items,cases,outputs),F(1,2))
 def test_excluding_failure_is_rejected(self):
  outputs,cases,items=self.fixture()
  with self.assertRaises(ValueError):C.weighted_task_score(items[:1],cases,outputs)
 def test_duplicate_case_rejected(self):
  outputs,cases,items=self.fixture()
  with self.assertRaises(ValueError):C.weighted_task_score(items+[items[0]],cases,outputs)
 def test_frozen_weights_used_exactly(self):
  outputs,cases,items=self.fixture();cases["good"]["metric_weight"]=dict(n=1,d=3)
  self.assertEqual(C.weighted_task_score(items,cases,outputs),F(1,4))


class ActivationTests(unittest.TestCase):
 def test_first_step_only_does_not_satisfy_all_request_use(self):
  ranks=[dict(rank=n,required_decode_inputs=1023,bole_processed_inputs=1,native_processed_inputs=1022,
              unattributed_decode_inputs=0,tree_steps=1,component_calls={})for n in range(4)]
  result=dict(feature_profile=reference("a"),rows=[dict(request_key="unit-only",phase="measured",engine_request_id="unit-only-engine",ranks=ranks)])
  profile=dict(schema="bole.formal-feature-profile/v1",expect_bole_decode="all",required_components=[])
  rows=[dict(request_key="unit-only",phase="measured",engine_request_id="unit-only-engine")]
  with patch.object(C,"proof",return_value=result),patch.object(C,"obj",return_value=profile):
   with self.assertRaises(ValueError):C.activation({},reference("record"),{},rows,reference("a"),True)
 def test_prepared_policy_never_passes(self):
  with patch.object(C,"obj",return_value=dict(schema="bole.formal-acceptance-policy/v1",prepared_only=True)):
   with self.assertRaises(ValueError):C.validate_policy(dict(policy=reference("record")))


if __name__=="__main__":unittest.main()

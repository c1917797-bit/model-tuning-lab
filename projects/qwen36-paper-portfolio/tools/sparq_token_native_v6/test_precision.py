"""Strict finite-precision contract tests. No Torch, Docker or NPU."""
import ast,copy,math,struct,sys,unittest
from pathlib import Path
from precision_oracle import PROTOCOL,bits32,classify,validate_witness
CHANNELS=list(range(32))
def f32(x):return struct.unpack(">f",struct.pack(">f",x))[0]
class ExactTie(unittest.TestCase):
 """Historical stable-ID probability-CPU32 diagnostic; not author ANN tie policy."""
 def make(self,scores,a,b,budget=128,local=1):
  return classify(scores,a,b,CHANNELS,CHANNELS,budget,local)
 def fixture(self):
  # 126 strict entries, two cutoff-equal alternatives, latest forced.
  scores=[2.]*126+[1.,1.,0.]
  return self.make(scores,list(range(127))+[128],list(range(126))+[127,128])
 def test_exact_binary32_tie_with_stable_low_id_and_forced_latest(self):
  w=self.fixture();self.assertTrue(validate_witness(w))
  self.assertEqual(w["changed_ids"],[126,127]);self.assertEqual(w["cutoff_equal"],[126,127])
  self.assertTrue(w["exact_cutoff_tie_explains_fp64"]);self.assertFalse(w["nonzero_score_tolerance"])
 def test_equal_support_still_strict_not_unconditionally_tie(self):
  w=self.fixture();w=self.make([2.]*126+[1.,1.,0.],w["support32"],w["support32"])
  self.assertTrue(validate_witness(w));self.assertFalse(w["exact_cutoff_tie_explains_fp64"])
 def test_one_binary32_ulp_difference_is_not_tie(self):
  higher=struct.unpack(">f",struct.pack(">I",0x3f800001))[0]
  with self.assertRaisesRegex(ValueError,"outside exact"):
   self.make([2.]*126+[higher,1.,0.],list(range(127))+[128],list(range(126))+[127,128])
 def test_nearby_binary64_values_do_not_manufacture_binary32_inputs(self):
  with self.assertRaisesRegex(ValueError,"already be exactly"):
   self.make([2.]*126+[1.+1e-12,1.,0.],list(range(127))+[128],list(range(126))+[127,128])
 def test_wrong_stable_tied_id_is_not_legal_for_this_port(self):
  with self.assertRaisesRegex(ValueError,"strict stable"):
   self.make([2.]*126+[1.,1.,0.],list(range(126))+[127,128],list(range(127))+[128])
 def test_wrong_forced_local_support_is_rejected(self):
  with self.assertRaisesRegex(ValueError,"strict stable"):
   self.make([2.]*126+[1.,1.,0.],list(range(128)),list(range(128)))
 def test_changed_strictly_above_token_rejected(self):
  with self.assertRaisesRegex(ValueError,"outside exact"):
   self.make([2.]*126+[1.,1.,0.],list(range(127))+[128],list(range(1,128))+[128])
 def test_channel_precision_divergence_is_not_token_tie(self):
  with self.assertRaisesRegex(ValueError,"channel identity"):
   classify([2.]*126+[1.,1.,0.],list(range(127))+[128],list(range(126))+[127,128],
    CHANNELS,list(range(1,33)))
 def test_no_fp64_sort_has_to_be_invented_when_all_tokens_selected(self):
  w=self.make([1.,0.,2.],[0,1,2],[0,1,2]);self.assertTrue(validate_witness(w))
 def test_single_live_token_all_forced_empty_prior(self):
  w=self.make([.5],[0],[0]);self.assertTrue(validate_witness(w));self.assertIsNone(w["cutoff_bits"])
 def test_support_duplicate_bool_out_of_domain_order_rejected(self):
  for v in ([0]*128,[True]+list(range(1,127))+[128],list(range(127))+[129],list(reversed(list(range(127))+[128]))):
   with self.subTest(v=v),self.assertRaises(ValueError):
    self.make([2.]*126+[1.,1.,0.],v,list(range(126))+[127,128])
 def test_nonfinite_or_nonfloat_score_rejected(self):
  for value in (float("nan"),float("inf"),float("-inf"),True,1):
   with self.subTest(value=value),self.assertRaises(ValueError):
    self.make([2.]*126+[value,1.,0.],list(range(127))+[128],list(range(126))+[127,128])
 def test_fixture_receipt_change_cannot_keep_success_boolean(self):
  for key,value in (("changed_ids",[]),("cutoff_equal",[126]),("support32",list(range(126))+[127,128]),
   ("strictly_above",list(range(125))),("nonzero_score_tolerance",True),("protocol","legacy"),
   ("channels64",list(range(1,33))),("cutoff_bits","7f800000"),("exact_cutoff_tie_explains_fp64",False)):
   w=self.fixture();w[key]=value
   with self.subTest(key=key),self.assertRaises((ValueError,TypeError)):validate_witness(w)
 def test_serialized_noncutoff_fp64_swap_rejected(self):
  w=self.fixture();w["support64"]=list(range(1,128))+[128];w["changed_ids"]=[0,127]
  with self.assertRaises(ValueError):validate_witness(w)
 def test_no_hardcoded_failed_token_ids_or_epsilon_in_classifier(self):
  tree=ast.parse(Path(__file__).with_name("precision_oracle.py").read_text())
  fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="classify")
  constants=[n.value for n in ast.walk(fn) if isinstance(n,ast.Constant)]
  self.assertNotIn(361,constants);self.assertNotIn(1157,constants)
  self.assertFalse(any(type(v) is float and 0<v<1 for v in constants))
 def test_arbitrary_tied_values_can_change_attention_output_materially(self):
  # Ranking tie alone cannot license PA output or recurrent state accuracy.
  ref=[10.,10.];candidate=[-10.,-10.]
  rms=math.sqrt(sum((x-y)**2 for x,y in zip(candidate,ref))/2)/math.sqrt(sum(x*x for x in ref)/2)
  self.assertGreater(rms,.005)
class SourceClosure(unittest.TestCase):
 def src(self,name):return Path(__file__).with_name(name).read_text()
 def test_oracle_never_calls_candidate_or_native_or_uses_saved_observed_score(self):
  s=self.src("precision_oracle.py");tree=ast.parse(s)
  fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="independent")
  calls=[n for n in ast.walk(fn) if isinstance(n,ast.Call)]
  self.assertFalse(any(isinstance(n.func,ast.Attribute) and n.func.attr in ("run","support","_npu_paged_attention") for n in calls))
  self.assertNotIn("candidate_ranking",s);self.assertNotIn("torch_npu",s)
  self.assertIn("kcpu.index_select",s);self.assertIn("vcpu.index_select",s)
 def test_float32_selector_and_float64_V_PA_independent(self):
  s=self.src("precision_oracle.py")
  for text in ("dtype=torch.float32","t.dtype==torch.float32","val64=val.double()","t.dtype==torch.float64","weights@nv"):
   self.assertIn(text,s)
 def test_author_feedback_full_matrix_FP64_hard_literal_complete_diagnostic(self):
  # Old probability-CPU32/PA gates above are diagnostic history, not author ANN authority.
  s=self.src("matrix.py")
  for text in ("author_feedback(torch,objects,rq,refk,refv","author_feedback(torch,objects,q,refk,refv",
   "reference_previous.copy_(expected","previous.copy_(out)","for step in range(160)","for b in range(1,17)",
   'conditional_metric["passed"] and literal_metric["finite"]',
   "author_literal_output_hard_gate=False","literal_output_deviation_complete_every_head=True",
   "FP64_reselect_formal=False","candidate_data_used_by_formal_reference=False",
   "full_original_qKV_FP64_recomputed=True","native_PA_executed=False"):
   self.assertIn(text,s)
  self.assertIn('LIMITS={"relative_rms":.005,"cosine":.99998}',self.src("numeric_gate.py"))
  oracle=self.src("independent_oracle.py")
  self.assertIn('ref=literal_reference(torch,objects,q[None],key[None],value[None]',oracle)
  self.assertIn('result=conditional(torch,q,k,v,dims,selected,reallocation)',oracle)
  self.assertIn('require(torch.equal(score,witness_score[:,:n])',oracle)
  self.assertIn('require(torch.equal(ranking,witness_ranking[:n])',oracle)
  self.assertIn("no backend ULP relaxation",oracle)
 def test_current_consumer_requires_every_author_witness_hardFP64_completeLiteral(self):
  s=self.src("ann_matrix_consumer.py")
  for text in ('row["CPU32_stable_ID_required"] is False',
   'metrics(row["author_conditional_fp64_metric"],b)',
   'diagnostic=row["author_literal_output_metric"]',
   'diagnostic["passed"]==calculated',
   'row["literal_output_deviation_complete_every_head"] is True',
   'for name in ("author_reference_q_selector_witness","author_reference_rq_selector_witness")',
   'row["full_original_qKV_FP64_recomputed"] is True',
   'row["literal_selector_observation_restored"] is True',
   'w["nonzero_score_tolerance"] is False',
   'require(keys==expected and steps==20480',
   'len(case["actual_step_refs"])==160'):
   self.assertIn(text,s)
  self.assertIn('row["FP64_reselect_formal"] is False',s)
  self.assertIn('lo<=x<=hi',s);self.assertIn('len(v)==6',s)
  self.assertIn("from ann_matrix_consumer import validate_matrix as author_ann_validate",self.src("receipt.py"))
 def test_CPU_smoke_consumed_before_device_no_stub_success(self):
  s=self.src("preflight.py");tree=ast.parse(s)
  fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="cpu_golden_smoke")
  text=ast.get_source_segment(s,fn)
  self.assertIn("checked=independent(torch",text)
  self.assertIn('conditional_cpu64_equal=bool(torch.allclose(',text)
  self.assertIn('validate_precision_smoke(report.get("registered_precision_smoke"))',s)
  self.assertNotIn("set_device",text)
 def test_new_component_protocol_not_legacy_model_authority(self):
  s=self.src("consume_numeric.py")
  self.assertIn('"schema":"sparq.complete-token-component/v9-author-ann-FP32-compensation"',s)
  self.assertNotIn('"schema":"sparq.complete-token-component/v7-fp32-support"',s)
  self.assertIn('"original011_numeric_status":"failed-not-promoted"',s)
  for field in ("model_executed","matched1024_e2e_verified","final2048_task_verified"):
   self.assertIn('"'+field+'":False',s)
  self.assertIn('report.get("precision_contract")==PROTOCOL',self.src("ann_matrix_consumer.py"))
  self.assertIn('original-dtype-selector/v4-FP32-compensation-fixed-capacity-per-request-SUM',self.src("contract.py"))
 def test_no_Torch_import_in_stdlib_helper(self):
  self.assertNotIn("torch",sys.modules);self.assertNotIn("torch_npu",sys.modules)
if __name__=="__main__":unittest.main(verbosity=2)

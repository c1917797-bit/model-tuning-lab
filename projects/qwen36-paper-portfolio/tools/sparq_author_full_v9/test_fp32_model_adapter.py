"""Stdlib handoff/allocator/diagnostic contracts; never native/model PASS."""
import ast,copy,math,unittest
from pathlib import Path
import allocation_contract as a,ann_fa_consumer as fa,source_contract as c,component_handoff as h
ROOT=Path(__file__).resolve().parent
def source(name):return (ROOT/name).read_text()
class FP32Adapter(unittest.TestCase):
 def test_exact_registered_persistent_dtype_shape_budget(self):
  p=a.shape_plan(320)
  self.assertEqual(p["output"],((16,6,256),4))
  self.assertEqual(p["alpha"],((16,6),4));self.assertEqual(p["weights"],((16,6,128),4))
  self.assertEqual(p["mean_off"],((16,256),4));self.assertEqual(p["corrected"],((16,6,256),2))
  self.assertEqual(p["key"],((17,128,1,256),2))
  self.assertEqual(set(a.ROW_VIEWS)|set(a.FIXED_VIEWS),set(p))
 def test_guarded_dtype_delta_counted_exactly(self):
  p=a.shape_plan(320);prior=dict(p);prior.pop("mean_off")
  for n in ("output","alpha","weights"):prior[n]=(p[n][0],2)
  old=sum((math.prod(s)+128)*v for s,v in prior.values())
  increase=sum((math.prod(p[n][0])+128)*2 for n in ("output","alpha","weights"))+(16*256+128)*4
  self.assertEqual(a.guarded_bytes(320)-old,increase)
 def test_native_metadata_and_selector_not_widened(self):
  p=a.shape_plan(264)
  self.assertEqual(p["importance"][1],2);self.assertEqual(p["scale"][1],2)
  self.assertEqual(p["lengths"][1],4);self.assertEqual(p["selected"][1],8)
  s=source("long_workspace.py");self.assertIn('int32={"lengths","pa_table","budget_tensor"}',s)
  self.assertIn("type(ws).run is numeric.ANNWorkspace.run",s)
  self.assertFalse(any(isinstance(n,ast.FunctionDef) and n.name=="run" for n in ast.walk(ast.parse(s))))
 def test_meanOFF_FP32_distinct_from_corrected_and_graph_static(self):
  s=source("ann_model_state.py")
  self.assertIn("zero=ws.mean_off",s);self.assertNotIn("zero=ws.corrected",s)
  self.assertIn("zero.zero_()",s);self.assertIn("zero.dtype==self.t.float32",s)
  self.assertIn("zero_mean.dtype==torch.float32",source("no_pa_full.py"))
  self.assertIn('self.alpha=alloc("alpha",(16,6),t.float32)',source("ann_snapshot.py"))
 def test_true_long_budget_with_other_owners_and_peak_failclosed(self):
  self.assertLess(a.guarded_bytes(320)+a.transient_upper(320),a.AUX_CEILING)
  for other,peak in ((a.AUX_CEILING,10),(0,10+a.AUX_CEILING+1)):
   with self.assertRaises(ValueError):a.budget_admission(320,other,10,10,peak)
 def fixture(self,rms):
  H=dict(shape=[256],dtype="torch.float64",size_bytes=2048,sha256="a"*64,observed_complete_tensor=True)
  row=dict(full_dimensions=256,actual_energy=1.,reference_energy=1.,dot=1.,squared_error=rms*rms,
   actual_hash=copy.deepcopy(H),reference_hash=copy.deepcopy(H))
  metric=dict(relative_rms=[[rms]*6],cosine=[[1.]*6],finite=True,passed=rms<=fa.RMS)
  return [copy.deepcopy(row) for _ in range(6)],metric
 def test_literal_outside_threshold_complete_is_diagnostic_not_parity(self):
  rows,metric=self.fixture(.01)
  out=fa.literal_diagnostic(rows,metric,"outside-original-hard-thresholds-diagnostic-only")
  self.assertFalse(out["hard_gate"]);self.assertFalse(out["within_original_thresholds"])
  with self.assertRaises(ValueError):fa.reductions(rows,metric)
 def test_literal_missing_row_or_wrong_pass_label_rejected(self):
  rows,metric=self.fixture(.01)
  with self.assertRaises(ValueError):fa.literal_diagnostic(rows[:-1],metric,"outside-original-hard-thresholds-diagnostic-only")
  metric["passed"]=True
  with self.assertRaises(ValueError):fa.literal_diagnostic(rows,metric,"within-original-hard-thresholds")
 def test_hard_FP64_limits_domain_no_epsilon_remain(self):
  self.assertEqual((fa.RMS,fa.COS),(.005,.99998))
  rows,metric=self.fixture(.01)
  with self.assertRaises(ValueError):fa.reductions(rows,metric)
  rows[0]["reference_energy"]=0
  with self.assertRaises(ValueError):fa.literal_diagnostic(rows,metric,"outside-original-hard-thresholds-diagnostic-only")
 def test_original_refs_exact_current_not_union_or_model_permission(self):
  m=c.obj(h.PROPOSED);out=h.proposed_source_interfaces()
  self.assertTrue(out["proposed_only"]);self.assertFalse(out["model_permission"])
  self.assertEqual(m["paper_cutoff"],"2026-10-08T19:00:00Z")
  bad=copy.deepcopy(m);bad["registered_author_successor"]["protocol"]="retired-author-literal-hard-parity"
  with self.assertRaises(ValueError):h.manifest(bad,h.CURRENT)
 def test_model_serializer_consumer_same_source_and_dtype_fields(self):
  p=source("ann_model_oracle.py");q=source("ann_fa_consumer.py")
  for s in (p,q):self.assertIn("sparq.actual-model-author-ann-FP32-FA/v2",s)
  for k in ("final_output_dtype","compensation_dtype","literal_BF16_hard_gate","literal_deviation_status"):self.assertIn(k,p);self.assertIn(k,q)
  self.assertIn('source_ANN=dict(path=str(c.KERNEL/"SOURCE_MANIFEST.json"),sha256=c.KERNEL_SHA)',p)
  self.assertIn('reductions(row["FP64_full_vector_reductions"]',q)
  self.assertIn('literal_diagnostic(row["literal_full_vector_reductions"]',q)
 def test_formal_source_never_routes_literal_diagnostic_to_timing(self):
  self.assertIn("if self.diagnostic:",source("ann_model_state.py"))
  self.assertIn("sample=self.snapshot(prefix,b,query.device) if self.diagnostic else None",source("ann_model_state.py"))
  self.assertIn('w["timing_debug_off"] is True',source("consume_service.py"))
if __name__=="__main__":unittest.main()

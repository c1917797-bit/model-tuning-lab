"""Stdlib tests only. These tests are not numerical/device/model acceptance."""
import ast,math,types,unittest
from contract import topk_legal
from literal_author import extracted,ANN_NODES,CAUSAL_NODES
class TopK(unittest.TestCase):
 def test_exact_ties_arbitrary_IDs(self):
  for ids in ([0,1],[1,0],[0,2],[2,0]):self.assertEqual(topk_legal([2.,2.,2.,1.],ids,2)["epsilon"],0)
 def test_non_tie_no_one_ULP(self):
  with self.assertRaises(ValueError):topk_legal([1.,math.nextafter(1.,2.)],[0],1)
 def test_non_tie_order(self):
  with self.assertRaises(ValueError):topk_legal([2.,3.,1.],[0,1],2)
 def test_forced_positive_infinity(self):
  self.assertEqual(topk_legal([1.,2.,float("inf")],[2,1],2,forced=(2,))["selected_count"],2)
 def test_nonlocal_infinity_rejected(self):
  with self.assertRaises(ValueError):topk_legal([float("inf"),1.],[0],1)
 def test_nan_rejected(self):
  with self.assertRaises(ValueError):topk_legal([float("nan"),1.],[0],1)
 def test_duplicate_rejected(self):
  with self.assertRaises(ValueError):topk_legal([2.,1.],[0,0],2)
 def test_invalid_domain_rejected(self):
  with self.assertRaises(ValueError):topk_legal([2.,1.,100.],[2],1,valid=(0,1))
 def test_forced_missing_rejected(self):
  with self.assertRaises(ValueError):topk_legal([1.,2.,3.],[2,1],2,forced=(0,))
 def test_all_domain(self):self.assertEqual(topk_legal([3.,2.,1.],[0,1,2],3)["tied_excluded"],[])
class ASTClosure(unittest.TestCase):
 def test_missing_class_fails(self):
  with self.assertRaises(ValueError):extracted(b"def gather(): pass\n",ANN_NODES)
 def test_duplicate_class_fails(self):
  with self.assertRaises(ValueError):extracted(b"def score_to_mask(): pass\ndef score_to_mask(): pass\ndef causal_index(): pass\n",CAUSAL_NODES)
 def test_unrelated_import_not_executed(self):
  tree=extracted(b"import transformers\ndef score_to_mask(x): return x\ndef causal_index(x): return score_to_mask(x)\n",CAUSAL_NODES)
  self.assertFalse(any(isinstance(n,ast.Import) for n in tree.body))
 def test_actual_source_excerpt_dataclass_namespace_without_Torch(self):
  from literal_author import build
  fake=types.SimpleNamespace(Tensor=object,nn=types.SimpleNamespace(Module=object))
  ann,causal=build(fake)
  settings=ann["Settings"](127,0,True,"sparse_q",rank=32)
  self.assertEqual(settings.score.rank,32)
  self.assertEqual(settings.local_k,0)
  self.assertEqual(ann["Settings"].__module__,"frozen_ann_math_AST_excerpt")
  self.assertTrue(callable(causal["causal_index"]))
  import sys
  self.assertIs(sys.modules[ann["Settings"].__module__].__dict__,ann)
  self.assertEqual(causal["causal_index"].__module__,"frozen_causal_math_AST_excerpt")
 def test_bodies_exact_AST(self):
  source=b"def score_to_mask(x): return x+1\ndef causal_index(x): return score_to_mask(x)\n"
  original=ast.parse(source.decode()).body
  selected=extracted(source,CAUSAL_NODES).body[1:]
  self.assertEqual([ast.dump(x) for x in original],[ast.dump(x) for x in selected])
class LiteralObserver(unittest.TestCase):
 class Value:
  def __init__(self,value):self.value=value
  def detach(self):return self
  def clone(self):return self
 class Score:
  def __init__(self):self.hook=None;self.removed=False
  def register_forward_hook(self,hook):
   self.hook=hook;score=self
   class Handle:
    def remove(self):score.hook=None;score.removed=True
   return Handle()
 def fixture(self,fail=False):
  ann={};calls=[]
  def original(t,dim,i):calls.append((t,dim,i));return t
  ann["gather"]=original;score=self.Score();v=self.Value(17)
  class Module:
   def __init__(self):self.score=score
   def __call__(self,q,k,value,mask):
    self_q=ann["gather"](q,-1,v);self_k=ann["gather"](k,-1,v)
    score.hook(score,(self_q,self_k),v)
    if fail:raise RuntimeError("original-first-fault")
    return self_q,value
  return ann,Module(),original,score,calls,v
 def test_transparent_same_call_values(self):
  from literal_author import observed_call
  ann,module,original,score,calls,v=self.fixture()
  q=object();k=object();value=object()
  out,weights,channels,stage=observed_call(ann,module,q,k,value,object())
  self.assertIs(out,q);self.assertIs(weights,value);self.assertIs(stage,v)
  self.assertEqual(len(channels),2);self.assertEqual(len(calls),2)
  self.assertIs(ann["gather"],original);self.assertTrue(score.removed)
 def test_original_first_fault_hook_and_namespace_restored(self):
  from literal_author import observed_call
  ann,module,original,score,calls,v=self.fixture(True)
  with self.assertRaisesRegex(RuntimeError,"original-first-fault"):observed_call(ann,module,object(),object(),object(),object())
  self.assertIs(ann["gather"],original);self.assertTrue(score.removed);self.assertIsNone(score.hook)
 def test_two_independent_calls_no_shared_namespace_observation(self):
  from literal_author import observed_call
  ann,module,original,score,calls,v=self.fixture()
  first=observed_call(ann,module,object(),object(),object(),object())
  score.removed=False
  second=observed_call(ann,module,object(),object(),object(),object())
  self.assertIsNot(first[2],second[2]);self.assertEqual(len(calls),4)
  self.assertIs(ann["gather"],original);self.assertTrue(score.removed)
class FormalSourceBoundary(unittest.TestCase):
 def function(self,name,file):
  from pathlib import Path
  tree=ast.parse((Path(__file__).parent/file).read_text())
  return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
 def test_formal_FP64_has_no_candidate_or_workspace_import(self):
  node=self.function("author_feedback","independent_oracle.py")
  text=ast.unparse(node)
  self.assertIn("literal_reference(",text);self.assertIn("ref['channels']",text);self.assertIn("ref['indices']",text)
  self.assertNotIn("workspace",text);self.assertNotIn("candidate",",".join(a.arg for a in node.args.args))
  self.assertIn("conditional(torch, q, k, v, dims, selected",text)
 def test_FP64_final_logits_use_original_q_full_history(self):
  node=self.function("conditional","independent_oracle.py");text=ast.unparse(node)
  self.assertIn("query.detach().cpu().double()",text);self.assertIn("key.detach().cpu().double()",text)
  self.assertIn("value.detach().cpu().double()",text)
  self.assertIn("weights @ selected_value",text);self.assertIn("value.mean(0)",text)
  self.assertNotIn("score_observation",text)
 def test_matrix_q_rq_two_independent_source_calls(self):
  node=self.function("run_case","matrix.py")
  calls=[n for n in ast.walk(node) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="author_feedback"]
  self.assertEqual(len(calls),2)
  self.assertEqual([n.args[2].id for n in calls],["rq","q"])
  self.assertTrue(all(len(n.args)==8 for n in calls))
 def test_reselect_only_explicit_diagnostic_not_feedback(self):
  node=self.function("run_case","matrix.py");text=ast.unparse(node)
  self.assertIn("expected = feedback['output']",text)
  self.assertNotIn("expected = diagnostic_",text);self.assertNotIn("reference_previous.copy_(diagnostic",text)
  self.assertIn("FP64_reselect_formal=False",text)
 def test_original_two_stage_equal_predicates_unchanged(self):
  node=self.function("source_legality","independent_oracle.py")
  calls=[n for n in ast.walk(node) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="equal"]
  self.assertEqual(len(calls),2);text=ast.unparse(node)
  self.assertIn("torch.equal(score, witness_score[:, :n])",text)
  self.assertIn("torch.equal(ranking, witness_ranking[:n])",text)
 def test_zero_domain_no_epsilon_and_no_hidden_author_edit(self):
  node=self.function("conditional","independent_oracle.py");text=ast.unparse(node)
  self.assertIn("denominator > 0",text);self.assertIn("numerator > 0",text)
  self.assertNotIn("clamp",text)
  self.assertFalse(any(isinstance(n,ast.BinOp) and isinstance(n.op,ast.Add) and
   any(isinstance(v,ast.Constant) and type(v.value) is float and 0<abs(v.value)<1e-6 for v in (n.left,n.right)) for n in ast.walk(node)))
 def test_current_canonical_context_distinct_private_frozen(self):
  node=self.function("source_pins","contract.py");text=ast.unparse(node)
  self.assertIn("ROOT.resolve() == BASE.resolve()",text)
  self.assertIn("m['source_count'] == 42",text);self.assertIn("private-frozen41-BF16-substrate",ast.unparse(node))
  self.assertIn("m['files']['contract.py'] == sha(Path(__file__).resolve())",text)

class CPUBeforeValidation(unittest.TestCase):
 def fixture(self,root):
  import cpu_smoke as smoke
  from contract import PROTOCOL,write_new
  raw=write_new(root/"raw.json",{"unit_fixture_only":True,"npu_executed":False})
  cases=[]
  for batch in (1,2):
   for mean in (False,True):
    cases.append({"batch":batch,"reallocation":mean,"source_stage_checked":True,
     "native_input_untouched":True,"guards":True,"candidate_data_used_by_formal_reference":False,
     "FP64_reselect_formal":False,"reference_selector":"own BF16 literal author q/rq independent",
     "literal_outside_capture":True,"literal_output_metric":{"passed":True,"finite":True,"relative_rms":[[0.0]*6],"cosine":[[1.0]*6]},
     "conditional_fp64_metric":{"passed":False,"finite":True,"relative_rms":[[.006]*6],"cosine":[[1.0]*6]},
     "raw_observation_is_not_acceptance":True,
     "author_literal_output_hard_gate":False,"literal_output_deviation_complete_every_head":True,
     "original_BF16_dual_gate_status":"FAILED-not-promoted"})
  return {"protocol":PROTOCOL,"source_sha256":smoke.sha(__import__("pathlib").Path(smoke.__file__).resolve()),
   "torch_npu_initialized_after":False,"torch_threads":1,"npu_executed":False,"raw_before":raw,"cases":cases}
 def test_complete_raw_survives_original_metric_rejection(self):
  import tempfile,json
  from pathlib import Path
  from cpu_smoke import publish_validate
  parent=Path("/cache/cch/qwen36-paper-preparation-20261007/sparse")
  with tempfile.TemporaryDirectory(dir=parent,prefix="ann-cpu-observer-") as name:
   root=Path(name);report=self.fixture(root)
   with self.assertRaisesRegex(ValueError,"all actual four CPU-BF16"):
    publish_validate(report,root,root)
   raw=json.loads((root/"ANN_CPU_CASES_BEFORE_VALIDATE.json").read_text())
   self.assertEqual(raw["report"],report);self.assertEqual(len(raw["report"]["cases"]),4)
   self.assertFalse(raw["validation_attempted"]);self.assertFalse(raw["validation_passed"])
   self.assertFalse(raw["native_numeric_ready"]);self.assertFalse(raw["npu_executed"])
   self.assertEqual(raw["report"]["cases"][0]["conditional_fp64_metric"]["relative_rms"],[[.006]*6])
 def test_existing_final_rejects_before_validate_without_overwrite(self):
  import tempfile
  from pathlib import Path
  from unittest.mock import patch
  import cpu_smoke as smoke
  parent=Path("/cache/cch/qwen36-paper-preparation-20261007/sparse")
  with tempfile.TemporaryDirectory(dir=parent,prefix="ann-cpu-observer-") as name:
   root=Path(name);report=self.fixture(root);final=root/"ANN_CPU_CASES_BEFORE_VALIDATE.json"
   final.write_bytes(b"original retained bytes")
   with patch.object(smoke,"validate",side_effect=AssertionError("must not run")) as mocked:
    with self.assertRaises(FileExistsError):smoke.publish_validate(report,root,root)
   self.assertEqual(final.read_bytes(),b"original retained bytes");mocked.assert_not_called()
 def test_exact_publish_before_validate_and_original_toy_geometry(self):
  from pathlib import Path
  source=(Path(__file__).parent/"cpu_smoke.py").read_text();tree=ast.parse(source)
  observe=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="publish_validate")
  calls=[n for n in ast.walk(observe) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
  self.assertLess(next(n.lineno for n in calls if n.func.id=="write_new"),next(n.lineno for n in calls if n.func.id=="validate"))
  smoke=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="smoke")
  text=ast.unparse(smoke)
  self.assertIn("lengths = [129, 257][:batch]",text);self.assertIn("for correction in (False, True):",text)
  self.assertIn("output_root = Path(output)",text);self.assertIn("output_root, host_alias",text)
  self.assertEqual(sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="source_legality" for n in ast.walk(smoke)),1)
 def test_nonfinite_observation_not_silent_zero_or_metric_change(self):
  from cpu_smoke import observed_tensor
  class T:
   dtype="unit-fixture";device="cpu"
   shape=(3,)
   def stride(self):return (1,)
   def is_contiguous(self):return True
   def detach(self):return self
   def cpu(self):return self
   def tolist(self):return [float("nan"),float("inf"),-float("inf")]
  self.assertEqual(observed_tensor(T())["values"],["NaN","+Infinity","-Infinity"])


class RegisteredFP32Compensation(unittest.TestCase):
 def source(self,name):
  from pathlib import Path
  return (Path(__file__).parent/name).read_text()
 def test_BF16_selector_prefix_only_registered_rank_layout_delta(self):
  import hashlib
  text=self.source("ann_workspace.py")
  prefix=text[text.index("  # Matches original SparseQ"):text.index("  if reallocation:")]
  registered="  # Registered fixed-capacity layout port: [6,2304] SUM(0) per request.\n  # Persistent input/output; static B loop, no host live-length read/capture.\n  self.rank_input.copy_(self.score)\n  self.rank_input.masked_fill_(recent[:,None,:],torch.finfo(torch.float32).max)\n  for i in range(b):\n   torch.sum(self.rank_input[i],dim=0,out=self.ranking[i])"
  historical="  self.ranking.copy_(self.score.masked_fill(recent[:,None,:],torch.finfo(torch.float32).max).sum(1))"
  self.assertEqual(prefix.count(registered),1)
  restored=prefix.replace(registered,historical)
  self.assertEqual(hashlib.sha256(restored.encode()).hexdigest(),"312bd865b9dfb3577b74dd94414014e242af5e26bafef6c7144390d8523301f2")
 def test_original_BF16_QK_score_staging_retained(self):
  text=self.source("ann_workspace.py")
  self.assertIn("query.div(math.sqrt(256))",text);self.assertIn("exact_scores.add_",text)
  self.assertIn("qshort.div(scale[:,:,None])",text)
  self.assertNotIn("query.float()",text);self.assertNotIn("qshort.float()",text)
 def test_FP32_buffers_and_only_final_BF16_cast(self):
  text=self.source("ann_workspace.py")
  for name,shape in (("alpha","(batch,6)"),("weights","(batch,6,128)"),("output","(batch,6,256)")):
   self.assertIn("self."+name+"=alloc("+shape+",torch.float32)",text)
  final=text[text.index("  if reallocation:"):]
  self.assertEqual(final.count(".to(vc.dtype)"),1)
  self.assertIn("torch.bmm(weights,sv.float())",final)
  self.assertNotIn("mean[:,None,:].to",final);self.assertNotIn(".sum(-1).to",final)
 def test_hard_FP64_but_literal_complete_diagnostic_not_fake_parity(self):
  text=self.source("matrix.py")
  self.assertIn('require(conditional_metric["passed"] and literal_metric["finite"]',text)
  self.assertNotIn('conditional_metric["passed"] and literal_metric["passed"]',text)
  self.assertIn("author_literal_output_hard_gate=False",text)
  self.assertIn("literal_output_deviation_complete_every_head=True",text)
  self.assertIn('original_BF16_dual_gate_status="FAILED-not-promoted"',text)
 def test_literal_failed_metric_still_required_and_classified(self):
  text=self.source("ann_matrix_consumer.py")
  self.assertIn('diagnostic=row["author_literal_output_metric"]',text)
  self.assertIn('diagnostic["passed"]==calculated',text)
  self.assertIn('metrics(row["author_conditional_fp64_metric"],b)',text)
 def test_complete_matrix_original_coverage_unchanged(self):
  text=self.source("matrix.py")
  self.assertIn("range(1,17)",text);self.assertIn("range(160)",text)
  self.assertIn('("eager",0),("graph",0),("graph",1),("graph",2)',text)
  self.assertIn("if step==80:",text);self.assertIn("if step%11==0:",text)
  self.assertIn("require(len(cases)==128",text)
 def test_original_cpu_four_toy_inputs_unchanged(self):
  text=self.source("cpu_smoke.py")
  self.assertIn("lengths=[129,257][:batch]",text)
  self.assertIn("(torch.arange(k.numel()).view_as(k)%31)/2048",text)
  self.assertIn("for correction in (False,True):",text)
 def test_original_FP64_function_bytes_and_literal_unadapted(self):
  from pathlib import Path
  from contract import sha
  self.assertEqual(sha(Path(__file__).parent/"literal_author.py"),"1468b55c25aa99132d3f7d7dcbd9ead7b0b88c4707d08d999a9754312eb21602")
  import hashlib
  text=self.source("independent_oracle.py")
  self.assertEqual(hashlib.sha256(text[text.index("def history"):].encode()).hexdigest(),"108f43c5b68377edecb458086c7ad6f4f7ec5ec7107073dd3772f30c1b62d836")
  self.assertEqual(sha(Path(__file__).parent/"independent_oracle.py"),"6ed5f73deffc1790f6c6c54806181956248a6042080ca10ead8116abb7e4e945")

class FixedPaperCutoff(unittest.TestCase):
 def policy(self):
  from pathlib import Path
  text=(Path(__file__).parent/"receipt.py").read_text();tree=ast.parse(text)
  node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="validate_cutoff_fields")
  def require(ok,message):
   if not ok:raise ValueError(message)
  from receipt import EXECUTION_CLOCK
  ns={"require":require,"EXECUTION_CLOCK":EXECUTION_CLOCK};exec(compile(ast.Module(body=[node],type_ignores=[]),"<actual-receipt-cutoff-policy>","exec"),ns)
  return ns["validate_cutoff_fields"]
 def test_exact_paper_and_separate_portfolio(self):
  from receipt import EXECUTION_CLOCK
  value={"paper_cutoff":"2026-10-08T19:00:00Z","portfolio_cutoff":"2026-10-09T11:17:31Z","execution_clock":EXECUTION_CLOCK}
  self.assertEqual(self.policy()(value),value)
 def test_portfolio_must_not_replace_paper(self):
  with self.assertRaisesRegex(ValueError,"fixed paper19Z"):
   self.policy()({"paper_cutoff":"2026-10-09T11:17:31Z","portfolio_cutoff":"2026-10-09T11:17:31Z"})
 def test_missing_or_changed_cutoff_fails(self):
  for value in ({},{"paper_cutoff":"2026-10-08T19:00:01Z","portfolio_cutoff":"2026-10-09T11:17:31Z"},
    {"paper_cutoff":"2026-10-08T19:00:00Z","portfolio_cutoff":"2026-10-09T11:17:30Z"}):
   with self.assertRaisesRegex(ValueError,"fixed paper19Z"):self.policy()(value)
 def test_host_child_source_and_consumer_share_policy(self):
  from pathlib import Path
  root=Path(__file__).parent
  receipt=ast.parse((root/"receipt.py").read_text())
  assign={node.targets[0].id:node.value for node in receipt.body if isinstance(node,ast.Assign) and
   len(node.targets)==1 and isinstance(node.targets[0],ast.Name)}
  self.assertEqual(assign["PAPER_CUT"].value,"2026-10-08T19:00:00+00:00")
  self.assertEqual(assign["PORTFOLIO_CUT"].value,"2026-10-09T11:17:31+00:00")
  self.assertIsInstance(assign["CUT"],ast.Name);self.assertEqual(assign["CUT"].id,"REPAIR_CUT")
  self.assertEqual(assign["REPAIR_CUT"].value,"2026-10-10T07:00:25+00:00")
  source=next(n for n in receipt.body if isinstance(n,ast.FunctionDef) and n.name=="source_identity")
  self.assertIn("validate_cutoff_fields(m)",ast.unparse(source))
  numeric=(root/"numeric_gate.py").read_text()
  self.assertIn("datetime.fromisoformat(CUT)",numeric)
  self.assertNotIn('datetime.fromisoformat("2026-10-09',numeric)
  self.assertIn("validate_cutoff_fields(report)",(root/"ann_matrix_consumer.py").read_text())


class RegisteredFixedCapacityRank(unittest.TestCase):
 def function(self,file,name):
  from pathlib import Path
  tree=ast.parse((Path(__file__).parent/file).read_text())
  return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
 def geometry(self):
  def require(ok,message):
   if not ok:raise ValueError(message)
  ns={"require":require}
  exec(compile(ast.Module(body=[self.function("independent_oracle.py","rank_geometry")],type_ignores=[]),"<actual-rank-metadata>","exec"),ns)
  return ns["rank_geometry"]
 def test_actual_short39_and_full2157_geometry(self):
  q=types.SimpleNamespace(shape=(6,256))
  for n in (1,39,2148,2157,2304):
   self.assertEqual(self.geometry()(q,types.SimpleNamespace(shape=(n,256)),2304),n)
 def test_reject_wrong_capacity_empty_overflow_or_head_geometry(self):
  q=types.SimpleNamespace(shape=(6,256))
  for shape,capacity in (((39,256),2157),((39,256),True),((0,256),2304),((2305,256),2304),((39,255),2304)):
   with self.assertRaises(ValueError):self.geometry()(q,types.SimpleNamespace(shape=shape),capacity)
  with self.assertRaises(ValueError):self.geometry()(types.SimpleNamespace(shape=(5,256)),types.SimpleNamespace(shape=(39,256)),2304)
 def test_real_candidate_static_request_sum_persistent_out(self):
  from pathlib import Path
  tree=ast.parse((Path(__file__).parent/"ann_workspace.py").read_text())
  klass=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=="ANNWorkspace")
  run=next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name=="run")
  loops=[n for n in run.body if isinstance(n,ast.For)]
  self.assertEqual(len(loops),1);loop=loops[0]
  self.assertEqual(ast.unparse(loop.iter),"range(b)")
  self.assertEqual(len(loop.body),1);self.assertIsInstance(loop.body[0],ast.Expr)
  calls=[n for n in ast.walk(loop.body[0]) if isinstance(n,ast.Call)]
  self.assertEqual(len(calls),1);call=calls[0]
  self.assertEqual(ast.unparse(call.func),"torch.sum")
  self.assertEqual(ast.unparse(call.args[0]),"self.rank_input[i]")
  self.assertEqual({k.arg:ast.unparse(k.value) for k in call.keywords},{"dim":"0","out":"self.ranking[i]"})
  self.assertNotIn(".item(",ast.unparse(loop));self.assertNotIn(".cpu(",ast.unparse(loop))
  ctor=next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name=="__init__")
  self.assertIn("self.rank_input = alloc((batch, 6, self.capacity), torch.float32)",ast.unparse(ctor))
 def test_independent_score_and_padded_sum_not_candidate_reuse(self):
  node=self.function("independent_oracle.py","native_stage");text=ast.unparse(node)
  self.assertEqual([v.arg for v in node.args.args],["torch","q","key","dims","capacity"])
  self.assertIn("for query in q:",text);self.assertIn("projected.div(scale) @ projected_key.T",text)
  self.assertIn("torch.full((6, capacity), float('-inf'), dtype=torch.float32, device=score.device)",text)
  self.assertIn("padded[:, n - 1]",text);self.assertIn("padded.sum(0)[:n]",text)
  self.assertNotIn("candidate",text);self.assertNotIn("witness",text)
 def test_both_real_callers_pass_actual_workspace_capacity(self):
  from pathlib import Path
  for file,name in (("matrix.py","run_case"),("cpu_smoke.py","smoke")):
   node=self.function(file,name)
   calls=[n for n in ast.walk(node) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="source_legality"]
   self.assertEqual(len(calls),1);self.assertEqual(len(calls[0].args),8)
   self.assertEqual(ast.unparse(calls[0].args[-1]),"workspace.capacity")
 def consumer(self):
  from contract import require
  ns={"require":require}
  exec(compile(ast.Module(body=[self.function("ann_matrix_consumer.py","validate_rank_layout")],type_ignores=[]),"<actual-rank-consumer>","exec"),ns)
  return ns["validate_rank_layout"]
 def record(self,n):
  return {"protocol":"per-request-FP32-SUM0-fixed-capacity/v1","capacity":2304,"live_length":n,
   "current_sentinel":n-1,"own_inputs":True,"candidate_rank_or_score_used":False,
   "cropped_reduction_diagnostic_only":True,"cropped_vs_registered_difference_tokens":[]}
 def test_real_consumer_short39_and_rank_difference_diagnostic(self):
  for n in (39,2148):
   row=self.record(n)
   if n==2148:row["cropped_vs_registered_difference_tokens"]=[2140]
   self.assertEqual(self.consumer()(row,n),row)
 def test_real_consumer_reject_old_cropped_candidate_reuse_and_wrong_sentinel(self):
  for key,value in (("protocol","old-cropped"),("capacity",2157),("current_sentinel",2303),
   ("own_inputs",False),("candidate_rank_or_score_used",True),("cropped_reduction_diagnostic_only",False),
   ("cropped_vs_registered_difference_tokens",[39]),("cropped_vs_registered_difference_tokens",[1,1])):
   row=self.record(39);row[key]=value
   with self.assertRaises(ValueError):self.consumer()(row,39)
 def test_exact_stage_gates_and_cropped_rank_not_acceptance(self):
  node=self.function("independent_oracle.py","source_legality");text=ast.unparse(node)
  equal=[n for n in ast.walk(node) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="equal"]
  self.assertEqual(len(equal),2)
  self.assertIn("torch.equal(score, witness_score[:, :n])",text);self.assertIn("torch.equal(ranking, witness_ranking[:n])",text)
  self.assertNotIn("torch.equal(cropped",text);self.assertNotIn("allclose",text)
class ExplicitUser72hRepairClock(unittest.TestCase):
 def test_old_manifest_without_new_clock_and_extended_epoch_rejected(self):
  from receipt import validate_cutoff_fields,EXECUTION_CLOCK
  old={"paper_cutoff":"2026-10-08T19:00:00Z","portfolio_cutoff":"2026-10-09T11:17:31Z"}
  with self.assertRaises(ValueError):validate_cutoff_fields(old)
  for field,value in (("repair_cutoff_epoch",1791615626),("total_cutoff_epoch",1791788426),("owner","old-ba508")):
   changed=dict(EXECUTION_CLOCK);changed[field]=value
   with self.assertRaises(ValueError):validate_cutoff_fields(dict(old,execution_clock=changed))
 def test_actual_protocol_source_binding_and_same_budget(self):
  from pathlib import Path
  import receipt
  from unittest.mock import patch
  original=__import__("json").loads(Path(receipt.USER_TIME_PROTOCOL["path"]).read_bytes())
  with patch.object(receipt,"load",return_value=original) as observed:
   self.assertEqual(receipt.execution_clock(),receipt.EXECUTION_CLOCK)
   observed.assert_called_once_with(receipt.USER_TIME_PROTOCOL)
  changed=dict(original,first_candidate_repair_cutoff_epoch=1791615626)
  with patch.object(receipt,"load",return_value=changed):
   with self.assertRaises(ValueError):receipt.execution_clock()
  source=receipt.source_identity
  self.assertIn("execution_clock()",__import__("inspect").getsource(source))
  import host
  self.assertEqual(host.PHASE_SECONDS,5400);self.assertEqual(host.CLEANUP_SECONDS,90)
  self.assertEqual(host.MEM,8*1024**3);self.assertEqual(host.HOST_MEM,256*1024**2);self.assertEqual(host.RESERVE,8*1024**3)

if __name__=="__main__":unittest.main()

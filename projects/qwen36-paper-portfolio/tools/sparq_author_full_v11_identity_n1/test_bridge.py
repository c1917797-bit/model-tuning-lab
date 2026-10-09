"""Actual stdlib control/source regressions ONLY, no simulated model numerical PASS."""
import ast,copy,os,types,unittest
from pathlib import Path
from unittest.mock import patch
import common as c,bridge,lifecycle,workspace_budget as budget,source_contract as sc
class CommonAndLifecycle(unittest.TestCase):
 def test_default_off_no_runtime_import(self):
  import sys
  with patch.dict(os.environ,{"QWEN36_SPARQ_STOCK_FULL_ENABLED":"0"}):
   self.assertEqual(bridge.install_from_env(),dict(default_enabled=False,model_executed=False,model_ready=False))
  self.assertNotIn("torch",sys.modules);self.assertNotIn("torch_npu",sys.modules)
 def test_common_both_arms_stock_full_no_eager_tax(self):
  for arm in ("dense","candidate"):self.assertFalse(c.validate(copy.deepcopy(c.COMMON),arm)["model_ready"])
  for key,bad in (("enforce_eager",True),("kv_cache_memory_bytes",12*1024**3),("enable_prefix_caching",True)):
   v=copy.deepcopy(c.COMMON);v[key]=bad
   for arm in ("dense","candidate"):
    with self.assertRaises(ValueError):c.validate(v,arm)
  for field,bad in (("cudagraph_mode","PIECEWISE"),("cudagraph_capture_sizes",[1,2,16]),("cudagraph_num_of_warmups",0)):
   v=copy.deepcopy(c.COMMON);v["compilation_config"][field]=bad
   with self.assertRaises(ValueError):c.validate(v,"candidate")
  v=copy.deepcopy(c.COMMON);v["additional_config"]["pa_shape_list"]=[]
  with self.assertRaises(ValueError):c.validate(v,"dense")
 def test_all_batch_rows_reorder_and_finished_reuse(self):
  for batch in range(1,17):
   book=lifecycle.RequestLedger()
   rows=[dict(rid="r%d"%i,object_id=i+100,computed=1000+i,scheduled=1) for i in range(batch)]
   first=book.prepare(rows);self.assertEqual(len(book.decode([1001+i for i in range(batch)])),batch)
   reordered=[dict(row,computed=row["computed"]+1) for row in rows[::-1]]
   second=book.prepare(reordered);book.decode([row["computed"]+1 for row in reordered])
   leases={r["rid"]:(r["generation"],r["slot"]) for r in first}
   self.assertEqual(leases,{r["rid"]:(r["generation"],r["slot"]) for r in second})
   book.finish(["r0"]);third=book.prepare([dict(rid="r0",object_id=99999,computed=1,scheduled=1)])
   self.assertEqual(third[0]["generation"],2);self.assertEqual(third[0]["slot"],0)
   self.assertEqual(book.decode([2])[0]["native_length"],2)
 def test_ABA_rollback_duplicate_and_mixed_decode_reject(self):
  book=lifecycle.RequestLedger();book.prepare([dict(rid="a",object_id=1,computed=3,scheduled=1)])
  for rows in ([dict(rid="a",object_id=2,computed=3,scheduled=1)],
               [dict(rid="a",object_id=1,computed=2,scheduled=1)],
               [dict(rid="a",object_id=1,computed=3,scheduled=1)]*2):
   with self.assertRaises(ValueError):book.prepare(rows)
  book.prepare([dict(rid="a",object_id=1,computed=4,scheduled=2)])
  with self.assertRaises(ValueError):book.decode([6])
 def test_paused_slots_never_stolen(self):
  book=lifecycle.RequestLedger();book.prepare([dict(rid="r%d"%i,object_id=i+1,computed=1,scheduled=1) for i in range(16)])
  with self.assertRaises(ValueError):book.prepare([dict(rid="new",object_id=100,computed=1,scheduled=1)])
 def test_ledger_is_exact_pinned_original(self):
  path=next(p for p in sc.PINS if p.endswith("/model_bridge.py"))
  original=next(n for n in ast.parse(Path(path).read_text()).body if isinstance(n,ast.ClassDef) and n.name=="RequestLedger")
  current=next(n for n in ast.parse(Path(lifecycle.__file__).read_text()).body if isinstance(n,ast.ClassDef))
  self.assertEqual(ast.dump(current,include_attributes=False),ast.dump(original,include_attributes=False))
 def test_model_permission_rejects_real_failed_component_before_Torch(self):
  ref=dict(path="/cache/cch/qwen36-paper-preparation-20261007/sparse/MAIN-sparq-v6-009-002-native-20261008-001/gate/REPORT.json",
   sha256="f3bf94122b432a15e138ab7c595d66e4d8f0aa79264d2f9bf83b28a725f5907d")
  with self.assertRaises(ValueError):sc.actual_component(ref["path"],ref["sha256"])
  import sys;self.assertNotIn("torch",sys.modules)
class BudgetAndActualSources(unittest.TestCase):
 def source(self,key):
  return Path(next(p for p in sc.PINS if p.endswith("/"+key))).read_text()
 def test_all_buckets_guarded_not_numeric18page(self):
  total=sum(budget.guarded_bytes(b,320) for b in range(1,17))*16
  self.assertGreater(total,budget.guarded_bytes(16,18)*16)
  self.assertLess(total+budget.transient_ceiling(16,320),c.AUX_CEILING)
  with self.assertRaises(ValueError):budget.guarded_bytes(1,321)
 def test_actual_peak_and_cumulative_failclosed(self):
  baseline=40*1024**3
  budget.admission(0,1,320,baseline,baseline,baseline)
  for used,current,peak in ((c.AUX_CEILING,baseline,baseline),(0,baseline+c.AUX_CEILING+1,baseline+c.AUX_CEILING+1),(0,baseline,baseline+c.AUX_CEILING+1)):
   with self.assertRaises(ValueError):budget.admission(used,16,320,current,baseline,peak)
 def test_baseline_not_profile_and_preallocate_outside_capture(self):
  src=Path(bridge.__file__).read_text()
  self.assertIn("self.baseline_allocated=None",src)
  self.assertIn("self.dummy_depth>0 and not capturing",src)
  self.assertLess(src.index("budget.admission(existing"),src.index("ws=self.core.GraphTokenWorkspace"))
  self.assertIn("common.SCREEN_PAGES<=pages<=320",src)
  self.assertIn("CPU PA context prepared BEFORE GLOBAL graph capture",src)
  self.assertLess(src.index("ws.native_pa.set_lengths([r.SEQ_LEN_WITH_MAX_PA_WORKSPACE]"),src.index('got=originals["_dummy_run"](runner,*args,**kwargs)'))
  self.assertIn("real replay native metadata pointers/stride/layout",src)
  self.assertIn('if mode=="formal":',src)
  self.assertIn("consume_authority(",src)
 def test_actual_stock_pa_selector_route_two_arm_source(self):
  src=self.source("ascend_attention_utils.py")
  self.assertIn("FULL_DECODE_ONLY",src);self.assertIn("pa_shape_list",src)
  asc=self.source("ascend_config.py");self.assertIn('additional_config.get("pa_shape_list", [])',asc)
  config=self.source("compilation.py");self.assertIn("FULL_DECODE_ONLY = (FULL, NONE)",config)
 def test_original_cache_writer_before_impl(self):
  tree=ast.parse(self.source("attention_v1.py"));cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=="AscendAttentionBackendImpl")
  fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=="forward")
  calls=[n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
  writes=[n.lineno for n in calls if n.func.attr=="reshape_and_cache"];reads=[n.lineno for n in calls if n.func.attr=="forward_impl"]
  self.assertEqual(len(writes),1);self.assertLess(writes[0],min(reads))
  current=Path(bridge.__file__).read_text();self.assertIn("return original_outer(impl,layer,*args,**kwargs)",current)
  self.assertNotIn("DeviceOperator.reshape_and_cache(",current)
 def test_actual_stock_replay_then_update_not_reordered(self):
  tree=ast.parse(self.source("model_runner_v1.py"))
  cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=="NPUModelRunner")
  fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=="_model_forward")
  branch=next(n for n in fn.body if isinstance(n,ast.If) and ast.unparse(n.test)=="self.enable_enpu")
  calls=[n for st in branch.orelse for n in ast.walk(st) if isinstance(n,ast.Call)]
  replay=min(n.lineno for n in calls if isinstance(n.func,ast.Name) and n.func.id=="run_model")
  update=min(n.lineno for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr=="_update_full_graph_params_if_needed")
  self.assertLess(replay,update)
  acl=self.source("acl_graph.py");self.assertIn("graph.replay()",acl);self.assertIn("current_stream().synchronize()",acl)
 def test_actual_capture_warmup_and_cpu_device_lengths(self):
  gpu=self.source("gpu_model_runner.py");runner=self.source("model_runner_v1.py");attention=self.source("attention_v1.py")
  self.assertIn("cudagraph_num_of_warmups",gpu);self.assertIn("CUDAGraphMode.NONE",gpu)
  tree=ast.parse(gpu);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=="GPUModelRunner")
  fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=="_warmup_and_capture")
  assign=next(n for n in fn.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="force_attention" for t in n.targets))
  self.assertEqual(ast.unparse(assign.value),"cudagraph_runtime_mode == CUDAGraphMode.FULL")
  calls=[n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="_dummy_run"]
  self.assertEqual(len(calls),2)
  keywords=[{k.arg:ast.unparse(k.value) for k in n.keywords} for n in calls]
  self.assertTrue(all(x["uniform_decode"]=="desc.uniform" for x in keywords))
  warmup=next(x for x in keywords if x.get("force_attention")=="force_attention")
  capture=next(x for x in keywords if x.get("is_graph_capturing")=="True")
  self.assertEqual(warmup["cudagraph_runtime_mode"],"CUDAGraphMode.NONE")
  self.assertEqual(capture["cudagraph_runtime_mode"],"cudagraph_runtime_mode")
  self.assertIn("optimistic_seq_lens",runner);self.assertIn("seq_lens_list",attention)
  self.assertIn("SEQ_LEN_WITH_MAX_PA_WORKSPACE = 6144",runner)
  self.assertIn("ws.lengths.detach().cpu().tolist()==host",Path(bridge.__file__).read_text())
  current=Path(bridge.__file__).read_text()
  self.assertIn("self.runner.seq_lens[:batch]",current)
  self.assertNotIn(".seq_lens.to(",current)
 def test_formal_trace_not_enabled_by_source_helper(self):
  src=Path(bridge.__file__).read_text()
  self.assertLess(src.index("authority=c.actual_component"),src.index("import torch,torch_npu"))
  self.assertIn('if mode=="formal":',src)
  self.assertIn("consume_authority(",src)
  self.assertIn("async_numerical_pass=False",src)
  self.assertNotIn("native_PA_executed=True",src)
if __name__=="__main__":unittest.main()

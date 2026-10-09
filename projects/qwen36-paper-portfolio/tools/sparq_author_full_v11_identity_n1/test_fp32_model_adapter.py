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

class EffectiveAscendCommon(unittest.TestCase):
 """Real common callable and installed-source byte contracts; not NPU evidence."""
 def fixture(self):
  from types import SimpleNamespace as S
  class DecodeOnly:
   def decode_mode(self):return "FULL"
   def mixed_mode(self):return "NONE"
  mode=DecodeOnly();Mode=S(FULL_DECODE_ONLY=mode,FULL="FULL",NONE="NONE")
  cc=S(cudagraph_mode=mode,cudagraph_capture_sizes=list(range(1,17)),cudagraph_num_of_warmups=1)
  pc=S(tensor_parallel_size=4,data_parallel_size=1)
  r=S(vllm_config=S(compilation_config=cc,parallel_config=pc),model_config=S(enforce_eager=False),
   max_num_reqs=16,speculative_config=None,lora_config=None,use_cp=False,use_async_scheduling=False,
   enable_enpu=False,use_sparse=False,use_compress=False)
  return r,Mode,S(pa_shape_list=list(range(1,17)))
 def test_requested_common_two_same_arms_unchanged(self):
  import common
  self.assertEqual(common.COMPILATION["cudagraph_num_of_warmups"],2)
  self.assertIs(common.COMMON["compilation_config"],common.COMPILATION)
  for arm in ("dense","candidate"):
   self.assertTrue(common.validate(copy.deepcopy(common.COMMON),arm)["source_policy_checked"])
  self.assertEqual((common.COMMON["max_model_len"],common.COMMON["max_num_seqs"]),(40960,16))
 def test_effective_official_one_actual_validator(self):
  import common
  self.assertIs(common.validate_runner(*self.fixture()),True)
  self.assertEqual(common.ASCEND_EFFECTIVE_WARMUPS,1)
 def test_requested_two_cannot_be_runtime_substitute(self):
  import common
  r,Mode,asc=self.fixture();r.vllm_config.compilation_config.cudagraph_num_of_warmups=2
  with self.assertRaisesRegex(ValueError,"cudagraph_num_of_warmups"):
   common.validate_runner(r,Mode,asc)
 def test_noncanonical_effective_counts_fail_closed(self):
  import common
  for value in (0,2,3,True,1.0,None,float("nan"),float("inf")):
   with self.subTest(value=repr(value)):
    r,Mode,asc=self.fixture();r.vllm_config.compilation_config.cudagraph_num_of_warmups=value
    with self.assertRaisesRegex(ValueError,"cudagraph_num_of_warmups"):common.validate_runner(r,Mode,asc)
 def test_all_other_original_runtime_predicates_independent(self):
  import common
  cases=(("model_config.enforce_eager",True,"enforce_eager"),
   ("vllm_config.compilation_config.cudagraph_mode","EAGER","cudagraph_mode"),
   ("vllm_config.compilation_config.cudagraph_capture_sizes",list(range(1,16)),"cudagraph_capture_sizes"),
   ("vllm_config.parallel_config.tensor_parallel_size",2,"tensor_parallel_size"),
   ("vllm_config.parallel_config.data_parallel_size",2,"data_parallel_size"),
   ("max_num_reqs",15,"max_num_reqs"),("speculative_config",{},"speculative_config"),
   ("lora_config",{},"lora_config"),("use_cp",True,"use_cp"),("use_async_scheduling",True,"use_async_scheduling"),
   ("enable_enpu",True,"enable_enpu"),("use_sparse",True,"use_sparse"),("use_compress",True,"use_compress"))
  for path,value,field in cases:
   with self.subTest(field=field):
    r,Mode,asc=self.fixture();owner=r;parts=path.split(".")
    for part in parts[:-1]:owner=getattr(owner,part)
    setattr(owner,parts[-1],value)
    with self.assertRaisesRegex(ValueError,field):common.validate_runner(r,Mode,asc)
  r,Mode,asc=self.fixture();asc.pa_shape_list=list(range(1,16))
  with self.assertRaisesRegex(ValueError,"pa_shape_list"):common.validate_runner(r,Mode,asc)
 def test_missing_runtime_facts_fail_with_field_name(self):
  import common
  for field in ("max_num_reqs","speculative_config","lora_config","use_cp","use_async_scheduling","enable_enpu","use_sparse","use_compress"):
   with self.subTest(field=field):
    r,Mode,asc=self.fixture();delattr(r,field)
    with self.assertRaisesRegex(ValueError,"missing field "+field):common.validate_runner(r,Mode,asc)
  r,Mode,asc=self.fixture();del r.vllm_config.compilation_config.cudagraph_num_of_warmups
  with self.assertRaisesRegex(ValueError,"missing field cudagraph_num_of_warmups"):common.validate_runner(r,Mode,asc)
 def test_FULL_decode_and_NONE_mixed_each_required(self):
  import common
  for name in ("decode_mode","mixed_mode"):
   with self.subTest(field=name):
    r,Mode,asc=self.fixture();setattr(r.vllm_config.compilation_config.cudagraph_mode,name,lambda:"PIECEWISE")
    with self.assertRaisesRegex(ValueError,"cudagraph_mode."+name):common.validate_runner(r,Mode,asc)
 def test_all16_capture_and_PA_order_exact_no_subset(self):
  import common
  for values in ([],list(range(16,0,-1)),[1]*16,list(range(1,18)),None):
   for field in ("cudagraph_capture_sizes","pa_shape_list"):
    with self.subTest(field=field,values=values):
     r,Mode,asc=self.fixture()
     setattr(r.vllm_config.compilation_config if field=="cudagraph_capture_sizes" else asc,field,values)
     with self.assertRaisesRegex(ValueError,field):common.validate_runner(r,Mode,asc)
 def test_enforce_eager_identity_false_stays_strict(self):
  import common
  for value in (0,None,True,"false"):
   r,Mode,asc=self.fixture();r.model_config.enforce_eager=value
   with self.assertRaisesRegex(ValueError,"enforce_eager"):common.validate_runner(r,Mode,asc)
 def test_actual_official_platform_normalization_source_and_AST(self):
  import common
  path=Path(common.ASCEND_PLATFORM_SOURCE);c.bound(path,common.ASCEND_PLATFORM_SHA)
  tree=ast.parse(path.read_text());functions=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=="check_and_update_config"]
  self.assertEqual(len(functions),1)
  # Assignment is a direct method-body statement, not a speculative nested branch.
  assignments=[n for n in functions[0].body if isinstance(n,ast.Assign) and any(
   isinstance(t,ast.Attribute) and isinstance(t.value,ast.Name) and t.value.id=="compilation_config" and
   t.attr=="cudagraph_num_of_warmups" for t in n.targets)]
  self.assertEqual(len(assignments),1);self.assertEqual(assignments[0].lineno,533)
  self.assertIsInstance(assignments[0].value,ast.Constant);self.assertEqual(assignments[0].value.value,1)
  self.assertEqual(c.PINS[str(path)],common.ASCEND_PLATFORM_SHA)
  self.assertEqual(c.RUNTIME_PINS[common.ASCEND_PLATFORM_RUNTIME],common.ASCEND_PLATFORM_SHA)
 def test_same660_archive_binding_and_actual_N1_source_closure(self):
  import common,json
  receipt=str(Path(common.ASCEND_PLATFORM_SOURCE).parent/"COPY_IDENTITY.json")
  x=c.obj(dict(path=receipt,sha256=c.PINS[receipt]))
  before=json.loads(x["before"]["stdout"]);after=json.loads(x["after"]["stdout"])
  self.assertEqual((x["before"]["exit"],x["after"]["exit"]),(0,0))
  self.assertEqual((len(before),len(after)),(1,1))
  cid="cdd4a68f2049edc2382992893dbad45503015647afb2e5e1aeea1c51a1882abb"
  for row in (before[0],after[0]):
   self.assertEqual(row["Id"],cid)
   self.assertEqual(row["Image"],"sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1")
   self.assertIs(row["State"]["Running"],False);self.assertEqual(row["State"]["Pid"],0)
   self.assertIs(row["State"]["OOMKilled"],False);self.assertFalse(row.get("ExecIDs"))
   self.assertEqual(row["HostConfig"].get("Devices",[]),[])
  self.assertEqual(before[0]["State"],after[0]["State"])
  value=x["sources"]["ascend_platform.py"]
  self.assertEqual((value["runtime_path"],value["bytes"],value["sha256"]),
   (common.ASCEND_PLATFORM_RUNTIME,62514,common.ASCEND_PLATFORM_SHA))
  self.assertEqual(value["copy"]["exit"],0)
  self.assertIn(cid+":"+common.ASCEND_PLATFORM_RUNTIME,value["copy"]["argv"])
  mf=c.obj(dict(path=str(ROOT/"SOURCE_MANIFEST.json"),sha256=c.sha(ROOT/"SOURCE_MANIFEST.json")))
  self.assertEqual(mf["source_pins"],c.PINS);self.assertEqual(mf["runtime_pins"],c.RUNTIME_PINS)
  self.assertEqual(mf["source_count"],len(c.OWN)+len(c.PINS)+len(c.HOST_DEPENDENCIES))
  self.assertEqual(mf["source_count"],140)
  self.assertEqual(len(mf["runtime_pins"]),32)
  # Real N1 still delegates installed-byte validation before model allocation.
  n1=ast.parse(source("identity_bridge.py"))
  gate=next(n for n in n1.body if isinstance(n,ast.FunctionDef) and n.name=="n1_dependency_gate")
  self.assertTrue(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and
   isinstance(n.func.value,ast.Name) and n.func.value.id=="c" and n.func.attr=="runtime_sources" for n in ast.walk(gate)))
  runtime=next(n for n in ast.parse(source("source_contract.py")).body if isinstance(n,ast.FunctionDef) and n.name=="runtime_sources")
  self.assertTrue(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and
   isinstance(n.func.value,ast.Name) and n.func.value.id=="RUNTIME_PINS" and n.func.attr=="items" for n in ast.walk(runtime)))
 def test_clean_I_actual_common_entry_without_runtime_modules(self):
  import json,subprocess,sys,tempfile
  code=r"""
import json,runpy,sys
from types import SimpleNamespace as S
m=runpy.run_path(sys.argv[1])
class DecodeOnly:
 def decode_mode(self):return "FULL"
 def mixed_mode(self):return "NONE"
mode=DecodeOnly();Mode=S(FULL_DECODE_ONLY=mode,FULL="FULL",NONE="NONE")
cc=S(cudagraph_mode=mode,cudagraph_capture_sizes=list(range(1,17)),cudagraph_num_of_warmups=1)
r=S(vllm_config=S(compilation_config=cc,parallel_config=S(tensor_parallel_size=4,data_parallel_size=1)),
 model_config=S(enforce_eager=False),max_num_reqs=16,speculative_config=None,lora_config=None,use_cp=False,
 use_async_scheduling=False,enable_enpu=False,use_sparse=False,use_compress=False)
asc=S(pa_shape_list=list(range(1,17)))
assert m["validate_runner"](r,Mode,asc) is True
for arm in ("dense","candidate"):assert m["validate"](m["COMMON"],arm)["source_policy_checked"]
cc.cudagraph_num_of_warmups=2
try:m["validate_runner"](r,Mode,asc)
except ValueError as e:
 assert "cudagraph_num_of_warmups" in str(e);rejected=True
else:raise AssertionError("requested2 accepted as runtime")
assert not any(k=="torch" or k.startswith(("torch.","torch_npu","vllm")) for k in sys.modules)
print(json.dumps(dict(requested=2,effective=1,wrong_effective_rejected=rejected,source_only=True,npu_executed=False)))
"""
  with tempfile.TemporaryDirectory() as cwd:
   r=subprocess.run([sys.executable,"-I","-B","-c",code,str(ROOT/"common.py")],cwd=cwd,
    env=dict(__import__("os").environ,PYTHONPATH=""),capture_output=True,text=True,timeout=20)
  self.assertEqual(r.returncode,0,r.stderr)
  self.assertEqual(json.loads(r.stdout),dict(requested=2,effective=1,wrong_effective_rejected=True,source_only=True,npu_executed=False))
if __name__=="__main__":unittest.main()

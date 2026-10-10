"""Real immutable JSON-file fixtures for the independent ABI rejoin, not NPU evidence."""
import copy,hashlib,importlib.util,json,sys,tempfile,types,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
def load(n):
 s=importlib.util.spec_from_file_location("_mixed_abi_consume_"+n,HERE/(n+".py"))
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
C=load("consume_whole_cpu");L=load("loader")
class Independent(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  self.source=dict(path="/fixture/source.json",bytes=1,sha256="a"*64)
  self.recipe_ref=dict(path="/fixture/recipe.json",bytes=1,sha256="b"*64)
  self.recipe=dict(diagnostic_root=str(self.root))
  self.result=dict(worker_first_fault_refs=[],worker_first_fault=None)
  self.ids=[dict(pid=100+i,start_ticks=200+i,cgroup="fixture")for i in range(4)]
  self.rows=[];self.canary=[]
  for rank in range(4):
   proof=dict(schema="kivi.actual-rank-driver-properties/v1",logical_rank=rank,current_device=rank,
    helper_source=dict(path="/vllm-workspace/vllm-ascend/vllm_ascend/ops/triton/triton_utils.py",bytes=2090,sha256=C.ABI_HELPER_SHA),
    device_properties=dict(num_aicore=7,num_vectorcore=13),raw_properties_repr="{'fixture_only': True}",
    driver_type_module="fixture",driver_type_name="FixtureDriver",source_api=C.ABI_SOURCE_API,
    model_ready=False,performance_ready=False,run_authority=False)
   self.rows.append(dict(proof,source_ref=self.source,recipe_ref=self.recipe_ref,identity=self.ids[rank]))
   self.canary.append(dict(logical=rank,physical=rank+4,actual_driver_properties=copy.deepcopy(proof)))
  self.ctx=types.SimpleNamespace(core=L,producer=self.source)
 def write(self):
  for i,q in enumerate(self.rows):
   p=self.root/("DRIVER-PROPERTIES-r%d.json"%i)
   with p.open("xb")as f:f.write((json.dumps(q,sort_keys=True)+"\n").encode())
 def consume(self):
  self.write()
  return C.capture_abi(self.ctx,self.result,self.recipe,self.recipe_ref,self.ids,self.canary)
 def test_complete_real_files_rejoined_all4_no_model_permission(self):
  refs=self.consume();self.assertEqual(len(refs),4)
  for i,r in enumerate(refs):
   self.assertEqual(L.obj(r),self.rows[i]);self.assertFalse(L.obj(r)["model_ready"])
 def test_bad_counts_no_boolean_alias_or_fallback(self):
  for v in(True,0,-1,65536,7.0,None):
   q=copy.deepcopy(self.rows[0]);q["device_properties"]["num_aicore"]=v
   with self.assertRaises(ValueError):C.driver_record(q,0)
 def test_rank_or_helper_source_mismatch_rejected(self):
  for k,v in(("current_device",1),("logical_rank",True)):
   q=copy.deepcopy(self.rows[0]);q[k]=v
   with self.assertRaises(ValueError):C.driver_record(q,0)
  q=copy.deepcopy(self.rows[0]);q["helper_source"]["sha256"]="0"*64
  with self.assertRaises(ValueError):C.driver_record(q,0)
 def test_missing_actual_worker_file_not_promoted(self):
  self.write();self.rows[3]["source_ref"]=dict(self.source)
  # Missing-file fixture is an explicit separate recipe root, never a real failed raw deletion.
  self.recipe["diagnostic_root"]=str(self.root/"not-created")
  with self.assertRaises(FileNotFoundError):C.capture_abi(self.ctx,self.result,self.recipe,self.recipe_ref,self.ids,self.canary)
 def test_preserved_FATAL_or_summary_fault_excludes_success(self):
  self.write()
  with(self.root/"RANK-2-FATAL.json").open("xb")as f:f.write(b'{"fixture_failure":true}\n')
  with self.assertRaisesRegex(ValueError,"fatal excludes"):C.capture_abi(self.ctx,self.result,self.recipe,self.recipe_ref,self.ids,self.canary)
  self.result["worker_first_fault"]={"primary":"fixture"}
  with self.assertRaisesRegex(ValueError,"first worker fault"):C.capture_abi(self.ctx,self.result,self.recipe,self.recipe_ref,self.ids,self.canary)
 def test_foreign_worker_identity_rejected(self):
  self.rows[2]["identity"]=dict(self.ids[2],pid=999)
  with self.assertRaisesRegex(ValueError,"initialized worker"):self.consume()
 def test_N1_worker_count_disagreement_rejected(self):
  self.canary[1]["actual_driver_properties"]["device_properties"]["num_vectorcore"]=17
  with self.assertRaisesRegex(ValueError,"same actual N1"):self.consume()
 def test_foreign_source_recipe_rejected(self):
  self.rows[3]["recipe_ref"]=dict(self.recipe_ref,sha256="0"*64)
  with self.assertRaisesRegex(ValueError,"initialized worker"):self.consume()
 def test_ABI_permission_flag_cannot_pass(self):
  q=copy.deepcopy(self.rows[0]);q["model_ready"]=True
  with self.assertRaisesRegex(ValueError,"not model success"):C.driver_record(q,0)
if __name__=="__main__":unittest.main(verbosity=2)

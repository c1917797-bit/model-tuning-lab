"""012 driver/FATAL consumer regressions using exact producer expressions/files.
Fixture-only: no driver/Torch/NPU/controller command executes.
"""
import ast,copy,hashlib,importlib.util,json,sys,tempfile,types,unittest
from pathlib import Path
CORE=None
PRODUCER_ARCHIVE=None
COMMON=None
class ActualDriverConsumer(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.n=0
  self.cid="a"*64
  self.m=json.loads((PRODUCER_ARCHIVE/"SOURCE_MANIFEST.json").read_bytes())
  self.source=dict(path=CORE.PRODUCER_ROOT+"/SOURCE_MANIFEST.json",bytes=CORE.PRODUCER_BYTES,sha256=CORE.PRODUCER_SHA)
  self.own={Path(r["path"]).name:r for r in self.m["files"]}
  p,wire=self.original("runtime_boundary.py")
  spec=importlib.util.spec_from_file_location("_whole012_boundary_fixture_"+str(id(self)),p)
  self.boundary=importlib.util.module_from_spec(spec);exec(compile(wire,str(p),"exec"),self.boundary.__dict__)
  self.identities=[dict(pid=i+123,start_ticks=i+456,cgroup="7:memory:/docker/"+self.cid)for i in range(4)]
  self.recipe=dict(container_id=self.cid,diagnostic_root=str(self.root),
   rank_request_paths={str(i):str(self.root/("ACTUAL_OWNER_REQUEST-r%d.json"%i))for i in range(4)})
  self.rr=self.publish(self.root/"recipe.json",self.recipe)
  for rank,ident in enumerate(self.identities):
   self.publish(Path(self.recipe["rank_request_paths"][str(rank)]),dict(schema="kivi.actual-rank-owner-request/v1",
    rank=rank,source_ref=self.source,container_id=self.cid,identity=ident))
  self.ctx=types.SimpleNamespace(m=self.m,producer=self.source,own=self.own,runtime_boundary=self.boundary,
   c=types.SimpleNamespace(ref=CORE.ref,obj=CORE.obj))
  self.good=dict(worker_first_fault_refs=[],worker_first_fault=None)
 def tearDown(self):self.tmp.cleanup()
 def publish(self,path,value):
  with Path(path).open("xb")as stream:stream.write(json.dumps(value,allow_nan=False).encode()+b"\n")
  return CORE.ref(path)
 def original(self,name):
  row=self.own[name];path=PRODUCER_ARCHIVE/name;wire=path.read_bytes()
  self.assertEqual((len(wire),hashlib.sha256(wire).hexdigest()),(row["bytes"],row["sha256"]))
  return path,wire
 def proof(self,rank):
  # This is the actual frozen return expression; no retyped producer schema.
  path,wire=self.original("runtime_boundary.py")
  fn=next(n for n in ast.parse(wire).body if isinstance(n,ast.FunctionDef)and n.name=="core_properties")
  node=next(n for n in reversed(fn.body)if isinstance(n,ast.Return))
  helper=next(r for r in self.m["dependencies"]if r["path"]=="/cache/cch/vllm-ascend/vllm_ascend/ops/triton/triton_utils.py")
  raw={"num_aicore":7,"num_vectorcore":13,"fixture_only":True}
  active=types.SimpleNamespace()
  env=dict(props={k:raw[k]for k in("num_aicore","num_vectorcore")},source=copy.deepcopy(helper),rank=rank,text=repr(raw),
   triton=types.SimpleNamespace(runtime=types.SimpleNamespace(driver=types.SimpleNamespace(active=active))))
  props,value=eval(compile(ast.fix_missing_locations(ast.Expression(body=node.value)),str(path),"eval"),env)
  self.assertEqual(props,value["device_properties"]);return value
 def produce(self):
  # Evaluate actual N1 append and worker publication expressions.
  gp,gw=self.original("guest_probe.py");bt,bw=self.original("kivi_firstdecode_bootstrap.py")
  gtree=ast.parse(gw);btree=ast.parse(bw)
  n1=next(n for n in ast.walk(gtree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)
   and n.func.attr=="append"and isinstance(n.func.value,ast.Name)and n.func.value.id=="canary").args[0]
  worker=next(n for n in ast.walk(btree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)
   and n.func.attr=="publish"and any(isinstance(x,ast.Constant)and x.value=="DRIVER-PROPERTIES-r%d.json"for x in ast.walk(n)))
  records=[]
  for rank in range(4):
   proof=self.proof(rank)
   env=dict(device=rank,fmt=2,value=[4.,5.],driver_proof=proof)
   records.append(eval(compile(ast.fix_missing_locations(ast.Expression(body=n1)),str(gp),"eval"),env))
   env=dict(driver_proof=proof,source_ref=self.source,recipe_ref=self.rr,identity=self.identities[rank])
   value=eval(compile(ast.fix_missing_locations(ast.Expression(body=worker.args[1])),str(bt),"eval"),env)
   self.publish(self.root/("DRIVER-PROPERTIES-r%d.json"%rank),value)
  return records
 def consume(self,rows,result=None):
  return CORE.worker_driver_abi(self.ctx,self.recipe,self.rr,self.identities,rows,self.good if result is None else result)
 def mutate(self,rank,key,value):
  path=self.root/("DRIVER-PROPERTIES-r%d.json"%rank)
  row=json.loads(path.read_bytes());row[key]=value
  path.write_bytes(json.dumps(row).encode()+b"\n")
 def test_actual_N1_and_worker_publication_all4_consumed(self):
  rows=self.produce();refs=self.consume(rows)
  self.assertEqual(refs,[CORE.ref(self.root/("DRIVER-PROPERTIES-r%d.json"%i))for i in range(4)])
 def test_wrong_installed_helper_not_archive_alias(self):
  for change in(dict(path=self.m["runtime_abi_original_refs"]["helper"]["path"]),dict(bytes=True),dict(sha256="f"*64)):
   value=self.proof(0);value["helper_source"].update(change)
   with self.subTest(change=change),self.assertRaisesRegex(ValueError,"installed helper path"):
    CORE.driver_properties(value,0,self.m)
 def test_wrong_rank_current_device_and_bool_rejected(self):
  for key,value in(("logical_rank",1),("current_device",True),("current_device",2)):
   proof=self.proof(0);proof[key]=value
   with self.subTest(key=key,value=value),self.assertRaisesRegex(ValueError,"driver rank"):
    CORE.driver_properties(proof,0,self.m)
 def test_bounded_corecounts_no_guess_or_bool(self):
  for value in(True,0,65536,7.0,None):
   proof=self.proof(0);proof["device_properties"]["num_aicore"]=value
   with self.subTest(value=value),self.assertRaisesRegex(ValueError,"bounded integer"):
    CORE.driver_properties(proof,0,self.m)
 def test_driver_missing_unknown_or_promoted_fields_rejected(self):
  for key,value in(("source_api","torch.npu.get_device_properties"),("model_ready",True),("raw_properties_repr","")):
   proof=self.proof(0);proof[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):CORE.driver_properties(proof,0,self.m)
  proof=self.proof(0);proof["estimated_num_aicore"]=7
  with self.assertRaises(ValueError):CORE.driver_properties(proof,0,self.m)
 def test_worker_foreign_PID_start_CID_source_recipe_rejected(self):
  rows=self.produce();original=json.loads((self.root/"DRIVER-PROPERTIES-r0.json").read_bytes())
  for key,value in(("identity",dict(self.identities[0],pid=999)),("source_ref",{}),("recipe_ref",{})):
   self.mutate(0,key,value)
   with self.subTest(key=key),self.assertRaisesRegex(ValueError,"worker driver source"):self.consume(rows)
   (self.root/"DRIVER-PROPERTIES-r0.json").write_bytes(json.dumps(original).encode()+b"\n")
 def test_N1_worker_count_disagreement_rejected(self):
  rows=self.produce();self.mutate(0,"device_properties",dict(num_aicore=8,num_vectorcore=13))
  with self.assertRaisesRegex(ValueError,"same actual N1/worker"):self.consume(rows)
 def test_missing_fourth_worker_cannot_be_three_rank_success(self):
  rows=self.produce();(self.root/"DRIVER-PROPERTIES-r3.json").unlink()
  with self.assertRaises((ValueError,OSError)):self.consume(rows)
  with self.assertRaisesRegex(ValueError,"all four"):self.consume(rows[:3])
 def test_nonempty_RESULT_fatal_even_without_file_rejected(self):
  rows=self.produce()
  for changed in(dict(worker_first_fault={"primary":"original"}),dict(worker_first_fault_refs=[{"path":"original"}]),{}):
   result=dict(self.good,**changed)if changed else dict(worker_first_fault_refs=[])
   with self.subTest(changed=changed),self.assertRaisesRegex(ValueError,"never promote FATAL"):self.consume(rows,result)
 def test_real_original_Fatal_file_cannot_hide_behind_empty_RESULT(self):
  rows=self.produce();error=AttributeError("actual missing ABI fixture")
  def fail():raise error
  with self.assertRaises(AttributeError)as caught:
   self.boundary.initialize(fail,rank=1,recipe=self.recipe,recipe_ref=self.rr,source_ref=self.source,
    helper_ref=self.own["runtime_boundary.py"],identity=self.identities[1],publish=self.publish)
  self.assertIs(caught.exception,error)
  with self.assertRaises(self.boundary.WorkerFatal)as failure:self.consume(rows)
  raw=CORE.obj(failure.exception.worker_fault_refs[0])
  self.assertEqual(raw["identity"],self.identities[1]);self.assertEqual(raw["primary"]["type"],"AttributeError")
  self.assertEqual(failure.exception.worker_first_fault,raw)
 def test_Fatal_bad_original_owner_or_source_is_not_trusted(self):
  rows=self.produce()
  def fail():raise ValueError("first fixture")
  with self.assertRaises(ValueError):
   self.boundary.initialize(fail,rank=0,recipe=self.recipe,recipe_ref=self.rr,source_ref=self.source,
    helper_ref=self.own["runtime_boundary.py"],identity=dict(self.identities[0],start_ticks=999),publish=self.publish)
  with self.assertRaisesRegex(ValueError,"rank-owner request"):self.consume(rows)
 def test_actual_producer_fields_and_consumer_call_edges(self):
  hp,hw=self.original("host_run.py");tree=ast.parse(hw)
  result=next(n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=="dict"
   and any(k.arg=="worker_first_fault_refs"for k in n.keywords))
  self.assertEqual(next(k.value.id for k in result.keywords if k.arg=="worker_first_fault_refs"),"worker_fault_refs")
  self.assertEqual(next(k.value.id for k in result.keywords if k.arg=="worker_first_fault"),"worker_first_fault")
  core=ast.parse(Path(CORE.__file__).read_bytes())
  fn=next(n for n in core.body if isinstance(n,ast.FunctionDef)and n.name=="producer_only")
  calls=[n for n in ast.walk(fn)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)]
  self.assertEqual(sum(n.func.id=="reject_worker_fatal"for n in calls),1)
  self.assertEqual(sum(n.func.id=="worker_driver_abi"for n in calls),1)
  consume=next(n for n in core.body if isinstance(n,ast.FunctionDef)and n.name=="consume")
  self.assertTrue(any(isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=="raw_result"for n in ast.walk(consume)))

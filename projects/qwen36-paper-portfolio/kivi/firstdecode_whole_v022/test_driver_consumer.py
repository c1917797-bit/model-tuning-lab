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
  env=dict(props={k:raw[k]for k in("num_aicore","num_vectorcore")},source=dict(helper,path=CORE.DRIVER_HELPER_ORIGIN),rank=rank,text=repr(raw),
   triton=types.SimpleNamespace(runtime=types.SimpleNamespace(driver=types.SimpleNamespace(active=active))))
  props,value=eval(compile(ast.fix_missing_locations(ast.Expression(body=node.value)),str(path),"eval"),env)
  self.assertEqual(props,value["device_properties"]);return value
 def allocator(self,rank):
  # Execute the exact frozen producer row expression with inert counter values.
  # This is a wire/consumer fixture, never a live allocator or HBM measurement.
  path,wire=self.original("installer.py")
  outer=next(n for n in ast.parse(wire).body if isinstance(n,ast.FunctionDef)and n.name=="allocator_observer")
  snapshot=next(n for n in outer.body if isinstance(n,ast.FunctionDef)and n.name=="snapshot")
  row=next(n for n in snapshot.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=="row"for t in n.targets))
  keys=("allocated_bytes.all.current","allocated_bytes.all.peak","reserved_bytes.all.current","reserved_bytes.all.peak")
  env=dict(rank=rank,label="N1-AFTER-TINY",time=types.SimpleNamespace(time_ns=lambda:1791600000000000000),
   MEMORY_SHA="b489a7dc22b77d5f50b3329801fe64cb4c7f908cf2abaea75c0efbd7f4c436c1",
   source="/usr/local/python3.12.13/lib/python3.12/site-packages/torch_npu/npu/memory.py",
   keys=keys,values=dict(zip(keys,(111,222,333,444))))
  return eval(compile(ast.fix_missing_locations(ast.Expression(body=row.value)),str(path),"eval"),env)
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
   env=dict(device=rank,fmt=2,value=[4.,5.],driver_proof=proof,allocator_proof=self.allocator(rank))
   records.append(eval(compile(ast.fix_missing_locations(ast.Expression(body=n1)),str(gp),"eval"),env))
   env=dict(driver_proof=proof,source_ref=self.source,recipe_ref=self.rr,identity=self.identities[rank])
   value=eval(compile(ast.fix_missing_locations(ast.Expression(body=worker.args[1])),str(bt),"eval"),env)
   self.publish(self.root/("DRIVER-PROPERTIES-r%d.json"%rank),value)
  return CORE.obj(self.publish(self.root/'N1-original.json',records))
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

 def test_allocator_actual_N1_wire_roundtrip_all4(self):
  rows=self.produce();self.consume(rows)
  for rank,row in enumerate(rows):
   self.assertEqual(CORE.allocator_observation(row["allocator_observation"],rank,self.m),
    dict(zip(("allocated_bytes.all.current","allocated_bytes.all.peak","reserved_bytes.all.current","reserved_bytes.all.peak"),(111,222,333,444))))
 def test_allocator_missing_unknown_fields_rejected(self):
  for key in("bytes","stage"):
   row=self.allocator(0);del row[key]
   with self.subTest(key=key),self.assertRaisesRegex(ValueError,"diagnostic fields"):CORE.allocator_observation(row,0,self.m)
  row=self.allocator(0);row["estimated"]=1
  with self.assertRaisesRegex(ValueError,"diagnostic fields"):CORE.allocator_observation(row,0,self.m)
 def test_allocator_source_and_archive_alias_rejected(self):
  for key,value in(("source_sha256","f"*64),("runtime_path",next(r["path"]for r in self.m["dependencies"]if r["sha256"]==self.allocator(0)["source_sha256"]))):
   row=self.allocator(0);row[key]=value
   with self.subTest(key=key),self.assertRaisesRegex(ValueError,"installed allocator"):CORE.allocator_observation(row,0,self.m)
  m=copy.deepcopy(self.m);m["dependencies"]=[r for r in m["dependencies"]if r["sha256"]!=self.allocator(0)["source_sha256"]]
  with self.assertRaisesRegex(ValueError,"source dependency"):CORE.allocator_observation(self.allocator(0),0,m)
 def test_allocator_wrong_rank_stage_time_rejected(self):
  for key,value in(("rank",True),("rank",1),("stage","ALLOCATOR-GATHERED"),("time_ns",True),("time_ns",0)):
   row=self.allocator(0);row[key]=value
   with self.subTest(key=key,value=value),self.assertRaises(ValueError):CORE.allocator_observation(row,0,self.m)
 def test_allocator_counter_missing_bool_negative_rejected(self):
  for value in(True,-1,1.5,None):
   row=self.allocator(0);row["bytes"]["allocated_bytes.all.current"]=value
   with self.subTest(value=value),self.assertRaisesRegex(ValueError,"allocator counters"):CORE.allocator_observation(row,0,self.m)
  row=self.allocator(0);del row["bytes"]["reserved_bytes.all.peak"]
  with self.assertRaisesRegex(ValueError,"allocator counters"):CORE.allocator_observation(row,0,self.m)
 def test_allocator_no_physical_or_permission_promotion(self):
  for key in("physical_hbm","synchronized","peaks_reset","model_ready","run_authority","diagnostic_only"):
   row=self.allocator(0);row[key]=not row[key]
   with self.subTest(key=key),self.assertRaisesRegex(ValueError,"cannot authorize"):CORE.allocator_observation(row,0,self.m)

# Whole original N1 bytes, not a modeled helper origin or a driver execution.
ACTUAL_CANARY_REF=dict(path="/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-model-firstdecode-main-20261010-018/candidate/CANARY_N1.json",
 bytes=127423,sha256="0c2b63410a068f25ad92971aba5993421d26fcdb484b09145f7322325c6612f4")
class ActualInstalledDriverOrigin(unittest.TestCase):
 def actual(self):
  p=COMMON.OBSERVATION_ARCHIVE/"CANARY_N1.json"if COMMON.OBSERVATION_ARCHIVE is not None else Path(ACTUAL_CANARY_REF["path"])
  wire=p.read_bytes()
  self.assertEqual((len(wire),hashlib.sha256(wire).hexdigest()),
   (ACTUAL_CANARY_REF["bytes"],ACTUAL_CANARY_REF["sha256"]))
  m=json.loads((PRODUCER_ARCHIVE/"SOURCE_MANIFEST.json").read_bytes())
  self.assertEqual(hashlib.sha256((PRODUCER_ARCHIVE/"SOURCE_MANIFEST.json").read_bytes()).hexdigest(),CORE.PRODUCER_SHA)
  return CORE.decode(wire),m
 def test_actual_all4_installed_origin_and_driver_counts_consumed(self):
  raw,m=self.actual();rows=raw["canary"]
  self.assertEqual(raw["source"],dict(path=CORE.PRODUCER_ROOT+"/SOURCE_MANIFEST.json",bytes=CORE.PRODUCER_BYTES,sha256=CORE.PRODUCER_SHA))
  self.assertEqual(len(rows),4);self.assertEqual(raw["status"],"N1_ALL4_TINY_CHECKED")
  origins=[]
  for rank,row in enumerate(rows):
   proof=row["actual_driver_properties"]
   self.assertEqual(CORE.driver_properties(proof,rank,m),dict(num_aicore=20,num_vectorcore=40))
   origins.append(proof["helper_source"])
  self.assertTrue(all(r==origins[0]for r in origins))
  self.assertEqual(origins[0]["path"],CORE.DRIVER_HELPER_ORIGIN)
 def test_actual_unknown_cached_archive_and_noncanonical_origins_rejected(self):
  raw,m=self.actual();proof=raw["canary"][0]["actual_driver_properties"]
  for path in(m["runtime_abi_original_refs"]["helper"]["path"],
   "/cache/cch/vllm-ascend/vllm_ascend/ops/triton/triton_utils.py",
   "/unknown"+CORE.DRIVER_HELPER_ORIGIN,
   CORE.DRIVER_HELPER_ORIGIN.replace("/ops/","/ops/../ops/")):
   bad=copy.deepcopy(proof);bad["helper_source"]["path"]=path
   with self.subTest(path=path),self.assertRaisesRegex(ValueError,"installed helper path"):
    CORE.driver_properties(bad,0,m)
 def test_actual_origin_does_not_relax_sha_bytes_rank_or_dependency(self):
  raw,m=self.actual();proof=raw["canary"][0]["actual_driver_properties"]
  for key,value in(("bytes",True),("bytes",2091),("sha256","f"*64)):
   bad=copy.deepcopy(proof);bad["helper_source"][key]=value
   with self.subTest(key=key,value=value),self.assertRaisesRegex(ValueError,"installed helper path"):
    CORE.driver_properties(bad,0,m)
  with self.assertRaisesRegex(ValueError,"driver rank"):CORE.driver_properties(proof,1,m)
  bad=copy.deepcopy(m);bad["dependencies"]=[r for r in bad["dependencies"]if r!=bad["runtime_abi_original_refs"]["helper"]]
  with self.assertRaisesRegex(ValueError,"installed helper path"):CORE.driver_properties(proof,0,bad)

 def test_actual_all4_worker_originals_match_N1_recipe_and_namespace(self):
  raw,m=self.actual();base=COMMON.OBSERVATION_ARCHIVE
  result=COMMON.CurrentCwdAndOriginalMountOrder.actual(self,"RESULT.json")
  recipe_ref=result["npu"]["recipe"]
  self.assertEqual((recipe_ref["bytes"],recipe_ref["sha256"]),(5012,"9798f7557332382032756ad9001dfefea10292d088ab76533d504ba9fc614ed7"))
  rp=base/"RECIPE.json"if base is not None else Path(recipe_ref["path"])
  wire=rp.read_bytes();self.assertEqual((len(wire),hashlib.sha256(wire).hexdigest()),(recipe_ref["bytes"],recipe_ref["sha256"]))
  recipe=CORE.decode(wire);ns=COMMON.CurrentNativeTitleRepresentation.actual(self)
  hashes=("2363cfd8aea8e4796c9edbd3e99402bd7f97c5fffaaee75f02573d9dfaae5b59",
   "cdd9bef6f46e8c963bf96bf2680e1aa25f09cc8415d74fc6f37099e069119fc8",
   "3b499aeed759d2d7c568f32467d5d266976b9b176ed632ca550aab47cb5a959c",
   "376b78a4f1b78081cfc1e373662a6cef0eb6bf21a8c4d33d5a673de1adbdd2df")
  for rank,digest in enumerate(hashes):
   name="DRIVER-PROPERTIES-r%d.json"%rank
   path=base/name if base is not None else Path(recipe["diagnostic_root"])/name
   wire=path.read_bytes();self.assertEqual((len(wire),hashlib.sha256(wire).hexdigest()),(2210,digest))
   row=CORE.decode(wire)
   self.assertEqual(row["source_ref"],raw["source"]);self.assertEqual(row["recipe_ref"],recipe_ref)
   self.assertEqual(row["identity"],ns["host_processes"][rank+1]["guest_identity"])
   proof={k:v for k,v in row.items()if k not in("source_ref","recipe_ref","identity")}
   self.assertEqual(proof,raw["canary"][rank]["actual_driver_properties"])
   self.assertEqual(CORE.driver_properties(proof,rank,m),dict(num_aicore=20,num_vectorcore=40))


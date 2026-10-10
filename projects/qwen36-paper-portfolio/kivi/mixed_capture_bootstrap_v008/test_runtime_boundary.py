"""Actual source/API projection and real failure-file tests; never native proof."""
import ast,copy,hashlib,importlib.util,io,json,os,sys,tempfile,types,unittest
from pathlib import Path
from contextlib import ExitStack,redirect_stdout
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
ARCHIVE=os.environ.get("KIVI_RUNTIME_ABI_ARCHIVE_FIXTURE")
ANCESTOR=os.environ.get("KIVI_RUNTIME_ABI_ANCESTOR_FIXTURE")
def load(name):
 s=importlib.util.spec_from_file_location("_abi_tests_"+name,HERE/(name+".py"));m=importlib.util.module_from_spec(s)
 sys.modules[s.name]=m;s.loader.exec_module(m);return m
B=load("runtime_boundary");L=load("loader")
def exact_archive(name,sha):
 if ARCHIVE:p=Path(ARCHIVE)/name
 else:
  m=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
  rows=[v for v in m["runtime_abi_original_refs"].values()if Path(v["path"]).name==name and v["sha256"]==sha]
  if len(rows)!=1:raise ValueError("one exact runtime ABI source archive")
  p=Path(rows[0]["path"])
 b=p.read_bytes()
 if hashlib.sha256(b).hexdigest()!=sha:raise ValueError("exact real archive")
 return p,b
class Driver(unittest.TestCase):
 def runtime(self,raw=None,initialized=True,current=0,cache=None):
  calls=[];device=[current]
  npu=types.SimpleNamespace(is_initialized=lambda:initialized,device_count=lambda:4,current_device=lambda:device[0],
   get_device_properties=lambda *a:(_ for _ in ()).throw(AssertionError("wrong Torch API")))
  torch=types.SimpleNamespace(npu=npu)
  values={"num_aicore":7,"num_vectorcore":13,"fixture_only":True}if raw is None else raw
  def getter(rank):calls.append(rank);return copy.deepcopy(values)
  active=types.SimpleNamespace(utils=types.SimpleNamespace(get_device_properties=getter))
  triton=types.SimpleNamespace(runtime=types.SimpleNamespace(driver=types.SimpleNamespace(active=active)))
  path,wire=exact_archive("triton_utils.py",B.HELPER_SHA)
  rt=types.ModuleType(B.HELPER_NAME);rt.__file__=str(path);rt.HAS_TRITON=True
  rt.torch=torch;rt.triton=triton;rt._NUM_AICORE=-1;rt._NUM_VECTORCORE=-1
  tree=ast.parse(wire);nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)
   and n.name in("init_device_properties_triton","get_aicore_num","get_vectorcore_num")]
  exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),"exec"),rt.__dict__)
  if cache is not None:rt._NUM_AICORE,rt._NUM_VECTORCORE=cache
  return torch,triton,rt,calls,device
 def execute(self,torch,triton,rt,rank=0):
  with patch.object(B.importlib,"import_module",side_effect=lambda n:rt if n==B.HELPER_NAME else None):
   return B.core_properties(torch,triton,rank,L.ref)
 def test_actual018c_API_exact_path_and_original_helper(self):
  _,wire=exact_archive("numeric.py","7853f967eb44f32da3de785111adcb23ff01fc7cbe95e50dfb78a2c6ff18979a")
  def calls(tree):return [ast.dump(n)for n in ast.walk(tree)if isinstance(n,ast.Call)
   and isinstance(n.func,ast.Attribute)and n.func.attr=="get_device_properties"]
  self.assertEqual(calls(ast.parse(wire)),calls(ast.parse((HERE/"runtime_boundary.py").read_bytes())))
  torch,triton,rt,seen,_=self.runtime()
  props,proof=self.execute(torch,triton,rt)
  self.assertEqual(props,{"num_aicore":7,"num_vectorcore":13});self.assertEqual(seen,[0,0])
  self.assertEqual(proof["helper_source"],L.ref(rt.__file__));self.assertFalse(proof["model_ready"])
 def test_each_actual_current_rank_is_queried_without_Torch_property_object(self):
  torch,triton,rt,seen,device=self.runtime()
  for rank in range(4):
   device[0]=rank;props,proof=self.execute(torch,triton,rt,rank);self.assertEqual(proof["logical_rank"],rank)
  self.assertEqual(seen,[0,0,1,2,3])
 def test_missing_nonint_bool_zero_overflow_counts_no_fallback(self):
  for raw in({},{"num_aicore":True,"num_vectorcore":13},{"num_aicore":0,"num_vectorcore":13},
   {"num_aicore":65536,"num_vectorcore":13},{"num_aicore":7.0,"num_vectorcore":13},
   {"num_aicore":7,"num_vectorcore":None}):
   torch,triton,rt,seen,_=self.runtime(raw)
   with self.assertRaises((ValueError,AssertionError,TypeError)):self.execute(torch,triton,rt)
 def test_source_SHA_checked_before_driver_and_helper_calls(self):
  torch,triton,rt,seen,_=self.runtime()
  with patch.object(B.importlib,"import_module",return_value=rt):
   with self.assertRaisesRegex(ValueError,"same660 helper"):
    B.core_properties(torch,triton,0,lambda p:dict(path=str(p),bytes=2090,sha256="0"*64))
  self.assertEqual(seen,[])
 def test_original_cached_helper_disagreement_is_rejected_not_reset(self):
  torch,triton,rt,seen,_=self.runtime(cache=(11,17))
  with self.assertRaisesRegex(ValueError,"properties agree"):self.execute(torch,triton,rt)
  self.assertEqual((rt._NUM_AICORE,rt._NUM_VECTORCORE),(11,17))
 def test_uninitialized_wrong_rank_bool_rank_or_current_device_rejected(self):
  for initialized,current,rank in((False,0,0),(True,1,0),(True,0,True),(True,0,4)):
   torch,triton,rt,seen,_=self.runtime(initialized=initialized,current=current)
   with self.assertRaisesRegex(ValueError,"owned TP4"):self.execute(torch,triton,rt,rank)
   self.assertEqual(seen,[])
 def test_foreign_compiler_object_not_accepted(self):
  torch,triton,rt,seen,_=self.runtime();rt.triton=object()
  with self.assertRaisesRegex(ValueError,"compiler objects"):self.execute(torch,triton,rt)
  self.assertEqual(seen,[])
 def test_N1_only_checks_after_actual_tensor_sync_and_before_full_config(self):
  tree=ast.parse((HERE/"guest_probe.py").read_bytes());run=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=="run")
  loop=next(n for n in ast.walk(run)if isinstance(n,ast.For)and isinstance(n.target,ast.Name)and n.target.id=="device")
  getter=next(n for n in ast.walk(loop)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=="core_properties")
  sync=next(n for n in ast.walk(loop)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=="synchronize")
  self.assertGreater(getter.lineno,sync.lineno)
  branches=[n for n in run.body if isinstance(n,ast.If)and ast.dump(n.test)==ast.dump(ast.parse('mode == "n1"',mode="eval").body)]
  self.assertEqual(len(branches),1);self.assertIn(loop,list(ast.walk(branches[0])))
  self.assertNotIn("get_device_properties(rank)",(HERE/"kivi_mixed_bootstrap.py").read_text())

class Fatal(unittest.TestCase):
 def setup_io(self,root):
  c=load("model_contract");stack=ExitStack();self.addCleanup(stack.close)
  if os.name=="nt":
   sentinel=-90217
   def op(path,flags):
    return sentinel if Path(path).is_dir() else os.open(path,flags)
   view=types.SimpleNamespace(O_RDONLY=os.O_RDONLY,O_DIRECTORY=getattr(os,"O_DIRECTORY",0),
    open=op,fsync=lambda fd:None if fd==sentinel else os.fsync(fd),
    close=lambda fd:None if fd==sentinel else os.close(fd),link=os.link)
   stack.enter_context(patch.object(c,"os",view))
  source=c.write(root/"source.json",{"fixture":"source"});helper=c.ref(HERE/"runtime_boundary.py")
  identity=dict(pid=123,start_ticks=456,cgroup="0::/docker/"+("a"*64))
  requests={str(i):str(root/("owner%d.json"%i))for i in range(4)}
  recipe=dict(container_id="a"*64,diagnostic_root=str(root),rank_request_paths=requests)
  rr=c.write(root/"recipe.json",recipe)
  c.write(Path(requests["0"]),dict(schema="kivi.actual-rank-owner-request/v1",rank=0,
   source_ref=source,container_id=recipe["container_id"],identity=identity))
  args=dict(rank=0,recipe=recipe,recipe_ref=rr,source_ref=source,helper_ref=helper,identity=identity,publish=c.write)
  return c,args
 def fire(self,args,error):
  def invocation():raise error
  with self.assertRaises(type(error))as caught:B.initialize(invocation,**args)
  self.assertIs(caught.exception,error)
 def test_success_returns_same_original_object_no_files(self):
  with tempfile.TemporaryDirectory()as d:
   c,a=self.setup_io(Path(d));answer=object();self.assertIs(B.initialize(lambda:answer,**a),answer)
   self.assertFalse(B.fatal_path(a["recipe"],0).exists())
 def test_real_original_file_and_exception_preserved(self):
  with tempfile.TemporaryDirectory()as d:
   c,a=self.setup_io(Path(d));error=AttributeError("actual ABI fixture")
   self.fire(a,error);row=c.obj(c.ref(B.fatal_path(a["recipe"],0)))
   self.assertEqual(row["primary"]["type"],"AttributeError");self.assertIn("actual ABI fixture",row["primary"]["traceback"])
   self.assertEqual(row["identity"],a["identity"]);self.assertFalse(row["run_authority"])
 def test_existing_host_pure_read_gets_first_fault_separate_from_controller_error(self):
  with tempfile.TemporaryDirectory()as d:
   c,a=self.setup_io(Path(d));self.fire(a,AttributeError("missing property"))
   with self.assertRaises(B.WorkerFatal)as failure:
    B.raise_if_any(c,a["recipe"],a["recipe_ref"],a["source_ref"],a["helper_ref"])
   self.assertEqual(len(failure.exception.worker_fault_refs),1)
   self.assertEqual(failure.exception.worker_first_fault["primary"]["type"],"AttributeError")
   self.assertEqual(c.obj(failure.exception.worker_fault_refs[0]),failure.exception.worker_first_fault)
 def test_bad_recipe_source_or_helper_cannot_be_trusted_failure(self):
  for key in("recipe_ref","source_ref","helper_ref"):
   with tempfile.TemporaryDirectory()as d:
    c,a=self.setup_io(Path(d));self.fire(a,ValueError("fixture"))
    values=dict(a);values[key]=dict(path="/foreign",bytes=1,sha256="0"*64)
    with self.assertRaisesRegex(ValueError,"fatal source/recipe/rank"):
     B.raise_if_any(c,values["recipe"],values["recipe_ref"],values["source_ref"],values["helper_ref"])
 def test_wrong_original_rank_identity_rejected(self):
  with tempfile.TemporaryDirectory()as d:
   c,a=self.setup_io(Path(d));a["identity"]=dict(a["identity"],pid=124);self.fire(a,ValueError("fixture"))
   with self.assertRaisesRegex(ValueError,"rank-owner request"):
    B.raise_if_any(c,a["recipe"],a["recipe_ref"],a["source_ref"],a["helper_ref"])
 def test_publication_failure_never_masks_primary(self):
  with tempfile.TemporaryDirectory()as d:
   c,a=self.setup_io(Path(d))
   def rejected(*args):raise OSError("publication fixture")
   a["publish"]=rejected;out=io.StringIO()
   with redirect_stdout(out):self.fire(a,AttributeError("first primary"))
   row=json.loads(out.getvalue());self.assertIn("publication fixture",row["secondary_publication"])
   self.assertEqual(row["worker_first_fault"]["primary"]["message"],"first primary")
 def test_exclusive_first_fatal_is_not_overwritten(self):
  with tempfile.TemporaryDirectory()as d:
   c,a=self.setup_io(Path(d));self.fire(a,AttributeError("first"))
   p=B.fatal_path(a["recipe"],0);before=c.ref(p)
   with redirect_stdout(io.StringIO()):self.fire(a,ValueError("second"))
   self.assertEqual(c.ref(p),before);self.assertEqual(c.obj(before)["primary"]["message"],"first")
 def test_no_failure_file_does_not_poll_devices_or_create_outputs(self):
  with tempfile.TemporaryDirectory()as d:
   c,a=self.setup_io(Path(d));before=sorted(p.name for p in Path(d).iterdir())
   self.assertIsNone(B.raise_if_any(c,a["recipe"],a["recipe_ref"],a["source_ref"],a["helper_ref"]))
   self.assertEqual(sorted(p.name for p in Path(d).iterdir()),before)
 def test_actual_host_checks_before_observe_health_and_preserves_cleanup_body(self):
  prior=HERE/"host003_reference.py";wire=prior.read_bytes()
  self.assertEqual(hashlib.sha256(wire).hexdigest(),"da37951739e4a675f35837f5ba764eb19f074d39b99384478e62c23063a4f7ef")
  own=ast.parse((HERE/"host_run.py").read_bytes());old=ast.parse(wire)
  def fn(tree,name):return next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name==name)
  self.assertEqual(hashlib.sha256((HERE/"host_common.py").read_bytes()).hexdigest(),
   "72d9c8d1523e8998094eb4ca9e2047e11dfef1026751f3d737925d46bab37813")
  run=fn(own,"run");startup=next(n for n in ast.walk(run)if isinstance(n,ast.While)and isinstance(n.test,ast.Constant)and n.test.value is True)
  self.assertEqual(ast.unparse(startup.body[0].value.func),"boundary.raise_if_any")
  guarded=next(n for n in run.body if isinstance(n,ast.Try));previous=next(n for n in fn(old,"run").body if isinstance(n,ast.Try))
  self.assertEqual(ast.dump(guarded.finalbody[0]),ast.dump(previous.finalbody[0]))
  result=next(n for n in ast.walk(guarded)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=="dict"
   and any(k.arg=="worker_first_fault_refs"for k in n.keywords))
  self.assertIn("primary",[k.arg for k in result.keywords])
if __name__=="__main__":unittest.main(verbosity=2)

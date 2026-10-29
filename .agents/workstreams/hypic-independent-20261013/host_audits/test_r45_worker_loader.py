"""R45 startup controls; fake native fixture is HOST-only, not device proof."""
import ast,hashlib,importlib,importlib.util,inspect,json,os,sys,tempfile,unittest
from pathlib import Path
from types import ModuleType,SimpleNamespace
from unittest.mock import patch
from compilation_budget_r45 import worker_loader as w

class LoaderControls(unittest.TestCase):
 def manifest(self):
  return {"compilation_budget":{"enabled":True,"profile":"source-pinned-triton-compile-v1","max_calls":512},
   "source_sha256":{p:"0"*64 for p in ("compilation_budget_r45/patch.py","compilation_budget_r45/worker_loader.py","compilation_budget_r45/sitecustomize.py")}}
 def test_disabled_needs_no_manifest(self):
  with patch.dict(os.environ,{},clear=True):
   self.assertFalse(w._compilation_budget_enabled({"source_sha256":{}}))
   before=tuple(sys.meta_path);w.enable()();self.assertEqual(before,tuple(sys.meta_path))
 def test_exact_enabled_policy(self):
  with patch.dict(os.environ,{"INDEPENDENT_COMPILATION_BUDGET":"1"}):
   self.assertTrue(w._compilation_budget_enabled(self.manifest()))
 def test_policy_mutations_rejected(self):
  for mutate in ("source","profile","bound","disabled","flag"):
   m=self.manifest();flag="1"
   if mutate=="source":m["source_sha256"].pop("compilation_budget_r45/patch.py")
   if mutate=="profile":m["compilation_budget"]["profile"]="other"
   if mutate=="bound":m["compilation_budget"]["max_calls"]=513
   if mutate=="disabled":flag="0"
   if mutate=="flag":flag="true"
   with self.subTest(mutate=mutate),patch.dict(os.environ,{"INDEPENDENT_COMPILATION_BUDGET":flag}):
    with self.assertRaises(ValueError):w._compilation_budget_enabled(m)
 def test_enabled_without_policy_rejected(self):
  with patch.dict(os.environ,{"INDEPENDENT_COMPILATION_BUDGET":"1"}):
   with self.assertRaises(ValueError):w._compilation_budget_enabled({"source_sha256":{}})
 def test_cleanup_all_even_if_first_fails(self):
  done=[];problem=OSError("first")
  def fail():done.append("observer");raise problem
  with self.assertRaises(OSError)as raised:w._close_all([fail,lambda:done.append("facade"),lambda:done.append("fd")])
  self.assertIs(raised.exception,problem);self.assertEqual(done,["observer","facade","fd"])
 def test_original_failure_wins_cleanup(self):
  problem=ValueError("original");done=[]
  def fail():raise OSError("cleanup")
  w._close_all([fail,lambda:done.append("closed")],problem);self.assertEqual(done,["closed"])
 def test_finder_and_scheduler_cleanup_despite_stop_error(self):
  finder=object();done=[]
  def fail():done.append("observer");raise OSError("close")
  with patch.object(w,"_finder",finder),patch.object(w,"_stop",fail),patch.object(w,"_scheduler_stop",lambda:done.append("scheduler")):
   sys.meta_path.append(finder)
   try:
    with self.assertRaises(OSError):w._uninstall_owned()
    self.assertNotIn(finder,sys.meta_path);self.assertIsNone(w._stop);self.assertIsNone(w._scheduler_stop)
    self.assertEqual(done,["observer","scheduler"])
   finally:
    if finder in sys.meta_path:sys.meta_path.remove(finder)
 def rank_module(self,group=None,error=None):
  module=ModuleType("vllm.distributed")
  def get():
   if error:raise error
   return group
  module.get_tp_group=get
  return module
 def test_rank_actual_tp_group_and_unknown(self):
  for rank in range(4):
   with patch.dict(sys.modules,{"vllm.distributed":self.rank_module(SimpleNamespace(world_size=4,rank_in_group=rank))}):
    self.assertEqual(w._actual_rank(),rank)
  with patch.dict(sys.modules,{"vllm.distributed":self.rank_module(error=AssertionError("not ready"))}):
   self.assertIsNone(w._actual_rank())
 def test_rank_mismatch_not_swallowed(self):
  for group in (SimpleNamespace(world_size=8,rank_in_group=0),SimpleNamespace(world_size=4,rank_in_group=4),SimpleNamespace(world_size=4,rank_in_group=True)):
   with patch.dict(sys.modules,{"vllm.distributed":self.rank_module(group)}):
    with self.assertRaises(ValueError):w._actual_rank()
  with patch.dict(sys.modules,{"vllm.distributed":self.rank_module(error=RuntimeError("group failure"))}):
   with self.assertRaises(RuntimeError):w._actual_rank()
 def test_source_owned_new_module_functions(self):
  source=Path(w.__file__).read_bytes()
  for name,value in vars(w).items():
   if inspect.isfunction(value)and value.__module__==w.__name__:w.verify_raw_function(w,source,value,name=name)
 def test_original_raw_event_writer_unchanged(self):
  from graph_candidate import worker_loader as old
  def writer(p):
   rows=[n for n in ast.walk(ast.parse(Path(p).read_bytes()))if isinstance(n,ast.FunctionDef)and n.name=="raw_emit"]
   self.assertEqual(len(rows),1);return ast.dump(rows[0],include_attributes=False)
  self.assertEqual(writer(w.__file__),writer(old.__file__))
 def test_native_importer_rejects_unknown_wrapper(self):
  import importlib.machinery
  with tempfile.TemporaryDirectory()as directory:
   p=Path(directory)/"vllm_ascend";(p/"worker").mkdir(parents=True);(p/"__init__.py").write_text("")
   target=p/"worker/model_runner_v1.py";target.write_text("raise RuntimeError('not executed')\n")
   package=ModuleType("vllm_ascend");package.__file__=str(p/"__init__.py")
   spec=importlib.util.spec_from_file_location(w.WORKER,target)
   with patch.dict(sys.modules,{"vllm_ascend":package}),patch.object(w,"WORKER_SHA256",hashlib.sha256(target.read_bytes()).hexdigest()):
    original,path,source,code=w._verified_native_spec(spec);self.assertIs(original,spec.loader)
    class Unknown(importlib.machinery.SourceFileLoader):pass
    spec.loader=Unknown(w.WORKER,str(target))
    with self.assertRaises(ValueError):w._verified_native_spec(spec)
 def test_old_loader_conflict_rejected_before_manifest(self):
  fake=ModuleType("graph_candidate.worker_loader");fake._finder=object()
  with patch.dict(os.environ,{"INDEPENDENT_GRAPH_HYPIC":"1"}),patch.dict(sys.modules,{"graph_candidate.worker_loader":fake}):
   with self.assertRaisesRegex(ValueError,"another compact"):w.enable()
 def test_startup_real_native_execution_precedes_observer(self):
  source=ast.parse(Path(w.__file__).read_bytes())
  funcs={n.name:n for n in ast.walk(source)if isinstance(n,ast.FunctionDef)}
  native=funcs["_exec_verified_module"]
  calls=[(n.lineno,ast.unparse(n.func))for n in ast.walk(native)if isinstance(n,ast.Call)]
  first=min(line for line,name in calls if name=="self.original.exec_module")
  observer=min(line for line,name in calls if name=="_activate_compilation")
  algorithm=min(line for line,name in calls if name=="activate_graph_candidate")
  self.assertLess(first,observer);self.assertLess(observer,algorithm)
  for fn in ("_actual_rank","_activate_compilation","_close_all"):
   self.assertIn(fn,funcs)
if __name__=="__main__":unittest.main()

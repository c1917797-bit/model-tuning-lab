"""Actual qualified raw/geometry import-chain regressions; no numeric/model proof.
Tests run the real delegate initializer/cpu_context and real loader geometry calls.
Only resource/evidence scalar inputs are inert fixtures; no fake module keys.
"""
import ast,hashlib,importlib.util,json,os,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
TEMP=Path("C:/Users/Huawei/AppData/Local/Temp")
OLD_ROOT="/cache/cch/qwen36-paper-preparation-20261007/lowbit/kivi-model-firstdecode-bootstrap-v1-018"
RAW_ROOT="/cache/cch/qwen36-paper-preparation-20261007/recurrent/kivi-raw-cpu-provenance-v023-20261011"
WHOLE_ROOT="/cache/cch/qwen36-paper-preparation-20261007/recurrent/kivi-firstdecode-whole-provenance-v022-20261011"
CAPTURE=(HERE if (HERE/"firstdecode_precondition.py").exists()else HERE.parent)if os.name=="nt"else Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/kivi-mixed-capture-bootstrap-v1-008")
SHARED=Path("C:/Users/Huawei/AppData/Local/Packages/sandbox.{48fdcea7-5947-498c-a068-4bc4cdaddb04}/AC/Temp/kivi-c132-reviewed-source/model-deps")
def source(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
 if name in sys.modules:raise ValueError("test will not overwrite an ambient module")
 sys.modules[name]=m
 try:spec.loader.exec_module(m)
 except BaseException:sys.modules.pop(name,None);raise
 return m
def ref(path):
 path=Path(path).resolve();b=path.read_bytes();return dict(path=str(path),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def pin(path,digest):
 r=ref(path)
 if r["sha256"]!=digest:raise ValueError("actual source archive identity")
 return r
def roots():
 if os.name=="nt":return (TEMP/"kivi-firstdecode-hbm-budget-v018-20261010/bootstrap",
  TEMP/"kivi-raw-cpu-provenance-v023-20261011",TEMP/"kivi-firstdecode-whole-provenance-v022-20261011")
 return Path(OLD_ROOT),Path(RAW_ROOT),Path(WHOLE_ROOT)
def dep(digest,name):
 if os.name=="nt":return Path(pin(SHARED/name,digest)["path"])
 m=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
 paths={r["path"]for r in m["dependencies"]if r["sha256"]==digest}
 if len(paths)!=1:raise ValueError("unique actual dependency")
 return Path(pin(next(iter(paths)),digest)["path"])
def helper():
 # No shared fixture module replaces production helper globals.
 return source(HERE/"consumer_namespace.py","_namespace_fixture_helper")
N=helper()
def geometry(loader,root):
 old,raw,whole=roots()
 roles={"kivi_layout_consumer":pin(dep("71f45ada3acf89b68b0338a74897cbb68ab5cc980a3788aa6c4afd282d823927","kivi_layout_consumer.py"),
  "71f45ada3acf89b68b0338a74897cbb68ab5cc980a3788aa6c4afd282d823927"),
  "spans":pin(dep("2eb0a604dead0181c51e4314a15efb6aca48d51436f7eeb254ef3f5ce4518831","spans.py"),
  "2eb0a604dead0181c51e4314a15efb6aca48d51436f7eeb254ef3f5ce4518831")}
 files=[pin(root/"provider_independent.py","332b222442ace7ba90a2ed41cae66f0806dec3639d8711cac86609955afe6f9c"),
        pin(root/"explicit_geometry.py","77b678af5eea524c59405d98a3681415810e2e77b7f8cf9cde9fd241b28d4157")]
 if root==CAPTURE:return loader.geometry_modules(dict(runtime_roles=roles,files=files))
 # Execute the original full-consumer's exact loader prefix, without pretending
 # the absent actual64 numeric output/owner values exist.
 tree=ast.parse((whole/"consume_whole.py").read_bytes())
 fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=="explicit_allocations")
 lines=[]
 for n in fn.body:
  if isinstance(n,ast.Assign)and any(isinstance(x,ast.Call)and isinstance(x.func,ast.Attribute)
    and x.func.attr=="module"for x in ast.walk(n)):lines.append(n)
  elif isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Attribute)and n.value.func.attr=="module":lines.append(n)
 assert len(lines)==4
 env=dict(l=loader,roles=roles,ctx=types.SimpleNamespace(own={Path(r["path"]).name:r for r in files}))
 exec(compile(ast.Module(body=lines,type_ignores=[]),str(whole/"consume_whole.py"),"exec"),env)
 return sys.modules["provider_independent"],env["geometry"]
def first_actual():
 old,raw,whole=roots()
 l=source(Path(pin(old/"loader.py","67d8d9f63982362ffd0fd5acd53ea01fbd57cb4952b6de144bdc0038cc3b38d4")["path"]),
  "_kivi_firstdecode_whole_source_loader")
 d=source(Path(pin(raw/"delegate.py","0aa9009410a6521bfd8febeaddbfa855d28798b3469b3f03b21a0146818a4b45")["path"]),
  "_kivi_b1_exact_raw_delegate")
 pin(whole/"consume_whole.py","933d4324c9e15ae97d7df48558029ae7f1d49d2e356dc6defcc1ae1ff4123e44")
 d.initialize(whole)
 # Real cpu_context imports the exact actual resource module. Its fixture
 # namespace records are never consumed or represented as original evidence.
 original=list(sys.path);sys.path.insert(0,str(raw))
 try:
  ctx=types.SimpleNamespace(cleanup=lambda *a:None,observation=lambda *a:None)
  d.cpu_context(ctx,dict(cid="f"*64,arm="cpu-preflight"),dict(joint_peer_plan=ref(raw/"SOURCE_MANIFEST.json"),
   cpu_only_raw_resource_source=pin(raw/"cpu_raw_resources.py","7ab0550775349577415ddc80bd7fb5573770284d2c2eb44e5e82375b93ef1ca5")))
 finally:sys.path[:]=original
 independent,g=geometry(l,old)
 return dict(old_geometry=ref(g.__file__),old_module_id=id(independent),real_resource_module=ref(sys.modules["cpu_raw_resources"].__file__))
def mixed_geometry():
 l=source(CAPTURE/"loader.py","_mixed_terminal_loader")
 independent,g=geometry(l,CAPTURE)
 return dict(new_geometry=ref(g.__file__),new_module_id=id(independent))
class NamespaceChain(unittest.TestCase):
 def test01_original_actual_geometry_alias_conflict_preserved(self):
  def run():
   first_actual()
   with self.assertRaisesRegex(ValueError,"no foreign cached namespace"):mixed_geometry()
   return {"original_failure_preserved":True}
  N.isolated_call(run,"firstdecode")
 def test02_actual_raw_cpu_and_geometry_prefix_scoped(self):
  value=N.isolated_call(first_actual,"firstdecode")
  self.assertEqual(value["real_resource_module"]["sha256"],"7ab0550775349577415ddc80bd7fb5573770284d2c2eb44e5e82375b93ef1ca5")
  self.assertNotIn("cpu_raw_resources",sys.modules);self.assertNotIn("provider_independent",sys.modules)
 def test03_firstdecode_then_nested_mixed_then_actual_geometry(self):
  first=N.isolated_call(first_actual,"firstdecode")
  def second():
   again=N.isolated_call(first_actual,"firstdecode")
   self.assertEqual(first["old_geometry"],again["old_geometry"])
   return mixed_geometry()
  final=N.isolated_call(second,"mixed")
  self.assertEqual(final["new_geometry"],ref(CAPTURE/"explicit_geometry.py"))
  self.assertNotIn("explicit_geometry",sys.modules)
 def test04_repeated_scopes_leave_no_consumer_context(self):
  before=dict(sys.modules)
  for _ in range(2):N.isolated_call(first_actual,"firstdecode")
  self.assertEqual(set(before),set(sys.modules))
  self.assertTrue(all(sys.modules[k]is v for k,v in before.items()))
 def test05_existing_actual_cpu_module_rejected_unchanged(self):
  _,raw,_=roots();m=source(raw/"cpu_raw_resources.py","cpu_raw_resources")
  m.FIXTURE_MUTABLE={"unchanged":True};called=[]
  try:
   with self.assertRaisesRegex(ValueError,"occupied at entry"):N.isolated_call(lambda:called.append(1),"firstdecode")
   self.assertIs(sys.modules["cpu_raw_resources"],m);self.assertEqual(m.FIXTURE_MUTABLE,{"unchanged":True});self.assertEqual(called,[])
  finally:del sys.modules["cpu_raw_resources"]
 def test06_existing_configurable_contract_rejected_before_globals(self):
  name="_kivi_firstdecode_whole_contract";m=types.ModuleType(name);m.DEPS={"before":1};sys.modules[name]=m
  try:
   with self.assertRaisesRegex(ValueError,"occupied at entry"):N.isolated_call(lambda:m.DEPS.clear(),"firstdecode")
   self.assertEqual(m.DEPS,{"before":1});self.assertIs(sys.modules[name],m)
  finally:del sys.modules[name]
 def test07_partial_actual_import_exception_restores(self):
  expected=RuntimeError("original numeric fixture failure");before=dict(sys.modules)
  def fail():first_actual();raise expected
  with self.assertRaises(RuntimeError)as caught:N.isolated_call(fail,"firstdecode")
  self.assertIs(caught.exception,expected);self.assertEqual(set(before),set(sys.modules))
  self.assertTrue(all(sys.modules[k]is v for k,v in before.items()))
 def test08_preexisting_registry_replacement_fails_and_restores(self):
  name="_namespace_sentinel";sentinel=types.ModuleType(name);sys.modules[name]=sentinel
  try:
   def fail():sys.modules[name]=types.ModuleType("wrong");return {}
   with self.assertRaisesRegex(ValueError,"pre-existing"):N.isolated_call(fail,"firstdecode")
   self.assertIs(sys.modules[name],sentinel)
  finally:del sys.modules[name]
 def test09_path_pollution_fails_and_restores(self):
  original=list(sys.path);path=sys.path
  def fail():sys.path.append("/not-authorized");return {}
  with self.assertRaisesRegex(ValueError,"pre-existing"):N.isolated_call(fail,"firstdecode")
  self.assertIs(sys.path,path);self.assertEqual(sys.path,original)
 def test10_module_result_cannot_escape(self):
  def fail():first_actual();return {"module":sys.modules["provider_independent"]}
  with self.assertRaises(TypeError):N.isolated_call(fail,"firstdecode")
  self.assertNotIn("provider_independent",sys.modules)
 def test11_error_and_registry_pollution_preserve_original_cause(self):
  original=RuntimeError("primary actual fixture");name="_namespace_sentinel";m=types.ModuleType(name);sys.modules[name]=m
  try:
   def fail():sys.modules[name]=None;raise original
   with self.assertRaises(ValueError)as caught:N.isolated_call(fail,"firstdecode")
   self.assertIs(caught.exception.__cause__,original);self.assertIs(sys.modules[name],m)
  finally:del sys.modules[name]
 def test12_actual_original_cpu_guard_rejects_inside_restores_outside(self):
  top=CAPTURE
  tree=ast.parse((top/"firstdecode_precondition.py").read_bytes())
  call=next(n for n in ast.walk(tree)if isinstance(n,ast.Call)and len(n.args)>1 and isinstance(n.args[1],ast.Constant)
   and n.args[1].value=="no ambient resource substitution")
  expression=compile(ast.Expression(call.args[0]),str(top/"firstdecode_precondition.py"),"eval")
  self.assertTrue(eval(expression,dict(sys=sys)))
  def inside():
   first_actual();self.assertFalse(eval(expression,dict(sys=sys)));return {}
  N.isolated_call(inside,"firstdecode");self.assertTrue(eval(expression,dict(sys=sys)))
 def test13_actual_wrappers_route_source_chain_without_shared_context(self):
  paired=HERE if (HERE/"screen_predecessor.py").exists()else(HERE/"paired"if os.name=="nt"else Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/kivi-c16-mixed1024-bootstrap-v1-008"))
  def run():
   path=list(sys.path);sys.path.insert(0,str(paired))
   try:
    pre=source(paired/"screen_predecessor.py","_namespace_actual_pair_predecessor")
    gate=source(paired/"mixed_gate.py","_namespace_actual_pair_mixed")
    # Replace only the unavailable evidence-body boundary, not the real wrapper,
    # delegate, loader, resource import, or geometry module loading statements.
    with patch.object(pre,"_replay",lambda a:first_actual()):
     initial=pre.replay({})
    def mixed_body(a,m):
     cap=source(CAPTURE/"firstdecode_precondition.py","_mixed_terminal_firstdecode")
     def load(path,digest,name):
      return source(Path(pin(path,digest)["path"]),name)
     c=types.SimpleNamespace(module=load)
     m={"files":[ref(CAPTURE/"consumer_namespace.py")]}
     with patch.object(cap,"_replay",lambda *a:first_actual()):again=cap.replay(c,m,{})
     self.assertEqual(initial["old_geometry"],again["old_geometry"])
     return mixed_geometry()
    with patch.object(gate,"_replay",mixed_body):answer=gate.replay({}, {})
    self.assertNotIn("provider_independent",sys.modules)
    return answer
   finally:sys.path[:]=path
  answer=N.isolated_call(run,"mixed")
  self.assertEqual(answer["new_geometry"],ref(CAPTURE/"explicit_geometry.py"))

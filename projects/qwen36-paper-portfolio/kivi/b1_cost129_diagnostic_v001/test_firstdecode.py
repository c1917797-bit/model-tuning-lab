"""Focused stdlib source/real finish-wrapper regressions, not model authority."""
import ast,hashlib,importlib.util,json,os,sys,types,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
def module(name):
 key="_test_kivi_firstdecode_"+name
 spec=importlib.util.spec_from_file_location(key,HERE/(name+".py"))
 value=importlib.util.module_from_spec(spec);sys.modules[key]=value;spec.loader.exec_module(value);return value
FINISH=module("finish_after_native");PRE=module("prerequisite");SERVER=module("server_entry")
def fixture(drained=True):
 calls=[];closed=[];published=[]
 runner=types.SimpleNamespace(requests={},input_batch=types.SimpleNamespace(num_reqs=0,req_ids=[]))
 def native(scheduler):
  calls.append(scheduler)
  if not drained:runner.requests={"real-id":object()}
  return lambda:"original-deferred-answer"
 runner._update_states=native
 close=lambda:closed.append("close")or{"actual_final":"fixture-only"}
 digest=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 final=FINISH.install(runner,close,["real-id"],digest,published.append)
 return runner,final,calls,closed,published,native
class FirstDecode(unittest.TestCase):
 def test_complete_own_source_compiles_no_token_concatenation(self):
  for p in sorted(HERE.glob("*.py")):
   wire=p.read_bytes();compile(wire,str(p),"exec");ast.parse(wire)
   self.assertNotIn(b"__name__"+b"for",wire)
 def test_default_off_export_does_not_import_torch(self):
  before=set(sys.modules);old=os.environ.pop("QWEN36_KIVI_FIRSTDECODE_DIAGNOSTIC",None)
  try:
   value=module("kivi_firstdecode_bootstrap")
   with self.assertRaisesRegex(ValueError,"explicit firstdecode opt-in"):getattr(value,"FirstDecodeWorker")
   self.assertFalse(any(x=="torch"or x.startswith("torch.")for x in set(sys.modules)-before))
  finally:
   if old is not None:os.environ["QWEN36_KIVI_FIRSTDECODE_DIAGNOSTIC"]=old
 def test_actual_finish_zero_tick_preserves_original_deferred_and_restore(self):
  r,final,calls,closed,published,native=fixture()
  output=r._update_states(types.SimpleNamespace(finished_req_ids=["real-id"],total_num_scheduled_tokens=0))
  self.assertEqual(output(),"original-deferred-answer");self.assertEqual(len(calls),1)
  self.assertIs(r._update_states,native);self.assertEqual(len(closed),1);self.assertEqual(final(),published[0])
 def test_no_http_done_or_empty_schedule_can_make_final(self):
  r,final,calls,closed,published,native=fixture()
  r._update_states(types.SimpleNamespace(finished_req_ids=[]))
  with self.assertRaisesRegex(ValueError,"has not occurred"):final()
  self.assertEqual(len(calls),1);self.assertEqual(closed,[]);self.assertEqual(published,[])
 def test_foreign_finished_rejected_before_original_call(self):
  r,final,calls,closed,published,native=fixture()
  with self.assertRaisesRegex(ValueError,"unrelated retirement"):r._update_states(types.SimpleNamespace(finished_req_ids=["foreign-id"]))
  self.assertEqual(calls,[]);self.assertEqual(closed,[])
 def test_actual_finished_but_native_not_drained_rejected(self):
  r,final,calls,closed,published,native=fixture(False)
  with self.assertRaisesRegex(ValueError,"native request/batch drain"):r._update_states(types.SimpleNamespace(finished_req_ids=["real-id"]))
  self.assertEqual(len(calls),1);self.assertEqual(closed,[]);self.assertEqual(published,[])
 def test_wrong_original_source_guard_is_not_bypassed(self):
  runner=types.SimpleNamespace(_update_states=lambda x:None)
  with self.assertRaisesRegex(ValueError,"exact installed update owner"):
   FINISH.install(runner,lambda:None,["real-id"],"0"*64,lambda x:None)
 def test_actual_packed3_whole_ref_is_not_model_permission(self):
  if not(HERE/"SOURCE_MANIFEST.json").is_file():self.fail("actual source manifest is required for declared software CLI")
  l=module("loader");m=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
  value=PRE.consumed(m["packed3_qualification_ref"],l.obj)
  self.assertEqual((value["frames"],value["output_rows"],value["kernel_calls"]),(20,24,60))
  self.assertIs(value["model_ready"],False)
 def test_prior_packed3_result_wrong_sha_rejected_without_read(self):
  calls=[]
  with self.assertRaisesRegex(ValueError,"actual MAIN-consumed"):
   PRE.consumed(dict(path="/not-an-authority",bytes=2195,sha256="0"*64),lambda x:calls.append(x))
  self.assertEqual(calls,[])
 def test_actual_native_cli_boolean_actions_not_false_string(self):
  args=SERVER.native_argv(8250,10*1024**3)
  for flag in("--no-async-scheduling","--enable-chunked-prefill","--no-enable-prefix-caching","--enforce-eager"):
   self.assertEqual(args.count(flag),1)
  self.assertNotIn("false",args);self.assertEqual(args[args.index("--max-num-seqs")+1],"1")
  self.assertEqual(args[args.index("--max-num-batched-tokens")+1],"32768")
  self.assertEqual(args[args.index("--worker-cls")+1],"kivi_firstdecode_bootstrap.FirstDecodeWorker")
 def test_cli_bounds_remain_hard(self):
  for port,cache in((True,1),(8250,True),(8250,11*1024**3),(80,10*1024**3)):
   with self.assertRaises(ValueError):SERVER.native_argv(port,cache)
 def test_cpu_native_worker_import_is_only_in_real_n1_branch(self):
  tree=ast.parse((HERE/"guest_probe.py").read_bytes());parents={}
  for p in ast.walk(tree):
   for ch in ast.iter_child_nodes(p):parents[ch]=p
  found=[]
  for node in ast.walk(tree):
   if isinstance(node,ast.Call)and isinstance(node.func,ast.Attribute)and node.func.attr=="import_module"and node.args and isinstance(node.args[0],ast.Constant)and node.args[0].value=="vllm_ascend.worker.worker":
    cur=node;ancestor=None
    while cur in parents:
     cur=parents[cur]
     if isinstance(cur,ast.If):ancestor=cur;break
    found.append(ancestor)
  self.assertEqual(len(found),1);self.assertEqual(ast.dump(found[0].test),ast.dump(ast.parse('mode == "n1"',mode="eval").body))

def actual_chain():
 """Execute the unchanged real guest binding assignment, then the pinned policy.
 Runtime callable origin/device behavior is intentionally NOT represented here.
 """
 l=module("loader");m=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
 tree=ast.parse((HERE/"guest_probe.py").read_bytes())
 run=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=="run")
 stmt=next(x for x in run.body if isinstance(x,ast.Assign)and any(isinstance(t,ast.Name)and t.id=="binding"for t in x.targets))
 namespace=dict(m=m,path=Path(m["native_format_patch_chain"]["format"]["path"]))
 exec(compile(ast.Module(body=[stmt],type_ignores=[]),str(HERE/"guest_probe.py"),"exec"),namespace)
 rows=[r for r in m["dependencies"]if Path(r["path"]).name=="format_policy.py"]
 if len(rows)!=1 or rows[0]["sha256"]!="f3003c9c5eb67e7fd3cb10b9cefe0322431db21eae163ab0b2a13a02ab077b7a":
  raise ValueError("one unchanged actual format policy source")
 policy=l.module("_kivi_firstdecode_actual_format_chain_policy",rows[0])
 return namespace["binding"],l,policy

class ActualFormatChain(unittest.TestCase):
 def test_actual_guest_binding_and_original_consumer_all_six_refs(self):
  binding,l,policy=actual_chain();visited=[]
  def bound(r):
   wire=l.checked(r);visited.append(dict(r));return wire
  self.assertTrue(policy.validate_chain(binding,bound))
  self.assertEqual(set(binding["patch_chain"]),set(policy.CHAIN))
  self.assertEqual(len(visited),6);self.assertEqual(visited,[binding["patch_chain"][key]for key in policy.CHAIN])
 def test_original_v002_key_failure_reproduced_before_any_byte_read(self):
  binding,l,policy=actual_chain();legacy=json.loads(json.dumps(binding));chain=legacy["patch_chain"]
  chain["manager"]=chain.pop("patch_manager");chain["npu"]=chain.pop("npu_patches");visited=[]
  with self.assertRaisesRegex(ValueError,"whole real export/automatic-patch chain"):
   policy.validate_chain(legacy,lambda r:visited.append(r))
  self.assertEqual(visited,[])
 def test_closed_six_key_contract_rejects_missing_and_unknown(self):
  binding,l,policy=actual_chain()
  for malformed in ("missing","unknown"):
   bad=json.loads(json.dumps(binding))
   if malformed=="missing":bad["patch_chain"].pop("root")
   else:bad["patch_chain"]["origin"]=bad["patch_chain"]["root"]
   with self.assertRaisesRegex(ValueError,"whole real export/automatic-patch chain"):
    policy.validate_chain(bad,l.checked)
 def test_correct_labels_do_not_bypass_wrong_source_pin(self):
  binding,l,policy=actual_chain();bad=json.loads(json.dumps(binding))
  bad["patch_chain"]["root"]["sha256"]="0"*64;visited=[]
  with self.assertRaisesRegex(ValueError,"same image660 patch chain source"):
   policy.validate_chain(bad,lambda r:visited.append(r))
  self.assertEqual(visited,[])
 def test_original_consumer_verifies_actual_ref_size_not_only_labels(self):
  binding,l,policy=actual_chain();bad=json.loads(json.dumps(binding))
  bad["patch_chain"]["loader"]["bytes"]+=1
  with self.assertRaisesRegex(ValueError,"whole stable byte source identity"):
   policy.validate_chain(bad,l.checked)
 def test_binding_propagates_cpu_recipe_and_actual_worker_collector(self):
  host=ast.parse((HERE/"host_run.py").read_bytes())
  maker=next(x for x in host.body if isinstance(x,ast.FunctionDef)and x.name=="make_recipe")
  recipe=next(x.value for x in maker.body if isinstance(x,ast.Assign)and any(isinstance(t,ast.Name)and t.id=="recipe"for t in x.targets))
  value=next(x.value for x in recipe.keywords if x.arg=="native_format_binding")
  self.assertEqual(ast.dump(value),ast.dump(ast.parse('c.obj(cpu["report"])["native_format_binding"]',mode="eval").body))
  boot=ast.parse((HERE/"kivi_firstdecode_bootstrap.py").read_bytes())
  value=next(x.value for x in ast.walk(boot)if isinstance(x,ast.Assign)and any(isinstance(t,ast.Name)and t.id=="binding"for t in x.targets))
  self.assertEqual(ast.dump(value),ast.dump(ast.parse('recipe["native_format_binding"]',mode="eval").body))
  prebind=ast.parse((HERE/"prebind.py").read_bytes())
  self.assertEqual(sum(isinstance(x,ast.Call)and isinstance(x.func,ast.Attribute)and x.func.attr=="bind"and isinstance(x.func.value,ast.Name)and x.func.value.id=="collector"for x in ast.walk(prebind)),1)
  l=module("loader");m=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
  rows=[r for r in m["dependencies"]if Path(r["path"]).name=="adapter.py"and r["sha256"]=="984a5c8b470026d94c456833b9706da14baac4a977120cd818086226617297b1"]
  self.assertEqual(len(rows),1)
  adapter=ast.parse(l.checked(rows[0]));collector=next(x for x in adapter.body if isinstance(x,ast.ClassDef)and x.name=="Collector")
  bind=next(x for x in collector.body if isinstance(x,ast.FunctionDef)and x.name=="bind")
  value=next(x.value for x in ast.walk(bind)if isinstance(x,ast.Assign)and any(isinstance(t,ast.Name)and t.id=="binding"for t in x.targets))
  self.assertEqual(ast.dump(value),ast.dump(ast.parse('self.owner["native_format_binding"]',mode="eval").body))
  self.assertEqual(sum(isinstance(x,ast.Call)and isinstance(x.func,ast.Attribute)and x.func.attr=="bind_getter"for x in ast.walk(bind)),1)


class CannPythonBinding(unittest.TestCase):
 def actual(self):
  l=module("loader");m=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
  return module("cann_python"),l,m
 def test_actual_sameimage_resolution_ref_pinned_without_acl_import(self):
  C,l,m=self.actual();before=sys.modules.get("acl")
  x=C.config(m,l.checked)
  self.assertEqual(x["resolution_ref"]["bytes"],2435)
  self.assertEqual(x["resolution_ref"]["sha256"],"8bb531a2a6d033fbed14010a5acbd0f317717fc491825a09ea09175dd72eaec9")
  self.assertIs(sys.modules.get("acl"),before)
 def test_cann_config_unknown_root_or_bool_size_cannot_supply_namespace(self):
  C,l,m=self.actual()
  for key,value in(("pythonpath_root","/untrusted/python"),("acl_bytes",True)):
   bad=json.loads(json.dumps(m));bad["cann_python_binding"][key]=value
   with self.assertRaisesRegex(ValueError,"one source-bound real image660"):C.config(bad,l.checked)
 def test_source_or_python_stub_loader_rejected_before_binary_read(self):
  C,l,m=self.actual();spec=importlib.util.spec_from_file_location("acl",C.ACL,loader=importlib.machinery.SourceFileLoader("acl",C.ACL))
  with self.assertRaisesRegex(ValueError,"actual selected ACL extension origin/loader"):C.spec_identity(spec)
 def test_foreign_cached_acl_not_deleted_or_replaced(self):
  from unittest.mock import patch
  C,l,m=self.actual();foreign=types.ModuleType("acl");foreign.__file__="/untrusted/acl.py"
  with patch.dict(sys.modules,{"acl":foreign}):
   with self.assertRaisesRegex(ValueError,"foreign cached ACL origin"):C.cached()
   self.assertIs(sys.modules["acl"],foreign)
 def test_missing_acl_cache_cannot_claim_native_import_or_memcpy(self):
  from unittest.mock import patch
  C,l,m=self.actual()
  saved={k:v for k,v in sys.modules.items()if k=="acl"or k.startswith("acl.")}
  self.assertEqual(saved,{},"stdlib software process must not import actual ACL")
  with self.assertRaisesRegex(ValueError,"actual ACL import has not occurred"):C.cached(required=True,memcpy_required=True)
 def test_explicit_path_install_metadata_only_and_failure_restores_namespace(self):
  # Transparent filesystem/spec spies isolate pure namespace logic only.
  # This never creates or executes an ACL module or supplies device architecture.
  from unittest.mock import patch
  C,l,m=self.actual();source=l.ref(HERE/"SOURCE_MANIFEST.json");before=list(sys.path)
  spec=importlib.util.spec_from_file_location("acl",C.ACL,loader=importlib.machinery.ExtensionFileLoader("acl",C.ACL))
  def file_spy(path,size,digest):return dict(path=path,size_bytes=size,sha256=digest)
  try:
   with patch.object(Path,"is_dir",return_value=True),patch.object(Path,"resolve",lambda p:p),patch.object(Path,"is_symlink",return_value=False),patch.object(C,"file_identity",side_effect=file_spy),patch.object(C.importlib.machinery.PathFinder,"find_spec",return_value=spec),patch.object(C.importlib.util,"find_spec",return_value=spec):
    out=C.install(m,l.checked,source)
    self.assertIn(C.ROOT,sys.path);self.assertFalse(out["acl_import_executed_by_helper"])
    self.assertEqual(out["effective_resolution"],out["fixed_root_resolution"]);self.assertNotIn("acl",sys.modules)
   sys.path[:]=before
   wrong=importlib.util.spec_from_file_location("acl","/untrusted/acl.py")
   with patch.object(Path,"is_dir",return_value=True),patch.object(Path,"resolve",lambda p:p),patch.object(Path,"is_symlink",return_value=False),patch.object(C,"file_identity",side_effect=file_spy),patch.object(C.importlib.machinery.PathFinder,"find_spec",return_value=spec),patch.object(C.importlib.util,"find_spec",return_value=wrong):
    with self.assertRaisesRegex(ValueError,"actual selected ACL extension origin/loader"):C.install(m,l.checked,source)
   self.assertEqual(sys.path,before)
  finally:sys.path[:]=before
 def test_actual_three_entries_share_binding_before_native_import(self):
  tree=ast.parse((HERE/"loader.py").read_bytes());load=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=="load")
  texts=[ast.unparse(x)for x in load.body]
  memory=next(i for i,x in enumerate(texts)if "before = memory.memory("in x)
  install=next(i for i,x in enumerate(texts)if "cann.install(m, checked, r)"in x)
  donor=next(i for i,x in enumerate(texts)if "donor.load_modules("in x)
  self.assertLess(memory,install);self.assertLess(install,donor)
  for filename in("guest_probe.py","server_entry.py","kivi_firstdecode_bootstrap.py"):
   data=(HERE/filename).read_text();self.assertIn("l.load(",data)
   self.assertIn('own["cann_python"]',data)
   self.assertIn("cann_python_binding",data)
  helper=ast.parse((HERE/"cann_python.py").read_bytes())
  self.assertFalse(any(isinstance(x,ast.Import)and any(a.name=="acl"or a.name.startswith("acl.")for a in x.names)for x in ast.walk(helper)))
  self.assertFalse(any(isinstance(x,ast.ImportFrom)and x.module and(x.module=="acl"or x.module.startswith("acl."))for x in ast.walk(helper)))


class ActualInputPreflight(unittest.TestCase):
 def actual(self):
  c=module("model_contract");i=module("input_recipe")
  m=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
  model=c.obj(m["model_manifest"]);config=c.obj(c.bound(Path("/models/Qwen3.6-27B")/"config.json",c.CONFIG_SHA))
  self.assertEqual(model["host_model_root"],"/cache/efim/Qwen3.6-27B")
  prompt=[1000+j%257 for j in range(16384)]+[2000+(j*17)%4093 for j in range(16384)]
  return c,i,m,config,prompt
 def test_actual_checkpoint_nested_vocab_and_original_failure(self):
  c,i,m,config,prompt=self.actual()
  with self.assertRaises(KeyError):config["vocab_size"]
  self.assertEqual(i.validate_config(config,prompt,c.require),248320)
 def test_missing_nested_config_cannot_fall_back_to_root_vocab(self):
  c,i,m,config,prompt=self.actual();config.pop("text_config");config["vocab_size"]=248320
  with self.assertRaisesRegex(ValueError,"nested text config"):i.validate_config(config,prompt,c.require)
 def test_unknown_model_or_text_type_fails_closed(self):
  c,i,m,config,prompt=self.actual()
  for target in ("root","text"):
   bad=json.loads(json.dumps(config));(bad if target=="root"else bad["text_config"])["model_type"]="unknown"
   with self.assertRaises(ValueError):i.validate_config(bad,prompt,c.require)
 def test_noninteger_or_missing_vocab_rejected(self):
  c,i,m,config,prompt=self.actual()
  for v in (True,None,0,-1,248320.0,"248320"):
   bad=json.loads(json.dumps(config));bad["text_config"]["vocab_size"]=v
   with self.assertRaisesRegex(ValueError,"positive integer"):i.validate_config(bad,prompt,c.require)
 def test_conflicting_vocab_and_token_domain_rejected(self):
  c,i,m,config,prompt=self.actual();bad=json.loads(json.dumps(config));bad["vocab_size"]=248321
  with self.assertRaisesRegex(ValueError,"conflicting"):i.validate_config(bad,prompt,c.require)
  for token in (True,-1,248320):
   badprompt=list(prompt);badprompt[0]=token
   with self.assertRaisesRegex(ValueError,"token domain"):i.validate_config(config,badprompt,c.require)
 def test_actual_full_input_producer_and_refs_before_device(self):
  import tempfile
  c,i,m,config,prompt=self.actual();source=c.ref(HERE/"SOURCE_MANIFEST.json")
  with tempfile.TemporaryDirectory(prefix="kivi-input-preflight-")as temp:
   plan,protocol=i.create(c,source,m["model_manifest"],Path(temp),"software-only",host=False)
   p=c.obj(plan);q=c.obj(protocol)
   self.assertEqual(q["body"]["prompt"],prompt);self.assertEqual(q["body"]["max_tokens"],2)
   self.assertEqual(c.obj(p["rows"][0]["prompt_token_ids_ref"]),prompt)
   self.assertEqual(q["plan_ref"],plan);self.assertIs(q["model_ready"],False)
   self.assertEqual(c.obj(p["tokenizer_ref"])["model_manifest"],m["model_manifest"])
   actual_tokenizer=c.obj(p["tokenizer_ref"])["tokenizer_config"]
   self.assertEqual(actual_tokenizer["path"],"/models/Qwen3.6-27B/tokenizer_config.json")
   model=c.obj(m["model_manifest"]);declared=next(r for r in model["files"]if r["relative_path"]=="tokenizer_config.json")
   self.assertEqual((actual_tokenizer["bytes"],actual_tokenizer["sha256"]),(declared["size_bytes"],declared["sha256"]))
 def test_real_host_input_producer_precedes_every_container_create(self):
  tree=ast.parse((HERE/"host_run.py").read_bytes())
  run=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=="run")
  calls=[x for x in ast.walk(run)if isinstance(x,ast.Call)]
  inputs=[x for x in calls if isinstance(x.func,ast.Name)and x.func.id=="input_recipe"]
  creates=[x for x in calls if isinstance(x.func,ast.Attribute)and x.func.attr=="create"]
  self.assertEqual(len(inputs),1);self.assertEqual(len(creates),2)
  self.assertTrue(all(inputs[0].lineno<x.lineno for x in creates))
  maker=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=="make_recipe")
  self.assertFalse(any(isinstance(x,ast.Call)and isinstance(x.func,ast.Name)and x.func.id=="input_recipe"for x in ast.walk(maker)))


class RuntimeClosure(unittest.TestCase):
 def test_actual_runtime_roles_in_mounted_file_closure(self):
  m=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
  declared={r["path"]:r for r in m["files"]+m["dependencies"]}
  for name,r in m["runtime_roles"].items():self.assertEqual(declared.get(r["path"]),r,name)
 def test_original_v006_stale_role_rejected_before_runtime_import(self):
  from unittest.mock import patch
  l=module("loader");m=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
  m["runtime_roles"]["installer"]["path"]="/cache/cch/qwen36-paper-preparation-20261007/lowbit/kivi-model-firstdecode-bootstrap-v1-004/installer.py"
  source=l.ref(HERE/"SOURCE_MANIFEST.json")
  with patch.object(l,"obj",return_value=m):
   with self.assertRaisesRegex(ValueError,"runtime role must be in actual mounted"):l.source(source["sha256"])


class ActualOwnerReferenceCreator(unittest.TestCase):
 """Real source creator/write/check/read seam. No Docker/device commands.
 The local Windows-only directory-fsync spy does not qualify POSIX durability.
 Full owned admission additionally replays the unchanged actual packed3 Ref.
 """
 def creator(self,root,inspect_kind="ref2",bad=None):
  import tempfile,time
  from contextlib import ExitStack
  from unittest.mock import patch
  c=module("model_contract");l=module("loader")
  tree=ast.parse((HERE/"host_run.py").read_bytes())
  fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=="owner_precondition")
  ns=dict(c=c,Path=Path,time=time)
  exec(compile(ast.Module(body=[fn],type_ignores=[]),str(HERE/"host_run.py"),"exec"),ns)
  stack=ExitStack();self.addCleanup(stack.close)
  if os.name=="nt":
   # Only a directory fsync IO spy: all file bytes/fsync/hardlink/stat/SHA are real.
   sentinel=-90217;directory_sync=[]
   def directory_open(path,flags):
    if Path(path).is_dir():
     directory_sync.append(str(path));return sentinel
    return os.open(path,flags)
   def fsync(fd):
    if fd!=sentinel:return os.fsync(fd)
   def close(fd):
    if fd!=sentinel:return os.close(fd)
   view=types.SimpleNamespace(O_RDONLY=os.O_RDONLY,O_DIRECTORY=getattr(os,"O_DIRECTORY",0),
     open=directory_open,fsync=fsync,close=close,link=os.link)
   stack.enter_context(patch.object(c,"os",view))
  safety=types.ModuleType("safety_host")
  safety.device_map=lambda:dict((("/dev/davinci%d"%i),("/dev/davinci%d"%(i-4)))for i in range(4,8))
  stack.enter_context(patch.dict(sys.modules,{"safety_host":safety}))
  source=c.write(root/"SOURCE.json",dict(schema="software-owner-source-only/v1"))
  inspection=c.write(root/"inspect.json",dict(exit_code=0,stdout=json.dumps([dict(Id="a"*64)])))
  original=dict(path=inspection["path"],sha256=inspection["sha256"])
  selected=dict(inspection if inspect_kind=="ref3"else original)
  if bad:selected.update(bad)
  refs=dict(source=source)
  pre=c.write(root/"RESOURCE.json",dict(schema="software-resources-only/v1"))
  cpu=dict(report=c.write(root/"CPU.json",dict(schema="software-cpu-only/v1")))
  n1=c.write(root/"N1.json",dict(schema="software-n1-only/v1"))
  calls=[]
  def inspect():calls.append(dict(selected));return dict(Id="a"*64),dict(selected)
  ctl=types.SimpleNamespace(out=root,cid="a"*64,inspect=inspect,created_monotonic=10.0,
    deadline=5410.0,remaining=lambda cap:5300.0)
  return c,l,ns["owner_precondition"],ctl,refs,pre,cpu,n1,inspection,calls
 def actual(self,root,**kw):
  c,l,creator,ctl,refs,pre,cpu,n1,inspection,calls=self.creator(root,**kw)
  owner=creator(ctl,refs,pre,cpu,n1);return c,l,owner,l.obj(owner),inspection,calls
 def test_real_creator_all_six_and_mapping_nested_use_strict_actual_bytes(self):
  import tempfile
  with tempfile.TemporaryDirectory(prefix="kivi-owner-ref3-")as temp:
   c,l,ref,value,inspection,calls=self.actual(Path(temp))
   self.assertEqual(len(calls),2)
   self.assertTrue(all(set(x)=={"path","sha256"}for x in calls))
   self.assertEqual(value["owned_inspect_ref"],inspection)
   for name in("owned_inspect_ref","resource_ref","mapping_ref","clock_ref","canary_ref","cpu_ref"):
    self.assertEqual(set(value[name]),{"path","bytes","sha256"});l.obj(value[name])
   mapping=l.obj(value["mapping_ref"]);self.assertEqual(mapping["inspect"],inspection);l.obj(mapping["inspect"])
   self.assertFalse(value["model_ready"]);self.assertFalse(value["performance_ready"])
 def test_real_creator_to_unchanged_owned_admission_with_actual_packed3(self):
  import tempfile
  m=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
  with tempfile.TemporaryDirectory(prefix="kivi-owner-admission-")as temp:
   c,l,ref,value,inspection,calls=self.actual(Path(temp))
   source=l.ref(HERE/"SOURCE_MANIFEST.json")
   value["source"]=source
   # Fixture source must bind the actual current MF; recreate exclusively, not overwrite.
   rebound=c.write(Path(temp)/"CURRENT_OWNER.json",value)
   recipe=dict(compiled_numeric_qualification_ref=m["packed3_qualification_ref"],external_owner_authority_ref=rebound,
     container_id="a"*64,image_id=c.IMAGE)
   accepted=PRE.owned(recipe,l.obj,source,dict(cgroup="7:memory:/docker/"+("a"*64)))
   self.assertEqual(accepted,value);self.assertEqual(l.obj(value["mapping_ref"])["inspect"],inspection)
 def test_original_ref2_is_rejected_by_unchanged_loader_before_object_read(self):
  import tempfile
  with tempfile.TemporaryDirectory(prefix="kivi-original-ref2-")as temp:
   c,l,creator,ctl,refs,pre,cpu,n1,inspection,calls=self.creator(Path(temp))
   self.assertEqual(c.checked(dict(path=inspection["path"],sha256=inspection["sha256"])),inspection)
   with self.assertRaisesRegex(ValueError,"exact bounded3Ref"):l.obj(ctl.inspect()[1])
 def test_creator_existing_ref3_preserved_and_bad_original_sha_rejected(self):
  import tempfile
  with tempfile.TemporaryDirectory(prefix="kivi-existing-ref3-")as temp:
   c,l,ref,value,inspection,calls=self.actual(Path(temp),inspect_kind="ref3")
   self.assertEqual(value["owned_inspect_ref"],inspection)
  with tempfile.TemporaryDirectory(prefix="kivi-wrong-inspect-sha-")as temp:
   root=Path(temp);c,l,creator,ctl,refs,pre,cpu,n1,inspection,calls=self.creator(root,bad=dict(sha256="0"*64))
   with self.assertRaisesRegex(ValueError,"actual complete SHA"):creator(ctl,refs,pre,cpu,n1)
   self.assertFalse((root/"OWNER_PRECONDITION.json").exists());self.assertFalse((root/"ACTUAL_DEVICE_MAP.json").exists())
 def test_creator_bool_wrong_size_and_extra_key_not_normalized_away(self):
  import tempfile
  for bad in(dict(bytes=True),dict(bytes=1),dict(origin="unknown")):
   with tempfile.TemporaryDirectory(prefix="kivi-bad-inspect-ref-")as temp:
    root=Path(temp);c,l,creator,ctl,refs,pre,cpu,n1,inspection,calls=self.creator(root,bad=bad)
    with self.assertRaises(ValueError):creator(ctl,refs,pre,cpu,n1)
    self.assertFalse((root/"OWNER_PRECONDITION.json").exists())
 def test_missing_original_inspect_cannot_create_owner_or_fake_size(self):
  import tempfile
  with tempfile.TemporaryDirectory(prefix="kivi-missing-inspect-")as temp:
   root=Path(temp);c,l,creator,ctl,refs,pre,cpu,n1,inspection,calls=self.creator(root)
   Path(inspection["path"]).unlink()
   with self.assertRaisesRegex(ValueError,"actual regular file"):creator(ctl,refs,pre,cpu,n1)
   self.assertFalse((root/"OWNER_PRECONDITION.json").exists())
 def test_consumer_rejects_changed_original_after_owner_publication(self):
  import tempfile
  with tempfile.TemporaryDirectory(prefix="kivi-changed-inspect-")as temp:
   c,l,ref,value,inspection,calls=self.actual(Path(temp))
   # Deliberate mutation of this test's own fixture, never a historical receipt.
   with Path(inspection["path"]).open("ab")as out:out.write(b" ")
   with self.assertRaisesRegex(ValueError,"whole stable byte source identity"):l.obj(value["owned_inspect_ref"])
 def test_actual_creator_only_two_checked_inspect_calls_and_loader_stays_closed(self):
  tree=ast.parse((HERE/"host_run.py").read_bytes())
  fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=="owner_precondition")
  inspected=[x for x in ast.walk(fn)if isinstance(x,ast.Call)and isinstance(x.func,ast.Attribute)and x.func.attr=="inspect"]
  normalized=[x for x in ast.walk(fn)if isinstance(x,ast.Call)and isinstance(x.func,ast.Attribute)and x.func.attr=="checked"]
  self.assertEqual(len(inspected),2);self.assertEqual(len(normalized),2)
  for call in normalized:self.assertEqual(ast.dump(call.args[0]),ast.dump(ast.parse("ctl.inspect()[1]",mode="eval").body))
  l=module("loader")
  for bad in(dict(path="/never",sha256="0"*64),dict(path="/never",bytes=True,sha256="0"*64),dict(path="/never",bytes=1,sha256="0"*64,origin="unknown")):
   with self.assertRaisesRegex(ValueError,"exact bounded3Ref"):l.checked(bad)

if __name__=="__main__":unittest.main(verbosity=2)

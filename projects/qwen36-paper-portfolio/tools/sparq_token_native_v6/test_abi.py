"""Actual-source stdlib ABI regressions; fake callables are contracts, never deployed ABI PASS."""
import ast,copy,hashlib,json,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
import preflight as p,receipt
class NativeAPI(unittest.TestCase):
 # These legacy synthetic callable fixtures test the keyword matcher only.
 # Runtime exports() exclusively uses the new source-bound ATB validator.
 def setUp(self):
  self.generic=mock.patch.object(p,"validate_exports",side_effect=p.validate_signature_contracts);self.generic.start()
 def tearDown(self):self.generic.stop()
 def test_ops_bootstrap_precedes_device_operator_import(self):
  calls=[];expected=object()
  def importer(name,*args,**kwargs):
   calls.append((name,kwargs.get("fromlist")))
   return expected
  with mock.patch("builtins.__import__",side_effect=importer):
   self.assertIs(p.import_device_operator(),expected)
  self.assertEqual(calls,[("vllm_ascend.ops",["__name__"]),("vllm_ascend.device.device_op",["DeviceOperator"])])
  self.assertNotIn("torch",sys.modules)
 def test_bootstrap_failure_preserved_without_early_device_operator_import(self):
  calls=[]
  def importer(name,*args,**kwargs):
   calls.append(name)
   raise RuntimeError("actual bootstrap failure fixture")
  with mock.patch("builtins.__import__",side_effect=importer):
   observed=p.safe_observe(p.import_device_operator)
  self.assertEqual(calls,["vllm_ascend.ops"])
  self.assertFalse(observed["ok"])
  self.assertEqual(observed["error"]["text"],"actual bootstrap failure fixture")
  self.assertNotIn("torch",sys.modules)
 def source(self):
  return Path("/cache/cch/qwen36-adakv-prep-20261007/immutable-source-660/device_op.py").read_text()
 def record(self,name,args):
  fn=lambda:None
  row={"export_lookup_error":None,"binding":p.callable_observation(fn),"dispatcher":[],
   "dispatcher_scan_error":None}
  row["binding"]["signature"]={"ok":True,"value":{"text":"("+",".join(args)+")","arguments":[
   {"name":a,"kind":"POSITIONAL_OR_KEYWORD","default":None,"has_default":False,"annotation":None} for a in args]},"error":None}
  row["binding"]["doc"]=None;row["binding"]["text_signature"]=None
  return row
 def records(self):
  return {name:self.record(name,sorted(args)) for name,args in p.REQUIRED.items()}
 def test_actual_captured_source_exact_wrapper_and_native_map(self):
  source=self.source();self.assertEqual(hashlib.sha256(source.encode()).hexdigest(),p.NATIVE_SOURCE_SHA)
  got=p.wrapper_source_contract(source)
  self.assertIn("slot_mapping",got["wrapper_arguments"])
  self.assertNotIn("slot_mapping",got["native_arguments"])
  self.assertEqual(got["keyword_mapping"]["slot_indices"],"slot_mapping")
 def test_wrapper_AST_wrong_native_name_target_value_extra_write_or_positional_rejected(self):
  source=self.source()
  for before,after in (("slot_indices=slot_mapping","slot_mapping=slot_mapping"),
   ("slot_indices=slot_mapping","slot_indices=key"),
   ("torch_npu._npu_reshape_and_cache(","torch_npu.other_writer("),
   ("key=key, value=value, key_cache=key_cache, value_cache=value_cache, slot_indices=slot_mapping",
    "key, value, key_cache, value_cache, slot_mapping"),
   ("key=key, value=value, key_cache=key_cache, value_cache=value_cache, slot_indices=slot_mapping",
    "key=key, value=value, key_cache=key_cache, value_cache=value_cache, slot_indices=slot_mapping, other=key")):
   changed=source.replace(before,after,1)
   self.assertNotEqual(changed,source)
   with self.subTest(before=before,after=after),self.assertRaises(ValueError):p.wrapper_ast_contract(changed)
   with self.subTest(scope="fixed source SHA"),self.assertRaises(ValueError):p.wrapper_source_contract(changed,hashlib.sha256(changed.encode()).hexdigest())
 def test_real_golden_native_writer_calls_keep_wrapper_slot_mapping(self):
  source=(Path(__file__).parent/"matrix.py").read_text();tree=ast.parse(source)
  calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="reshape_and_cache"]
  self.assertEqual(len(calls),3)
  for call in calls:self.assertEqual({k.arg for k in call.keywords},{"key","value","key_cache","value_cache","slot_mapping"})
  self.assertEqual({next(k.value.id for k in call.keywords if k.arg=="slot_mapping") for call in calls},{"indices","mapping","idx"})
  self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and
   n.func.attr=="_npu_reshape_and_cache" for n in ast.walk(tree)))
 def test_actual_paged_attention_keywords_match_unchanged_core(self):
  source=(Path(__file__).parent/"sparq_token_v4/core.py").read_bytes()
  manifest=json.loads((receipt.ROOT/"SOURCE_MANIFEST.json").read_bytes())
  self.assertEqual(hashlib.sha256(source).hexdigest(),manifest["files"]["sparq_token_v4/core.py"])
  tree=ast.parse(source);helper=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=="NativePAHost")
  execute=next(n for n in helper.body if isinstance(n,ast.FunctionDef) and n.name=="execute")
  args=next(n for n in ast.walk(execute) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="args" for t in n.targets))
  self.assertEqual({k.arg for k in args.value.keywords},p.REQUIRED["_npu_paged_attention"])
  self.assertEqual(ast.unparse(next(k.value for k in args.value.keywords if k.arg=="context_lens")),"self.context.value")
  calls=[n for n in ast.walk(helper) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="_npu_paged_attention"]
  self.assertEqual(len(calls),3)
  for call in calls:self.assertEqual({k.arg for k in call.keywords},({None,"workspace"} if len(call.keywords)==2 else {None}))
 def test_native_slot_indices_complete_signature_positive(self):
  got=p.validate_exports(self.records())
  self.assertEqual(got["_npu_reshape_and_cache"]["required_arguments"],sorted(p.WRAPPER_MAP))
  self.assertFalse(got["_npu_reshape_and_cache"]["numerical_support_verified"])
  self.assertNotIn("torch",sys.modules)
 def test_wrapper_name_in_native_signature_is_rejected(self):
  rows=self.records();rows["_npu_reshape_and_cache"]=self.record("_npu_reshape_and_cache",["key","value","key_cache","value_cache","slot_mapping"])
  with self.assertRaises(ValueError):p.validate_exports(rows)
 def test_union_of_incompatible_overloads_never_passes(self):
  rows=self.records();r=rows["_npu_reshape_and_cache"]
  r["binding"]["signature"]={"ok":False,"value":None,"error":{"type":"ValueError","repr":"raw","text":"raw"}}
  r["dispatcher"]=[{"name":"npu::_npu_reshape_and_cache","text":"fixture overload","overload_name":str(i),
   "arguments":[{"name":a,"type":"Tensor","kwarg_only":False,"has_default":False,"default":None} for a in args],"returns":[]} for i,args in enumerate((["key","value","key_cache"],["value_cache","slot_indices"]))]
  with self.assertRaises(ValueError):p.validate_exports(rows)
 def test_foreign_namespace_cannot_impersonate_torch_npu_dispatcher(self):
  rows=self.records();r=rows["_npu_reshape_and_cache"]
  r["binding"]["signature"]={"ok":False,"value":None,"error":{"type":"ValueError","repr":"raw","text":"raw"}}
  r["dispatcher"]=[{"name":"_C_ascend::_npu_reshape_and_cache","text":"all argument names fixture","overload_name":"",
   "arguments":[{"name":a} for a in p.WRAPPER_MAP],"returns":[]}]
  with self.assertRaises(ValueError):p.validate_exports(rows)
 def test_argument_prose_is_not_binding_signature(self):
  rows=self.records();r=rows["_npu_reshape_and_cache"]
  r["binding"]["signature"]={"ok":False,"value":None,"error":{"type":"ValueError","repr":"raw","text":"raw"}}
  r["binding"]["doc"]="Args: key value key_cache value_cache slot_indices"
  with self.assertRaises(ValueError):p.validate_exports(rows)
 def test_complete_native_doc_signature_positive_and_wrong_mapping_negative(self):
  rows=self.records();r=rows["_npu_reshape_and_cache"]
  r["binding"]["signature"]={"ok":False,"value":None,"error":{"type":"ValueError","repr":"raw","text":"raw"}}
  r["binding"]["doc"]="_npu_reshape_and_cache(Tensor key, Tensor value, Tensor key_cache, Tensor value_cache, Tensor slot_indices) -> None"
  self.assertEqual(len(p.validate_exports(rows)["_npu_reshape_and_cache"]["matched_single_signatures"]),1)
  r["binding"]["doc"]=r["binding"]["doc"].replace("slot_indices","slot_mapping")
  with self.assertRaises(ValueError):p.validate_exports(rows)
 def test_no_keyword_support_from_positional_only_python_args_or_kwargs(self):
  for mode in ("POSITIONAL_ONLY","VAR_KEYWORD","VAR_POSITIONAL"):
   rows=self.records()
   for arg in rows["_npu_reshape_and_cache"]["binding"]["signature"]["value"]["arguments"]:arg["kind"]=mode
   with self.subTest(mode=mode),self.assertRaises(ValueError):p.validate_exports(rows)
 def test_collector_preserves_raw_missing_export_and_schema_errors_without_assertion(self):
  torch=SimpleNamespace(_C=SimpleNamespace(_jit_get_all_schemas=lambda:(_ for _ in ()).throw(RuntimeError("actual scan fixture failed"))))
  rows=p.collect_exports(torch,SimpleNamespace())
  self.assertEqual(set(rows),set(p.REQUIRED))
  for row in rows.values():
   self.assertEqual(row["dispatcher_scan_error"]["text"],"actual scan fixture failed")
   self.assertIsNotNone(row["export_lookup_error"])
   self.assertFalse(row["binding"]["callable"])
  with self.assertRaises(ValueError):p.validate_exports(rows)
 def test_raw_process_addresses_retained_but_not_abi_identity(self):
  rows=p.validate_exports(self.records());other=copy.deepcopy(rows)
  for r in rows.values():r["binding"]["source_file"]={"ok":False,"value":None,"error":{"type":"TypeError","repr":"at 0x123","text":"at 0x123"}}
  for r in other.values():r["binding"]["source_file"]={"ok":False,"value":None,"error":{"type":"TypeError","repr":"at 0x999","text":"at 0x999"}}
  self.assertNotEqual(rows,other);self.assertEqual(p.export_contract_identity(rows),p.export_contract_identity(other))
  other["_npu_reshape_and_cache"]["required_arguments"]=["slot_mapping"]
  self.assertNotEqual(p.export_contract_identity(rows),p.export_contract_identity(other))
 def test_observer_saved_before_any_api_or_cpu_golden_assertion(self):
  source=Path(p.__file__).read_text();tree=ast.parse(source)
  fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="probe")
  top=[n for n in fn.body if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=="save_observations"]
  self.assertEqual(len(top),1);saved=top[0].lineno
  calls={n.func.id:n.lineno for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ("validate_observation","cpu_golden_smoke")}
  self.assertLess(saved,calls["validate_observation"]);self.assertLess(saved,calls["cpu_golden_smoke"])
  collector=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="collect_exports")
  self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="require" for n in ast.walk(collector)))
 def test_actual_original_v4_failure_preserved_not_relabelled(self):
  path=Path(__file__).parent/"original_v4_failed_ABI.json"
  self.assertEqual(receipt.sha(path),"6831432f7cead82b13d1dffc6dbd2e2b5d714cf37ae7802d6611cf4c22214677")
  raw=json.loads(path.read_bytes());self.assertEqual(raw["status"],"failed")
  self.assertIn("_npu_reshape_and_cache",raw["primary_error"])
  self.assertIsNone(raw["npu_executed"]);self.assertNotIn("actual_exports",raw)
  with self.assertRaises(ValueError):p.validate_abi(raw,{}, {})
  child=Path(__file__).parent/"original_v4_failed_child.json"
  self.assertEqual(receipt.sha(child),"fbbc184b6e606080318dc982b30b86d510ca607bb1ef5f37b7f1421e8f2663c5")
  record=json.loads(child.read_bytes());self.assertEqual(record["exit_code"],1)
  self.assertIn("slot_mapping",self.source());self.assertIn("slot_indices",self.source())
 def test_default_off_entry_imports_no_torch(self):
  import contextlib,io
  with mock.patch.object(sys,"argv",["preflight.py"]),contextlib.redirect_stdout(io.StringIO()) as out:p.main()
  self.assertFalse(json.loads(out.getvalue())["ready"]);self.assertNotIn("torch",sys.modules)
 def test_observed_extra_required_argument_not_silently_omitted(self):
  rows=self.records();r=rows["_npu_reshape_and_cache"]
  r["binding"]["signature"]["value"]["arguments"].append({"name":"unexpected","kind":"POSITIONAL_OR_KEYWORD","has_default":False})
  with self.assertRaises(ValueError):p.validate_exports(rows)
  r["binding"]["signature"]["value"]["arguments"][-1]["has_default"]=True
  self.assertTrue(p.validate_exports(rows)["_npu_reshape_and_cache"]["single_signature_matched"])
 def test_doc_extra_required_or_default_argument_contract(self):
  rows=self.records();r=rows["_npu_reshape_and_cache"]
  r["binding"]["signature"]={"ok":False,"value":None,"error":{"type":"ValueError","repr":"raw","text":"raw"}}
  r["binding"]["doc"]="_npu_reshape_and_cache(Tensor key, Tensor value, Tensor key_cache, Tensor value_cache, Tensor slot_indices, Tensor workspace)"
  with self.assertRaises(ValueError):p.validate_exports(rows)
  r["binding"]["doc"]=r["binding"]["doc"].replace("workspace)","workspace=None)")
  self.assertTrue(p.validate_exports(rows)["_npu_reshape_and_cache"]["single_signature_matched"])
 def test_dispatcher_preserves_full_argument_metadata_and_overload(self):
  argument=SimpleNamespace(name="slot_indices",type="Tensor",kwarg_only=True,has_default_value=lambda:True,default_value=None)
  schema=SimpleNamespace(name="npu::_npu_reshape_and_cache",overload_name="out",arguments=[argument],returns=[])
  got=p.schema_observation(schema)
  self.assertEqual(got["arguments"],[{"name":"slot_indices","type":"Tensor","kwarg_only":True,"has_default":True,"default":"None"}])
  self.assertEqual(got["overload_name"],"out")
 def test_collection_exception_does_not_replace_primary_with_persistence_failure(self):
  import argparse,contextlib,io
  args=SimpleNamespace(execute=True,source_manifest=Path("/fixture/SOURCE_MANIFEST.json"),
   source_manifest_sha256="1"*64,output=Path("/sparq-results/ABI.json"),host_output_root=Path("/fixture"))
  def failed_probe(a):
   a.observation={"fixture_only":"not authority"};a.observation_ref=None
   raise ValueError("original source import failure fixture")
  captured=[]
  def write(path,value):
   captured.append(value)
   return {"path":str(path),"sha256":"2"*64}
  with mock.patch.object(argparse.ArgumentParser,"parse_args",return_value=args),mock.patch.object(p,"probe",side_effect=failed_probe),\
   mock.patch.object(p,"save_observations",side_effect=OSError("observation persistence failure fixture")),\
   mock.patch.object(Path,"is_dir",return_value=True),mock.patch.object(Path,"exists",return_value=False),\
   mock.patch.object(p,"write_new",side_effect=write),contextlib.redirect_stdout(io.StringIO()),\
   self.assertRaisesRegex(ValueError,"original source import failure fixture"):
   p.main()
  self.assertEqual(len(captured),1)
  self.assertEqual(captured[0]["primary_error"]["text"],"original source import failure fixture")
  self.assertEqual(captured[0]["secondary_errors"][0]["text"],"observation persistence failure fixture")
  self.assertEqual(captured[0]["status"],"failed");self.assertFalse(captured[0]["ready"])
  self.assertNotIn("torch",sys.modules)
 def test_collection_try_except_only_retains_and_reraises_primary(self):
  tree=ast.parse(Path(p.__file__).read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="probe")
  blocks=[n for n in fn.body if isinstance(n,ast.Try)]
  self.assertEqual(len(blocks),1)
  handler=blocks[0].handlers[0]
  self.assertIsInstance(handler.body[-1],ast.Raise)
  self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="save_observations" for n in ast.walk(handler)))
class ActualATBBinding(unittest.TestCase):
 RAW=Path("/cache/cch/qwen36-paper-preparation-20261007/sparse/MAIN-sparq-v6-005-native-20261007-001/cpu-preflight/ABI_OBSERVATIONS.json")
 ABI=RAW.with_name("ABI.json")
 SNAPSHOT=Path("/cache/cch/qwen36-paper-preparation-20261007/sparse/atb-source-image-v1-20261008-0126/_atb_ops.py")
 def raw(self):
  self.assertEqual(receipt.sha(self.RAW),"6276dd65241ff82e2860725a0e9fb1b831d407bc1bfc1fbf24bfd05f471b9247")
  return json.loads(self.RAW.read_bytes())
 def fixture(self):
  # Additional closure fields are explicit software fixtures, NEVER original actual ABI evidence.
  rows=copy.deepcopy(self.raw()["exports_after_source_import"]);source=self.SNAPSHOT.read_text()
  self.assertEqual(receipt.sha(self.SNAPSHOT),p.ATB_SOURCE_SHA)
  for name,row in rows.items():
   binding=row["binding"]
   binding["atb_provenance"]={"ok":True,"error":None,"value":{
    "module_file":p.ATB_SOURCE,"module_source":source,"module_source_sha256":p.ATB_SOURCE_SHA,
    "chain":[{"module":p.ATB_MODULE,"name":name,"qualname":"create_lazy_atb_function.<locals>.generated_function",
     "source_file":p.ATB_SOURCE,"source":"    @wraps(api_func)\n    def wrapper(*args, **kwargs):\n        _register_atb_extensions()\n        return api_func(*args, **kwargs)\n",
     "closure_scalars":{},"closure_functions":{"api_func":{"module":p.ATB_MODULE,
      "qualname":"create_lazy_atb_function.<locals>.generated_function","source_file":p.ATB_SOURCE}},
     "wrapped_is_closure_callee":True},{"module":p.ATB_MODULE,"name":"generated_function",
     "qualname":"create_lazy_atb_function.<locals>.generated_function","source_file":p.ATB_SOURCE,
     "source":binding["source"]["value"],"closure_scalars":{"api_name":name},
     "closure_functions":{},"wrapped_is_closure_callee":False}]}}
  return rows
 def test_original_failed_005_exact_ATB_schema_positive_not_receipt_promotion(self):
  original=json.loads(self.ABI.read_bytes())
  self.assertEqual(receipt.sha(self.ABI),"e18737761ed8c6fa3d3cff650323a6ce2403491d745fed3939d32edef7348df9")
  self.assertEqual(original["status"],"failed");self.assertFalse(original["npu_executed"])
  self.assertIn("one complete native signature",original["primary_error"]["text"])
  for name,row in self.raw()["exports_after_source_import"].items():
   self.assertEqual(p.atb_dispatcher_contract(name,row["dispatcher"]),row["dispatcher"][0])
  with self.assertRaises(ValueError):p.validate_abi(original,{}, {})
  # Prior observer lacks actual module hash/closure, so strict006 never promotes it.
  with self.assertRaisesRegex(ValueError,"source/closure observation"):
   p.validate_exports(self.raw()["exports_after_source_import"])
 def test_source_bound_ATB_software_fixture_positive(self):
  result=p.validate_exports(self.fixture())
  for name,row in result.items():
   witness=row["matched_single_signatures"]
   self.assertEqual(len(witness),1);self.assertEqual(witness[0]["provenance"]["dispatcher"],"atb::"+name)
   self.assertFalse(row["numerical_support_verified"]);self.assertNotIn("torch",sys.modules)
 def test_complete_original_schema_namespace_and_metadata_negatives(self):
  raw=self.raw()["exports_after_source_import"]
  for name,row in raw.items():
   for mode in ("npu","_C_ascend","other-atb","overload","missing","union","slot_mapping","type","default","extra","return"):
    schemas=copy.deepcopy(row["dispatcher"]);s=schemas[0]
    if mode in ("npu","_C_ascend"):s["name"]=mode+"::"+name;s["text"]=s["text"].replace("atb::",mode+"::")
    if mode=="other-atb":s["name"]="atb::other_operator"
    if mode=="overload":s["overload_name"]="out"
    if mode=="missing":s["arguments"].pop()
    if mode=="union":schemas.append(copy.deepcopy(s))
    if mode=="slot_mapping":s["arguments"][-1]["name"]="slot_mapping"
    if mode=="type":s["arguments"][0]["type"]="int"
    if mode=="default":s["arguments"][0]["has_default"]=True
    if mode=="extra":s["arguments"].append(dict(name="foreign",type="Tensor",has_default=False,default=None,kwarg_only=False))
    if mode=="return":s["returns"]=[dict(name="",type="Tensor")]
    with self.subTest(name=name,mode=mode),self.assertRaises(ValueError):p.atb_dispatcher_contract(name,schemas)
 def test_exact_wrapper_module_source_and_closure_negatives(self):
  for mode in ("module","name","qualname","source-file","generated-source","module-hash","module-bytes","closure-target",
   "closure-function","chain-missing","cycle-marker","chain-source","missing"):
   rows=self.fixture();b=rows["_npu_reshape_and_cache"]["binding"];v=b["atb_provenance"]["value"]
   if mode=="module":b["module"]="foreign.atb"
   if mode=="name":b["name"]="_npu_paged_attention"
   if mode=="qualname":b["qualname"]="foreign_function"
   if mode=="source-file":b["source_file"]["value"]="/foreign/_atb_ops.py"
   if mode=="generated-source":b["source"]["value"]=b["source"]["value"].replace("torch.ops.atb","torch.ops.npu")
   if mode=="module-hash":v["module_source_sha256"]="0"*64
   if mode=="module-bytes":v["module_source"]+="\n# changed\n"
   if mode=="closure-target":v["chain"][-1]["closure_scalars"]["api_name"]="_npu_paged_attention"
   if mode=="closure-function":v["chain"][-1]["closure_functions"]["extra"]={"module":"foreign"}
   if mode=="chain-missing":v["chain"]=[]
   if mode=="cycle-marker":v["chain"][-1]["wrapped_is_closure_callee"]=True
   if mode=="chain-source":v["chain"][-1]["source"]=v["chain"][-1]["source"].replace("torch.ops.atb","torch.ops.npu")
   if mode=="missing":del b["atb_provenance"]
   with self.subTest(mode=mode),self.assertRaises(ValueError):p.validate_exports(rows)
 def test_generic_python_or_doc_witness_cannot_override_foreign_runtime_export(self):
  rows=self.fixture();b=rows["_npu_reshape_and_cache"]["binding"];b["module"]="foreign"
  b["signature"]={"ok":True,"error":None,"value":{"text":"fixture-complete","arguments":[
   dict(name=n,kind="POSITIONAL_OR_KEYWORD",has_default=False) for n in p.REQUIRED["_npu_reshape_and_cache"]]}}
  b["doc"]="_npu_reshape_and_cache(Tensor key, Tensor value, Tensor key_cache, Tensor value_cache, Tensor slot_indices)"
  with self.assertRaises(ValueError):p.validate_exports(rows)
 def test_incomplete_original_module_or_dispatcher_observation_rejected(self):
  for name in p.REQUIRED:
   rows=self.fixture();rows[name]["dispatcher_scan_error"]={"type":"RuntimeError","text":"actual scan failed"}
   with self.assertRaises(ValueError):p.validate_exports(rows)
   rows=self.fixture();rows[name]["binding"]["atb_provenance"]={"ok":False,"value":None,"error":{"type":"OSError","text":"read failure"}}
   with self.assertRaises(ValueError):p.validate_exports(rows)
 def test_actual_installed_source_fragment_and_lazy_dispatch_in_source(self):
  source=self.SNAPSHOT.read_text();self.assertEqual(receipt.sha(self.SNAPSHOT),p.ATB_SOURCE_SHA)
  tree=ast.parse(source)
  functions=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=="generated_function"]
  self.assertEqual(len(functions),1)
  fn=functions[0]
  calls=[n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="getattr"]
  self.assertEqual(len(calls),1)
  self.assertEqual(ast.unparse(calls[0]),"getattr(torch.ops.atb, api_name)")
  self.assertIn("lazy_load_atb_so",ast.unparse(fn.decorator_list[0]))
 def test_deployed_exports_path_always_strict_and_identity_binds_actual_provenance(self):
  rows=self.fixture()
  with mock.patch.object(p,"collect_exports",return_value=rows):
   self.assertTrue(p.exports(None,None)["_npu_paged_attention"]["single_signature_matched"])
  original=p.validate_exports(rows);other=copy.deepcopy(original)
  other["_npu_paged_attention"]["binding"]["atb_provenance"]["value"]["chain"][-1]["closure_scalars"]["api_name"]="foreign"
  self.assertNotEqual(p.export_contract_identity(original),p.export_contract_identity(other))


class PAHostGraphABI(unittest.TestCase):
 def fixture(self):
  # Explicit SOFTWARE contract fixtures from actual lazy wrapper source; NOT actual graph ABI.
  rows=ActualATBBinding().fixture()
  name=p.PA_WORKSPACE_NAME;row=copy.deepcopy(rows["_npu_paged_attention"])
  binding=row["binding"];binding["name"]=name
  chain=binding["atb_provenance"]["value"]["chain"]
  chain[0]["name"]=name;chain[-1]["closure_scalars"]["api_name"]=name
  args=[dict(name=n,type={"num_kv_heads":"int","num_heads":"int","scale_value":"float"}.get(n,"Tensor"),
   has_default=False,default=None,kwarg_only=False) for n in sorted(p.REQUIRED["_npu_paged_attention"])]
  row["dispatcher"]=[dict(name="atb::"+name,overload_name="",text="SOFTWARE-CONTRACT-ONLY",arguments=args,returns=[dict(name="",type="Tensor")])]
  graph={}
  for name in p.PA_GRAPH_NAMES:
   item=copy.deepcopy(binding);item.update(module="torch_npu.npu.graphs",name=name,qualname=name)
   item.pop("atb_provenance",None)
   graph[name]=dict(lookup_error=None,binding=item)
  return dict(workspace=row,graph=graph,source_callsite_sha256=p.PA_SOURCE_SHA)
 def test_exact_workspace_lazy_source_and_graph_software_positive_not_native_authority(self):
  fixture=self.fixture();self.assertIs(p.validate_pa_graph_api(fixture),fixture)
  self.assertEqual(p.pa_graph_identity(fixture)["source_callsite_sha256"],p.PA_SOURCE_SHA)
  self.assertNotIn("torch",sys.modules);self.assertNotIn("torch_npu",sys.modules)
 def test_partial_foreign_layout_schema_and_graph_bindings_failclosed(self):
  for mode in ("foreign-namespace","wrong-type","missing","overload","union","return","closure","graph-missing","graph-foreign","graph-name","graph-error"):
   item=self.fixture();schema=item["workspace"]["dispatcher"][0]
   if mode=="foreign-namespace":schema["name"]=schema["name"].replace("atb::","npu::")
   elif mode=="wrong-type":schema["arguments"][0]["type"]="int"
   elif mode=="missing":schema["arguments"].pop()
   elif mode=="overload":schema["overload_name"]="out"
   elif mode=="union":item["workspace"]["dispatcher"].append(copy.deepcopy(schema))
   elif mode=="return":schema["returns"]=[]
   elif mode=="closure":item["workspace"]["binding"]["atb_provenance"]["value"]["chain"][-1]["closure_scalars"]["api_name"]="_npu_paged_attention"
   elif mode=="graph-missing":item["graph"].pop("graph_task_update_begin")
   elif mode=="graph-foreign":item["graph"]["graph_task_update_begin"]["binding"]["module"]="foreign.graphs"
   elif mode=="graph-name":item["graph"]["graph_task_update_begin"]["binding"]["name"]="other"
   elif mode=="graph-error":item["graph"]["graph_task_update_begin"]["lookup_error"]={"type":"AttributeError","text":"raw"}
   with self.subTest(mode=mode),self.assertRaises(ValueError):p.validate_pa_graph_api(item)
 def test_actual_raw_collection_preserves_missing_graph_before_assertion(self):
  torch=SimpleNamespace(_C=SimpleNamespace(_jit_get_all_schemas=lambda:[]),npu=SimpleNamespace())
  observed=p.collect_pa_graph_api(torch,SimpleNamespace())
  self.assertEqual(set(observed["graph"]),set(p.PA_GRAPH_NAMES))
  self.assertTrue(all(x["lookup_error"]["type"]=="AttributeError" for x in observed["graph"].values()))
  self.assertEqual(observed["workspace"]["export_lookup_error"]["type"],"AttributeError")
  with self.assertRaises(ValueError):p.validate_pa_graph_api(observed)
  tree=ast.parse(Path(p.__file__).read_text());probe=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="probe")
  def line(name):
   return next(n.lineno for n in ast.walk(probe) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id==name)
  self.assertLess(line("collect_pa_graph_api"),line("save_observations"));self.assertLess(line("save_observations"),line("validate_observation"))
  recheck=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="recheck_preinit")
  self.assertIn("collect_pa_graph_api",ast.unparse(recheck))
  self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="set_device" for n in ast.walk(recheck)))

if __name__=="__main__":unittest.main(verbosity=2)

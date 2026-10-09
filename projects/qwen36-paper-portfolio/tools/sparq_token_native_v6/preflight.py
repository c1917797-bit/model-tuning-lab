"""Actual no-device native ABI observer; source-bound wrapper/native names. Default OFF."""
import argparse,ast,copy,hashlib,importlib.metadata,inspect,json,os,re,sys
from pathlib import Path
from receipt import *
WRAPPER_ARGUMENTS=("cls","key","value","key_cache","value_cache","slot_mapping")
WRAPPER_MAP={"key":"key","value":"value","key_cache":"key_cache","value_cache":"value_cache","slot_indices":"slot_mapping"}
NATIVE_SOURCE_SHA="de6a8547df3ff92bf8666e475be56840005cccb3272452c2d6cac4c3f1ddff47"
NATIVE_SOURCE=Path("/vllm-workspace/vllm-ascend/vllm_ascend/device/device_op.py")
REQUIRED={"_npu_paged_attention":{"query","key_cache","value_cache","num_heads","num_kv_heads","scale_value","block_table","context_lens","out"},
 "_npu_reshape_and_cache":set(WRAPPER_MAP)}
def error_record(error):
 return {"type":type(error).__name__,"repr":repr(error),"text":str(error)}
def safe_observe(fn):
 try:return {"ok":True,"value":fn(),"error":None}
 except BaseException as error:return {"ok":False,"value":None,"error":error_record(error)}
def import_device_operator():
 # Pinned v0.23 has an early device_op/fused_moe import cycle. Initialize the
 # Ascend ops package first, as in the existing source-proven plugin bootstrap.
 # This changes import order only; no upstream source or numerical gate changes.
 __import__("vllm_ascend.ops",fromlist=["__name__"])
 return __import__("vllm_ascend.device.device_op",fromlist=["DeviceOperator"])
def callable_observation(fn):
 result={"callable":callable(fn),"kind":type(fn).__name__,"module":getattr(fn,"__module__",None),
  "qualname":getattr(fn,"__qualname__",None),"name":getattr(fn,"__name__",None),
  "doc":getattr(fn,"__doc__",None),"text_signature":getattr(fn,"__text_signature__",None)}
 def signature():
  sig=inspect.signature(fn)
  return {"text":str(sig),"arguments":[{"name":p.name,"kind":p.kind.name,
   "default":None if p.default is inspect.Parameter.empty else repr(p.default),
   "has_default":p.default is not inspect.Parameter.empty,"annotation":None if p.annotation is inspect.Parameter.empty else repr(p.annotation)}
   for p in sig.parameters.values()]}
 result["signature"]=safe_observe(signature)
 result["source_file"]=safe_observe(lambda:inspect.getsourcefile(fn))
 result["source"]=safe_observe(lambda:inspect.getsource(fn))
 if getattr(fn,"__module__",None)==ATB_MODULE:result["atb_provenance"]=collect_atb_provenance(fn)
 return result
def schema_observation(schema):
 return {"name":str(schema.name),"overload_name":str(schema.overload_name),"text":str(schema),
  "arguments":[{"name":str(a.name),"type":str(a.type),"kwarg_only":bool(a.kwarg_only),
   "has_default":bool(a.has_default_value()),"default":repr(a.default_value) if a.has_default_value() else None}
   for a in schema.arguments],"returns":[{"name":str(a.name),"type":str(a.type)} for a in schema.returns]}
def collect_exports(torch,torch_npu):
 schema_scan=safe_observe(lambda:[schema_observation(s) for s in torch._C._jit_get_all_schemas()])
 records={}
 for name in REQUIRED:
  export=safe_observe(lambda:getattr(torch_npu,name))
  fn=export["value"] if export["ok"] else None
  basename=(name,name.lstrip("_"))
  schemas=sorted([s for s in (schema_scan["value"] or []) if s["name"].split("::")[-1] in basename],key=lambda s:s["text"])
  records[name]={"export_lookup_error":export["error"],"binding":callable_observation(fn),"dispatcher":schemas,
   "dispatcher_scan_error":schema_scan["error"]}
 return records
def document_signatures(name,text):
 """Only complete callable-header signatures count; argument prose is never a witness."""
 if type(text) is not str:return []
 patterns=re.compile(r"(?<![A-Za-z0-9_])("+re.escape(name)+"|"+re.escape(name.lstrip("_"))+r")\s*\(")
 signatures=[]
 for match in patterns.finditer(text):
  start=match.end();depth=1;end=start
  while end<len(text) and depth:
   depth+=(text[end]=="(")-(text[end]==")");end+=1
  if depth:continue
  parts=[];previous=0;nest=0
  body=text[start:end-1]
  for index,char in enumerate(body):
   if char in "([{":nest+=1
   elif char in ")]}":nest-=1
   elif char=="," and nest==0:parts.append(body[previous:index]);previous=index+1
  parts.append(body[previous:]);arguments=[];keyword_only=False;valid=True
  for raw in parts:
   token=raw.strip()
   if token in ("","/"):continue
   if token=="*":keyword_only=True;continue
   if token.startswith("*"):valid=False;break
   has_default="=" in token
   default=token.split("=",1)[1].strip() if has_default else None
   token=token.split("=",1)[0].strip()
   if ":" in token:argument=token.split(":",1)[0].strip()
   else:
    found=re.search(r"([A-Za-z_][A-Za-z_0-9]*)\??$",token)
    argument=found.group(1) if found else None
   if not argument or not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*",argument):valid=False;break
   arguments.append({"name":argument,"keyword_only":keyword_only,"has_default":has_default,"default":default})
  if valid and arguments and len({a["name"] for a in arguments})==len(arguments):
   signatures.append({"text":text[match.start():end],"arguments":arguments})
 return signatures
def keyword_contract(arguments,needed,kind):
 names={a["name"] for a in arguments if a.get("kind") not in ("VAR_KEYWORD","VAR_POSITIONAL")}
 if not names>=needed:return False
 if any(a.get("kind")=="POSITIONAL_ONLY" for a in arguments if a["name"] in needed):return False
 # An extra required argument cannot be supplied by this exact frozen keyword call.
 return all(a["name"] in needed or a.get("has_default") is True or a.get("kind") in ("VAR_KEYWORD","VAR_POSITIONAL")
  for a in arguments)
def validate_signature_contracts(records):
 require(type(records) is dict and set(records)==set(REQUIRED),"complete two actual native export observations")
 validated={}
 for name,needed in REQUIRED.items():
  r=copy.deepcopy(records[name]);binding=r["binding"];require(binding.get("callable") is True and r["export_lookup_error"] is None,"actual callable native export: "+name)
  witnesses=[]
  for schema in r["dispatcher"]:
   # Ascend custom registrations are retained, but cannot impersonate torch_npu's npu dispatcher.
   if schema["name"].split("::")[0]!="npu":continue
   args=schema["arguments"];names={a["name"] for a in args}
   if keyword_contract(args,needed,"dispatcher"):witnesses.append({"kind":"actual_dispatcher","text":schema["text"],"arguments":args})
  signature=binding["signature"]
  if signature["ok"]:
   args=signature["value"]["arguments"];names={a["name"] for a in args if a["kind"] not in ("VAR_KEYWORD","VAR_POSITIONAL")}
   if keyword_contract(args,needed,"python"):
    witnesses.append({"kind":"actual_python_signature","text":signature["value"]["text"],"arguments":args})
  for kind,text in (("actual_binding_doc",binding.get("doc")),("actual_binding_text_signature",binding.get("text_signature"))):
   for signature in document_signatures(name,text):
    if keyword_contract(signature["arguments"],needed,"document"):witnesses.append({"kind":kind,**signature})
  require(witnesses,"one complete native signature with actual keyword names BEFORE device initialization: "+name)
  r.update(required_arguments=sorted(needed),single_signature_matched=True,matched_single_signatures=witnesses,
   numerical_support_verified=False)
  validated[name]=r
 return validated

ATB_MODULE="torch_npu.op_plugin.atb._atb_ops"
ATB_SOURCE="/usr/local/python3.12.13/lib/python3.12/site-packages/torch_npu/op_plugin/atb/_atb_ops.py"
ATB_SOURCE_SHA="b9f3b41645faecb9bc8c9a48cb90edb9274b040470a50c3d97bc3283b3ba8c00"
ATB_LAZY_SHA="b0a2c36dcd61fdacb0871745574c5f76c795225af4c79d2fc4f2dafb11bb40ff"
ATB_GENERATED_SHA="c4eb95a77e89caef0aaa7e42129776a76daa0d1e0e4d87056586f78b8b4ff757"
ATB_SCHEMAS={
 "_npu_paged_attention":"atb::_npu_paged_attention(Tensor query, Tensor key_cache, Tensor value_cache, int num_kv_heads, int num_heads, float scale_value, Tensor block_table, Tensor context_lens, Tensor(a!) out, *, Tensor? workspace=None) -> ()",
 "_npu_reshape_and_cache":"atb::_npu_reshape_and_cache(Tensor key, Tensor value, Tensor(a!) key_cache, Tensor(b!) value_cache, Tensor slot_indices) -> ()"}
def collect_atb_provenance(fn):
 # Observation-only, never initialize/call the lazy ATB callable.
 def collect():
  module=sys.modules.get(ATB_MODULE);path=getattr(module,"__file__",None)
  source=Path(path).read_bytes()
  chain=[];target=fn;seen=set()
  for depth in range(8):
   if id(target) in seen:raise ValueError("cyclic actual wrapper chain")
   seen.add(id(target));cv=inspect.getclosurevars(target)
   scalars={k:v for k,v in cv.nonlocals.items() if type(v) in (str,int,float,bool) or v is None}
   functions={k:{"module":v.__module__,"qualname":v.__qualname__,"source_file":v.__code__.co_filename}
    for k,v in cv.nonlocals.items() if inspect.isfunction(v)}
   next_target=getattr(target,"__wrapped__",None)
   if next_target is not None and (not inspect.isfunction(next_target) or
    not any(v is next_target for v in cv.nonlocals.values())):
    raise ValueError("actual __wrapped__ is not closure callee")
   chain.append({"module":target.__module__,"name":target.__name__,"qualname":target.__qualname__,
    "source_file":target.__code__.co_filename,"source":inspect.getsource(target.__code__),
    "closure_scalars":scalars,"closure_functions":functions,
    "wrapped_is_closure_callee":next_target is not None})
   if next_target is None:break
   target=next_target
  else:raise ValueError("actual wrapper chain exceeds bounded observer")
  return {"module_file":path,"module_source_sha256":hashlib.sha256(source).hexdigest(),
   "module_source":source.decode("utf-8"),"chain":chain}
 return safe_observe(collect)
def atb_provenance_contract(name,binding):
 require(name in (*REQUIRED,"_npu_paged_attention_get_workspace") and binding.get("module")==ATB_MODULE and
  binding.get("name")==name and binding.get("qualname")=="create_lazy_atb_function.<locals>.generated_function",
  "exact two installed TorchNPU ATB lazy wrappers, no foreign namespace impersonation")
 source_file=binding["source_file"];source=binding["source"]
 require(source_file["ok"] and source_file["value"]==ATB_SOURCE and source["ok"] and
  hashlib.sha256(source["value"].encode()).hexdigest()==ATB_GENERATED_SHA,
  "actual source-bound ATB generated callable")
 provenance=binding.get("atb_provenance",{})
 require(provenance.get("ok") is True and provenance.get("error") is None,"complete actual ATB source/closure observation")
 v=provenance["value"]
 require(v["module_file"]==ATB_SOURCE and v["module_source_sha256"]==ATB_SOURCE_SHA and
  hashlib.sha256(v["module_source"].encode()).hexdigest()==ATB_SOURCE_SHA,
  "actual unchanged installed ATB module bytes, not module-name only")
 chain=v["chain"];require(type(chain) is list and len(chain)==2,"complete bounded actual lazy wrapper chain")
 for i,row in enumerate(chain):
  require(row["module"]==ATB_MODULE and row["source_file"]==ATB_SOURCE and
   row["wrapped_is_closure_callee"]==(i<len(chain)-1),"actual lazy decorator/closure provenance")
 outer=chain[0]
 require(outer["closure_scalars"]=={} and outer["closure_functions"]=={"api_func":{
  "module":ATB_MODULE,"qualname":"create_lazy_atb_function.<locals>.generated_function","source_file":ATB_SOURCE}} and
  hashlib.sha256(outer["source"].encode()).hexdigest()==ATB_LAZY_SHA,
  "actual unchanged lazy_load_atb_so -> wrapped api_func closure")
 final=chain[-1]
 require(final["qualname"]=="create_lazy_atb_function.<locals>.generated_function" and
  final["closure_scalars"]=={"api_name":name} and final["closure_functions"]=={} and
  hashlib.sha256(final["source"].encode()).hexdigest()==ATB_GENERATED_SHA,
  "actual captured api_name closes over only the exact observed dispatcher target")
 return {"module":ATB_MODULE,"module_source_sha256":ATB_SOURCE_SHA,"api_name":name,
  "dispatcher":"atb::"+name,"native_algorithm_verified":False}
ATB_SCHEMA_RECORDS={"_npu_paged_attention":{"arguments":[{"default":None,"has_default":False,"kwarg_only":False,"name":"query","type":"Tensor"},{"default":None,"has_default":False,"kwarg_only":False,"name":"key_cache","type":"Tensor"},{"default":None,"has_default":False,"kwarg_only":False,"name":"value_cache","type":"Tensor"},{"default":None,"has_default":False,"kwarg_only":False,"name":"num_kv_heads","type":"int"},{"default":None,"has_default":False,"kwarg_only":False,"name":"num_heads","type":"int"},{"default":None,"has_default":False,"kwarg_only":False,"name":"scale_value","type":"float"},{"default":None,"has_default":False,"kwarg_only":False,"name":"block_table","type":"Tensor"},{"default":None,"has_default":False,"kwarg_only":False,"name":"context_lens","type":"Tensor"},{"default":None,"has_default":False,"kwarg_only":False,"name":"out","type":"Tensor"},{"default":"None","has_default":True,"kwarg_only":True,"name":"workspace","type":"Optional[Tensor]"}],"name":"atb::_npu_paged_attention","overload_name":"","returns":[],"text":"atb::_npu_paged_attention(Tensor query, Tensor key_cache, Tensor value_cache, int num_kv_heads, int num_heads, float scale_value, Tensor block_table, Tensor context_lens, Tensor(a!) out, *, Tensor? workspace=None) -> ()"},"_npu_reshape_and_cache":{"arguments":[{"default":None,"has_default":False,"kwarg_only":False,"name":"key","type":"Tensor"},{"default":None,"has_default":False,"kwarg_only":False,"name":"value","type":"Tensor"},{"default":None,"has_default":False,"kwarg_only":False,"name":"key_cache","type":"Tensor"},{"default":None,"has_default":False,"kwarg_only":False,"name":"value_cache","type":"Tensor"},{"default":None,"has_default":False,"kwarg_only":False,"name":"slot_indices","type":"Tensor"}],"name":"atb::_npu_reshape_and_cache","overload_name":"","returns":[],"text":"atb::_npu_reshape_and_cache(Tensor key, Tensor value, Tensor(a!) key_cache, Tensor(b!) value_cache, Tensor slot_indices) -> ()"}}
def atb_dispatcher_contract(name,schemas):
 require(name in REQUIRED and schemas==[ATB_SCHEMA_RECORDS[name]],
  "one byte-bound complete installed ATB default schema; no foreign namespace/type/overload union")
 require(keyword_contract(schemas[0]["arguments"],REQUIRED[name],"dispatcher"),
  "exact observed schema accepts unchanged frozen native keyword call")
 return copy.deepcopy(schemas[0])
def validate_exports(records):
 require(type(records) is dict and set(records)==set(REQUIRED),"complete two actual native export observations")
 validated={}
 for name,needed in REQUIRED.items():
  r=copy.deepcopy(records[name]);binding=r["binding"]
  require(binding.get("callable") is True and r["export_lookup_error"] is None and
   r["dispatcher_scan_error"] is None,"complete actual callable/dispatcher scan: "+name)
  provenance=atb_provenance_contract(name,binding)
  schema=atb_dispatcher_contract(name,r["dispatcher"])
  r.update(required_arguments=sorted(needed),single_signature_matched=True,
   matched_single_signatures=[{"kind":"actual_source_bound_atb_dispatcher","text":schema["text"],
    "arguments":schema["arguments"],"provenance":provenance}],numerical_support_verified=False)
  validated[name]=r
 return validated
def exports(torch,torch_npu):
 return validate_exports(collect_exports(torch,torch_npu))
def wrapper_ast_contract(source):
 tree=ast.parse(source);classes=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=="BaseDeviceAdaptor"]
 require(len(classes)==1,"one actual BaseDeviceAdaptor")
 functions=[n for n in classes[0].body if isinstance(n,ast.FunctionDef) and n.name=="reshape_and_cache"]
 require(len(functions)==1,"one actual native cache writer wrapper")
 fn=functions[0]
 require([a.arg for a in fn.args.args]==list(WRAPPER_ARGUMENTS) and not fn.args.posonlyargs and not fn.args.kwonlyargs and
  fn.args.vararg is None and fn.args.kwarg is None and not fn.args.defaults and
  len(fn.decorator_list)==1 and isinstance(fn.decorator_list[0],ast.Name) and fn.decorator_list[0].id=="classmethod",
  "exact wrapper arguments; slot_mapping is NOT native parameter")
 require(len(fn.body)==1 and isinstance(fn.body[0],ast.Expr) and isinstance(fn.body[0].value,ast.Call),"wrapper has only one unchanged native writer call")
 call=fn.body[0].value
 require(isinstance(call.func,ast.Attribute) and isinstance(call.func.value,ast.Name) and
  call.func.value.id=="torch_npu" and call.func.attr=="_npu_reshape_and_cache" and not call.args and
  all(k.arg is not None and isinstance(k.value,ast.Name) for k in call.keywords),"exact native callee and keyword-only passthrough")
 mapping={k.arg:k.value.id for k in call.keywords}
 require(len(call.keywords)==len(mapping)==5 and mapping==WRAPPER_MAP,"native slot_indices maps only to wrapper slot_mapping, no union/alternate ABI")
 return {"wrapper_arguments":list(WRAPPER_ARGUMENTS),"native_arguments":sorted(REQUIRED["_npu_reshape_and_cache"]),
  "keyword_mapping":mapping,"native_export":"torch_npu._npu_reshape_and_cache","source_sha256":NATIVE_SOURCE_SHA,
  "actual_writer_source_verified":True,"numerical_support_verified":False}
def wrapper_source_contract(source,digest=NATIVE_SOURCE_SHA):
 require(hashlib.sha256(source.encode()).hexdigest()==digest==NATIVE_SOURCE_SHA,"actual unchanged DeviceOperator source bytes")
 return wrapper_ast_contract(source)
def export_contract_identity(records):
 """Raw exceptions keep addresses in observations; process-address bytes are not ABI identity."""
 result={}
 for name,record in records.items():
  binding=record["binding"]
  def outcome(item):
   return {"ok":item["ok"],"value":item["value"] if item["ok"] else None,
    "error_type":item["error"]["type"] if not item["ok"] else None}
  result[name]={"binding":{k:binding[k] for k in ("callable","kind","module","qualname","name","doc","text_signature")},
   "signature":outcome(binding["signature"]),"source_file":outcome(binding["source_file"]),"source":outcome(binding["source"]),
   "dispatcher":record["dispatcher"],"required_arguments":record["required_arguments"],
   "atb_provenance":binding.get("atb_provenance"),"matched_single_signatures":record["matched_single_signatures"],"single_signature_matched":record["single_signature_matched"]}
 return result
PA_WORKSPACE_NAME="_npu_paged_attention_get_workspace"
PA_GRAPH_NAMES=("ExternalEvent","Stream","stream","current_stream","graph_task_group_begin","graph_task_group_end","graph_task_update_begin","graph_task_update_end")
PA_SOURCE_SHA="80005aba42bcf61247cc0d91502a0f1338194a4b38dd82bc521f6d3c84958390"
def collect_pa_graph_api(torch,torch_npu):
 scan=safe_observe(lambda:[schema_observation(s) for s in torch._C._jit_get_all_schemas()])
 export=safe_observe(lambda:getattr(torch_npu,PA_WORKSPACE_NAME))
 name=PA_WORKSPACE_NAME
 workspace={"export_lookup_error":export["error"],"binding":callable_observation(export["value"] if export["ok"] else None),
  "dispatcher":[s for s in (scan["value"] or []) if s["name"].split("::")[-1]==name],"dispatcher_scan_error":scan["error"]}
 graph={}
 for name in PA_GRAPH_NAMES:
  actual=safe_observe(lambda:getattr(torch.npu,name))
  graph[name]={"lookup_error":actual["error"],"binding":callable_observation(actual["value"] if actual["ok"] else None)}
 return {"workspace":workspace,"graph":graph,"source_callsite_sha256":PA_SOURCE_SHA}
def validate_pa_graph_api(record):
 require(type(record) is dict and record.get("source_callsite_sha256")==PA_SOURCE_SHA and
  set(record.get("graph",{}))==set(PA_GRAPH_NAMES),"complete source-bound deployed PA graph API observation")
 workspace=record["workspace"]
 require(workspace["export_lookup_error"] is None and workspace["dispatcher_scan_error"] is None and
  workspace["binding"]["callable"] is True,"complete actual PA workspace callable/schema")
 atb_provenance_contract(PA_WORKSPACE_NAME,workspace["binding"])
 schemas=workspace["dispatcher"];require(len(schemas)==1,"one actual complete workspace schema, no overload union")
 schema=schemas[0]
 required=REQUIRED["_npu_paged_attention"]
 types={name:"Tensor" for name in required};types.update(num_kv_heads="int",num_heads="int",scale_value="float")
 args=schema["arguments"]
 require(schema["name"]=="atb::"+PA_WORKSPACE_NAME and schema["overload_name"]=="" and
  keyword_contract(args,required,"dispatcher") and
  all(a["type"]==types[a["name"]] and a.get("has_default") is False for a in args if a["name"] in required) and
  len(schema["returns"])==1 and schema["returns"][0]["type"]=="Tensor",
  "exact source-bound PA workspace kwargs/types/Tensor return, no foreign or partial signature")
 for name,item in record["graph"].items():
  binding=item["binding"];module=binding.get("module") or ""
  require(item["lookup_error"] is None and binding["callable"] is True and
   (module=="torch_npu._C" or module.startswith("torch_npu.npu.")) and
   binding.get("name") in (name,"_npu_"+name),
   "actual installed TorchNPU graph export identity, never foreign callable: "+name)
 return record
def pa_graph_identity(record):
 validate_pa_graph_api(record)
 def stable(binding):
  value={k:binding.get(k) for k in ("callable","kind","module","qualname","name","doc","text_signature")}
  for key in ("signature","source_file","source"):
   observed=binding[key];value[key]=dict(ok=observed["ok"],value=observed["value"] if observed["ok"] else None,
    error_type=None if observed["ok"] else observed["error"]["type"])
  if "atb_provenance" in binding:value["atb_provenance"]=binding["atb_provenance"]
  return value
 return {"workspace":{"binding":stable(record["workspace"]["binding"]),"dispatcher":record["workspace"]["dispatcher"]},
  "graph":{k:stable(v["binding"]) for k,v in record["graph"].items()},"source_callsite_sha256":record["source_callsite_sha256"]}

def collect_wrapper(module):
 file=getattr(module,"__file__",None)
 source=safe_observe(lambda:Path(file).read_text())
 return {"file":file,"file_sha256":safe_observe(lambda:hashlib.sha256(Path(file).read_bytes()).hexdigest()),
  "module_source":source,"DeviceOperator_is_BaseDeviceAdaptor":getattr(module,"DeviceOperator",None) is getattr(module,"BaseDeviceAdaptor",object()),
  "wrapper":callable_observation(getattr(getattr(module,"BaseDeviceAdaptor",None),"reshape_and_cache",None))}
def device_nodes():
 return sorted(str(p) for p in Path("/dev").iterdir() if p.name.startswith("davinci") or p.name in ("devmm_svm","hisi_hdc"))
def device_fds():
 fds=[]
 for p in Path("/proc/self/fd").iterdir():
  try:destination=os.readlink(p)
  except FileNotFoundError:continue
  if any(k in destination for k in ("/dev/davinci","/dev/devmm_svm","/dev/hisi_hdc")):fds.append({"fd":p.name,"target":destination})
 return sorted(fds,key=lambda x:int(x["fd"]))
def flags(torch_npu):
 result={"device_nodes":safe_observe(device_nodes),"Ascend_fds":safe_observe(device_fds)}
 result["torch_npu_initialized"]=safe_observe(lambda:torch_npu.npu.is_initialized())
 return result
def validate_observation(observation,source,files):
 require(observation.get("schema")=="sparq.actual-no-device-observations/v5" and observation.get("source_manifest")==source and
  observation.get("script_sha256")==files["preflight.py"] and observation.get("collection_finished") is True,
  "complete original observer saved BEFORE assertion")
 for stage in ("after_torch_import","after_source_import"):
  f=observation["flags"][stage]
  require(all(x["ok"] and x["error"] is None for x in f.values()) and
   f["device_nodes"]["value"]==[] and f["Ascend_fds"]["value"]==[] and
   f["torch_npu_initialized"]["value"] is False,"actual CPU-only imports/observations initialized a device or opened Ascend FD")
 require(observation["device_nodes_before"]==[] and observation["Ascend_fds_before"]==[],"actual initial CPU-only nodes/FD")
 require(observation["source_import"]["ok"],"actual original source import failed")
 w=observation["wrapper"]
 require(w["file"]==str(NATIVE_SOURCE) and w["file_sha256"]["ok"] and w["file_sha256"]["value"]==NATIVE_SOURCE_SHA and
  w["module_source"]["ok"] and w["DeviceOperator_is_BaseDeviceAdaptor"] is True,"actual unchanged original native wrapper source and binding")
 wrapper=wrapper_source_contract(w["module_source"]["value"])
 require(observation["source_import"]["ok"],"actual original source import failed")
 exports=validate_exports(observation["exports_after_source_import"])
 validate_pa_graph_api(observation["pa_graph_after_source_import"])
 return wrapper,exports
def validate_precision_smoke(report):
 import math
 from precision_oracle import PROTOCOL
 require(type(report) is dict and report.get("protocol")==PROTOCOL and
  report.get("oracle_sha256")==sha(Path(__file__).parent/"precision_oracle.py") and
  report.get("torch_npu_initialized_after") is False,"actual this-source no-device CPU32 oracle")
 cases=report.get("cases",[])
 require(len(cases)==2 and {x.get("batch") for x in cases}=={1,2} and
  all(x.get("strict_support32") is True and x.get("conditional_cpu64_equal") is True and
      x.get("full_support_domain")==3 and type(x.get("maximum_error")) in (int,float) and
      math.isfinite(x["maximum_error"]) and x["maximum_error"]<=1e-10 for x in cases),
      "actual CPU32 selection and CPU64 conditional math smoke before any device")
 return report
def validate_cpu_golden(report):
 require(type(report) is dict and report.get("schema")=="sparq.actual-cpu-golden-smoke/v4" and report.get("device")=="cpu" and
  report.get("source_sha256")==sha(Path(__file__).parent/"numeric_gate.py") and report.get("torch_npu_initialized_after") is False and
  report.get("npu_executed") is False,"actual this-source no-device CPU-FP64 toy golden receipt")
 cases=report.get("cases",[])
 require(len(cases)==4 and {(x.get("batch"),x.get("reallocation")) for x in cases}=={(b,m) for b in (1,2) for m in (False,True)} and
  all(x.get("all_outputs_dtype")=="torch.float64" and x.get("all_outputs_cpu") is True and
   x.get("finite") is True and x.get("independent_scalar_support_equal") is True and
   type(x.get("maximum_scalar_error")) in (int,float) and x["maximum_scalar_error"]<=1e-10 for x in cases),
  "actual four CPU golden/meanOFFON/scalar-oracle cases, not NPU admission")
 validate_precision_smoke(report.get("registered_precision_smoke"))
 return report
def cpu_golden_smoke(torch,torch_npu):
 from numeric_gate import golden,HEADS,DIM,BLOCK
 from sparq_token_v4.oracle import reference
 from precision_oracle import PROTOCOL,independent
 cases=[];precision_cases=[]
 for batch in (1,2):
  rows=[[2*i,2*i+1] for i in range(batch)];lengths=[33,129][:batch]
  query=((torch.arange(batch*HEADS*DIM,dtype=torch.float32).reshape(batch,HEADS,DIM)%7-3)/64).to(torch.bfloat16)
  kc=((torch.arange(2*batch*BLOCK*DIM,dtype=torch.float32).reshape(2*batch,BLOCK,1,DIM)%17-8)/64).to(torch.bfloat16)
  vc=((torch.arange(2*batch*BLOCK*DIM,dtype=torch.float32).reshape(2*batch,BLOCK,1,DIM)%31-15)/64).to(torch.bfloat16)
  for correction in (False,True):
   out,support,means,alpha=golden(torch,query,kc,vc,rows,lengths,32,128,1,correction)
   maximum=0.
   for i,(row,n) in enumerate(zip(rows,lengths)):
    ids=torch.tensor(row,dtype=torch.long)
    keys=kc.index_select(0,ids).view(-1,DIM)[:n].double().tolist()
    values=vc.index_select(0,ids).view(-1,DIM)[:n].double().tolist()
    scalar=reference(query[i].double().tolist(),keys,values,32,128,1,correction)
    require(support[i].tolist()==scalar["support"],"actual CPU FP64 independently selected scalar support")
    expected=torch.tensor(scalar["output"],dtype=torch.float64)
    maximum=max(maximum,float((out[i]-expected).abs().max()),
     max(abs(float(x)-y) for x,y in zip(means[i],scalar["mean"])),
     max(abs(float(x)-y) for x,y in zip(alpha[i],scalar["alpha"])))
   cases.append(dict(batch=batch,reallocation=correction,all_outputs_dtype="torch.float64",
    all_outputs_cpu=all(x.device.type=="cpu" for x in (out,means,alpha)),
    finite=bool(torch.isfinite(out).all() and torch.isfinite(means).all() and torch.isfinite(alpha).all()),
    independent_scalar_support_equal=True,maximum_scalar_error=maximum))
  short_lengths=[3]*batch
  short_out,short_support,_,_=golden(torch,query,kc,vc,rows,short_lengths,32,128,1,False)
  checked=independent(torch,query,kc,vc,rows,short_lengths,short_support,capacity=256)
  error=float((checked["conditional_pa"]-short_out).abs().max())
  precision_cases.append(dict(batch=batch,strict_support32=all(x.tolist()==[0,1,2] for x in checked["supports"]),
    conditional_cpu64_equal=bool(torch.allclose(checked["conditional_pa"],short_out,rtol=1e-10,atol=1e-12)),
    full_support_domain=3,maximum_error=error))
 precision_smoke=dict(protocol=PROTOCOL,oracle_sha256=sha(Path(__file__).parent/"precision_oracle.py"),
  torch_npu_initialized_after=torch_npu.npu.is_initialized(),cases=precision_cases)
 report=dict(registered_precision_smoke=precision_smoke,schema="sparq.actual-cpu-golden-smoke/v4",device="cpu",source_sha256=sha(Path(__file__).parent/"numeric_gate.py"),
  torch_npu_initialized_after=torch_npu.npu.is_initialized(),npu_executed=False,cases=cases)
 return validate_cpu_golden(report)


def validate_abi(report,source,files):
 require(report.get("schema")=="sparq.actual-no-device-abi/v5" and report.get("status")=="actual-schema-checked" and
  report.get("source_manifest")==source and report.get("sources_before")==report.get("sources_after")==files and
  report.get("script_sha256")==files["preflight.py"],"complete actual original this-source no-device ABI")
 observation=load(report["original_observations"])
 require(observation==report["actual_observations"],"original pre-assertion observer Ref/inline bytes disagree")
 wrapper,actual=validate_observation(observation,source,files)
 require(report.get("actual_wrapper_native_contract")==wrapper and report.get("actual_exports")==actual and
  report.get("actual_pa_graph_api")==observation["pa_graph_after_source_import"],
  "actual wrapper/native signature and exact keyword mapping; no incompatible union")
 require(report.get("actual_device_initialized_before") is False and report.get("actual_device_initialized_after") is False and
  report.get("actual_guest_device_nodes_before")==[] and report.get("actual_guest_device_nodes_after")==[] and
  report.get("actual_Ascend_fds_before")==[] and report.get("actual_Ascend_fds_after")==[] and
  report.get("npu_executed") is False and report.get("native_export_arguments_checked") is True and
  report.get("actual_source_import_checked") is True and report.get("primary_error") is None and report.get("secondary_errors")==[],
  "no initialized/failed/partial original receipt promotion")
 validate_cpu_golden(report.get("actual_cpu_golden"))
 from cpu_smoke import validate as validate_ann_cpu
 validate_ann_cpu(report["actual_author_ann_cpu"])
 require(report.get("stack",{}).get("vllm_ascend")=="0.23.0" and report["stack"].get("torch") and report["stack"].get("torch_npu"),"actual original stack")
 return report
def recheck_preinit(torch,torch_npu,report,source,files):
 validate_abi(report,source,files)
 initialized=getattr(torch_npu.npu,"is_initialized",None)
 require(callable(initialized) and initialized() is False,"same-process no device context before native schema")
 require(export_contract_identity(exports(torch,torch_npu))==export_contract_identity(report["actual_exports"]),"actual same-process schemas/exports drift before set_device")
 require(pa_graph_identity(collect_pa_graph_api(torch,torch_npu))==pa_graph_identity(report["actual_pa_graph_api"]),
  "actual same-process source-bound PA workspace/graph exports drift before set_device")
 require(initialized() is False,"same-process schema check unexpectedly initialized device")
 return report
def mapped_libraries():
 mapped={}
 for line in Path("/proc/self/maps").read_text().splitlines():
  words=line.split()
  if len(words)>=6 and words[-1].startswith("/") and ".so" in words[-1] and any(k in words[-1].lower() for k in ("torch_npu","vllm","opapi")):
   p=Path(words[-1])
   if p.is_file() and not p.is_symlink():mapped[str(p)]=sha(p)
 return mapped
def save_observations(a,observation):
 target=a.output.parent/"ABI_OBSERVATIONS.json";image_ref=write_new(target,observation)
 original={"path":str(a.host_output_root/target.name),"sha256":image_ref["sha256"]}
 bound(original["path"],original["sha256"])
 return original
def probe(a):
 root=Path(__file__).resolve().parent;source,files=source_identity(root,a.source_manifest,a.source_manifest_sha256,"runtime")
 require(a.output and a.output.parent==Path("/sparq-results") and not a.output.exists() and
  a.host_output_root and a.host_output_root.is_absolute() and a.host_output_root.is_dir() and not a.host_output_root.is_symlink(),
  "explicit new owned no-device ABI leaf and identical readonly host-output alias")
 observation={"schema":"sparq.actual-no-device-observations/v5","source_manifest":source,"script_sha256":files["preflight.py"],
  "actual_argv":[sys.executable,"-B",*sys.argv],"device_nodes_before":device_nodes(),"Ascend_fds_before":device_fds(),
  "flags":{},"imports":{},"collection_finished":False,"npu_executed":False,"numerical_support_verified":False,"ready":False}
 a.observation=observation;a.observation_ref=None
 # Capture actual modules and signatures first. No API/numerical assertion may suppress their raw evidence.
 try:
  import torch,torch_npu
  observation["imports"]={"torch":{"file":torch.__file__,"version":torch.__version__},
   "torch_npu":{"file":torch_npu.__file__,"version":torch_npu.__version__}}
  observation["flags"]["after_torch_import"]=flags(torch_npu)
  observation["exports_before_source_import"]=collect_exports(torch,torch_npu)
  module_observation=safe_observe(import_device_operator)
  module=module_observation["value"];observation["source_import"]={"ok":module_observation["ok"],"error":module_observation["error"]}
  observation["wrapper"]=collect_wrapper(module) if module is not None else None
  observation["exports_after_source_import"]=collect_exports(torch,torch_npu)
  observation["pa_graph_after_source_import"]=collect_pa_graph_api(torch,torch_npu)
  observation["flags"]["after_source_import"]=flags(torch_npu)
  observation["actually_mapped_libraries"]=safe_observe(mapped_libraries)
  observation["actual_stack"]=safe_observe(lambda:{"vllm_ascend":importlib.metadata.version("vllm-ascend"),
   "torch_npu":torch_npu.__version__,"torch":torch.__version__})
  observation["collection_finished"]=True
 except BaseException as error:
  observation["collection_error"]=error_record(error)
  # Main persists this partial observation without replacing the original import/collection error.
  raise
 a.observation_ref=save_observations(a,observation)
 require(os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD")=="0" and os.environ.get("PYTHONDONTWRITEBYTECODE")=="1","no backend autoload/bytecode")
 wrapper,actual=validate_observation(observation,source,files)
 cpu_smoke=cpu_golden_smoke(torch,torch_npu)
 from cpu_smoke import smoke as author_ann_cpu_smoke
 ann_cpu=author_ann_cpu_smoke(torch,torch_npu,a.output.parent,a.host_output_root)
 require(observation["actually_mapped_libraries"]["ok"] and observation["actual_stack"]["ok"],"complete native mapped libraries/stack evidence")
 mapped=observation["actually_mapped_libraries"]["value"];stack=observation["actual_stack"]["value"]
 require(str(Path(torch_npu._C.__file__)) in mapped,"actual mapped TorchNPU ABI library")
 initialized=getattr(torch_npu.npu,"is_initialized",None)
 require(initialized() is False and device_nodes()==[] and device_fds()==[],"CPU golden/source imports unexpectedly initialized/opened device")
 _,after=source_identity(root,a.source_manifest,a.source_manifest_sha256,"runtime");require(after==files,"actual source closure before/after")
 report={"schema":"sparq.actual-no-device-abi/v5","status":"actual-schema-checked","source_manifest":source,"sources_before":files,"sources_after":after,
  "original_observations":a.observation_ref,"actual_observations":observation,"actual_wrapper_native_contract":wrapper,
  "actual_exports":actual,"actual_pa_graph_api":observation["pa_graph_after_source_import"],"actual_cpu_golden":cpu_smoke,"actual_author_ann_cpu":ann_cpu,"actually_mapped_libraries":mapped,"stack":stack,
  "actual_argv":[sys.executable,"-B",*sys.argv],
  "actual_guest_device_nodes_before":observation["device_nodes_before"],"actual_guest_device_nodes_after":device_nodes(),
  "actual_Ascend_fds_before":observation["Ascend_fds_before"],"actual_Ascend_fds_after":device_fds(),
  "actual_device_initialized_before":False,"actual_device_initialized_after":False,"native_export_arguments_checked":True,
  "actual_source_import_checked":True,"script_sha256":files["preflight.py"],"primary_error":None,"secondary_errors":[],
  "npu_executed":False,"numerical_support_verified":False,"ready":False}
 validate_abi(report,source,files);r=write_new(a.output,report)
 print("MAIN_SPARQ_TOKEN_V5_NO_DEVICE "+json.dumps({"actual_abi":r,"original_observations":a.observation_ref,"npu_executed":False,"ready":False}),flush=True)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 p.add_argument("--source-manifest",type=Path);p.add_argument("--source-manifest-sha256");p.add_argument("--output",type=Path)
 p.add_argument("--host-output-root",type=Path);a=p.parse_args()
 if not a.execute:print(json.dumps({"default_enabled":False,"npu_executed":False,"ready":False}));return
 require(a.source_manifest and a.source_manifest_sha256,"actual source Ref required")
 try:probe(a)
 except BaseException as error:
  secondary=[]
  # Preserve the original error; never replace it with an observation/cleanup error.
  if getattr(a,"observation",None) is not None and not getattr(a,"observation_ref",None):
   try:a.observation_ref=save_observations(a,a.observation)
   except BaseException as extra:secondary.append(error_record(extra))
  if a.output and a.output.parent==Path("/sparq-results") and a.output.parent.is_dir() and not a.output.exists():
   r=write_new(a.output,{"schema":"sparq.actual-no-device-abi/v5","status":"failed","primary_error":error_record(error),
    "secondary_errors":secondary,"original_observations":getattr(a,"observation_ref",None),"actual_observations":getattr(a,"observation",None),
    "script_sha256":sha(Path(__file__)),"actual_argv":[sys.executable,"-B",*sys.argv],
    "npu_executed":False,"numerical_support_verified":False,"ready":False})
   print("MAIN_SPARQ_TOKEN_V5_NO_DEVICE "+json.dumps({"actual_abi":r,"status":"failed","ready":False}),flush=True)
  raise
if __name__=="__main__":main()

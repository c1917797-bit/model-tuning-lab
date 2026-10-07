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
def validate_exports(records):
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
   "matched_single_signatures":record["matched_single_signatures"],"single_signature_matched":record["single_signature_matched"]}
 return result
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
 return wrapper,exports
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
 return report
def cpu_golden_smoke(torch,torch_npu):
 from numeric_gate import golden,HEADS,DIM,BLOCK
 from sparq_token_v4.oracle import reference
 cases=[]
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
 report=dict(schema="sparq.actual-cpu-golden-smoke/v4",device="cpu",source_sha256=sha(Path(__file__).parent/"numeric_gate.py"),
  torch_npu_initialized_after=torch_npu.npu.is_initialized(),npu_executed=False,cases=cases)
 return validate_cpu_golden(report)


def validate_abi(report,source,files):
 require(report.get("schema")=="sparq.actual-no-device-abi/v5" and report.get("status")=="actual-schema-checked" and
  report.get("source_manifest")==source and report.get("sources_before")==report.get("sources_after")==files and
  report.get("script_sha256")==files["preflight.py"],"complete actual original this-source no-device ABI")
 observation=load(report["original_observations"])
 require(observation==report["actual_observations"],"original pre-assertion observer Ref/inline bytes disagree")
 wrapper,actual=validate_observation(observation,source,files)
 require(report.get("actual_wrapper_native_contract")==wrapper and report.get("actual_exports")==actual,
  "actual wrapper/native signature and exact keyword mapping; no incompatible union")
 require(report.get("actual_device_initialized_before") is False and report.get("actual_device_initialized_after") is False and
  report.get("actual_guest_device_nodes_before")==[] and report.get("actual_guest_device_nodes_after")==[] and
  report.get("actual_Ascend_fds_before")==[] and report.get("actual_Ascend_fds_after")==[] and
  report.get("npu_executed") is False and report.get("native_export_arguments_checked") is True and
  report.get("actual_source_import_checked") is True and report.get("primary_error") is None and report.get("secondary_errors")==[],
  "no initialized/failed/partial original receipt promotion")
 validate_cpu_golden(report.get("actual_cpu_golden"))
 require(report.get("stack",{}).get("vllm_ascend")=="0.23.0" and report["stack"].get("torch") and report["stack"].get("torch_npu"),"actual original stack")
 return report
def recheck_preinit(torch,torch_npu,report,source,files):
 validate_abi(report,source,files)
 initialized=getattr(torch_npu.npu,"is_initialized",None)
 require(callable(initialized) and initialized() is False,"same-process no device context before native schema")
 require(export_contract_identity(exports(torch,torch_npu))==export_contract_identity(report["actual_exports"]),"actual same-process schemas/exports drift before set_device")
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
  module_observation=safe_observe(lambda:__import__("vllm_ascend.device.device_op",fromlist=["DeviceOperator"]))
  module=module_observation["value"];observation["source_import"]={"ok":module_observation["ok"],"error":module_observation["error"]}
  observation["wrapper"]=collect_wrapper(module) if module is not None else None
  observation["exports_after_source_import"]=collect_exports(torch,torch_npu)
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
 require(observation["actually_mapped_libraries"]["ok"] and observation["actual_stack"]["ok"],"complete native mapped libraries/stack evidence")
 mapped=observation["actually_mapped_libraries"]["value"];stack=observation["actual_stack"]["value"]
 require(str(Path(torch_npu._C.__file__)) in mapped,"actual mapped TorchNPU ABI library")
 initialized=getattr(torch_npu.npu,"is_initialized",None)
 require(initialized() is False and device_nodes()==[] and device_fds()==[],"CPU golden/source imports unexpectedly initialized/opened device")
 _,after=source_identity(root,a.source_manifest,a.source_manifest_sha256,"runtime");require(after==files,"actual source closure before/after")
 report={"schema":"sparq.actual-no-device-abi/v5","status":"actual-schema-checked","source_manifest":source,"sources_before":files,"sources_after":after,
  "original_observations":a.observation_ref,"actual_observations":observation,"actual_wrapper_native_contract":wrapper,
  "actual_exports":actual,"actual_cpu_golden":cpu_smoke,"actually_mapped_libraries":mapped,"stack":stack,
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

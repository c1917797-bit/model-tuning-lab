"""MAIN-owned image no-device actual exports/source probe; default OFF."""
import argparse,hashlib,importlib.metadata,inspect,json,os,re
from pathlib import Path
from receipt import *
REQUIRED={"_npu_paged_attention":{"query","key_cache","value_cache","num_heads","num_kv_heads","scale_value","block_table","context_lens","out"},
 "_npu_reshape_and_cache":{"key","value","key_cache","value_cache","slot_mapping"}}
def exports(torch,torch_npu):
 all_schemas=list(torch._C._jit_get_all_schemas());records={}
 for name,needed in REQUIRED.items():
  fn=getattr(torch_npu,name,None);require(callable(fn),"actual native export missing: "+name)
  schemas=sorted([s for s in all_schemas if str(s.name).split("::")[-1] in (name,name.lstrip("_"))],key=str)
  sources=[];found=set();single_match=False
  for s in schemas:
   names={a.name for a in s.arguments};sources.append({"kind":"actual_dispatcher","text":str(s)})
   found|=names;single_match|=names>=needed
  try:
   sig=inspect.signature(fn);sources.append({"kind":"actual_python_signature","text":str(sig)});found|=set(sig.parameters);single_match|=set(sig.parameters)>=needed
  except (ValueError,TypeError):pass
  doc=getattr(fn,"__doc__",None);ts=getattr(fn,"__text_signature__",None)
  for kind,text in (("actual_binding_doc",doc),("actual_binding_text_signature",ts)):
   if type(text) is str and text.strip():
    names={a for a in needed if re.search(r"\b"+re.escape(a)+r"\b",text)}
    sources.append({"kind":kind,"text":text});found|=names;single_match|=names>=needed
  require(single_match and found>=needed,"actual source-bound native binding lacks required argument names BEFORE any device init: "+name)
  records[name]={"required_arguments":sorted(needed),"observed_arguments":sorted(found),"actual_binding_kind":type(fn).__name__,
    "actual_binding_module":getattr(fn,"__module__",None),"actual_signatures":sources,
    "numerical_support_verified":False,"single_signature_matched":single_match}
 return records

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
 require(report.get("schema")=="sparq.actual-no-device-abi/v4" and report.get("status")=="actual-schema-checked" and
  report.get("source_manifest")==source and report.get("sources_before")==report.get("sources_after")==files and
  report.get("script_sha256")==files["preflight.py"],"complete actual original this-source no-device ABI")
 require(report.get("actual_device_initialized_before") is False and report.get("actual_device_initialized_after") is False and
  report.get("actual_guest_device_nodes_before")==[] and report.get("actual_guest_device_nodes_after")==[] and report.get("npu_executed") is False and report.get("native_export_arguments_checked") is True and
  report.get("actual_source_import_checked") is True and report.get("primary_error") is None and report.get("secondary_errors")==[],
  "original no-device source/exports checked, no initialised/failed receipt promotion")
 validate_cpu_golden(report.get("actual_cpu_golden"))
 require(set(report.get("actual_exports",{}))==set(REQUIRED),"both real native exports required")
 for name,needed in REQUIRED.items():
  r=report["actual_exports"][name]
  require(r.get("required_arguments")==sorted(needed) and set(r.get("observed_arguments",[]))>=needed and
   r.get("actual_signatures") and r.get("single_signature_matched") is True,"one complete original signature, never union of incompatible overloads")
  require(r.get("numerical_support_verified") is False,"schema receipt is never numerical support")
 require(report.get("stack",{}).get("vllm_ascend")=="0.23.0" and report["stack"].get("torch") and report["stack"].get("torch_npu"),"actual original stack")
 return report
def recheck_preinit(torch,torch_npu,report,source,files):
 validate_abi(report,source,files)
 initialized=getattr(torch_npu.npu,"is_initialized",None)
 require(callable(initialized) and initialized() is False,"same-process no device context before native schema")
 require(exports(torch,torch_npu)==report["actual_exports"],"actual same-process schemas/exports drift before set_device")
 require(initialized() is False,"same-process schema check unexpectedly initialized device")
 return report

def device_nodes():
 return sorted(str(p) for p in Path("/dev").iterdir() if p.name.startswith("davinci") or p.name in ("devmm_svm","hisi_hdc"))
def probe(a):
 root=Path(__file__).resolve().parent;source,files=source_identity(root,a.source_manifest,a.source_manifest_sha256,"runtime")
 require(a.output and a.output.parent==Path("/sparq-results") and not a.output.exists(),"new owned no-device ABI leaf")
 require(os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD")=="0" and os.environ.get("PYTHONDONTWRITEBYTECODE")=="1","no backend autoload/bytecode")
 before=device_nodes();require(before==[],"actual CPU-only ABI guest exposes Ascend node")
 import torch,torch_npu
 initialized=getattr(torch_npu.npu,"is_initialized",None);require(callable(initialized) and initialized() is False,"actual no-device initialization flag required")
 actual=exports(torch,torch_npu)
 cpu_smoke=cpu_golden_smoke(torch,torch_npu)
 import vllm_ascend.device.device_op as module
 require(str(Path(module.__file__))=="/vllm-workspace/vllm-ascend/vllm_ascend/device/device_op.py" and sha(Path(module.__file__))=="de6a8547df3ff92bf8666e475be56840005cccb3272452c2d6cac4c3f1ddff47","actual original native writer wrapper bytes")
 require(module.DeviceOperator is module.BaseDeviceAdaptor and importlib.metadata.version("vllm-ascend")=="0.23.0","actual unchanged original adapter and deployed version")
 require(initialized() is False,"native exports/import probe unexpectedly initialized device")
 _,after=source_identity(root,a.source_manifest,a.source_manifest_sha256,"runtime");require(after==files,"actual source closure before/after")
 mapped={}
 for line in Path("/proc/self/maps").read_text().splitlines():
  words=line.split()
  if len(words)>=6 and words[-1].startswith("/") and ".so" in words[-1] and any(k in words[-1].lower() for k in ("torch_npu","vllm","opapi")):
   p=Path(words[-1])
   if p.is_file() and not p.is_symlink():mapped[str(p)]=sha(p)
 require(str(Path(torch_npu._C.__file__)) in mapped,"actual mapped TorchNPU ABI library")
 report={"schema":"sparq.actual-no-device-abi/v4","status":"actual-schema-checked","source_manifest":source,"sources_before":files,"sources_after":after,
   "actual_exports":actual,"actual_cpu_golden":cpu_smoke,"actually_mapped_libraries":mapped,"stack":{"vllm_ascend":"0.23.0","torch_npu":torch_npu.__version__,"torch":torch.__version__},
   "actual_argv":[__import__("sys").executable,"-B",*__import__("sys").argv],
   "actual_imported_origins":{name:bound(module.__file__,sha(Path(module.__file__))) for name,module in (("torch",torch),("torch_npu",torch_npu))},
   "actual_guest_device_nodes_before":before,"actual_guest_device_nodes_after":device_nodes(),
   "actual_device_initialized_before":False,"actual_device_initialized_after":False,"native_export_arguments_checked":True,
   "actual_source_import_checked":True,"script_sha256":files["preflight.py"],"primary_error":None,"secondary_errors":[],
   "npu_executed":False,"numerical_support_verified":False,"ready":False}
 validate_abi(report,source,files);r=write_new(a.output,report)
 print("MAIN_SPARQ_TOKEN_V4_NO_DEVICE "+json.dumps({"actual_abi":r,"npu_executed":False,"ready":False}),flush=True)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 p.add_argument("--source-manifest",type=Path);p.add_argument("--source-manifest-sha256");p.add_argument("--output",type=Path);a=p.parse_args()
 if not a.execute:print(json.dumps({"default_enabled":False,"npu_executed":False,"ready":False}));return
 require(a.source_manifest and a.source_manifest_sha256,"actual source Ref required")
 try:probe(a)
 except BaseException as error:
  if a.output and a.output.parent==Path("/sparq-results") and a.output.parent.is_dir() and not a.output.exists():
   r=write_new(a.output,{"schema":"sparq.actual-no-device-abi/v4","status":"failed","primary_error":repr(error),
     "script_sha256":sha(Path(__file__)),"actual_argv":[__import__("sys").executable,"-B",*__import__("sys").argv],
     "npu_executed":None,"numerical_support_verified":False,"ready":False})
   print("MAIN_SPARQ_TOKEN_V4_NO_DEVICE "+json.dumps({"actual_abi":r,"status":"failed","ready":False}),flush=True)
  raise
if __name__=="__main__":main()

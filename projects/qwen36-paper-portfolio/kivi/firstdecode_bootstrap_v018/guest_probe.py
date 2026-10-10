"""Actual same660 CPU import/parser and all4 tiny N1 preconditions; not model PASS."""
import argparse,importlib,importlib.util,inspect,json,os,sys,time
from pathlib import Path
def need(v,m):
 if not v:raise ValueError(m)
def run(mode,sha,output,port,cache_bytes):
 here=Path(__file__).resolve().parent
 spec=importlib.util.spec_from_file_location("_kivi_firstdecode_source_loader",here/"loader.py")
 l=importlib.util.module_from_spec(spec);sys.modules[spec.name]=l;spec.loader.exec_module(l)
 limit=(8 if mode=="cpu" else 64)*1024**3
 m,source,mods,adapter,new,own=l.load(sha,memory_limit=limit)
 torch=importlib.import_module("torch");npu=importlib.import_module("torch_npu")
 initial=torch.npu.is_initialized()
 if mode=="cpu":need(initial is False,"Devices[]CPU did not initialize NPU")
 fn=getattr(npu,"get_npu_format");path=Path(inspect.getfile(fn)).resolve()
 binding=dict(module="torch_npu",attribute="get_npu_format",runtime_path=str(path),
              archive_ref=m["native_format_patch_chain"]["format"],patch_chain=m["native_format_patch_chain"])
 adapter.OPS_PACKET=torch.ops.npu.get_npu_format
 original,enum,observation=mods["format_policy"].bind_getter(npu,binding,adapter,adapter.OPS_PACKET)
 entry=l.module("_kivi_firstdecode_server_entry",l.own(m,"server_entry.py"))
 api=importlib.import_module("vllm.entrypoints.openai.api_server")
 need(l.ref(api.__file__)["sha256"]==m["installed_api_server_sha256"],"actual deployed api_server")
 args=entry.parse_native(api,port,cache_bytes)
 proof=l.module("_kivi_firstdecode_config_proof",l.own(m,"config_cpu.py"))
 effective=None
 if mode=="cpu":effective=entry.actual_config_precheck(api,args,mode,torch,proof,cache_bytes)
 canary=[]
 if mode=="n1":
  native=importlib.import_module("vllm_ascend.worker.worker").NPUWorker
  own["cann_python"].cached(required=True,memcpy_required=True)
  for v in(native,native.initialize_from_config,native.load_model):
   mods["layout"][1].source_file(v,"c392da56095b255d47fe5ad7ffdfbedd269fe69851690e89a8d2ed44c073f6c3")
  need(torch.npu.device_count()==4,"only own four logical devices")
  for device in range(4):
   torch.npu.set_device(device)
   a=torch.tensor([1.,2.],device="npu:%d"%device);b=a+3
   torch.npu.synchronize()
   value=b.cpu().tolist();fmt=mods["format_policy"].serial(original(b),enum)
   need(value==[4.,5.],"all4 actual tensor/sync values")
   boundary=l.module("_kivi_actual_runtime_boundary",l.own(m,"runtime_boundary.py"))
   compiled=l.framework(mods,torch,npu,device)
   props,driver_proof=boundary.core_properties(torch,compiled["triton"],device,l.ref)
   allocator_sample=new["installer"].allocator_observer(torch,device,lambda label,row:row)
   allocator_proof=allocator_sample("N1-AFTER-TINY")
   canary.append(dict(logical=device,physical=device+4,output=value,format=fmt,
    actual_driver_properties=driver_proof,allocator_observation=allocator_proof))
  effective=entry.actual_config_precheck(api,args,mode,torch,proof,cache_bytes)
 else:need(torch.npu.is_initialized()is False,"parser/source import did not initialize NPU")
 memory=own["memory"].memory(expected_limit=limit)
 own["memory"].consume_memory(memory,expected_limit=limit)
 return l.publish(output,dict(schema="kivi.actual-firstdecode-preflight/v1",
  status="CPU_IMPORT_PARSER_CHECKED"if mode=="cpu"else"N1_ALL4_TINY_CHECKED",
  source=source,mode=mode,actual_identity=mods["layout"][1].identity(),memory=memory,
  cann_python_binding=own["cann_python_binding"],cann_cached_after_imports=own["cann_python"].cached(),
   native_format_binding=binding,getter=observation,native_argv=entry.native_argv(port,cache_bytes),
  actual_parsed=dict(async_scheduling=args.async_scheduling,enable_chunked_prefill=args.enable_chunked_prefill,
   enforce_eager=args.enforce_eager,mamba_cache_mode=args.mamba_cache_mode,enable_prefix_caching=args.enable_prefix_caching),
  canary=canary,actual_configuration=effective,native_worker_import_qualified=(mode=="n1"),
  native_worker_cpu_scope="archived byte compile only; no native class import in CPU branch",
  model_ready=False,performance_ready=False,registered_worker_factory_checked=False))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 p.add_argument("--mode",choices=["cpu","n1"]);p.add_argument("--source-manifest-sha256")
 p.add_argument("--output",type=Path);p.add_argument("--port",type=int,default=8250)
 p.add_argument("--cache-bytes",type=int,default=6*1024**3);a=p.parse_args()
 if not a.execute:print(json.dumps(dict(enabled=False,model_ready=False)));return 0
 need(a.mode and a.output is not None,"explicit own stage/output")
 run(a.mode,a.source_manifest_sha256,a.output,a.port,a.cache_bytes);return 0
if __name__=="__main__":raise SystemExit(main())

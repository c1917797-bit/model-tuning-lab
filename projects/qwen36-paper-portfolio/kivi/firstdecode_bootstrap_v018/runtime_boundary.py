"""Actual packed3 driver ABI plus source-bound worker-init failure handoff.
No Torch import at module load, no controller, no retry, no device admission.
"""
import importlib,inspect,json,time,traceback
from pathlib import Path
HELPER_SHA="f94d81f163f0076e8243990dd687f7ec8d42ce1ed30d67eea3155bf1c3a073a4"
HELPER_BYTES=2090
HELPER_NAME="vllm_ascend.ops.triton.triton_utils"
def need(v,m):
 if not v:raise ValueError(m)
def core_properties(torch,triton,rank,read_ref):
 need(type(rank)is int and rank in range(4) and torch.npu.is_initialized() is True
  and torch.npu.device_count()==4 and torch.npu.current_device()==rank,
  "actual initialized current logical rank in owned TP4")
 rt=importlib.import_module(HELPER_NAME)
 source=read_ref(Path(rt.__file__).resolve())
 need(source["sha256"]==HELPER_SHA and source["bytes"]==HELPER_BYTES
  and rt.__name__==HELPER_NAME and rt.HAS_TRITON is True
  and rt.torch is torch and rt.triton is triton,"exact actual same660 helper and compiler objects")
 for fn in(rt.init_device_properties_triton,rt.get_aicore_num,rt.get_vectorcore_num):
  need(Path(inspect.getsourcefile(fn)).resolve()==Path(source["path"]),"unwrapped original helper callable source")
 # This is the actual018c numeric.py API; torch_npu NPUDeviceProperties is not it.
 raw=triton.runtime.driver.active.utils.get_device_properties(torch.npu.current_device())
 rt.init_device_properties_triton()
 need(type(raw)is dict and raw.get("num_aicore")==rt.get_aicore_num()
  and raw.get("num_vectorcore")==rt.get_vectorcore_num(),"actual deployed driver/helper properties agree")
 props={key:raw.get(key)for key in("num_aicore","num_vectorcore")}
 need(all(type(v)is int and 0<v<=65535 for v in props.values()),"actual bounded compiler core counts, no fallback")
 need(torch.npu.current_device()==rank,"same actual device after driver read")
 text=repr(raw);need(len(text)<=16384,"whole bounded driver representation")
 return props,dict(schema="kivi.actual-rank-driver-properties/v1",logical_rank=rank,
  current_device=rank,helper_source=source,device_properties=props,raw_properties_repr=text,
  driver_type_module=type(triton.runtime.driver.active).__module__,
  driver_type_name=type(triton.runtime.driver.active).__qualname__,
  source_api="triton.runtime.driver.active.utils.get_device_properties(torch.npu.current_device())",
  model_ready=False,performance_ready=False,run_authority=False)
def fatal_path(recipe,rank):
 need(type(rank)is int and rank in range(4),"actual rank")
 return Path(recipe["diagnostic_root"])/("RANK-%d-FATAL.json"%rank)
def initialize(invoke,*,rank,recipe,recipe_ref,source_ref,helper_ref,identity,publish):
 """Preserve original exception; a publication failure is secondary stderr only."""
 try:return invoke()
 except BaseException as error:
  value=dict(schema="kivi.actual-worker-initialize-fatal/v1",rank=rank,
   identity=identity,container_id=recipe["container_id"],source_ref=source_ref,
   recipe_ref=recipe_ref,helper_ref=helper_ref,stage="initialize_from_config",
   observed_epoch_ns=time.time_ns(),
   primary=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()),
   model_ready=False,performance_ready=False,run_authority=False)
  try:publish(fatal_path(recipe,rank),value)
  except BaseException as secondary:
   print(json.dumps(dict(worker_first_fault=value,secondary_publication=repr(secondary))),flush=True)
  raise
class WorkerFatal(RuntimeError):
 def __init__(self,refs,rows):
  self.worker_fault_refs=refs
  self.worker_first_fault=rows[0]
  super().__init__("source-bound worker initialization fatal: rank%d %s: %s"%
   (rows[0]["rank"],rows[0]["primary"]["type"],rows[0]["primary"]["message"]))
def raise_if_any(c,recipe,recipe_ref,source_ref,helper_ref):
 """Pure bounded reads in existing startup loop, before health/observe/poll."""
 pairs=[]
 for rank in range(4):
  path=fatal_path(recipe,rank)
  if not path.exists():continue
  ref=c.ref(path);row=c.obj(ref)
  need(row["schema"]=="kivi.actual-worker-initialize-fatal/v1" and row["rank"]==rank
   and row["container_id"]==recipe["container_id"] and row["source_ref"]==source_ref
   and row["recipe_ref"]==recipe_ref and row["helper_ref"]==helper_ref
   and row["stage"]=="initialize_from_config","exact actual worker fatal source/recipe/rank")
  ident=row["identity"]
  need(type(ident)is dict and set(ident)=={"pid","start_ticks","cgroup"}
   and type(ident["pid"])is type(ident["start_ticks"])is int
   and ident["pid"]>0 and ident["start_ticks"]>0 and recipe["container_id"]in ident["cgroup"],
   "actual source-qualified worker identity")
  request=c.obj(c.ref(recipe["rank_request_paths"][str(rank)]))
  need(request["schema"]=="kivi.actual-rank-owner-request/v1" and request["rank"]==rank
   and request["source_ref"]==source_ref and request["container_id"]==recipe["container_id"]
   and request["identity"]==ident,"same original rank-owner request")
  primary=row["primary"]
  need(type(primary)is dict and set(primary)=={"type","message","traceback"}
   and all(type(v)is str for v in primary.values()) and primary["type"] and primary["traceback"]
   and type(row["observed_epoch_ns"])is int and row["observed_epoch_ns"]>0,
   "complete original exception not a success flag")
  need(row["model_ready"]is row["performance_ready"]is row["run_authority"]is False,"failure never permits run")
  pairs.append((ref,row))
 if pairs:
  pairs.sort(key=lambda p:(p[1]["observed_epoch_ns"],p[1]["rank"]))
  raise WorkerFatal([p[0]for p in pairs],[p[1]for p in pairs])
 return None

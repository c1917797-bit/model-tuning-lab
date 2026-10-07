"""Independent, bounded BEFORE-guard receipt; never changes the frozen guard."""
from __future__ import annotations
import hashlib
import inspect
import json
import os
from pathlib import Path
import sys
from v3_contract import V2,OBSERVER_SHA,RUNTIME,canonical,file_sha,require,source_contract
MAX_RECORD_BYTES=131072
def exclusive_json(path,record):
 data=canonical(record)+b"\n"
 require(len(data)<=MAX_RECORD_BYTES,"before-guard record byte cap exceeded")
 # No shared Writer, buffered events stream, overwrite, retry or import-time write.
 with Path(path).open("xb",buffering=0) as f:
  f.write(data);os.fsync(f.fileno())
def values(value):
 if hasattr(value,"detach"):value=value.detach()
 if hasattr(value,"cpu"):value=value.cpu()
 if hasattr(value,"tolist"):value=value.tolist()
 return value
def optional(read):
 try:return {"available":True,"value":read()}
 except Exception as e:return {"available":False,"error":type(e).__name__,"detail":str(e)}
def tensor_info(value,limit):
 if value is None:return None
 shape=tuple(int(n) for n in value.shape)
 require(len(shape)<=2 and all(n>=0 for n in shape) and value.numel()<=limit,
         "actual bound tensor exceeds diagnostic limit")
 return {"shape":list(shape),"dtype":str(value.dtype),"device":str(value.device),
         "values":values(value),"diagnostic_d2h":str(value.device)!="cpu"}
def before_record(runner,args,kwargs,observer,signature,rank,sources,arm):
 batch=runner.input_batch;turn=int(observer.turn)+1
 require(0<=turn<33,"before-guard turn outside frozen protocol")
 ids=list(batch.req_ids[:int(batch.num_reqs)])
 require(len(ids)==1,"before-guard scope is actual C1 only")
 bound=signature.bind(runner,*args,**kwargs)
 expected_n=1024 if turn==0 else 1
 positions=bound.arguments.get("positions")
 input_ids=bound.arguments.get("input_ids")
 cached=runner.requests[ids[0]]
 starts_cpu=values(runner.gdn_query_start_loc.cpu[:2])
 starts_np=values(runner.gdn_query_start_loc.np[:2])
 computed_cpu=values(batch.num_computed_tokens_cpu_tensor[:1])
 computed_np=values(batch.num_computed_tokens_cpu[:1])
 # Optional observations are explicit; unavailable data is not synthesized.
 scheduled=getattr(runner,"num_scheduled_tokens",None)
 record={"schema":"damp-fixed-admission-before-guard/v3","phase":"before-frozen-begin",
  "rank":rank,"physical_card":rank+4,"arm":arm,"observer_turn_before":int(observer.turn),
  "turn":turn,"expected":{"starts":[0,expected_n],"computed":[0 if turn==0 else 1023+turn]},
  "current":{"starts_cpu":starts_cpu,"starts_np":starts_np,
   "computed_cpu":computed_cpu,"computed_np":computed_np,"input_req_ids":ids,
   "request_num_computed_tokens":optional(lambda:int(cached.num_computed_tokens)),
   "num_scheduled_tokens_cpu":optional(lambda:values(scheduled.cpu[:1])),
   "num_scheduled_tokens_np":optional(lambda:values(scheduled.np[:1])),
   "num_tokens_padded":bound.arguments.get("num_tokens_padded"),
   "uses_mrope":bool(runner.uses_mrope),
   "positions":tensor_info(positions,3072),"input_ids":tensor_info(input_ids,1024),
   "num_prompt_tokens_cpu":optional(lambda:values(batch.num_prompt_tokens_cpu_tensor[:1]))},
  "native_sources":sources,"guard_source":{"path":str(V2/"v2_observer.py"),"sha256":OBSERVER_SHA,
    "original_expression_unchanged":True},
  "native_model_called_yet":False,"not_admission":True,"source_lock_issued":False}
 return record
def wrap_original(original,make_record,save_record):
 def wrapped(runner,*args,**kwargs):
  batch=getattr(runner,"input_batch",None)
  if batch is None or not int(getattr(batch,"num_reqs",0)):
   return original(runner,*args,**kwargs)
  # If BEFORE evidence itself fails, fail before any original model writer;
  # no native exception exists yet. Once original is called, propagate its
  # same exception object without finally/secondary evidence writes.
  record=make_record(runner,args,kwargs)
  save_record(record)
  return original(runner,*args,**kwargs)
 return wrapped
def install():
 source_contract()
 import damp_fixed_v2
 require(Path(damp_fixed_v2.__file__).resolve()==V2/"damp_fixed_v2.py","wrong frozen entrypoint")
 damp_fixed_v2.register()
 import vllm_ascend.worker.model_runner_v1 as runners
 import v2_observer
 from vllm.distributed import get_tensor_model_parallel_rank,get_tensor_model_parallel_world_size
 Runner=runners.NPUModelRunner;original=Runner._model_forward
 require(not hasattr(Runner,"_damp_v3_before_guard"),"v3 installed twice")
 require(inspect.isfunction(original) and original.__name__=="supervised_forward"
         and Path(original.__code__.co_filename).resolve()==V2/"v2_observer.py"
         and original.__globals__ is vars(v2_observer),"not frozen original supervised callable")
 closure=inspect.getclosurevars(original).nonlocals
 require(set(closure)=={"installed_forward","observer","supervisor"},"frozen closure ABI drift")
 observer=closure["observer"]
 require(observer is closure["supervisor"].observer,"supervisor/observer identity differs")
 require(type(observer).__name__=="Observer" and type(observer).__module__=="v2_observer"
         and Path(type(observer).begin.__code__.co_filename).resolve()==V2/"v2_observer.py",
         "wrong actual observer.begin source")
 sources={}
 for path,digest in RUNTIME.items():
  require(file_sha(path)==digest,"actual runtime source drift: "+path)
  sources[path]={"sha256":digest,"bytes":Path(path).stat().st_size}
 # This follows the original frozen signature, not the variadic outer wrapper.
 native=runners.NPUModelRunner._damp_admission_supervisor
 require(native is closure["supervisor"],"actual runner supervisor identity differs")
 actual_native=closure["installed_forward"]
 if os.environ["DAMP_ADMISSION_ARM"]=="on":
  actual_native=Runner._damp_original_forward
 signature=inspect.signature(actual_native)
 root=Path(os.environ["DAMP_CAPTURE_OUTPUT"]).resolve()
 arm=os.environ["DAMP_ADMISSION_ARM"]
 def make_record(runner,args,kwargs):
  # Like frozen v2 begin, consult TP only at a real native-forward frame.
  require(get_tensor_model_parallel_world_size()==4,"actual TP4 required")
  rank=int(get_tensor_model_parallel_rank());require(0<=rank<4,"wrong actual rank")
  return before_record(runner,args,kwargs,observer,signature,rank,sources,arm)
 def save_record(record):
  name="before-guard-rank-%d-turn-%03d.json"%(record["rank"],record["turn"])
  exclusive_json(root/name,record)
 Runner._model_forward=wrap_original(original,make_record,save_record)
 Runner._damp_v3_before_guard={"original":original,"observer":observer,"rank":"lazy-real-forward",
                            "source":str(Path(__file__).resolve())}

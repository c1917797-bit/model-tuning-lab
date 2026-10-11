"""Replay the exact current018 producer/raw whole consumer. Never create a process/lease."""
import importlib.util,json,sys,types
from pathlib import Path
import screen_contract as c
PATH_KEYS=("result","terminal","raw_result","raw_terminal","raw_owned","raw_cleanup","raw_child","raw_owner_result")
def module(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
 c.need(name not in sys.modules,"no foreign predecessor namespace")
 sys.modules[name]=m
 try:spec.loader.exec_module(m)
 except BaseException:sys.modules.pop(name,None);raise
 return m
def replay(arguments):
 # arguments are the exact source-pinned raw023 --mode consume inputs, never commands.
 c.need(type(arguments)is dict and all(arguments.get(k)for k in PATH_KEYS),"complete actual018 raw/whole originals")
 root=Path(c.RAW["path"]).parent;base=Path(c.WHOLE["path"]).parent
 for reference in(c.PRODUCER,c.WHOLE,c.RAW):
  mf=c.read(reference)
  own=mf["files"]
  rows=own if type(own)is list else [dict(path=str(Path(reference["path"]).parent/n),**r)for n,r in own.items()]
  for r in rows:
   c.need(c.ref(r["path"])==r,"all exact predecessor source files")
 core=module(root/"delegate.py","_kivi_b1_exact_raw_delegate")
 core.initialize(base)
 c.need("cpu_raw_resources"not in sys.modules,"no ambient CPU resource module")
 sys.path.insert(0,str(root))
 try:
  a=types.SimpleNamespace(**arguments)
  for key in PATH_KEYS:setattr(a,key,Path(getattr(a,key)))
  c.need(a.raw_wall_seconds==5400,"unchanged complete raw budget")
  ctx=core.Context(c.PRODUCER)
  ctx=core.cpu_context(ctx,core.obj(core.ref(a.raw_owned)),core.obj(core.ref(a.raw_owner_result)))
  result=core.consume(a,ctx)
 finally:sys.path.pop(0)
 c.need(result["status"]=="FIRSTDECODE_OWNED_RAW_AND_WHOLE_CONSUMED"
  and result["producer_source"]==c.PRODUCER and result["firstdecode_integration_checked"]is True
  and result["FA_frames"]==64 and result["native_finished_all4_checked"]is True
  and result["original_prefill_tokens"]==32768 and result["actual_first_decode_length"]==32769
  and result["model_ready"]is result["performance_ready"]is result["run_authority"]is False,
  "actual complete018 firstdecode prerequisite, not a performance result")
 return result

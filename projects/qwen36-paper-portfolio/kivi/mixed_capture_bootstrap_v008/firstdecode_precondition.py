"""Replay exact018 whole022/raw023 delegate, including actual CPU source/resource context.
Pure original-file replay; never trust a PASS flag, create a process or acquire a lease.
"""
import sys
from types import SimpleNamespace
from pathlib import Path
PRODUCER={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/kivi-model-firstdecode-bootstrap-v1-018/SOURCE_MANIFEST.json","bytes":110307,"sha256":"a5726b3ec27178f574962b02a745ffe20060ebd42bf2de3d4cffc0161df5a7e4"}
WHOLE={"path":"/cache/cch/qwen36-paper-preparation-20261007/recurrent/kivi-firstdecode-whole-provenance-v022-20261011/SOURCE_MANIFEST.json","bytes":15242,"sha256":"ba21cb0c57429333fd883f32381c570f2f7f0239bcc1c7981dc0e39708053a50"}
RAW={"path":"/cache/cch/qwen36-paper-preparation-20261007/recurrent/kivi-raw-cpu-provenance-v023-20261011/SOURCE_MANIFEST.json","bytes":11123,"sha256":"337da6b9edf7704771ee8973445a5d23b7a63b6a9ec0451afadaa94838994c5a"}
CORE_SHA="933d4324c9e15ae97d7df48558029ae7f1d49d2e356dc6defcc1ae1ff4123e44"
def replay(c,m,args_ref):
 row=next(r for r in m["files"]if Path(r["path"]).name=="consumer_namespace.py")
 helper=c.module(row["path"],row["sha256"],"_mixed_consumer_namespace")
 return helper.isolated_call(lambda:_replay(c,m,args_ref),"firstdecode")
def _replay(c,m,args_ref):
 c.require(m["firstdecode_producer_ref"]==PRODUCER and m["firstdecode_whole_source"]==WHOLE
  and m["firstdecode_raw_source"]==RAW,"exact currently reviewed full018 prerequisite sources")
 row=m["runtime_roles"]["firstdecode_consumer"]
 c.require(row["path"]==str(Path(WHOLE["path"]).parent/"consume_whole.py")
  and row["sha256"]==CORE_SHA,"same whole022 original core")
 for ref in(PRODUCER,WHOLE,RAW):
  mf=c.obj(ref);own=mf["files"]
  rows=own if type(own)is list else[dict(path=str(Path(ref["path"]).parent/n),**r)for n,r in own.items()]
  for r in rows:c.require(c.checked(r)==r,"all exact predecessor source files")
 args=c.obj(args_ref);keys=("result","terminal","raw_result","raw_terminal","raw_owned","raw_cleanup","raw_child","raw_owner_result")
 c.require(type(args)is dict and all(type(args.get(k))is str and Path(args[k]).is_absolute()for k in keys),
  "complete actual018 original operation paths")
 rawmf=c.obj(RAW);root=Path(RAW["path"]).parent
 delegate_ref=dict(path=str(root/"delegate.py"),**rawmf["files"]["delegate.py"])
 core=c.module(delegate_ref["path"],delegate_ref["sha256"],"_mixed_exact_raw023_delegate")
 core.initialize(Path(WHOLE["path"]).parent)
 c.require("cpu_raw_resources"not in sys.modules,"no ambient resource substitution")
 sys.path.insert(0,str(root))
 try:
  a=SimpleNamespace(**args)
  for key in keys:setattr(a,key,Path(getattr(a,key)))
  c.require(a.raw_wall_seconds==5400,"unchanged original raw budget")
  ctx=core.Context(PRODUCER)
  ctx=core.cpu_context(ctx,core.obj(core.ref(a.raw_owned)),core.obj(core.ref(a.raw_owner_result)))
  result=core.consume(a,ctx)
 finally:sys.path.pop(0)
 c.require(result["schema"]=="kivi.actual-firstdecode-whole-consumed/v1"
  and result["status"]=="FIRSTDECODE_OWNED_RAW_AND_WHOLE_CONSUMED"
  and result["producer_source"]==PRODUCER and result["firstdecode_integration_checked"]is True
  and result["FA_frames"]==64 and result["original_prefill_tokens"]==32768
  and result["actual_first_decode_length"]==32769 and result["native_finished_all4_checked"]is True
  and result["MAIN_original_operation_verified"]is True
  and result["model_ready"]is result["performance_ready"]is result["mixed_checked"]is False,
  "whole actual firstdecode predecessor; no mixed/full-model permission")
 return result

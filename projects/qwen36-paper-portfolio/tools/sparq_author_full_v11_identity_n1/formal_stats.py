"""Timing-OFF final snapshot, only explicit formal mode; no tensor observation in timed loop.
Startup worker identity is published before warmups. One owned SIGUSR1 request
after the actual client timer closes finalizes counters and original identities.
This is not an HTTP/plugin endpoint, not a numerical or active-GDN equivalence gate.
"""
import hashlib,json,os,re,signal,threading,time
from pathlib import Path
import source_contract as c,gdn_state
def proc(pid=None):
 root=Path("/proc")/str(os.getpid() if pid is None else pid)
 raw=(root/"cmdline").read_bytes();stat=(root/"stat").read_text()
 tail=stat[stat.rfind(")")+2:].split();c.require(len(tail)>=20,"complete actual proc stat")
 return dict(pid=int(root.name),stat=stat,start_ticks=int(tail[19]),cgroup=(root/"cgroup").read_text(),
  cmdline_sha256=hashlib.sha256(raw).hexdigest(),argv=raw.decode().rstrip("\0").split("\0"))
def start(state,rank,source,files,component):
 c.require(threading.current_thread() is threading.main_thread() and
  signal.getsignal(signal.SIGUSR1)==signal.SIG_DFL,"owned formal finalizer requires main thread/default SIGUSR1; never replace handler")
 root=Path(os.environ["QWEN36_SPARQ_MODEL_TRACE_ROOT"])
 identity=dict(schema="sparq.formal-worker-start/v1",rank=rank,source=source,source_files=files,
  component=component,mode="formal",arm=state.arm,process=proc(),pre_weight_memory=state.startup_memory_ref,created_ns=time.time_ns(),
  diagnostic_trace_enabled=False,common_identity_flag=__import__("identity_bridge").flag())
 c.write(root/("FORMAL_WORKER-r%d.json"%rank),identity)
 finalized=False
 def finalize(signum,frame):
  nonlocal finalized
  c.require(signum==signal.SIGUSR1 and not finalized and state.current is None and state.last_ctx is not None,
   "one formal final snapshot only while no real model turn is active")
  state.t.npu.current_stream().synchronize() # AFTER client end, not formal per-token timing.
  ctx=state.last_ctx;gdn=[];donor=state.gdn_runtime["gdn"].AscendGatedDeltaNetAttention
  for prefix,obj in ctx.no_compile_layers.items():
   match=re.search(r"(?:^|\.)layers\.([0-9]+)(?:\.|$)",prefix)
   if not match or int(match.group(1)) not in gdn_state.GDN:continue
   c.require(obj.forward.__func__ is donor.forward and obj._forward_core.__func__ is donor._forward_core,
    "all actual original GDN donor/receiver functions, no formal GDN replacement")
   gdn.append(dict(layer=int(match.group(1)),prefix=prefix,forward_source=obj.forward.__module__,
    core_source=obj._forward_core.__module__,state_identities=[list(state.tensor_identity(x)) for x in obj.kv_cache]))
  c.require({x["layer"] for x in gdn}==set(gdn_state.GDN) and len(gdn)==48,"complete actual formal48 GDN bindings")
  captures={}
  for batch in sorted(state.capture_batches):
   records=state.registry.complete(batch,state.acl.get_graph_params())
   captures[str(batch)]={p:dict(layer=state.bindings[p]["layer"],impl_id=state.bindings[p]["impl_id"]) for p in records}
  value=dict(schema="sparq.formal-worker-final/v1",rank=rank,source=source,source_files=files,component=component,
   arm=state.arm,mode="formal",worker_start=c.bound(root/("FORMAL_WORKER-r%d.json"%rank),c.sha(root/("FORMAL_WORKER-r%d.json"%rank))),
   process=proc(),observed_ns=time.time_ns(),timing_debug_off=True,diagnostic_trace_enabled=False,
   common_identity_flag=__import__("identity_bridge").flag(),
   model_entries=state.model_entries,real_turns=state.formal_turns,full_turns=state.formal_full_turns,
   original_full_replays=state.formal_replays,original_post_updates=state.formal_post_updates,
   batch_counts=state.formal_batches,requests=state.formal_requests,captures=captures,GDN=gdn,
   budget=state.budget() if state.arm=="candidate" else dict(full_native_KV_GDN_not_removed=True,dense_fake_aux_not_allocated=True),
   additional_numeric_or_task_pass_claimed=False)
  c.write(root/("FORMAL_FINAL-r%d.json"%rank),value);finalized=True
 signal.signal(signal.SIGUSR1,finalize)
def main():
 import argparse
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 p.add_argument("--trace");p.add_argument("--source");p.add_argument("--source-sha256");p.add_argument("--output")
 a=p.parse_args()
 if not a.execute:print(json.dumps(dict(status="disabled",ready=False)));return
 source,files=c.source(a.source,a.source_sha256);root=Path(a.trace);records=[];end=time.monotonic()+30
 c.require(root.is_absolute() and root.resolve()==root and Path("/cache/cch") in root.parents,"owned same-path trace")
 for rank in range(4):
  start=c.obj(c.bound(root/("FORMAL_WORKER-r%d.json"%rank),c.sha(root/("FORMAL_WORKER-r%d.json"%rank))))
  c.require(start["source"]==source and start["source_files"]==files and start["rank"]==rank and
   start["mode"]=="formal" and all(start["process"][k]==proc(start["process"]["pid"])[k] for k in ("pid","start_ticks","cgroup","cmdline_sha256","argv")),
   "actual source-bound namespace PID/stat/start/argv/cgroup before signaling")
  c.require(not (root/("FORMAL_FINAL-r%d.json"%rank)).exists(),"no prior finalization/retry")
  os.kill(start["process"]["pid"],signal.SIGUSR1)
 for rank in range(4):
  path=root/("FORMAL_FINAL-r%d.json"%rank)
  while not path.exists():
   c.require(time.monotonic()<end,"bounded actual finalizer did not return; retain first error")
   time.sleep(.02)
  records.append(c.bound(path,c.sha(path)))
 result=c.write(a.output,dict(schema="sparq.actual-formal-finalization/v1",source=source,workers=records,
  signaled_after_client=True,ready=False))
 print("SPARQ_FORMAL_FINALIZED "+json.dumps(dict(result=result)),flush=True)
if __name__=="__main__":main()

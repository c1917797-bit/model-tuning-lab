"""Actual TP4 diagnostic workload, not a native numerical/performance gate.
All true B1..16/full/reuse and B2..16 mixed opportunities. The independent
whole-model consumer, not this client, validates every rank/layer/turn/cell.
"""
import json,time,threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import service_contract as c
def cohorts():
 return [(b,kind) for b in range(1,17) for kind in ("initial","reuse")]+[(b,"mixed") for b in range(2,17)]
def count():return sum(b for b,_ in cohorts())
def engine_id(server_id):
 c.require(type(server_id) is str and server_id and len(server_id)<256,"actual SSE response id")
 # Captured installed completion.serving passes request_id+"-"+str(i) to engine.
 # Here n=1/one prompt=>i=0. Base request id itself is OBSERVED, not guessed.
 return server_id+"-0"
def await_first(events,states,futures,end):
 for event in events:
  while not event.wait(.05):
   c.require(time.monotonic()<end and not any(x.done() for x in futures),"actual holder ended/failed before mixed injection")
 c.require(all(states) and not any(x.done() for x in futures),"all actual decode holders remain live for mixed opportunity")
 return [engine_id(x["server_id"]) for x in states]
def await_actual_full(trace,ids,batch,end):
 # One rank is an injection trigger ONLY, never a coverage/numerical verdict.
 # All4 ranks/all64 layers/every actual frame are consumed independently later.
 seen=set()
 while time.monotonic()<end:
  for p in sorted(Path(trace).glob("rank0-*-actual-model-boundary.json")):
   if p.name in seen:continue
   seen.add(p.name);x=json.loads(p.read_text())["value"]
   if x["runtime"]=="FULL" and x["batch"]==batch and set(x["request_ids"])==set(ids):
    return c.bound(p,c.sha(p))
  time.sleep(.05)
 raise ValueError("actual FULL holder trigger unavailable; never invent mixed coverage")
def collect(request,root,port,trace,outputs):
 c.require(outputs==160,"unchanged existing model diagnostic output protocol")
 rows=[];log=[];end=time.monotonic()+4700
 for b,kind in cohorts():
  c.require(time.monotonic()<end,"whole bounded diagnostic workload exhausted")
  marker="b%02d-%s"%(b,kind);cell=root/marker;cell.mkdir()
  with ThreadPoolExecutor(max_workers=b) as pool:
   if kind!="mixed":
    futures=[pool.submit(request,cell,port,c.prompt_ids(j%40),outputs,marker+"-%02d"%j) for j in range(b)]
    current=[x.result() for x in futures];trigger=None
   else:
    events=[threading.Event() for _ in range(b-1)];states=[None]*(b-1)
    def notify(j,state):
     states[j]=state;events[j].set()
    futures=[pool.submit(request,cell,port,c.prompt_ids(j%40),outputs,marker+"-holder-%02d"%j,
     on_first=lambda state,j=j:notify(j,state)) for j in range(b-1)]
    ids=await_first(events,states,futures,end)
    trigger=await_actual_full(trace,ids,b-1,min(end,time.monotonic()+180))
    c.require(not any(x.done() for x in futures),"actual holders completed before source-supported mixed injection")
    fresh=pool.submit(request,cell,port,c.prompt_ids(39),outputs,marker+"-new")
    current=[x.result() for x in [*futures,fresh]]
   c.require(len(current)==b and all(x["ok"] and x["completion_tokens"]==outputs for x in current),
    "entire actual diagnostic cohort SSE/IDs/length; no retry or partial promotion")
   rows.extend(current);log.append(dict(batch=b,kind=kind,responses=[c.bound(cell/(x["id"]+".json"),c.sha(cell/(x["id"]+".json"))) for x in current],
    actual_rank0_injection_trigger=trigger,trigger_is_not_validation=True,
    all_rank_model_coverage_pending=True))
 c.require(len(rows)==count(),"entire model workload request plan")
 return rows,log

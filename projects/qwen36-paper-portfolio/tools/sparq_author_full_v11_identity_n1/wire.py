"""Independent original raw SSE replay and exact HTTP cohort consumer; stdlib."""
import json,math
from pathlib import Path
import service_contract as c
def replay(row,prompt,root,outputs,exact=True):
 from bench import StreamState
 p=c.own_mount_path(root,row["raw_sse"]["path"]);c.bound(p,row["raw_sse"]["sha256"])
 state=StreamState(prompt,outputs);last=float("-inf")
 with p.open("r",encoding="utf-8") as src:
  for line in src:
   e=json.loads(line);now=e["receipt"]
   c.require(type(now) in (float,int) and math.isfinite(now) and now>=last,"actual monotonic raw SSE receipts")
   last=now;raw=e["line"].encode()
   if raw.startswith(b"data: "):state.feed(raw[6:].strip(),now)
 if exact:state.finish_check()
 else:c.require(state.done and state.prompt_seen and state.finish in ("stop","length") and 0<len(state.tokens)<=outputs and
  state.usage and state.usage["completion_tokens"]==len(state.tokens) and state.usage["prompt_tokens"]==len(prompt) and
  state.usage["total_tokens"]==len(prompt)+len(state.tokens),"actual task normalEOS capped output")
 c.require(row["ok"] is True and row["done"] is True and row["output_tokens"]==state.tokens and row["first"]==state.first and
  row["last"]==state.last and row["usage"]==state.usage and row["finish_reason"]==state.finish and
  row["completion_tokens"]==len(state.tokens) and row["prompt_tokens"]==len(prompt) and row["prompt_digest"]==c.digest(prompt) and
  row["actual_server_response_id"]==state.server_id,
  "entire actual wire/prompt/usage/timing/request-ID identity, not inline counts")
 c.require(type(row["submitted"]) in (int,float) and type(row["response_end"]) in (int,float) and
  math.isfinite(row["submitted"]) and math.isfinite(row["response_end"]) and
  row["submitted"]<=row["first"]<=row["last"]<=row["response_end"],"actual request timing interval")
 from identity_bridge import verify_row
 engine=verify_row(row,__import__("bench").service_root(root))
 return dict(engine_id=engine,prompt_tokens=len(prompt),output_tokens=len(state.tokens))
def http(ref,arm_ref):
 x=c.obj(ref);arm=c.obj(arm_ref);root=Path(ref["path"]).parent
 c.require(x["schema"]=="sparq.actual-http/v1" and x["status"]=="complete" and x["arm_ref"]==arm_ref and
  x["mode"]==arm["mode"] and x["arm"]==arm["arm"] and x["protocol"]==arm["protocol"] and arm["common"]==c.COMMON and
  arm["command"]==c.server_argv(arm["port"]),"actual entire client -> source-bound common stock arm")
 protocol=c.DIAGNOSTIC_PROTOCOL if arm["mode"]=="diagnostic" else c.PROTOCOL
 c.require(protocol==x["protocol"] and len(x["warmups"])==2 and len(x["responses"])==protocol["requests"],"complete mode/count")
 requested={}
 for i,row in enumerate(x["warmups"]):
  c.require(row["id"]=="warmup%d"%i,"actual warmup order")
  r=replay(row,c.prompt_ids(i),root,1);requested[r["engine_id"]]=r
 rows=x["responses"];outputs=protocol["output_tokens"]
 if arm["mode"]=="diagnostic":
  import model_workload
  cohorts=x["actual_cohorts"];c.require([(z["batch"],z["kind"]) for z in cohorts]==model_workload.cohorts(),"all47 real diagnostic cohorts")
  flattened=[]
  for z in cohorts:
   b=z["batch"];kind=z["kind"];marker="b%02d-%s"%(b,kind)
   c.require(len(z["responses"])==b and z["trigger_is_not_validation"] is True,"full actual diagnostic cohort")
   if kind=="mixed":
    c.require(z["actual_rank0_injection_trigger"],"real mixed trigger Ref required")
    trigger=c.obj(z["actual_rank0_injection_trigger"])
    c.require(trigger["rank"]==0 and trigger["kind"]=="actual-model-boundary" and
     trigger["value"]["runtime"]=="FULL" and trigger["value"]["batch"]==b-1,
     "actual FULL trigger is injection evidence only")
   else:c.require(z["actual_rank0_injection_trigger"] is None,"no guessed trigger for uniform cohorts")
   for j,rr in enumerate(z["responses"]):
    row=c.obj(rr);expected=marker+("-new" if kind=="mixed" and j==b-1 else "-holder-%02d"%j if kind=="mixed" else "-%02d"%j)
    c.require(row["id"]==expected and Path(rr["path"])==root/marker/(expected+".json"),"source-planned cohort/response file")
    r=replay(row,c.prompt_ids(39 if kind=="mixed" and j==b-1 else j%40),root,outputs)
    c.require(r["engine_id"] not in requested,"unique actual engine request")
    requested[r["engine_id"]]=r;flattened.append(row)
  c.require(c.canonical(flattened)==c.canonical(rows),"whole cohort response bytes equal report, no removed row")
 else:
  c.require([z["id"] for z in rows]==["request%02d"%i for i in range(40)],"all measured requests in source order")
  for i,row in enumerate(rows):
   r=replay(row,c.prompt_ids(i),root,outputs);c.require(r["engine_id"] not in requested,"unique measured engine ID")
   requested[r["engine_id"]]=r
  points=[(r["submitted"],1) for r in rows]+[(r["response_end"],-1) for r in rows];live=peak=0
  for _,delta in sorted(points,key=lambda x:(x[0],x[1])):live+=delta;peak=max(peak,live)
  c.require(live==0 and 1<=peak<=16,"actual measured bounded C16 HTTP overlap")
 wall=max(z["response_end"] for z in rows)-min(z["submitted"] for z in rows)
 c.require(wall>0,"positive actual full wall")
 metrics=dict(output_tokens_per_second=len(rows)*outputs/wall,wall_seconds=wall,
  mean_ttft_seconds=sum(r["first"]-r["submitted"] for r in rows)/len(rows),
  mean_tpot_seconds=sum((r["last"]-r["first"])/(outputs-1) for r in rows)/len(rows))
 c.require(metrics==x["metrics"],"independent original wire fixed output metrics")
 return dict(requests=requested,metrics=metrics,mode=x["mode"],arm=x["arm"],report=ref)

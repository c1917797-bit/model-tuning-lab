"""Strict fixed1024 client and final2048 response producer. All raw SSE retained."""
from __future__ import annotations
import argparse,json,time,sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request,urlopen
import service_contract as c
require=c.require
class StreamState:
    def __init__(self, prompt, outputs):
        self.prompt=prompt;self.outputs=outputs;self.tokens=[];self.first=self.last=None
        self.prompt_seen=False;self.usage=None;self.finish=None;self.done=False;self.server_id=None
    def feed(self, data, now):
        if data == b"[DONE]":
            require(not self.done,"duplicate DONE");self.done=True;return
        require(not self.done,"event after DONE")
        obj=json.loads(data);require("error" not in obj,"server stream error: "+str(obj))
        require(type(obj.get("id")) is str and obj["id"],"actual server response request id")
        if self.server_id is None:self.server_id=obj["id"]
        require(self.server_id==obj["id"],"actual SSE response id changed")
        if obj.get("usage") is not None:self.usage=obj["usage"]
        for choice in obj.get("choices",[]):
            require(choice.get("index")==0,"multiple/foreign output choice")
            prompt=choice.get("prompt_token_ids")
            if prompt is not None:
                require(not self.prompt_seen and prompt==self.prompt,"stream prompt changed/repeated")
                self.prompt_seen=True
            ids=choice.get("token_ids")
            require(type(ids) is list and all(type(v) is int and v>=0 for v in ids),
                    "actual token-ID deltas required; text/chunks cannot substitute")
            if ids:
                require(self.finish is None,"tokens after terminal choice")
                self.first=now if self.first is None else self.first;self.last=now
                self.tokens.extend(ids)
                require(len(self.tokens)<=self.outputs,"unexpected cumulative/overlong token IDs")
            if choice.get("finish_reason") is not None:
                require(self.finish is None,"duplicate terminal choice")
                self.finish=choice["finish_reason"]
    def finish_check(self):
        require(self.done and self.prompt_seen and self.finish=="length" and
                len(self.tokens)==self.outputs,"stream IDs/prompt/length/DONE incomplete")
        require(self.usage is not None and self.usage.get("completion_tokens")==self.outputs and
                self.usage.get("prompt_tokens")==len(self.prompt) and
                self.usage.get("total_tokens")==len(self.prompt)+self.outputs,"missing/incorrect exact usage")
        require(self.first is not None and self.last is not None,"token arrival time missing")

def service_root(client_leaf):
 root=Path(client_leaf)
 if root.name=="client":return root.parent/"service"
 c.require(root.parent.name=="client","known client cohort/task under exact arm")
 return root.parent.parent/"service"
def actual_mapping(server_id,client_leaf):
 from identity_bridge import mapping
 return mapping(server_id,service_root(client_leaf))
def request(root,port,prompt,outputs,rid,*,exact=True,ignore_eos=True,on_first=None):
 state=StreamState(prompt,outputs);began=time.perf_counter();raw=root/(rid+".sse.jsonl")
 payload=dict(model="qwen36-sparq-tp4",prompt=prompt,max_tokens=outputs,temperature=0,seed=0,
   ignore_eos=ignore_eos,stream=True,return_token_ids=True,echo=True,n=1,request_id="sparq-"+rid,
   stream_options={"include_usage":True})
 if exact:payload["min_tokens"]=outputs
 result=dict(id=rid,prompt_digest=c.digest(prompt),prompt_tokens=len(prompt),max_tokens=outputs,submitted=began,
  ok=False,done=False,finish_reason=None,output_tokens=[],error=None)
 try:
  with raw.open("xb") as w:
   r=Request("http://127.0.0.1:%d/v1/completions"%port,data=c.canonical(payload),headers={"Content-Type":"application/json"},method="POST")
   with urlopen(r,timeout=4800) as response:
    require(response.status==200,"actual HTTP status")
    for line in response:
     now=time.perf_counter();w.write(c.canonical(dict(receipt=now,line=line.decode("utf-8",errors="replace")))+b"\n");w.flush()
     if not line.startswith(b"data: "):continue
     first_before=state.first
     state.feed(line[6:].strip(),now)
     if first_before is None and state.first is not None and on_first is not None:on_first(dict(server_id=state.server_id,first=state.first,**actual_mapping(state.server_id,root)))
     if state.done:break
  if exact:state.finish_check()
  else:
   require(state.done and state.prompt_seen and state.finish in ("stop","length") and 0<len(state.tokens)<=outputs and state.usage is not None and
    state.usage.get("completion_tokens")==len(state.tokens) and state.usage.get("prompt_tokens")==len(prompt) and
    state.usage.get("total_tokens")==len(prompt)+len(state.tokens),"actual final taskEOS/max2048 usage/IDs/DONE")
  result.update(ok=True,done=True,first=state.first,last=state.last,finish_reason=state.finish,
   completion_tokens=len(state.tokens),output_tokens=state.tokens,usage=state.usage,
   **actual_mapping(state.server_id,root))
 except BaseException as primary:result.update(error=repr(primary),completion_tokens=len(state.tokens),output_tokens=state.tokens,
  first=state.first,last=state.last,finish_reason=state.finish,done=state.done)
 result["response_end"]=time.perf_counter();result["raw_sse"]=c.bound(raw,c.sha(raw))
 c.write(root/(rid+".json"),result);return result
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 p.add_argument("--arm-dir",type=Path);p.add_argument("--port",type=int);p.add_argument("--output",type=Path)
 p.add_argument("--tasks");p.add_argument("--tasks-sha256");a=p.parse_args()
 if not a.execute:print(json.dumps(dict(enabled=False,screen_verified=False,final_tasks_verified=False)));return
 require(a.arm_dir and a.port and a.output and not a.output.exists() and a.output==a.arm_dir.parent/"client" and Path("/cache/cch") in a.output.parents,"actual new owned client output")
 arm=c.obj(c.bound(a.arm_dir/"ARM.json",c.sha(a.arm_dir/"ARM.json")))
 require(arm["port"]==a.port and arm["command"]==c.server_argv(a.port) and arm["common"]==c.COMMON,"real arm/client config")
 a.output.mkdir(exist_ok=False);report=dict(schema="sparq.actual-http/v1",status="running",arm=arm["arm"],arm_ref=c.bound(a.arm_dir/"ARM.json",c.sha(a.arm_dir/"ARM.json")),
  protocol=arm["protocol"],mode=arm["mode"],quality_evaluated=False,profiling=False)
 try:
  warmups=[request(a.output,a.port,c.prompt_ids(i),1,"warmup%d"%i) for i in range(2)]
  require(all(r["ok"] for r in warmups),"strict actual warmups");report["warmups"]=warmups
  protocol=arm["protocol"];count=protocol["requests"];outputs=protocol["output_tokens"]
  require(protocol==(c.DIAGNOSTIC_PROTOCOL if arm["mode"]=="diagnostic" else c.PROTOCOL),"exact actual mode/protocol")
  if arm["mode"]=="diagnostic":
   import model_workload
   rows,cohorts=model_workload.collect(request,a.output,a.port,a.arm_dir/"trace",outputs)
   report["actual_cohorts"]=cohorts;report["all_rank_model_coverage_pending"]=True
  else:
   with ThreadPoolExecutor(max_workers=16) as pool:
    futures=[pool.submit(request,a.output,a.port,c.prompt_ids(i),outputs,"request%02d"%i) for i in range(count)]
    rows=[x.result() for x in futures]
  require(all(r["ok"] and r["completion_tokens"]==outputs for r in rows),"full exact mode request count/output cap/original token IDs")
  wall=max(r["response_end"] for r in rows)-min(r["submitted"] for r in rows);require(wall>0,"positive actual stream wall")
  report.update(responses=rows,metrics=dict(output_tokens_per_second=count*outputs/wall,wall_seconds=wall,
   mean_ttft_seconds=sum(r["first"]-r["submitted"] for r in rows)/count,
   mean_tpot_seconds=sum((r["last"]-r["first"])/(outputs-1) for r in rows)/count),status="screen-complete")
  if a.tasks:
   require(arm["mode"]=="formal","final tasks forbidden in diagnostic mode")
   tasks_ref=c.bound(a.tasks,a.tasks_sha256);tasks=c.task_manifest(tasks_ref);report["tasks_ref"]=tasks_ref;report["tasks"]={}
   for task,t in tasks["tasks"].items():
    target=a.output/task;target.mkdir();responses=[];stream=enumerate(c.task_prompts(t))
    # At most16 full long prompts/futures in RAM. Same task protocol/count/order;
    # these quality runs are not the paired1024 performance measurement.
    with ThreadPoolExecutor(max_workers=16) as pool:
     while True:
      chunk=[]
      for _ in range(16):
       try:i,original=next(stream)
       except StopIteration:break
       chunk.append((i,original))
      if not chunk:break
      pending=[pool.submit(request,target,a.port,r["prompt_token_ids"],2048,"task%05d"%i,exact=False,ignore_eos=False) for i,r in chunk]
      for future,(_,original) in zip(pending,chunk):
       row=future.result();row["task_request_id"]=original["id"];responses.append(row)
    require(len(responses)==t["request_count"] and all(r["ok"] for r in responses),"full actual final task requests, no resume/missing rows")
    rr=c.write(target/"RESPONSES.json",dict(schema="sparq.final-task-responses/v1",task=task,arm=arm["arm"],protocol_identity=c.digest([c.COMMON,arm["refs"]["source"],arm["refs"]["model-manifest"],tasks_ref,t,dict(cap=2048,temperature=0,seed=0,ignore_eos=False,thinking=False)]),
     max_tokens=2048,thinking_mode_enabled=False,temperature=0,seed=0,ignore_eos=False,rows=responses))
    report["tasks"][task]=dict(responses=rr,scorer_source=t["scorer_source"],original_scorer_cli=t["scorer_cli"],score_pending=True)
  report["status"]="complete"
 except BaseException as primary:
  report.update(status="failed",primary=repr(primary));raise
 finally:
  ref=c.write(a.output/"REPORT.json",report);print("SPARQ_SERVICE_HTTP "+json.dumps(dict(report=ref,status=report["status"])),flush=True)
if __name__=="__main__":main()

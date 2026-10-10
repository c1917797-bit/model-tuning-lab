"""Thin B1 HTTP adapter. Reuses exact original StreamState; no controller/device code."""
import ast,hashlib,json,math,time
from pathlib import Path
from urllib.request import Request,urlopen
import screen_contract as c
BENCH_SHA="71e53e668b69fc28141e954d3cf0111cf67850500a36160951849b6dbb7696aa"
def stream_state():
 path=Path(__file__).parent/"bench_original.py";wire=path.read_bytes()
 c.need(hashlib.sha256(wire).hexdigest()==BENCH_SHA,"exact frozen original HTTP parser")
 body=[n for n in ast.parse(wire).body if isinstance(n,ast.ClassDef)and n.name=="StreamState"]
 c.need(len(body)==1,"single actual original parser")
 ns=dict(json=json,require=c.need);exec(compile(ast.Module(body=body,type_ignores=[]),str(path),"exec"),ns)
 return ns["StreamState"]
def publish(path,value):
 b=c.canonical(value)+b"\n"
 with Path(path).open("xb")as out:c.need(out.write(b)==len(b),"whole exclusive output")
 return c.ref(path)
def request(root,port,plan):
 root=Path(root);prompt=c.prompt();outputs=plan["outputs"];state=stream_state()(prompt,outputs)
 payload=c.payload(prompt,outputs);began=time.perf_counter();raw=root/(plan["name"]+".sse.jsonl")
 # Same original SSE transport/timestamps; KIVI uses its actual header-ID ingress.
 result=dict(id=plan["name"],header_id=plan["header_id"],prompt_digest=hashlib.sha256(c.canonical(prompt)).hexdigest(),
  prompt_tokens=len(prompt),max_tokens=outputs,submitted=began,ok=False,done=False,output_tokens=[],error=None)
 captured=[];captured_bytes=0
 try:
  if True:
   req=Request("http://127.0.0.1:%d/v1/completions"%port,data=c.canonical(payload),method="POST",
    headers={"Content-Type":"application/json","X-Request-Id":plan["header_id"]})
   with urlopen(req,timeout=4800)as response:
    c.need(response.status==200,"actual HTTP200")
    for line in response:
     now=time.perf_counter();entry=c.canonical(dict(receipt=now,line=line.decode("utf8",errors="strict")))+b"\n"
     captured_bytes+=len(entry);c.need(captured_bytes<=8*1024**2,"bounded original SSE buffer")
     captured.append(entry)
     if not line.startswith(b"data: "):continue
     state.feed(line[6:].strip(),now)
     if state.done:break
  state.finish_check()
  c.need(state.server_id=="cmpl-"+plan["header_id"],"actual source-declared response ID")
  result.update(ok=True,done=True,first=state.first,last=state.last,finish_reason=state.finish,
   completion_tokens=len(state.tokens),output_tokens=state.tokens,usage=state.usage,actual_server_response_id=state.server_id)
 except BaseException as error:
  result.update(error=repr(error),completion_tokens=len(state.tokens),output_tokens=state.tokens,
   first=state.first,last=state.last,finish_reason=state.finish,done=state.done)
 result["response_end"]=time.perf_counter()
 # Identical bounded host-side wire retention in both arms, AFTER timed response.
 with raw.open("xb")as out:
  for entry in captured:c.need(out.write(entry)==len(entry),"whole original post-response SSE bytes")
 result["raw_sse"]=c.ref(raw)
 return publish(root/(plan["name"]+".json"),result)
def replay(row,plan,root):
 c.need(Path(row["raw_sse"]["path"]).parent==Path(root),"owned raw wire path")
 c.need(c.ref(row["raw_sse"]["path"])==row["raw_sse"],"whole raw SSE bytes")
 prompt=c.prompt();state=stream_state()(prompt,plan["outputs"]);last=float("-inf")
 with Path(row["raw_sse"]["path"]).open("r",encoding="utf8")as src:
  for line in src:
   event=json.loads(line);now=event["receipt"]
   c.need(type(now)in(int,float)and math.isfinite(now)and now>=last,"actual monotonic raw receipts");last=now
   raw=event["line"].encode()
   if raw.startswith(b"data: "):state.feed(raw[6:].strip(),now)
 state.finish_check()
 c.need(row["ok"]is True and row["done"]is True and row["id"]==plan["name"]
  and row["header_id"]==plan["header_id"] and row["actual_server_response_id"]==state.server_id=="cmpl-"+plan["header_id"]
  and row["output_tokens"]==state.tokens and row["first"]==state.first and row["last"]==state.last
  and row["usage"]==state.usage and row["finish_reason"]==state.finish and row["completion_tokens"]==len(state.tokens)
  and row["prompt_tokens"]==32768 and row["max_tokens"]==plan["outputs"] and row["prompt_digest"]==hashlib.sha256(c.canonical(prompt)).hexdigest(),
  "original whole wire/prompt/usage/timing identity")
 c.need(row["submitted"]<=row["first"]<=row["last"]<=row["response_end"],"actual E2E request interval")
 return dict(wire_checked=True,native_finished_checked=False,numerical_checked=False)
def run(root,port,run_id,await_native_retired):
 # Callback must be bound by the pending source-qualified dense/candidate host bridge.
 # HTTP DONE by itself never permits the next request or final worker drain.
 c.need(callable(await_native_retired),"actual all4 native retirement resolver required")
 root=Path(root);root.mkdir(exist_ok=False);results=[]
 for plan in c.rows(run_id):
  rr=request(root,port,plan);row=c.read(rr);replay(row,plan,root)
  retired=await_native_retired(plan,rr)
  c.need(type(retired)is list and len(retired)==4,"all4 actual native retirement refs")
  for r in retired:c.read(r)
  results.append(dict(plan=plan,response=rr,native_retirement_refs=retired))
 return publish(root/"REPORT.json",dict(schema="kivi.b1-fixed1024-http/v1",protocol=c.PROTOCOL,
  rows=results,metrics=c.metrics(c.read(results[-1]["response"])),model_ready=False,performance_ready=False,run_authority=False))

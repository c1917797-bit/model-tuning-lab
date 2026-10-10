"""One declared32768+2 HTTP request; native all4 final, never HTTP DONE as finish."""
import argparse,hashlib,importlib.util,json,sys,time,urllib.request
from pathlib import Path
def need(v,m):
 if not v:raise ValueError(m)
def run(l,recipe_ref,output,port):
 recipe=l.obj(recipe_ref);protocol=l.obj(recipe["actual_input_protocol_ref"])
 body=protocol["body"];plan=l.obj(recipe["declared_ingress_plan_ref"])
 need(len(plan["rows"])==1 and body["prompt"]==l.obj(plan["rows"][0]["prompt_token_ids_ref"])
  and len(body["prompt"])==32768 and body["max_tokens"]==2 and body["n"]==1 and body["ignore_eos"]is True
  and body["echo"]is body["return_token_ids"]is body["stream"]is True
  and "request_id"not in body,"exact full input+2 outputs; one header ID only")
 req=urllib.request.Request("http://127.0.0.1:%d/v1/completions"%port,
  data=json.dumps(body,separators=(",",":")).encode(),method="POST",
  headers={"Content-Type":"application/json",**protocol["headers"]})
 started=time.monotonic();chunks=[];done=False;usage=None;tokens=[];prompt=None;ids=set()
 raw_path=output.with_name("RAW_SSE.jsonl")
 with raw_path.open("x")as raw,urllib.request.urlopen(req,timeout=3000)as response:
  need(response.status==200,"actual HTTP200")
  for line in response:
   text=line.decode("utf8");raw.write(json.dumps({"raw_line":text},separators=(",",":"))+"\n");raw.flush()
   if not text.startswith("data:"):continue
   payload=text[5:].strip()
   if payload=="[DONE]":done=True;break
   value=json.loads(payload);chunks.append(value)
   if "id"in value:ids.add(value["id"])
   if value.get("usage")is not None:usage=value["usage"]
   for choice in value.get("choices",[]):
    if choice.get("prompt_token_ids")is not None:
     need(prompt is None or prompt==choice["prompt_token_ids"],"same echoed full prompt")
     prompt=choice["prompt_token_ids"]
    if choice.get("token_ids")is not None:tokens.extend(choice["token_ids"])
 need(done and usage is not None and usage["prompt_tokens"]==32768 and usage["completion_tokens"]==2
  and tokens and len(tokens)==2 and prompt==body["prompt"] and len(ids)==1,"actual whole prompt/two tokens/DONE/usage")
 # Source-declared server ID is a protocol check, not assignment/native engine identity.
 need(next(iter(ids))==plan["rows"][0]["declared_server_id"],"actual server ID follows original protocol")
 root=Path(recipe["diagnostic_root"]);finals=[root/("RANK-%d-FINAL-INDEX.json"%rank)for rank in range(4)]
 until=time.monotonic()+120
 while not all(p.is_file()for p in finals):
  need(time.monotonic()<until and time.time()<1791788425,"actual all4 final retirement bounded, no dummy request")
  time.sleep(.1)
 rank_refs=[l.obj(l.ref(path))for path in finals]
 bundles=[l.obj(ref)for ref in rank_refs]
 need([v["rank"]for v in bundles]==list(range(4)),"actual distinct all4 final bundles")
 return l.publish(output,dict(schema="kivi.actual-firstdecode-client/v1",status="HTTP_AND_NATIVE_FINAL_OBSERVED",
  source_ref=recipe["source_ref"],recipe_ref=recipe_ref,input_protocol_ref=recipe["actual_input_protocol_ref"],
  raw_sse_ref=l.ref(raw_path),actual_server_response_id=next(iter(ids)),completion_token_ids=tokens,
  usage=usage,done_observed=True,rank_bundle_refs=rank_refs,elapsed_seconds=time.monotonic()-started,
  native_retirement_is_not_inferred_from_HTTP_DONE=True,model_ready=False,performance_ready=False))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 p.add_argument("--source-manifest-sha256");p.add_argument("--recipe-ref-json",type=Path)
 p.add_argument("--output",type=Path);p.add_argument("--port",type=int,default=8250);a=p.parse_args()
 if not a.execute:print(json.dumps(dict(enabled=False,model_ready=False)));return 0
 here=Path(__file__).resolve().parent;spec=importlib.util.spec_from_file_location("_kivi_firstdecode_client_loader",here/"loader.py")
 l=importlib.util.module_from_spec(spec);sys.modules[spec.name]=l;spec.loader.exec_module(l);l.source(a.source_manifest_sha256)
 run(l,json.loads(a.recipe_ref_json.read_bytes()),a.output,a.port);return 0
if __name__=="__main__":raise SystemExit(main())

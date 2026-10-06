"""40/C16 matched HTTP screen with exact token-ID delta timing and durable SSE."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen
from contract import PROTOCOL, canonical, digest, prompt_ids, require, sha, summarize, write_new

class StreamState:
    def __init__(self, prompt, outputs):
        self.prompt=prompt;self.outputs=outputs;self.tokens=[];self.first=self.last=None
        self.prompt_seen=False;self.usage=None;self.finish=None;self.done=False
    def feed(self, data, now):
        if data == b"[DONE]":
            require(not self.done,"duplicate DONE");self.done=True;return
        require(not self.done,"event after DONE")
        obj=json.loads(data);require("error" not in obj,"server stream error: "+str(obj))
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

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--arm-dir",type=Path,required=True)
    p.add_argument("--port",type=int,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    arm=json.loads((a.arm_dir/"ARM.json").read_text())
    service_root=Path(__file__).resolve().parent
    require(arm["service_sources"]=={str(p.relative_to(service_root)):sha(p)
                    for p in service_root.rglob("*") if p.is_file()},"client scripts differ from launched service")
    require(arm["prepare_only"] is False and arm["arm"] in ("dense","candidate"),"live arm manifest")
    require("--port" in arm["argv"] and arm["argv"][arm["argv"].index("--port")+1]==str(a.port),
            "client port differs from arm launch")
    root=a.output_dir.resolve()
    require(Path("/kvbuffer-results") in root.parents and not root.exists(),"new client result root only")
    root.mkdir(parents=True,exist_ok=False)
    write_new(root/"PROTOCOL.json",dict(schema="kvbp.http-protocol/v1",protocol=PROTOCOL,
              arm_file_sha256=sha(a.arm_dir/"ARM.json"),
              prompts=[dict(index=i,sha256=digest(prompt_ids(i))) for i in range(40)],
              timing_basis="received-SSE-token-ID-deltas",
              coalesced_delta_policy="each token in a delta shares its receipt timestamp",
              quality_evaluation=False))
    base="http://127.0.0.1:%d"%a.port
    def request(index,outputs,tag,submitted):
        prompt=prompt_ids(index);state=StreamState(prompt,outputs)
        payload=dict(model="qwen36-kvbp-p1",prompt=prompt,max_tokens=outputs,min_tokens=outputs,
                     temperature=0,seed=0,ignore_eos=True,stream=True,return_token_ids=True,
                     echo=False,n=1,request_id="kvbp-"+tag+"-"+str(index),
                     stream_options={"include_usage":True})
        raw=root/(tag+"-%02d.sse.jsonl"%index)
        row=dict(index=index,submitted=submitted,prompt_ids_sha256=digest(prompt),
                 prompt_tokens=len(prompt),completion_tokens=0,ok=False,done=False,error=None)
        try:
            with raw.open("xb") as stream:
                req=Request(base+"/v1/completions",data=canonical(payload),
                            headers={"Content-Type":"application/json"},method="POST")
                with urlopen(req,timeout=7200) as response:
                    require(response.status==200,"unexpected HTTP status")
                    for line in response:
                        now=time.perf_counter()
                        # Persist before JSON parsing, usage checks, token checks or assertions.
                        stream.write(canonical(dict(receipt=now,line=line.decode("utf-8",errors="replace")))+b"\n")
                        stream.flush()
                        if not line.startswith(b"data: "):continue
                        state.feed(line[6:].strip(),now)
                        if state.done:break
            state.finish_check()
            row.update(ok=True,done=state.done,first=state.first,last=state.last,
                       finish_reason=state.finish,completion_tokens=len(state.tokens),
                       output_ids_sha256=digest(state.tokens),usage=state.usage)
        except BaseException as error:
            row.update(error=repr(error),finish_reason=state.finish,done=state.done,
                       completion_tokens=len(state.tokens),first=state.first,last=state.last)
        row["response_end"]=time.perf_counter()
        write_new(root/(tag+"-%02d.result.json"%index),row)
        return row
    report=dict(schema="kvbp.same-eager-screen/v1",arm=arm["arm"],status="running",
                protocol=PROTOCOL,arm_sha256=sha(a.arm_dir/"ARM.json"),quality_evaluated=False,
                scope="P1-eager-prefix-off-screen-not-final-three-round-or-accuracy-acceptance")
    try:
        warmups=[request(i,1,"warmup",time.perf_counter()) for i in range(2)]
        write_new(root/"WARMUPS.json",warmups)
        require(all(r["ok"] for r in warmups),"warmup failed; do not launch formal requests")
        with ThreadPoolExecutor(max_workers=16) as pool:
            futures=[pool.submit(request,i,1024,"request",time.perf_counter()) for i in range(40)]
            responses=sorted((f.result() for f in futures),key=lambda x:x["index"])
        report["responses"]=responses
        report["metrics"]=summarize(responses,"received-SSE-token-ID-deltas")
        report["status"]="screen_complete"
    except BaseException as error:
        report.update(status="failed",error=repr(error));raise
    finally:
        write_new(root/"REPORT.json",report)
    print(json.dumps(report["metrics"],sort_keys=True))

if __name__=="__main__":main()

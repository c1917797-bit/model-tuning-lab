"""Standalone grading-only scorer. Actual worker identity must be independently consumed; no guessed engine ID."""
import argparse,hashlib,json,math,os,re,time
from pathlib import Path
BINDING={'task': 'GSM8K', 'count': 1319, 'dataset': {'path': '/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-shared-final-task-inputs-003-MAIN-user72h-final-hftransport-004/download/github/openai--grade-school-math/grade_school_math/data/test.jsonl', 'sha256': '3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14'}, 'prompts': {'path': '/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-shared-final-task-inputs-003-MAIN-user72h-tokenlist-005/inputs/GSM8K.prompts.json', 'sha256': '94cc27bb415cf5705f8b4f0220468762d9b705bd657f9a3c8a370a5777d6c1d5'}, 'model_root': '/models/Qwen3.6-27B', 'assets': {'chat_template.jinja': {'path': '/models/Qwen3.6-27B/chat_template.jinja', 'sha256': 'e84f32a23fdda27689f868aa4a1a5621f41133e51a48d7f3efcbea2839574259'}, 'config.json': {'path': '/models/Qwen3.6-27B/config.json', 'sha256': '69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c'}, 'generation_config.json': {'path': '/models/Qwen3.6-27B/generation_config.json', 'sha256': 'e70c136c1b78ddc1fb0905bac8e733a4dc448d4f852a5dd75143fffc70be550e'}, 'merges.txt': {'path': '/models/Qwen3.6-27B/merges.txt', 'sha256': 'a9d356d7bdf1ef4949e3e748e95b8e10ad9d4e2e838eddc38a0a7b6b94d1db8d'}, 'tokenizer.json': {'path': '/models/Qwen3.6-27B/tokenizer.json', 'sha256': '5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42'}, 'tokenizer_config.json': {'path': '/models/Qwen3.6-27B/tokenizer_config.json', 'sha256': '5186f0defcd7f232382c7f0aebcd2252d073bb921ab240e407b7ae8745d2b29b'}, 'vocab.json': {'path': '/models/Qwen3.6-27B/vocab.json', 'sha256': 'ce99b4cb2983d118806ce0a8b777a35b093e2000a503ebde25853284c9dfa003'}}, 'tokenizer_class': 'TokenizersBackend', 'decoder_versions': {'transformers_version': '5.5.4', 'tokenizers_version': '0.22.2'}, 'official_provenance': {'repo': 'openai/grade-school-math', 'commit': '3101c7d5072418e28b9008a6636bde82a006892c', 'source': {'path': '/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-shared-final-task-inputs-003-MAIN-user72h-final-hftransport-004/download/github/openai--grade-school-math/grade_school_math/dataset.py', 'sha256': 'c22b81bccaaebfd1123be296e8b3c3dca3ddc704c46b70bf4a50603bb627e197'}, 'license': {'path': '/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-shared-final-task-inputs-003-MAIN-user72h-final-hftransport-004/download/github/openai--grade-school-math/LICENSE', 'sha256': '86bbb73e855821d7c401912fd4bf82e34313e6e3b6fd6f909f2b6cc9e209a53b'}, 'exact_function_fragment_sha256': '8a14aaa25bdb5227182eec6f7e37edf2148fea1ba8d5b71f9305f420202533eb', 'dataset': {'repository': 'openai/grade-school-math', 'commit': '3101c7d5072418e28b9008a6636bde82a006892c', 'file': {'path': '/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-shared-final-task-inputs-003-MAIN-user72h-final-hftransport-004/download/github/openai--grade-school-math/grade_school_math/data/test.jsonl', 'sha256': '3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14'}, 'evaluation_only': True}}, 'adaptation': 'named Qwen zero-shot chat: exact official test question plus newline and final #### <number> format instruction; no train examples or invented rows; not an official OpenAI chat prompt', 'response_schema': 'sparq.final-task-responses/v1', 'worker_identity_authorized': False}
ANS_RE = re.compile(r"#### (\-?[0-9\.\,]+)")

INVALID_ANS = "[invalid]"

def extract_answer(completion):
    match = ANS_RE.search(completion)
    if match:
        match_str = match.group(1).strip()
        match_str = match_str.replace(",", "")
        return match_str
    else:
        return INVALID_ANS

def is_correct(model_completion, gt_example):
    gt_answer = extract_answer(gt_example["answer"])
    assert gt_answer != INVALID_ANS
    return extract_answer(model_completion) == gt_answer

def require(v,why):
 if not v:raise ValueError(why)
def sha(p):
 p=Path(p);require(p.is_absolute() and p.resolve()==p and p.is_file() and not p.is_symlink(),"ordinary source/input")
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(262144),b""):h.update(b)
 return h.hexdigest()
def bound(r):require(sha(r["path"])==r["sha256"],"bound input changed");return Path(r["path"])
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
def array(p):
 decoder=json.JSONDecoder();buf="";pos=0;eof=False
 with Path(p).open("r",encoding="utf-8") as f:
  def fill():
   nonlocal buf,pos,eof
   buf=buf[pos:];pos=0;s=f.read(65536);eof=not s;buf+=s;require(len(buf)<=64*1024**2,"bounded real row")
  def ws():
   nonlocal pos
   while True:
    while pos<len(buf) and buf[pos].isspace():pos+=1
    if pos<len(buf) or eof:return
    fill()
  ws();require(buf[pos]=="[","array");pos+=1;ws()
  if pos<len(buf) and buf[pos]=="]":pos+=1
  else:
   while True:
    while True:
     try:r,end=decoder.raw_decode(buf,pos);break
     except json.JSONDecodeError:require(not eof,"invalid complete array");fill()
    pos=end;yield r;ws();require(pos<len(buf),"array delimiter");ch=buf[pos];pos+=1
    if ch=="]":break
    require(ch==",","array comma");ws();require(pos<len(buf) and buf[pos]!="]","trailing comma")
  ws();require(eof and pos==len(buf),"trailing bytes")
def gold_rows():
 p=bound(BINDING["dataset"])
 if BINDING["task"]=="LongBench-v2":
  for row in array(p):yield row["_id"],row
 else:
  with p.open("r",encoding="utf-8") as f:
   for i,line in enumerate(f):yield "gsm8k-test-%04d"%i,json.loads(line)
def replay(row,prompt,root):
 r=row["raw_sse"];p=bound(r);require(root in p.parents and p.resolve()==p,"own actual wire source")
 tokens=[];prompt_seen=False;done=False;finish=None;usage=None;sid=None;first=last=None;last_receipt=-math.inf
 with p.open("r",encoding="utf-8") as f:
  for line in f:
   e=json.loads(line);now=e["receipt"];require(type(now) in (int,float) and math.isfinite(now) and now>=last_receipt,"actual wire timing")
   last_receipt=now;line=e["line"]
   if not line.startswith("data: "):continue
   data=line[6:].strip()
   if data=="[DONE]":require(not done,"duplicate DONE");done=True;continue
   require(not done,"data after DONE");x=json.loads(data);require("error" not in x and type(x.get("id")) is str and x["id"],"actual stream response")
   if sid is None:sid=x["id"]
   require(sid==x["id"],"stream ID changed")
   if x.get("usage") is not None:usage=x["usage"]
   for z in x.get("choices",[]):
    require(z.get("index")==0,"single original completion")
    if z.get("prompt_token_ids") is not None:require(not prompt_seen and z["prompt_token_ids"]==prompt,"wire actual prompt");prompt_seen=True
    ids=z.get("token_ids");require(type(ids) is list and all(type(v) is int and 0<=v<248320 for v in ids),"actual wire token IDs")
    if ids:
     require(finish is None,"tokens after finish");first=now if first is None else first;last=now;tokens+=ids;require(len(tokens)<=2048,"normalEOS cap")
    if z.get("finish_reason") is not None:require(finish is None,"duplicate terminal");finish=z["finish_reason"]
 require(done and prompt_seen and finish in ("stop","length") and 0<len(tokens)<=2048 and type(usage) is dict and usage.get("prompt_tokens")==len(prompt) and usage.get("completion_tokens")==len(tokens) and usage.get("total_tokens")==len(prompt)+len(tokens),"whole capped normalEOS wire")
 require(row["ok"] is True and row["done"] is True and row["error"] is None and row["output_tokens"]==tokens and row["finish_reason"]==finish and row["first"]==first and row["last"]==last and row["usage"]==usage and row["actual_server_response_id"]==sid and row["completion_tokens"]==len(tokens) and row["prompt_tokens"]==len(prompt) and row["prompt_digest"]==digest(prompt),"all real row/wire identities")
 require(all(type(row[k]) in (int,float) and math.isfinite(row[k]) for k in ("submitted","response_end")) and row["submitted"]<=first<=last<=row["response_end"],"real timing interval")
 return tokens
def run(responses,output):
 require(output.is_absolute() and output.parent.resolve()==output.parent and output.parent.is_dir() and not output.exists() and not output.is_symlink(),"unique actual score output")
 for n,r in BINDING["assets"].items():bound(r)
 bound(BINDING["prompts"]);bound(BINDING["dataset"])
 from transformers import AutoTokenizer
 import transformers,tokenizers
 require(dict(transformers_version=transformers.__version__,tokenizers_version=tokenizers.__version__)==BINDING["decoder_versions"],"same actual tokenizer runtime")
 t=AutoTokenizer.from_pretrained(BINDING["model_root"],local_files_only=True,trust_remote_code=False,use_fast=True)
 require(type(t).__name__==BINDING["tokenizer_class"] and t.eos_token_id==248046 and t.clean_up_tokenization_spaces is False,"actual Qwen decoder")
 x=json.loads(responses.read_bytes())
 require(x["schema"]==BINDING["response_schema"]=="sparq.final-task-responses/v1" and x["task"]==BINDING["task"] and x["arm"] in ("dense","candidate") and x["max_tokens"]==2048 and x["thinking_mode_enabled"] is False and x["temperature"]==0 and x["seed"]==0 and x["ignore_eos"] is False and re.fullmatch("[0-9a-f]{64}",x["protocol_identity"]),"actual FULL task protocol")
 rows=x["rows"];require(len(rows)==BINDING["count"],"no partial/skipped response cohort")
 prompts=array(BINDING["prompts"]["path"]);gold=gold_rows();grades=[]
 for i,r in enumerate(rows):
  try:p=next(prompts);rid,g=next(gold)
  except StopIteration:raise ValueError("short official inputs")
  require(r["task_request_id"]==p["id"]==rid,"full exact official task order")
  tokens=replay(r,p["prompt_token_ids"],responses.parent)
  text=t.decode(tokens,skip_special_tokens=True,clean_up_tokenization_spaces=False)
  if BINDING["task"]=="LongBench-v2":answer=extract_answer(text);expected=g["answer"];ok=answer==expected
  else:answer=extract_answer(text);expected=extract_answer(g["answer"]);require(expected!=INVALID_ANS,"valid official GSM gold");ok=is_correct(text,g)
  grades.append(dict(id=rid,output_token_count=len(tokens),decoded_sha256=hashlib.sha256(text.encode()).hexdigest(),answer=answer,gold=expected,correct=bool(ok)))
 require(next(prompts,None) is None and next(gold,None) is None,"extra official input row")
 value=dict(schema="qwen36.actual-task-score/v1",worker_identity_authorized=False,final_task_accuracy_accepted=False,task=BINDING["task"],arm=x["arm"],responses_sha256=sha(responses),protocol_identity=x["protocol_identity"],scorer_source=dict(path=str(Path(__file__).resolve()),sha256=sha(Path(__file__).resolve())),request_count=len(grades),score=sum(r["correct"] for r in grades)/len(grades),rows=grades,official_provenance=BINDING["official_provenance"],adaptation=BINDING["adaptation"],dataset=BINDING["dataset"],prompts=BINDING["prompts"],decoder_versions=BINDING["decoder_versions"],score_unit="proportion; paired consumer reports percentage-points and relative-percent")
 pending=output.with_name(output.name+".pending-"+str(time.time_ns()))
 with pending.open("x") as f:json.dump(value,f,sort_keys=True,allow_nan=False);f.write("\n");f.flush();os.fsync(f.fileno())
 os.link(pending,output);fd=os.open(output.parent,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)
 print(json.dumps(dict(score=dict(path=str(output),sha256=sha(output)),request_count=len(grades),task=BINDING["task"])),flush=True)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true");p.add_argument("--responses",type=Path);p.add_argument("--output",type=Path);a=p.parse_args()
 if not a.execute:print(json.dumps(dict(default_enabled=False,task=BINDING["task"],scored=False)));return
 require(a.responses and a.output,"explicit actual responses and new output");run(a.responses,a.output)
if __name__=="__main__":main()

# Original official source license retained below:
# MIT License
# 
# Copyright (c) 2021 OpenAI
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

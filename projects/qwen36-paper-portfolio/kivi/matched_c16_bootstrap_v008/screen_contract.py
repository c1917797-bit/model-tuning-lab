"""Fixed C16/40 matched screen; selected mixed numerical gate mandatory, tasks/FULL unresolved."""
import hashlib,json,math
from pathlib import Path
GIB=1024**3
CUTOFF=1791788425
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
PRODUCER={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/kivi-model-firstdecode-bootstrap-v1-018/SOURCE_MANIFEST.json","bytes":110307,"sha256":"a5726b3ec27178f574962b02a745ffe20060ebd42bf2de3d4cffc0161df5a7e4"}
WHOLE={"path":"/cache/cch/qwen36-paper-preparation-20261007/recurrent/kivi-firstdecode-whole-provenance-v022-20261011/SOURCE_MANIFEST.json","bytes":15242,"sha256":"ba21cb0c57429333fd883f32381c570f2f7f0239bcc1c7981dc0e39708053a50"}
RAW={"path":"/cache/cch/qwen36-paper-preparation-20261007/recurrent/kivi-raw-cpu-provenance-v023-20261011/SOURCE_MANIFEST.json","bytes":11123,"sha256":"337da6b9edf7704771ee8973445a5d23b7a63b6a9ec0451afadaa94838994c5a"}
COMMON=dict(model="/models/Qwen3.6-27B",served_model_name="qwen36",tensor_parallel_size=4,data_parallel_size=1,
 dtype="bfloat16",seed=0,max_model_len=33792,max_num_batched_tokens=40960,max_num_seqs=16,
 kv_cache_memory_bytes=6*GIB,enforce_eager=True,enable_prefix_caching=False,mamba_cache_mode="none",
 enable_chunked_prefill=True,async_scheduling=False,compilation_mode="NONE",cudagraph_mode="NONE")
PROTOCOL=dict(requests=40,concurrency=16,input_tokens=32768,output_tokens=1024,temperature=0,seed=0,
 ignore_eos=True,min_tokens=1024,thinking=False,prompt_kind="raw-token-ids-no-chat-template",
 warmups=2,warmup_output_tokens=2,arm_order=["dense","candidate"],rounds=1)
ALGORITHM_DELTA=dict(dense="unchanged native attention/native cache provider",
 candidate="source-pinned KIVI packed QK/AV decode plus explicit same-total-budget provider",
 bits=2,prefill="native attention in both arms; candidate additionally writes compact state",
 candidate_native_blocks=198,candidate_compact_pages=2376,dense_native_blocks=253,
 candidate_charged_bytes=6417785856,total_budget_bytes=6*GIB,
 projection_only=True,B1_only=False,C16_ready=False,candidate_resident_upper_bound=7,dense_resident_upper_bound=10,preemption_supported=False)
BUDGET=dict(phase_seconds=5400,cleanup_seconds=90,host_bytes=512*1024**2,guest_bytes=64*GIB,
 guest_CPU=4,host_CPU=1,reserve_CPU=2,total_CPU=7,ordinary_initial_floor_bytes=73*GIB,
 workspace_bytes=32*GIB,hbm_reserve_mib=3072,cutoff_epoch=CUTOFF,budget_reset=False)
def need(v,m):
 if not v:raise ValueError(m)
def canonical(x):return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
def ref(p):
 p=Path(p);need(p.is_absolute()and p.resolve()==p and p.is_file()and not p.is_symlink(),"ordinary exact file")
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def read(r):
 need(type(r)is dict and set(r)=={"path","bytes","sha256"}and type(r["bytes"])is int and 0<r["bytes"]<=8*1024**2,
  "complete bounded actual Ref3")
 need(ref(r["path"])==r,"source/evidence bytes changed")
 return json.loads(Path(r["path"]).read_bytes())
def prompt(index=0):
 # Exact original frozen SparQ fixed40 prompt_ids(i), not an official task.
 need(type(index)is int and 0<=index<40,"fixed40 actual prompt index")
 return [1000+j%257 for j in range(16384)]+[2000+(index*131+j*17)%4093 for j in range(16384)]
def rows(run):
 need(type(run)is str and run and all(c.isalnum()or c=="-"for c in run),"exclusive run label")
 warmups=[dict(name="warmup%d"%i,header_id="kivi-c16-"+run+"-warmup%d"%i,
  outputs=2,measured=False,prompt_index=i)for i in range(2)]
 measured=[dict(name="request%02d"%i,header_id="kivi-c16-"+run+"-request%02d"%i,
  outputs=1024,measured=True,prompt_index=i)for i in range(40)]
 return warmups+measured
def native_argv(port,worker):
 need(type(port)is int and 1024<=port<=65535 and type(worker)is str and worker,"explicit actual worker binding")
 return ["--model",COMMON["model"],"--served-model-name","qwen36","--host","127.0.0.1","--port",str(port),
 "--tensor-parallel-size","4","--data-parallel-size","1","--dtype","bfloat16","--seed","0",
 "--max-model-len","33792","--max-num-seqs","16","--max-num-batched-tokens","40960",
 "--kv-cache-memory-bytes",str(6*GIB),"--no-enable-prefix-caching","--mamba-cache-mode","none",
 "--enable-chunked-prefill","--no-async-scheduling","--enforce-eager","--disable-log-stats","--worker-cls",worker]
def matched_argv(dense,candidate):
 # Only the explicitly different worker/plugin implementation may differ.
 need(dense[-2:][0]==candidate[-2:][0]=="--worker-cls"and dense[:-1]==candidate[:-1],
  "all common native parameters equal; algorithm worker is sole argv delta")
 return True
def payload(prompt_ids,outputs,index=0):
 need(prompt_ids==prompt(index)and outputs in(2,1024),"exact C16 full32768 input/warmup or measured count")
 return dict(model="qwen36",prompt=prompt_ids,n=1,stream=True,temperature=0,seed=0,max_tokens=outputs,
  min_tokens=outputs,ignore_eos=True,echo=True,return_token_ids=True,stream_options={"include_usage":True})
def metrics(rows):
 need(type(rows)is list and len(rows)==40,"all40 measured responses, no warmups")
 for row in rows:
  need(row["completion_tokens"]==1024 and row["done"]is True and row["finish_reason"]=="length",
   "every actual fixed1024 response")
  a,b,c,d=(row[k]for k in("submitted","first","last","response_end"))
  need(all(type(v)in(int,float)and math.isfinite(v)for v in(a,b,c,d))and a<=b<=c<=d and d>a,
   "actual whole E2E interval")
 wall=max(r["response_end"]for r in rows)-min(r["submitted"]for r in rows)
 return dict(output_tokens_per_second=40960/wall,wall_seconds=wall,
  mean_ttft_seconds=sum(r["first"]-r["submitted"]for r in rows)/40,
  mean_tpot_seconds=sum((r["last"]-r["first"])/1023 for r in rows)/40)
def pair(dense,candidate):
 for x in(dense,candidate):
  need(set(x)=={"output_tokens_per_second","wall_seconds","mean_ttft_seconds","mean_tpot_seconds"}
   and all(type(v)in(int,float)and math.isfinite(v)and v>=0 for v in x.values())
   and x["wall_seconds"]>0 and x["output_tokens_per_second"]>0,"complete positive matched metrics")
 ratio=candidate["output_tokens_per_second"]/dense["output_tokens_per_second"]
 return dict(throughput_ratio=ratio,improvement_percent=(ratio-1)*100,screen_pass=ratio>=1.10,
  performance_accepted=False,C16_verified=False,FULL_verified=False,final_task_accuracy_verified=False,
  model_ready=False,run_authority=False)

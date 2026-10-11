"""B1 preliminary matched screen contract; never C16/FULL/final acceptance."""
import hashlib,json,math
from pathlib import Path
GIB=1024**3
CUTOFF=1791788425
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
PRODUCER={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/kivi-model-firstdecode-bootstrap-v1-018/SOURCE_MANIFEST.json","bytes":110307,"sha256":"a5726b3ec27178f574962b02a745ffe20060ebd42bf2de3d4cffc0161df5a7e4"}
WHOLE={"path":"/cache/cch/qwen36-paper-preparation-20261007/recurrent/kivi-firstdecode-whole-vector-writer-v023-20261011/SOURCE_MANIFEST.json","bytes":16365,"sha256":"09ae6fca169c145774ee1466f423348cdf506aa1f5565f0131a44f1dfcbbf6cc"}
RAW={"path":"/cache/cch/qwen36-paper-preparation-20261007/recurrent/kivi-raw-cpu-vector-writer-v024-20261011/SOURCE_MANIFEST.json","bytes":13550,"sha256":"a39f189a473947bb28aed5e9885a101e7cd02b7c8438ee892735543f3d0ce265"}
COMMON=dict(model="/models/Qwen3.6-27B",served_model_name="qwen36",tensor_parallel_size=4,data_parallel_size=1,
 dtype="bfloat16",seed=0,max_model_len=33792,max_num_batched_tokens=32768,max_num_seqs=1,
 kv_cache_memory_bytes=6*GIB,enforce_eager=True,enable_prefix_caching=False,mamba_cache_mode="none",
 enable_chunked_prefill=True,async_scheduling=False,compilation_mode="NONE",cudagraph_mode="NONE")
PROTOCOL=dict(requests=1,concurrency=1,input_tokens=32768,output_tokens=129,temperature=0,seed=0,
 ignore_eos=True,min_tokens=129,thinking=False,prompt_kind="raw-token-ids-no-chat-template",
 warmups=2,warmup_output_tokens=2,arm_order=["dense","candidate"],rounds=1)
ALGORITHM_DELTA=dict(dense="unchanged native attention/native cache provider",
 candidate="source-pinned KIVI packed QK/AV decode plus explicit same-total-budget provider",
 bits=2,prefill="native attention in both arms; candidate additionally writes compact state",
 candidate_native_blocks=198,candidate_compact_pages=2376,dense_native_blocks=253,
 candidate_charged_bytes=6417785856,total_budget_bytes=6*GIB,
 projection_only=True,B1_only=True,C16_ready=False)
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
def prompt():
 # Exact firstdecode018 raw token recipe, also original SparQ prompt_ids(0).
 return [1000+j%257 for j in range(16384)]+[2000+(j*17)%4093 for j in range(16384)]
def rows(run):
 need(type(run)is str and run and all(c.isalnum()or c=="-"for c in run),"exclusive run label")
 return [dict(name=name,header_id="kivi-b1-"+run+"-"+name,outputs=count,measured=measured)
  for name,count,measured in(("warmup0",2,False),("warmup1",2,False),("request00",129,True))]
def native_argv(port,worker):
 need(type(port)is int and 1024<=port<=65535 and type(worker)is str and worker,"explicit actual worker binding")
 return ["--model",COMMON["model"],"--served-model-name","qwen36","--host","127.0.0.1","--port",str(port),
 "--tensor-parallel-size","4","--data-parallel-size","1","--dtype","bfloat16","--seed","0",
 "--max-model-len","33792","--max-num-seqs","1","--max-num-batched-tokens","32768",
 "--kv-cache-memory-bytes",str(6*GIB),"--no-enable-prefix-caching","--mamba-cache-mode","none",
 "--enable-chunked-prefill","--no-async-scheduling","--enforce-eager","--disable-log-stats","--worker-cls",worker]
def matched_argv(dense,candidate):
 # Only the explicitly different worker/plugin implementation may differ.
 need(dense[-2:][0]==candidate[-2:][0]=="--worker-cls"and dense[:-1]==candidate[:-1],
  "all common native parameters equal; algorithm worker is sole argv delta")
 return True
def payload(prompt_ids,outputs):
 need(prompt_ids==prompt()and outputs in(2,129),"exact B1 full32768 input/warmup or measured count")
 return dict(model="qwen36",prompt=prompt_ids,n=1,stream=True,temperature=0,seed=0,max_tokens=outputs,
  min_tokens=outputs,ignore_eos=True,echo=True,return_token_ids=True,stream_options={"include_usage":True})
def metrics(row):
 need(row["completion_tokens"]==129 and row["done"]is True and row["finish_reason"]=="length","actual fixed1024 only")
 a,b,c,d=(row[k]for k in("submitted","first","last","response_end"))
 need(all(type(v)in(int,float)and math.isfinite(v)for v in(a,b,c,d))and a<=b<=c<=d and d>a,"actual E2E interval")
 return dict(output_tokens_per_second=129/(d-a),wall_seconds=d-a,mean_ttft_seconds=b-a,
  mean_tpot_seconds=(c-b)/128)
def pair(dense,candidate):
 for x in(dense,candidate):
  need(set(x)=={"output_tokens_per_second","wall_seconds","mean_ttft_seconds","mean_tpot_seconds"}
   and all(type(v)in(int,float)and math.isfinite(v)and v>=0 for v in x.values())
   and x["wall_seconds"]>0 and x["output_tokens_per_second"]>0,"complete positive matched metrics")
 ratio=candidate["output_tokens_per_second"]/dense["output_tokens_per_second"]
 return dict(throughput_ratio=ratio,improvement_percent=(ratio-1)*100,screen_pass=False,diagnostic_ratio_only=True,
  performance_accepted=False,C16_verified=False,FULL_verified=False,final_task_accuracy_verified=False,
  model_ready=False,run_authority=False)

"""Numerical-only source-bound atomic admission via native pause/ADD/resume."""
import asyncio,contextvars,functools,hashlib,importlib,inspect,json,os,time
from pathlib import Path
CUT=1792220533
PINS={'vllm.entrypoints.openai.completion.serving':'c67bff55fa29c5f89000c3afdc9c7c66305612b13a8a1d85976e5872cee086d7','vllm.v1.engine.async_llm':'2128cf018fe136b698c5e89dc7325bc6dced9d516cc9d772695f044716970b64','vllm.v1.engine.core':'cf9cbde601afb80925254aae814033abeab3817f9c4fe7bf01ca92edc9d10c2d','vllm.v1.engine.core_client':'e41fe15caa59dfd289ae212b3eaefc20c34be87a72e779df03d970f9714b793d','vllm.v1.core.sched.scheduler':'9ae1491f57a6294e32416b93ef2ea68107fa0d65c3a4d7f745f1261012f735e9'}
SCOPE=contextvars.ContextVar('actual_numeric_bulk',default=None)
_installed=False
def need(v,s):
 if not v:raise ValueError(s)
def body_valid(r):
 need(type(r.prompt)is list and len(r.prompt)==2 and all(type(x)is list for x in r.prompt),'one native bulk prompt list, not two HTTP threads')
 need([len(x)for x in r.prompt]==[32768,8192]and all(type(t)is int and t>=0 for x in r.prompt for t in x),'exact actual token-list lengths')
 need(r.stream is False and r.n==1 and r.max_tokens==r.min_tokens==3 and r.ignore_eos is True and r.return_token_ids is True and r.echo is False,'numerical nonstream three-token full choice IDs')
def group_state(engine,prompts=None):return dict(engine=engine,ready=asyncio.Event(),rows=[],resumed=False,expected={len(x):hashlib.sha256(json.dumps(x,separators=(',',':')).encode()).hexdigest()for x in prompts}if prompts is not None else None)
async def added(group,request):
 ids=request.prompt_token_ids
 need(type(ids)is list and len(ids)in(32768,8192),'actual processed ADD prompt length')
 need(request.request_id not in [r['request_id']for r in group['rows']],'unique real child request')
 digest=hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest()
 need(group['expected']is None or group['expected'].get(len(ids))==digest,'actual native ADD bytes match frozen bulk prompt')
 group['rows'].append(dict(request_id=request.request_id,tokens=len(ids),sha256=digest))
 need(len(group['rows'])<=2,'no extra native ADD in this numerical group')
 if len(group['rows'])==2:
  need(sorted(r['tokens']for r in group['rows'])==[8192,32768],'both independent actual prompts before resume')
  await group['engine'].resume_generation();group['resumed']=True;group['ready'].set()
async def grouped(engine,invoke,receipt,prompts):
 need(time.time()+35<CUT,'original cutoff and enqueue/cleanup budget')
 need(await engine.is_paused()is False,'do not hijack already-paused service')
 await engine.pause_generation(mode='keep',clear_cache=False)
 need(await engine.is_paused()is True,'native pause acknowledged')
 group=group_state(engine,prompts);token=SCOPE.set(group);task=None;primary=None
 try:
  task=asyncio.create_task(invoke())
  await asyncio.wait_for(group['ready'].wait(),timeout=30)
  out=await asyncio.wait_for(task,timeout=min(900,CUT-time.time()-5))
  return out
 except BaseException as exc:
  primary=repr(exc)
  if task is not None:task.cancel();await asyncio.gather(task,return_exceptions=True)
  if group['rows']:await engine.abort([r['request_id']for r in group['rows']],internal=True)
  raise
 finally:
  SCOPE.reset(token)
  if not group['resumed']:await engine.resume_generation()
  value=dict(schema='numeric.atomic-admission/v1',rows=group['rows'],native_pause_keep=True,clear_cache=False,resumed=True,primary=primary,actual_packed_tokens_unverified=True,performance=False)
  with Path(receipt).open('x')as f:json.dump(value,f,sort_keys=True);f.write('\n')
def install(request_id,receipt):
 global _installed
 if os.environ.get('NUMERICAL_ATOMIC_PREFILL_ENABLE')!='1':return False
 need(not _installed and type(request_id)is str and request_id.endswith('-packed40960')and Path(receipt).is_absolute()and not Path(receipt).exists(),'single explicit numerical request/absent receipt')
 modules={}
 for name,sha in PINS.items():
  m=importlib.import_module(name);need(hashlib.sha256(Path(inspect.getsourcefile(m)).read_bytes()).hexdigest()==sha,'actual installed source '+name);modules[name]=m
 serving=modules['vllm.entrypoints.openai.completion.serving'].OpenAIServingCompletion
 llm=modules['vllm.v1.engine.async_llm'].AsyncLLM
 original=serving._create_completion;original_add=llm._add_request;sig=inspect.signature(original_add)
 used=False;active=False
 @functools.wraps(original_add)
 async def add(self,*a,**kw):
  group=SCOPE.get()
  if group is None:return await original_add(self,*a,**kw)
  need(self is group['engine'],'same native AsyncLLM transport')
  bound=sig.bind(self,*a,**kw);result=await original_add(self,*a,**kw)
  await added(group,bound.arguments['request']);return result
 @functools.wraps(original)
 async def completion(self,request,raw_request=None):
  nonlocal used,active
  if getattr(request,'request_id',None)!=request_id:
   need(not active,'exclusive numerical admission; no unrelated request interleave')
   return await original(self,request,raw_request)
  need(not used and not active,'no repeat/retry of same frozen numerical input');body_valid(request);used=active=True
  cfg=self.engine_client.vllm_config
  need(cfg.parallel_config.data_parallel_size==1 and cfg.parallel_config.tensor_parallel_size==4,'actual single engine TP4 scope')
  need(cfg.scheduler_config.max_num_batched_tokens==40960 and cfg.scheduler_config.max_num_seqs>=2 and cfg.scheduler_config.long_prefill_token_threshold==0 and cfg.cache_config.enable_prefix_caching is False,'unaltered explicit full-token budget, no chunk threshold/cache-hit ambiguity')
  try:return await grouped(self.engine_client,lambda:original(self,request,raw_request),receipt,request.prompt)
  finally:active=False
 llm._add_request=add;serving._create_completion=completion;_installed=True
 return True

"""Actual local-checkpoint input generation; called by original Devices[] preflight."""
from pathlib import Path
import hashlib
import sys
import json
import time
from types import SimpleNamespace

MODEL='/models/Qwen3.6-27B'
def run(sr,m,C):
 started=time.monotonic()
 import hypic32k_input as I
 C.need(C.ref(Path(I.__file__).resolve())==m['files']['hypic32k_input.py'],'actual source-owned32k input module')
 generator=Path(I.GENERATOR['path'])
 C.need(generator==Path(I.__file__).resolve().parent/'benchmark_shared_prefix.py','source-owned generator, no historical lazy path')
 C.need(I.GENERATOR==m['files']['benchmark_shared_prefix.py'],'actual complete generator Ref')
 C.checked(I.GENERATOR)
 from transformers import AutoTokenizer
 tokenizer=AutoTokenizer.from_pretrained(MODEL,trust_remote_code=True,local_files_only=True)
 before=set(sys.modules)
 value=I.dataset(tokenizer)
 I.validate(value)
 C.need('_bole_current_hypic32k_generator'not in set(sys.modules)-before,'no leaked private generator module')
 rows=value['prompt_cases']
 hashes=[hashlib.sha256(I.canonical(row)).hexdigest()for row in rows]
 selected={}
 for role,index in [('warmup',0),('measured',2),('retirement-barrier',1)]:
  actual=I.select(value,role)
  C.need(actual==rows[index],'actual client role selection unchanged')
  selected[role]=dict(index=index,tokens=len(actual),token_ids_sha256=hashes[index])
 C.need(len(rows)==42 and all(len(row)==32768 for row in rows),'actual complete42case32k generation')
 C.need(value['shared_prefix_tokens']==16384 and value['current_concurrency']==1,'actual32k/16k/C1')
 requests=requests_before_transport(I,value,m,C)
 return dict(schema='bole.actual-local-tokenizer-input-preflight/v1',source=sr,
  generator=I.GENERATOR,checkpoint=MODEL,local_files_only=True,trust_remote_code=True,
  tokenizer_class=type(tokenizer).__name__,pool_size=len(rows),lengths=[len(row)for row in rows],
  token_ids_sha256=hashes,selected=selected,shared_prefix_tokens=value['shared_prefix_tokens'],
  shared_prefix_sha256=hashlib.sha256(I.canonical(rows[0][:16384])).hexdigest(),
  input_tokens=value['input_tokens'],segment_ends=value['segment_ends'],
  formal_output_tokens=value['formal_output_tokens'],current_concurrency=value['current_concurrency'],
  HYPIC_enabled=value['HYPIC_enabled'],historical_40_C16_reference_only=value['historical_40_C16_reference_only'],
  request_construction=requests,elapsed_seconds=time.monotonic()-started,
  HTTP=False,NPU=False,numerical_qualified=False,performance_qualified=False)

def requests_before_transport(I,value,m,C):
 import performance_service_client as client
 from vllm.entrypoints.openai.completion.protocol import CompletionRequest
 protocol=Path(sys.modules[CompletionRequest.__module__].__file__).resolve()
 C.need(hashlib.sha256(protocol.read_bytes()).hexdigest()=='93c720549f2a9ef217d7c2a60710225c862032517520dd9ba693d4820f55365c','actual pinned service CompletionRequest source')
 C.need(C.ref(Path(client.__file__).resolve())==m['files']['performance_service_client.py'],'actual source-owned client')
 class ExpectedTransportStop(BaseException):pass
 name='_bole_current_hypic32k_generator';had=name in sys.modules;prior=sys.modules.get(name)
 donor=I.generator();out=[]
 try:
  args=SimpleNamespace(model='qwen36-mxr-eager',base_url='http://127.0.0.1:8230',
   timeout=2400,input_tokens=32768,prefix_tokens=0,respect_eos=False)
  for role,index,count in [('warmup',-1,8),('measured',0,8),('retirement-barrier',1,1)]:
   ids=I.select(value,role);seen=[]
   def stop(wire,timeout):
    C.need(wire.full_url=='http://127.0.0.1:8230/v1/completions','actual loopback completion URL')
    body=json.loads(wire.data)
    C.need(body['prompt']==ids and body['max_tokens']==count,'actual tokenIDs/output count in constructed request')
    C.need(body['seed']==0 and body['temperature']==0 and body['stream']is True,'unchanged actual deterministic streaming request')
    C.need((body.get('ignore_eos')is True)if count==8 else 'ignore_eos'not in body,'actual8/1 EOS contract')
    parsed=CompletionRequest.model_validate(body)
    C.need(parsed.prompt==ids and parsed.max_tokens==count and parsed.stream is True,'actual service schema accepts exact32k/8/8/1 request')
    C.need(parsed.return_token_ids is True and parsed.stream_options.include_usage is True,'actual service schema return-tokenIDs and usage stream options')
    C.need(parsed.seed==0 and parsed.temperature==0 and parsed.top_p==1 and parsed.n==1,'actual service schema common sampling')
    C.need(not parsed.model_extra,'no silently retained unexpected request extensions')
    seen.append(dict(role=role,index=index,output_tokens=count,
     input_tokens=len(ids),body_sha256=hashlib.sha256(wire.data).hexdigest(),transport_called=False,
     actual_service_schema=CompletionRequest.__module__+'.'+CompletionRequest.__name__,
     protocol_ref=C.ref(protocol),payload_keys=sorted(body),validated_fields=sorted(parsed.model_fields_set)))
    raise ExpectedTransportStop()
   try:client.request(donor,args,ids,index,count,role,transport=stop,records=[])
   except ExpectedTransportStop:pass
   else:raise ValueError('actual request must reach expected no-HTTP transport stop')
   C.need(len(seen)==1,'exact one constructed request, no retry')
   out.extend(seen)
 finally:
  if had:sys.modules[name]=prior
  else:sys.modules.pop(name,None)
 return out

"""Frozen diagnostic raw-token workload, not a task/calibration accuracy claim."""
from pathlib import Path
def validate_config(config,prompt,need):
 need(type(config)is dict and config.get("model_type")=="qwen3_5","actual composite Qwen model type")
 text=config.get("text_config")
 need(type(text)is dict and text.get("model_type")=="qwen3_5_text","actual nested text config")
 vocab=text.get("vocab_size")
 need(type(vocab)is int and vocab>0,"positive integer text vocabulary")
 need("vocab_size"not in config or(type(config["vocab_size"])is int and config["vocab_size"]==vocab),"no conflicting root vocabulary")
 need(type(prompt)is list and len(prompt)==32768 and all(type(t)is int and 0<=t<vocab for t in prompt),"actual model token domain")
 return vocab
def create(c,source,model_manifest,out,run_id,*,host=True):
 c.require(type(host)is bool,"explicit host or existing read-only guest model namespace")
 model=c.obj(model_manifest)
 root=Path(model["host_model_root"]if host else"/models/Qwen3.6-27B")
 prompt=[1000+j%257 for j in range(16384)]+[2000+(j*17)%4093 for j in range(16384)]
 config=c.obj(c.bound(root/"config.json",c.CONFIG_SHA))
 validate_config(config,prompt,c.require)
 tokens=c.write(out/"PROMPT_IDS.json",prompt)
 producer=c.write(out/"INPUT_PRODUCER.json",dict(schema="kivi.firstdecode-raw-token-producer/v1",
  source=source,prompt_ref=tokens,actual_count=32768,raw_token_ids_no_chat_template=True,
  thinking_enabled=False,scope="fixed synthetic diagnostic; not official task/calibration",model_ready=False))
 tokenizer=c.write(out/"TOKENIZER_BINDING.json",dict(model_manifest=model_manifest,
  tokenizer_config=c.ref(root/"tokenizer_config.json"),raw_token_ids=True,chat_template_applied=False))
 header="kivi-firstdecode-"+run_id
 server="cmpl-"+header
 row=dict(header_request_id=header,body_request_id=None,declared_server_id=server,
  declared_passed_id=server+"-0",prompt_token_ids_ref=tokens)
 profile=dict(endpoint="/v1/completions",prompt_count=1,n=1,beam_search=False,streaming_input=False)
 plan=c.write(out/"INGRESS_PLAN.json",dict(schema="kivi.declared-model-ingress-plan/v1",profile=profile,
  input_producer_ref=producer,tokenizer_ref=tokenizer,model_binding_ref=c.checked(model_manifest),
  rows=[row],declared_randomization_off=True,model_ready=False,run_authority=False))
 body=dict(model="qwen36",prompt=prompt,n=1,stream=True,temperature=0,seed=0,max_tokens=2,
  ignore_eos=True,echo=True,return_token_ids=True,stream_options={"include_usage":True})
 protocol=c.write(out/"INPUT_PROTOCOL.json",dict(schema="kivi.actual-firstdecode-input/v1",
  body=body,headers={"X-Request-Id":header},plan_ref=plan,source_ref=source,
  prompt_tokens=32768,max_completion_tokens=2,model_ready=False,run_authority=False))
 return plan,protocol

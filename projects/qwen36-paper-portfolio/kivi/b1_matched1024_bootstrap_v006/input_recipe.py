"""Exact018 token producer with three declared sequential B1 screening owners."""
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
 import screen_contract as policy
 c.require(type(host)is bool,"explicit host or read-only guest checkpoint")
 model=c.obj(model_manifest);root=Path(model["host_model_root"]if host else"/models/Qwen3.6-27B")
 prompt=policy.prompt();validate_config(c.obj(c.bound(root/"config.json",c.CONFIG_SHA)),prompt,c.require)
 tokens=c.write(out/"PROMPT_IDS.json",prompt)
 producer=c.write(out/"INPUT_PRODUCER.json",dict(schema="kivi.b1-fixed1024-token-producer/v1",
  source=source,prompt_ref=tokens,actual_count=32768,raw_token_ids_no_chat_template=True,
  thinking_enabled=False,scope="synthetic matched B1 screen; not official task accuracy",model_ready=False))
 tokenizer=c.write(out/"TOKENIZER_BINDING.json",dict(model_manifest=model_manifest,
  tokenizer_config=c.ref(root/"tokenizer_config.json"),raw_token_ids=True,chat_template_applied=False))
 rows=[]
 for row in policy.rows(run_id):
  server="cmpl-"+row["header_id"]
  rows.append(dict(header_request_id=row["header_id"],body_request_id=None,declared_server_id=server,
   declared_passed_id=server+"-0",prompt_token_ids_ref=tokens))
 profile=dict(endpoint="/v1/completions",prompt_count=1,n=1,beam_search=False,streaming_input=False)
 plan=c.write(out/"INGRESS_PLAN.json",dict(schema="kivi.declared-model-ingress-plan/v1",profile=profile,
  input_producer_ref=producer,tokenizer_ref=tokenizer,model_binding_ref=c.checked(model_manifest),
  rows=rows,declared_randomization_off=True,model_ready=False,run_authority=False))
 protocol=c.write(out/"INPUT_PROTOCOL.json",dict(schema="kivi.actual-b1-fixed1024-input/v1",
  source_ref=source,plan_ref=plan,prompt_ref=tokens,protocol=policy.PROTOCOL,
  requests=[dict(row,payload=policy.payload(prompt,row["outputs"]))for row in policy.rows(run_id)],
  prompt_tokens=32768,maximum_completion_tokens=1024,model_ready=False,run_authority=False))
 return plan,protocol

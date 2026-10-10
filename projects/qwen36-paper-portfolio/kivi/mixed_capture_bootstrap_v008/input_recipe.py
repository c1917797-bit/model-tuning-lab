"""Complete64 input production before any container; no model/NPU work."""
from pathlib import Path
def create(c,source,model_manifest,out,run_id):
 def role(n):r=c.role(n);return c.module(r["path"],r["sha256"],"_mixed_input_"+n)
 life=role("input_lifecycle");matched=role("matched_prompts");oracle=role("assignment_oracle")
 maker=role("input_plan")
 model=c.obj(model_manifest);root=Path(model["host_model_root"])
 config=c.obj(c.bound(root/"config.json",c.CONFIG_SHA));text=config.get("text_config",{})
 vocab=text.get("vocab_size")
 c.require(config.get("model_type")=="qwen3_5" and text.get("model_type")=="qwen3_5_text"
  and type(vocab)is int and vocab>0,"actual composite text vocabulary")
 for i in range(4):
  prompt=matched.prompt_ids(i)
  c.require(len(prompt)==32768 and all(type(t)is int and 0<=t<vocab for t in prompt),"whole actual token domain")
 token=c.write(out/"TOKENIZER_BINDING.json",dict(model_manifest=model_manifest,
  tokenizer_config=c.ref(root/"tokenizer_config.json"),raw_token_ids=True,chat_template_applied=False))
 return maker.create(life=life,matched=matched,oracle=oracle,
  publish=lambda label,value:c.write(out/(label+".json"),value),model_binding_ref=model_manifest,
  tokenizer_ref=token,producer_source_ref=c.role("input_plan"),run_id=run_id)

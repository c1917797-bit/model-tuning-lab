"""Common text-only workload options; no model/kernel change."""
import json
LIMITS={'image':0,'video':0}
FLAG='--limit-mm-per-prompt'
def argv(value):
 out=list(value)
 if FLAG in out or any(x.startswith(FLAG+'=')for x in out):raise ValueError('no hidden or duplicate multimodal limit')
 return out+[FLAG,json.dumps(LIMITS,sort_keys=True,separators=(',',':'))]
def require_parsed(args,engine):
 for name,obj in(('serve parser',args),('AsyncEngineArgs',engine)):
  limits=getattr(obj,'limit_mm_per_prompt',None)
  if type(limits)is not dict or any(type(limits.get(k))is not int or limits[k]!=0 for k in LIMITS):raise ValueError('actual '+name+' text-only image/video zero quotas')
  if getattr(obj,'enable_mm_embeds',None)is not False:raise ValueError('actual '+name+' multimodal embeddings disabled')
 from vllm.config.multimodal import MultiModalConfig
 mm=MultiModalConfig(limit_per_prompt=engine.limit_mm_per_prompt,enable_mm_embeds=engine.enable_mm_embeds)
 values={k:mm.get_limit_per_prompt(k)for k in LIMITS}
 if any(type(x)is not int or x!=0 for x in values.values()):raise ValueError('actual current-image MultiModalConfig zero quotas')
 return dict(schema='bole.actual-common-text-only-parser/v1',limit_mm_per_prompt=values,model_config_constructed=False,NPU=False)

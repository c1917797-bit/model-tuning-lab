"""Frozen final-task input gate only; never downloads/generates data or scores."""
import math
import source_contract as c
PY="/usr/local/python3.12.13/bin/python3"
def manifest(ref):
 x=c.obj(ref)
 c.require(x.get("schema")=="qwen36.frozen-final-task-inputs/v1" and set(x.get("tasks",{}))=={"LongBench-v2","GSM8K"} and
  x.get("max_tokens")==2048 and x.get("thinking_mode_enabled") is False and x.get("temperature")==0 and
  x.get("seed")==0 and x.get("ignore_eos") is False,"actual frozen two-task no-thinking normalEOS2048 protocol")
 for name,row in x["tasks"].items():
  for key in ("dataset","prompts","scorer_source"):
   r=row[key];c.bound(r["path"],r["sha256"])
  cli=row["scorer_cli"]
  c.require(cli[:3]==[PY,"-B",row["scorer_source"]["path"]] and cli.count("@RESPONSES@")==cli.count("@OUTPUT@")==1,
   "actual frozen scorer source+exact CLI")
 return x
def loss(dense,candidate):
 c.require(type(dense) in (int,float) and type(candidate) in (int,float) and math.isfinite(dense) and
  math.isfinite(candidate) and 0<dense<=1 and 0<=candidate<=1,"actual proportions from bound scorer output, no intermediate tensor loss")
 pp=(dense-candidate)*100;relative=(dense-candidate)/dense*100
 return dict(loss_percentage_points=pp,loss_relative_percent=relative,accepted=pp<=1 and relative<=1,
  limit_interpretation="conservative both<=1, each task separately",
  cannot_substitute_for_native_or_full64_numeric=True)

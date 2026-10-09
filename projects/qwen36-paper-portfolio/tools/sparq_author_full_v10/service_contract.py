"""FULLv3 host/HTTP facade. Exact current41-source prerequisite; no legacy kernel grant."""
from __future__ import annotations
import hashlib,importlib.util,json,math,os,re,time
from pathlib import Path
import common,source_contract as sc
BASE=Path(__file__).resolve().parent
ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab")
INTEGRATED=Path("/opt/host/vnf/austinov/model-tuning-lab/projects/qwen36-paper-portfolio/tools/sparq_author_full_v10")
KERNEL=sc.KERNEL;KERNEL_SHA=sc.KERNEL_SHA
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
PY="/usr/local/python3.12.13/bin/python3";GIB=1024**3
PAPER_CUT="2026-10-08T19:00:00+00:00";PORTFOLIO_CUT="2026-10-09T11:17:31+00:00"
# New human-authorized total72h stage; historical paper/portfolio dates stay unchanged.
USER72H_CUT="2026-10-12T07:00:25+00:00";CUT=USER72H_CUT
execution_clock=sc.execution_clock;validate_execution_clock=sc.validate_execution_clock
FA=common.FA;GDN=tuple(i for i in range(64) if i%4!=3)
CONFIG_SHA="69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c"
MODEL_MANIFEST_REF={"path":"/cache/cch/qwen36-paper-preparation-20261007/sparse/actual-input-inventory-v1-001/MAIN-original-checkpoint-fullhash-20261008-001/ACTUAL_MODEL_MANIFEST.json",
 "sha256":"11ac18fa31878609b6b56a9c9213d12729cdb466d14c587efcf6d261566a706c"}
ORIGINAL_MODEL_ROOT="/cache/efim/Qwen3.6-27B"
NATIVE_BYTES=10*GIB;AUX_CEILING=2*GIB;TOTAL_STATE_CEILING=NATIVE_BYTES+AUX_CEILING;HBM_RESERVE_MIB=3072
COMMON=common.COMMON
PROTOCOL=dict(requests=40,concurrency=16,input_tokens=32768,shared_prefix_tokens=16384,output_tokens=1024,
 temperature=0,seed=0,ignore_eos=True,warmups=2,prompt_kind="raw-token-ids-no-chat-template",thinking_mode_enabled=False)
DIAGNOSTIC_PROTOCOL=dict(PROTOCOL,requests=407,output_tokens=160,
 purpose="actual TP4/64layer/longcontext/request-reuse diagnostic; no matched performance")
H8=ROOT/"projects/kvbuffer-parallel-ascend/tools/short_horizon_h8_gate_v4/host_run.py"
DEPS={str(H8):"4ddd75d6ce7558f0131992da3a5514df43dfb4b33f45674722ba5769ecef5e20",
 str(ROOT/"projects/kvbuffer-parallel-ascend/tools/full_matrix_host_v2/host.py"):"ab0296c698df00c9c3b2ce377601f6d6723adde6efb4a9e65407beca51ba5f86",
 str(ROOT/"projects/kvbuffer-parallel-ascend/tools/saved_step_native_order_v2/host_run.py"):"86c1ca7f59c6ad5b2b4d5efb155394455a12376cf368e06f9e2e13d39b7192fc"}
require=sc.require;canonical=sc.canonical;sha=sc.sha;bound=sc.bound;obj=sc.obj;write=sc.write;module=sc.module
def digest(value):return hashlib.sha256(canonical(value)).hexdigest()
def source(ref,context="host"):
 source_,files=sc.source(ref["path"],ref["sha256"]);m=sc.obj(source_);return m
def component(ref,replay=False):return sc.component(ref,replay=replay)
def component_readonly_mounts(ref):
 from component_handoff import readonly_component_mounts
 return readonly_component_mounts(ref)
def model(ref,host=True):
 require(ref==MODEL_MANIFEST_REF,"exact actual original29-file checkpoint Ref; no model switch by display label")
 x=obj(ref);require(x.get("host_model_root")==ORIGINAL_MODEL_ROOT and x.get("complete_file_count")==29 and
  x.get("weight_shard_count")==15 and x.get("total_bytes")==55586107940 and x.get("schema")=="qwen36.actual-model-manifest/v1" and x.get("image_id")==IMAGE and
  x.get("config_sha256")==CONFIG_SHA and x.get("dtype")=="bfloat16" and type(x.get("files")) is list and x["files"],
  "actual MAIN frozen model/tokenizer manifest mandatory, no invented data revision")
 root=Path(x["host_model_root"] if host else "/models/Qwen3.6-27B")
 require(root.is_absolute() and ".." not in root.parts and root.is_dir() and not root.is_symlink(),"actual ordinary model root")
 seen=set()
 for row in x["files"]:
  n=row["relative_path"];p=Path(n)
  require(not p.is_absolute() and ".." not in p.parts and n not in seen and
    re.fullmatch("[a-f0-9]{64}",row["sha256"]) and type(row["size_bytes"]) is int and row["size_bytes"]>=0,
    "unique full frozen model file metadata");seen.add(n)
  path=root/p;require(path.is_file() and not path.is_symlink() and path.stat().st_size==row["size_bytes"],"actual frozen model inventory size")
 require("config.json" in seen and any(n.startswith("tokenizer") for n in seen) and
  any(n.endswith(".safetensors") for n in seen),"model weights/tokenizer/config complete inventory required")
 require(sha(root/"config.json")==CONFIG_SHA,"actual config bytes changed")
 # Weight/tokenizer SHA verification is a MAIN-only preflight, not child preparation.
 for row in x["files"]:bound(root/row["relative_path"],row["sha256"])
 return x
def iter_prompt_array(path,max_item_chars=2*1024**2):
 """Bounded streaming top-level array; no full token-array JSON in host RAM."""
 decoder=json.JSONDecoder();buf="";pos=0;eof=False
 p=Path(path);require(p.is_absolute() and p.resolve()==p and p.is_file() and not p.is_symlink(),"ordinary exact task prompt file")
 with p.open("r",encoding="utf-8") as f:
  def fill():
   nonlocal buf,pos,eof
   buf=buf[pos:];pos=0
   part=f.read(65536);eof=not part;buf+=part
   require(len(buf)<=max_item_chars,"bounded individual prompt JSON item")
  def whitespace():
   nonlocal pos
   while True:
    while pos<len(buf) and buf[pos] in " \t\r\n":pos+=1
    if pos<len(buf) or eof:return
    fill()
  whitespace();require(pos<len(buf) and buf[pos]=="[","original prompts must be JSON array");pos+=1
  whitespace()
  if pos<len(buf) and buf[pos]=="]":pos+=1
  else:
   while True:
    while True:
     try:value,end=decoder.raw_decode(buf,pos);break
     except json.JSONDecodeError:
      require(not eof,"invalid/incomplete original prompt JSON");fill()
    pos=end;yield value;whitespace()
    require(pos<len(buf),"incomplete original prompts array")
    delimiter=buf[pos];pos+=1
    if delimiter=="]":break
    require(delimiter==",","original prompt array comma/closing bracket");whitespace()
    require(pos<len(buf) and buf[pos]!="]","trailing comma rejected")
  whitespace();require(pos==len(buf) and eof,"trailing non-whitespace original prompt bytes")
def task_prompts(task):
 count=task["request_count"];require(type(count) is int and 0<count<=100000,"bounded full task request count")
 bound(task["prompts"]["path"],task["prompts"]["sha256"]);ids=set();n=0
 for row in iter_prompt_array(task["prompts"]["path"]):
  require(type(row) is dict and type(row.get("id")) is str and 0<len(row["id"])<=256 and row["id"] not in ids,
   "unique actual full task ID")
  tokens=row.get("prompt_token_ids")
  require(type(tokens) is list and 0<len(tokens)<=38912 and all(type(t) is int and 0<=t<248320 for t in tokens),
   "full actual exact task prompt token IDs <=38912; no tokenization/unknown IDs")
  ids.add(row["id"]);n+=1;require(n<=count,"extra full task prompt row")
  yield row
 require(n==count,"full exact task request count mismatch")
def task_manifest(ref):
 x=obj(ref);require(x.get("schema")=="qwen36.frozen-final-task-inputs/v1" and x.get("tasks") and
  set(x["tasks"])=={"LongBench-v2","GSM8K"} and x.get("max_tokens")==2048 and
  x.get("thinking_mode_enabled") is False and x.get("temperature")==0 and x.get("seed")==0,
  "actual two-task frozen2048 dataset/prompt/scorer/sampling identity required")
 for task,t in x["tasks"].items():
  for key in ("dataset","prompts","scorer_source","prompt_source","no_thinking_template_source"):bound(t[key]["path"],t[key]["sha256"])
  require(t.get("prompt_protocol") and t["prompt_protocol"].get("apply_chat_template_kwargs")==dict(enable_thinking=False) and
   t["prompt_protocol"].get("tokenizer_manifest")==MODEL_MANIFEST_REF and t["prompt_protocol"].get("source")==t["prompt_source"],
   "actual frozen prompt generator/template/tokenizer evidence required; completion extra enable_thinking is ignored")
  for row in task_prompts(t):pass
  require(t.get("scorer_cli") and t["scorer_cli"][0]==PY and t["scorer_cli"][1]=="-B" and
   t["scorer_cli"][2]==t["scorer_source"]["path"] and t["scorer_cli"].count("@RESPONSES@")==1 and
   t["scorer_cli"].count("@OUTPUT@")==1,"actual original scorer CLI source/placeholder positions")
 return x
def loss(d,c):
 require(type(d) in (int,float) and type(c) in (int,float) and math.isfinite(d) and math.isfinite(c) and 0<d<=1 and 0<=c<=1,
   "actual score proportions")
 pp=(d-c)*100;relative=(d-c)/d*100
 return dict(loss_percentage_points=pp,loss_relative_percent=relative,accepted=pp<=1 and relative<=1,
  limit_interpretation="conservative both <=1; keep actual both values")
def prompt_ids(i):
 require(type(i) is int and 0<=i<40,"fixed40 index")
 return [1000+j%257 for j in range(16384)]+[2000+(i*131+j*17)%4093 for j in range(16384)]

def server_argv(port):
 from full_entry import server_argv as entry
 return entry(port)
def docker_argv(cid,args):
 require(re.fullmatch("[a-f0-9]{64}",cid or ""),"exact complete owned CID")
 return ["/usr/bin/docker","exec",cid,"/bin/bash","-c",'source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"',"kvbp-diagnostic",PY,"-B",*args]
def own_mount_path(root,p):
 root=Path(root);path=Path(p)
 require(root.is_absolute() and path.is_absolute() and root in path.parents and path.resolve()==path
  and ".." not in path.parts,"actual same-path cache owned arm output; no guest alias")
 return path
def required_source_mounts():
 km=obj(dict(path=str(KERNEL/"SOURCE_MANIFEST.json"),sha256=KERNEL_SHA))
 result=set(DEPS)|set(sc.PINS)
 result.update(km["dependencies"])
 result.update(v["captured_source_ref"]["path"] for v in [km["native_device_operator"],*km["model_sources"].values()])
 return sorted(result)

def diagnostic_authority(ref,component_ref,source_ref,replay=False):
 from consume_model import consume_authority
 return consume_authority(ref,source_ref,component_ref,replay=replay)

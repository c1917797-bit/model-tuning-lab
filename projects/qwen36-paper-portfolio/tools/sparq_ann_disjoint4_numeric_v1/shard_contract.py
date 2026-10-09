"""Disjoint FOUR-card allocation/coverage, stdlib only; no numerical oracle.
Immutable global coordinates/seeds preserve original run_case math and inputs.
Weights are source-derived live-token operation counts, NOT elapsed timings.
"""
import hashlib,json
from pathlib import Path
CARDS=(4,5,6,7)
MODES=(("eager",0),("graph",0),("graph",1),("graph",2))
SCHEMA="sparq.author-ann-disjoint4-allocation/v1"
SHARD_SCHEMA="sparq.author-ann-disjoint-numeric/v1"
AGG_SCHEMA="sparq.author-ann-disjoint4-numeric/v1"
BASE_SOURCE={"path":"/opt/host/vnf/austinov/model-tuning-lab/projects/qwen36-paper-portfolio/tools/sparq_token_native_v6/SOURCE_MANIFEST.json","sha256":"eb7ed908879c6bdea7fab670bcf83e570a7439045e2d8e5c4535c6a41611f528"}
ORIGINAL_MATRIX_SHA="02484f6fecd08548f4eebac5eb39e6552affc4b0fc2c3a8591fff86eac3f56d4"
def need(ok,why):
 if not ok:raise ValueError(why)
def digest(value):
 return hashlib.sha256((json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode()).hexdigest()
def coordinates():
 return [(b,m,c,t) for b in range(1,17) for m,t in MODES for c in (False,True)]
def coordinate(row):
 need(type(row) is dict and set(row)=={"batch","mode","reallocation","trial","case_id","seed"},"exact immutable coordinate fields")
 b,m,c,t=(row[k] for k in ("batch","mode","reallocation","trial"))
 need(type(b) is int and b in range(1,17) and type(c) is bool and (m,t) in MODES,"actual original full matrix coordinate")
 need(row["case_id"]=="b%d-%s-mean%d-t%d"%(b,m,c,t) and type(row["seed"]) is int and row["seed"]==49585+b+100*t,"original GLOBAL coordinate/seed, no local reindex")
 return b,m,c,t
def row(key):
 b,m,c,t=key
 return dict(batch=b,mode=m,reallocation=c,trial=t,case_id="b%d-%s-mean%d-t%d"%(b,m,c,t),seed=49585+b+100*t)
def token_work(batch):
 """Original 160-step rotating slots + step80 reuse, no Torch or math outputs.
 Independent scheduling estimator; does not replace any validation oracle.
 """
 need(type(batch) is int and batch in range(1,17),"true B1..16 source cost")
 slots=list(range(batch));lengths={s:2048-3*s for s in slots};total=0
 for step in range(160):
  if step%11==0:slots=slots[1:]+slots[:1]
  if step==80:lengths[slots[0]]=1
  total+=sum(lengths[s]+1 for s in slots)
  for s in slots:lengths[s]+=1
 return total
def allocation():
 """Deterministic LPT over complete original cases, balanced by source cost.
 Stable ties use global coordinate index; all eight variants of every B survive.
 """
 keys=coordinates();weights={key:token_work(key[0]) for key in keys}
 groups=[[] for _ in CARDS];totals=[0]*4
 order=sorted(enumerate(keys),key=lambda pair:(-weights[pair[1]],pair[0]))
 for _,key in order:
  i=min(range(4),key=lambda j:(totals[j],len(groups[j]),(j-key[0])%4))
  groups[i].append(key);totals[i]+=weights[key]
 for group in groups:group.sort(key=keys.index)
 return dict(schema=SCHEMA,cards=list(CARDS),full_cases=128,steps_per_case=160,full_steps=20480,
  original_matrix_sha256=ORIGINAL_MATRIX_SHA,
  cost_model=dict(kind="source-derived-live-query-token-count",measured_elapsed=False,
   formula="sum160(sum actual per-request length after rotation/step80 reset)",
   limitations="constant capture/cache/serialization and CPU/NPU operation timing not measured; no duration guarantee"),
  shards=[dict(shard_id=i,physical=card,logical=0,assigned_cases=[row(k) for k in groups[i]],
   assigned_count=len(groups[i]),assigned_steps=len(groups[i])*160,estimated_token_work=totals[i])
   for i,card in enumerate(CARDS)])
def validate_allocation(plan):
 expected=allocation()
 need(plan==expected,"exact preregistered allocation/cost model; no omitted/changed cases, seeds or map")
 seen=set()
 for shard in plan["shards"]:
  for r in shard["assigned_cases"]:
   k=coordinate(r);need(k not in seen,"disjoint case ownership");seen.add(k)
 need(seen==set(coordinates()) and sum(s["assigned_steps"] for s in plan["shards"])==20480,"EXACT all128/20480 aggregate coverage")
 return plan
def assigned(plan,shard_id):
 validate_allocation(plan);need(type(shard_id) is int and shard_id in range(4),"actual shard ID0..3")
 return plan["shards"][shard_id]
def check_headers(report,plan,shard_id):
 shard=assigned(plan,shard_id)
 need(report.get("schema")==SHARD_SCHEMA and report.get("shard_id")==shard_id and
  report.get("physical")==shard["physical"] and report.get("logical")==0 and report.get("status")=="shard_passed",
  "actual shard scope; never original128 report/PASS")
 need(report.get("allocation_sha256")==digest(plan) and report.get("assigned_cases")==shard["assigned_cases"] and
  report.get("completed_cases")==shard["assigned_count"] and report.get("completed_steps")==shard["assigned_steps"],
  "actual declared versus completed immutable shard coverage")
 headers=report.get("cases");need(type(headers) is list and len(headers)==shard["assigned_count"],"actual complete shard case headers")
 actual=[]
 for h in headers:
  r={k:h[k] for k in ("batch","mode","reallocation","trial")}
  r.update(case_id="b%d-%s-mean%d-t%d"%(r["batch"],r["mode"],r["reallocation"],r["trial"]),seed=49585+r["batch"]+100*r["trial"])
  actual.append(r)
 need(actual==shard["assigned_cases"],"ordered exact assigned coordinates; duplicate/missing or wrong shard rejected")
 return shard
def joint_budget(host,daemon):
 need(host["effective_capacity"]>=1 and daemon["effective_capacity"]>=6,"host1 + four guests + reserve2 actual effective CPU")
 hc=min(host["effective_cpus"]);spare=sorted(set(daemon["effective_cpus"])-{hc})
 need(len(spare)>=6,"seven distinct host/guest/reserve effective CPU slots")
 common={r["key"]:r["capacity"] for r in host["quota_ancestors"]}
 caps=[r["capacity"] for r in daemon["quota_ancestors"] if r["key"] in common and r["capacity"] is not None]
 caps += [common[r["key"]] for r in daemon["quota_ancestors"] if r["key"] in common and common[r["key"]] is not None]
 need(not caps or min(caps)>=7,"shared actual cgroup ancestor admits summed sevenCPU")
 return dict(host_cpu=hc,guest_cpus=spare[:4],reserve_cpus=spare[4:6],host_cpu_budget=1,
  guest_cpu_budget=4,reserve_cpu_budget=2,common_finite_capacity=min(caps) if caps else None,future_external_guarantee=False)

OWNER="sparq-ann-disjoint4-v1"
ROOT=Path(__file__).resolve().parent
PHASE_SECONDS=5400
CLEANUP_SECONDS=90
GUEST_BYTES=8*1024**3
HOST_BYTES=256*1024**2
RESERVE_BYTES=8*1024**3
OUTPUT_BYTES=4*5*1024**3
OWN=("shard_contract.py","shard_rows.py","shard_proof.py","shard_numeric.py","shard_host.py","shard_consume.py","test_shards.py")
def read_ref(ref):
 p=Path(ref["path"]);need(p.is_absolute() and p.is_file() and not p.is_symlink() and ".." not in p.parts,"exact absolute ordinary Ref")
 h=hashlib.sha256()
 with p.open("rb") as f:
  for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
 need(h.hexdigest()==ref["sha256"],"original Ref bytes changed")
 return p.read_bytes()
def own_identity(path,sha256):
 import re
 p=Path(path);need(p==ROOT/"SOURCE_MANIFEST.json" and re.fullmatch("[0-9a-f]{64}",sha256 or ""),"exact current packet manifest")
 ref=dict(path=str(p),sha256=sha256);m=json.loads(read_ref(ref))
 need(m["schema"]=="sparq.disjoint4-source/v1" and m["ready"] is False and set(m["files"])==set(OWN) and m["native_source"]==BASE_SOURCE,"separate immutable packet+native substrate identities")
 for name,d in m["files"].items():read_ref(dict(path=str(ROOT/name),sha256=d))
 mf=json.loads(read_ref(BASE_SOURCE));need(mf["source_count"]==42 and len(mf["files"])==31 and mf["files"]["matrix.py"]==ORIGINAL_MATRIX_SHA and m["native_files"]==mf["files"],"original native42 complete immutable substrate")
 for name,d in mf["files"].items():read_ref(dict(path=str(Path(BASE_SOURCE["path"]).parent/name),sha256=d))
 pins={}
 for path,d in mf["dependencies"].items():pins[path]=d
 for pair in [mf["native_device_operator"],*mf["model_sources"].values()]:
  pins[pair["captured_source_ref"]["path"]]=pair["captured_source_ref"]["sha256"]
 for r in (mf["author_sources"]["ann"],mf["author_sources"]["causal"],*mf["author_sources"]["identities"],mf["execution_clock"]["authorization"]):
  pins[r["path"]]=r["sha256"]
 need(len(pins)==11 and m["native_external_pins"]==pins and m["source_count"]==50,"seven packet +42 native +native manifest, no self manifest recursion")
 for path,d in pins.items():read_ref(dict(path=path,sha256=d))
 need(m["allocation"]==allocation() and m["execution_clock"]["owner"]==OWNER and
  {k:v for k,v in m["execution_clock"].items() if k!="owner"}=={k:v for k,v in mf["execution_clock"].items() if k!="owner"},
  "unchanged human72h cutoff/authorization, explicit NEW definition owner")
 return ref,m
def native():
 import importlib,sys
 root=str(Path(BASE_SOURCE["path"]).parent)
 if root not in sys.path:sys.path.insert(0,root)
 module=importlib.import_module("receipt")
 need(Path(module.__file__).resolve()==Path(root)/"receipt.py","actual frozen native namespace, no runtime global patch")
 source,files=module.source_identity(Path(root),Path(BASE_SOURCE["path"]),BASE_SOURCE["sha256"])
 return module,source,files
def shard_argv(output,proof,allocation_ref,own_ref,shard_id):
 c,source,files=native()
 return [c.PY,"-B",str(ROOT/"shard_numeric.py"),"--execute","--output",str(output),
 "--device-proof",proof["path"],"--device-proof-sha256",proof["sha256"],
 "--allocation",allocation_ref["path"],"--allocation-sha256",allocation_ref["sha256"],"--shard-id",str(shard_id),
 "--source-manifest",own_ref["path"],"--source-manifest-sha256",own_ref["sha256"]]
def publication(path,value):
 # Uses frozen atomic exclusive serialization, never critical candidate math.
 native()
 from contract import write_new
 return write_new(Path(path),value)

def own_clock(manifest):
 c,_,_=native()
 value=dict(c.execution_clock(),owner=OWNER)
 need(manifest["execution_clock"]==value,"same human72h repair cutoff, no reset")
 return value

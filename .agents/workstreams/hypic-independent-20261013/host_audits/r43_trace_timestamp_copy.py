"""Offline decimal timestamp adapter; original capture/parser/canonical gate unchanged."""
import argparse,hashlib,json,math,os,re,shutil,sys
from decimal import Decimal,ROUND_FLOOR
from pathlib import Path
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits import r43_renewal_policy as policy
from host_audits.r41_profile_trace import inventory,audit_tree,sha
NUMBER=re.compile(r"-?[0-9]+(?:\.[0-9]{1,9})?\Z")
def decimal_time(value):
 if type(value)not in(str,int,float):raise ValueError("timestamp type")
 if type(value)is float and not math.isfinite(value):raise ValueError("nonfinite timestamp")
 text=str(value)
 if len(text)>30 or not NUMBER.fullmatch(text):raise ValueError("timestamp decimal grammar")
 d=Decimal(text)
 if not d.is_finite()or abs(d)>=Decimal("1e18"):raise ValueError("timestamp bound")
 return d
def events_of(raw):
 ev=raw.get("traceEvents")if isinstance(raw,dict)else raw
 if not isinstance(ev,list)or not ev:raise ValueError("complete nonempty trace array required")
 return ev
def inspect_events(events):
 times=[];complete=0
 for e in events:
  if not isinstance(e,dict):raise ValueError("event object required")
  if "ts"in e:times.append(decimal_time(e["ts"]))
  if e.get("ph")=="X":
   if "ts"not in e:raise ValueError("complete span timestamp absent")
   d=e.get("dur")
   if type(d)not in(int,float)or not math.isfinite(d)or d<0:raise ValueError("finite nonnegative duration required")
   complete+=1
 if not times or not complete:raise ValueError("actual timestamped complete spans required")
 return min(times),len(events),complete
def adapt_events(events,origin):
 result=[]
 for e in events:
  n=dict(e)
  if "ts"in e:
   relative=decimal_time(e["ts"])-origin
   value=float(relative)
   if not math.isfinite(value)or relative<0 or Decimal(str(value))!=relative:raise ValueError("timestamp decimal roundtrip loss")
   n["ts"]=value
  result.append(n)
 verify_events(events,result,origin)
 return result
def verify_events(original,normalized,origin):
 inspect_events(original);inspect_events(normalized)
 if len(original)!=len(normalized):raise ValueError("event count differs")
 changed=0
 for a,b in zip(original,normalized):
  if set(a)!=set(b):raise ValueError("event fields differ")
  if any(a[k]!=b[k]for k in a if k!="ts"):raise ValueError("non-timestamp event field differs")
  if "ts"in a:
   if type(b["ts"])not in(int,float)or not math.isfinite(b["ts"]):raise ValueError("normalized timestamp not finite numeric")
   if decimal_time(b["ts"])+origin!=decimal_time(a["ts"]):raise ValueError("timestamp exact decimal offset differs")
   changed+=1
 return {"events":len(original),"timestamps":changed,"all_non_ts_fields_and_order_preserved":True,"exact_decimal_time_differences_preserved":True}
def save(path,value):
 data=(json.dumps(value,sort_keys=True,allow_nan=False,separators=(",",":"))+"\n").encode()
 with Path(path).open("xb")as f:f.write(data);f.flush();os.fsync(f.fileno())
 return hashlib.sha256(data).hexdigest()
def load_plan(path):
 path=Path(path).resolve();plan=json.loads(path.read_bytes())
 if sha(__file__)!=plan["helper_sha256"]:raise ValueError("timestamp helper source drift")
 cp=W/plan["contract"]
 if sha(cp)!=plan["contract_sha256"]:raise ValueError("timestamp contract drift")
 c=json.loads(cp.read_bytes());policy.check(c,root=W,require_new_root=False)
 source=Path(plan["parsed_root"]);output=Path(plan["normalized_root"])
 if source.parent!=policy.RAW_PARENT or output.parent!=policy.RAW_PARENT or source==output or source.is_symlink()or output.is_symlink():raise ValueError("dedicated distinct parser/normalization roots required")
 rp=source/"result.json"
 if sha(rp)!=plan["parser_result_sha256"]:raise ValueError("actual parser result drift")
 r=json.loads(rp.read_bytes())
 if r.get("exit_code")!=0 or not r.get("original_capture_unchanged")or r.get("failure",{}).get("message")!="finite nonnegative complete event spans required":raise ValueError("exact completed official parse/schema-failure provenance required")
 if set(plan["trace_sha256"])!={str(p.relative_to(source/"profiles"))for p in(source/"profiles").glob("*/ASCEND_PROFILER_OUTPUT/trace_view.json")}:raise ValueError("four exact trace paths required")
 if len(plan["trace_sha256"])!=4:raise ValueError("four trace ranks required")
 return plan,c,source,output
def run(plan_path):
 plan,c,source,output=load_plan(plan_path)
 if output.exists():raise ValueError("new exclusive normalization root required")
 files,total=inventory(source/"profiles");inputs={str(p.relative_to(source/"profiles")):sha(p)for p in files}
 if any(inputs.get(n)!=h for n,h in plan["trace_sha256"].items()):raise ValueError("source trace drift")
 if os.statvfs(output.parent).f_bavail*os.statvfs(output.parent).f_frsize<8*1024**3:raise ValueError("normalization raw space")
 scans=[]
 for name in sorted(plan["trace_sha256"]):
  raw=json.loads((source/"profiles"/name).read_bytes());scans.append(inspect_events(events_of(raw)));del raw
 origin=min(x[0]for x in scans).to_integral_value(rounding=ROUND_FLOOR)
 output.mkdir()
 save(output/"input-manifest.json",{"files":inputs,"plan_sha256":sha(plan_path),"origin_us":str(origin),"units":"us","official_parsed_root":str(source)})
 for p in files:
  rel=str(p.relative_to(source/"profiles"))
  if rel in plan["trace_sha256"]:continue
  q=output/"profiles"/rel;q.parent.mkdir(parents=True,exist_ok=True)
  with p.open("rb")as src,q.open("xb")as dst:shutil.copyfileobj(src,dst,1024**2)
 rows={}
 for name in sorted(plan["trace_sha256"]):
  raw=json.loads((source/"profiles"/name).read_bytes());events=events_of(raw);norm=adapt_events(events,origin)
  converted=dict(raw,traceEvents=norm)if isinstance(raw,dict)else norm
  target=output/"profiles"/name;target.parent.mkdir(parents=True,exist_ok=True);save(target,converted)
  del converted
  persisted=json.loads(target.read_bytes());proof=verify_events(events,events_of(persisted),origin)
  rows[name]={**proof,"input_sha256":inputs[name],"output_sha256":sha(target)};del raw,events,norm,persisted
 if any(sha(source/"profiles"/n)!=h for n,h in inputs.items()):raise ValueError("original parsed source mutated")
 release=json.loads(Path(plan["release_proof"]["path"]).read_bytes())
 if sha(plan["release_proof"]["path"])!=plan["release_proof"]["sha256"]:raise ValueError("capture release proof drift")
 workers={int(k):int(v)for k,v in release["graph"]["workers"].items()}
 metrics=audit_tree(output/"profiles",workers)
 result={"schema":"hypic-r43-exact-timestamp-copy/v1","helper_sha256":sha(__file__),"plan_sha256":sha(plan_path),"origin_us":str(origin),"units":"us","rows":rows,"official_parsed_unchanged":True,"four_rank_trace_valid":metrics["four_rank_trace_valid"],"profiler":metrics,"original_failed_audit_preserved":True,"full_goal_complete":False,"new_performance_acceptance":False}
 digest=save(output/"result.json",result)
 print(json.dumps({"result":str(output/"result.json"),"sha256":digest,"four_rank_trace_valid":result["four_rank_trace_valid"],"origin_us":str(origin),"events":sum(r["events"]for r in rows.values())}))
def verify(plan_path,result_path):
 plan,c,source,output=load_plan(plan_path);r=json.loads(Path(result_path).read_bytes())
 if Path(result_path)!=output/"result.json"or r["plan_sha256"]!=sha(plan_path)or r["helper_sha256"]!=sha(__file__)or not r["four_rank_trace_valid"]:raise ValueError("exact normalization result linkage required")
 m=json.loads((output/"input-manifest.json").read_bytes());origin=Decimal(m["origin_us"])
 if m["plan_sha256"]!=sha(plan_path)or r["origin_us"]!=m["origin_us"]or m["units"]!="us":raise ValueError("one shared microsecond origin required")
 files,_=inventory(source/"profiles")
 if {str(p.relative_to(source/"profiles")):sha(p)for p in files}!=m["files"]:raise ValueError("official parsed input changed")
 if {str(p.relative_to(output/"profiles"))for p in inventory(output/"profiles")[0]}!=set(m["files"]):raise ValueError("normalized file set differs")
 for n,h in m["files"].items():
  target=output/"profiles"/n
  if n not in plan["trace_sha256"]:
   if sha(target)!=h:raise ValueError("non-trace file changed")
   continue
  if r["rows"][n]["input_sha256"]!=h or sha(target)!=r["rows"][n]["output_sha256"]:raise ValueError("trace byte linkage differs")
  a=json.loads((source/"profiles"/n).read_bytes());b=json.loads(target.read_bytes())
  if isinstance(a,dict)and {k:v for k,v in a.items()if k!="traceEvents"}!={k:v for k,v in b.items()if k!="traceEvents"}:raise ValueError("trace envelope changed")
  verify_events(events_of(a),events_of(b),origin);del a,b
 return {"normalized_root":str(output),"origin_us":str(origin),"rows":r["rows"],"result_sha256":sha(result_path),"plan_sha256":sha(plan_path),"helper_sha256":sha(__file__),"all_records_replayed":True}
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--plan",required=True);a=p.parse_args();run(a.plan)

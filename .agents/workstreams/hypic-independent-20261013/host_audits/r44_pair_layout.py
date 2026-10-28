"""Read-only accepted R44 trace/CSV orientation; no service-speed inference."""
import argparse,collections,csv,gc,hashlib,json,math,os,resource,time
from pathlib import Path
W=Path(__file__).resolve().parent.parent
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def events_of(data):
 events=data.get("traceEvents")if isinstance(data,dict)else data
 if not isinstance(events,list)or not events:raise ValueError("complete nonempty trace required")
 return events
def flow_key(event):
 value=event.get("id")
 if type(value)not in(int,str):return None
 return(str(event.get("cat","")),str(event.get("name","")),type(value).__name__,str(value))
def flow_summary(events):
 keys={};unsupported=0;samples={}
 for event in events:
  phase=event.get("ph")
  if phase not in("s","t","f"):continue
  key=flow_key(event)
  if key is None:unsupported+=1;continue
  keys.setdefault(key,collections.Counter())[phase]+=1
  samples.setdefault(key[0],{"name":key[1],"id_type":key[2],"id_string":key[3]})
 result={}
 for key,row in keys.items():
  cat=key[0];out=result.setdefault(cat,collections.Counter());out["keys"]+=1
  out["starts"]+=row["s"];out["ends"]+=row["f"];out["intermediate"]+=row["t"]
  if row["s"]==1 and row["f"]==1:out["one_to_one"]+=1
  if row["s"]==1 and row["f"]>1:out["fan_out"]+=1
  if row["s"]>1:out["ambiguous_multi_start"]+=1
  if row["s"]==0:out["missing_start"]+=1
  if row["f"]==0:out["missing_end"]+=1
 return {"categories":{k:dict(v)for k,v in result.items()},"unsupported_id_events":unsupported,"examples":samples,
 "scope":"Typed rank-local category/name/ID cardinality only; fan-out/unmatched/ambiguous retained. No inferred causal edges."}
def interval_union(intervals):
 rows=sorted(intervals);total=0.0;end=None
 for start,stop in rows:
  if not math.isfinite(start)or not math.isfinite(stop)or stop<start:raise ValueError("finite ordered interval required")
  if end is None or start>end:total+=stop-start;end=stop
  elif stop>end:total+=stop-end;end=stop
 return total
def finite_span(event):
 start=event.get("ts");duration=event.get("dur")
 if type(start)not in(int,float)or type(duration)not in(int,float)or not math.isfinite(start)or not math.isfinite(duration)or duration<0:raise ValueError("finite numeric nonnegative complete span required")
 return start,start+duration
def trace_layout(path):
 data=json.loads(path.read_bytes(),parse_constant=lambda s:(_ for _ in()).throw(ValueError("nonfinite JSON")))
 events=events_of(data);names={}
 for e in events:
  if e.get("ph")=="M"and e.get("name")=="process_name":names[str(e.get("pid"))]=e.get("args",{}).get("name","")
 cats=collections.Counter();phases=collections.Counter();complete={};markers=[];min_ts=None;max_end=None
 for e in events:
  phases[str(e.get("ph",""))]+=1;cats[str(e.get("cat",""))]+=1
  if e.get("ph")!="X":continue
  start,end=finite_span(e);min_ts=start if min_ts is None else min(min_ts,start);max_end=end if max_end is None else max(max_end,end)
  proc=names.get(str(e.get("pid")),"<unknown>");complete.setdefault(proc,collections.Counter())[str(e.get("name",""))]+=1
  name=str(e.get("name",""))
  if len(markers)<256 and any(x in name for x in("execute_context_","ProfilerStep","npu_fx_compiler inference","compile_fx","compile_inner")):
   markers.append({"name":name,"process":proc,"ts_us":start,"dur_us":end-start,"scope":"Observed annotation only; name is not compilation/phase proof."})
 flows=flow_summary(events)
 return {"trace_sha256":sha(path),"bytes":path.stat().st_size,"events":len(events),"process_names":names,"phase_counts":dict(phases),"category_counts":dict(cats),
 "complete_by_process":{k:{"count":sum(v.values()),"top_names":v.most_common(16)}for k,v in complete.items()},"annotation_samples":markers,
 "all_span_envelope_us":[min_ts,max_end],"flows":flows,"scope":"Schema and work-label orientation, not compute occupancy, critical path or removable wall time."}
def csv_layout(path):
 with path.open(newline="",encoding="utf-8-sig")as f:
  reader=csv.DictReader(f);headers=reader.fieldnames
  if not headers:raise ValueError("CSV header absent")
  count=0;samples=[];matmul_samples=[];types=collections.Counter()
  preferred=[k for k in headers if any(x in k.lower()for x in("shape","duration","type","name","stream","task","start","mac","memory","cube"))]
  type_key=next((k for k in headers if k.lower().replace(" ","").replace("_","")=="optype"),None)
  for row in reader:
   count+=1
   if count>2000000:raise ValueError("bounded CSV row count exceeded")
   if type_key:types[row.get(type_key,"")]+=1
   short={k:row.get(k)for k in preferred}
   if len(samples)<2:samples.append(short)
   if len(matmul_samples)<6 and any("matmul"in str(v).lower()for v in row.values()):matmul_samples.append(short)
 return {"sha256":sha(path),"bytes":path.stat().st_size,"headers":headers,"rows":count,"op_type_counts":dict(types),"first_rows":samples,"matmul_rows":matmul_samples,
 "scope":"Official CSV field/schema and representative geometry; not summed service work or a local speed claim."}
def check_report(group,row,acceptance,report):
 if acceptance.get("state")!="BOTH_COUNT2_ARMS_FULL_DIAGNOSTIC_GUARDS_TRACE_AND_RELEASE_VALID"or acceptance.get("arms",{}).get(group,{}).get("report")!=row:raise ValueError("accepted pair report binding required")
 if report.get("policy")!={"group":group,"algorithm_on":group=="G3","pdc_on":False}:raise ValueError("exact actual arm identity required")
 if not report.get("r44_diagnostic_transport_valid")or not report.get("live_release_verified")or not report.get("profiler",{}).get("four_rank_trace_valid")or report.get("r44_profiler",{}).get("max_iterations")!=2:raise ValueError("full count2 accepted diagnostic required")
def run(plan_path):
 plan_path=Path(plan_path).resolve();plan=json.loads(plan_path.read_bytes())
 if sha(__file__)!=plan["helper_sha256"]:raise ValueError("actual helper source drift")
 for field in("method","acceptance"):
  row=plan[field]
  if sha(row["path"])!=row["sha256"]:raise ValueError("frozen analysis input drift")
 acceptance=json.loads(Path(plan["acceptance"]["path"]).read_bytes())
 output=Path(plan["output_root"])
 if output.parent!=Path("/opt/host/vnf/cch-hypic-independent-20261028")or output.is_symlink()or output.exists():raise ValueError("new exact analysis root required")
 reports={};profiles={}
 for group,row in plan["reports"].items():
  path=Path(row["path"])
  if sha(path)!=row["sha256"]:raise ValueError("accepted report drift")
  report=json.loads(path.read_bytes())
  check_report(group,row,acceptance,report)
  if Path(plan["normalized_roots"][group])!=Path(report["r43_timestamp_normalization"]["normalized_root"]):raise ValueError("actual accepted normalization root required")
  reports[group]=report;profiles[group]=report["r44_profiler"]
 if set(reports)!={"G1","G3"}or profiles["G1"]!=profiles["G3"]or reports["G1"]["r44_host_source_sha256"]!=reports["G3"]["r44_host_source_sha256"]:raise ValueError("matched two-arm closure/profile required")
 output.mkdir();started=time.monotonic();rows={}
 for group,report in reports.items():
  norm=Path(plan["normalized_roots"][group]);parsed=Path(report["r43_offline_supplemental"]["parsed_root"])/"profiles";expected=report["r43_offline_supplemental"]["parsed_file_sha256"];ranks={}
  for rank,proof in report["profiler"]["ranks"].items():
   if time.monotonic()-started>plan["timeout_seconds"]:raise TimeoutError("bounded analysis elapsed ceiling")
   trace=norm/"profiles"/proof["trace"]
   if trace.is_symlink()or sha(trace)!=proof["trace_sha256"]:raise ValueError("exact accepted trace bytes required")
   row=trace_layout(trace);prefix=str(Path(proof["metadata"]).parent)+"/";csvs={}
   for name,digest in expected.items():
    if name.startswith(prefix)and name.endswith(".csv")and any(x in Path(name).name for x in("op_summary","kernel_details")):
     path=parsed/name
     if path.is_symlink()or sha(path)!=digest:raise ValueError("exact accepted official CSV required")
     csvs[name]=csv_layout(path)
   row["official_csv"]=csvs;row["worker_pid"]=proof["worker_pid"];ranks[rank]=row;gc.collect()
  rows[group]=ranks
 result={"schema":"hypic-r44-pair-layout/v1","helper_sha256":sha(__file__),"plan_sha256":sha(plan_path),"reports":plan["reports"],"ranks":rows,
 "elapsed_seconds":time.monotonic()-started,"no_devices":True,"new_inference":False,"critical_path_attributed":False,"new_performance_acceptance":False,"full_goal_complete":False}
 data=(json.dumps(result,sort_keys=True,allow_nan=False)+"\n").encode()
 with(output/"result.json").open("xb")as f:f.write(data);f.flush();os.fsync(f.fileno())
 print(json.dumps({"output":str(output/"result.json"),"sha256":sha(output/"result.json"),"ranks":{g:{k:{"events":v["events"],"csv_files":len(v["official_csv"])}for k,v in r.items()}for g,r in rows.items()},"no_speed_claim":True}))
if __name__=="__main__":
 parser=argparse.ArgumentParser();parser.add_argument("--plan",required=True);args=parser.parse_args()
 resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3));run(args.plan)

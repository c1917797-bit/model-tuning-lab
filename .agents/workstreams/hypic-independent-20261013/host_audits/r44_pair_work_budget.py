"""Read accepted R44 work and observed gaps; no inference or causal-removal claim."""
import argparse,collections,csv,gc,hashlib,json,os,re,resource,time
from decimal import Decimal,InvalidOperation
from pathlib import Path
from host_audits import r44_pair_layout as layout
D=Decimal
PARENT=Path("/opt/host/vnf/cch-hypic-independent-20261028")
def decimal(value):
 if isinstance(value,bool)or not isinstance(value,(str,int,float,Decimal)):raise ValueError("decimal scalar required")
 try:r=D(str(value).strip())
 except InvalidOperation:raise ValueError("invalid decimal")
 if not r.is_finite():raise ValueError("finite decimal required")
 return r
def span(start,duration):
 a=decimal(start);d=decimal(duration)
 if d<0:raise ValueError("negative duration")
 return a,a+d
def merge(rows):
 out=[]
 for a,b in sorted(rows):
  if not a.is_finite()or not b.is_finite()or b<a:raise ValueError("finite ordered interval")
  if out and a<=out[-1][1]:out[-1]=(out[-1][0],max(out[-1][1],b))
  else:out.append((a,b))
 return out
def length(rows):return sum((b-a for a,b in merge(rows)),D(0))
def intersection(left,right):
 a=merge(left);b=merge(right);i=j=0;total=D(0)
 while i<len(a)and j<len(b):
  total+=max(D(0),min(a[i][1],b[j][1])-max(a[i][0],b[j][0]))
  if a[i][1]<=b[j][1]:i+=1
  else:j+=1
 return total
def shapes(value):
 value=value.strip().strip('"')
 if not value:return []
 result=[]
 for item in value.split(";"):
  item=item.strip().strip("[]()")
  if not re.fullmatch(r"[0-9]+(?:\s*,\s*[0-9]+)*",item):return None
  dims=tuple(int(x.strip())for x in item.split(","))
  if any(x<=0 for x in dims):return None
  result.append(dims)
 return result
def matmul_flops(inputs,outputs):
 a=shapes(inputs);b=shapes(outputs)
 if a is None or b is None or len(a)!=2 or len(b)!=1 or any(len(x)!=2 for x in a+b):return None
 (m,k),rhs=a;(outm,n)=b[0]
 if m!=outm or rhs not in((n,k),(k,n)):return None
 return 2*m*n*k
def csv_work(path,origin):
 counts=collections.Counter();cores=collections.Counter();geometries=collections.Counter();flops=collections.Counter();unknown=collections.Counter();projections=[];rows=0;bounds=[]
 with path.open(newline="",encoding="utf-8-sig")as f:
  reader=csv.DictReader(f)
  required={"Type","Accelerator Core","Start Time(us)","Duration(us)","Input Shapes","Output Shapes","Input Data Types"}
  if not required.issubset(reader.fieldnames or []):raise ValueError("actual official CSV schema required")
  for row in reader:
   rows+=1
   if rows>2000000:raise ValueError("CSV ceiling")
   typ=row["Type"].strip();core=row["Accelerator Core"].strip()
   start,end=span(row["Start Time(us)"],row["Duration(us)"]);start-=origin;end-=origin;bounds.append((start,end))
   counts[typ]+=1;cores[core]+=1
   if "matmul" in typ.lower():
    key=(typ,row["Input Shapes"].strip(),row["Output Shapes"].strip(),row["Input Data Types"].strip(),core)
    geometries[key]+=1
    value=matmul_flops(key[1],key[2])
    if value is None:unknown[typ]+=1
    else:flops[typ]+=value
    ins=shapes(key[1]);outs=shapes(key[2])
    if ins and outs and len(ins)==2 and len(ins[0])==2 and ins[0][1]==5120 and ins[1]==(4096,5120) and outs==[(ins[0][0],4096)]:
     projections.append((start,end,ins[0][0],row.get("Stream ID","").strip(),row.get("Task ID","").strip()))
 geometries=[{"type":k[0],"input_shapes":k[1],"output_shapes":k[2],"input_dtype":k[3],"core":k[4],"calls":v,"flops_per_call":str(matmul_flops(k[1],k[2]))if matmul_flops(k[1],k[2])is not None else None}for k,v in sorted(geometries.items())]
 projection_groups=[]
 for a,b,m,stream,task in sorted(projections):
  if projection_groups and projection_groups[-1]["rows"]==m:
   projection_groups[-1]["calls"]+=1;projection_groups[-1]["last_end_us"]=str(b)
  else:projection_groups.append({"rows":m,"calls":1,"first_start_us":str(a),"last_end_us":str(b)})
 return {"csv_sha256":layout.sha(path),"rows":rows,"type_counts":dict(counts),"core_counts":dict(cores),"matmul_geometry":geometries,"validated_2d_matmul_flops_by_type":{k:str(v)for k,v in flops.items()},"unmodeled_matmul_calls":dict(unknown),"projection_chronological_runs":projection_groups,"csv_event_envelope_us":[str(min(a for a,b in bounds)),str(max(b for a,b in bounds))]if bounds else None,"scope":"Observed capture work only; FLOP geometry is not a service-time model. Projection runs are not proven forward boundaries."}
def trace_work(path):
 data=json.loads(path.read_bytes(),parse_float=D,parse_constant=lambda x:(_ for _ in()).throw(ValueError("nonfinite JSON")))
 events=layout.events_of(data);names={}
 for e in events:
  if e.get("ph")=="M"and e.get("name")=="process_name":names[str(e.get("pid"))]=e.get("args",{}).get("name","")
 allhw=[];control=[];otherhw=[];sync=[];comm=[];types=collections.Counter();sync_names=collections.Counter();annotations=[];hwcounts=collections.Counter()
 for e in events:
  if e.get("ph")!="X":continue
  a,b=span(e.get("ts"),e.get("dur"));name=str(e.get("name",""));proc=names.get(str(e.get("pid")),"<unknown>")
  if proc=="Ascend Hardware":
   allhw.append((a,b));hwcounts[name]+=1
   if any(t in name.upper()for t in("EVENT_WAIT","EVENT_RECORD","EVENT_RESET"))or name.upper() in("NOP","NPU::NOP"):
    control.append((a,b));types["event_control"]+=1
   else:
    otherhw.append((a,b));types["observed_non_control_hardware"]+=1
  elif proc=="CANN"and "synchronizestream"in name.lower():sync.append((a,b));sync_names[name]+=1
  elif proc=="Communication":comm.append((a,b))
  if len(annotations)<128 and any(x in name for x in("ProfilerStep","execute_context_","npu_fx_compiler inference","compile_fx","compile_inner")):
   annotations.append({"name":name,"process":proc,"start_us":str(a),"duration_us":str(b-a)})
 active=merge(otherhw);gaps=[(active[i][1],active[i+1][0])for i in range(len(active)-1)]
 horizon=active[-1][1]-active[0][0]if active else D(0)
 return {"trace_sha256":layout.sha(path),"events":len(events),"actual_process_names":names,"hardware_event_counts":dict(hwcounts),"classes":dict(types),"non_control_hardware_horizon_us":str(horizon),"non_control_hardware_union_us":str(length(active)),"observed_non_control_gaps_us":str(length(gaps)),"event_control_union_us":str(length(control)),"all_hardware_union_us":str(length(allhw)),"cann_stream_sync_calls":sum(sync_names.values()),"cann_stream_sync_names":dict(sync_names),"cann_stream_sync_union_us":str(length(sync)),"sync_coincident_with_observed_gaps_us":str(intersection(sync,gaps)),"communication_process_union_us_separate_not_additive":str(length(comm)),"largest_observed_gaps_us":[str(b-a)for a,b in sorted(gaps,key=lambda x:x[1]-x[0],reverse=True)[:12]],"annotations_not_compile_or_phase_proof":annotations,"flows":layout.flow_summary(events),"scope":"Per-rank observed unions, no across-rank sums. Non-control includes unclassified/memcpy/communication fragments; EVENT controls separate. Sync-gap overlap is coincidence, not removable cost or dependency proof."}
def run(plan_path):
 plan_path=Path(plan_path);plan=json.loads(plan_path.read_bytes())
 if layout.sha(__file__)!=plan["helper_sha256"]or layout.sha(layout.__file__)!=plan["layout_helper_sha256"]:raise ValueError("source binding")
 for field in("method","acceptance"):
  row=plan[field]
  if layout.sha(row["path"])!=row["sha256"]:raise ValueError("frozen method/pair drift")
 acceptance=json.loads(Path(plan["acceptance"]["path"]).read_bytes());reports={}
 for group,binding in plan["reports"].items():
  if layout.sha(binding["path"])!=binding["sha256"]:raise ValueError("report drift")
  r=json.loads(Path(binding["path"]).read_bytes());layout.check_report(group,binding,acceptance,r);reports[group]=r
 if set(reports)!={"G1","G3"}or reports["G1"]["r44_profiler"]!=reports["G3"]["r44_profiler"]or reports["G1"]["r44_host_source_sha256"]!=reports["G3"]["r44_host_source_sha256"]:raise ValueError("matched source/profile required")
 output=Path(plan["output_root"])
 if output.parent!=PARENT or output.is_symlink()or output.exists():raise ValueError("new exact root required")
 output.mkdir();started=time.monotonic();results={}
 for group,r in reports.items():
  norm=Path(r["r43_timestamp_normalization"]["normalized_root"]);origin=decimal(r["r43_timestamp_normalization"]["origin_us"])
  parsed=Path(r["r43_offline_supplemental"]["parsed_root"])/"profiles";expected=r["r43_offline_supplemental"]["parsed_file_sha256"];ranks={}
  for rank,proof in r["profiler"]["ranks"].items():
   if time.monotonic()-started>plan["timeout_seconds"]:raise TimeoutError("bounded analysis timeout")
   trace=norm/"profiles"/proof["trace"]
   if trace.is_symlink()or layout.sha(trace)!=proof["trace_sha256"]:raise ValueError("accepted trace drift")
   row=trace_work(trace);prefix=str(Path(proof["metadata"]).parent)+"/";csvs={}
   for name,digest in expected.items():
    if name.startswith(prefix)and Path(name).name=="kernel_details.csv":
     path=parsed/name
     if path.is_symlink()or layout.sha(path)!=digest:raise ValueError("CSV drift")
     csvs[name]=csv_work(path,origin)
   if len(csvs)!=1:raise ValueError("one actual official kernel table required")
   row["official_kernel_csv"]=csvs;row["worker_pid"]=proof["worker_pid"];ranks[rank]=row;gc.collect()
  results[group]=ranks
 result={"schema":"hypic-r44-observed-work-budget/v1","helper_sha256":layout.sha(__file__),"layout_helper_sha256":layout.sha(layout.__file__),"plan_sha256":layout.sha(plan_path),"reports":plan["reports"],"ranks":results,"elapsed_seconds":time.monotonic()-started,"no_devices":True,"new_inference":False,"actual_phase_equivalence_proven":False,"causal_removable_budget_proven":False,"service_speed_gain_proven":False,"full_goal_complete":False}
 with(output/"result.json").open("xb")as f:f.write((json.dumps(result,sort_keys=True,allow_nan=False)+"\n").encode());f.flush();os.fsync(f.fileno())
 print(json.dumps({"output":str(output/"result.json"),"sha256":layout.sha(output/"result.json"),"elapsed_seconds":result["elapsed_seconds"],"service_speed_gain_proven":False}))
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--plan",required=True);a=p.parse_args();resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3));run(a.plan)

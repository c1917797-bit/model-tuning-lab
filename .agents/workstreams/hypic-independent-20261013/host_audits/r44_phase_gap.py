"""Accepted-trace phase anchors and disjoint observed gap coverage; no speed claim."""
import argparse,collections,csv,gc,json,os,resource,time
from pathlib import Path
from decimal import Decimal as D
from host_audits import r44_pair_layout as layout
from host_audits import r44_pair_work_budget as work
PARENT=Path("/opt/host/vnf/cch-hypic-independent-20261028")
def gap_coverage(gaps,main_spans,gdn_spans,guard_spans,other_custom):
 events=[]
 for label,rows in enumerate((gaps,main_spans,gdn_spans,guard_spans,other_custom)):
  for a,b in work.merge(rows):
   if b>a:events.extend(((a,label,1),(b,label,-1)))
 state=[0]*5;last=None;totals=collections.defaultdict(lambda:D(0))
 for point,group,change in sorted(events):
  if last is not None and point>last and state[0]:
   if state[2]:label="gdn_with_nested_guard_op_span"if state[3]else"gdn_other_recorded_scope"
   elif state[4]:label="other_registered_custom_op"
   elif state[1]:label="other_recorded_main_thread_scope"
   else:label="no_recorded_main_thread_scope"
   totals[label]+=point-last
  state[group]+=change;last=point
 if any(state):raise ValueError("interval accounting not closed")
 if sum(totals.values(),D(0))!=work.length(gaps):raise ValueError("gap partition conservation")
 return {k:str(v)for k,v in totals.items()}
def hardware_key(event):
 a=event.get("args",{})
 for key in("Task Id","Physic Stream Id"):
  if type(a.get(key))not in(int,str):raise ValueError("exact hardware task/stream metadata")
 return(str(event["name"]),str(a["Task Id"]),str(a["Physic Stream Id"]),work.decimal(event["ts"]))
def csv_embedding(row,origin):
 out=work.shapes(row["Output Shapes"])
 if row["Type"]!="GatherV2"or not out or len(out)!=1 or len(out[0])!=2 or out[0][1]!=5120:raise ValueError("actual embedding geometry")
 return (row["Name"],row["Task ID"].strip(),row["Stream ID"].strip(),work.decimal(row["Start Time(us)"])-origin),out[0][0]
def forward_windows(embeddings,end):
 ordered=sorted(embeddings,key=lambda e:work.decimal(e["ts"]))
 if len(ordered)!=2:raise ValueError("exact observed count2 embedding anchors required")
 points=[work.decimal(e["ts"])for e in ordered]+[end]
 if not points[0]<points[1]<points[2]:raise ValueError("ordered nonempty anchored windows")
 return [(points[i],points[i+1])for i in range(2)]
def analyze(trace,csvpath,origin,pid):
 data=json.loads(trace.read_bytes(),parse_float=D,parse_constant=lambda x:(_ for _ in()).throw(ValueError("nonfinite JSON")))
 es=layout.events_of(data);names={str(e.get("pid")):e.get("args",{}).get("name","")for e in es if e.get("ph")=="M"and e.get("name")=="process_name"}
 main=[];gdn=[];guard=[];custom=[];active=[];emb=[];cpuemb=[];hwindex=collections.defaultdict(list);endpoints=collections.defaultdict(lambda:{"s":[],"t":[],"f":[]})
 guard_names={"aten::equal","aten::isfinite","aten::all","aten::item","aten::_local_scalar_dense"}
 for e in es:
  phase=e.get("ph")
  if phase in("s","t","f"):
   key=layout.flow_key(e)
   if key is not None:endpoints[key][phase].append(e)
  if phase!="X":continue
  a,b=work.span(e.get("ts"),e.get("dur"));n=str(e.get("name",""));proc=names.get(str(e.get("pid")),"<unknown>")
  if proc=="Python"and str(e.get("tid"))==str(pid):
   main.append((a,b))
   if n=="vllm::qwen_gdn_attention_core":gdn.append((a,b))
   elif n.startswith("vllm::"):custom.append((a,b))
   if n in guard_names:guard.append((a,b))
   if n=="aten::embedding":cpuemb.append(e)
  if proc=="Ascend Hardware":
   if not any(t in n.upper()for t in("EVENT_WAIT","EVENT_RECORD","EVENT_RESET"))and n.upper()!="NOP":active.append((a,b))
   if "Embedding" in n:
    emb.append(e);hwindex[hardware_key(e)].append(e)
 if len(cpuemb)!=2:raise ValueError("two actual main-thread embedding calls required")
 anchors=[]
 with csvpath.open(newline="",encoding="utf-8-sig")as f:
  for row in csv.DictReader(f):
   if row["Type"]!="GatherV2":continue
   key,rows=csv_embedding(row,origin);matches=hwindex[key]
   if len(matches)!=1:raise ValueError("unique exact embedding CSV/task/stream/start trace binding")
   e=matches[0];target=(str(e["pid"]),str(e["tid"]),work.decimal(e["ts"]));links=[]
   for k,ends in endpoints.items():
    relevant=[f for f in ends["f"]if(str(f.get("pid")),str(f.get("tid")),work.decimal(f.get("ts")))==target]
    if not relevant:continue
    links.append({"category":k[0],"name":k[1],"id_type":k[2],"id_string":k[3],"starts":len(ends["s"]),"ends":len(ends["f"]),"intermediate":len(ends["t"]),"start_points":[{"process":names.get(str(s.get("pid")),"<unknown>"),"pid":str(s.get("pid")),"tid":str(s.get("tid")),"ts_us":str(s.get("ts"))}for s in ends["s"]]})
   anchors.append({"rows":rows,"hardware_start_us":str(key[3]),"task_id":key[1],"stream_id":key[2],"incoming_exact_endpoint_flows":links,"flow_cardinality_not_forced":True})
 anchors.sort(key=lambda r:D(r["hardware_start_us"]))
 if len(anchors)!=2:raise ValueError("two complete unique official embedding rows required")
 active=work.merge(active);gaps=[(active[i][1],active[i+1][0])for i in range(len(active)-1)]
 windows=forward_windows(emb,active[-1][1]);phase_rows=[]
 for i,(a,b)in enumerate(windows):
  clipped=[(max(a,c),min(b,d))for c,d in gaps if c<b and d>a]
  phase_rows.append({"embedding_input_rows":anchors[i]["rows"],"device_anchor_window_us":[str(a),str(b)],"observed_noncontrol_gaps_us":str(work.length(clipped)),"gap_disjoint_main_thread_coverage_us":gap_coverage(clipped,main,gdn,guard,custom),"scope":"Device-anchor window, not a proven whole forward critical path. CPU overlap is temporal coverage, not causal removable time."})
 return {"trace_sha256":layout.sha(trace),"csv_sha256":layout.sha(csvpath),"embedding_anchors":anchors,"cpu_embedding_calls":[{"start_us":str(e["ts"]),"duration_us":str(e["dur"])}for e in sorted(cpuemb,key=lambda x:work.decimal(x["ts"]))],"gdn_registered_call_count":len(gdn),"other_registered_call_count":len(custom),"phases":phase_rows,"whole_capture_gap_disjoint_coverage_us":gap_coverage(gaps,main,gdn,guard,custom),"flow_cardinality":layout.flow_summary(es),"no_compile_or_graph_absence_inference":True}

def worker_steps(path,expected,rank,steps):
 if path.is_symlink()or layout.sha(path)!=expected:raise ValueError("accepted worker bytes drift")
 out={step:{"model":[],"first_progress":[],"request_layers":{}}for step in steps}
 with path.open()as f:
  for line in f:
   e=json.loads(line);step=e.get("step")
   if step not in out:continue
   if e.get("rank")!=rank:raise ValueError("actual rank differs")
   kind=e.get("event")
   if kind=="compact_model_rows_completed":out[step]["model"].append({k:e[k]for k in("rank","step","original_rows","retained_rows","request_ids")})
   if kind=="native_request_progress":out[step]["first_progress"].append({k:e[k]for k in("request_id","computed_tokens","scheduled_tokens")})
   if kind in("mixed_native_gdn_completed","compact_gdn_body_composed"):
    request=e["request_id"];row=out[step]["request_layers"].setdefault(request,{"kinds":set(),"retained_rows":set(),"layers":set()})
    row["kinds"].add(kind);row["retained_rows"].add(e["retained_rows"]);row["layers"].add(e["layer"])
 for step,row in out.items():
  if len(row["model"])!=1:raise ValueError("unique actual completed step required")
  model=row["model"][0];total=0
  if set(model["request_ids"])!=set(row["request_layers"]):raise ValueError("actual layer request coverage differs")
  for q,proof in row["request_layers"].items():
   if len(proof["retained_rows"])!=1 or len(proof["kinds"])!=1 or len(proof["layers"])!=48:raise ValueError("exact48 consistent actual C1 layers")
   retained=next(iter(proof["retained_rows"]));total+=retained
   row["request_layers"][q]={"kind":next(iter(proof["kinds"])),"retained_rows":retained,"actual_layers":48}
  if total!=model["retained_rows"]:raise ValueError("retained row conservation")
 return {"worker_sha256":expected,"selected_steps":out,"scope":"Fixed4preps+2actualwarm*1024 output steps place first measured selected step at2053. Per-layer receipts prove actual request row composition, not CPU/device timestamp synchronization."}

def run(plan_path):
 plan_path=Path(plan_path);plan=json.loads(plan_path.read_bytes())
 for p,digest in plan["helper_sources"].items():
  if layout.sha(p)!=digest:raise ValueError("analysis helper source drift")
 if layout.sha(__file__)!=plan["helper_sha256"]:raise ValueError("self binding")
 for key in("method","acceptance","work_budget"):
  row=plan[key]
  if layout.sha(row["path"])!=row["sha256"]:raise ValueError("frozen evidence/method drift")
 acceptance=json.loads(Path(plan["acceptance"]["path"]).read_bytes());reports={}
 for group,row in plan["reports"].items():
  if layout.sha(row["path"])!=row["sha256"]:raise ValueError("report drift")
  r=json.loads(Path(row["path"]).read_bytes());layout.check_report(group,row,acceptance,r);reports[group]=r
 if set(reports)!={"G1","G3"}or reports["G1"]["r44_host_source_sha256"]!=reports["G3"]["r44_host_source_sha256"]:raise ValueError("matched exact source")
 for path,digest in plan["runtime_source_sha256"].items():
  if layout.sha(path)!=digest:raise ValueError("frozen current runtime source drift")
 output=Path(plan["output_root"])
 if output.parent!=PARENT or output.is_symlink()or output.exists():raise ValueError("new exact CPU root")
 output.mkdir();began=time.monotonic();out={}
 for group,r in reports.items():
  norm=Path(r["r43_timestamp_normalization"]["normalized_root"])/"profiles";parsed=Path(r["r43_offline_supplemental"]["parsed_root"])/"profiles";expected=r["r43_offline_supplemental"]["parsed_file_sha256"];origin=work.decimal(r["r43_timestamp_normalization"]["origin_us"]);ranks={}
  for rank,proof in r["profiler"]["ranks"].items():
   if time.monotonic()-began>plan["timeout_seconds"]:raise TimeoutError("CPU budget")
   trace=norm/proof["trace"];relative=str(Path(proof["trace"]).parent/"kernel_details.csv");csvp=parsed/relative
   if trace.is_symlink()or csvp.is_symlink()or layout.sha(trace)!=proof["trace_sha256"]or layout.sha(csvp)!=expected[relative]:raise ValueError("bound accepted trace/CSV")
   ranks[rank]=analyze(trace,csvp,origin,proof["worker_pid"])
   if group=="G3":
    name="compact-worker-"+str(proof["worker_pid"])+".jsonl";worker=Path(plan["g3_worker_root"])/name
    ranks[rank]["actual_selected_worker_steps"]=worker_steps(worker,r["worker_sha256"][name],int(rank),plan["selected_steps"])
   gc.collect()
  out[group]=ranks
 result={"schema":"hypic-r44-phase-gap-anchors/v1","plan_sha256":layout.sha(plan_path),"helper_sha256":layout.sha(__file__),"reports":plan["reports"],"ranks":out,"elapsed_seconds":time.monotonic()-began,"no_devices":True,"new_inference":False,"causal_removal_proven":False,"service_gain_proven":False,"full_goal_complete":False}
 with(output/"result.json").open("xb")as f:f.write((json.dumps(result,sort_keys=True,allow_nan=False)+"\n").encode());f.flush();os.fsync(f.fileno())
 print(json.dumps({"path":str(output/"result.json"),"sha256":layout.sha(output/"result.json"),"elapsed_seconds":result["elapsed_seconds"]}))
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--plan",required=True);a=p.parse_args();resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3));run(a.plan)

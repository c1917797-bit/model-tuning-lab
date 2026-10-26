"""Fail-closed four-rank official Torch NPU trace closure; no speed attribution."""
import hashlib,json,math,re
from pathlib import Path
MAX_TOTAL=2*1024**3
MAX_TRACE=256*1024**2
def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb")as f:
  for b in iter(lambda:f.read(1024**2),b""):h.update(b)
 return h.hexdigest()
def inventory(root):
 root=Path(root)
 if not root.exists():return [],0
 if root.is_symlink():raise ValueError("profile root symlink")
 files=[];total=0
 for p in root.rglob("*"):
  if p.is_symlink():raise ValueError("profile symlink")
  if p.is_file():
   total+=p.stat().st_size;files.append(p)
   if total>MAX_TOTAL or len(files)>8192:raise ValueError("bounded profile storage exceeded")
 return files,total
def info_records(root):
 files,_=inventory(root);rows={}
 for p in files:
  if not re.fullmatch(r"profiler_info_[0-3]\.json",p.name):continue
  if p.stat().st_size>2*1024**2:raise ValueError("bounded profiler metadata exceeded")
  j=json.loads(p.read_bytes());rank=j.get("rank_id")
  if type(rank)is not int or rank not in range(4)or rank in rows:raise ValueError("unique real profiler rank required")
  rows[rank]=(p,j)
 return rows
def union(intervals):
 total=0.;end=None
 for a,b in sorted(intervals):
  if end is None or a>=end:total+=b-a;end=b
  elif b>end:total+=b-end;end=b
 return total
def trace_metrics(events):
 if not isinstance(events,list)or not events:raise ValueError("nonempty complete trace array required")
 names={e.get("pid"):e.get("args",{}).get("name","")for e in events if isinstance(e,dict)and e.get("ph")=="M"and e.get("name")=="process_name"}
 cp={p for p,n in names.items()if n=="Python"}
 hw={p for p,n in names.items()if"Ascend Hardware"in n or"AI Core"in n}
 if not cp or not hw:raise ValueError("actual Python and Ascend hardware trace processes required")
 intervals={"CPU":[],"NPU":[]};top={};shapes=0;flows=0
 for e in events:
  if not isinstance(e,dict):raise ValueError("trace event object required")
  if e.get("ph")in("s","f"):flows+=1
  if e.get("ph")!="X":continue
  a=e.get("ts");d=e.get("dur")
  if any(type(x)not in(int,float)or not math.isfinite(x)for x in(a,d))or d<0:
   raise ValueError("finite nonnegative complete event spans required")
  if d==0:continue
  k="CPU"if e.get("pid")in cp else"NPU"if e.get("pid")in hw else None
  if k:
   intervals[k].append((a,a+d));name=str(e.get("name",""))
   key=k+"::"+name;row=top.setdefault(key,[0,0.]);row[0]+=1;row[1]+=d
  if e.get("args",{}).get("Input Dims"):shapes+=1
 if not all(intervals.values()):raise ValueError("actual positive CPU and device events required")
 return {"events":len(events),"cpu_interval_union_us":union(intervals["CPU"]),"npu_interval_union_us":union(intervals["NPU"]),
  "flow_events":flows,"events_with_input_dims":shapes,
  "top_raw_duration_not_removable_time":[{"name":k,"calls":v[0],"sum_us":v[1]}for k,v in sorted(top.items(),key=lambda x:x[1][1],reverse=True)[:30]],
  "scope":"Per-rank trace interval unions and overlapping raw hotspot ranking only. No across-rank sum, causal removal or speed claim."}
def audit_tree(root,workers):
 root=Path(root);files,total=inventory(root);rows=info_records(root);expected={int(k):int(v)for k,v in workers.items()}
 if set(rows)!=set(range(4))or set(expected)!=set(range(4)):raise ValueError("all four profiler ranks required")
 result={}
 for rank,(p,j)in rows.items():
  m=re.search(r"_([0-9]+)_[0-9]{17}_ascend_pt$",p.parent.name)
  if not m or int(m[1])!=expected[rank]:raise ValueError("profiler directory PID differs from actual worker")
  acts=j.get("config",{}).get("common_config",{}).get("activities",[])
  if set(acts)!={"ProfilerActivity.CPU","ProfilerActivity.NPU"}:raise ValueError("CPU+NPU collection identity required")
  q=p.parent/"ASCEND_PROFILER_OUTPUT/trace_view.json"
  if not q.is_file()or q.is_symlink()or not 0<q.stat().st_size<=MAX_TRACE:raise ValueError("closed bounded parsed rank trace required")
  raw=json.loads(q.read_bytes());ev=raw.get("traceEvents")if isinstance(raw,dict)else raw
  result[str(rank)]={"worker_pid":expected[rank],"metadata":str(p.relative_to(root)),"metadata_sha256":sha(p),
    "trace":str(q.relative_to(root)),"trace_sha256":sha(q),"metrics":trace_metrics(ev)}
 return {"four_rank_trace_valid":True,"total_bytes":total,"files":len(files),"ranks":result,
  "source":"Original torch_npu parsed Text export, bounded all four source-bound ranks; exact device mapping separately audited.",
  "critical_path_attributed":False,"new_speed_acceptance":False}

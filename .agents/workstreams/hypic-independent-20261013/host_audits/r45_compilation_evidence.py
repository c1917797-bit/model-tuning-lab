"""Independent R45 event completeness and optimistic causal-budget bounds.

All clocks/IDs are exact Python integers. Native-call unions are upper bounds:
parent spans may contain nested observer writes; no inclusive or rank sums are
reported as removable service time. A sufficient bound is not a causal fix.
"""
import math,re
from decimal import Decimal,ROUND_FLOOR,ROUND_CEILING
PROFILE="source-pinned-triton-compile-v1"
PINS={"triton.runtime.jit":"8f170a849331e9ce75b0d2d05e0bcd6ad2f9de838bfb277e823617982d672aad",
 "triton.compiler.compiler":"4e432986cb567b94d282f9a2c2f9911a6c3718337289fa936f240282a6a5d54b"}
KINDS={"jit_cache_miss","compiler_api","binary_load"}
NEEDED_WEIGHTED_NS=621109004293  # ceil621.1090042927442 seconds; conservative admission threshold.
def exact_ns(value):
 if type(value)is not str or len(value)>24 or re.fullmatch(r"0|[1-9][0-9]*",value)is None:
  raise ValueError("canonical exact nonnegative integer clock string required")
 return int(value)
def intervals(rows):
 out=[]
 for a,b in sorted(rows):
  if type(a)is not int or type(b)is not int or a<0 or b<a:raise ValueError("ordered exact integer interval")
  if out and a<=out[-1][1]:out[-1]=(out[-1][0],max(out[-1][1],b))
  else:out.append((a,b))
 return out
def duration(rows):return sum(b-a for a,b in intervals(rows))
def intersection(a,b):
 left=intervals(a);right=intervals(b);i=j=0;out=[]
 while i<len(left)and j<len(right):
  lo=max(left[i][0],right[j][0]);hi=min(left[i][1],right[j][1])
  if hi>lo:out.append((lo,hi))
  if left[i][1]<right[j][1]:i+=1
  else:j+=1
 return intervals(out)
def _common(row,pid,manifest):
 if row.get("pid")!=pid or type(row.get("pid"))is not int or row.get("manifest_sha256")!=manifest:
  raise ValueError("actual worker PID/source manifest required")
def audit_worker(rows,*,pid,rank,manifest):
 if type(pid)is not int or type(rank)is not int or rank not in range(4):raise ValueError("actual TP4 worker mapping")
 starts={};ends={};stacks={};installed=0;health=[];frames=[];unknown=async_calls=0;started_count=completed=0
 for row in rows:
  event=row.get("event","")
  if not event.startswith("r45_compilation_"):continue
  _common(row,pid,manifest)
  if event=="r45_compilation_observer_installed":
   if starts or installed or row.get("profile")!=PROFILE or row.get("max_calls")!=512 or row.get("default_disabled")is not True or row.get("upstream_sources")!=PINS:
    raise ValueError("one exact default-off source-bound activation before calls")
   installed+=1;continue
  if installed!=1:raise ValueError("observation before exact activation")
  if event=="r45_compilation_health":
   values=[row.get(k)for k in("calls","completed","active","skipped_initialized_loads")]
   if any(type(v)is not int or v<0 for v in values)or row.get("profile")!=PROFILE or row.get("failed")is not False:
    raise ValueError("healthy exact bounded observer counters")
   calls,done,active,skipped=values
   if calls>started_count or done>completed or done+active!=calls or calls>512:
    raise ValueError("health snapshot counters differ from actual observed prefix")
   if health and any(a<b for a,b in zip((calls,done,skipped),health[-1])):
    raise ValueError("observer counters moved backwards")
   if type(row.get("rank"))is not int or row.get("rank")!=rank or type(row.get("step"))is not int or row["step"]<0:
    raise ValueError("health tied to actual completed worker step")
   health.append((calls,done,skipped));continue
  if event not in("r45_compilation_begin","r45_compilation_end"):raise ValueError("unknown R45 evidence event")
  ident=row.get("call_id");thread=row.get("thread_id");parent=row.get("parent_call_id");kind=row.get("kind")
  if type(ident)is not int or not 1<=ident<=512 or type(thread)is not str or re.fullmatch(r"[1-9][0-9]*",thread)is None or kind not in KINDS:
   raise ValueError("bounded exact call/thread/kind identity")
  assigned=row.get("rank")
  if assigned is not None and(type(assigned)is not int or assigned!=rank):raise ValueError("actual worker rank mismatch")
  if type(row.get("metadata"))is not dict:raise ValueError("explicit actual metadata required")
  stack=stacks.setdefault(thread,[])
  if event=="r45_compilation_begin":
   if ident!=started_count+1 or ident in starts:raise ValueError("no missing/duplicate begin IDs")
   if parent!=(stack[-1]if stack else None):raise ValueError("actual same-thread nested parent required")
   if any(starts[x]["kind"]==kind for x in stack)or len(stack)>=8:raise ValueError("recursive/nesting guard")
   exact_ns(row.get("wrapper_entry_ns"));starts[ident]=row;stack.append(ident);started_count+=1
  else:
   begin=starts.get(ident)
   if begin is None or ident in ends or not stack or stack[-1]!=ident:raise ValueError("no missing/duplicate/out-of-order end")
   for key in("parent_call_id","kind","rank","thread_id","pid","metadata","wrapper_entry_ns"):
    if row.get(key)!=begin.get(key):raise ValueError("begin/end identity or metadata differs")
   a=exact_ns(row.get("original_started_ns"));b=exact_ns(row.get("original_ended_ns"))
   entry=exact_ns(row["wrapper_entry_ns"]);probe=exact_ns(row.get("begin_probe_ns"))
   if not entry<=a<=b or exact_ns(row.get("original_duration_ns"))!=b-a or probe!=a-entry:
    raise ValueError("exact original interval and probe clock arithmetic")
   if row.get("failed")is not False or row.get("error_type")is not None or type(row.get("return_type"))is not str:
    raise ValueError("failed/incomplete original call is not accepted diagnostic")
   if parent is not None:
    # The native parent call starts after its begin receipt and before nested wrapper entry.
    parent_start=starts[parent]
    if entry<exact_ns(parent_start["wrapper_entry_ns"]):raise ValueError("nested clock moved backwards")
   meta=row["metadata"];async_flag=meta.get("async_compile_active",False)
   if type(async_flag)is not bool:raise ValueError("explicit async mode")
   unknown+=assigned is None or meta.get("unassociated")is True
   async_calls+=async_flag
   frames.append({"call_id":ident,"parent_call_id":parent,"kind":kind,"thread_id":thread,
    "rank":assigned,"wrapper_entry_ns":str(entry),"native_start_ns":str(a),"native_end_ns":str(b),"begin_probe_ns":str(probe),
    "kernel_name":meta.get("kernel_name"),"async_compile_active":async_flag,"metadata":meta})
   stack.pop();ends[ident]=row;completed+=1
 if installed!=1 or not health or any(stacks.values())or len(starts)!=len(ends)or started_count>512:
  raise ValueError("complete activation/calls/healthy completed-step evidence required")
 for frame in frames:
  parent=frame["parent_call_id"]
  if parent is not None:
   a=exact_ns(ends[parent]["original_started_ns"]);b=exact_ns(ends[parent]["original_ended_ns"])
   if not a<=exact_ns(frame["native_start_ns"])<=exact_ns(frame["native_end_ns"])<=b:
    raise ValueError("child outside actual native parent interval")
 by_thread={}
 for frame in sorted(frames,key=lambda x:x["call_id"]):
  if frame["parent_call_id"]is None:
   tid=frame["thread_id"];entry=exact_ns(frame["wrapper_entry_ns"])
   if entry<by_thread.get(tid,0):raise ValueError("same-thread native call clock moved backwards")
   by_thread[tid]=exact_ns(frame["native_end_ns"])
  else:
   if exact_ns(frame["wrapper_entry_ns"])<exact_ns(ends[frame["parent_call_id"]]["original_started_ns"]):
    raise ValueError("child wrapper entered before native parent")
 unions={kind:intervals([(exact_ns(f["native_start_ns"]),exact_ns(f["native_end_ns"]))for f in frames if f["kind"]==kind])for kind in KINDS}
 all_union=intervals([row for value in unions.values()for row in value])
 return {"pid":pid,"rank":rank,"calls":started_count,"completed":completed,"health_snapshots":len(health),
  "unassigned_or_unassociated_calls":unknown,"async_jit_misses":async_calls,"frames":frames,
  "native_call_union_ns":str(duration(all_union)),"per_kind_union_ns":{k:str(duration(v))for k,v in unions.items()},
  "intervals":all_union,"scope":"Deduplicated native-call observation upper bounds. Not exclusive removable blocking or performance."}
def outward_float_ns(value,*,upper):
 if type(value)not in(int,float)or not math.isfinite(value)or value<0:raise ValueError("finite original request clock")
 exact=Decimal(value)if type(value)is int else Decimal.from_float(value)
 uncertainty=Decimal(0)if type(value)is int else Decimal.from_float(math.ulp(value))
 scaled=(exact+(uncertainty if upper else-uncertainty))*Decimal(10**9)
 return max(0,int(scaled.to_integral_value(rounding=ROUND_CEILING if upper else ROUND_FLOOR)))
def request_intervals(results):
 if type(results)is not list or len(results)!=40:raise ValueError("same actual full40 response denominator")
 decode=[];whole=[];seen=set()
 for row in results:
  m=row.get("metrics",{});ident=m.get("request_id")
  if row.get("ok")is not True or type(ident)is not str or not ident or ident in seen:raise ValueError("40 actual unique successful requests")
  seen.add(ident);a=m.get("started");b=m.get("first_content");c=m.get("ended")
  if any(type(v)not in(int,float)or not math.isfinite(v)for v in(a,b,c))or not 0<=a<=b<=c:raise ValueError("actual ordered first/last token clocks")
  whole.append((outward_float_ns(a,upper=False),outward_float_ns(c,upper=True)))
  decode.append((ident,outward_float_ns(b,upper=False),outward_float_ns(c,upper=True)))
 return intervals(whole),decode
def budget(worker_reports,results,*,shared_monotonic_clock_proven=False):
 if type(worker_reports)is not list or len(worker_reports)!=4 or{r["rank"]for r in worker_reports}!=set(range(4)):
  raise ValueError("four accepted physical worker reports")
 if shared_monotonic_clock_proven is not True:
  return {"clock_binding_valid":False,"causal_budget_valid":False,"allow_kernel_rewrite":False,
   "reason":"Shared CLOCK_MONOTONIC namespace/source proof absent; separate per-rank upper bounds only, no rank sum or invented token overlap."}
 measured,decode=request_intervals(results)
 global_union=intervals([pair for report in worker_reports for pair in report["intervals"]])
 overlap=intersection(global_union,measured)
 weighted=sum(duration(intersection(overlap,[(a,b)]))for ident,a,b in decode)
 optimistic16=duration(overlap)*16
 upper=min(weighted,optimistic16)
 sufficient=upper>=NEEDED_WEIGHTED_NS
 return {"clock_binding_valid":True,"observed_native_call_measured_union_ns":str(duration(overlap)),
  "actual_request_decode_overlap_upper_weighted_ns":str(weighted),"optimistic16_upper_weighted_ns":str(optimistic16),
  "upper_weighted_ns":str(upper),"necessary_recovery_weighted_ns":str(NEEDED_WEIGHTED_NS),
  "insufficient_even_with_observation_overhead":not sufficient,"allow_kernel_rewrite":False,
  "causal_budget_valid":False,
  "decision":"INSUFFICIENT_OPTIMISTIC_COMPILATION_BUDGET"if not sufficient else"EXCLUSIVE_SOURCE_BLOCKING_AND_PROBE_COST_STILL_REQUIRED",
  "scope":"Upper bound includes any unknown native waits/nested observation writes and async/unassigned intervals. It can reject this route, never establish a causal repair or service gain."}

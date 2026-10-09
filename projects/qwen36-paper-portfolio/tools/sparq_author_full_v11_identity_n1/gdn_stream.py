"""Independent all-row GDN logical-byte checker and joint ordinary-RAM plan.
Stdlib at import. Runtime NumPy only accelerates the SAME exact IEEE exponent
scan; no NPU operation, candidate math or free-running dense-state equality.
Complete raw before stays CPU-resident. Every after row is streamed once.
This is a NEW live-check protocol, not historical permanent-rawdump authority.
"""
import hashlib,json,struct,sys
import evidence as c
PROTOCOL="sparq.GDN-all-row-live-byte-finite/v2"
BUDGET="sparq.GDN-four-rank-real-shape-budget/v1"
GUEST=64*1024**3
RESERVE=2*1024**3

MEMORY="sparq.actual-owned-memory-leaf/v1"
MEMORY_KEYS={1:("memory.limit_in_bytes","memory.usage_in_bytes","memory.max_usage_in_bytes"),
 2:("memory.max","memory.current","memory.peak")}
def _memory_path(value):
 from pathlib import PurePosixPath
 c.require(type(value) is str and value.startswith("/") and "\\" not in value and
  (value=="/" or all(p not in ("",".","..") for p in value[1:].split("/"))),
  "absolute normalized memory namespace path")
 return PurePosixPath(value)
def _mount_field(value):
 import re
 c.require(re.search(r"\\(?!040|011|012|134)",value) is None,"valid mountinfo escaped field")
 return re.sub(r"\\(040|011|012|134)",lambda m:chr(int(m[1],8)),value)
def memory_layout(proc_cgroup,mountinfo):
 """Guest leaf only. Host admission still proves every ancestor separately."""
 c.require(type(proc_cgroup) is str and proc_cgroup and type(mountinfo) is str and mountinfo,
  "actual complete process cgroup and mountinfo")
 memory=[];unified=[]
 for line in proc_cgroup.splitlines():
  words=line.split(":",2)
  c.require(len(words)==3 and words[0].isdigit(),"complete proc cgroup row")
  controllers=words[1].split(",") if words[1] else []
  c.require(len(set(controllers))==len(controllers),"unique cgroup controller row")
  if "memory" in controllers:memory.append(words[2])
  if words[:2]==["0",""]:unified.append(words[2])
 c.require(len(memory)<=1 and len(unified)<=1,"unique actual memory hierarchy")
 version=1 if memory else 2;groups=memory if memory else unified
 c.require(len(groups)==1,"actual v1 memory or unified v2 controller present")
 group=_memory_path(groups[0]);found=[]
 for line in mountinfo.splitlines():
  fields=line.split(" - ")
  c.require(len(fields)==2,"complete mountinfo row")
  left=fields[0].split();right=fields[1].split()
  c.require(len(left)>=6 and len(right)==3,"complete mountinfo fields")
  if (version==1 and right[0]=="cgroup" and "memory" in right[2].split(",")) or (version==2 and right[0]=="cgroup2"):
   root=_memory_path(_mount_field(left[3]));point=_memory_path(_mount_field(left[4]))
   c.require(point==_memory_path("/sys/fs/cgroup") or _memory_path("/sys/fs/cgroup") in point.parents,
    "actual cgroup namespace mountpoint, not arbitrary file fallback")
   c.require(group==root or root in group.parents,"process memory group lies inside actual mount root")
   leaf=point/group.relative_to(root)
   found.append(dict(version=version,cgroup=str(group),mount_root=str(root),mount_point=str(point),
    path=str(leaf),mount_line=line,mount_options=left[5],super_options=right[2],
    full_host_ancestors_observed=False))
 c.require(len(found)==1,"exact one actual memory mount; no root fallback or ambiguous controller")
 return found[0]
def _memory_process(stat,pid):
 c.require(type(stat) is str and stat.startswith(str(pid)+" (") and ")" in stat,"actual process stat")
 tail=stat[stat.rfind(")")+2:].split()
 c.require(len(tail)>=20 and tail[19].isdigit() and int(tail[19])>0 and tail[0] not in ("Z","X","x"),
  "live self PID/start identity during memory read")
 return dict(pid=pid,start_ticks=int(tail[19]))
def _memory_identity(value,directory=False):
 import stat
 c.require(type(value) is dict and set(value)=={"device","inode","mode"} and
  all(type(value[k]) is int for k in value) and value["device"]>=0 and value["inode"]>0 and
  (stat.S_ISDIR(value["mode"]) if directory else stat.S_ISREG(value["mode"])),
  "actual non-symlink cgroup leaf/control inode identity")
 return value
def _memory_number(raw):
 import re
 c.require(type(raw) is str and re.fullmatch("[0-9]+",raw.strip()) is not None,
  "finite decimal memory controller value; missing/unlimited is not capacity")
 return int(raw.strip())
def consume_memory(value,expected_limit=GUEST,container_id=None,namespace_pid=None):
 import re
 c.require(type(value) is dict,"actual owned memory leaf must be a dictionary")
 if value.get("schema")==MEMORY_SAMPLE:value=_expand_memory_sample(value)
 c.require(type(expected_limit) is int and expected_limit in (8*1024**3,GUEST),
  "only registered CPU8GiB or model64GiB profile; default model unchanged")
 c.require(type(value) is dict and value["schema"]==MEMORY and type(value["process"]["pid"]) is int and
  value["process"]["pid"]>0,"actual owned memory leaf schema/PID")
 pid=value["process"]["pid"]
 before=_memory_process(value["stat_before"],pid);after=_memory_process(value["stat_after"],pid)
 c.require(before==after==value["process"] and value["proc_cgroup"]==value["proc_cgroup_after"] and
  value["mountinfo_raw"]==value["mountinfo_after"],"stable actual PID/start/cgroup/mountinfo memory extent")
 layout=memory_layout(value["proc_cgroup"],value["mountinfo_raw"])
 c.require(type(value["version"]) is int and value["full_host_ancestors_observed"] is False and
  all(value[k]==v for k,v in layout.items()) and value["expected_limit_bytes"]==expected_limit,
  "independently resolved namespace leaf and unchanged registered cap")
 names=MEMORY_KEYS[layout["version"]];wanted={str(__import__("pathlib").PurePosixPath(layout["path"])/n) for n in names}
 c.require(set(value["control_raw"])==set(value["file_identities"])==set(value["file_identities_after"])==wanted,
  "exact three original memory control files and inode identities")
 c.require(value["leaf_identity"]==value["leaf_identity_after"],"actual memory leaf inode changed")
 _memory_identity(value["leaf_identity"],True)
 for path in wanted:
  c.require(value["file_identities"][path]==value["file_identities_after"][path],"actual memory control inode changed")
  _memory_identity(value["file_identities"][path])
 numbers=[]
 for n in names:
  raw=value["control_raw"][str(__import__("pathlib").PurePosixPath(layout["path"])/n)]
  numbers.append(_memory_number(raw))
 c.require(value["limit_raw_after"]==value["control_raw"][str(__import__("pathlib").PurePosixPath(layout["path"])/names[0])],
  "actual memory limit changed during sample")
 maximum,current,peak=numbers
 c.require(maximum==expected_limit and 0<=current<=maximum and peak>=current,
  "actual exact owned memory cap and sane usage/peak; no unlimited host fallback")
 c.require(all(type(value[k]) is int for k in ("memory_max","memory_current","memory_peak")) and
  (value["memory_max"],value["memory_current"],value["memory_peak"])==tuple(numbers),
  "claimed memory numbers must equal original control bytes")
 if container_id is not None:
  c.require(type(container_id) is str and re.fullmatch("[0-9a-f]{64}",container_id) is not None and
   container_id in __import__("pathlib").PurePosixPath(layout["cgroup"]).parts,
   "actual leaf belongs to exact owned full CID")
 if namespace_pid is not None:c.require(pid==namespace_pid,"same actual CPU/N1 namespace process")
 return value
def _read_memory_text(path):
 from pathlib import Path
 return Path(path).read_text()
def _read_memory_identity(path,directory=False):
 import os
 row=os.stat(path,follow_symlinks=False)
 return _memory_identity(dict(device=row.st_dev,inode=row.st_ino,mode=row.st_mode),directory)
def memory(expected_limit=GUEST):
 """No framework/device import. Namespace leaf is NOT full-host ancestor proof."""
 import os
 from pathlib import PurePosixPath
 pid=os.getpid();stat_before=_read_memory_text("/proc/self/stat")
 raw=_read_memory_text("/proc/self/cgroup");mountinfo=_read_memory_text("/proc/self/mountinfo")
 layout=memory_layout(raw,mountinfo);names=MEMORY_KEYS[layout["version"]];controls={};ids={}
 leaf=_read_memory_identity(layout["path"],True)
 for n in names:
  path=str(PurePosixPath(layout["path"])/n);ids[path]=_read_memory_identity(path);controls[path]=_read_memory_text(path)
 after_ids={path:_read_memory_identity(path) for path in ids}
 limit_after=_read_memory_text(str(PurePosixPath(layout["path"])/names[0]))
 result=dict(schema=MEMORY,**layout,process=_memory_process(stat_before,pid),
  stat_before=stat_before,stat_after=_read_memory_text("/proc/self/stat"),
  proc_cgroup=raw,proc_cgroup_after=_read_memory_text("/proc/self/cgroup"),
  mountinfo_raw=mountinfo,mountinfo_after=_read_memory_text("/proc/self/mountinfo"),
  control_raw=controls,file_identities=ids,file_identities_after=after_ids,
  leaf_identity=leaf,leaf_identity_after=_read_memory_identity(layout["path"],True),
  limit_raw_after=limit_after,expected_limit_bytes=expected_limit,
  memory_max=_memory_number(controls[str(PurePosixPath(layout["path"])/names[0])]),
  memory_current=_memory_number(controls[str(PurePosixPath(layout["path"])/names[1])]),
  memory_peak=_memory_number(controls[str(PurePosixPath(layout["path"])/names[2])]))
 return consume_memory(result,expected_limit)

MEMORY_SAMPLE="sparq.actual-owned-memory-leaf-sample/v1"
MEMORY_DYNAMIC=("process","stat_before","stat_after","control_raw","file_identities","file_identities_after",
 "leaf_identity","leaf_identity_after","limit_raw_after","expected_limit_bytes","memory_max","memory_current","memory_peak")
def _memory_digest(text):return hashlib.sha256(text.encode()).hexdigest()
def _expand_memory_sample(value):
 proof=c.obj(value["namespace_proof"])
 c.require(proof["schema"]=="sparq.actual-preweight-memory/v1" and proof["model_allocation_not_started"] is True,
  "actual immutable preweight namespace proof, not a per-token guessed mount")
 base=proof["memory"];consume_memory(base)
 for k in ("proc_cgroup","proc_cgroup_after","mountinfo_raw","mountinfo_after"):
  c.require(value[k+"_sha256"]==_memory_digest(base[k]),"same namespace raw bytes at current sample; no hidden drift")
 expanded=dict(base)
 for k in MEMORY_DYNAMIC:expanded[k]=value[k]
 c.require(value["process"]==base["process"],"sample stays in same actual preweight worker PID/start")
 return expanded
def memory_sample(value,namespace_ref):
 # Keep raw mountinfo only in immutable per-process startup, not four new
 # copies in every token/epoch budget record. Usage and peak are always fresh.
 consume_memory(value);proof=c.obj(namespace_ref);base=proof["memory"];consume_memory(base)
 c.require(all(value[k]==base[k] for k in memory_layout(value["proc_cgroup"],value["mountinfo_raw"])) and
  value["process"]==base["process"] and value["leaf_identity"]==base["leaf_identity"] and
  value["file_identities"]==base["file_identities"],"actual leaf must match source-bound startup before compact publication")
 result=dict(schema=MEMORY_SAMPLE,namespace_proof=namespace_ref)
 for k in MEMORY_DYNAMIC:result[k]=value[k]
 for k in ("proc_cgroup","proc_cgroup_after","mountinfo_raw","mountinfo_after"):result[k+"_sha256"]=_memory_digest(value[k])
 _expand_memory_sample(result)
 return result

CHUNK=1024**2
FINITE_TEMP=CHUNK+CHUNK//2
def natural(identity):
 shape=identity["shape"];dtype=identity["dtype"]
 c.require(type(shape) is list and len(shape)>=2 and all(type(n) is int and n>0 for n in shape)
  and dtype in ("torch.bfloat16","torch.float32"),"complete actual initialized native logical shape/dtype")
 return __import__("math").prod(shape[1:])*(2 if dtype=="torch.bfloat16" else 4)
def plan(records,baseline,epoch,source,max_model_len):
 c.require(type(baseline) is int and baseline>0 and type(epoch) is int and epoch>0 and
  type(max_model_len) is int and max_model_len==40960,"actual shared guest baseline/epoch/current full-model logical bound")
 c.require(type(records) is list and len(records)==4 and {r["rank"] for r in records}==set(range(4)),
  "one actual pre-allocation plan from each of all4 ranks")
 before=0;rows=[];peak=[];states=0;leaf=None;pids=set()
 for r in sorted(records,key=lambda x:x["rank"]):
  c.require(type(r["rank"]) is int and type(r["epoch"]) is int and r["schema"]==BUDGET and r["epoch"]==epoch and r["source"]==source and
   type(r["cgroup"]["memory_current"]) is int and r["cgroup"]["memory_current"]>0 and
   type(r["cgroup"]["memory_max"]) is int and r["cgroup"]["memory_max"]==GUEST and r["max_model_len"]==max_model_len,
   "same actual source/epoch/shared64GiB guest, never separate stale rank budgets")
  identity=consume_memory(r["cgroup"])
  if r["cgroup"]["schema"]==MEMORY_SAMPLE:
   c.require(c.obj(r["cgroup"]["namespace_proof"])["source"]==source,"same actual source preweight namespace proof")
  key=tuple(identity[k] for k in ("version","cgroup","path","mount_root","mount_point"))+(tuple(sorted(identity["leaf_identity"].items())),)
  if leaf is None:leaf=key
  c.require(key==leaf and identity["process"]["pid"] not in pids,"all4 distinct actual workers share ONE exact memory leaf")
  pids.add(identity["process"]["pid"])
  c.require(type(r["states"]) is list and len(r["states"])==96 and
   {(s["layer"],s["name"]) for s in r["states"]}==
    {(i,n) for i in range(64) if i%4!=3 for n in ("conv","recurrent")},
   "both true initialized native states of each of all48 GDN layers")
  amount=0;largest=0
  for s in r["states"]:
   unit=natural(s["identity"]);count=s["identity"]["shape"][0]
   amount+=unit*count;largest=max(largest,unit);states+=1
  before+=amount;rows.append(dict(rank=r["rank"],before_bytes=amount,max_row_bytes=largest))
  peak.append(r["cgroup"]["memory_current"])
 # Independent FP64/literal diagnostic executes one request/layer at a time on
 # each rank. Bound eight full FP64 K/V-sized arrays + sixteen six-head arrays;
 # source diagnostics must reject a future allocation exceeding this contract.
 oracle_per_rank=max_model_len*(8*256*8+16*6*8)+16*1024**2
 temporary=sum(2*r["max_row_bytes"]+FINITE_TEMP for r in rows)
 oracle=4*oracle_per_rank;upper=max([baseline]+peak)+before+temporary+oracle+RESERVE
 c.require(upper<=GUEST,"joint baseline+ALL original-before+all4 row/finite temporaries+oracle+reserve <=64GiB")
 return dict(schema=BUDGET,epoch=epoch,source=source,ranks=rows,records=records,all_initialized_states=states,
  actual_baseline_bytes=max([baseline]+peak),all_before_bytes=before,after_copy_and_finite_temp_bytes=temporary,
  full_FA_oracle_reserved_bytes=oracle,reserve_bytes=RESERVE,planned_upper_bytes=upper,guest_limit_bytes=GUEST,
  blind_limit_allocation=False,planned_before_dump_bytes=0,first_bad_row_raw_reserved_bytes=2*sum(r["max_row_bytes"] for r in rows),
  readiness=False)
def consume_budget(p):
 got=plan(p["records"],p["actual_baseline_bytes"],p["epoch"],p["source"],40960)
 c.require(got==p,"entire actual joint allocation proof independently re-derived")
 return got
def view(data):
 m=memoryview(data)
 c.require(m.contiguous,"complete contiguous CPU logical row, not allocator padding")
 return m.cast("B") # Always flatten; len(multidimensional uint8 view) is NOT nbytes.
def finite(data,dtype,np=None):
 c.require(sys.byteorder=="little","actual source image IEEE little-endian CPU bytes")
 raw=view(data);width=2 if dtype=="torch.bfloat16" else 4
 c.require(dtype in ("torch.bfloat16","torch.float32") and len(raw)%width==0,"exact original dtype/full logical row size")
 mask=0x7f80 if width==2 else 0x7f800000
 for offset in range(0,len(raw),CHUNK):
  block=raw[offset:offset+CHUNK]
  if np is None:
   for j,(word,) in enumerate(struct.iter_unpack("<H" if width==2 else "<I",block)):
    if word&mask==mask:return dict(finite=False,element=(offset//width)+j,bits=word)
  else:
   words=np.frombuffer(block,dtype="<u2" if width==2 else "<u4")
   marked=np.bitwise_and(words,mask);flags=np.equal(marked,mask)
   if bool(flags.any()):
    j=int(flags.argmax());return dict(finite=False,element=(offset//width)+j,bits=int(words[j]))
 return dict(finite=True,elements=len(raw)//width)
class FirstRowError(ValueError):
 def __init__(self,why,record):super().__init__(why);self.record=record
class Checker:
 def __init__(self,identity,written,np=None):
  self.identity=identity;self.unit=natural(identity);self.count=identity["shape"][0]
  c.require(type(written) is list and written==sorted(set(written)) and
   all(type(i) is int and 0<=i<self.count for i in written),"actual original writer slots")
  self.written=written;self.np=np;self.next=0;self.active_changed=[];self.before=hashlib.sha256();self.after=hashlib.sha256()
  self.finite_elements=0
 def row(self,slot,before,after):
  c.require(slot==self.next and type(slot) is int,"complete ordered row sequence, no sampling/duplicate")
  a=view(before);b=view(after)
  c.require(len(a)==len(b)==self.unit,"entire original before/after logical row")
  changed=(a!=b);f=finite(b,self.identity["dtype"],self.np)
  record=dict(slot=slot,written=slot in self.written,bitwise_changed=changed,finite=f,
   before_sha256=hashlib.sha256(a).hexdigest(),after_sha256=hashlib.sha256(b).hexdigest(),row_bytes=self.unit)
  if not f["finite"]:raise FirstRowError("actual GDN nonfinite active/inactive full-row after",record)
  if slot not in self.written and changed:raise FirstRowError("actual inactive native GDN row changed",record)
  if changed:self.active_changed.append(slot)
  # Prefix explicit slot/length: concatenation cannot hide reorder or missing rows.
  prefix=struct.pack("<QQ",slot,self.unit);self.before.update(prefix);self.before.update(a);self.after.update(prefix);self.after.update(b)
  self.finite_elements+=f["elements"];self.next+=1
  return record
 def finish(self):
  c.require(self.next==self.count,"all original active AND inactive rows completely observed")
  return dict(protocol=PROTOCOL,total_slots=self.count,row_bytes=self.unit,written_slots=self.written,
   inactive_slots=[i for i in range(self.count) if i not in self.written],active_changed_slots=self.active_changed,
   rows_checked=self.next,logical_before_bytes=self.next*self.unit,logical_after_bytes=self.next*self.unit,
   finite_elements_checked=self.finite_elements,all_after_finite=True,all_inactive_exact=True,
   original_before_stream_sha256=self.before.hexdigest(),original_after_stream_sha256=self.after.hexdigest(),
   first_exception=None,active_changed_is_observation_not_gate=True,active_dense_equality_not_claimed=True,
   permanent_success_after_dump=False,independent_live_checker=True,model_ready=False)
def consume_summary(summary,identity,written):
 unit=natural(identity);number=identity["shape"][0];s=summary
 c.require(s["protocol"]==PROTOCOL and s["total_slots"]==s["rows_checked"]==number and s["row_bytes"]==unit and
  s["written_slots"]==written and s["inactive_slots"]==[i for i in range(number) if i not in written] and
  s["logical_before_bytes"]==s["logical_after_bytes"]==number*unit and
  s["finite_elements_checked"]==number*unit//(2 if identity["dtype"]=="torch.bfloat16" else 4),
  "whole live-check coverage/dtype/byte counts and actual reconstructed writer domain")
 c.require(s["all_after_finite"] is s["all_inactive_exact"] is s["independent_live_checker"] is True and
  s["first_exception"] is None and s["active_changed_is_observation_not_gate"] is True and
  s["active_dense_equality_not_claimed"] is True and s["permanent_success_after_dump"] is False and s["model_ready"] is False,
  "new full-row live-check protocol, not historical rawdump/dense equivalence PASS")
 for k in ("original_before_stream_sha256","original_after_stream_sha256"):
  c.require(__import__("re").fullmatch("[a-f0-9]{64}",s[k] or "") is not None,"complete ordered actual byte stream digest")
 changes=s["active_changed_slots"]
 c.require(type(changes) is list and changes==sorted(set(changes)) and set(changes)<=set(written),
  "every changed row was an actual active writer, inactive exact preserved")
 return dict(protocol=PROTOCOL,all_rows=number,all_after_finite=True,all_inactive_exact=True,
  written_slots=written,inactive_slots=s["inactive_slots"],active_changed_slots=changes,
  all_logical_bytes_compared=True,live_byte_source=summary,postmortem_success_bytes_replay_claimed=False,
  active_state_dense_equivalence_not_claimed=True,model_ready=False)

def validate_probe(probe,files):
 g=probe["GDN_stream_checker"]
 c.require(g["protocol"]==PROTOCOL and g["source"]["sha256"]==files["gdn_stream.py"] and
  g["state_arithmetic_executed"] is False and g["actual_initialized_shape_and_joint_budget_pending"] is True,
  "actual same-image CPU new-checker source dependency; no synthetic state/model proof")
 c.bound(g["source"]["path"],g["source"]["sha256"])
 np=g["numpy"];p=np["file"]["path"]
 c.require(type(np["version"]) is str and np["version"] and
  __import__("pathlib").Path(p).is_absolute() and ".." not in __import__("pathlib").Path(p).parts and p.endswith(".py") and
  __import__("re").fullmatch("[a-f0-9]{64}",np["file"]["sha256"] or "") is not None,
  "actual immutable660 image NumPy module observed in CPU source closure; no host nonexistent path dereference")
 return g

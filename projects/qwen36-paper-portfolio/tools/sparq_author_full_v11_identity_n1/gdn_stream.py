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
 c.require(g["protocol"]==PHYSICAL_PROTOCOL and g["source"]["sha256"]==files["gdn_stream.py"] and
  g["state_arithmetic_executed"] is False and g["actual_initialized_shape_and_joint_budget_pending"] is True,
  "actual same-image CPU new-checker source dependency; no synthetic state/model proof")
 c.bound(g["source"]["path"],g["source"]["sha256"])
 np=g["numpy"];p=np["file"]["path"]
 c.require(type(np["version"]) is str and np["version"] and
  __import__("pathlib").Path(p).is_absolute() and ".." not in __import__("pathlib").Path(p).parts and p.endswith(".py") and
  __import__("re").fullmatch("[a-f0-9]{64}",np["file"]["sha256"] or "") is not None,
  "actual immutable660 image NumPy module observed in CPU source closure; no host nonexistent path dereference")
 return g
# REFERENCE_OR_TEST successor: raw shared-pool ownership, not per-layer
# inactive semantics. Historical v2 helpers above remain historical only.
PHYSICAL_PROTOCOL="sparq.GDN-shared-physical-pool-byte-reference/v3"
PHYSICAL_BUDGET="sparq.GDN-four-rank-physical-pool-budget/v2"
ALLOCATOR_PINS={
 "/vllm-workspace/vllm/vllm/v1/worker/gpu_model_runner.py":"6250ca0670c4593aa2f7c4567c9c71d6cb3d8182624a985d4d4e33d5bf054666",
 "/vllm-workspace/vllm-ascend/vllm_ascend/worker/model_runner_v1.py":"94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968",
 "/vllm-workspace/vllm-ascend/vllm_ascend/attention/attention_v1.py":"80005aba42bcf61247cc0d91502a0f1338194a4b38dd82bc521f6d3c84958390"}
def writer_sources(raw):
 c.require(raw.get("allocator_source_pins")==ALLOCATOR_PINS,
  "same installed original allocator/request/cache writer source, not producer flags")
IDENTITY_FIELDS=("shape","stride","dtype","device","pointer","storage_pointer",
 "storage_offset","storage_bytes","native_format_value","native_format_type")
def physical_identity(x):
 c.require(type(x) is dict and all(k in x for k in IDENTITY_FIELDS),"complete actual byte-view identity")
 shape=x["shape"];stride=x["stride"];width=2 if x["dtype"]=="torch.bfloat16" else 4
 c.require(x["dtype"] in ("torch.bfloat16","torch.float32") and type(shape) is list and
  len(shape)>=2 and type(stride) is list and len(stride)==len(shape) and
  all(type(v) is int and v>0 for v in shape+stride),"original supported typed shape/stride")
 product=1;inner=[]
 for n in reversed(shape[1:]):inner.insert(0,product);product*=n
 c.require(stride[1:]==inner and stride[0]>=product,"source original contiguous inner row with exact outer gap")
 c.require(all(type(x[k]) is int for k in ("pointer","storage_pointer","storage_offset","storage_bytes","native_format_value")) and
  x["pointer"]>0 and x["storage_pointer"]>0 and x["storage_offset"]>=0 and
  x["storage_bytes"]>0 and x["storage_bytes"]%width==0 and
  x["pointer"]==x["storage_pointer"]+x["storage_offset"]*width and
  (x["storage_offset"]+(shape[0]-1)*stride[0]+product)*width<=x["storage_bytes"],
  "actual pointer/offset/storage extent, never same-storage alias guess")
 c.require(type(x["device"]) is str and __import__("re").fullmatch(r"npu:[0-9]+",x["device"]) is not None and
  x["native_format_value"]==2 and x["native_format_type"]=="torch_npu.npu._format.Format",
  "actual ND byte-addressable Ascend view; unsupported layout fails closed")
 return dict(width=width,row_bytes=product*width,rows=shape[0])
def _checked_identity(x,cache=None):
 c.require(type(x) is dict and all(k in x for k in IDENTITY_FIELDS),"complete actual byte-view identity")
 encoded=json.dumps({k:x[k] for k in IDENTITY_FIELDS},sort_keys=True,separators=(",",":"),allow_nan=False)
 if cache is not None and encoded in cache:return cache[encoded]
 result=(physical_identity(x),hashlib.sha256(encoded.encode()).hexdigest())
 if cache is not None:cache[encoded]=result
 return result
def exact_view_key(x):return _checked_identity(x)[1]
def slab_key(x):
 physical_identity(x)
 return (x["device"],x["storage_pointer"],x["storage_bytes"],x["native_format_value"],x["native_format_type"])
def _validated_row_extent(x,info,slot):
 c.require(type(slot) is int and 0<=slot<info["rows"],"actual typed state slot extent")
 start=(x["storage_offset"]+slot*x["stride"][0])*info["width"]
 return [start,start+info["row_bytes"]]
def row_extent(x,slot):return _validated_row_extent(x,physical_identity(x),slot)
def _validated_view_extents(x,info):
 # Exact complete typed view only. Contiguous rows have no intervening bytes;
 # padded outer strides retain EVERY gap, never a bounding-box exemption.
 start=x["storage_offset"]*info["width"];step=x["stride"][0]*info["width"]
 if step==info["row_bytes"]:return [[start,start+info["rows"]*step]]
 return [[start+i*step,start+i*step+info["row_bytes"]] for i in range(info["rows"])]
def full_view_extents(x):return _validated_view_extents(x,physical_identity(x))
def normalize_extents(rows,size):
 c.require(type(size) is int and size>0 and type(rows) is list,"finite complete physical slab")
 rows=sorted(rows)
 result=[]
 for r in rows:
  c.require(type(r) is list and len(r)==2 and all(type(v) is int for v in r) and
   0<=r[0]<r[1]<=size,"source-derived physical byte interval inside owned slab")
  if result and r[0]<=result[-1][1]:result[-1][1]=max(result[-1][1],r[1])
  else:result.append(list(r))
 return result
def intersections(a,b):
 out=[];i=j=0
 while i<len(a) and j<len(b):
  lo=max(a[i][0],b[j][0]);hi=min(a[i][1],b[j][1])
  if lo<hi:out.append([lo,hi])
  if a[i][1]<=b[j][1]:i+=1
  else:j+=1
 return out
def complement(rows,size):
 rows=normalize_extents(rows,size);out=[];start=0
 for a,b in rows:
  if start<a:out.append([start,a])
  start=b
 if start<size:out.append([start,size])
 return out
def fa_write_extents(identity,raw):return _validated_fa_write_extents(identity,raw,physical_identity(identity))
def _validated_fa_write_extents(identity,raw,info):
 """Original attention_v1.py1439-1453 real slot_mapping[:actual].
 Exact ND stride proves byte-offset=storage_offset*2+slot*512.
 EVERY actual slot is validated; sort only merges adjacent complete tokens.
 """
 writer_sources(raw)
 c.require(identity["dtype"]=="torch.bfloat16" and len(identity["shape"])==4 and
  identity["shape"][1:]==[128,1,256] and identity["stride"]==[32768,256,256,1],
  "source-qualified ordinary BF16 CP1 kernel128 FA writer view")
 c.require(type(raw) is dict and raw["schema"]=="sparq.actual-native-FA-writer-metadata/v1" and
  raw["cache_write_scope"]=="original-reshape-and-cache-real-token-slice" and
  raw["is_encoder_decoder"] is False and raw["cache_sharing_target"] is None and
  raw["CP"] is False and raw["quantized"] is False,"actual unchanged ordinary native FA writer branch")
 impl=raw["actual_implementation"]
 c.require(impl["class"]=="vllm_ascend.attention.attention_v1.AscendAttentionBackendImpl" and
  impl["attn_type"]==impl["decoder_value"]=="AttentionType.DECODER" and type(impl["impl_id"]) is int and impl["impl_id"]>0 and
  impl["enable_c8_quant"] is impl["enable_hamming_sparse"] is impl["is_kv_producer"] is False and
  impl["kv_sharing_target_layer_name"] is None,"actual captured ordinary decoder implementation fields")
 n=raw["num_actual_tokens"];slots=raw["slot_mapping"]
 c.require(type(n) is int and n>0 and type(slots) is list and len(slots)==n and
  all(type(v) is int and -1<=v<identity["shape"][0]*128 for v in slots),
  "complete actual real-token native slot mapping, not lengths/table claims")
 ordered=sorted(v for v in slots if v>=0)
 c.require(all(ordered[i-1]!=ordered[i] for i in range(1,len(ordered))),"no actual native FA writer collision")
 rows=[];base=identity["storage_offset"]*info["width"]
 for slot in ordered:
  start=base+slot*512
  if rows and start==rows[-1][1]:rows[-1][1]=start+512
  else:rows.append([start,start+512])
 return rows

def _minus(parts,cuts):
 out=[]
 for a,b in parts:
  pos=a
  for lo,hi in cuts:
   if hi<=pos or lo>=b:continue
   if pos<lo:out.append([pos,min(lo,b)])
   pos=max(pos,hi)
   if pos>=b:break
  if pos<b:out.append([pos,b])
 return out
def physical_owners(states,fa,raw_loader=c.obj):
 """All96 logical states and all16 FA writers; exact complete alias only."""
 import gdn_metadata
 c.require(type(states) is list and len(states)==96 and
  {(s["layer"],s["name"]) for s in states}=={(i,n) for i in range(64) if i%4!=3 for n in ("conv","recurrent")} and
  len({s["rank"] for s in states})==len({s["epoch"] for s in states})==1,
  "all48 logical layers/both96 states in one real rank and epoch")
 c.require(type(fa) is list and len(fa)==16 and {s["layer"] for s in fa}==set(range(3,64,4)),
  "all16 actual FA metadata: no missing overlay writer")
 pools={};pairs={};identity_cache={}
 def checked(x):
  info,vk=_checked_identity(x,identity_cache)
  key=(x["device"],x["storage_pointer"],x["storage_bytes"],x["native_format_value"],x["native_format_type"])
  return info,vk,key
 for s in states:pairs.setdefault(s["layer"],{})[s["name"]]=s
 for layer,pair in pairs.items():
  a,b=pair["conv"],pair["recurrent"];raw=raw_loader(a["metadata"])
  c.require(a["metadata"]==b["metadata"] and raw["prefix"]==a["prefix"]==b["prefix"] and
   raw["epoch"]==a["epoch"]==b["epoch"] and raw["rank"]==a["rank"]==b["rank"],
   "actual metadata belongs to each exact logical state")
  domain=gdn_metadata.plan(raw,a["identity"]["shape"][0],b["identity"]["shape"][0])
  for name,s in pair.items():
   x=s["identity"];info,vk,key=checked(x)
   c.require(x["device"]=="npu:"+str(s["rank"]),"no cross-rank pointer alias")
   p=pools.setdefault(key,dict(identity={k:x[k] for k in ("device","storage_pointer","storage_bytes","native_format_value","native_format_type")},
    members=[],views={},operations=[]))
   if vk not in p["views"]:
    extent=_validated_view_extents(x,info)
    c.require(all(not intersections(extent,v["extents"]) for v in p["views"].values()),
     "GDN views must be exact whole aliases or disjoint; partial overlap rejected")
    p["views"][vk]=dict(identity=x,extents=extent,members=[])
   member=dict(layer=layer,name=name,prefix=s["prefix"],metadata=s["metadata"],view=vk)
   p["members"].append(member);p["views"][vk]["members"].append(member)
   writes=domain["written_slots"][name]
   p["operations"].append(dict(layer=layer,kind="GDN",dtype=x["dtype"],view=vk,
    metadata=s["metadata"],name=name,slots=writes,extents=[_validated_row_extent(x,info,i) for i in writes]))
 for row in fa:
  c.require(row["rank"]==states[0]["rank"] and row["epoch"]==states[0]["epoch"],
   "same actual FA/GDN turn and rank")
  raw=raw_loader(row["metadata"]);writer_sources(raw)
  c.require(raw["layer"]==row["layer"] and raw["prefix"]==row["prefix"] and raw["rank"]==row["rank"] and
   raw["epoch"]==row["epoch"] and len(row["cache"])==2,"both actual original K/V identities and metadata")
  k,v=row["cache"];ki,kv,kk=checked(k);vi,vv,vk=checked(v)
  c.require(kk==vk and not intersections(_validated_view_extents(k,ki),_validated_view_extents(v,vi)),
   "complete disjoint native K/V views in original shared slab")
  for index,(x,info,key) in enumerate(((k,ki,kk),(v,vi,vk))):
   c.require(x["device"]=="npu:"+str(row["rank"]) and key in pools,
    "actual all64 initialized FA and GDN physical slab, not foreign cache")
   pools[key]["operations"].append(dict(layer=row["layer"],kind="FA",dtype="torch.bfloat16",
    metadata=row["metadata"],cache_index=index,extents=_validated_fa_write_extents(x,raw,info)))
 for p in pools.values():
  size=p["identity"]["storage_bytes"]
  p["operations"].sort(key=lambda x:(x["layer"],x.get("name",""),x.get("cache_index",-1)))
  p["allowed_write_extents"]=normalize_extents([r for op in p["operations"] for r in op["extents"]],size)
  p["protected_extents"]=complement(p["allowed_write_extents"],size)
  p["all_physical_bytes"]=size;p["protected_bytes"]=sum(b-a for a,b in p["protected_extents"])
  p["before_owner"]=hashlib.sha256(json.dumps(p["identity"],sort_keys=True,separators=(",",":")).encode()).hexdigest()
  p["exact_views"]=list(p["views"].values());del p["views"]
 return sorted(pools.values(),key=lambda x:(x["identity"]["device"],x["identity"]["storage_pointer"]))
def type_segments(pool,prior):
 """Last observed native writer byte type, not cached-request ownership.
 Original raw zeros initialize storage, but we never assign prehistory a
 GDN type. Every real model turn is observed; dummy writes confer no request
 ownership. FA writes remove ONLY their exact bytes, never a complete row.
 """
 size=pool["all_physical_bytes"];out=[]
 for r in prior:
  c.require(set(r)=={"start","stop","dtype","view","layer"} and
   r["dtype"] in ("torch.bfloat16","torch.float32") and
   any(exact_view_key(v["identity"])==r["view"] for v in pool["exact_views"]) and
   r["layer"] in [m["layer"] for m in pool["members"]],"prior typed history same original exact pool/logical metadata")
  width=2 if r["dtype"]=="torch.bfloat16" else 4
  c.require(0<=r["start"]<r["stop"]<=size and r["start"]%width==r["stop"]%width==0,
   "entire original typed element boundary; no FA reinterpret")
  c.require(not intersections([[r["start"],r["stop"]]],[[t["start"],t["stop"]] for t in out]),
   "nonoverlapping prior last-writer types")
  out.append(dict(r))
 for op in pool["operations"]:
  cuts=normalize_extents(op["extents"],size);kept=[]
  for old in out:
   for a,b in _minus([[old["start"],old["stop"]]],cuts):kept.append(dict(old,start=a,stop=b))
  c.require(all(r["start"]%(2 if r["dtype"]=="torch.bfloat16" else 4)==
   r["stop"]%(2 if r["dtype"]=="torch.bfloat16" else 4)==0 for r in kept),
   "unsupported FA/GDN overlap cuts a retained typed element")
  out=kept
  if op["kind"]=="GDN":
   for a,b in cuts:out.append(dict(start=a,stop=b,dtype=op["dtype"],view=op["view"],layer=op["layer"]))
 return sorted(out,key=lambda x:(x["start"],x["stop"]))
def typed_ledger(pools,previous,rank,epoch,source):
 c.require(type(previous) is dict and previous.get("schema")=="sparq.actual-pool-last-writer-types/v1" and
  previous.get("rank")==rank and previous.get("epoch")==epoch-1 and previous.get("source")==source,
  "exact prior real model epoch/source/rank; no unexplained typed prehistory")
 old={p["before_owner"]:p for p in previous["pools"]}
 if epoch==1:c.require(not old,"first observed real request has no guessed retained typed state")
 else:c.require(set(old)=={p["before_owner"] for p in pools},"same immutable original physical owners across real epochs")
 return dict(schema="sparq.actual-pool-last-writer-types/v1",rank=rank,epoch=epoch,source=source,
  pools=[dict(before_owner=p["before_owner"],identity=p["identity"],segments=type_segments(p,old.get(p["before_owner"],{}).get("segments",[])))
   for p in pools],allocator_retirement_not_claimed=True)
def _object_bytes(value,seen=None):
 # Actual CPython metadata heap, shared references counted once. The
 # source-accounting multiplier covers concurrent original+derived trees,
 # JSON publication/parse and current consumer history, NOT a kernel limit.
 seen=set() if seen is None else seen
 if id(value) in seen:return 0
 seen.add(id(value));size=sys.getsizeof(value)
 if type(value) is dict:return size+sum(_object_bytes(k,seen)+_object_bytes(v,seen) for k,v in value.items())
 if type(value) in (list,tuple):return size+sum(_object_bytes(v,seen) for v in value)
 return size
METADATA_HEAP_BOUND="json-occurrence-conservative-heap-upper/v1"
def _metadata_heap_upper(value,active=None):
 # Fixed source accounting, deliberately NO alias credit/sys.getsizeof.
 # Bounds JSON-built CPython3.10/3.12 containers and scalars conservatively;
 # this is not a measured peak or an OS allocator/kernel hard bound.
 # Every repeated occurrence is charged, independent of JSON key interning.
 active=set() if active is None else active
 kind=type(value)
 if value is None or kind is bool:return 64
 if kind is str:return 128+4*len(value)
 if kind is int:return 128+8*((abs(value).bit_length()+29)//30)
 if kind is float:
  c.require(__import__("math").isfinite(value),"finite budget metadata scalar");return 128
 c.require(kind in (dict,list,tuple),"budget metadata must be JSON-built")
 token=id(value);c.require(token not in active,"cyclic budget metadata rejected")
 active.add(token)
 try:
  if kind is dict:
   c.require(all(type(k) is str for k in value),"JSON budget metadata string keys")
   return 512+512*len(value)+sum(_metadata_heap_upper(k,active)+_metadata_heap_upper(v,active) for k,v in value.items())
  return 256+32*len(value)+sum(_metadata_heap_upper(v,active) for v in value)
 finally:active.remove(token)
def physical_budget(records,baseline_refs,epoch,source,max_model_len=40960,raw_loader=c.obj):
 c.require(type(records) is list and len(records)==4 and {r["rank"] for r in records}==set(range(4)) and
  len(baseline_refs)==4 and max_model_len==40960,"all4 real plans/fresh baselines, original full model domain")
 leaf=None;pids=set();allpools=[];baseline=[];largest=0
 for r,br in zip(sorted(records,key=lambda x:x["rank"]),baseline_refs):
  c.require(r["schema"]==PHYSICAL_BUDGET and r["epoch"]==epoch and r["source"]==source and
   r["max_model_len"]==max_model_len and r["original_cpu_before_allocated"] is False,
   "source-bound all4 before-allocation physical plans")
  m=consume_memory(raw_loader(br));prior=consume_memory(r["cgroup"])
  c.require(m["process"]==prior["process"] and m["memory_max"]==GUEST,
   "fresh baseline same worker PID/start/exact64GiB")
  k=tuple(m[v] for v in ("version","cgroup","path","mount_root","mount_point"))+(tuple(sorted(m["leaf_identity"].items())),)
  if leaf is None:leaf=k
  c.require(k==leaf and m["process"]["pid"] not in pids,"all4 distinct workers same actual64GiB leaf")
  if r["cgroup"]["schema"]==MEMORY_SAMPLE:
   c.require(raw_loader(r["cgroup"]["namespace_proof"])["source"]==source,"same actual preweight source")
  pids.add(m["process"]["pid"]);baseline.append(m["memory_current"])
  pools=physical_owners(r["states"],r["fa"],raw_loader)
  largest=max(largest,max(natural(v["identity"]) for p in pools for v in p["exact_views"]))
  allpools.append(dict(rank=r["rank"],pools=pools))
 before=sum(p["all_physical_bytes"] for row in allpools for p in row["pools"])
 # Cross-process deterministic conservative metadata accounting. Preserve
 # ALL original8heap/4wire/all4 terms; no Python-object-alias savings.
 # Source constructs fresh JSON-built records/views, never shrunk containers.
 heap=_metadata_heap_upper(records)+_metadata_heap_upper(allpools)
 wire=sum(len(json.dumps(v,sort_keys=True,separators=(",",":"),allow_nan=False).encode()) for v in (records,allpools))
 metadata=8*heap+4*wire
 temp=4*(metadata+4*CHUNK+4*largest+FINITE_TEMP)
 oracle=4*(max_model_len*(8*256*8+16*6*8)+16*1024**2)
 upper=max(baseline)+before+temp+oracle+RESERVE
 return dict(schema=PHYSICAL_BUDGET,epoch=epoch,source=source,records=records,baseline_refs=baseline_refs,
  pools=allpools,actual_baseline_bytes=max(baseline),all_physical_before_bytes=before,
  physical_copy_count=sum(len(r["pools"]) for r in allpools),all_logical_state_count=384,
  metadata_heap_bytes_per_worker=heap,metadata_wire_bytes_per_worker=wire,
  metadata_heap_copy_multiplier=8,metadata_wire_buffer_multiplier=4,
  metadata_heap_bound_formula=METADATA_HEAP_BOUND,metadata_heap_is_conservative_fixed_bound=True,
  all4_metadata_transient_reserved_bytes=4*metadata,temporary_accounting_not_measured_peak=True,
  after_chunk_and_typed_temp_bytes=temp,full_FA_oracle_reserved_bytes=oracle,reserve_bytes=RESERVE,
  planned_upper_bytes=upper,guest_limit_bytes=GUEST,budget_fits=upper<=GUEST,ready=False)
def consume_physical_budget(proof,raw_loader=c.obj):
 got=physical_budget(proof["records"],proof["baseline_refs"],proof["epoch"],proof["source"],raw_loader=raw_loader)
 c.require(got==proof,"independent complete raw metadata physical owners/budget replay")
 c.require(proof["budget_fits"] is True and proof["planned_upper_bytes"]<=GUEST,
  "same64GiB full physical before+oracle+all4 transients+2GiB reserve")
 return proof
class PhysicalChecker:
 """One complete ordered before/after stream; no full-row write exemption."""
 def __init__(self,pool,segments,np=None):
  self.pool=pool;self.np=np;self.next=0;self.before=hashlib.sha256();self.after=hashlib.sha256()
  self.segments=segments;self.typed_bytes=[0]*len(segments);self.protected_bytes=0
 def chunk(self,offset,before,after):
  a=view(before);b=view(after);size=self.pool["all_physical_bytes"]
  c.require(type(offset) is int and offset==self.next and 0<len(a)==len(b)<=CHUNK and offset+len(a)<=size,
   "entire original physical slab including padding exactly once in order")
  end=offset+len(a)
  for start,stop in self.pool["protected_extents"]:
   lo=max(start,offset);hi=min(stop,end)
   if lo<hi:
    c.require(a[lo-offset:hi-offset]==b[lo-offset:hi-offset],
     "actual unwritten byte changed; partial written row is not exempt")
    self.protected_bytes+=hi-lo
  for i,r in enumerate(self.segments):
   lo=max(r["start"],offset);hi=min(r["stop"],end)
   if lo<hi:
    got=finite(b[lo-offset:hi-offset],r["dtype"],self.np)
    c.require(got["finite"] is True,"actual last-GDN-writer typed bytes nonfinite, excluding exact FA writes only")
    self.typed_bytes[i]+=hi-lo
  self.before.update(a);self.after.update(b);self.next=end
 def finish(self):
  c.require(self.next==self.pool["all_physical_bytes"] and self.protected_bytes==self.pool["protected_bytes"] and
   self.typed_bytes==[r["stop"]-r["start"] for r in self.segments],
   "complete pool/padding protection and every source-derived typed segment")
  return dict(schema=PHYSICAL_PROTOCOL,before_owner=self.pool["before_owner"],physical_bytes_checked=self.next,
   protected_bytes_checked=self.protected_bytes,all_unwritten_bytes_exact=True,
   typed_segments_sha256=hashlib.sha256(json.dumps(self.segments,sort_keys=True,separators=(",",":")).encode()).hexdigest(),typed_bytes_checked=sum(self.typed_bytes),
   original_before_stream_sha256=self.before.hexdigest(),original_after_stream_sha256=self.after.hexdigest(),
   FA_bytes_not_FP32_reinterpreted=True,old_per_layer_inactive_gate_not_claimed=True,
   allocator_retirement_not_claimed=True,model_ready=False)
def consume_physical_summary(s,pool,segments):
 c.require(s["schema"]==PHYSICAL_PROTOCOL and s["before_owner"]==pool["before_owner"] and
  s["physical_bytes_checked"]==pool["all_physical_bytes"] and s["protected_bytes_checked"]==pool["protected_bytes"] and
  s["typed_segments_sha256"]==hashlib.sha256(json.dumps(segments,sort_keys=True,separators=(",",":")).encode()).hexdigest() and s["typed_bytes_checked"]==sum(r["stop"]-r["start"] for r in segments) and
  all(s[k] is True for k in ("all_unwritten_bytes_exact","FA_bytes_not_FP32_reinterpreted",
   "old_per_layer_inactive_gate_not_claimed","allocator_retirement_not_claimed")) and s["model_ready"] is False,
  "new exact physical oracle scope; old per-layer inactive/allocator retirement never promoted")
 for k in ("original_before_stream_sha256","original_after_stream_sha256"):
  c.require(__import__("re").fullmatch("[a-f0-9]{64}",s[k] or "") is not None,"full ordered physical stream SHA")
 return s

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
 before=0;rows=[];peak=[];states=0
 for r in sorted(records,key=lambda x:x["rank"]):
  c.require(type(r["rank"]) is int and type(r["epoch"]) is int and r["schema"]==BUDGET and r["epoch"]==epoch and r["source"]==source and
   type(r["cgroup"]["memory_current"]) is int and r["cgroup"]["memory_current"]>0 and
   type(r["cgroup"]["memory_max"]) is int and r["cgroup"]["memory_max"]==GUEST and r["max_model_len"]==max_model_len,
   "same actual source/epoch/shared64GiB guest, never separate stale rank budgets")
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

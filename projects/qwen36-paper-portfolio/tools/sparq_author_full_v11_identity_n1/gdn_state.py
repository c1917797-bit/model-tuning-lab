"""Independent complete inactive native GDN state-byte consumer, stdlib.
Active candidate GDN states are NOT compared with dense free-running states.
Reads actual writer metadata; never trusts producer's written-slot boolean.
"""
import math
from pathlib import Path
import evidence as c
import gdn_metadata,gdn_stream
GDN=tuple(i for i in range(64) if i%4!=3)
def slot_bytes(ref,want):
 c.require(set(ref)=={"path","sha256","size_bytes"} and ref["size_bytes"]==want,"entire actual state-slot byte Ref")
 p=Path(c.bound(ref["path"],ref["sha256"])["path"])
 c.require(p.stat().st_size==want,"exact whole state-slot logical bytes")
 return p
def same(a,b):
 with a.open("rb") as x,b.open("rb") as y:
  while True:
   left=x.read(1024**2);right=y.read(1024**2)
   if left!=right:return False
   if not left:return True
def identity(x):
 shape=x["shape"];stride=x["stride"]
 c.require(type(shape) is list and len(shape)>=2 and all(type(v) is int and v>0 for v in shape) and
  type(stride) is list and len(stride)==len(shape) and all(type(v) is int and v>0 for v in stride) and
  x["dtype"] in ("torch.bfloat16","torch.float32") and x["device"].startswith("npu:") and
  type(x["pointer"]) is int and x["pointer"]>0 and type(x["storage_pointer"]) is int and x["storage_pointer"]>0,
  "actual native original state allocation identity")
 # Source mamba_utils explicitly allows padded outer page stride. Preserve exact
 # stride/format identity; do not impose ND2 or contiguous whole-state fiction.
 natural=math.prod(shape[1:]);inner=list(stride[1:]);expect=[];product=1
 for n in reversed(shape[1:]):expect.insert(0,product);product*=n
 c.require(inner==expect and stride[0]>=natural and x["storage_offset"]>=0 and
  x["storage_bytes"]>=(x["storage_offset"]+(shape[0]-1)*stride[0]+natural)*(2 if x["dtype"]=="torch.bfloat16" else 4),
  "source-supported nonoverlapping contiguous logical row with padded native page stride")
 return natural*(2 if x["dtype"]=="torch.bfloat16" else 4)
def consume_historical_raw(event,pinned_state_sources):
 c.require(event["layer"] in GDN and event["prefix"] and event["original_forward_core_unchanged"] is True
  and event["original_forward_unchanged"] is True and event["deployed_state_sources"]==pinned_state_sources,
  "original donor/receiver source identity; no sparse patched GDN math")
 raw=c.obj(event["actual_metadata_before"])
 c.require(raw["prefix"]==event["prefix"] and raw["epoch"]==event["epoch"] and raw["rank"]==event["rank"] and
  raw["device_snapshot_copied_outside_GLOBAL_capture"] is True,"whole actual metadata epoch/prefix/rank")
 states=event["states"];c.require(type(states) is list and len(states)==2 and
  [s["name"] for s in states]==["conv","recurrent"],"both native GDN state tensors")
 domain=gdn_metadata.plan(raw,*[s["identity_before"]["shape"][0] for s in states]);checked=[]
 for state in states:
  ident=state["identity_before"];unit=identity(ident)
  c.require(ident==state["identity_after"] and state["state_slot_axis"]==0,"same entire native backing before/after model")
  number=ident["shape"][0];writes=domain["written_slots"][state["name"]]
  inactive=set(range(number))-set(writes);rows=state["untouched_slots"]
  c.require(type(rows) is list and len(rows)==len(inactive) and
   {r["slot"] for r in rows}==inactive,"every unused/paused/foreign/zero-length native slot, no sampling")
  for row in rows:
   c.require(type(row["slot"]) is int,"actual physical state slot")
   c.require(same(slot_bytes(row["before"],unit),slot_bytes(row["after"],unit)),
    "untouched GDN state changed at layer/slot "+str((event["layer"],row["slot"])))
  checked.append(dict(name=state["name"],total_slots=number,written_slots=writes,all_untouched_slots=sorted(inactive),
   state_slot_bytes=unit,all_logical_bytes_compared=True,untouched_slots_identical=True,identity=ident,
   allocator_page_gap_bytes_not_claimed=True))
 return dict(schema="sparq.actual-GDN-untouched-state-check/v1",layer=event["layer"],prefix=event["prefix"],
  rank=event["rank"],epoch=event["epoch"],states=checked,writer_domain=domain,passed=True,
  active_state_dense_equivalence_not_claimed=True,model_ready=False)

def consume(event,pinned_state_sources,checker_ref=None,expected_source=None):
 if event.get("schema")!=gdn_stream.PROTOCOL:
  c.require(checker_ref is None,"current whole-model rejects historical rawdump protocol authority")
  return consume_historical_raw(event,pinned_state_sources)
 c.require(event["layer"] in GDN and event["prefix"] and event["original_forward_core_unchanged"] is True
  and event["original_forward_unchanged"] is True and event["deployed_state_sources"]==pinned_state_sources,
  "unchanged actual GDN math/source identity")
 c.require(checker_ref is not None and event["independent_checker"]==checker_ref,
  "exact source-bound independently implemented all-row live checker")
 c.bound(checker_ref["path"],checker_ref["sha256"])
 raw=c.obj(event["actual_metadata_before"])
 c.require(raw["prefix"]==event["prefix"] and raw["epoch"]==event["epoch"] and raw["rank"]==event["rank"] and
  raw["device_snapshot_copied_outside_GLOBAL_capture"] is True,"current complete actual writer metadata")
 proof=gdn_stream.consume_budget(c.obj(event["joint_budget"]))
 c.require(proof["epoch"]==event["epoch"] and expected_source is not None and proof["source"]==expected_source,"current epoch joint BEFORE/after-row ordinary budget")
 states=event["states"]
 c.require(type(states) is list and len(states)==2 and [s["name"] for s in states]==["conv","recurrent"],
  "both entire actual native GDN original state tensors")
 domain=gdn_metadata.plan(raw,*[s["identity_before"]["shape"][0] for s in states]);checked=[]
 actual=next(r for r in proof["records"] if r["rank"]==event["rank"])
 c.require(all(r["checker"]==checker_ref for r in proof["records"]),"joint real-shape plan bound to same current independent checker")
 for state in states:
  ident=state["identity_before"];unit=identity(ident)
  c.require(ident==state["identity_after"] and state["state_slot_axis"]==0 and
   state["original_before_CPU_saved"] is True and state["after_all_rows_streamed_once"] is True and
   state["all_after_rows_finite"] is True,"whole original before/after identity/coverage retained")
  known=[r for r in actual["states"] if r["prefix"]==event["prefix"] and r["name"]==state["name"]]
  c.require(len(known)==1 and known[0]["layer"]==event["layer"] and known[0]["identity"]==ident,
   "same actually initialized native state as all4 preallocation plan")
  writes=domain["written_slots"][state["name"]]
  record=gdn_stream.consume_summary(state["live_check"],ident,writes)
  c.require(record["all_rows"]*unit==state["live_check"]["logical_after_bytes"] and
   state["active_state_dense_equivalence_not_asserted"] is True,
   "all active finite is required; free-running active state is not forced to dense")
  c.require(state["active_slots"]==[dict(slot=i,bitwise_changed=i in record["active_changed_slots"],after_finite=True) for i in writes],
   "all actually active changed/unchanged rows, no skipped finite checks")
  checked.append(dict(name=state["name"],total_slots=ident["shape"][0],written_slots=writes,
   all_untouched_slots=record["inactive_slots"],state_slot_bytes=unit,all_logical_bytes_compared=True,
   untouched_slots_identical=True,all_active_and_inactive_after_finite=True,identity=ident,
   independent_live_byte_check=record,allocator_page_gap_bytes_not_claimed=True))
 return dict(schema="sparq.actual-GDN-all-row-live-check/v2",layer=event["layer"],prefix=event["prefix"],
  rank=event["rank"],epoch=event["epoch"],states=checked,writer_domain=domain,passed=True,
  protocol=gdn_stream.PROTOCOL,joint_budget=event["joint_budget"],independent_checker=checker_ref,
  numpy_dependency=actual["numpy"],
  all_active_and_inactive_after_finite=True,postmortem_success_bytes_replay_claimed=False,
  active_state_dense_equivalence_not_claimed=True,model_ready=False)

def main():
 import argparse,json
 import gdn_source
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 p.add_argument("--event");p.add_argument("--event-sha256");p.add_argument("--output")
 p.add_argument("--checker");p.add_argument("--checker-sha256");p.add_argument("--source-manifest-sha256")
 a=p.parse_args()
 if not a.execute:
  print(json.dumps(dict(status="disabled",model_executed=False,ready=False)));return
 c.require(a.event and a.event_sha256 and a.output,"whole actual state event Ref and new output")
 event=c.obj(dict(path=a.event,sha256=a.event_sha256))
 checker=None if not a.checker else c.bound(a.checker,a.checker_sha256)
 expected=None
 if checker:
  import source_contract as full
  expected,_=full.source(str(full.ROOT/"SOURCE_MANIFEST.json"),a.source_manifest_sha256)
 result=consume(event,gdn_source.sources(),checker,expected)
 result.update(scope="all-row-live-byte-finite" if checker else "historical-inactive-rawdump-only",ready=False,model_ready=False)
 print(json.dumps(c.write(a.output,result),sort_keys=True))
if __name__=="__main__":main()

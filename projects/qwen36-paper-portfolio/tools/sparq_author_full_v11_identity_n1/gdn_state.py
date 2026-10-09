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

def consume(event,pinned_state_sources,checker_ref=None,expected_source=None,physical_context=None):
 if event.get("schema")==gdn_stream.PHYSICAL_PROTOCOL:
  return consume_physical(event,pinned_state_sources,checker_ref,expected_source,physical_context)
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


# v16 is explicitly a new physical shared-pool reference, not old v2 inactive
# semantics. Each Observer and EACH whole-trace replay owns a separate
# context. Only its current epoch is retained, never process-global state.
class PhysicalContext:
 def __init__(self):self.cache={}
def physical_owner(record,root,source,checker_ref):
 m=gdn_stream.consume_memory(record["cgroup"])
 return dict(source=source,checker=checker_ref,rank=record["rank"],trace_root=str(root),
  process=m["process"],version=m["version"],cgroup=m["cgroup"],path=m["path"],
  mount_root=m["mount_root"],mount_point=m["mount_point"],leaf_identity=m["leaf_identity"])
def consume_physical_epoch(ref,checker_ref,source,context):
 c.require(isinstance(context,PhysicalContext),"explicit isolated physical consumer context required")
 raw=c.obj(ref);rank=raw["rank"];epoch=raw["epoch"];root=Path(ref["path"]).parent
 c.require(root.is_absolute() and root.resolve()==root and Path("/cache/cch") in root.parents,
  "exact owned physical trace root for current consumption")
 cachekey=(source["sha256"],checker_ref["sha256"],rank,str(root))
 old=context.cache.get(cachekey)
 if old is not None and old["ref"]==ref:return old
 c.require(raw["schema"]==gdn_stream.PHYSICAL_PROTOCOL and raw["source"]==source and
  raw["independent_checker"]==checker_ref and raw["all64_actual_writer_metadata"] is True and
  raw["postmortem_success_bytes_replay_claimed"] is False,
  "one source-bound real physical epoch, not postmortem raw success replay")
 proof=gdn_stream.consume_physical_budget(c.obj(raw["joint_budget"]))
 c.require(proof["epoch"]==epoch and proof["source"]==source,"same actual all4 byte-pool budget")
 record=next(r for r in proof["records"] if r["rank"]==rank)
 namespace_owner=physical_owner(record,root,source,checker_ref)
 if old is not None:c.require(old["owner"]==namespace_owner,"same actual PID/start/CID/namespace leaf within physical history")
 pools=next(r["pools"] for r in proof["pools"] if r["rank"]==rank)
 ledger=c.obj(raw["ledger"])
 if epoch==1:
  c.require(old is None,"first actual epoch once; no reset of typed history")
  previous=c.obj(ledger["previous"])
  c.require(previous==dict(schema="sparq.actual-pool-last-writer-types/v1",rank=rank,epoch=0,source=source,
   pools=[],allocator_retirement_not_claimed=True),"no invented GDN-type or allocator prehistory")
 else:
  c.require(old is not None and old["epoch"]==epoch-1 and old["ledger_ref"]==ledger["previous"],
   "independent sequential all-real-epoch typed history; no skipped/deleted turn")
  previous=old["ledger"]
 rebuilt=gdn_stream.typed_ledger(pools,previous,rank,epoch,source)
 rebuilt.update(previous=ledger["previous"],joint_budget=raw["joint_budget"])
 c.require(rebuilt==ledger,"independent all64 metadata last-writer-type replay, never producer tags")
 c.require(raw["original_full_before_copy_count"]==len(pools)==len(raw["pool_summaries"]),
  "ONE complete physical before copy per initialized original slab")
 summaries={};summary_refs={};segments={p["before_owner"]:p["segments"] for p in ledger["pools"]}
 for r in raw["pool_summaries"]:
  row=c.obj(r);owner=row["before_owner"]
  c.require(owner not in summaries,"one complete ordered before/after stream per physical owner")
  pool=next((p for p in pools if p["before_owner"]==owner),None)
  c.require(pool is not None,"no unknown physical owner success")
  summaries[owner]=gdn_stream.consume_physical_summary(row,pool,segments[owner]);summary_refs[owner]=r
 c.require(set(summaries)=={p["before_owner"] for p in pools},"all complete original slabs including padding")
 result=dict(ref=ref,epoch=epoch,rank=rank,record=record,pools=pools,summaries=summaries,
  ledger=rebuilt,ledger_ref=raw["ledger"],summary_refs=summary_refs,numpy=record["numpy"],source=source,
  joint_budget=raw["joint_budget"],owner=namespace_owner)
 context.cache[cachekey]=result
 return result
def consume_physical(event,pinned_state_sources,checker_ref,source,context):
 c.require(event["layer"] in GDN and event["prefix"] and event["rank"] in range(4) and
  event["original_forward_core_unchanged"] is event["original_forward_unchanged"] is True and
  event["deployed_state_sources"]==pinned_state_sources and checker_ref is not None and
  event["independent_checker"]==checker_ref and source is not None,
  "original actual all48 source/class identities, current independently bound physical checker")
 c.bound(checker_ref["path"],checker_ref["sha256"])
 got=consume_physical_epoch(event["physical_epoch"],checker_ref,source,context)
 c.require(got["epoch"]==event["epoch"] and got["rank"]==event["rank"] and got["joint_budget"]==event["joint_budget"],
  "logical layer references same actual rank/epoch/physical budget")
 states=event["states"];c.require(len(states)==2 and [s["name"] for s in states]==["conv","recurrent"],
  "both96 original native state identities still explicit")
 raw=c.obj(event["actual_metadata_before"])
 domain=gdn_metadata.plan(raw,*[s["identity_before"]["shape"][0] for s in states])
 c.require(raw["rank"]==event["rank"] and raw["epoch"]==event["epoch"] and raw["prefix"]==event["prefix"],
  "actual logical writer metadata retained, not union claims")
 checked=[]
 for s in states:
  x=s["identity_before"];identity(x);gdn_stream.physical_identity(x)
  c.require(x==s["identity_after"] and s["state_slot_axis"]==0,"all original logical before/after identities")
  known=[r for r in got["record"]["states"] if r["layer"]==event["layer"] and r["name"]==s["name"]]
  c.require(len(known)==1 and known[0]["prefix"]==event["prefix"] and known[0]["identity"]==x and
   known[0]["metadata"]==event["actual_metadata_before"],"exact complete alias and own actual metadata")
  vk=gdn_stream.exact_view_key(x)
  owners=[p for p in got["pools"] if any(m["layer"]==event["layer"] and m["name"]==s["name"] and
   m["prefix"]==event["prefix"] and m["view"]==vk for m in p["members"])]
  c.require(len(owners)==1,"one complete physical before owner, not pointer-only merge")
  p=owners[0];summary=got["summaries"][p["before_owner"]]
  checked.append(dict(name=s["name"],identity=x,total_slots=x["shape"][0],
   written_slots=domain["written_slots"][s["name"]],physical_before_owner=p["before_owner"],
   physical_stream_summary_ref=got["summary_refs"][p["before_owner"]],physical_epoch=event["physical_epoch"],
   all_unwritten_physical_bytes_exact=True,last_actual_GDN_typed_segments_finite=True,
   old_per_layer_inactive_gate_not_claimed=True,allocator_retirement_not_claimed=True))
 return dict(schema="sparq.actual-GDN-shared-physical-check/v3",protocol=gdn_stream.PHYSICAL_PROTOCOL,
  layer=event["layer"],prefix=event["prefix"],rank=event["rank"],epoch=event["epoch"],states=checked,
  writer_domain=domain,joint_budget=event["joint_budget"],independent_checker=checker_ref,numpy_dependency=got["numpy"],
  all_unwritten_physical_bytes_exact=True,last_actual_GDN_typed_segments_finite=True,
  old_per_layer_inactive_gate_not_claimed=True,allocator_retirement_not_claimed=True,
  active_state_dense_equivalence_not_claimed=True,postmortem_success_bytes_replay_claimed=False,passed=True,model_ready=False)

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
 result=consume(event,gdn_source.sources(),checker,expected,PhysicalContext())
 result.update(scope="all-row-live-byte-finite" if checker else "historical-inactive-rawdump-only",ready=False,model_ready=False)
 print(json.dumps(c.write(a.output,result),sort_keys=True))
if __name__=="__main__":main()

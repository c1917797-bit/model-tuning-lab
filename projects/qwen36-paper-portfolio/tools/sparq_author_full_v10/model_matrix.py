"""Exhaustive real model/lifecycle coverage, never Python-call counts on FULL replay."""
FA=tuple(range(3,64,4));GDN=tuple(i for i in range(64) if i%4!=3)
BATCHES=tuple(range(1,17))
def need(ok,why):
 if not ok:raise ValueError(why)
def expected():
 # The declared model schedule requires all true batches, actual mixed NONE,
 # actual stock FULL decode, and actual reused allocator slots. No new RMS gate.
 return {(rank,batch,kind,layer) for rank in range(4) for batch in BATCHES
  for kind in ("mixed-prefill-decode","decode-FULL","request-slot-reuse")
  for layer in range(64)}
class Coverage:
 def __init__(self):
  self.seen=set();self.turns={};self.last={};self.reuses=[];self.last_pointers={}
 def turn(self,rank,event):
  need(type(rank) is int and rank in range(4),"real TP4 rank")
  batch=event["batch"];frame=event["frame"];epoch=event["epoch"]
  need(type(batch) is int and batch in BATCHES and len(frame)==batch and
   len({r["rid"] for r in frame})==batch,"true B1..16 request rows, no padded authority")
  need(type(epoch) is int and epoch>self.turns.get(rank,0),"actual monotonic turn, no duplicated/stale replay")
  self.turns[rank]=epoch
  need(event["runtime"] in ("NONE","FULL") and event["all_16_FA_conditional_output_passed"] is True
   and event["all_48_GDN_untouched_slot_preservation_passed"] is True,
   "complete actual64 layer checks, never source counts or selected token samples")
  need(set(event["fa"])=={str(i) for i in FA} and set(event["gdn"])=={str(i) for i in GDN},
   "independently consumed actual16FA +48GDN records")
  for r in frame:
   need(type(r["generation"]) is int and r["generation"]>0 and type(r["slot"]) is int and r["slot"] in range(16),
    "actual request generation/slot")
   identity=(r["rid"],r["generation"]);old=self.last.get((rank,r["slot"]))
   if old is not None and old!=identity:
    need(r["computed"]==0 and event["actual_finished_generation_before_reuse"] is True,
     "slot reused only after exact original scheduler-finished identity")
    self.reuses.append((rank,batch,epoch,r["slot"],old,identity))
   self.last[(rank,r["slot"])]=identity
  kinds=[]
  if event["runtime"]=="FULL":
   need(event["original_ACL_replay_count"]==1 and event["fresh_16_PA_post_updates"]==16,
    "actual original ACL replay plus all16 stock PA POST updates")
   kinds.append("decode-FULL")
  elif event["actual_mixed_prefill_and_decode"] is True:kinds.append("mixed-prefill-decode")
  if any(x[0]==rank and x[1]==batch and x[2]==epoch for x in self.reuses):kinds.append("request-slot-reuse")
  for kind in kinds:
   for layer in range(64):self.seen.add((rank,batch,kind,layer))
 def finish(self):
  missing=sorted(expected()-self.seen)
  need(not missing,"incomplete actual model64/batch/mixed/reuse/FULL coverage: "+str(missing[:8]))
  return dict(real_ranks=4,layers=64,FA=16,GDN=48,true_batches=list(BATCHES),
   exhaustive_coverage_cells=len(expected()),covered_cells=len(self.seen),
   actual_FULL_stock=True,mixed_and_slot_reuse=True,model_matrix_checked=True,
   performance_checked=False,task_quality_checked=False,ready=False)

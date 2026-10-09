"""Independent actual scheduler and per-layer native GDN slot lifecycle consumer.
No virtual RequestLedger slot is accepted as physical allocator evidence.
"""
import evidence as c,gdn_metadata,gdn_state
import hashlib,json
BATCHES=tuple(range(1,17))
class Coverage:
 def __init__(self):self.turns={};self.live={};self.seen=set();self.finished={};self.reuse_digest=hashlib.sha256();self.reuse_count=0
 def consume_turn(self,rank,boundary,gdn_events):
  e=boundary;batch=e["batch"];epoch=e["epoch"];scheduler=e["native_request_rows"]
  c.require(rank in range(4) and batch in BATCHES and type(epoch) is int and epoch==self.turns.get(rank,0)+1,
   "complete monotonic all real model epochs; no skipped layer/turn sample")
  self.turns[rank]=epoch
  c.require(scheduler["schema"]=="sparq.actual-scheduler-allocation/v1" and
   scheduler["actual_original_prepare_returned"] is True and scheduler["request_ids_order"]==e["request_ids"] and
   len(e["request_ids"])==batch and len(set(e["request_ids"]))==batch,"actual original scheduler request rows")
  rows=scheduler["request_rows"]
  c.require([r["rid"] for r in rows]==e["request_ids"] and set(scheduler["block_ids"])==set(e["request_ids"]),
   "entire actual scheduler/block allocation request order")
  qs=scheduler["query_start_loc_cpu"];qlens=gdn_metadata.segments(qs,"actual runner query offsets")
  c.require(len(qlens)==batch and qlens==[r["scheduled"] for r in rows],"actual mixed query lengths and scheduler counts")
  finished=set(scheduler["finished_req_ids"]);self.finished.setdefault(rank,set()).update(finished)
  for key,old in list(self.live.items()):
   if key[0]==rank and old["rid"] in finished:old["finished"]=True
  reused=False
  for event in gdn_events:
   c.require(event["layer"] in gdn_state.GDN and event["rank"]==rank and event["epoch"]==epoch,"current actual GDN layer epoch")
   raw=c.obj(event["actual_metadata_before"]);domain=gdn_metadata.plan(raw,*[s["identity_before"]["shape"][0] for s in event["states"]])
   c.require(raw["request_ids"]==e["request_ids"] and domain["query_lengths"][:batch]==qlens and
    all(n==0 for n in domain["query_lengths"][batch:]),"no stale GDN padded metadata vs real runner")
   for kind in ("conv","recurrent"):
    for native in domain[kind+"_rows"]:
     pos=native["row"];c.require(pos<batch,"padded native writer row cannot acquire a real request")
     req=rows[pos];key=(rank,event["prefix"],kind,native["slot"]);old=self.live.get(key)
     identity=(req["rid"],req["object_id"])
     if old is not None and old["identity"]!=identity:
      c.require(old["finished"] and req["computed"]==0,"physical GDN slot reuse only after exact original finish; no live/paused stealing")
      reused=True;record=dict(rank=rank,epoch=epoch,batch=batch,layer=event["layer"],state=kind,
       native_slot=native["slot"],old_request=old["rid"],new_request=req["rid"])
      self.reuse_digest.update(json.dumps(record,sort_keys=True,separators=(",",":")).encode());self.reuse_count+=1
     elif old is not None:c.require(req["computed"]>=old["computed"],"same native slot request rollback")
     self.live[key]=dict(identity=identity,rid=req["rid"],computed=req["computed"],finished=False)
  c.require(len(gdn_events)==48 and {x["layer"] for x in gdn_events}==set(gdn_state.GDN),"all48 actual per-group allocations, no one-group extrapolation")
  kinds=[]
  if e["runtime"]=="FULL":c.require(qlens==[1]*batch,"real FULL decode rows");kinds.append("FULL")
  elif any(r["computed"]>0 and r["scheduled"]==1 for r in rows) and any(r["scheduled"]>1 for r in rows):kinds.append("mixed")
  if reused:kinds.append("reuse")
  for kind in kinds:self.seen.add((rank,batch,kind))
  return dict(rank=rank,epoch=epoch,batch=batch,actual_kinds=kinds,physical_slot_reuse=reused,
   inactive_byte_preservation_separately_consumed=True,virtual_request_slots_not_consumed=True)
 def finish(self):
  wanted={(r,b,k) for r in range(4) for b in BATCHES for k in ("FULL","reuse")} | {(r,b,"mixed") for r in range(4) for b in BATCHES if b>=2}
  missing=sorted(wanted-self.seen)
  c.require(not missing,"actual TP4/allB mixed/reuse/FULL allocation coverage missing "+str(missing[:12]))
  return dict(cells=len(wanted),observed=len(self.seen),all_true_batches=list(BATCHES),actual_reuse_count=self.reuse_count,actual_reuse_rolling_sha256=self.reuse_digest.hexdigest(),full_original_turn_inputs_retained=True,model_ready=False)

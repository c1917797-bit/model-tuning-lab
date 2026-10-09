"""Exact original request ledger extracted from pinned eager model bridge; stdlib."""
import common
require=common.require
class RequestLedger:
 """Real runner request object identities + finished generations, never batch indices."""
 def __init__(self,capacity=16):
  self.capacity=capacity;self.live={};self.generations={};self.active=[];self.steps=0
 def finish(self,ids):
  for rid in ids:
   self.live.pop(rid,None)
 def prepare(self,rows,finished=()):
  self.finish(finished);require(type(rows) is list and 0<len(rows)<=self.capacity,"actual model request batch capacity")
  ids=[r["rid"] for r in rows];require(len(set(ids))==len(ids),"duplicate actual request identity")
  prepared=[]
  for row in rows:
   rid=row["rid"];require(type(rid) is str and rid and type(row["computed"]) is int and row["computed"]>=0 and
     type(row["scheduled"]) is int and row["scheduled"]>0 and type(row["object_id"]) is int and row["object_id"]>0,
     "actual request object/computed/scheduled fields")
   previous=self.live.get(rid)
   if previous is None:
    used={r["slot"] for r in self.live.values()};available=sorted(set(range(self.capacity))-used)
    require(available,"actual paused request leases exceed admitted16; never steal a live slot")
    generation=self.generations.get(rid,0)+1;self.generations[rid]=generation
    previous=dict(rid=rid,generation=generation,slot=available[0],object_id=row["object_id"],computed=row["computed"])
    self.live[rid]=previous
   require(previous["object_id"]==row["object_id"] and row["computed"]>=previous["computed"],
    "request-ID ABA or rollback/recompute requires explicit finish/new generation")
   previous["computed"]=row["computed"]
   prepared.append(dict(previous,scheduled=row["scheduled"],expected_length=row["computed"]+row["scheduled"]))
  self.active=prepared;self.steps+=1;return [dict(x) for x in prepared]
 def decode(self,lengths):
  require(len(lengths)==len(self.active) and all(type(n) is int and n>0 for n in lengths),"actual nonempty decode sequence lengths")
  require(all(x["scheduled"]==1 and x["expected_length"]==n for x,n in zip(self.active,lengths)),
   "actual query rows/runner lease/native seq lengths disagree; no batch-row alias")
  return [dict(x,native_length=n) for x,n in zip(self.active,lengths)]

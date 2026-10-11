"""Observer-OFF boundary journal; no per-token scalar journal claims or raw tensor IO."""
import json
def need(v,m):
 if not v:raise ValueError(m)
class BoundaryJournal:
 def __init__(self,publish,identity,rank,owner_ref,event_ref,expected_ids,read):
  need(callable(publish)and callable(identity)and callable(read)and type(rank)is int and rank in range(4),
   "actual timing boundary callbacks/rank")
  need(type(expected_ids)is list and expected_ids and len(expected_ids)==len(set(expected_ids)),"actual all planned owners")
  self.publish=publish;self.identity=identity;self.ident=identity();self.rank=rank
  self.owner=owner_ref;self.event=event_ref;self.expected=set(expected_ids);self.read=read
  self.retired=set();self.ingress=set();self.refs=[];self.failed=False;self.final=None
 def __call__(self,label,value):
  need(self.final is None and self.identity()==self.ident,"actual live boundary owner")
  row=json.loads(json.dumps(value,sort_keys=True,allow_nan=False))
  schema=row.get("schema","")
  if schema=="kivi.actual-native-ingress/v1":
   need(row["rank"]==self.rank and row["identity"]==self.ident and row["req_id"]in self.expected-self.ingress
    and row["scheduled_type"]=="SchedulerOutput/NewRequestData"
    and type(row["prompt_token_ids"])is list and len(row["prompt_token_ids"])==32768,
    "actual unique complete source-native ingress boundary")
   self.ingress.add(row["req_id"])
  elif schema=="kivi.actual-packed-qwen-retire/v1":
   need(row["rank"]==self.rank and row["identity"]==self.ident and row["actual_native_finished"]is True
    and row["request_id"]in self.ingress-self.retired,"actual unique source-native retirement")
   self.retired.add(row["request_id"])
  elif schema=="kivi.actual-packed-qwen-update/v1":
   need(row["rank"]==self.rank and row["identity"]==self.ident,"actual boundary update owner")
  elif "fail"in schema.lower():self.failed=True
  else:raise ValueError("timing forbids per-token FRAME/OUTPUT/raw/observer publication")
  ref=self.publish(label,row);need(self.read(ref)==row,"actual immutable timing boundary roundtrip")
  self.refs.append(ref);return ref
 def finish(self,final_ref):
  need(self.final is None and not self.failed and self.identity()==self.ident,"one nonfailed actual drain")
  final=self.read(final_ref)
  need(final["schema"]=="kivi.actual-packed-qwen-installer-final/v1"
   and final["rank"]==self.rank and final["identity"]==self.ident and final["owner_ref"]==self.owner
   and final["event_ref"]==self.event and set(final["finished"])==self.expected==self.retired==self.ingress
   and len(final["finished"])==len(self.expected) and final["diagnostic"]is False
   and final["timing_model_prerequisite_external"]is True and final["graph_checked"]is False
   and final["model_ready"]is final["run_authority"]is False,"actual Book.close/native finish, not HTTP DONE")
  value=dict(schema="kivi.b1-timing-native-final/v1",rank=self.rank,identity=self.ident,owner_ref=self.owner,
   event_ref=self.event,final_ref=final_ref,boundary_refs=self.refs,finished=sorted(self.retired),
   complete_per_token_journal=False,numeric_verified=False,model_ready=False,run_authority=False)
  self.final=self.publish("B1-TIMING-r%d-FINAL"%self.rank,value);return self.final

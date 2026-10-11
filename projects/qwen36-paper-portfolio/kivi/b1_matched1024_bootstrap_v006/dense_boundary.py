"""B1 native OFF arm: source-owned ingress/finish boundary only; no tensor observer."""
import hashlib,inspect,types
from pathlib import Path
RUNNER_SHA="94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968"
def need(v,m):
 if not v:raise ValueError(m)
def pin(value):
 path=Path(inspect.getfile(getattr(value,"__func__",value))).resolve()
 need(path.is_file()and not path.is_symlink()and hashlib.sha256(path.read_bytes()).hexdigest()==RUNNER_SHA,
  "exact original native runner, not a stacked algorithm patch")
def install(runner,bindings,identity,rank,publish,publish_final,source_ref,recipe_ref,cached_guard):
 pin(type(runner));pin(runner._update_states)
 need("_update_states"not in vars(runner)and not runner.requests and runner.input_batch.num_reqs==0,
  "native empty B1 runner before first request")
 ident=identity();need(ident==bindings.owner["rank_bindings"][str(rank)],"actual source-bound all4 rank")
 expected=list(bindings.expected);need(len(expected)==3,"two warmup owners and one measured owner")
 need(callable(cached_guard),"same source-pinned common cached-ingress guard")
 current=runner._update_states;seen=set();retired=set();refs=[];state={"final":None,"scheduler_type":None}
 def emit(label,row):
  need(identity()==ident,"same actual native boundary owner")
  ref=publish(label,row);refs.append(ref);return ref
 def update(self,scheduler):
  need(state["final"]is None,"own live native B1 worker")
  new=[v.req_id for v in scheduler.scheduled_new_reqs];finished=list(scheduler.finished_req_ids)
  need(len(new)<=1 and len(set(finished))==len(finished)and set(finished)<=seen-retired,
   "unique actual native retirement, no guessed HTTP completion")
  boundary=state["scheduler_type"]is None or bool(new)or bool(finished)
  if boundary:
   need(identity()==ident,"same actual native lifecycle boundary identity")
   bindings.check_new(scheduler,ident,rank,emit);state["scheduler_type"]=type(scheduler)
  else:cached_guard(bindings,scheduler,state["scheduler_type"],ident,rank)
  seen.update(new)
  need(len(seen-retired-set(finished))<=1,"B1 only; no unqualified concurrency")
  answer=current(scheduler) # exact original call once, including deferred return
  need(set(self.requests)==seen-retired-set(finished)and self.input_batch.num_reqs<=1,
   "actual native state; no preemption/removal or hidden owner")
  for rid in finished:
   need(rid not in self.requests and rid not in self.input_batch.req_ids,"actual native owner drained")
   emit("PACKED-QWEN-r%d-RETIRE-%s"%(rank,rid),
    dict(schema="kivi.actual-packed-qwen-retire/v1",rank=rank,identity=ident,request_id=rid,
     actual_native_finished=True,algorithm_arm="dense",source_ref=source_ref,recipe_ref=recipe_ref,
     runner_source_sha256=RUNNER_SHA,model_ready=False))
   retired.add(rid)
  if retired==set(expected):
   need(not self.requests and self.input_batch.num_reqs==0 and not self.input_batch.req_ids
    and self._update_states is replacement,"complete own native drain and exact wrapper")
   self._update_states=current
   state["final"]=emit("B1-DENSE-r%d-FINAL"%rank,dict(schema="kivi.b1-dense-native-final/v1",
    rank=rank,identity=ident,source_ref=source_ref,recipe_ref=recipe_ref,finished=sorted(retired),
    boundary_refs=list(refs),runner_source_sha256=RUNNER_SHA,original_update_restored=True,
    complete_per_token_journal=False,numeric_verified=False,model_ready=False,run_authority=False))
   publish_final(state["final"])
  return answer
 replacement=types.MethodType(update,runner);runner._update_states=replacement
 return state

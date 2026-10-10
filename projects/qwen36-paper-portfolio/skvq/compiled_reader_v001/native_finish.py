"""Source-pinned ORIGINAL _update_states, native finished IDs and exact owned restore.
No HTTP/SSE-DONE inference, scheduler synthesis, dummy request or new drain.
"""
import sys,types
import contract as C
from native_binding import sources,ASCEND
from numeric import identity
class Finish:
    def __init__(self,worker,binding,source,rank,root):
        self.runner=worker.model_runner;self.binding=binding;self.source=source;self.rank=rank;self.root=root
        self.origins=sources();cls=sys.modules[ASCEND].NPUModelRunner
        C.need(type(self.runner)is cls and "_update_states"not in self.runner.__dict__,"actual original runner/no overlapping update hook")
        self.original=self.runner._update_states
        C.need(self.original.__func__ is cls._update_states,"exact original native update body")
        self.ref=None;self.closed=False
        owner=self
        def update(receiver,scheduler_output):
            C.need(receiver is owner.runner and not owner.closed and sources()==owner.origins,"same source-qualified native state receiver")
            finished=sorted(scheduler_output.finished_req_ids)
            result=owner.original(scheduler_output) # Preserve original deferred callable return.
            if owner.binding.owner is not None and owner.binding.owner in finished:
                value=dict(schema="skvq.compiled-reader.native-finished/v1",source_ref=owner.source,rank_identity=owner.rank,
                  finished_req_ids=finished,requests_after=sorted(receiver.requests),
                  input_batch_after=[x for x in receiver.input_batch.req_ids if x is not None],
                  called_original_update=True,actual_original_function_origin=owner.origins[ASCEND],
                  num_scheduled_tokens=dict(scheduler_output.num_scheduled_tokens),
                  total_num_scheduled_tokens=scheduler_output.total_num_scheduled_tokens,actual_process=identity())
                owner.ref=C.atomic(owner.root/"NATIVE_FINISHED.json",value) # Original state BEFORE predicates.
                C.need(finished==[owner.binding.owner]and not value["requests_after"]and not value["input_batch_after"],
                  "real single owner retired in original requests/input batch")
            return result
        self.bound=types.MethodType(update,self.runner);self.runner.__dict__["_update_states"]=self.bound
    def consume(self,ref,worker,caches,rank):
        C.need(ref==self.ref and worker.model_runner is self.runner and rank==self.rank and ref is not None,"actual original finished evidence required")
        value=C.obj(ref)
        C.need(value["source_ref"]==self.source and value["rank_identity"]==rank and value["called_original_update"]is True and
          value["finished_req_ids"]==[self.binding.owner]and not value["requests_after"]and not value["input_batch_after"]and
          value["actual_original_function_origin"]==self.origins[ASCEND]and sources()==self.origins,"actual native finish/source closure")
        C.need(all(c.request==self.binding.owner and c.epoch==1 for c in caches.values()),"same actual compact owners, no HTTP shortcut")
    def restore(self):
        C.need(self.runner.__dict__.get("_update_states")is self.bound,"owned exact update hook")
        del self.runner.__dict__["_update_states"];restored=self.runner._update_states
        C.need(restored.__func__ is self.original.__func__ and restored.__self__ is self.original.__self__,"original native update bound restored")
        self.closed=True

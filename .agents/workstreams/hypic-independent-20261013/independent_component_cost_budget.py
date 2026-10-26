"""Default-off selected-step component timing. Original functions/writes remain unchanged."""
import functools,hashlib,importlib,inspect,sys,threading,time,types
from pathlib import Path
GROUPS=("c1_packed_prepare","c1_prefix_alignment","mixed_native_prepare","layer_finite_validate")
SPECS=(("independent_c1_packed_prepare",None,"prepare_packed_layer","c1_packed_prepare"),
       ("independent_c1_short_prefix",None,"align_short_prefix_terminals","c1_prefix_alignment"),
       ("independent_native_decode_prepare",None,"prepare_native_decode","mixed_native_prepare"),
       ("independent_layer_finite_guard","LayerFiniteGuard","validate","layer_finite_validate"))
class ComponentBudget:
    def __init__(self,receipt_emit,resolve,*,clock=time.perf_counter_ns,max_calls=100000,max_steps=256):
        if(not callable(receipt_emit)or not callable(resolve)or not callable(clock)
           or type(max_calls)is not int or not 1<=max_calls<=100000
           or type(max_steps)is not int or not 1<=max_steps<=256):
            raise ValueError("explicit bounded component observer required")
        self.receipt_emit=receipt_emit;self.resolve=resolve;self.clock=clock
        self.max_calls=max_calls;self.max_steps=max_steps
        self.lock=threading.RLock();self.active=None;self.sealed=set()
        self.closed=False;self.failed=False;self.emitting=False;self.slots=[]
    def _now(self):
        x=self.clock()
        if type(x)is not int or x<0:raise ValueError("nonnegative integer monotonic clock required")
        return x
    def _identity(self,event):
        identity=self.resolve(event)
        if identity is None:return None
        key,ids=identity
        if(type(key)is not tuple or len(key)!=2 or type(key[0])is not int or key[0]not in range(4)
           or type(key[1])is not int or key[1]<0 or type(ids)is not tuple
           or not 1<=len(ids)<=64 or len(set(ids))!=len(ids)
           or any(type(x)is not str or not x or len(x)>512 for x in ids)):
            raise ValueError("actual bounded selected rank/step/request set required")
        return key,ids
    def _step(self,identity):
        if self.closed or self.failed or self.emitting:raise RuntimeError("component observer closed/failed/recursive")
        if identity is None:
            if self.active is not None:raise ValueError("selected component step abandoned")
            return None
        key,ids=identity
        if key in self.sealed:raise ValueError("component callback after sealed step")
        if self.active is None:
            if len(self.sealed)>=self.max_steps:raise ValueError("component step bound exceeded")
            self.active={"key":key,"ids":ids,"thread":threading.get_ident(),"stack":[],"calls":0,
                         "groups":{g:{"calls":0,"inclusive_ns":0,"exclusive_observed_ns":0,
                                      "max_ns":0,"failures":0}for g in GROUPS},
                         "root_interval_union_ns":0,"probe_metadata_ns":0}
        s=self.active
        if s["key"]!=key or s["ids"]!=ids or s["thread"]!=threading.get_ident():
            raise ValueError("overlapping or changed selected component identity")
        return s
    def assert_ownership(self):
        for owner,name,original,wrapped in self.slots:
            if inspect.getattr_static(owner,name)is not wrapped:
                raise RuntimeError("component observer target ownership changed")
    def timed(self,group,original,*args,**kwargs):
        if group not in GROUPS or not callable(original):raise ValueError("declared component target required")
        entered=self._now()
        with self.lock:
            self.assert_ownership();s=self._step(self._identity({}))
            if s is not None:
                if s["calls"]>=self.max_calls or len(s["stack"])>=8:
                    self.failed=True;raise ValueError("component call/depth bound exceeded")
                if any(x["group"]==group for x in s["stack"]):
                    self.failed=True;raise RuntimeError("recursive component target")
                started=self._now()
                if started<entered:raise ValueError("component clock moved backwards")
                frame={"group":group,"started":started,"children":0}
                s["stack"].append(frame);s["calls"]+=1
        if s is None:return original(*args,**kwargs)
        def finish(failed):
            ended=self._now()
            with self.lock:
                self.assert_ownership()
                if self._identity({})!=(s["key"],s["ids"]):
                    self.failed=True;raise ValueError("component selected context changed during original call")
                if(self.active is not s or not s["stack"]or s["stack"][-1]is not frame
                   or s["thread"]!=threading.get_ident()or ended<started):
                    self.failed=True;raise ValueError("component interval/ownership mismatch")
                duration=ended-started
                if frame["children"]>duration:
                    self.failed=True;raise ValueError("nested component intervals exceed parent")
                s["stack"].pop();row=s["groups"][group];row["calls"]+=1
                row["inclusive_ns"]+=duration;row["exclusive_observed_ns"]+=duration-frame["children"]
                row["max_ns"]=max(row["max_ns"],duration);row["failures"]+=int(failed)
                if s["stack"]:s["stack"][-1]["children"]+=duration
                else:s["root_interval_union_ns"]+=duration
                meta_end=self._now()
                if meta_end<ended:raise ValueError("component metadata clock moved backwards")
                s["probe_metadata_ns"]+=started-entered+meta_end-ended
        try:result=original(*args,**kwargs)
        except BaseException as error:
            self.failed=True
            try:finish(True)
            except BaseException as cleanup:
                if hasattr(error,"add_note"):error.add_note("Owned component timing cleanup failed: "+str(cleanup)[:256])
            raise
        else:
            finish(False);return result
    def wrap_emit(self,original_emit):
        if not callable(original_emit)or original_emit is self.receipt_emit:
            raise ValueError("distinct unchanged original callback and raw receipt sink required")
        @functools.wraps(original_emit)
        def observed(event):
            if event.get("event")!="compact_model_rows_completed":
                return original_emit(event)
            with self.lock:
                self.assert_ownership();s=self._step(self._identity(event))
                if s is None or s["stack"]or not s["calls"]:
                    self.failed=True;raise ValueError("complete selected component scopes required")
                key=s["key"];ids=s["ids"]
                if event.get("rank")!=key[0]or event.get("step")!=key[1]or event.get("request_ids")!=list(ids):
                    self.failed=True;raise ValueError("component/model completion identity differs")
            # The original callback writes model completion and the unchanged
            # R36 durable fence first. Additional receipts bypass that sealed
            # selected-step wrapper and use the same original unfiltered writer.
            try:result=original_emit(event)
            except BaseException:
                self.failed=True;raise
            with self.lock:
                if self.active is not s or self.failed:raise RuntimeError("failed component step cannot seal")
                receipt={"event":"r38_component_budget_step","rank":key[0],"step":key[1],"request_ids":list(ids),
                         "groups":s["groups"],"root_interval_union_ns":s["root_interval_union_ns"],
                         "probe_metadata_ns":s["probe_metadata_ns"],"calls":s["calls"],
                         "original_function_arguments_results_exceptions_unchanged":True,
                         "original_evidence_unfiltered":True,"r36_completion_fence_precedes_receipts":True,
                         "scope":"Observed original CPU-call spans, including queued NPU waits and nested probes. Not isolated GPU time, removable time or service speed."}
                self.emitting=True
                try:
                    began=self._now();self.receipt_emit(receipt);ended=self._now()
                    if ended<began:raise ValueError("receipt clock moved backwards")
                    self.receipt_emit({"event":"r38_component_budget_flush","rank":key[0],"step":key[1],
                        "request_ids":list(ids),"first_receipt_emit_ns":ended-began,"extra_receipt_records":2,
                        "flush_record_own_write_time_unmeasured":True,
                        "scope":"First diagnostic receipt write/fsync observed; this second record's write is counted but not timed. No zero-overhead assumption."})
                except BaseException:
                    self.failed=True;raise
                finally:self.emitting=False
                self.sealed.add(key);self.active=None
            return result
        return observed
    def install(self,bindings,root):
        if self.slots or self.closed or self.failed:raise RuntimeError("one owned component installation")
        if type(bindings)is not dict:raise ValueError("actual source bindings required")
        from graph_candidate.prefill_bridge import verify_support
        from graph_candidate.source_contract import verify_raw_function
        root=Path(root).resolve();verified=[]
        for module_name,class_name,name,group in SPECS:
            module=importlib.import_module(module_name)
            if Path(module.__file__).resolve()!=root/(module_name+".py"):
                raise ValueError("actual component module outside owning source root")
            source=verify_support(module,bindings.get(module_name))
            owner=module if class_name is None else getattr(module,class_name)
            original=inspect.getattr_static(owner,name)
            if type(original)is not types.FunctionType or hasattr(original,"__wrapped__"):
                raise ValueError("exact unwrapped source-owned component function required")
            qualname=name if class_name is None else class_name+"."+name
            verify_raw_function(module,source,original,name=name,qualname=qualname)
            verified.append((owner,name,original,group))
        slots=[]
        try:
            for owner,name,original,group in verified:
                def make(fn,label):
                    @functools.wraps(fn)
                    def wrapped(*a,**kw):return self.timed(label,fn,*a,**kw)
                    return wrapped
                wrapped=make(original,group);setattr(owner,name,wrapped)
                slots.append((owner,name,original,wrapped))
            self.slots=slots;self.assert_ownership()
        except BaseException:
            for owner,name,original,wrapped in reversed(slots):
                if inspect.getattr_static(owner,name)is wrapped:setattr(owner,name,original)
            raise
        return self.stop
    def close(self):
        with self.lock:
            if self.closed:return
            self.closed=True
            if self.active is not None or self.failed:
                raise ValueError("uncompleted or failed component observation cannot be accepted")
    def stop(self):
        with self.lock:
            self.assert_ownership()
            for owner,name,original,wrapped in reversed(self.slots):setattr(owner,name,original)
            self.slots=[]
            self.close()
def make_component_budget(receipt_emit,resolve):
    return ComponentBudget(receipt_emit,resolve)

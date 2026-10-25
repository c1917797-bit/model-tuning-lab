"""Bounded observation of the existing evidence emitter and its original fsync.
This module neither batches nor suppresses writes, and imports no device runtime.
"""
import functools,sys,threading,time

def selected_step(event):
    module=sys.modules.get("independent_compact_model_hook")
    selection=None if module is None else module.CURRENT_COMPACT_MODEL.get()
    if selection is None:return None
    plans=tuple(selection.plans)
    if not plans:raise ValueError("selected evidence step has no plans")
    key=(plans[0].rank,plans[0].step)
    if any((p.rank,p.step)!=key for p in plans):raise ValueError("mixed selected step")
    if event.get("rank",key[0])!=key[0]or event.get("step",key[1])!=key[1]:
        raise ValueError("evidence/selected step differs")
    ids=tuple(p.request_id for p in plans)
    if key[0]not in range(4)or type(key[1])is not int or len(ids)>64 or len(set(ids))!=len(ids):
        raise ValueError("bounded actual rank/step/request identity required")
    return key,ids

def interval_union_ns(intervals):
    end=None;total=0
    for start,stop in sorted(intervals):
        if stop<start:raise ValueError("negative monotonic interval")
        if end is None or start>end:total+=stop-start;end=stop
        elif stop>end:total+=stop-end;end=stop
    return total

class EvidenceIOBudget:
    def __init__(self,fd,fsync,counts,*,resolve=selected_step,clock=time.perf_counter_ns,
                 max_events=100000,max_steps=256):
        if type(fd)is not int or fd<0 or not all(callable(x)for x in(fsync,counts,resolve,clock)):
            raise ValueError("owned evidence FD and callbacks required")
        if type(max_events)is not int or not 1<=max_events<=100000 or type(max_steps)is not int or not 1<=max_steps<=256:
            raise ValueError("explicit bounded evidence observer required")
        self.fd=fd;self.original_fsync=fsync;self.counts=counts;self.resolve=resolve;self.clock=clock
        self.max_events=max_events;self.max_steps=max_steps;self.events=0
        self.lock=threading.RLock();self.local=threading.local();self.buckets={};self.sealed=set()
    def fsync(self,fd):
        if fd!=self.fd:raise ValueError("observer may synchronize only its owned evidence FD")
        frame=getattr(self.local,"frame",None)
        if frame is None:return self.original_fsync(fd)
        begin=self.clock()
        try:return self.original_fsync(fd)
        finally:
            end=self.clock()
            if end<begin:raise ValueError("negative fsync interval")
            frame["fsync"].append((begin,end))
    def _bucket(self,key,ids):
        with self.lock:
            if key in self.sealed:raise ValueError("selected step emitted after model-row seal")
            if self.events>=self.max_events:raise ValueError("evidence IO observer event limit")
            if key not in self.buckets:
                if len(self.buckets)+len(self.sealed)>=self.max_steps:raise ValueError("evidence IO observer step limit")
                self.buckets[key]={"ids":ids,"emit":[],"fsync":[],"groups":{},"threads":set(),
                    "calls":0,"written":0,"bytes":0,"filtered":0,"failed":0}
            b=self.buckets[key]
            if b["ids"]!=ids:raise ValueError("selected request set changed within a step")
            self.events+=1
            return b
    def _record(self,b,event,start,end,frame,before,after,failed):
        if end<start:raise ValueError("negative emitter interval")
        count=after[0]-before[0];size=after[1]-before[1]
        if count not in(0,1)or size<0:raise ValueError("original writer counters changed unexpectedly")
        with self.lock:
            kind=event.get("event")
            if type(kind)is not str or len(kind)>160:raise ValueError("bounded source event name required")
            if kind not in b["groups"]and len(b["groups"])>=128:raise ValueError("evidence IO group limit")
            g=b["groups"].setdefault(kind,{"calls":0,"emit_ns":0,"fsync_ns":0})
            g["calls"]+=1;g["emit_ns"]+=end-start;g["fsync_ns"]+=sum(y-x for x,y in frame["fsync"])
            b["calls"]+=1;b["written"]+=count;b["bytes"]+=size
            b["filtered"]+=int(count==0 and not failed);b["failed"]+=int(failed)
            b["emit"].append((start,end));b["fsync"].extend(frame["fsync"]);b["threads"].add(threading.get_ident())
    def _seal(self,key):
        with self.lock:
            b=self.buckets.pop(key);self.sealed.add(key)
        if b["failed"]:raise ValueError("failed original emission cannot form a valid budget")
        emit_union=interval_union_ns(b["emit"]);sync_union=interval_union_ns(b["fsync"])
        if sync_union>emit_union:raise ValueError("fsync intervals escaped original emitter")
        return {"event":"r35_evidence_io_budget_step","rank":key[0],"step":key[1],
            "request_ids":list(b["ids"]),"original_emit_calls":b["calls"],"original_written_events":b["written"],
            "original_written_bytes":b["bytes"],"original_filtered_calls":b["filtered"],
            "original_fsync_calls":len(b["fsync"]),"emit_interval_union_ns":emit_union,
            "emit_interval_sum_ns":sum(y-x for x,y in b["emit"]),
            "fsync_interval_union_ns":sync_union,"fsync_interval_sum_ns":sum(y-x for x,y in b["fsync"]),
            "selected_envelope_ns":max(y for x,y in b["emit"])-min(x for x,y in b["emit"]),
            "observed_threads":len(b["threads"]),"groups":b["groups"],
            "original_fsync_preserved":True,"extra_budget_row_intended":1,
            "extra_budget_row_excluded_from_observation":True,
            "scope":"Selected model context through model-row completion only; later native-progress and outside-context events excluded. Timed diagnostic, not speed treatment or whole-service causal saving."}
    def wrap(self,original_emit):
        @functools.wraps(original_emit)
        def observed(event):
            identity=self.resolve(event)
            if identity is None:return original_emit(event)
            if getattr(self.local,"frame",None)is not None:raise RuntimeError("recursive observed evidence emission")
            key,ids=identity;b=self._bucket(key,ids)
            before=self.counts();frame={"fsync":[]};self.local.frame=frame;begin=self.clock();failure=None
            try:result=original_emit(event)
            except BaseException as exc:
                failure=exc;raise
            finally:
                end=self.clock();self.local.frame=None
                try:self._record(b,event,begin,end,frame,before,self.counts(),failure is not None)
                except BaseException:
                    if failure is None:raise
            if event.get("event")=="compact_model_rows_completed":
                # Bypass this wrapper: exactly one extra diagnostic row, no recursion.
                original_emit(self._seal(key))
            return result
        return observed

def make_budget(fd,fsync,counts):
    return EvidenceIOBudget(fd,fsync,counts)

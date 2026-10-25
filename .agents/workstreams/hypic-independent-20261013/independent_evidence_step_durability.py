"""Default-off selected-model-step evidence durability; never buffers/drops writes.

Only the owned evidence FD is affected. Completion evidence is fsynced before
its callback returns; interrupted, uncompleted steps may lack a durable seal.
"""
import functools,sys,threading

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
    if(type(key[0])is not int or key[0]not in range(4)or type(key[1])is not int
       or key[1]<0 or not 1<=len(ids)<=64 or any(type(x)is not str or not x or len(x)>512 for x in ids)
       or len(set(ids))!=len(ids)):
        raise ValueError("bounded actual rank/step/request identity required")
    return key,ids

class StepDurability:
    def __init__(self,fd,fsync,counts,*,resolve=selected_step,max_events=100000,
                 max_bytes=134217728,max_steps=4096):
        if(type(fd)is not int or fd<0 or not all(callable(x)for x in(fsync,counts,resolve))
           or type(max_events)is not int or not 1<=max_events<=100000
           or type(max_bytes)is not int or not 1<=max_bytes<=134217728
           or type(max_steps)is not int or not 1<=max_steps<=4096):
            raise ValueError("bounded owned FD and durability callbacks required")
        self.fd=fd;self.original_fsync=fsync;self.counts=counts;self.resolve=resolve
        self.max_events=max_events;self.max_bytes=max_bytes;self.max_steps=max_steps
        self.lock=threading.RLock();self.local=threading.local()
        self.active=None;self.sealed=set();self.closed=False;self.failed=False
        self.fsync_attempts=0;self.fsync_completed=0;self.cleanup_error=None
    def _sync(self):
        self.fsync_attempts+=1
        result=self.original_fsync(self.fd)
        self.fsync_completed+=1
        return result
    def fsync(self,fd):
        if fd!=self.fd:raise ValueError("durability may synchronize only its owned evidence FD")
        frame=getattr(self.local,"frame",None)
        if frame is None:return self._sync()
        if frame["requests"]:raise ValueError("one original fsync request per original record required")
        frame["requests"]=1
        if frame["event"]=="compact_model_rows_completed":
            result=self._sync()
            frame["completion_fsynced"]=True
            return result
        return None
    def _counts(self):
        counts=self.counts()
        if(type(counts)not in(tuple,list)or len(counts)!=2
           or any(type(x)is not int or x<0 for x in counts)):
            raise ValueError("original evidence counters required")
        return tuple(counts)
    def _abort(self,error):
        self.failed=True
        try:
            if self.active is not None:self._sync()
        except BaseException as cleanup:
            self.cleanup_error=cleanup
            if hasattr(error,"add_note"):
                error.add_note("Owned evidence cleanup fsync failed: "+type(cleanup).__name__+": "+str(cleanup)[:512])
        finally:self.active=None
    def _step(self,identity,before):
        key,ids=identity
        if(type(key)is not tuple or len(key)!=2 or type(key[0])is not int or key[0]not in range(4)
           or type(key[1])is not int or key[1]<0 or type(ids)is not tuple
           or not 1<=len(ids)<=64 or any(type(x)is not str or not x or len(x)>512 for x in ids)
           or len(set(ids))!=len(ids)):
            raise ValueError("invalid selected step identity")
        if key in self.sealed:raise ValueError("selected step emitted after durable seal")
        if self.active is None:
            if len(self.sealed)>=self.max_steps:raise ValueError("durable step limit exceeded")
            self.active={"key":key,"ids":ids,"thread":threading.get_ident(),
                "start":before,"events":0,"bytes":0,"requests":0,"fsync_start":self.fsync_completed}
        step=self.active
        if(step["key"]!=key or step["ids"]!=ids or step["thread"]!=threading.get_ident()):
            raise ValueError("overlapping or changed selected evidence step")
        if step["events"]>=self.max_events:raise ValueError("pending event bound exceeded")
        return step
    def wrap(self,original_emit):
        @functools.wraps(original_emit)
        def durable(event):
            if getattr(self.local,"frame",None)is not None:
                raise RuntimeError("recursive durable evidence emission")
            with self.lock:
                if self.closed or self.failed:raise RuntimeError("durability writer is closed or failed")
                try:
                    identity=self.resolve(event)
                    if identity is None:
                        if self.active is not None:raise ValueError("selected evidence context abandoned before completion")
                        return original_emit(event)
                    before=self._counts();step=self._step(identity,before)
                    frame={"event":event.get("event"),"requests":0,"completion_fsynced":False}
                    self.local.frame=frame
                    try:result=original_emit(event)
                    finally:self.local.frame=None
                    after=self._counts()
                    if after[0]!=before[0]+1 or after[1]<=before[1] or frame["requests"]!=1:
                        raise ValueError("one original unfiltered complete write required")
                    step["events"]+=1;step["bytes"]+=after[1]-before[1];step["requests"]+=frame["requests"]
                    if(step["bytes"]>self.max_bytes or after[0]-step["start"][0]!=step["events"]
                       or after[1]-step["start"][1]!=step["bytes"]):
                        raise ValueError("pending bytes or original counter continuity exceeded")
                    if event.get("event")=="compact_model_rows_completed":
                        if not frame["completion_fsynced"]:raise ValueError("completion durability fence missing")
                        if self.fsync_completed-step["fsync_start"]!=1:
                            raise ValueError("unexpected selected-step fsync cadence")
                        key=step["key"]
                        receipt={"event":"r36_evidence_step_durable","rank":key[0],"step":key[1],
                            "request_ids":list(step["ids"]),"original_start_count":step["start"][0],
                            "original_end_count":after[0],"original_start_bytes":step["start"][1],
                            "original_end_bytes":after[1],"original_written_events":step["events"],
                            "original_written_bytes":step["bytes"],"original_fsync_requests":step["requests"],
                            "deferred_fsync_requests":step["requests"]-1,"completion_fsync_calls":1,
                            "receipt_fsync_calls":1,"completion_fsync_returned_before_receipt":True,
                            "callback_returns_after_receipt_fsync":True,
                            "scope":"Selected completed model-step evidence durable before callback return; no dropped writes. Uncompleted fatal-crash steps are not accepted."}
                        # Bypass this wrapper. Original writer immediately fsyncs
                        # this extra receipt; failure prevents successful return.
                        original_emit(receipt)
                        final=self._counts()
                        if(final[0]!=after[0]+1 or final[1]<=after[1]
                           or self.fsync_completed-step["fsync_start"]!=2):
                            raise ValueError("durable receipt write/fsync missing")
                        self.sealed.add(key);self.active=None
                    return result
                except BaseException as error:
                    self.local.frame=None;self._abort(error);raise
        return durable
    def close(self):
        with self.lock:
            if self.closed:return
            self.closed=True
            if self.active is not None:
                error=ValueError("cannot accept uncompleted selected evidence step at close")
                self._abort(error)
                raise error
            if self.failed:
                # A failed callback may have written a partial record. Retain it;
                # caller still propagates the original failure and rejects run.
                self._sync()

def make_durability(fd,fsync,counts):
    return StepDurability(fd,fsync,counts)

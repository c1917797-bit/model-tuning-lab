"""Bounded strong references around asynchronous foreign NPU launches.

No Torch import, environment changes or device API until an explicit recorded
event backend is supplied. Production event API qualification remains separate.
"""
from collections import deque
from threading import RLock

class LifetimeError(RuntimeError):pass

class Ticket:
    def __init__(self,pool,budget):
        self.pool=pool;self.budget=budget;self.buffers=();self.event=None
        self.armed=False;self.foreign_launch_entered=False;self.retired=False
    def arm(self,buffers):
        with self.pool.lock:
            self.pool.require(not self.retired and not self.armed and bool(buffers),'one pre-launch strong-reference arm')
            self.buffers=tuple(buffers);self.armed=True
    def entering_foreign_launch(self):
        with self.pool.lock:
            self.pool.require(self.armed and not self.foreign_launch_entered,'hold buffers before foreign launch')
            self.foreign_launch_entered=True
    def retain_extra(self,buffer):
        with self.pool.lock:
            self.pool.require(self.armed and not self.retired,'pending launch owns output too')
            self.buffers=(*self.buffers,buffer)
    def seal(self,event):
        with self.pool.lock:
            self.pool.require(self.foreign_launch_entered and self.event is None and not self.retired,'one actual recorded completion event')
            self.pool.require(callable(getattr(event,'query',None)) and callable(getattr(event,'synchronize',None)),'actual event API required')
            self.event=event

class KeepalivePool:
    def __init__(self,max_bytes,max_entries,poll_before_reserve=True):
        if type(max_bytes)is not int or max_bytes<=0 or type(max_entries)is not int or max_entries<=0 or type(poll_before_reserve)is not bool:raise LifetimeError('positive explicit limits and boolean polling policy')
        self.poll_before_reserve=poll_before_reserve
        self.max_bytes=max_bytes;self.max_entries=max_entries;self.lock=RLock()
        self.pending=deque();self.reserved_bytes=0;self.poisoned=False
        self.counters=dict(reservations=0,completed=0,pressure_waits=0,peak_bytes=0,peak_entries=0)
    def require(self,value,message):
        if not value:raise LifetimeError(message)
    def _retire(self,ticket):
        self.require(not ticket.retired,'retire exactly once')
        ticket.buffers=();ticket.retired=True;self.reserved_bytes-=ticket.budget
        self.counters['completed']+=1
    def reap(self):
        with self.lock:
            self.require(not self.poisoned,'failed foreign launch remains quarantined')
            while self.pending and self.pending[0].event is not None:
                t=self.pending[0]
                try:done=t.event.query()
                except BaseException:
                    self.poisoned=True;raise
                self.require(type(done)is bool,'event query is an actual boolean')
                if not done:break
                self.pending.popleft();self._retire(t)
    def reserve(self,bytes_required):
        with self.lock:
            self.require(type(bytes_required)is int and 0<bytes_required<=self.max_bytes,'one launch fits explicit keepalive bytes')
            if self.poll_before_reserve:self.reap()
            else:self.require(not self.poisoned,'failed foreign launch remains quarantined')
            while len(self.pending)>=self.max_entries or self.reserved_bytes+bytes_required>self.max_bytes:
                self.require(bool(self.pending),'bounded backpressure owns prior launch')
                t=self.pending[0];self.require(t.event is not None,'unsealed launch cannot be freed or waited blindly')
                self.counters['pressure_waits']+=1
                try:t.event.synchronize();done=t.event.query()
                except BaseException:
                    self.poisoned=True;raise
                self.require(done is True,'completed event required after pressure wait')
                self.pending.popleft();self._retire(t)
            t=Ticket(self,bytes_required);self.pending.append(t);self.reserved_bytes+=bytes_required
            self.counters['reservations']+=1
            self.counters['peak_bytes']=max(self.counters['peak_bytes'],self.reserved_bytes)
            self.counters['peak_entries']=max(self.counters['peak_entries'],len(self.pending))
            return t
    def abort_before_foreign_launch(self,ticket):
        with self.lock:
            self.require(ticket in self.pending and not ticket.foreign_launch_entered,'only never-submitted reservation can be canceled')
            self.pending.remove(ticket);self._retire(ticket)
    def quarantine(self,ticket):
        with self.lock:
            self.require(ticket in self.pending and ticket.armed,'retain potentially in-flight foreign buffers on failure')
            self.poisoned=True
    def finish(self):
        """Caller invokes outside timed work, before owned runtime teardown."""
        with self.lock:
            self.require(not self.poisoned,'quarantine needs owned device recovery; never free here')
            while self.pending:
                t=self.pending[0];self.require(t.event is not None,'cannot drain an unsealed foreign launch')
                try:t.event.synchronize();done=t.event.query()
                except BaseException:
                    self.poisoned=True;raise
                self.require(done is True,'actual completion before release')
                self.pending.popleft();self._retire(t)
            return dict(self.counters,pending=0,reserved_bytes=self.reserved_bytes)

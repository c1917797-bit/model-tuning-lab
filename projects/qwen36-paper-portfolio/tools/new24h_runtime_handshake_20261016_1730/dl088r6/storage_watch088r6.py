"""Read-only existing storage predicate, independent of the ARM critical path.

No ledger writes, no authority changes, no byte/stat/cap predicates replaced.
An initial synchronous check is required before this object is constructed.
"""
import threading,time

class Watch:
 def __init__(self,check,root,interval=2.0):
  self._check=check;self._root=root;self._interval=interval
  self._stop=threading.Event();self._lock=threading.Lock();self._error=None
  self._thread=threading.Thread(target=self._run,name='readonly-storage088r6',daemon=True)
 def start(self):self._thread.start()
 def _run(self):
  while not self._stop.is_set():
   try:self._check(self._root)
   except BaseException as exc:
    with self._lock:
     if self._error is None:self._error=exc
    return
   if self._stop.wait(self._interval):return
 def check(self):
  with self._lock:error=self._error
  if error is not None:raise error
 def close(self,deadline):
  self._stop.set();self._thread.join(max(0,deadline-time.monotonic()))
  if self._thread.is_alive():raise ValueError('read-only storage monitor did not quiesce within original cleanup deadline')
  self.check()

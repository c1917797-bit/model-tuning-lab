"""Supervised exact-code profiler. All callback errors are deferred until native success."""
from __future__ import annotations
import sys
import threading
from contextvars import ContextVar

def thread_profile():
    # Target CPython3.12 uses the public API. Host software-only regression may
    # run on CPython3.8: read its actual setprofile backing cell, never assume None.
    getter = getattr(threading, "getprofile", None)
    if getter is not None:
        return getter()
    if not hasattr(threading, "_profile_hook"):
        raise RuntimeError("thread profile ownership cannot be observed")
    return threading._profile_hook

class TraceFailure(RuntimeError):
    pass

class Supervisor:
    def __init__(self, code, observer):
        self.code, self.observer = code, observer
        self.active = ContextVar("fixed_admission_active", default=False)
        self.errors = []
        self.frames = {}
        self.calls = []
        self.returns = []
        # Store exact bound-method object once; sys.getprofile returns that object.
        self.callback = self._profile
        self.old_sys = None
        self.old_thread = None

    def install(self):
        if sys.getprofile() is not None or thread_profile() is not None:
            raise TraceFailure("existing profile hook; refuse to replace")
        self.old_sys, self.old_thread = sys.getprofile(), thread_profile()
        sys.setprofile(self.callback)
        threading.setprofile(self.callback)

    def restore(self):
        if sys.getprofile() is not self.callback or thread_profile() is not self.callback:
            raise TraceFailure("refuse to restore a replaced external hook")
        sys.setprofile(self.old_sys)
        threading.setprofile(self.old_thread)

    def _profile(self, frame, event, arg):
        if not self.active.get() or frame.f_code is not self.code or event not in ("call", "return"):
            return
        try:
            if event == "call":
                self.calls.append(id(frame))
                self.frames[id(frame)] = self.observer.before(frame)
            else:
                self.returns.append(id(frame))
                if id(frame) not in self.frames:
                    raise TraceFailure("native return has no supervised call")
                self.observer.after(frame, self.frames.pop(id(frame)))
                # Native _forward_core ordinarily returns None. Unwinding also emits
                # return(None): success is decided ONLY by the outer native call.
        except BaseException as error:
            self.errors.append((type(error).__name__, str(error)))
            try:
                self.observer.secondary_failure(event, error)
            except BaseException:
                pass  # Evidence failures can never replace the original native exception.

    def invoke(self, function, *args, **kwargs):
        if sys.getprofile() is not self.callback or thread_profile() is not self.callback:
            raise TraceFailure("profile hook replaced before native forward")
        self.errors, self.frames, self.calls, self.returns = [], {}, [], []
        token = self.active.set(True)
        try:
            result = function(*args, **kwargs)
        except BaseException as error:
            try:
                self.observer.native_failure(error, tuple(self.errors))
            except BaseException:
                pass
            try:
                self.restore()
            except BaseException:
                pass  # Preserve native exception, never overwrite an external hook.
            raise
        finally:
            self.active.reset(token)
        if sys.getprofile() is not self.callback:
            raise TraceFailure("profile hook removed during native forward")
        if self.errors:
            raise TraceFailure("diagnostic callback failed after native success: "+repr(self.errors[0]))
        if self.frames or len(self.calls) != 48 or self.calls != self.returns:
            # Calls and returns are sequential for this exact native GDN code.
            raise TraceFailure("incomplete supervised48 native call/return coverage")
        if self.observer.finish():
            self.restore()
        return result  # Identity-preserving, no replacement/cast/clone of native return.

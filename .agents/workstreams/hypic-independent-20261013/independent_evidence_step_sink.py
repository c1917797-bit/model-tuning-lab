"""Bounded source-bound evidence sink; model-step policy is unactivated."""
import json
import os
import re
import threading
from contextlib import contextmanager
from pathlib import Path


class SourceBoundEventSink:
    def __init__(self, path, *, manifest_sha256, max_events, max_bytes,
                 policy="per_event"):
        path = Path(path)
        if (policy not in ("per_event", "model_step")
                or not isinstance(manifest_sha256, str)
                or not re.fullmatch(r"[0-9a-f]{64}", manifest_sha256)
                or any(type(x) is not int or x <= 0 for x in (max_events, max_bytes))
                or not path.is_absolute() or not path.parent.is_dir()
                or path.parent.is_symlink()):
            raise ValueError("explicit bounded source identity/path/policy required")
        self.manifest_sha256 = manifest_sha256
        self.policy = policy
        self.max_events, self.max_bytes = max_events, max_bytes
        self.events = self.bytes = self.sync_count = 0
        self._lock = threading.RLock()
        self._closed = self._failed = self._dirty = False
        self._active = None
        self._fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                           | getattr(os, "O_NOFOLLOW", 0), 0o600)

    def _ready(self):
        if self._closed or self._failed:
            raise RuntimeError("evidence sink closed or failed")
        if self._active is not None and self._active[0] != threading.get_ident():
            raise RuntimeError("foreign thread in owned model step")

    def _sync(self):
        if self._dirty:
            try:
                os.fsync(self._fd)
            except BaseException:
                self._failed = True
                raise
            self.sync_count += 1
            self._dirty = False

    def __call__(self, event):
        with self._lock:
            self._ready()
            try:
                if not isinstance(event, dict):
                    raise ValueError("structured evidence event required")
                data = (json.dumps(dict(event, pid=os.getpid(),
                                       manifest_sha256=self.manifest_sha256),
                                   sort_keys=True, allow_nan=False) + "\n").encode()
                if self.events >= self.max_events or self.bytes + len(data) > self.max_bytes:
                    raise ValueError("evidence bound exceeded")
                view = memoryview(data)
                while view:
                    n = os.write(self._fd, view)
                    if n <= 0:
                        raise OSError("short evidence write")
                    self._dirty = True
                    view = view[n:]
                self.events += 1
                self.bytes += len(data)
                if self.policy == "per_event" or self._active is None:
                    self._sync()
            except BaseException:
                self._failed = True
                raise

    @contextmanager
    def model_step(self):
        with self._lock:
            self._ready()
            if self.policy != "model_step" or self._active is not None:
                raise RuntimeError("explicit nonnested model-step policy required")
            token = (threading.get_ident(), object())
            self._active = token
        try:
            yield
        finally:
            with self._lock:
                if self._active is not token or token[0] != threading.get_ident():
                    self._failed = True
                    raise RuntimeError("model-step fence ownership changed")
                try:
                    self._sync()
                finally:
                    self._active = None

    def flush(self):
        with self._lock:
            self._ready()
            self._sync()

    def close(self):
        with self._lock:
            if self._closed:
                return
            if self._active is not None:
                raise RuntimeError("cannot close an active model step")
            try:
                self._sync()
            finally:
                os.close(self._fd)
                self._closed = True

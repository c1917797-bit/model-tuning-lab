"""Opt-in, forward-scoped CPU metadata snapshots; no state/commit changes."""
from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy

_CURRENT = ContextVar("independent_step_metadata_cache", default=None)

@contextmanager
def metadata_scope(*, enabled=False):
    if type(enabled) is not bool:
        raise ValueError("explicit metadata cache boolean required")
    token = _CURRENT.set({} if enabled else None)
    try:
        yield
    finally:
        _CURRENT.reset(token)

def cpu_list(value):
    if value is None:
        raise ValueError("metadata tensor missing")
    cache = _CURRENT.get()
    # Inference tensors without a version counter cannot prove immutability.
    try:
        version = value._version
    except (AttributeError, RuntimeError):
        version = None
    if cache is None or version is None:
        return value.detach().cpu().tolist()
    key = id(value)
    previous = cache.get(key)
    if previous is not None and previous[0] is value and previous[1] == version:
        return deepcopy(previous[2])
    result = value.detach().cpu().tolist()
    # Keep the exact tensor alive; do not permit Python id reuse in this scope.
    cache[key] = (value, version, deepcopy(result))
    return result

class ForwardMetadataSnapshot:
    """Owned CPU snapshot for source-verified immutable forward metadata.

    Caller must prove builder completion and no metadata writes during this
    forward. Inference tensor identity alone is not an immutability proof.
    No object from this class may survive the enclosing model forward.
    """
    def __init__(self, requests, *, source_verified_immutable=False):
        if source_verified_immutable is not True:
            raise ValueError("source-verified forward immutability required")
        self.requests = tuple(requests)
        if not self.requests:
            raise ValueError("nonempty exact request identity required")
        self._entries = {}
        self._closed = False
        self.reads = 0
        self.hits = 0

    def read(self, metadata, field, requests):
        if self._closed or tuple(requests) != self.requests:
            raise ValueError("metadata snapshot forward/request identity mismatch")
        value = getattr(metadata, field, None)
        if value is None:
            raise ValueError("metadata tensor missing")
        key = (id(metadata), field)
        try:
            version = value._version
        except (AttributeError, RuntimeError):
            version = None
        previous = self._entries.get(key)
        if previous is not None:
            owner, tensor, old_version, frozen = previous
            if owner is not metadata or tensor is not value or old_version != version:
                raise ValueError("metadata changed during frozen forward")
            self.hits += 1
            return deepcopy(frozen)
        result = value.detach().cpu().tolist()
        self.reads += 1
        self._entries[key] = (metadata, value, version, deepcopy(result))
        return result

    def close(self):
        self._entries.clear()
        self._closed = True

_FORWARD = ContextVar("independent_forward_metadata_snapshot", default=None)

@contextmanager
def forward_snapshot_scope(requests, *, enabled=False):
    if type(enabled) is not bool:
        raise ValueError("explicit forward snapshot boolean required")
    if not enabled:
        yield
        return
    if _FORWARD.get() is not None:
        raise RuntimeError("nested forward metadata snapshot")
    snapshot = ForwardMetadataSnapshot(requests, source_verified_immutable=True)
    token = _FORWARD.set(snapshot)
    try:
        yield snapshot
    finally:
        snapshot.close()
        _FORWARD.reset(token)

def association_cpu_list(metadata, field, requests):
    snapshot = _FORWARD.get()
    identity = tuple((r.request_id, r.rank, r.step) for r in requests)
    if snapshot is None:
        value = getattr(metadata, field, None)
        if value is None:
            raise ValueError("metadata tensor missing")
        return value.detach().cpu().tolist()
    return snapshot.read(metadata, field, identity)

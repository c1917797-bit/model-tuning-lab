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

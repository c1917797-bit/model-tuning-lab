"""Default-off C2 block-table validation snapshots; not wired into serving.

A caller must independently source-prove metadata immutability for this exact
forward/group. CPU validation snapshots never replace native device block tables.
"""
import asyncio
from contextlib import contextmanager
from contextvars import ContextVar
import threading

from independent_step_metadata_cache import ForwardMetadataSnapshot

_CURRENT = ContextVar("independent_c2_block_table_snapshot", default=None)


def _owner():
    try:
        task = asyncio.current_task()
    except RuntimeError:
        task = None
    return threading.get_ident(), task


def _requests_and_rows(requests, request_rows):
    requests = tuple(requests)
    if not requests:
        raise ValueError("nonempty request/rank/step identity required")
    for item in requests:
        if (not isinstance(item, tuple) or len(item) != 3
                or not isinstance(item[0], str) or not item[0]
                or type(item[1]) is not int or item[1] < 0
                or type(item[2]) is not int or item[2] < 0):
            raise ValueError("exact request/rank/step identity required")
    if len({x[0] for x in requests}) != len(requests):
        raise ValueError("duplicate request identity")
    if len({x[1:] for x in requests}) != 1:
        raise ValueError("one rank and step per forward required")
    rows = tuple(range(len(requests))) if request_rows is None else tuple(request_rows)
    if (len(rows) != len(requests) or len(set(rows)) != len(rows)
            or any(type(row) is not int or row < 0 for row in rows)):
        raise ValueError("unique exact request-row mapping required")
    return requests, rows


def _tensor_identity(tensor):
    try:
        version = tensor._version
    except (AttributeError, RuntimeError):
        version = None
    return (version, tuple(tensor.shape), tuple(tensor.stride()),
            tensor.dtype, tensor.device, tensor.data_ptr())


class _C2BlockTableSnapshot:
    def __init__(self, requests, request_rows, *, source_verified_immutable):
        if source_verified_immutable is not True:
            raise ValueError("source-verified forward/group immutability required")
        self.requests, rows = _requests_and_rows(requests, request_rows)
        self._rows = dict(zip(rows, self.requests))
        self._snapshot = ForwardMetadataSnapshot(
            self.requests, source_verified_immutable=source_verified_immutable)
        self._owner = _owner()
        self._native = None
        self._tensor = None
        self._identity = None
        self._closed = False

    @property
    def reads(self):
        return self._snapshot.reads

    @property
    def hits(self):
        return self._snapshot.hits

    def _validate(self, native):
        if (self._closed or _CURRENT.get() is not self
                or _owner() != self._owner):
            raise ValueError("C2 snapshot outside owning forward/context")
        table = getattr(native, "block_tables", None)
        if table is None or table.ndim != 2:
            raise ValueError("two-dimensional native block table required")
        identity = _tensor_identity(table)
        if self._native is None:
            self._native, self._tensor, self._identity = native, table, identity
        elif (native is not self._native or table is not self._tensor
              or identity != self._identity):
            raise ValueError("native metadata/block table changed during forward")
        return table

    def read(self, native, request_row, block_count, *, request_identity):
        table = self._validate(native)
        if (type(request_row) is not int or request_row not in self._rows
                or not isinstance(request_identity, tuple) or len(request_identity) != 3
                or type(request_identity[1]) is not int
                or type(request_identity[2]) is not int
                or request_identity != self._rows[request_row]):
            raise ValueError("C2 snapshot request/rank/step/row mismatch")
        if (request_row >= table.shape[0] or type(block_count) is not int
                or not 1 <= block_count <= table.shape[1]):
            raise ValueError("C2 snapshot block-table row/count out of bounds")
        # Read the complete table once. Never cache only a short first window:
        # a later window still compares every required live block id.
        values = self._snapshot.read(native, "block_tables", self.requests)
        self._validate(native)
        result = values[request_row][:block_count]
        if len(result) != block_count:
            raise ValueError("C2 snapshot block-table coverage incomplete")
        return tuple(int(x) for x in result)

    def close(self):
        self._closed = True
        self._snapshot.close()
        self._rows.clear()
        self._native = self._tensor = self._identity = self._owner = None


@contextmanager
def c2_block_table_snapshot_scope(requests, *, request_rows=None, enabled=False,
                                  source_verified_immutable=False):
    """Own one immutable attention-group snapshot for one exact model forward.

    Rows default to request order; callers with another native row layout must
    supply the exact mapping. Scope objects cannot be borrowed by another thread
    or asyncio task, even when that task inherits the ContextVar.
    """
    if type(enabled) is not bool:
        raise ValueError("explicit C2 snapshot boolean required")
    if not enabled:
        yield None
        return
    if _CURRENT.get() is not None:
        raise RuntimeError("nested C2 block-table snapshot")
    snapshot = _C2BlockTableSnapshot(
        requests, request_rows, source_verified_immutable=source_verified_immutable)
    token = _CURRENT.set(snapshot)
    try:
        yield snapshot
    finally:
        snapshot.close()
        _CURRENT.reset(token)

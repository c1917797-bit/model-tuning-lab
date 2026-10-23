"""Default-off, forward-owned C2 block-table validation snapshots.

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

    def bind_native(self, native):
        """Bind the source-verified group object before any layer can use it."""
        self._validate(native)

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


def active_c2_block_table_snapshot():
    """Return only the current scope; read() still enforces task/thread owner."""
    return _CURRENT.get()


# Exact source contract for the selected official image. Read, do not import,
# nested runtime modules during the worker import hook (avoids import cycles).
_SOURCE_FILES = {
    "vllm": {
        "model_executor/models/qwen3_5.py": "04f3de5372973770d71c5c05f2e8a5e221ec52b62cca7a1e302d9201b61b8adc",
        "model_executor/models/qwen3_next.py": "8d614ce262ab9340585f9a2ad4ab117228f076e3672fcb5f04930ff0a38223ae",
        "forward_context.py": "1c6fa51e9a02a120fed5e7357afb1190516cbdfefd1c644dfcd860603f1527c5",
        "config/compilation.py": "301f785491044b4428aec617b8a98161ab7ffc424fc2bfb0f2ab26bed6ee6913",
        "compilation/decorators.py": "dd7167637a478aeaea3f2410a727ddefc702bda1d9bf632831c2a8b4811ebb1e",
    },
    "vllm_ascend": {
        "worker/model_runner_v1.py": "94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968",
        "attention/attention_v1.py": "80005aba42bcf61247cc0d91502a0f1338194a4b38dd82bc521f6d3c84958390",
        "worker/block_table.py": "8f77809c12af3bd9d56974edbbe5c792995f2620aadfe62411806f2e68d2ef0a",
    },
}


def verify_c2_snapshot_runtime_contract():
    """Verify pinned source bytes only; forward eligibility is checked later."""
    import hashlib
    from pathlib import Path
    import sys
    for package, files in _SOURCE_FILES.items():
        root_module = sys.modules.get(package)
        origin = getattr(root_module, "__file__", None)
        if not origin:
            raise ValueError("C2 snapshot live package origin missing")
        root = Path(origin).resolve().parent
        for relative, expected in files.items():
            path = root / relative
            module_name = package + "." + relative[:-3].replace("/", ".")
            imported = sys.modules.get(module_name)
            if imported is not None:
                actual = getattr(imported, "__file__", None)
                if not actual or Path(actual).resolve() != path.resolve():
                    raise ValueError("C2 snapshot imported source path drift")
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError("C2 snapshot official source drift: " + relative)


def validate_c2_snapshot_forward(selection, context, runtime):
    """Admit only the already captured ordinary eager, single-group forward.

    Native prepare writes the persistent table before forward; no snapshot
    survives that forward. Version-less inference tensors are NOT a proof.
    The pinned source path, real runtime capture and supported mode jointly
    delimit the candidate. The device trial must still validate stream/order.
    """
    mode = getattr(context, "cudagraph_runtime_mode", None)
    if (getattr(mode, "name", None) != "NONE" or getattr(mode, "value", None) != 0
            or getattr(context, "ubatch_slices", "missing") is not None):
        raise ValueError("C2 snapshot requires ordinary eager non-ubatch forward")
    metadata = getattr(context, "attn_metadata", None)
    if type(metadata) is not dict or runtime is None:
        raise ValueError("C2 snapshot needs exact native metadata/runtime capture")
    plans = tuple(selection.plans)
    identities = tuple((p.request_id, p.rank, p.step) for p in plans)
    _requests_and_rows(identities, None)
    if (tuple(p.request_id for p in plans) != tuple(runtime.request_ids)
            or any((p.rank, p.step) != (runtime.rank, runtime.step) for p in plans)
            or runtime.prompt_logprobs or selection.prompt_logprobs
            or tuple(selection.cache_slices) != tuple(runtime.cache_slices)
            or tuple(selection.attention_groups) != tuple(runtime.attention_groups)
            or tuple(selection.writable_kv_slots) != tuple(runtime.writable_kv_slots)):
        raise ValueError("C2 snapshot selection/native capture drift")
    groups = tuple(selection.attention_groups)
    if len(groups) != 1:
        raise ValueError("C2 snapshot supports one exact attention group")
    group, names = groups[0]
    names = tuple(names)
    if not names or len(set(names)) != len(names) or any(n not in metadata for n in names):
        raise ValueError("C2 snapshot full-attention metadata missing")
    native = metadata[names[0]]
    if any(metadata[name] is not native for name in names):
        raise ValueError("C2 snapshot attention group object drift")
    if (native.causal is not True or native.prefill is not None
            or native.decode_meta is not None or native.kvcomp_metadata is not None
            or native.num_decode_tokens != native.num_decodes
            or native.num_decodes < 0 or native.num_prefills < 1):
        raise ValueError("C2 snapshot unsupported CP/spec/metadata path")
    rows = []
    for plan in plans:
        caches = [c for c in selection.cache_slices
                  if c.request_id == plan.request_id and c.group == group]
        if len(caches) != 1 or (caches[0].rank, caches[0].step) != (plan.rank, plan.step):
            raise ValueError("C2 snapshot request/group capture mismatch")
        rows.append(caches[0].row)
    _requests_and_rows(identities, tuple(rows))
    return identities, tuple(rows), native

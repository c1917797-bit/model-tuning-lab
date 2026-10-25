"""Real selected-prefill snapshot ownership around unchanged C1/C2 helpers.

This new adapter replaces the old global-NONE assumption with the source-owned
router's per-call NONE/skip_compiled proof. It never changes config flags.
No service manifest currently activates it.
"""
from contextvars import ContextVar
from dataclasses import dataclass
import hashlib
import inspect
from pathlib import Path
import sys
import types

from .source_contract import verify_raw_function


def verify_support(module, expected):
    """Bind the actual imported unchanged helper bytes and source code."""
    if (type(expected) is not str or len(expected) != 64
            or type(module) is not types.ModuleType
            or sys.modules.get(module.__name__) is not module):
        raise ValueError("explicit frozen support source binding required")
    source = Path(module.__file__).resolve().read_bytes()
    if hashlib.sha256(source).hexdigest() != expected:
        raise ValueError("frozen independent helper source drift")
    return source


@dataclass
class PrefillBridge:
    forward: object
    assert_ownership: object
    stop: object


def install_prefill_bridge(native, *, enabled=False, verify_source=None,
                           select=None, emit=None, metadata_snapshot=False,
                           source_bindings=None, assert_entry=None):
    if not enabled:
        return None
    if not all(callable(x) for x in (verify_source, select, emit, assert_entry)):
        raise ValueError("complete selective prefill ownership callbacks required")
    if type(source_bindings) is not dict:
        raise ValueError("explicit frozen helper source map required")
    import independent_compact_model_hook as helper
    import independent_c2_block_table_snapshot as snapshot
    import independent_runner_context as runner
    from vllm.forward_context import get_forward_context
    from vllm.config.compilation import CUDAGraphMode
    for module, functions in (
            (helper, ("install_compact_model",)),
            (snapshot, ("validate_c2_snapshot_forward",
                        "c2_block_table_snapshot_scope",
                        "active_c2_block_table_snapshot")),
            (runner, ())):
        source = verify_support(module, source_bindings.get(module.__name__))
        for name in functions:
            function = getattr(module, name)
            # contextmanager is an exact stdlib-owned decorator; verify its
            # wrapped generator separately, without arbitrary unwrap traversal.
            if name == "c2_block_table_snapshot_scope":
                import contextlib
                if (type(function) is not types.FunctionType
                        or function.__code__ is not contextlib.contextmanager(
                            lambda: None).__code__
                        or function.__globals__ is not vars(contextlib)
                        or function.__code__.co_freevars != ("func",)
                        or len(function.__closure__ or ()) != 1):
                    raise ValueError("exact stdlib contextmanager wrapper required")
                raw = function.__closure__[0].cell_contents
                if getattr(function, "__wrapped__", None) is not raw:
                    raise ValueError("snapshot contextmanager wrapper identity drift")
                verify_raw_function(module, source, raw, name=name)
            else:
                verify_raw_function(module, source, function, name=name)
    cls = native.model_class
    if inspect.getattr_static(cls, "forward") is not native.model_receipt.forward:
        raise ValueError("prefill bridge must capture untouched native model forward")
    selection = ContextVar("graph_candidate_selection", default=None)
    active_snapshot = ContextVar("graph_candidate_snapshot", default=None)
    original_install = helper.install_compact_model
    original_validate = snapshot.validate_c2_snapshot_forward
    original_scope = snapshot.c2_block_table_snapshot_scope
    original_active = snapshot.active_c2_block_table_snapshot
    runtime_context = runner.CURRENT_RUNTIME_SNAPSHOT

    def selected_once(*args, **kwargs):
        current = selection.get()
        if current is None:
            raise RuntimeError("compact helper entered without selected prefill bridge")
        return current

    def audited_emit(event):
        if event.get("event") != "compact_model_rows_completed":
            emit(event)
            return
        evidence = active_snapshot.get()
        if evidence is None or original_active() is not evidence:
            raise RuntimeError("model completion lacks owning real C2 snapshot")
        # The unchanged helper has snapshot=False internally because the new
        # outer adapter owns the real scope. Report that provenance explicitly.
        emit(dict(event, c2_block_table_snapshot=True,
                  c2_block_table_snapshot_reads=evidence.reads,
                  c2_block_table_snapshot_hits=evidence.hits,
                  c2_snapshot_scope_owner="graph_candidate.prefill_bridge",
                  inner_helper_c2_snapshot=False))

    stop_inner = original_install(cls, enabled=True, verify_source=verify_source,
        select=selected_once, emit=audited_emit, metadata_snapshot=metadata_snapshot,
        c2_block_table_snapshot=False)
    inner = inspect.getattr_static(cls, "forward")
    if (getattr(inner, "_independent_compact_model_owned", False) is not True
            or getattr(inner, "__wrapped__", None) is not native.model_receipt.forward):
        stop_inner()
        raise ValueError("unchanged compact helper ownership drift")

    scope_raw = original_scope.__closure__[0].cell_contents
    support_functions = (original_install, original_validate, original_scope,
                         scope_raw, original_active, inner)
    support_receipts = tuple((f.__code__, f.__globals__, f.__defaults__, f.__kwdefaults__)
                             for f in support_functions)

    def assert_owned():
        native.assert_saved_native()
        if (helper.install_compact_model is not original_install
                or snapshot.validate_c2_snapshot_forward is not original_validate
                or snapshot.c2_block_table_snapshot_scope is not original_scope
                or snapshot.active_c2_block_table_snapshot is not original_active
                or runner.CURRENT_RUNTIME_SNAPSHOT is not runtime_context
                or getattr(inner, "__wrapped__", None) is not native.model_receipt.forward
                or original_scope.__closure__[0].cell_contents is not scope_raw
                or getattr(original_scope, "__wrapped__", None) is not scope_raw):
            raise ValueError("selective prefill support ownership changed")
        for function, receipt in zip(support_functions, support_receipts):
            if (function.__code__ is not receipt[0] or function.__globals__ is not receipt[1]
                    or function.__defaults__ is not receipt[2]
                    or function.__kwdefaults__ is not receipt[3]):
                raise ValueError("selective prefill support callable changed")

    def forward(model, *args, **kwargs):
        assert_entry(model)
        assert_owned()
        if "forward" in vars(model):
            raise ValueError("instance model forward override")
        context = get_forward_context()
        # Stronger exact enum identity complements unchanged full snapshot
        # validator, which also retains metadata/lease/request-row checks.
        if (context.cudagraph_runtime_mode is not CUDAGraphMode.NONE
                or context.ubatch_slices is not None
                or context.skip_compiled is not True):
            raise ValueError("selected prefill requires actual compiler-bypassed NONE")
        chosen = select(model, *args, **kwargs)
        if chosen is None:
            # Public producer and unselected NONE fallback retain native model
            # execution; the unchanged producer/layer hooks remain installed.
            return native.model_receipt.forward(model, *args, **kwargs)
        identities, rows, native_metadata = original_validate(
            chosen, context, runtime_context.get())
        token = selection.set(chosen)
        try:
            with original_scope(identities, request_rows=rows, enabled=True,
                                source_verified_immutable=True) as evidence:
                evidence.bind_native(native_metadata)
                evidence_token = active_snapshot.set(evidence)
                try:
                    return inner(model, *args, **kwargs)
                finally:
                    active_snapshot.reset(evidence_token)
        finally:
            selection.reset(token)

    def stop():
        # The caller must first remove its outer entry/model wrapper. Never
        # overwrite an unknown slot while unwinding this inner helper.
        if inspect.getattr_static(cls, "forward") is not inner:
            raise RuntimeError("remove selective outer model entry before bridge")
        stop_inner()

    return PrefillBridge(forward, assert_owned, stop)

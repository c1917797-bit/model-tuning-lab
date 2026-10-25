"""Opt-in candidate assembly for the new explicit graph worker loader.

This does not modify framework or existing independent source bytes. A new
reviewed manifest/launcher and bounded device contract are still required.
"""
from contextlib import ExitStack
from threading import Lock
import inspect
import sys
import types

from .entry_router import SelectiveEntryRouter
from .prefill_bridge import install_prefill_bridge, verify_support
from .source_contract import capture_native_bundle, _codes

_STARTUP_LOCK = Lock()


def _known_wrapper(function, module_name, qualname, bindings, *, wrapped=None):
    module = sys.modules.get(module_name)
    source = verify_support(module, bindings.get(module_name))
    if (type(function) is not types.FunctionType
            or function.__globals__ is not vars(module)
            or function.__code__.co_qualname != qualname):
        raise ValueError("exact known independent hook owner required")
    compiled = compile(source, function.__code__.co_filename, "exec", dont_inherit=True,
                       optimize=sys.flags.optimize)
    expected = [c for c in _codes(compiled) if c.co_qualname == qualname]
    if len(expected) != 1 or function.__code__ != expected[0]:
        raise ValueError("known independent hook source/code drift")
    if getattr(function, "__wrapped__", None) is not wrapped:
        raise ValueError("known independent hook native chain drift")
    return function


def _closure(function, name):
    values = dict(zip(function.__code__.co_freevars,
                      (cell.cell_contents for cell in function.__closure__ or ())))
    if name not in values:
        raise ValueError("known independent hook closure missing")
    return values[name]


def activate_graph_candidate(config, *, enabled=False, emit=None,
                             source_bindings=None, request_progress_limit=128):
    """Assemble only the narrow source-bound selective profile.

    Default disabled does not import any runtime/algorithm. Enabled callers
    supply the immutable old-package source hashes keyed by module name.
    This factory is not connected to the frozen package or any service.
    """
    if not enabled:
        return lambda: None
    if not callable(emit) or type(source_bindings) is not dict:
        raise ValueError("explicit source-bound enabled candidate required")
    if (type(config) is not dict or config.get("c2_layer_completion_barrier") is not True
            or config.get("c2_layer_finite_gate") is not True
            or config.get("c2_block_table_snapshot") is not True):
        raise ValueError("candidate retains actual C2 barrier/finite/snapshot checks")
    if not _STARTUP_LOCK.acquire(blocking=False):
        raise RuntimeError("another graph candidate startup is active")
    resources = ExitStack()
    original_install = None
    helper = None
    bridge_box = []
    router_box = []
    try:
        # The official registry must finish before this explicit activation.
        import vllm_ascend.ops
        from vllm.config.compilation import CompilationMode, CUDAGraphMode
        from vllm.forward_context import ForwardContext, BatchDescriptor, get_forward_context
        import torch
        import independent_compact_activation as base
        import independent_compact_model_hook as helper
        from .source_contract import verify_raw_function
        base_source = verify_support(base, source_bindings.get(base.__name__))
        verify_raw_function(base, base_source, base.activate_compact_hypic,
                            name="activate_compact_hypic")
        native = capture_native_bundle()
        original_install = helper.install_compact_model

        def assert_entry(model):
            if (len(router_box) != 1 or router_box[0]._entry_model is not model
                    or router_box[0]._native_decode):
                raise RuntimeError("prefill lacks source-owned selective entry")

        def install_bridge(cls, *, enabled=False, verify_source=None, select=None,
                           emit=None, metadata_snapshot=False,
                           c2_block_table_snapshot=False):
            if (not enabled or cls is not native.model_class
                    or c2_block_table_snapshot is not True or bridge_box
                    or helper.install_compact_model is not install_bridge):
                raise ValueError("unexpected model installer request")
            # Startup-only interception of this one known export. Restore the
            # exact source-verified installer while constructing its helper;
            # no running service or framework function is changed in place.
            helper.install_compact_model = original_install
            try:
                bridge = install_prefill_bridge(native, enabled=True,
                    verify_source=verify_source, select=select, emit=emit,
                    metadata_snapshot=metadata_snapshot,
                    source_bindings=source_bindings, assert_entry=assert_entry)
                bridge_box.append(bridge)
            finally:
                if helper.install_compact_model is not original_install:
                    raise RuntimeError("model installer ownership changed during startup")
                helper.install_compact_model = install_bridge
            return bridge.stop

        helper.install_compact_model = install_bridge
        try:
            stop_base = base.activate_compact_hypic(config, enabled=True, emit=emit,
                request_progress_limit=request_progress_limit)
        finally:
            if helper.install_compact_model is not install_bridge:
                raise RuntimeError("model installer export ownership changed")
            helper.install_compact_model = original_install
        resources.callback(stop_base)
        if len(bridge_box) != 1:
            raise ValueError("actual selected-prefill bridge not installed")
        bridge = bridge_box[0]
        gdn = inspect.getattr_static(native.gdn_class, "_forward_core")
        producer = getattr(gdn, "__wrapped__", None)
        c2 = inspect.getattr_static(native.c2_class, "forward")
        _known_wrapper(gdn, "independent_compact_gdn_hook",
            "install_compact_gdn.<locals>.wrapped", source_bindings, wrapped=producer)
        _known_wrapper(producer, "independent_public_gdn_hook",
            "install_public_gdn_producer.<locals>.wrapped_core",
            source_bindings, wrapped=native.gdn)
        _known_wrapper(c2, "experimental_c2_layer_barrier",
            "install_compact_c2.<locals>.wrapped", source_bindings, wrapped=native.c2)
        gdn_module = sys.modules["vllm_ascend.ops.gdn"]
        chunk = gdn_module.chunk_gated_delta_rule
        _known_wrapper(chunk, "independent_public_gdn_hook",
            "install_public_gdn_producer.<locals>.wrapped_chunk", source_bindings)
        if _closure(chunk, "original_chunk") is not native.chunk:
            raise ValueError("known producer chunk native closure changed")
        known = (gdn, producer, c2, chunk)
        receipts = tuple((f.__code__, f.__globals__, f.__defaults__, f.__kwdefaults__) for f in known)
        expected_slots = []

        def assert_owned():
            native.assert_saved_native()
            bridge.assert_ownership()
            if (helper.install_compact_model is not original_install
                    or gdn_module.chunk_gated_delta_rule is not chunk
                    or getattr(gdn, "__wrapped__", None) is not producer
                    or getattr(producer, "__wrapped__", None) is not native.gdn
                    or getattr(c2, "__wrapped__", None) is not native.c2
                    or _closure(chunk, "original_chunk") is not native.chunk):
                raise ValueError("known independent native/publication chain changed")
            for function, receipt in zip(known, receipts):
                if (function.__code__ is not receipt[0] or function.__globals__ is not receipt[1]
                        or function.__defaults__ is not receipt[2]
                        or function.__kwdefaults__ is not receipt[3]):
                    raise ValueError("known independent hook callable changed")
            for cls, name, expected in expected_slots:
                if inspect.getattr_static(cls, name) is not expected:
                    raise ValueError("selective graph entry slot ownership changed")

        router = SelectiveEntryRouter(model_class=native.model_class,
            native_call=native.call, native_forward=native.model_receipt.forward,
            compilation_mode=CompilationMode, graph_mode=CUDAGraphMode,
            forward_context_class=ForwardContext, batch_descriptor_class=BatchDescriptor,
            get_context=get_forward_context, is_compiling=torch.compiler.is_compiling,
            assert_ownership=assert_owned, prefill_forward=bridge.forward)
        router_box.append(router)
        stop_router = router.install(enabled=True, layers=(
            (native.gdn_class, "_forward_core", native.gdn, gdn),
            (native.c2_class, "forward", native.c2, c2)))
        resources.callback(stop_router)
        expected_slots.extend((cls, name, inspect.getattr_static(cls, name)) for cls, name in (
            (native.model_class, "__call__"), (native.model_class, "forward"),
            (native.gdn_class, "_forward_core"), (native.c2_class, "forward")))
        assert_owned()
        emit({"event": "graph_candidate_hooks_installed",
              "profile": "selective-prefill-native-decode-v1",
              "default_disabled": True, "native_decode_before_pic_contextvars": True,
              "selected_prefill_real_snapshot_owner": True,
              "compiler_or_graph_execution_proven": False,
              "scope": "source-bound installation; device proof pending"})
        return resources.pop_all().close
    except BaseException:
        resources.close()
        raise
    finally:
        if helper is not None and original_install is not None:
            # Do not overwrite a foreign export on any exceptional startup.
            current = helper.install_compact_model
            if current is original_install:
                pass
        _STARTUP_LOCK.release()

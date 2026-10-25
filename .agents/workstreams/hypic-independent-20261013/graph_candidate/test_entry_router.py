"""Focused CPU controls only. No official runtime imports or NPU work."""
from dataclasses import dataclass
from enum import Enum
import hashlib
from pathlib import Path
from types import SimpleNamespace, ModuleType
import sys
import tempfile
import unittest
from unittest.mock import patch
import torch

from graph_candidate.entry_router import SelectiveEntryRouter
from graph_candidate import source_contract


class CM(Enum):
    NONE = 0
    VLLM_COMPILE = 3


class GM(Enum):
    NONE = 0
    FULL = 2
    PIECEWISE = 1
    FULL_DECODE_ONLY = (2, 0)


@dataclass
class Descriptor:
    num_tokens: int = 2
    num_reqs: int = 2
    uniform: bool = True
    has_lora: bool = False
    num_active_loras: int = 0


@dataclass
class Context:
    cudagraph_runtime_mode: object = GM.NONE
    batch_descriptor: object = None
    ubatch_slices: object = None
    skip_compiled: bool = False
    attn_metadata: object = None


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.context = Context()
        self.compiling = False
        self.throw = False
        self.ownership_ok = True
        events = self.events

        class Layer:
            def forward(layer, x):
                return x + 2

        class Model:
            def forward(self, input_ids, positions, intermediate_tensors=None, inputs_embeds=None):
                return self.layer.forward(input_ids) * 3

            def __call__(model, x):
                events.append(("native_call", self.context.skip_compiled))
                return model.forward(x, None)

        self.Layer, self.Model = Layer, Model
        self.native_layer = Layer.forward
        self.native_forward = Model.forward
        self.native_call = Model.__call__

        def hypic_layer(layer, x):
            events.append("PIC_layer")
            return self.native_layer(layer, x)

        Layer.forward = hypic_layer
        self.hypic_layer = hypic_layer

        def prefill(model, x, *unused, **kwargs):
            events.append("PIC_model")
            if self.throw:
                raise ValueError("prefill failed")
            return self.native_forward(model, x, *unused, **kwargs)

        def assert_owned():
            if not self.ownership_ok:
                raise ValueError("ownership changed")

        self.router = SelectiveEntryRouter(
            model_class=Model, native_call=self.native_call,
            native_forward=self.native_forward, compilation_mode=CM, graph_mode=GM,
            forward_context_class=Context, batch_descriptor_class=Descriptor,
            get_context=lambda: self.context, is_compiling=lambda: self.compiling,
            assert_ownership=assert_owned, prefill_forward=prefill)
        self.model = Model()
        self.model.layer = Layer()
        config = SimpleNamespace(mode=CM.VLLM_COMPILE, cudagraph_mode=GM.FULL_DECODE_ONLY)
        self.model.compilation_config = config
        self.model.do_not_compile = False
        self.model.vllm_config = SimpleNamespace(
            compilation_config=config, model_config=SimpleNamespace(enforce_eager=False),
            parallel_config=SimpleNamespace(tensor_parallel_size=4,
                pipeline_parallel_size=1, data_parallel_size=1),
            speculative_config=None, lora_config=None)
        self.stop = None

    def install(self):
        self.stop = self.router.install(enabled=True,
            layers=((self.Layer, "forward", self.native_layer, self.hypic_layer),))

    def tearDown(self):
        if self.stop is not None and self.router._installed:
            self.stop()

    def full(self):
        self.context = Context(GM.FULL, Descriptor(), attn_metadata={
            "GDN": SimpleNamespace(num_prefills=0), "FA": SimpleNamespace(num_prefills=0)})

    def test_disabled_does_not_touch_slots(self):
        before = dict(vars(self.Model)), dict(vars(self.Layer))
        self.router.install()
        self.assertEqual(before, (dict(vars(self.Model)), dict(vars(self.Layer))))

    def test_none_prefill_uses_official_skip_then_restores(self):
        self.install()
        self.assertEqual(self.model(2), 12)
        self.assertEqual(self.events, [("native_call", True), "PIC_model", "PIC_layer"])
        self.assertIs(self.context.skip_compiled, False)
        self.assertIs(self.model.do_not_compile, False)
        self.assertIs(self.model.compilation_config.mode, CM.VLLM_COMPILE)

    def test_mixed_and_public_use_same_none_route(self):
        self.install()
        # Distinct semantic callers all enter actual NONE; selection remains the
        # HYPIC adapter's responsibility, never descriptor-label based here.
        for caller in ("private_prefill", "mixed", "public_producer"):
            self.events.clear()
            self.model(1)
            self.assertEqual(self.events[0], ("native_call", True), caller)
            self.assertIn("PIC_model", self.events)

    def test_exception_restores_skip_and_gate(self):
        self.install()
        self.throw = True
        with self.assertRaisesRegex(ValueError, "prefill failed"):
            self.model(2)
        self.assertFalse(self.context.skip_compiled)
        self.assertFalse(self.router._native_decode)
        self.assertIsNone(self.router._entry_model)
        self.throw = False
        self.assertEqual(self.model(1), 9)

    def test_prior_skip_true_is_preserved_on_none(self):
        self.context.skip_compiled = True
        self.install()
        self.model(1)
        self.assertTrue(self.context.skip_compiled)

    def test_full_decode_calls_native_before_pic(self):
        self.full()
        self.install()
        self.assertEqual(self.model(2), 12)
        self.assertEqual(self.events, [("native_call", False)])
        self.assertFalse(self.context.skip_compiled)
        self.assertFalse(self.router._native_decode)

    def test_wrong_actual_mode_fails(self):
        self.model.compilation_config.mode = CM.NONE
        self.install()
        with self.assertRaisesRegex(ValueError, "VLLM_COMPILE"):
            self.model(1)
        self.assertEqual(self.events, [])

    def test_fake_mode_label_fails(self):
        self.model.compilation_config.mode = SimpleNamespace(name="VLLM_COMPILE")
        self.install()
        with self.assertRaises(ValueError):
            self.model(1)

    def test_faked_do_not_compile_fails(self):
        self.model.do_not_compile = True
        self.install()
        with self.assertRaises(ValueError):
            self.model(1)

    def test_enforce_eager_fails(self):
        self.model.vllm_config.model_config.enforce_eager = True
        self.install()
        with self.assertRaises(ValueError):
            self.model(1)

    def test_full_mixed_descriptor_fails(self):
        self.full()
        self.context.batch_descriptor.uniform = False
        self.install()
        with self.assertRaisesRegex(ValueError, "pure one-token"):
            self.model(1)

    def test_full_multi_token_descriptor_fails(self):
        self.full()
        self.context.batch_descriptor.num_tokens = 4
        self.install()
        with self.assertRaises(ValueError):
            self.model(1)

    def test_full_with_actual_prefill_metadata_fails(self):
        self.full()
        self.context.attn_metadata["GDN"].num_prefills = 1
        self.install()
        with self.assertRaisesRegex(ValueError, "zero-prefill"):
            self.model(1)

    def test_fake_native_context_fails(self):
        self.context = SimpleNamespace(**vars(self.context))
        self.install()
        with self.assertRaisesRegex(ValueError, "ForwardContext"):
            self.model(1)

    def test_piecewise_fails(self):
        self.context.cudagraph_runtime_mode = GM.PIECEWISE
        self.install()
        with self.assertRaises(ValueError):
            self.model(1)

    def test_ubatch_fails(self):
        self.context.ubatch_slices = []
        self.install()
        with self.assertRaises(ValueError):
            self.model(1)

    def test_full_existing_skip_rejected(self):
        self.full()
        self.context.skip_compiled = True
        self.install()
        with self.assertRaises(ValueError):
            self.model(1)
        self.assertTrue(self.context.skip_compiled)

    def test_unowned_compiler_entry_fails(self):
        self.install()
        self.compiling = True
        with self.assertRaisesRegex(RuntimeError, "unowned compiled"):
            self.model(1)
        with self.assertRaisesRegex(RuntimeError, "compiling prefill"):
            self.model.forward(1, None)
        with self.assertRaisesRegex(RuntimeError, "compiling prefill"):
            self.model.layer.forward(1)

    def test_direct_model_and_layer_entry_fail(self):
        self.install()
        with self.assertRaisesRegex(RuntimeError, "bypassed"):
            self.model.forward(1, None)
        with self.assertRaisesRegex(RuntimeError, "bypassed"):
            self.model.layer.forward(1)

    def test_changed_native_ownership_fails_before_execution(self):
        self.install()
        self.ownership_ok = False
        with self.assertRaisesRegex(ValueError, "ownership changed"):
            self.model(1)
        self.assertEqual(self.events, [])

    def test_rollback_restores_exact_slots(self):
        self.install()
        self.stop()
        self.stop = None
        self.assertIs(self.Model.forward, self.native_forward)
        self.assertIs(self.Model.__call__, self.native_call)
        self.assertIs(self.Layer.forward, self.hypic_layer)

    def test_rollback_does_not_overwrite_foreign_slot(self):
        self.install()
        owned = self.Model.forward
        foreign = lambda model, x: x
        self.Model.forward = foreign
        with self.assertRaisesRegex(RuntimeError, "ownership changed"):
            self.stop()
        self.assertIs(self.Model.forward, foreign)
        self.Model.forward = owned

    def test_failed_install_restores_prior_layer(self):
        class Other:
            def forward(self, x):
                return x
        before = self.Layer.forward
        with self.assertRaisesRegex(ValueError, "slot changed"):
            self.router.install(enabled=True, layers=(
                (self.Layer, "forward", self.native_layer, self.hypic_layer),
                (Other, "forward", Other.forward, lambda self, x: x)))
        self.assertIs(self.Layer.forward, before)

    def test_native_decode_trace_avoids_pic_contextvar(self):
        # Real CPU Dynamo fullgraph negative/positive control, not NPU/CANN.
        from contextvars import ContextVar
        pic = ContextVar("must_not_enter_pic", default=0)
        self.router.is_compiling = torch.compiler.is_compiling
        def forbidden_prefill(model, x, *unused, **kwargs):
            pic.set(pic.get() + 1)
            raise AssertionError("PIC traced during decode")
        self.router.prefill_forward = forbidden_prefill
        self.full()
        compiled = torch.compile(lambda x: self.model.forward(x, None),
                                 backend="eager", fullgraph=True)
        def compiler_owner(model, x):
            if self.context.skip_compiled:
                return model.forward(x)
            return compiled(x)
        self.router.native_call = compiler_owner
        self.install()
        x = torch.tensor([1.0, 2.0])
        self.assertTrue(torch.equal(self.model(x), (x + 2) * 3))
        self.assertEqual(pic.get(), 0)
        self.assertEqual(self.events, [])
        self.assertFalse(self.router._native_decode)

    def test_full_native_branch_excludes_producer_chunk_but_none_keeps_it(self):
        # Mirrors only the pinned native branch predicate, not its algorithm.
        from contextvars import ContextVar
        producer_context = ContextVar("producer_must_stay_outside_decode", default="producer")
        publications = []
        def producer_chunk(x):
            publications.append(producer_context.get())
            return x + 2
        def native_layer(layer, x):
            if self.context.attn_metadata["GDN"].num_prefills > 0:
                return producer_chunk(x)
            return x + 2
        self.native_layer = native_layer
        self.router.is_compiling = torch.compiler.is_compiling
        self.full()
        compiled = torch.compile(lambda x: self.model.forward(x, None),
                                 backend="eager", fullgraph=True)
        def compiler_owner(model, x):
            return model.forward(x, None) if self.context.skip_compiled else compiled(x)
        self.router.native_call = compiler_owner
        self.install()
        x = torch.tensor([1.0])
        self.assertTrue(torch.equal(self.model(x), torch.tensor([9.0])))
        self.assertEqual(publications, [])
        self.context.cudagraph_runtime_mode = GM.NONE
        self.context.attn_metadata["GDN"].num_prefills = 1
        self.assertTrue(torch.equal(self.model(x), torch.tensor([9.0])))
        self.assertEqual(publications, ["producer"])

    def test_foreign_thread_cannot_borrow_live_decode_gate(self):
        from threading import Thread
        self.full()
        failures = []
        def foreign():
            try:
                self.model.layer.forward(1)
            except Exception as error:
                failures.append(error)
        def native_call(model, x):
            thread = Thread(target=foreign)
            thread.start()
            thread.join()
            return model.forward(x, None)
        self.router.native_call = native_call
        self.install()
        self.assertEqual(self.model(1), 9)
        self.assertEqual(len(failures), 1)
        self.assertRegex(str(failures[0]), "owning native entry thread")

    def test_unowned_fullgraph_compile_is_rejected(self):
        self.router.is_compiling = torch.compiler.is_compiling
        self.install()
        compiled = torch.compile(lambda x: self.model.forward(x),
                                 backend="eager", fullgraph=True)
        with self.assertRaises(Exception):
            compiled(torch.tensor([1.0]))


class SourceContractTests(unittest.TestCase):
    def test_source_owned_raw_and_wrong_wrapper(self):
        source = "def forward(x):\n    return x + 1\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.py"
            path.write_text(source)
            module = ModuleType("graph_source_fixture")
            module.__file__ = str(path)
            exec(compile(source, str(path), "exec"), vars(module))
            original = module.forward
            self.assertIs(source_contract.verify_raw_function(
                module, source, original, name="forward"), original)
            def foreign(x):
                return original(x)
            with self.assertRaises(ValueError):
                source_contract.verify_raw_function(module, source, foreign, name="forward")
            original.__wrapped__ = foreign
            with self.assertRaises(ValueError):
                source_contract.verify_raw_function(module, source, original, name="forward")

    def test_source_hash_drift_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.py"
            path.write_text("x = 1\n")
            module = ModuleType("graph_source_fixture")
            module.__file__ = str(path)
            with patch.dict(sys.modules, {module.__name__: module}), patch.dict(
                    source_contract.PINS, {module.__name__: ("fixture.py", "0" * 64)}):
                with self.assertRaisesRegex(ValueError, "bytes drift"):
                    source_contract.source_module(module.__name__)

    def test_exact_source_and_module_binding(self):
        source = b"x = 1\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.py"
            path.write_bytes(source)
            module = ModuleType("graph_source_fixture")
            module.__file__ = str(path)
            with patch.dict(sys.modules, {module.__name__: module}), patch.dict(
                    source_contract.PINS, {module.__name__: (
                        "fixture.py", hashlib.sha256(source).hexdigest())}):
                self.assertIs(source_contract.source_module(module.__name__)[0], module)

    def test_ambiguous_method_requires_source_owner(self):
        source = "class A:\n def forward(self,x): return x\nclass B:\n def forward(self,x): return x+1\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.py"
            path.write_text(source)
            module = ModuleType("graph_source_fixture")
            module.__file__ = str(path)
            exec(compile(source, str(path), "exec"), vars(module))
            with self.assertRaisesRegex(ValueError, "ambiguous"):
                source_contract.verify_raw_function(module, source, module.A.forward, name="forward")
            source_contract.verify_raw_function(module, source, module.A.forward,
                name="forward", qualname="A.forward")
            with self.assertRaises(ValueError):
                source_contract.verify_raw_function(module, source, module.A.forward,
                    name="forward", qualname="B.forward")


if __name__ == "__main__":
    unittest.main()

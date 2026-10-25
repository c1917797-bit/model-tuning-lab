"""Actual unchanged CPU helper/snapshot tests; fake native runtime, no NPU."""
from contextvars import ContextVar
from enum import Enum
import hashlib
from pathlib import Path
from types import ModuleType, SimpleNamespace
import sys
import unittest
from unittest.mock import patch
import torch

from graph_candidate.prefill_bridge import install_prefill_bridge
from graph_candidate.activation import activate_graph_candidate, _known_wrapper


class Mode(Enum):
    NONE = 0
    FULL = 2


class Plan:
    request_id = "selected-prefill"
    rank = 0
    step = 7
    token_start = 0
    scheduled_tokens = 3
    computed_tokens = 0
    def packed_rows(self):
        return (0, 2)


class BridgeTests(unittest.TestCase):
    def setUp(self):
        import independent_compact_model_hook as helper
        import independent_c2_block_table_snapshot as snapshot
        import independent_runner_context as runner
        self.helper, self.snapshot, self.runner = helper, snapshot, runner
        self.context = SimpleNamespace(cudagraph_runtime_mode=Mode.NONE,
            ubatch_slices=None, skip_compiled=True, attn_metadata={})
        self.module_patch = patch.dict(sys.modules, {
            "vllm": ModuleType("vllm"),
            "vllm.forward_context": ModuleType("vllm.forward_context"),
            "vllm.config": ModuleType("vllm.config"),
            "vllm.config.compilation": ModuleType("vllm.config.compilation")})
        self.module_patch.start()
        sys.modules["vllm"].__path__ = []
        sys.modules["vllm.config"].__path__ = []
        sys.modules["vllm.forward_context"].get_forward_context = lambda: self.context
        sys.modules["vllm.config.compilation"].CUDAGraphMode = Mode
        self.support = {module.__name__: hashlib.sha256(
            Path(module.__file__).resolve().read_bytes()).hexdigest()
            for module in (helper, snapshot, runner)}
        self.events = []
        self.selected_count = 0
        self.raise_native = False
        self.scope_seen = []
        self.guard_events = []
        cache = SimpleNamespace(request_id=Plan.request_id, rank=0, step=7, group=0, row=0)
        self.material_guard = self.Guard(self.guard_events)
        self.chosen = helper.CompactModelSelection((Plan(),), (2,), False,
            (cache,), ((0, ("full_attention",)),), ((0, (9,)),), self.material_guard)
        self.runtime = SimpleNamespace(request_ids=(Plan.request_id,), rank=0, step=7,
            prompt_logprobs=False, cache_slices=self.chosen.cache_slices,
            attention_groups=self.chosen.attention_groups,
            writable_kv_slots=self.chosen.writable_kv_slots)
        self.metadata = SimpleNamespace(block_tables=torch.tensor([[11, 12]]),
            causal=True, prefill=None, decode_meta=None, kvcomp_metadata=None,
            num_decode_tokens=0, num_decodes=0, num_prefills=1)
        self.context.attn_metadata = {"full_attention": self.metadata}
        self.request_runtime_token = runner.CURRENT_RUNTIME_SNAPSHOT.set(self.runtime)
        outer = self

        class Model:
            def forward(model, input_ids, positions,
                        intermediate_tensors=None, inputs_embeds=None):
                evidence = snapshot.active_c2_block_table_snapshot()
                outer.scope_seen.append(evidence)
                if outer.raise_native:
                    raise ValueError("native failed")
                if evidence is not None:
                    identity = (Plan.request_id, Plan.rank, Plan.step)
                    evidence.read(outer.metadata, 0, 2, request_identity=identity)
                    evidence.read(outer.metadata, 0, 2, request_identity=identity)
                return input_ids.float().unsqueeze(1) * 2

        self.Model = Model
        self.model = Model()
        self.original = Model.forward
        self.native = SimpleNamespace(model_class=Model,
            model_receipt=SimpleNamespace(forward=self.original),
            assert_saved_native=lambda: None)
        self.bridge = None

    class Guard:
        def __init__(self, events):
            self.events = events
        def __enter__(self):
            self.events.append("enter")
        def __exit__(self, *args):
            self.events.append("exit")

    def tearDown(self):
        if self.bridge is not None:
            self.bridge.stop()
        self.runner.CURRENT_RUNTIME_SNAPSHOT.reset(self.request_runtime_token)
        self.module_patch.stop()

    def select(self, *args, **kwargs):
        self.selected_count += 1
        return self.chosen

    def install(self):
        self.bridge = install_prefill_bridge(self.native, enabled=True,
            verify_source=lambda cls: None, select=self.select, emit=self.events.append,
            source_bindings=self.support, assert_entry=lambda model: None)

    def call(self):
        return self.bridge.forward(self.model, torch.tensor([4, 5, 6]), torch.arange(3))

    def test_disabled_returns_without_runtime_activation(self):
        self.assertIsNone(install_prefill_bridge(None))

    def test_actual_scope_math_helper_and_receipts(self):
        self.install()
        result = self.call()
        self.assertTrue(torch.equal(result, torch.tensor([[8.0], [0.0], [12.0]])))
        self.assertEqual(self.selected_count, 1)
        self.assertEqual(self.guard_events, ["enter", "exit"])
        self.assertIsNone(self.snapshot.active_c2_block_table_snapshot())
        event = self.events[-1]
        self.assertTrue(event["c2_block_table_snapshot"])
        self.assertFalse(event["inner_helper_c2_snapshot"])
        self.assertEqual(event["c2_snapshot_scope_owner"], "graph_candidate.prefill_bridge")
        self.assertEqual((event["c2_block_table_snapshot_reads"],
                          event["c2_block_table_snapshot_hits"]), (1, 1))
        self.assertTrue(self.scope_seen[-1]._closed)

    def test_native_exception_releases_real_scope_and_material_guard(self):
        self.install()
        self.raise_native = True
        with self.assertRaisesRegex(ValueError, "native failed"):
            self.call()
        self.assertIsNone(self.snapshot.active_c2_block_table_snapshot())
        self.assertEqual(self.guard_events, ["enter", "exit"])
        self.assertTrue(self.scope_seen[-1]._closed)
        self.assertEqual(self.events, [])

    def test_public_none_selection_preserves_native_without_fake_snapshot(self):
        self.install()
        self.chosen = None
        result = self.call()
        self.assertTrue(torch.equal(result, torch.tensor([[8.0], [10.0], [12.0]])))
        self.assertEqual(self.scope_seen, [None])
        self.assertEqual(self.events, [])
        self.assertEqual(self.selected_count, 1)

    def test_mixed_uses_existing_snapshot_validator_and_exact_identity(self):
        self.install()
        # Actual mixed native metadata has at least one prefill; here one native
        # decode row is included while the selected request remains source-owned.
        self.metadata.num_decodes = 1
        self.metadata.num_decode_tokens = 1
        self.call()
        self.assertEqual(self.selected_count, 1)
        self.assertTrue(self.scope_seen[-1]._closed)

    def test_selected_full_rejected(self):
        self.install()
        self.context.cudagraph_runtime_mode = Mode.FULL
        with self.assertRaisesRegex(ValueError, "compiler-bypassed NONE"):
            self.call()
        self.assertEqual(self.selected_count, 0)

    def test_selected_without_official_skip_rejected(self):
        self.install()
        self.context.skip_compiled = False
        with self.assertRaises(ValueError):
            self.call()

    def test_actual_request_identity_drift_rejected(self):
        self.install()
        self.runtime.request_ids = ("wrong",)
        with self.assertRaisesRegex(ValueError, "capture drift"):
            self.call()
        self.assertIsNone(self.snapshot.active_c2_block_table_snapshot())

    def test_actual_metadata_group_drift_rejected(self):
        self.install()
        self.context.attn_metadata = {}
        with self.assertRaisesRegex(ValueError, "metadata missing"):
            self.call()

    def test_instance_forward_override_rejected(self):
        self.install()
        self.model.forward = lambda *args: None
        with self.assertRaisesRegex(ValueError, "instance"):
            self.call()

    def test_support_hash_mismatch_rejected(self):
        self.support[self.helper.__name__] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source drift"):
            self.install()
        self.assertIs(self.Model.forward, self.original)

    def test_restore_exact_native_forward(self):
        self.install()
        self.bridge.stop()
        self.bridge = None
        self.assertIs(self.Model.forward, self.original)

    def test_rollback_preserves_unknown_outer_slot(self):
        self.install()
        inner = self.Model.forward
        foreign = lambda *args: None
        self.Model.forward = foreign
        with self.assertRaisesRegex(RuntimeError, "outer"):
            self.bridge.stop()
        self.assertIs(self.Model.forward, foreign)
        self.Model.forward = inner

    def test_disabled_activation_does_not_import_runtime(self):
        before = dict(vars(self.Model))
        stop = activate_graph_candidate(None)
        stop()
        self.assertEqual(before, dict(vars(self.Model)))

    def test_unsupported_enabled_configuration_fails_before_native_import(self):
        with self.assertRaisesRegex(ValueError, "barrier/finite/snapshot"):
            activate_graph_candidate({}, enabled=True, emit=lambda e: None,
                                     source_bindings={})


if __name__ == "__main__":
    unittest.main()

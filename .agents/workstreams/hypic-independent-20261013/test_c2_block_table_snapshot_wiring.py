"""CPU execution of activation/C2 wrapper wiring; no NPU/source acceptance."""
from contextlib import ExitStack, contextmanager, nullcontext
from types import ModuleType, SimpleNamespace
import sys
import unittest
from unittest.mock import patch

import torch

from independent_compact_activation import activate_compact_hypic, c2_install_route
from experimental_c2_layer_barrier import install_compact_c2
from independent_c2_block_table_snapshot import c2_block_table_snapshot_scope
from independent_compact_model_hook import CURRENT_COMPACT_MODEL, CompactModelSelection
from independent_runner_context import CURRENT_REQUEST_SLICES
from independent_mixed_query_plan import NativeQueryPlan
from independent_c2_query_plan import C2QueryPlan, QueryWindow
from independent_cache_map import CacheSlice
from test_independent_c2_metadata import metadata


def module(name, **attrs):
    result = ModuleType(name)
    for key, value in attrs.items():
        setattr(result, key, value)
    return result


class ActivationWiringTests(unittest.TestCase):
    @contextmanager
    def environment(self, *, enabled, late_failure=False, source_failure=False,
                    sink_failure=False):
        operations = []
        receipts = []
        model_options = []
        c2_options = []
        stage_options = []
        stage = SimpleNamespace(enable_mixed=True,
            compact_store=SimpleNamespace(async_material_transfer=False,
                verify_async_transfer=False, pool=SimpleNamespace()))
        stage.compact_kv_store = SimpleNamespace()
        def installer(name):
            def install(*args, **kwargs):
                operations.append("install " + name)
                return lambda: operations.append("stop " + name)
            return install
        stage.install_producer = installer("producer")
        stage.select_compact = lambda *args: None
        def stage_factory(**kwargs):
            stage_options.append(kwargs)
            operations.append("stage")
            return stage
        gdn = installer("gdn")
        flags = dict(c1_layer_completion_barrier=False,
            c1_layer_shadow_validation=False, c1_packed_wave=False,
            c1_partitioned_render=False, c1_lazy_initial_snapshot=False,
            c1_short_suffix_recurrent=False, c1_performance_mode=False,
            c1_first_divergence=False, c1_short_prefix_terminal_policy="chunk64",
            c1_first_divergence_head_policy="head0")
        for key, value in flags.items():
            setattr(gdn, key, value)
        def c1_route(config):
            return config, gdn, False
        def c2_on(stage, *, enabled=False, emit=None, **kwargs):
            c2_options.append(kwargs)
            return installer("c2")()
        # Old stub deliberately has no new kwarg, proving disabled compatibility.
        def c2_off(stage, *, enabled=False, emit=None):
            c2_options.append({})
            return installer("c2")()
        def model_base(kwargs):
            model_options.append(kwargs)
            operations.append("install model")
            if late_failure:
                raise RuntimeError("late model failure")
            return lambda: operations.append("stop model")
        def model_on(cls, *, enabled=False, verify_source=None, select=None,
                     emit=None, metadata_snapshot=False,
                     c2_block_table_snapshot=False):
            return model_base(dict(metadata_snapshot=metadata_snapshot,
                                   c2_block_table_snapshot=c2_block_table_snapshot))
        def model_off(cls, *, enabled=False, verify_source=None, select=None,
                      emit=None, metadata_snapshot=False):
            return model_base(dict(metadata_snapshot=metadata_snapshot))
        def verify():
            operations.append("verify")
            if source_failure:
                raise ValueError("source contract rejected")
        def emit(event):
            receipts.append(event)
            if sink_failure:
                raise RuntimeError("receipt sink failure")
        modules = {
            "vllm_ascend": module("vllm_ascend"),
            "vllm_ascend.ops": module("vllm_ascend.ops"),
            "vllm": module("vllm"),
            "vllm.model_executor": module("vllm.model_executor"),
            "vllm.model_executor.models": module("vllm.model_executor.models"),
            "vllm.model_executor.models.qwen3_5":
                module("vllm.model_executor.models.qwen3_5", Qwen3_5Model=object),
            "independent_compact_stage":
                module("independent_compact_stage", CompactCanonicalStage=stage_factory),
            "independent_compact_runtime_snapshot":
                module("independent_compact_runtime_snapshot",
                       activate_compact_runner=installer("runner")),
            "independent_compact_model_hook":
                module("independent_compact_model_hook",
                       install_compact_model=model_on if enabled else model_off),
        }
        with ExitStack() as stack:
            stack.enter_context(patch.dict(sys.modules, modules))
            stack.enter_context(patch("independent_compact_activation.c1_install_route",
                                      side_effect=c1_route))
            stack.enter_context(patch("experimental_c2_layer_barrier.install_compact_c2",
                                      new=c2_on if enabled else c2_off))
            verifier = stack.enter_context(patch(
                "independent_c2_block_table_snapshot.verify_c2_snapshot_runtime_contract",
                side_effect=verify))
            yield SimpleNamespace(operations=operations, receipts=receipts,
                model_options=model_options, c2_options=c2_options,
                stage_options=stage_options, verifier=verifier, emit=emit)

    def config(self, enabled):
        return {"c2_layer_completion_barrier": True,
                "c2_block_table_snapshot": enabled, "model_identity": "fixture"}

    def test_on_verifies_source_then_passes_flag_to_c2_and_model_and_receipt(self):
        with self.environment(enabled=True) as env:
            stop = activate_compact_hypic(self.config(True), enabled=True, emit=env.emit)
            self.assertEqual(env.operations[:2], ["verify", "stage"])
            self.assertEqual(env.c2_options, [{"block_table_snapshot": True}])
            self.assertEqual(env.model_options, [
                {"metadata_snapshot": False, "c2_block_table_snapshot": True}])
            self.assertEqual(env.stage_options, [{"model_identity": "fixture"}])
            self.assertIs(env.receipts[0]["c2_block_table_snapshot"], True)
            env.verifier.assert_called_once_with()
            stop()
            self.assertEqual(env.operations[-5:],
                ["stop model", "stop c2", "stop gdn", "stop producer", "stop runner"])

    def test_off_keeps_old_stub_call_signatures_and_does_not_verify(self):
        with self.environment(enabled=False, source_failure=True) as env:
            stop = activate_compact_hypic(self.config(False), enabled=True, emit=env.emit)
            env.verifier.assert_not_called()
            self.assertEqual(env.c2_options, [{}])
            self.assertEqual(env.model_options, [{"metadata_snapshot": False}])
            self.assertIs(env.receipts[0]["c2_block_table_snapshot"], False)
            stop()

    def test_source_failure_precedes_all_owned_installs(self):
        with self.environment(enabled=True, source_failure=True) as env:
            with self.assertRaisesRegex(ValueError, "source contract rejected"):
                activate_compact_hypic(self.config(True), enabled=True, emit=env.emit)
            self.assertEqual(env.operations, ["verify"])
            self.assertEqual(env.stage_options, [])
            self.assertEqual(env.receipts, [])

    def test_late_install_failure_rolls_back_only_owned_hooks(self):
        with self.environment(enabled=True, late_failure=True) as env:
            with self.assertRaisesRegex(RuntimeError, "late model failure"):
                activate_compact_hypic(self.config(True), enabled=True, emit=env.emit)
            self.assertEqual(env.operations[-4:],
                ["stop c2", "stop gdn", "stop producer", "stop runner"])
            self.assertNotIn("stop model", env.operations)
            self.assertEqual(env.receipts, [])

    def test_install_receipt_failure_rolls_back_complete_chain(self):
        with self.environment(enabled=True, sink_failure=True) as env:
            with self.assertRaisesRegex(RuntimeError, "receipt sink failure"):
                activate_compact_hypic(self.config(True), enabled=True, emit=env.emit)
            self.assertEqual(env.operations[-5:],
                ["stop model", "stop c2", "stop gdn", "stop producer", "stop runner"])

    def test_route_requires_explicit_boolean_and_layer_barrier(self):
        for value in (1, 0, None, "true"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                c2_install_route({"c2_layer_completion_barrier": True,
                                 "c2_block_table_snapshot": value})
        with self.assertRaises(ValueError):
            c2_install_route({"c2_block_table_snapshot": True})

    def test_route_preserves_finite_flag_and_does_not_mutate_config(self):
        config = {"c2_layer_completion_barrier": True,
                  "c2_layer_finite_gate": True, "c2_block_table_snapshot": True,
                  "kept": 1}
        with patch("experimental_c2_layer_barrier.install_compact_c2") as target:
            remaining, install, barrier = c2_install_route(config)
            install("stage", enabled=True, emit="sink")
            target.assert_called_once_with("stage", enabled=True, emit="sink",
                finite_gate=True, block_table_snapshot=True)
        self.assertEqual(remaining, {"kept": 1})
        self.assertTrue(barrier)
        self.assertIs(config["c2_block_table_snapshot"], True)

    def test_disabled_activation_does_not_import_or_verify_runtime(self):
        with patch("independent_c2_block_table_snapshot.verify_c2_snapshot_runtime_contract",
                   side_effect=AssertionError("unexpected verification")):
            activate_compact_hypic(None, enabled=False)()


class C2WrapperWiringTests(unittest.TestCase):
    @contextmanager
    def fixture(self, *, enabled, missing_scope=False, bad_lease=False,
                nonfinite=False, selected_none=False):
        calls = []
        events = []
        syncs = []
        leases = []
        class Backend:
            num_kv_heads = 1
            head_size = 256
            def forward(self, layer, q, k, v, cache, meta, out=None, *args):
                calls.append((layer.layer_name, meta.slot_mapping.tolist(),
                              meta.seq_lens_list))
                out.copy_(q + meta.seq_lens_list[0])
                return out
        original = Backend.forward
        backend_module = module("vllm_ascend.attention.attention_v1",
            AscendAttentionBackendImpl=Backend,
            AscendAttentionState=SimpleNamespace(PrefillCacheHit="paged"))
        @contextmanager
        def material(key):
            leases.append("held")
            try:
                values = torch.ones(2, 1, 256)
                if nonfinite:
                    values[0, 0, 0] = float("inf")
                yield 7, {"keys": torch.ones(2, 1, 256), "values": values,
                          "positions": torch.tensor([2, 3])}
            finally:
                leases.pop()
        stage = SimpleNamespace(
            compact_kv_store=SimpleNamespace(acquire_private=material))
        plans = (
            NativeQueryPlan("d", 0, 3, 0, 3, 1, "decode"),
            C2QueryPlan("p", 0, 3, 1, 0, 6, 2, 4, (0, 1, 4, 5),
                (QueryWindow(0, 2, 2, 0, 2), QueryWindow(4, 6, 6, 2, 4)), "body"))
        caches = (CacheSlice("d", 0, 3, 0, 0, 8, (1,), (11,)),
                  CacheSlice("p", 0, 3, 0, 1, 8, (2,), tuple(range(16, 22))))
        owned = (("d", 0, (11,)),
                 ("p", 0, () if bad_lease else tuple(range(16, 22))))
        selected = CompactModelSelection(plans, (0, 4), False, caches,
                    ((0, ("layer0", "layer1")),), owned)
        native = metadata()
        native.num_decodes = 1
        native.num_decode_tokens = 1
        native.num_prefills = 1
        native.block_tables = torch.tensor([[1], [2]], dtype=torch.int32)
        q = torch.arange(5 * 256).reshape(5, 256).float()
        out = torch.full_like(q, -1)
        key_cache = torch.zeros(3, 8, 1, 256)
        value_cache = torch.zeros_like(key_cache)
        model_token = CURRENT_COMPACT_MODEL.set(None if selected_none else selected)
        request_token = CURRENT_REQUEST_SLICES.set(None)
        def synchronize():
            self.assertEqual(leases, ["held"])
            syncs.append("layer")
        try:
            with ExitStack() as stack:
                stack.enter_context(patch.dict(sys.modules,
                    {backend_module.__name__: backend_module}))
                stack.enter_context(patch("experimental_c2_layer_barrier.inspect.getfile",
                                          return_value=__file__))
                stack.enter_context(patch("experimental_c2_layer_barrier.Path.read_bytes",
                                          return_value=b"cpu-source-double"))
                stack.enter_context(patch("experimental_c2_layer_barrier.hashlib.sha256",
                    return_value=SimpleNamespace(hexdigest=lambda:
                    "80005aba42bcf61247cc0d91502a0f1338194a4b38dd82bc521f6d3c84958390")))
                stack.enter_context(patch.object(torch, "npu",
                    SimpleNamespace(synchronize=synchronize), create=True))
                stack.enter_context(patch("independent_linear_material_pool.identity_key",
                                          return_value="body"))
                stack.enter_context(patch("independent_plan_material_identity.identity_for_plan",
                                          return_value="body"))
                context = (c2_block_table_snapshot_scope(
                    tuple((p.request_id, p.rank, p.step) for p in plans),
                    enabled=True, source_verified_immutable=True)
                    if enabled and not missing_scope else nullcontext(None))
                snapshot = stack.enter_context(context)
                if snapshot is not None:
                    snapshot.bind_native(native)
                getter = stack.enter_context(patch(
                    "independent_c2_block_table_snapshot.active_c2_block_table_snapshot",
                    return_value=snapshot))
                stop = install_compact_c2(stage, enabled=True, emit=events.append,
                    finite_gate=True, block_table_snapshot=enabled)
                try:
                    def run(name="layer0"):
                        return Backend().forward(SimpleNamespace(layer_name=name),
                            q, q, q, (key_cache, value_cache), native, out)
                    yield SimpleNamespace(run=run, events=events, calls=calls,
                        syncs=syncs, leases=leases, getter=getter, snapshot=snapshot,
                        native=native, q=q, out=out,
                        key_cache=key_cache, value_cache=value_cache)
                finally:
                    stop()
                self.assertIs(Backend.forward, original)
        finally:
            CURRENT_REQUEST_SLICES.reset(request_token)
            CURRENT_COMPACT_MODEL.reset(model_token)

    def test_real_wrapper_two_layers_reuses_one_copy_and_emits_once_per_layer(self):
        original_cpu = torch.Tensor.cpu
        copies = []
        def cpu(tensor, *args, **kwargs):
            copies.append(1)
            return original_cpu(tensor, *args, **kwargs)
        with self.fixture(enabled=True) as env:
            with patch.object(torch.Tensor, "cpu", cpu):
                env.run("layer0")
                env.run("layer1")
            self.assertEqual(len(copies), 1)
            self.assertEqual(env.syncs, ["layer", "layer"])
            self.assertEqual(env.leases, [])
            checks = [e for e in env.events
                      if e["event"] == "c2_block_table_snapshot_layer_checked"]
            self.assertEqual(len(checks), 2)
            for event, name, delta in zip(checks, ("layer0", "layer1"), ((1, 2), (0, 3))):
                self.assertEqual((event["rank"], event["step"], event["group"]), (0, 3, 0))
                self.assertEqual(event["layer"], name)
                self.assertEqual(event["request_ids"], ["d", "p"])
                self.assertEqual((event["reads_delta"], event["hits_delta"]), delta)
            self.assertEqual(env.calls[:3],
                [("layer0", [11], [4]), ("layer0", [16, 17], [2]),
                 ("layer0", [20, 21], [6])])
            self.assertTrue(torch.equal(env.out[:1], env.q[:1] + 4))
            self.assertTrue(torch.equal(env.out[1:3], env.q[1:3] + 2))
            self.assertTrue(torch.equal(env.out[3:], env.q[3:] + 6))
            self.assertEqual(env.key_cache.view(-1, 1, 256)[18:20].tolist(),
                             torch.ones(2, 1, 256).tolist())

    def test_off_calls_old_metadata_path_and_no_snapshot_receipt(self):
        original_cpu = torch.Tensor.cpu
        copies = []
        def cpu(tensor, *args, **kwargs):
            copies.append(1)
            return original_cpu(tensor, *args, **kwargs)
        with self.fixture(enabled=False) as env:
            with patch.object(torch.Tensor, "cpu", cpu):
                env.run()
            self.assertEqual(len(copies), 3)
            env.getter.assert_not_called()
            self.assertFalse(any(e["event"] == "c2_block_table_snapshot_layer_checked"
                                 for e in env.events))
            self.assertEqual(env.syncs, ["layer"])

    def test_selected_layer_without_scope_fails_before_any_commit_or_backend(self):
        with self.fixture(enabled=True, missing_scope=True) as env:
            with self.assertRaisesRegex(ValueError, "requires owning"):
                env.run()
            self.assertEqual(env.calls, [])
            self.assertEqual(env.syncs, [])
            self.assertEqual(env.events, [])
            self.assertFalse(env.key_cache.any())
            self.assertTrue((env.out == -1).all())

    def test_scope_not_required_for_unselected_native_forward(self):
        with self.fixture(enabled=True, missing_scope=True, selected_none=True) as env:
            env.run()
            env.getter.assert_not_called()
            self.assertEqual(len(env.calls), 1)
            self.assertEqual(env.events, [])

    def test_bad_lease_keeps_commit_and_completion_guards(self):
        with self.fixture(enabled=True, bad_lease=True) as env:
            with self.assertRaises(ValueError):
                env.run()
            self.assertEqual(env.calls, [])
            self.assertEqual(env.syncs, [])
            self.assertEqual(env.events, [])
            self.assertFalse(env.key_cache.any())
            self.assertEqual(env.leases, [])

    def test_nonfinite_public_value_still_fails_before_native_commit(self):
        with self.fixture(enabled=True, nonfinite=True) as env:
            with self.assertRaisesRegex(ValueError, "nonfinite"):
                env.run()
            self.assertEqual(env.calls, [])
            self.assertEqual(env.syncs, [])
            self.assertEqual(env.events, [])
            self.assertFalse(env.value_cache.any())
            self.assertEqual(env.leases, [])

    def test_block_table_drift_keeps_full_live_comparison(self):
        with self.fixture(enabled=True) as env:
            env.run()
            env.native.block_tables[1, 0] = 4
            before = len(env.calls)
            with self.assertRaises(ValueError):
                env.run("layer1")
            self.assertEqual(len(env.calls), before)
            self.assertEqual(len([e for e in env.events
                if e["event"] == "c2_block_table_snapshot_layer_checked"]), 1)

    def test_new_installer_flag_is_strict_even_when_disabled(self):
        for value in (1, 0, None, "true"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                install_compact_c2(None, block_table_snapshot=value)
        install_compact_c2(None, enabled=False)()


if __name__ == "__main__":
    unittest.main()

import enum
import hashlib
from pathlib import Path
from types import SimpleNamespace, ModuleType
import sys
import tempfile
import unittest
from unittest.mock import patch

import torch

from independent_c2_block_table_snapshot import (
    active_c2_block_table_snapshot, validate_c2_snapshot_forward,
    verify_c2_snapshot_runtime_contract)
from test_independent_c2_metadata import metadata
import test_independent_compact_model_hook as model_fixtures
from independent_c2_cache_binding import BoundQueryWindow
from independent_c2_metadata import window_metadata
from independent_compact_model_hook import install_compact_model, CURRENT_COMPACT_MODEL
from independent_runner_context import CURRENT_RUNTIME_SNAPSHOT


class Mode(enum.Enum):
    NONE = 0
    FULL = 2


def fixture():
    selection = model_fixtures.ModelHookTests().selection()
    native = metadata()
    cache = SimpleNamespace(request_id="r", rank=0, step=1, row=0, group=7)
    selection = type(selection)(selection.plans, selection.sampled_rows, False,
        (cache,), ((7, ("full.0", "full.1")),), (("r", 7, tuple(range(12))),))
    context = SimpleNamespace(cudagraph_runtime_mode=Mode.NONE, ubatch_slices=None,
        attn_metadata={"full.0": native, "full.1": native})
    runtime = SimpleNamespace(request_ids=("r",), rank=0, step=1, prompt_logprobs=False,
        cache_slices=selection.cache_slices, attention_groups=selection.attention_groups,
        writable_kv_slots=selection.writable_kv_slots)
    return selection, context, runtime, native


class ForwardAdmissionTests(unittest.TestCase):
    def test_valid_same_group_eager_capture(self):
        selection, context, runtime, native = fixture()
        ids, rows, actual = validate_c2_snapshot_forward(selection, context, runtime)
        self.assertEqual(ids, (("r", 0, 1),))
        self.assertEqual(rows, (0,))
        self.assertIs(actual, native)

    def test_graph_ubatch_and_metadata_list_rejected(self):
        for field, value in (("cudagraph_runtime_mode", Mode.FULL),
                             ("ubatch_slices", [0, 1]), ("attn_metadata", [])):
            selection, context, runtime, _ = fixture()
            setattr(context, field, value)
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_c2_snapshot_forward(selection, context, runtime)

    def test_missing_context_fields_or_runtime_rejected(self):
        selection, context, runtime, _ = fixture()
        for absent in ("cudagraph_runtime_mode", "ubatch_slices", "attn_metadata"):
            altered = SimpleNamespace(**vars(context))
            delattr(altered, absent)
            with self.subTest(absent=absent), self.assertRaises(ValueError):
                validate_c2_snapshot_forward(selection, altered, runtime)
        with self.assertRaises(ValueError):
            validate_c2_snapshot_forward(selection, context, None)

    def test_runtime_capture_and_rank_step_drift_rejected(self):
        for field, value in (("request_ids", ("other",)), ("rank", 1), ("step", 2),
                             ("cache_slices", ()), ("writable_kv_slots", ()),
                             ("prompt_logprobs", True)):
            selection, context, runtime, _ = fixture()
            setattr(runtime, field, value)
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_c2_snapshot_forward(selection, context, runtime)

    def test_group_object_or_coverage_drift_rejected(self):
        selection, context, runtime, _ = fixture()
        context.attn_metadata["full.1"] = metadata()
        with self.assertRaises(ValueError):
            validate_c2_snapshot_forward(selection, context, runtime)
        del context.attn_metadata["full.1"]
        with self.assertRaises(ValueError):
            validate_c2_snapshot_forward(selection, context, runtime)

    def test_multiple_groups_rejected(self):
        selection, context, runtime, _ = fixture()
        groups = ((7, ("full.0",)), (8, ("full.1",)))
        selection = type(selection)(selection.plans, selection.sampled_rows, False,
            selection.cache_slices, groups, selection.writable_kv_slots)
        runtime.attention_groups = groups
        with self.assertRaises(ValueError):
            validate_c2_snapshot_forward(selection, context, runtime)

    def test_spec_kvcomp_noncausal_rejected(self):
        for field, value in (("causal", False), ("prefill", object()),
                             ("decode_meta", object()), ("kvcomp_metadata", object()),
                             ("num_decode_tokens", 2), ("num_prefills", 0)):
            selection, context, runtime, native = fixture()
            setattr(native, field, value)
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_c2_snapshot_forward(selection, context, runtime)

    def test_request_group_capture_drift_rejected(self):
        selection, context, runtime, _ = fixture()
        runtime.cache_slices[0].group = 9
        with self.assertRaises(ValueError):
            validate_c2_snapshot_forward(selection, context, runtime)


class SourceContractTests(unittest.TestCase):
    def test_source_hash_and_imported_path_checked_without_nested_import(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "worker").mkdir()
            source = root / "worker" / "runner.py"
            source.write_text("source-fixture\n")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            pkg = SimpleNamespace(__file__=str(root / "__init__.py"))
            module = SimpleNamespace(__file__=str(source))
            with patch("independent_c2_block_table_snapshot._SOURCE_FILES",
                       {"fake_runtime": {"worker/runner.py": digest}}), \
                 patch.dict(sys.modules, {"fake_runtime": pkg,
                                        "fake_runtime.worker.runner": module}):
                verify_c2_snapshot_runtime_contract()
                module.__file__ = str(root / "different.py")
                with self.assertRaisesRegex(ValueError, "path drift"):
                    verify_c2_snapshot_runtime_contract()
                module.__file__ = str(source)
                source.write_text("changed\n")
                with self.assertRaisesRegex(ValueError, "source drift"):
                    verify_c2_snapshot_runtime_contract()

    def test_missing_live_package_origin_rejected(self):
        with patch("independent_c2_block_table_snapshot._SOURCE_FILES",
                   {"absent_runtime": {"x.py": "0" * 64}}), \
             patch.dict(sys.modules, {"absent_runtime": SimpleNamespace()}):
            with self.assertRaises(ValueError):
                verify_c2_snapshot_runtime_contract()


class ModelScopeTests(unittest.TestCase):
    def setUp(self):
        verifier=patch('independent_c2_native_forward.verify_c2_native_forward')
        checker=patch('independent_c2_native_forward.assert_c2_owned_forward')
        self.native_verify=verifier.start()
        self.native_assert=checker.start()
        self.addCleanup(verifier.stop)
        self.addCleanup(checker.stop)

    def run_model(self, fail=False):
        selection, context, runtime, native = fixture()
        observed = []
        class Base:
            def forward(self, ids, positions, intermediate_tensors=None, inputs_embeds=None):
                snapshot = active_c2_block_table_snapshot()
                observed.append(snapshot)
                if snapshot is None:
                    raise AssertionError("scope not active in original layer loop")
                for _ in range(3):
                    result = window_metadata(native,
                        BoundQueryWindow(0, 2, (3, 4), (39, 12), 5, (4, 5)),
                        request_row=0, cache_hit_state="paged",
                        block_table_reader=snapshot.read, request_identity=("r", 0, 1))
                    self_test.assertNotEqual(result.block_tables.data_ptr(),
                                             native.block_tables.data_ptr())
                if fail:
                    raise RuntimeError("fake layer failure")
                return ids[:, None].float() + positions.reshape(-1, 1).float()
        class Model(Base):
            pass
        self_test = self
        parent = ModuleType("vllm")
        parent.__path__ = []
        module = ModuleType("vllm.forward_context")
        module.get_forward_context = lambda: context
        events = []
        stop = install_compact_model(Model, enabled=True, verify_source=lambda c: None,
            select=lambda *args: selection, emit=events.append, c2_block_table_snapshot=True)
        token = CURRENT_RUNTIME_SNAPSHOT.set(runtime)
        try:
            with patch.dict(sys.modules, {"vllm": parent, "vllm.forward_context": module}):
                if fail:
                    with self.assertRaisesRegex(RuntimeError, "fake layer failure"):
                        Model().forward(torch.arange(12), torch.arange(12))
                else:
                    out = Model().forward(torch.arange(12), torch.arange(12))
                    self.assertEqual(out.shape, (12, 1))
                    self.assertEqual(out[11, 0].item(), 22)
                    self.assertEqual(events[0]["c2_block_table_snapshot_reads"], 1)
                    self.assertEqual(events[0]["c2_block_table_snapshot_hits"], 2)
            self.assertIsNone(active_c2_block_table_snapshot())
            self.assertIsNone(CURRENT_COMPACT_MODEL.get())
            with self.assertRaises(ValueError):
                observed[0].read(native, 0, 2, request_identity=("r", 0, 1))
        finally:
            CURRENT_RUNTIME_SNAPSHOT.reset(token)
            stop()
        self.assertIs(Model.forward, Base.forward)
        self.native_verify.assert_called_once()
        self.native_assert.assert_called_once()

    def test_real_model_wrapper_scopes_reader_and_restores_outputs(self):
        self.run_model()

    def test_model_exception_closes_scope_and_uninstalls_cleanly(self):
        self.run_model(fail=True)

    def test_default_path_never_requests_forward_context(self):
        Base, Model = model_fixtures.ModelHookTests().classes()
        stop = install_compact_model(Model, enabled=True, verify_source=lambda c: None,
            select=lambda *args: model_fixtures.ModelHookTests().selection(), emit=lambda e: None)
        with patch("independent_c2_block_table_snapshot.validate_c2_snapshot_forward",
                   side_effect=AssertionError("default unexpectedly opted in")):
            try:
                self.assertEqual(Model().forward(torch.arange(12), torch.arange(12)).shape, (12, 1))
            finally:
                stop()
        self.assertIs(Model.forward, Base.forward)
        self.native_verify.assert_not_called()
        self.native_assert.assert_not_called()

    def test_nonboolean_switch_rejected(self):
        _, Model = model_fixtures.ModelHookTests().classes()
        with self.assertRaises(ValueError):
            install_compact_model(Model, enabled=True, verify_source=lambda c: None,
                select=lambda *args: None, emit=lambda e: None, c2_block_table_snapshot=1)


if __name__ == "__main__":
    unittest.main()

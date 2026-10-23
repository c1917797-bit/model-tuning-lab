import sys
from dataclasses import replace
from types import ModuleType
import unittest
from unittest.mock import patch

import independent_compact_runtime_snapshot as runtime_hooks
import independent_runtime_adapter as native_adapter
from independent_runner_context import CURRENT_RUNTIME_SNAPSHOT
import test_independent_compact_runtime_snapshot as fixtures


class NativeCaptureDiagnosticTests(unittest.TestCase):
    def modules(self, runner):
        root = ModuleType("vllm_ascend")
        root.__path__ = []
        ops = ModuleType("vllm_ascend.ops")
        root.ops = ops
        worker = ModuleType("vllm_ascend.worker")
        worker.__path__ = []
        module = ModuleType("vllm_ascend.worker.model_runner_v1")
        module.NPUModelRunner = runner
        worker.model_runner_v1 = module
        root.worker = worker
        return {"vllm_ascend": root, "vllm_ascend.ops": ops,
                "vllm_ascend.worker": worker,
                "vllm_ascend.worker.model_runner_v1": module}

    def exercise(self, enabled, *, failure=None, sink_failure=False):
        requests, caches = fixtures.SnapshotTests().fixture()
        caches = tuple(replace(cache, group=5) for cache in caches)
        snapshot = runtime_hooks.freeze_compact_runtime(
            requests, caches, ((5, ("official.full.0", "official.full.1")),),
            (1, 3), prompt_logprobs=False)
        class Runner:
            use_cp = False
            def _prepare_inputs(self, *args, **kwargs):
                return "prepared"
            def execute_model(self):
                self._prepare_inputs(None, (2, 2))
                return CURRENT_RUNTIME_SNAPSHOT.get()
        original = Runner.execute_model
        events = []
        def emit(event):
            if sink_failure and event["event"] == "compact_native_attention_groups_captured":
                raise RuntimeError("sink failed")
            events.append(event)
        with patch.dict(sys.modules, self.modules(Runner)), \
             patch.object(native_adapter, "freeze_native_runner", return_value=requests), \
             patch.object(native_adapter, "verify_runner"), \
             patch.object(runtime_hooks, "capture_compact_runtime",
                          side_effect=failure, return_value=snapshot):
            stop = runtime_hooks.activate_compact_runner(
                enabled=True, emit=emit, record_attention_groups=enabled)
            try:
                if failure or sink_failure:
                    with self.assertRaises(RuntimeError):
                        Runner().execute_model()
                else:
                    self.assertIs(Runner().execute_model(), snapshot)
                self.assertIsNone(CURRENT_RUNTIME_SNAPSHOT.get())
            finally:
                stop()
        self.assertIs(Runner.execute_model, original)
        return events, snapshot

    def test_enabled_receipt_comes_from_native_capture(self):
        events, snapshot = self.exercise(True)
        captures = [e for e in events if e["event"] == "compact_native_attention_groups_captured"]
        self.assertEqual(len(captures), 1)
        self.assertEqual(captures[0], {
            "event": "compact_native_attention_groups_captured", "rank": 0, "step": 3,
            "request_ids": ["a", "b"],
            "attention_groups": [{"group": 5, "layers": ["official.full.0", "official.full.1"]}],
            "source": "verified-native-full-attention-spec"})
        self.assertEqual(snapshot.attention_groups, ((5, ("official.full.0", "official.full.1")),))

    def test_default_does_not_emit_native_group_diagnostic(self):
        events, _ = self.exercise(False)
        self.assertFalse(any(e["event"] == "compact_native_attention_groups_captured" for e in events))

    def test_capture_failure_emits_no_native_proof_and_cleans_context(self):
        events, _ = self.exercise(True, failure=RuntimeError("capture failed"))
        self.assertFalse(any(e["event"] == "compact_native_attention_groups_captured" for e in events))

    def test_sink_failure_is_not_accepted_native_capture(self):
        self.exercise(True, sink_failure=True)

    def test_explicit_switch_and_sink_required(self):
        for enabled, emit in ((1, lambda e: None), (True, None)):
            with self.assertRaises(ValueError):
                runtime_hooks.activate_compact_runner(
                    enabled=True, emit=emit, record_attention_groups=enabled)


if __name__ == "__main__":
    unittest.main()

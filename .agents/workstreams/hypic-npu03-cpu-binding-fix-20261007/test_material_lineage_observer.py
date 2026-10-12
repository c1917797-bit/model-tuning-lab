import importlib
import copy
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch
import torch
import material_lineage_observer as observer

SOURCE = Path("/cache/cch/hypic_vllm_ascend-hotproof-20261008")
sys.path.insert(0, str(SOURCE))
Store = importlib.import_module("hypic_vllm_ascend.material").MaterializedSegmentStore


class LineageTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {observer.SWITCH: "1"})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.store = Store()
        self.store.configure(max_mb=1, min_free_mb=0, max_segments=2,
            storage_device="cpu", gdn_storage_device="cpu", pin_cpu_material=False)
        self.store._device_free_bytes = lambda: None
        self.events = []
        self.identity = dict(step=1, producer_request_ids=["warmup"])
        self.handle = observer.install(self.store, segment_hash=b"a",
            layers={"kv": "attn", "gdn": "gdn"}, emit=self.events.append, rank=0,
            context=lambda: self.identity, request_id="target")
        self.addCleanup(self.handle.uninstall)

    def kv(self, value=1):
        return (torch.full((3, 1, 2), float(value)),
                torch.full((3, 1, 2), float(value+1)))

    def gdn(self, value=1):
        return (torch.full((1, 2, 2), float(value)),
                torch.full((2, 2), float(value+1)),
                torch.eye(2).unsqueeze(0))

    def write(self, value=1):
        self.store.begin_step([b"a"])
        self.assertTrue(self.store.put_full_kv(b"a", "attn", *self.kv(value)))
        self.assertTrue(self.store.put_gdn_state(b"a", "gdn", *self.gdn(value)))
        self.store.finish_step(require_full_kv=True, require_gdn=True,
                               require_transition=True)
        return self.store._segments[b"a"]

    def consume(self, obj, **kwargs):
        return self.handle.tracker.consume(obj, kind="kv", layer="attn",
            request_id="target", step=3, **kwargs)

    def test_real_store_producer_and_consumer_samples_join(self):
        obj = self.write()
        event = self.consume(obj)
        self.assertTrue(event["sampled_storage_equal"])
        self.assertEqual(event["generation"], 1)
        self.assertEqual(event["producer"]["producer_request_ids"], ["warmup"])
        self.assertEqual([e["event"] for e in self.events],
                         ["committed", "committed", "consumed"])

    def test_different_duplicate_inputs_keep_original_generation(self):
        obj = self.write()
        self.identity = dict(step=2, producer_request_ids=["other"])
        self.assertIs(self.write(9), obj)
        self.assertEqual([e["event"] for e in self.events][-2:], ["retained", "retained"])
        event = self.consume(obj)
        self.assertEqual(event["producer"]["step"], 1)
        self.assertTrue(event["sampled_storage_equal"])

    def test_same_hash_recreate_different_values_new_generation(self):
        old = self.write()
        self.store.remove(b"a")
        self.identity = dict(step=2, producer_request_ids=["new-warmup"])
        new = self.write(9)
        self.assertIsNot(old, new)
        self.assertEqual(self.consume(new)["generation"], 2)
        self.assertEqual(self.consume(old)["generation"], 1)

    def test_mutated_sample_is_detected_without_changing_store(self):
        obj = self.write()
        obj.full_kv_by_layer["attn"][0][0, 0, 0] += 7
        self.assertFalse(self.consume(obj)["sampled_storage_equal"])

    def test_unknown_object_and_wrong_layer_refused(self):
        obj = self.write()
        fake = types.SimpleNamespace(**vars(obj))
        with self.assertRaisesRegex(ValueError, "unobserved"):
            self.consume(fake)
        with self.assertRaisesRegex(ValueError, "identity"):
            self.handle.tracker.consume(obj, kind="kv", layer="wrong",
                                        request_id="target", step=3)

    def test_disabled_mode_never_reads_or_mutates_target(self):
        with patch.dict(os.environ, {observer.SWITCH: "0"}):
            handle = observer.install(object(), segment_hash=None, layers=None,
                                      emit=None, rank=None, context=None, request_id=None)
        handle.uninstall()

    def test_retained_wrapper_inert_after_uninstall(self):
        saved = self.store.put_full_kv
        tracker = self.handle.tracker
        self.handle.uninstall()
        self.store.begin_step([b"a"])
        self.assertTrue(saved(b"a", "attn", *self.kv()))
        self.assertEqual(self.events, [])
        self.assertIsNone(tracker.emit)
        self.assertEqual(tracker.records, {})
        self.assertNotIn("put_full_kv", vars(self.store))

    def test_context_mutation_does_not_change_stored_receipts(self):
        obj = self.write()
        self.identity["producer_request_ids"][0] = "changed"
        self.assertEqual(self.consume(obj)["producer"]["producer_request_ids"], ["warmup"])

    def test_capture_does_not_update_lru_timestamp(self):
        obj = self.write()
        before = obj.last_access_time
        self.consume(obj)
        self.assertEqual(obj.last_access_time, before)

    def test_wrong_request_and_step_rebinding_refused(self):
        obj = self.write()
        with self.assertRaisesRegex(ValueError, "wrong consumer"):
            self.handle.tracker.consume(obj, kind="kv", layer="attn",
                                        request_id="someone-else", step=3)
        self.consume(obj)
        with self.assertRaisesRegex(ValueError, "rebound"):
            self.handle.tracker.consume(obj, kind="kv", layer="attn",
                                        request_id="target", step=4)

    def test_event_budget_fails_closed(self):
        obj = self.write()
        self.handle.tracker.max_events = 2
        with self.assertRaisesRegex(RuntimeError, "budget"):
            self.consume(obj)

    def audit_ready(self):
        import material_lineage_audit
        obj = self.write()
        self.consume(obj)
        self.handle.tracker.consume(obj, kind="gdn", layer="gdn",
                                    request_id="target", step=3)
        kwargs = dict(request_id="target", rank=0, pid=os.getpid(),
                      segment_hash=b"a".hex(), layers={"kv": "attn", "gdn": "gdn"})
        return material_lineage_audit, kwargs

    def test_independent_audit_recomputes_flags_and_requires_components(self):
        audit, kwargs = self.audit_ready()
        result = audit.audit(self.events, **kwargs)
        self.assertTrue(all(x["sampled_storage_equal"] for x in result["observations"]))
        corrupt = copy.deepcopy(self.events)
        corrupt[-2]["stored_sample"][0]["values"][0] += 10
        corrupt[-2]["sampled_storage_equal"] = True
        result = audit.audit(corrupt, **kwargs)
        self.assertFalse(result["observations"][0]["sampled_storage_equal"])
        with self.assertRaisesRegex(ValueError, "both selected"):
            audit.audit(self.events[:-1], **kwargs)

    def test_independent_audit_rejects_wrong_rank_step_and_coordinates(self):
        audit, kwargs = self.audit_ready()
        for field, value in [("rank", 2), ("step", 4)]:
            corrupt = copy.deepcopy(self.events)
            corrupt[-1][field] = value
            with self.assertRaises(ValueError):
                audit.audit(corrupt, **kwargs)
        corrupt = copy.deepcopy(self.events)
        corrupt[-2]["stored_sample"][0]["coordinates"]["head"] = 1
        with self.assertRaisesRegex(ValueError, "coordinate"):
            audit.audit(corrupt, **kwargs)

    def test_preexisting_target_refused(self):
        self.write()
        self.handle.uninstall()
        with self.assertRaisesRegex(ValueError, "before target"):
            observer.install(self.store, segment_hash=b"a",
                layers={"kv": "attn", "gdn": "gdn"}, emit=self.events.append,
                rank=0, context=lambda: self.identity, request_id="target")


if __name__ == "__main__":
    unittest.main()

"""CPU controls for HOST R28; synthetic device receipts are not NPU proof."""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

WORKSTREAM = Path(__file__).resolve().parent.parent
if str(WORKSTREAM) not in sys.path:
    sys.path.insert(0, str(WORKSTREAM))

from host_audits import r28_quality_terminal as target
from independent_quality_schedule import quality_schedule
from independent_segment_selection import token_digest
from audit_catalog_quality_hot import audit_catalog_hot

RULER = Path("/cache/cch/model-tuning-lab-hypic-e2e-20261006/.agents/workstreams/"
             "WS-20260904-qwen38-dense-paper-to-ascend/hypic_quality_eval.py")


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


class TerminalControls(unittest.TestCase):
    """Actual reviewed controller/scorer bytes; all runtime records synthetic."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="hypic-r28-cpu-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.raw = self.base / "raw"
        self.raw.mkdir()
        self.sources = {}
        for name in (target.CONTROLLER_NAME, target.BASE_CONTROLLER_NAME):
            data = (WORKSTREAM / name).read_bytes()
            (self.base / name).write_bytes(data)
            self.sources[name] = hashlib.sha256(data).hexdigest()
        (self.base / "bound-helper.py").write_text("# synthetic source guard fixture\n")
        self.sources["bound-helper.py"] = hashlib.sha256(
            (self.base / "bound-helper.py").read_bytes()).hexdigest()
        public = {i: [1000 + i] * 16 for i in range(127)}
        public[86] = public[22]
        self.rows = [
            {"index": i, "sample_id": "sample-" + str(i), "reference": "A",
             "token_ids": [91, 92, 93, 94] + public[i] + [95],
             "segment": {"start": 4, "end": 20,
                         "tokens_sha256": token_digest(public[i])}}
            for i in range(127)]
        segments = list({tuple(t): t for t in public.values()}.values())
        self.inputs = {
            "schema": "hypic-quality-inputs/v1", "repetitions": 3,
            "generation": {"max_tokens": 1024, "temperature": 0, "seed": 0,
                           "ignore_eos": False, "enable_thinking": False},
            "requests": self.rows}
        self.catalog = {"schema": "hypic-public-catalog/v1",
                        "public_segments": segments}
        self.results = []
        self.journal = []
        for block in quality_schedule(self.rows, batch_samples=8):
            rep, batch = block["repetition"], block["batch"]
            for digest in block["producer_digests"]:
                self.journal.append({
                    "event": "quality-public-producer", "scored": False,
                    "repetition": rep, "batch": batch, "segment_sha256": digest,
                    "response": {"id": f"producer-{rep}-{batch}-{digest}",
                                 "usage": {"prompt_tokens": 16, "completion_tokens": 1},
                                 "choices": [{"finish_reason": "stop"}]}})
            for index in block["sample_indexes"]:
                row = self.rows[index]
                item = {
                    "index": index, "repetition": rep, "sample_id": row["sample_id"],
                    "segment_sha256": row["segment"]["tokens_sha256"],
                    "attempts": 1, "retries": 0, "ok": True,
                    "request_id": f"private-{rep}-{index}",
                    "response_text": "A",
                    "response_sha256": hashlib.sha256(b"A").hexdigest(),
                    "prediction": "A", "correct": True, "completion_tokens": 1,
                    "finish_reason": "stop", "truncated": False}
                self.results.append(item)
                self.journal.append(dict(item, event="quality-scored-response", scored=True))
        self.unit = {"requests": 381, "successful": 381, "correct": 381,
                     "retries": 0, "concurrency_bound": 8, "results": self.results}
        cid = "a" * 64
        self.start = {"container_id": cid, "image": "synthetic-image",
                      "devices": ["/dev/davinci" + str(i) for i in range(4)]}
        self.release = {"owned_container": cid, "removed": True, "port_free": True,
                        "final_physical_processes": []}
        self.samples = [{"foreign": [], "owners": [
            {"owned": True, "ownership_status": "owned-cgroup",
             "cgroup": "/" + cid, "npu": i} for i in range(4)]}]
        self.result = {"valid": True, "error": None, "guard_errors": [],
                       "responses": 381, "isolation_samples": 1,
                       "release": self.release}
        self.launch = {"controller_sha256": target.CONTROLLER_SHA256,
                       "diagnostic_sources": None, "argv": []}
        self.contract = {
            "formal_quality": True, "formal_performance": False,
            "formal_quality_canary": False, "physical_npus": [0, 1, 2, 3], "tp": 4,
            "enable_thinking": False, "max_output_tokens": 1024,
            "enable_prefix_caching": False, "image": "synthetic-image", "port": 8233,
            "raw_root": str(self.raw), "controller_sha256": target.CONTROLLER_SHA256,
            "baseline_host_source_sha256": self.sources,
            "quality_workload": {"inputs": {}, "catalog": {},
                                 "ruler_path": str(RULER), "batch_samples": 8}}
        self.cp = self.base / "quality.json"
        self.flush()

    def flush(self):
        for name, value in (("inputs", self.inputs), ("catalog", self.catalog)):
            path = self.base / (name + ".json")
            write_json(path, value)
            self.contract["quality_workload"][name] = {
                "path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        for name, value in (("result.json", self.result), ("responses.json", self.results),
                            ("quality-unit.json", self.unit), ("service-start.json", self.start),
                            ("release.json", self.release), ("isolation.json", self.samples),
                            ("launch.json", self.launch)):
            write_json(self.raw / name, value)
        journal = ([{"event": "isolation", "snapshot": x} for x in self.samples]
                   + self.journal + [{"event": "terminal", "result": self.result}])
        (self.raw / "events.jsonl").write_text(
            "".join(json.dumps(x) + "\n" for x in journal), encoding="utf-8")
        write_json(self.cp, self.contract)

    def reject(self, mutate):
        mutate()
        self.flush()
        with self.assertRaises((ValueError, OSError)):
            target.audit(self.cp)

    def update_result(self, **fields):
        self.results[0].update(fields)
        scored = next(x for x in self.journal if x["event"] == "quality-scored-response")
        scored.update(fields)

    def test_actual_r23_full381_and_real_r16_are_accepted(self):
        out = target.audit(self.cp)
        self.assertEqual(out["controller_identity"]["sha256"], target.CONTROLLER_SHA256)
        self.assertTrue(out["controller_identity"]["retained_r16_base_bound"])
        self.assertEqual(out["cohort"]["requests"], 381)
        self.assertEqual(out["quality_acceptance"], "NOT_DECIDED")
        self.assertFalse(out["live_release_verified"])

    def test_126_digests_keep_all127_samples_and381_scored(self):
        out = target.audit(self.cp)
        self.assertEqual(len(self.catalog["public_segments"]), 126)
        self.assertEqual(out["cohort"]["samples"], 127)
        self.assertEqual(out["cohort"]["requests"], 381)
        self.assertEqual(out["cohort"]["unscored_producers"], 381)

    def test_no_r16_import_requirement_is_invented(self):
        del self.sources[target.BASE_CONTROLLER_NAME]
        self.flush()
        self.assertFalse(target.audit(self.cp)["controller_identity"]["retained_r16_base_bound"])

    def test_missing_r23_cannot_use_old_r16_entry(self):
        self.reject(lambda: self.sources.pop(target.CONTROLLER_NAME))

    def test_old_r16_hash_cannot_claim_controller(self):
        self.reject(lambda: self.contract.update(controller_sha256=target.BASE_CONTROLLER_SHA256))

    def test_r23_hash_cannot_alias_retained_r16_entry(self):
        self.reject(lambda: self.sources.update({target.BASE_CONTROLLER_NAME: target.CONTROLLER_SHA256}))

    def test_renamed_r16_bytes_cannot_claim_r23(self):
        def mutate():
            data = (self.base / target.BASE_CONTROLLER_NAME).read_bytes()
            (self.base / target.CONTROLLER_NAME).write_bytes(data)
            self.sources[target.CONTROLLER_NAME] = hashlib.sha256(data).hexdigest()
            self.contract["controller_sha256"] = self.sources[target.CONTROLLER_NAME]
            self.launch["controller_sha256"] = self.sources[target.CONTROLLER_NAME]
        self.reject(mutate)

    def test_wrong_launch_controller_report(self):
        self.reject(lambda: self.launch.update(controller_sha256=target.BASE_CONTROLLER_SHA256))

    def test_actual_controller_file_drift(self):
        self.reject(lambda: (self.base / target.CONTROLLER_NAME).write_bytes(b"changed"))

    def test_bound_dependency_file_drift(self):
        self.reject(lambda: (self.base / "bound-helper.py").write_bytes(b"changed"))

    def test_shortened_response_inventory(self):
        self.reject(lambda: self.results.pop())

    def test_shortened_terminal_denominator(self):
        self.reject(lambda: self.result.update(responses=380))

    def test_shortened_unit_denominator(self):
        self.reject(lambda: self.unit.update(requests=380, successful=380))

    def test_failed_terminal_is_not_promoted(self):
        self.reject(lambda: self.result.update(valid=False))

    def test_retry_is_not_hidden(self):
        self.reject(lambda: self.update_result(attempts=2, retries=1))

    def test_failed_request_is_not_filtered(self):
        self.reject(lambda: self.update_result(ok=False, correct=False))

    def test_nonthinking1024_cannot_silently_change(self):
        self.reject(lambda: self.contract.update(enable_thinking=True, max_output_tokens=2048))

    def test_ignore_eos_cannot_silently_change(self):
        self.reject(lambda: self.inputs["generation"].update(ignore_eos=True))

    def test_stop_and_length_are_both_scored(self):
        self.update_result(finish_reason="length", completion_tokens=1024, truncated=True)
        self.flush()
        out = target.audit(self.cp)["cohort"]
        self.assertEqual((out["correct"], out["truncated"], out["natural_stop"]), (381, 1, 380))

    def test_above1024_is_rejected(self):
        self.reject(lambda: self.update_result(completion_tokens=1025))

    def test_hidden_length_truncation_is_rejected(self):
        self.reject(lambda: self.update_result(finish_reason="length", truncated=False))

    def test_wrong_end_reason_is_rejected(self):
        self.reject(lambda: self.update_result(finish_reason="abort"))

    def test_stored_score_is_independently_checked(self):
        self.reject(lambda: self.update_result(correct=False))

    def test_foreign_process_evidence_is_rejected(self):
        self.reject(lambda: self.samples[0].update(foreign=[{"pid": 9999}]))

    def test_incomplete_release_is_rejected(self):
        self.reject(lambda: self.release.update(removed=False))

    def test_wrong_physical_devices_are_rejected(self):
        self.reject(lambda: self.start.update(devices=["/dev/davinci4"]))

    def test_baseline_cannot_load_treatment(self):
        self.reject(lambda: self.launch.update(argv=["INDEPENDENT_COMPACT_HYPIC=1"]))


class SharedGenerationControls(unittest.TestCase):
    """Pure catalog audit controls, not device evidence or a smaller full run."""

    def fixture(self, *, rebuild=False):
        rows = [{"index": i, "segment": {"tokens_sha256": "shared", "start": 4, "end": 20}}
                for i in range(127)]
        results = [{"ok": True, "request_id": "api-" + str(i), "index": i,
                    "segment_sha256": "shared"} for i in range(2)]
        events = []
        for rank in range(4):
            common = {"rank": rank, "pid": rank + 100, "manifest_sha256": "m"}
            def publish(offset=0):
                for pool, count, kind in (
                    ("linear", 48, "compact_public_state_published"),
                    ("kv", 16, "compact_public_kv_published")):
                    for layer in range(count):
                        events.append(dict(common, event=kind, pool=pool, key=pool+str(layer),
                                           layer=pool+str(layer), generation=offset+layer+1,
                                           tokens_sha256="shared"))
            publish()
            for i in range(2):
                offset = 0
                if rebuild and i == 1:
                    for pool, count in (("linear", 48), ("kv", 16)):
                        for layer in range(count):
                            events.append(dict(common, event="compact_public_material_evicted",
                                               pool=pool, key=pool+str(layer), generation=layer+1))
                    publish(1000)
                    offset = 1000
                rid, step = "api-" + str(i) + "-runtime", i + 1
                events.append(dict(common, event="native_request_progress", request_id=rid,
                                   step=step, scheduled_tokens=64, computed_tokens=0))
                events.append(dict(common, event="compact_model_rows_completed",
                                   request_ids=[rid], step=step, original_rows=64, retained_rows=56))
                for pool, count, kind, skip in (
                    ("linear", 48, "compact_gdn_body_composed", "skipped_body_tokens"),
                    ("kv", 16, "compact_c2_queries_completed", "skipped_body_queries")):
                    for layer in range(count):
                        events.append(dict(common, event=kind, request_id=rid, step=step,
                                           layer=pool+str(layer), generation=offset+layer+1,
                                           retained_rows=56, finite=True, **{skip: 8}))
        return events, results, rows

    def audit(self, args, *, expected=2):
        return audit_catalog_hot(*args, manifest_sha256="m", expected_count=expected)

    def test_shared_live_generation_serves_distinct_requests(self):
        out = self.audit(self.fixture())
        self.assertEqual(out["denominator"], 2)
        self.assertEqual(out["generation_links"], 2*4*64)

    def test_rebuilt_live_generation_is_accepted(self):
        self.assertTrue(self.audit(self.fixture(rebuild=True))["accepted_catalog_hot_coverage"])

    def test_stale_pre_eviction_generation_is_rejected(self):
        events, results, rows = self.fixture(rebuild=True)
        event = next(x for x in events if x["event"] == "compact_gdn_body_composed"
                     and x["step"] == 2)
        event["generation"] = 1
        with self.assertRaises(ValueError):
            self.audit((events, results, rows))

    def test_shared_material_does_not_relax_full381_denominator(self):
        with self.assertRaises(ValueError):
            self.audit(self.fixture(), expected=381)


if __name__ == "__main__":
    unittest.main()


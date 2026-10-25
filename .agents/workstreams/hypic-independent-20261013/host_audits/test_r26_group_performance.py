"""Focused HOST composition controls only; mocked physical base is not NPU proof."""
from contextlib import ExitStack, contextmanager
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import r26_group_performance as audit
from native_pdc_metrics import audit_delta
from audit_formal_full40_pdc import audit_full40_pdc, bind_full40_pic_starts

MANIFEST = "a" * 64
WORKERS = {rank: 100 + rank for rank in range(4)}
LAYERS = ["layer-" + str(i) for i in range(16)]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def metrics(total, queries, hits, *, running=0):
    labels = 'engine="0",model_name="qwen3.5"'
    values = {"prefix_cache_queries_total": queries, "prefix_cache_hits_total": hits,
              "num_requests_running": running, "num_requests_waiting": 0}
    rows = ["vllm:" + name + "{" + labels + "} " + str(value)
            for name, value in values.items()]
    for reason in ("stop", "length", "abort", "error", "repetition"):
        rows.append('vllm:request_success_total{' + labels
                    + ',finished_reason="' + reason + '"} '
                    + str(total if reason == "length" else 0))
    return "\n".join(rows) + "\n"


def profile(group):
    algorithm = group in ("G3", "G4")
    pdc = group in ("G2", "G4")
    cfg = dict(prefill_prompt_snapshot=True, prompt_snapshot_probe_batches=0,
        c1_performance_mode=True, c1_layer_shadow_validation=False,
        c1_first_divergence=False, c1_async_material_verify=False,
        c1_async_material_transfer=algorithm, c1_lazy_initial_snapshot=algorithm,
        c1_partitioned_render=algorithm, c1_packed_wave=True,
        native_decode_batch=True, c1_layer_completion_barrier=True,
        c2_layer_completion_barrier=True, forward_metadata_snapshot=algorithm,
        c2_layer_finite_gate=algorithm, c1_short_suffix_recurrent=algorithm,
        c2_block_table_snapshot=algorithm, c2_block_table_diagnostic=algorithm)
    c = dict(performance_group=group, formal_performance=True, formal_quality=False,
        enable_prefix_caching=pdc, physical_npus=[0, 1, 2, 3], tp=4,
        enforce_eager=True, performance_round=1,
        protocol_notes={"timed_diagnostics": False},
        transfer_treatment="async" if algorithm else "native",
        lazy_snapshot_treatment="on" if algorithm else "native",
        r18_partitioned_acceptance={"enabled": algorithm},
        successor_manifest="manifest.json",
        independent_acceptance={"require_hypic_markers_absent": not algorithm})
    if algorithm:
        c["cache_diagnostic"] = {"compact_manifest": "manifest.json"}
        c["c2_snapshot_acceptance"] = dict(enabled=True,
            group_source="verified-native-full-attention-spec", layers=LAYERS)
    return c, cfg


@contextmanager
def cwd(path):
    old = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


class PolicyTests(unittest.TestCase):
    def test_four_actual_axes_are_not_relabelled(self):
        for group in ("G1", "G2", "G3", "G4"):
            c, cfg = profile(group)
            before = deepcopy(c)
            result = audit.validate_policy(c, cfg)
            self.assertEqual(result, dict(group=group,
                algorithm_on=group in ("G3", "G4"), pdc_on=group in ("G2", "G4")))
            self.assertEqual(c, before)

    def test_group_pdc_contradictions_and_truthy_boolean_rejected(self):
        for group in ("G1", "G2", "G3", "G4"):
            for value in (not profile(group)[0]["enable_prefix_caching"], 1, 0):
                c, cfg = profile(group)
                c["enable_prefix_caching"] = value
                with self.subTest(group=group, value=value), self.assertRaises(ValueError):
                    audit.validate_policy(c, cfg)

    def test_native_group_cannot_install_algorithm_or_omit_absence_gate(self):
        for group in ("G1", "G2"):
            c, cfg = profile(group)
            c["cache_diagnostic"] = {"compact_manifest": "manifest.json"}
            with self.assertRaises(ValueError):
                audit.validate_policy(c, cfg)
            c, cfg = profile(group)
            c["independent_acceptance"]["require_hypic_markers_absent"] = False
            with self.assertRaises(ValueError):
                audit.validate_policy(c, cfg)

    def test_algorithm_group_must_bind_actual_manifest_and_safety_profile(self):
        for group in ("G3", "G4"):
            c, cfg = profile(group)
            c["cache_diagnostic"]["compact_manifest"] = "other.json"
            with self.assertRaises(ValueError):
                audit.validate_policy(c, cfg)
            for field in ("c1_short_suffix_recurrent", "c2_layer_finite_gate",
                          "c2_block_table_snapshot", "c2_block_table_diagnostic",
                          "c1_layer_completion_barrier"):
                c, cfg = profile(group)
                cfg[field] = False
                with self.subTest(group=group, field=field), self.assertRaises(ValueError):
                    audit.validate_policy(c, cfg)

    def test_transfer_lazy_partition_and_timed_invariants_preserved(self):
        for change in ("transfer", "lazy", "partition", "shadow", "probe",
                       "verify", "performance", "diagnostics", "eager"):
            c, cfg = profile("G4")
            if change == "transfer": c["transfer_treatment"] = "native"
            if change == "lazy": c["lazy_snapshot_treatment"] = "native"
            if change == "partition": cfg["c1_partitioned_render"] = False
            if change == "shadow": cfg["c1_layer_shadow_validation"] = True
            if change == "probe": cfg["prompt_snapshot_probe_batches"] = 1
            if change == "verify": cfg["c1_async_material_verify"] = True
            if change == "performance": cfg["c1_performance_mode"] = False
            if change == "diagnostics": c["protocol_notes"]["timed_diagnostics"] = True
            if change == "eager": c["enforce_eager"] = False
            with self.subTest(change=change), self.assertRaises(ValueError):
                audit.validate_policy(c, cfg)

    @staticmethod
    def timed_partition_events():
        """A valid small partition isolates inherited policy, not full40 proof."""
        c, cfg = profile("G4")
        events = [dict(cfg, event="compact_hypic_hooks_installed", pid=pid,
                       rank=rank, manifest_sha256=MANIFEST)
                  for rank, pid in WORKERS.items()]
        for rank, pid in WORKERS.items():
            common = dict(rank=rank, pid=pid, manifest_sha256=MANIFEST,
                          step=1, layer="linear-0")
            events.append(dict(common, event="c1_packed_wave_prepared",
                state_schedule="partitioned", state_passes=1,
                actual_slot_commit="not_started", windows=1, packed_tokens=8,
                state_window_visits=1, state_token_visits=8, requests=["rid-0"]))
            events.append(dict(common, event="compact_gdn_body_composed",
                               request_id="rid-0", finite=True))
        return c, cfg, events

    def test_full_copy_diagnostic_rejected_with_otherwise_correct_transfer_flags(self):
        c, cfg, events = self.timed_partition_events()
        # Keep the real inherited partition audit in the R26 call chain.
        # Only later, independent metadata/finite/snapshot joins are isolated.
        with ExitStack() as stack:
            for name in ("validate_lazy_receipts", "audit_metadata_receipts",
                         "audit_finite_receipts", "audit_snapshot_receipts"):
                stack.enter_context(patch.object(audit, name, return_value={}))
            good = audit._algorithm_evidence(c, cfg,
                {"hot": {"worker_pids": WORKERS}}, events, MANIFEST, True)
            self.assertTrue(good["partition"]["enabled"])
            events.append(dict(event="c1_private_material_transfer_verified",
                               manifest_sha256=MANIFEST))
            with self.assertRaisesRegex(ValueError, "diagnostic overhead"):
                audit._algorithm_evidence(c, cfg,
                    {"hot": {"worker_pids": WORKERS}}, events, MANIFEST, True)

    def test_native_any_install_rejected_even_with_partition_disabled(self):
        for group in ("G1", "G2"):
            c, cfg = profile(group)
            self.assertFalse(audit._algorithm_evidence(
                c, cfg, {}, [], MANIFEST, False)["partition"]["enabled"])
            event = dict(cfg, event="compact_hypic_hooks_installed",
                         pid=WORKERS[0], rank=0, manifest_sha256=MANIFEST)
            self.assertIs(event["c1_partitioned_render"], False)
            with self.subTest(group=group), self.assertRaisesRegex(
                    ValueError, "algorithm event in native arm"):
                audit._algorithm_evidence(c, cfg, {}, [event], MANIFEST, False)

    def test_algorithm_requires_exactly_four_unique_install_receipts(self):
        _, _, original = self.timed_partition_events()
        self.assertTrue(audit.audit_timed_partition(
            original, MANIFEST, enabled=True)["enabled"])
        for change in ("missing", "extra", "duplicate_pid"):
            events = deepcopy(original)
            if change == "missing":
                events.pop(0)
            elif change == "extra":
                events.insert(0, dict(events[0]))
            else:
                events[1]["pid"] = events[0]["pid"]
            with self.subTest(change=change), self.assertRaisesRegex(
                    ValueError, "exact four-worker timed partition installation"):
                audit.audit_timed_partition(events, MANIFEST, enabled=True)

    def test_algorithm_proof_absence_is_not_excused_by_group_allowance(self):
        c, cfg = profile("G4")
        with self.assertRaises(ValueError):
            audit._algorithm_evidence(c, cfg, {"hot": {"worker_pids": WORKERS}},
                                      [], MANIFEST, True)

    def test_host_source_binding_and_runtime_separation(self):
        c = {"r26_host_audit": {"source_sha256": {audit._SELF: sha(audit.__file__)}}}
        self.assertEqual(audit._host_binding(c, audit._WS), c["r26_host_audit"]["source_sha256"])
        c["r26_host_audit"]["source_sha256"][audit._SELF] = "b" * 64
        with self.assertRaises(ValueError):
            audit._host_binding(c, audit._WS)


class CompositionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="r26-host-tests-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def fixture(self, group):
        base = self.root / group
        base.mkdir()
        raw = base / "raw"
        (raw / "diagnostics").mkdir(parents=True)
        c, cfg = profile(group)
        c.update(raw_root=str(raw), image="fixture-image", task_id="fixture-task",
                 controller_sha256=sha(audit._WS / "formal_r15_tp4.py"))
        config = base / "config.json"
        config.write_text(json.dumps(cfg))
        manifest = base / "manifest.json"
        manifest.write_text(json.dumps({"config": "config.json",
                                       "source_sha256": {"config.json": sha(config)}}))
        sources = {"manifest.json": sha(manifest)}
        if group in ("G3", "G4"):
            c["cache_diagnostic"]["source_sha256"] = sources
            events = []
            for rank, pid in WORKERS.items():
                event = dict(cfg, event="compact_hypic_hooks_installed", pid=pid,
                             rank=rank, manifest_sha256=sha(manifest))
                events.append(event)
            (raw / "diagnostics" / "compact-worker-fixture.jsonl").write_text(
                "\n".join(json.dumps(x) for x in events) + "\n")
        else:
            c["baseline_host_source_sha256"] = sources
        if group in ("G2", "G4"):
            c["native_pdc_metrics"] = {
                "official_logger_sha256": "ce2a0535d2b2b69e4368f34b692dac081be764e8d0eadab4f791b1afdcf43df4",
                "source_sha256": {name: sha(audit._WS / name) for name in (
                    "native_pdc_metrics.py", "formal_pdc_metrics_tp4.py",
                    "audit_native_pdc_metrics_terminal.py")}}
        prior_raw = base / "prior-raw"
        prior_raw.mkdir()
        for name in ("result.json", "responses.json", "release.json"):
            (prior_raw / name).write_text("{}")
        prior = base / "canary.json"
        prior.write_text(json.dumps({"controller_sha256": c["controller_sha256"],
                                     "raw_root": str(prior_raw)}))
        proof = dict(arm="ON", contract=prior.name, contract_sha256=sha(prior),
            raw_root=str(prior_raw), raw_sha256={name: sha(prior_raw / name) for name in
                ("result.json", "responses.json", "release.json")},
            audit={"bounded_canary_valid": True, "live_release_verified": True})
        accepted = base / "accepted.json"
        accepted.write_text(json.dumps(proof))
        c.update(required_canary_contract=prior.name, required_canary_sha256=sha(prior),
                 numerical_prerequisite_evidence={"path": accepted.name, "sha256": sha(accepted)})
        cp = base / "contract.json"
        cp.write_text(json.dumps(c))
        if group in ("G2", "G4"):
            (raw / "service-start.json").write_text(json.dumps({"container_id": "fixture-cid"}))
            before, after = metrics(4, 1000, 100), metrics(44, 1000000, 400000)
            receipt = dict(schema="native-pdc-metrics/v1", container_id="fixture-cid",
                image=c["image"], contract_sha256=sha(cp),
                official_logger_sha256=c["native_pdc_metrics"]["official_logger_sha256"],
                observer_sources=c["native_pdc_metrics"]["source_sha256"],
                before=before, after=after, audit=audit_delta(before, after))
            (raw / "native-pdc-observation.json").write_text(json.dumps(receipt))
        return base, cp, c, cfg

    def controls(self):
        stack = ExitStack()
        stack.enter_context(patch.object(audit, "_host_binding", return_value={"host-fixture": "pinned"}))
        base = stack.enter_context(patch.object(audit, "audit_r18_base",
            return_value={"hot": {"worker_pids": WORKERS}, "request_map": {}}))
        partition = stack.enter_context(patch.object(audit, "audit_timed_partition", return_value={"verified": True}))
        for name in ("validate_lazy_receipts", "audit_metadata_receipts",
                     "audit_finite_receipts", "audit_snapshot_receipts"):
            stack.enter_context(patch.object(audit, name, return_value={"verified": True}))
        g4 = stack.enter_context(patch.object(audit, "_g4_pdc_evidence", return_value={"full40_pdc_observed": True}))
        return stack, base, partition, g4

    def test_four_group_dispatch_retains_real_names_and_release_gate(self):
        for group in ("G1", "G2", "G3", "G4"):
            base, cp, c, cfg = self.fixture(group)
            stack, physical, partition, g4 = self.controls()
            with stack, cwd(base):
                result = audit.audit(cp, live_release=True)
            physical.assert_called_once_with(cp, live_release=True)
            self.assertEqual(result["r26_host_audit"]["group"], group)
            self.assertEqual(json.loads(cp.read_text())["performance_group"], group)
            self.assertEqual(partition.call_args.kwargs["enabled"], group in ("G3", "G4"))
            self.assertEqual("native_pdc_observed" in result, group in ("G2", "G4"))
            self.assertEqual(g4.call_count, int(group == "G4"))
            self.assertEqual("c2_block_table_snapshot" in result, group in ("G3", "G4"))

    def test_real_prerequisite_gate_accepts_bound_on_report_and_raw(self):
        base, cp, c, cfg = self.fixture("G1")
        proof = audit._prerequisite(c, base)
        self.assertEqual(proof["contract"], "canary.json")
        self.assertEqual(set(proof["raw_sha256"]),
                         {"result.json", "responses.json", "release.json"})

    def test_prerequisite_controller_contract_report_raw_and_digest_drift_rejected(self):
        base, cp, c, cfg = self.fixture("G1")
        accepted = base / "accepted.json"
        original_proof = json.loads(accepted.read_text())
        for field, value in (("arm", "OFF"), ("contract", "other.json"),
                             ("contract_sha256", "b" * 64),
                             ("raw_root", str(base / "unrelated-raw")),
                             ("audit", {"bounded_canary_valid": True, "live_release_verified": False}),
                             ("raw_sha256", {})):
            proof = dict(original_proof)
            proof[field] = value
            accepted.write_text(json.dumps(proof))
            changed = deepcopy(c)
            changed["numerical_prerequisite_evidence"]["sha256"] = sha(accepted)
            with self.subTest(field=field), self.assertRaises(ValueError):
                audit._prerequisite(changed, base)
        accepted.write_text(json.dumps(original_proof))
        for field in ("required_canary_sha256", "controller_sha256"):
            changed = deepcopy(c)
            changed[field] = "b" * 64
            with self.subTest(field=field), self.assertRaises(ValueError):
                audit._prerequisite(changed, base)
        changed = deepcopy(c)
        changed["numerical_prerequisite_evidence"]["sha256"] = "b" * 64
        with self.assertRaises(ValueError):
            audit._prerequisite(changed, base)
        (base / "prior-raw" / "result.json").write_text('{"valid": false}')
        with self.assertRaises(ValueError):
            audit._prerequisite(c, base)

    def test_pdc_observer_source_drift_rejected_before_physical_base(self):
        base, cp, c, cfg = self.fixture("G2")
        c["native_pdc_metrics"]["source_sha256"]["native_pdc_metrics.py"] = "b" * 64
        cp.write_text(json.dumps(c))
        stack, physical, _, _ = self.controls()
        with stack, cwd(base), self.assertRaises(ValueError):
            audit.audit(cp)
        physical.assert_not_called()

    def test_pdc_receipt_source_cid_contract_logger_error_drift_rejected(self):
        base, cp, c, cfg = self.fixture("G2")
        path = base / "raw" / "native-pdc-observation.json"
        original = json.loads(path.read_text())
        changes = {"container_id": "other", "image": "other",
                   "contract_sha256": "b" * 64, "official_logger_sha256": "b" * 64,
                   "observer_sources": {}, "error": {"type": "failure"}}
        for field, value in changes.items():
            receipt = dict(original)
            receipt[field] = value
            path.write_text(json.dumps(receipt))
            with self.subTest(field=field), self.assertRaises(ValueError):
                audit._native_pdc_observation(c, cp, base / "raw")

    def test_pdc_counter_recompute_and_boundaries_cannot_be_mirrored(self):
        base, cp, c, cfg = self.fixture("G2")
        path = base / "raw" / "native-pdc-observation.json"
        original = json.loads(path.read_text())
        for after in (metrics(45, 1000000, 400000),
                      metrics(44, 1000000, 400000, running=1),
                      metrics(44, 1000000, 100), metrics(44, 100, 100)):
            receipt = dict(original, after=after)
            path.write_text(json.dumps(receipt))
            with self.assertRaises(ValueError):
                audit._native_pdc_observation(c, cp, base / "raw")
        receipt = dict(original, audit={"aggregate_native_pdc_verified": True})
        path.write_text(json.dumps(receipt))
        with self.assertRaises(ValueError):
            audit._native_pdc_observation(c, cp, base / "raw")

    def test_g4_does_not_substitute_aggregate_for_missing_full40_pic_proof(self):
        base, cp, c, cfg = self.fixture("G4")
        stack, _, _, _ = self.controls()
        with stack, patch.object(audit, "_g4_pdc_evidence",
                                  side_effect=ValueError("missing per-request proof")), cwd(base):
            with self.assertRaisesRegex(ValueError, "per-request"):
                audit.audit(cp)

    def test_manifest_source_or_host_allowlist_drift_rejected(self):
        base, cp, c, cfg = self.fixture("G1")
        (base / "config.json").write_text("{}")
        with self.assertRaises(ValueError):
            audit._manifest(c, base)
        manifest = {"config": "config.json", "source_sha256":
                    {"config.json": sha(base / "config.json"),
                     "host_audits/r26_group_performance.py": "a" * 64}}
        (base / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaises(ValueError):
            audit._manifest(c, base)


def pdc_fixture():
    mapping = {"api-" + str(i): "rid-" + str(i) for i in range(40)}
    starts = {rid: 8192 for rid in mapping.values()}
    events, scheduler = [], []
    for rid in mapping.values():
        for rank, pid in WORKERS.items():
            events.append(dict(event="native_request_progress", request_id=rid,
                manifest_sha256=MANIFEST, rank=rank, pid=pid, step=1,
                first_observed=True, computed_tokens=7680, scheduled_tokens=4096))
        scheduler.append(dict(event="pic_scheduler_boundary_capped", request_id=rid,
            manifest_sha256=MANIFEST, native_block_size=1536,
            pic_start=8192, pic_end=8192 + 16384))
    return events, scheduler, mapping, starts


class Full40PdcControls(unittest.TestCase):
    def check(self, events, scheduler, mapping, starts):
        return audit_full40_pdc(events, scheduler, mapping, WORKERS, starts,
                               manifest_sha256=MANIFEST)

    def test_real_unchanged_helper_accepts_exact40_four_rank_prefix_evidence(self):
        evidence = pdc_fixture()
        result = self.check(*evidence)
        self.assertTrue(result["full40_pdc_observed"])
        self.assertEqual(len(result["requests"]), 40)

    def test_request_rank_initial_prefix_and_geometry_holes_rejected(self):
        for change in ("request", "rank", "prefix", "geometry", "source", "block"):
            events, scheduler, mapping, starts = pdc_fixture()
            if change == "request": events = [e for e in events if e["request_id"] != "rid-0"]
            if change == "rank": events = [e for e in events if not (e["request_id"] == "rid-0" and e["rank"] == 3)]
            if change == "prefix": events[0]["computed_tokens"] = 7679
            if change == "geometry": scheduler[0]["pic_end"] -= 1
            if change == "source": events[0]["manifest_sha256"] = "b" * 64
            if change == "block": scheduler[0]["native_block_size"] = 1024
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.check(events, scheduler, mapping, starts)

    def test_frozen_actual_input_geometry_and_missing_indices_rejected(self):
        with tempfile.TemporaryDirectory(prefix="r26-pic-tests-") as tmp:
            path = Path(tmp) / "tokens.json"
            prefix, public = [1] * 8192, [2] * 16384
            tokens = prefix + public + [3] * 8192
            artifact = {"native_prefix": prefix, "public_segment": public,
                "requests": [dict(index=i, token_ids=tokens, segment_start=8192,
                                  segment_end=24576) for i in range(40)]}
            path.write_text(json.dumps(artifact))
            mapping = {"api-" + str(i): "rid-" + str(i) for i in range(40)}
            results = [dict(index=i, ok=True, metrics={"request_id": "api-" + str(i)})
                       for i in range(40)]
            starts = bind_full40_pic_starts(str(path), sha(path), results, mapping)
            self.assertEqual(len(starts), 40)
            with self.assertRaises(ValueError):
                bind_full40_pic_starts(str(path), sha(path), results[:-1], mapping)
            artifact["requests"][0]["segment_start"] += 1
            path.write_text(json.dumps(artifact))
            with self.assertRaises(ValueError):
                bind_full40_pic_starts(str(path), sha(path), results, mapping)


if __name__ == "__main__":
    unittest.main()

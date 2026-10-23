"""Synthetic receipt controls and CPU CLI composition; not NPU evidence."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from audit_r24_c2_snapshot_canary import audit, audit_snapshot_receipts

WORKERS = {rank: 100 + rank for rank in range(4)}
MANIFEST = "a" * 64
LAYERS = ["language_model.model.layers.%d.self_attn.attn" % n
          for n in range(3, 64, 4)]
SOURCE = "verified-native-full-attention-spec"
MODEL = "compact_model_rows_completed"
CHECKED = "c2_block_table_snapshot_layer_checked"
CAPTURE = "compact_native_attention_groups_captured"
HOT = "compact_c2_queries_completed"
NATIVE = "mixed_native_c2_completed"
INSTALL = "compact_hypic_hooks_installed"


def events_for(enabled=True, *, steps=(7,), manifest=MANIFEST, background=False):
    events = []
    for rank, pid in WORKERS.items():
        common = dict(rank=rank, pid=pid, manifest_sha256=manifest)
        # Actual installation event does not know rank yet; derive it by PID.
        events.append(dict(event=INSTALL, pid=pid, manifest_sha256=manifest,
            c2_block_table_snapshot=enabled, c2_block_table_diagnostic=True))
        if background:
            events.append(dict(common, event=CAPTURE, step=2,
                request_ids=["public-producer"], source=SOURCE,
                attention_groups=[dict(group=9, layers=LAYERS)]))
        for step in steps:
            ids = ["hot-%d" % step, "native-%d" % step]
            events.append(dict(common, event=CAPTURE, step=step,
                request_ids=ids, source=SOURCE,
                attention_groups=[dict(group=9, layers=list(LAYERS))]))
            for index, layer in enumerate(LAYERS):
                events.append(dict(common, event=HOT, step=step, layer=layer,
                    request_id=ids[0], query_windows=2))
                events.append(dict(common, event=NATIVE, step=step, layer=layer,
                    request_id=ids[1], query_windows=1))
                if enabled:
                    events.append(dict(common, event=CHECKED, step=step,
                        layer=layer, group=9, request_ids=ids,
                        reads_delta=1 if index == 0 else 0,
                        hits_delta=2 if index == 0 else 3))
            events.append(dict(common, event=MODEL, step=step, request_ids=ids,
                c2_block_table_snapshot=enabled,
                c2_block_table_snapshot_reads=1 if enabled else 0,
                c2_block_table_snapshot_hits=47 if enabled else 0))
    return events


def first(events, kind, rank=0):
    return next(e for e in events
                if e["event"] == kind and e.get("rank", e["pid"] - 100) == rank)


class ReceiptAuditTests(unittest.TestCase):
    def check(self, events, *, enabled=True, workers=WORKERS, **kwargs):
        return audit_snapshot_receipts(events, workers, MANIFEST,
            enabled=enabled, expected_layers=LAYERS, **kwargs)

    def reject(self, events, *, enabled=True, **kwargs):
        with self.assertRaises(ValueError):
            self.check(events, enabled=enabled, **kwargs)

    def test_valid_on_exact_join_and_counter_totals(self):
        result = self.check(events_for())
        self.assertEqual((result["forwards"], result["checked_layers"],
            result["request_layer_completions"], result["reads"], result["hits"]),
            (4, 64, 128, 4, 188))
        self.assertTrue(all(row["group"] == 9 for row in result["per_forward"]))

    def test_valid_off_keeps_real_completions_but_no_snapshot_claim(self):
        result = self.check(events_for(False), enabled=False)
        self.assertEqual((result["forwards"], result["checked_layers"],
                          result["request_layer_completions"]), (4, 0, 128))
        self.assertEqual((result["reads"], result["hits"]), (0, 0))

    def test_multiple_forwards_and_native_only_capture_are_not_false_duplicates(self):
        result = self.check(events_for(steps=(7, 8), background=True))
        self.assertEqual(result["forwards"], 8)
        self.assertEqual(result["native_captures"], 12)

    def test_missing_or_duplicate_install_rejected(self):
        rows = events_for()
        self.reject([e for e in rows if e is not rows[0]])
        rows = events_for()
        rows.insert(1, deepcopy(rows[0]))
        self.reject(rows)

    def test_install_source_pid_rank_and_mode_must_match(self):
        for key, value in (("pid", 999), ("manifest_sha256", "b" * 64),
                           ("rank", 3), ("c2_block_table_snapshot", False),
                           ("c2_block_table_diagnostic", False)):
            rows = events_for()
            first(rows, INSTALL)[key] = value
            with self.subTest(key=key):
                self.reject(rows)

    def test_every_receipt_type_source_pid_rank_and_step_are_bound(self):
        for kind in (CAPTURE, MODEL, CHECKED, HOT, NATIVE):
            for key, value in (("pid", 999), ("rank", 3), ("rank", True),
                               ("manifest_sha256", "b" * 64), ("step", 0),
                               ("step", 8)):
                rows = events_for()
                first(rows, kind)[key] = value
                with self.subTest(kind=kind, key=key, value=value):
                    self.reject(rows)

    def test_receipts_before_own_install_rejected(self):
        rows = events_for()
        rows.insert(0, rows.pop(1))
        self.reject(rows)

    def test_missing_or_duplicate_model_rejected(self):
        rows = events_for()
        selected = first(rows, MODEL)
        self.reject([e for e in rows if e is not selected])
        rows = events_for()
        rows.append(deepcopy(first(rows, MODEL)))
        self.reject(rows)

    def test_missing_or_duplicate_checked_layer_rejected(self):
        rows = events_for()
        selected = first(rows, CHECKED)
        self.reject([e for e in rows if e is not selected])
        rows = events_for()
        rows.insert(rows.index(first(rows, CHECKED)), deepcopy(first(rows, CHECKED)))
        self.reject(rows)

    def test_missing_duplicate_or_extra_request_completion_rejected(self):
        rows = events_for()
        selected = first(rows, HOT)
        self.reject([e for e in rows if e is not selected])
        rows = events_for()
        rows.insert(rows.index(first(rows, HOT)), deepcopy(first(rows, HOT)))
        self.reject(rows)
        rows = events_for()
        first(rows, HOT)["request_id"] = "unrelated-extra"
        self.reject(rows)

    def test_missing_duplicate_or_unverified_native_capture_rejected(self):
        rows = events_for()
        selected = first(rows, CAPTURE)
        self.reject([e for e in rows if e is not selected])
        rows = events_for()
        rows.insert(2, deepcopy(first(rows, CAPTURE)))
        self.reject(rows)
        rows = events_for()
        first(rows, CAPTURE)["source"] = "checked-self-assertion"
        self.reject(rows)

    def test_native_capture_exact_single_group_and_full_layers_required(self):
        for groups in ([], [dict(group=9, layers=LAYERS)] * 2,
                       [dict(group=True, layers=LAYERS)],
                       [dict(group=9, layers=LAYERS[:-1])],
                       [dict(group=9, layers=LAYERS[:-1] + [LAYERS[0]])],
                       [dict(group=9, layers=LAYERS[:-1] + ["invented-layer"])]):
            rows = events_for()
            first(rows, CAPTURE)["attention_groups"] = groups
            with self.subTest(groups=groups):
                self.reject(rows)

    def test_checked_group_must_join_independent_native_capture(self):
        for value in (8, True, None):
            rows = events_for()
            first(rows, CHECKED)["group"] = value
            with self.subTest(value=value):
                self.reject(rows)
        rows = events_for()
        for e in rows:
            if e["event"] == CHECKED:
                e["group"] = 8
        self.reject(rows)

    def test_optional_pre_frozen_group_also_constrains_native_capture(self):
        self.check(events_for(), expected_group=9)
        self.reject(events_for(), expected_group=8)

    def test_native_capture_group_must_agree_across_tp_ranks(self):
        rows = events_for()
        for e in rows:
            if e.get("rank") == 0:
                if e["event"] == CAPTURE:
                    e["attention_groups"][0]["group"] = 8
                elif e["event"] == CHECKED:
                    e["group"] = 8
        self.reject(rows)

    def test_native_capture_cohort_must_match_model_not_merely_count(self):
        rows = events_for()
        first(rows, CAPTURE)["request_ids"] = ["hot-7", "another-native"]
        self.reject(rows)

    def test_capture_must_precede_first_c2_completion(self):
        rows = events_for()
        selected = first(rows, CAPTURE)
        rows.remove(selected)
        rows.insert(rows.index(first(rows, CHECKED)), selected)
        self.reject(rows)

    def test_checked_must_follow_all_layer_completions(self):
        rows = events_for()
        selected = first(rows, CHECKED)
        rows.remove(selected)
        rows.insert(rows.index(first(rows, NATIVE)), selected)
        self.reject(rows)

    def test_model_must_follow_all_checked_layers(self):
        rows = events_for()
        selected = first(rows, MODEL)
        rows.remove(selected)
        rows.insert(rows.index(first(rows, CHECKED)), selected)
        self.reject(rows)

    def test_disabled_model_must_also_follow_real_layer_completions(self):
        rows = events_for(False)
        selected = first(rows, MODEL)
        rows.remove(selected)
        rows.insert(rows.index(first(rows, HOT)), selected)
        self.reject(rows, enabled=False)

    def test_layer_inventory_cannot_be_renamed_or_extended(self):
        for kind in (HOT, NATIVE, CHECKED):
            rows = events_for()
            first(rows, kind)["layer"] = "invented-extra"
            with self.subTest(kind=kind):
                self.reject(rows)

    def test_request_sets_must_match_model_and_checked_exactly(self):
        for kind in (MODEL, CHECKED):
            for ids in (["hot-7"], ["hot-7", "unrelated"],
                        ["hot-7", "hot-7"], ["hot-7", False]):
                rows = events_for()
                first(rows, kind)["request_ids"] = ids
                with self.subTest(kind=kind, ids=ids):
                    self.reject(rows)

    def test_query_windows_are_positive_nonboolean_counts(self):
        for value in (0, -1, True, 1.0, None):
            rows = events_for()
            first(rows, HOT)["query_windows"] = value
            with self.subTest(value=value):
                self.reject(rows)

    def test_layer_window_read_hit_conservation_required(self):
        rows = events_for()
        first(rows, HOT)["query_windows"] = 3
        self.reject(rows)
        rows = events_for()
        first(rows, CHECKED)["hits_delta"] += 1
        self.reject(rows)

    def test_model_layer_counter_conservation_required(self):
        rows = events_for()
        first(rows, MODEL)["c2_block_table_snapshot_hits"] += 1
        self.reject(rows)

    def test_exact_counter_types_and_single_cold_read_required(self):
        for kind, key, value in (
                (MODEL, "c2_block_table_snapshot_reads", True),
                (MODEL, "c2_block_table_snapshot_reads", 2),
                (MODEL, "c2_block_table_snapshot_hits", 14),
                (CHECKED, "reads_delta", False),
                (CHECKED, "hits_delta", -1)):
            rows = events_for()
            first(rows, kind)[key] = value
            with self.subTest(kind=kind, key=key, value=value):
                self.reject(rows)

    def test_cold_read_cannot_be_shifted_to_later_layer_with_same_totals(self):
        rows = events_for()
        checked = [e for e in rows if e["event"] == CHECKED and e["rank"] == 0]
        checked[0].update(reads_delta=0, hits_delta=3)
        checked[1].update(reads_delta=1, hits_delta=2)
        self.reject(rows)

    def test_off_rejects_checked_nonzero_counters_and_ambiguous_mode(self):
        rows = events_for(False)
        rows.insert(rows.index(first(rows, MODEL)), deepcopy(first(events_for(), CHECKED)))
        self.reject(rows, enabled=False)
        for key, value in (("c2_block_table_snapshot", 0),
                           ("c2_block_table_snapshot", True),
                           ("c2_block_table_snapshot_reads", 1),
                           ("c2_block_table_snapshot_hits", False)):
            rows = events_for(False)
            first(rows, MODEL)[key] = value
            with self.subTest(key=key, value=value):
                self.reject(rows, enabled=False)

    def test_four_stable_worker_inventory_is_required(self):
        for workers in ({0: 100}, {0: 100, 1: 100, 2: 102, 3: 103},
                        {0: 100, 1: 101, 2: 102, 3: True}):
            with self.subTest(workers=workers):
                self.reject(events_for(), workers=workers)

    def test_frozen_inventory_and_mode_cannot_be_ambiguous(self):
        for layers in (LAYERS[:-1], LAYERS[:-1] + [LAYERS[0]], None):
            with self.subTest(layers=layers), self.assertRaises(ValueError):
                audit_snapshot_receipts(events_for(), WORKERS, MANIFEST,
                                        enabled=True, expected_layers=layers)
        with self.assertRaises(ValueError):
            audit_snapshot_receipts(events_for(), WORKERS, MANIFEST,
                                    enabled=1, expected_layers=LAYERS)


class CompositionTests(unittest.TestCase):
    def fixture(self, tmp, enabled=True):
        base = Path(tmp)
        raw = base / "raw"
        diagnostic = raw / "diagnostics"
        diagnostic.mkdir(parents=True)
        config = dict(c2_block_table_snapshot=enabled,
                      c2_layer_completion_barrier=True,
                      c2_block_table_diagnostic=True)
        (base / "config.json").write_text(json.dumps(config))
        manifest = base / "manifest.json"
        manifest.write_text(json.dumps(dict(config="config.json")))
        digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
        rows = events_for(enabled, manifest=digest)
        for pid in WORKERS.values():
            (diagnostic / ("compact-worker-%d.jsonl" % pid)).write_text(
                "\n".join(json.dumps(e) for e in rows if e["pid"] == pid) + "\n")
        contract = dict(raw_root=str(raw),
            cache_diagnostic=dict(compact_manifest="manifest.json"),
            c2_snapshot_acceptance=dict(enabled=enabled, group_source=SOURCE,
                                        layers=LAYERS))
        path = base / "contract.json"
        path.write_text(json.dumps(contract))
        return path

    def base_result(self):
        return dict(original_numeric_gate="retained",
                    hot=dict(worker_pids={str(r): pid for r, pid in WORKERS.items()}))

    def test_cli_composition_calls_unchanged_base_with_live_release(self):
        for enabled in (True, False):
            with self.subTest(enabled=enabled), TemporaryDirectory() as tmp:
                path = self.fixture(tmp, enabled)
                with patch("audit_r24_c2_snapshot_canary.audit_base",
                           return_value=self.base_result()) as base:
                    result = audit(path, live_release=True)
                base.assert_called_once_with(path.resolve(), live_release=True)
                self.assertEqual(result["original_numeric_gate"], "retained")
                self.assertIs(result["c2_block_table_snapshot"]["enabled"], enabled)

    def test_base_numerical_or_isolation_failure_is_not_bypassed(self):
        with TemporaryDirectory() as tmp:
            path = self.fixture(tmp)
            with patch("audit_r24_c2_snapshot_canary.audit_base",
                       side_effect=ValueError("original numeric/isolation gate")):
                with self.assertRaisesRegex(ValueError, "original numeric/isolation"):
                    audit(path)

    def test_cli_rejects_unfrozen_inventory_or_config_disagreement(self):
        for mutate in (
                lambda c: c.pop("c2_snapshot_acceptance"),
                lambda c: c["c2_snapshot_acceptance"].update(group_source="self-asserted"),
                lambda c: c["c2_snapshot_acceptance"].update(enabled=False)):
            with TemporaryDirectory() as tmp:
                path = self.fixture(tmp)
                contract = json.loads(path.read_text())
                mutate(contract)
                path.write_text(json.dumps(contract))
                with patch("audit_r24_c2_snapshot_canary.audit_base",
                           return_value=self.base_result()):
                    with self.assertRaises(ValueError):
                        audit(path)

    def test_cli_diagnostic_flag_required_in_config(self):
        with TemporaryDirectory() as tmp:
            path = self.fixture(tmp)
            config_path = path.parent / "config.json"
            config = json.loads(config_path.read_text())
            config["c2_block_table_diagnostic"] = False
            config_path.write_text(json.dumps(config))
            with patch("audit_r24_c2_snapshot_canary.audit_base",
                       return_value=self.base_result()):
                with self.assertRaises(ValueError):
                    audit(path)


class DiagnosticActivationTests(unittest.TestCase):
    def run_activation(self, snapshot, diagnostic):
        from test_c2_block_table_snapshot_wiring import ActivationWiringTests
        from independent_compact_activation import activate_compact_hypic
        helper = ActivationWiringTests()
        with helper.environment(enabled=snapshot) as env:
            runner = sys.modules["independent_compact_runtime_snapshot"]
            with patch.object(runner, "activate_compact_runner",
                              wraps=runner.activate_compact_runner) as call:
                config = helper.config(snapshot)
                config["c2_block_table_diagnostic"] = diagnostic
                stop = activate_compact_hypic(config, enabled=True, emit=env.emit)
                self.assertIs(env.receipts[0]["c2_block_table_diagnostic"], diagnostic)
                self.assertNotIn("c2_block_table_diagnostic", env.stage_options[0])
                if snapshot or diagnostic:
                    self.assertIs(call.call_args.kwargs["record_attention_groups"], True)
                else:
                    self.assertNotIn("record_attention_groups", call.call_args.kwargs)
                stop()

    def test_diagnostic_only_records_native_groups_without_enabling_snapshot(self):
        self.run_activation(False, True)

    def test_snapshot_records_native_groups_even_when_diagnostic_switch_false(self):
        self.run_activation(True, False)

    def test_default_off_preserves_old_runner_signature(self):
        self.run_activation(False, False)

    def test_diagnostic_flag_is_strict_boolean(self):
        from test_c2_block_table_snapshot_wiring import ActivationWiringTests
        from independent_compact_activation import activate_compact_hypic
        helper = ActivationWiringTests()
        for value in (1, 0, None, "true"):
            with self.subTest(value=value), helper.environment(enabled=False) as env:
                config = helper.config(False)
                config["c2_block_table_diagnostic"] = value
                with self.assertRaises(ValueError):
                    activate_compact_hypic(config, enabled=True, emit=env.emit)
                self.assertEqual(env.operations, [])


if __name__ == "__main__":
    unittest.main()

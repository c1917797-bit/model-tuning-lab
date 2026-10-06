"""Synthetic in-memory receipts exercise parsing ONLY; no real NPU authority."""
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import copy
import hashlib
import json
import sys
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import contract as a

def data(value):
    return json.dumps(value, sort_keys=True, allow_nan=False).encode() + b"\n"

class Fixture:
    """Real source/build/anchor bytes, SYNTHETIC operation reports/terminals.

    Software tests authenticate neither JSON origin nor actual execution.
    """
    def __init__(self):
        self.memory = {}
        self.c = a.frozen_contract(self.read)
        self.runtime = a.json_ref(a.Ref(a.REPO + "/" + a.BASE + "/RUNTIME_MANIFEST.json", a.RUNTIME_SHA), self.read)
        self.manifest = a.Ref(str(HERE / "SOURCE_MANIFEST.json"), a.digest(self.read(str(HERE / "SOURCE_MANIFEST.json"))))
        self.runs = []
        for stage in ("isolated", "native_feedback"):
            self.runs.append(self.make_run(stage))
    def read(self, path):
        if path in self.memory:
            return self.memory[path]
        return Path(path).read_bytes()
    def put(self, path, obj):
        self.memory[path] = data(obj)
        return a.Ref(path, a.digest(self.memory[path]))
    def obj(self, ref):
        return a.json_bytes(self.read(ref.path))
    def pack(self, label, entry, origin):
        p, error, slots = entry
        status = [1, 0, 4, 16384, 0, 16384, 0, 0] if not error else (
            [0, 1, 0, 0, 0, 16384, 0, 0] if error == 1 else [0, error, 0, 0, 0, 16384, 0, 0])
        # Each hash is a software fixture tag, never actual device bytes.
        tag = label.rsplit("_", 1)[0] if "_reset_" in label else label
        return {"label": label, "p": p, "indices": slots, "status_rows": [status[:] for _ in range(12 * p)],
                "guards": {key: True for key in (a.NUMERIC_GUARDS if error in (2, 3) else a.SUCCESS_GUARDS)},
                "passed": True, "fixture_origin": origin,
                "raw_after_sha256": hashlib.sha256(tag.encode()).hexdigest()}
    def ck(self, name, details=None):
        return {"name": name, "passed": True, "details": details}
    def pack_checks(self, cases):
        rows = []
        for case in cases:
            label = case["label"]
            rows.extend((self.ck(label + "_dispatch_and_nullable_D2H", copy.deepcopy(a.HEALTH)),
                         self.ck(label + "_status_fresh_nonalias"),
                         self.ck(label + "_full_raw_inputs_status", copy.deepcopy(case["guards"]))))
        return rows
    def report(self, stage, proof, root, when):
        c = self.c
        report = {"schema": "damp-selected-prefill-npu-gate/v1", "stage": stage,
                  "status": "isolated_selected_packing_pass" if stage == "isolated" else "native_chunk_selected_pack_feedback_pass",
                  "steps": 160, "limits": dict(c.LIMITS), "npu_executed": True, "general_sr": True,
                  "serving_ready": False, "performance_measurement_admitted": False, "graph_supported": False,
                  "float_candidate_enabled": False, "actual_runtime_soc": "Ascend910B4",
                  "schemas": a.schemas(), "completed_ns": when,
                  "bindings": {"sources": self.runtime["sources"], "dependencies": self.runtime["dependencies"],
                    "compiled_sources": c.COMPILED, "runtime_manifest": a.ref_dict(a.Ref(
                        a.REPO + "/" + a.BASE + "/RUNTIME_MANIFEST.json", a.RUNTIME_SHA)),
                    "build_receipt": {"path": "/cache/cch/qwen36-damp-20261006/selected-prefill-build-v1/build-receipt.json",
                                      "sha256": c.SELECTED_BUILD_SHA},
                    "library": {"path": "/cache/cch/qwen36-damp-20261006/selected-prefill-build-v1/build/libqwen36_damp_selected_prefill_v1_ops.so",
                                "sha256": c.SELECTED_SO_SHA},
                    "image_id": c.IMAGE, "opp_version_info_sha256": c.OPP_SHA, "device_proof": proof}}
        if stage == "isolated":
            matrix = a.pack_matrix(c)
            report["cases"] = [self.pack(label, entry, "CPU-FP32-isolated-not-native") for label, entry in matrix.items()]
            report.update(native_prefill_verified=False, decode_feedback_verified=False, fixture_origin="CPU-FP32-isolated-not-native")
            report["host_negatives"] = [{"label": label, "passed": True} for label in a.host_labels()]
            report["retired_calls"] = [{"label": label, "slots": value[2], "retry_allowed": False, "whole_call": True}
                                       for label, value in matrix.items() if value[1] in (2, 3)]
            checks = self.pack_checks(report["cases"])
            for _ in range(4):
                checks.extend((self.ck("prepare_dispatch", copy.deepcopy(a.HEALTH)),
                               self.ck("prepare_all_inputs_full_raw_unchanged")))
            checks.extend(self.ck("identical_reset_determinism") for _ in range(32))
            checks.extend(self.ck(label + "_rejected_all_inputs_raw_unchanged", {
                "dispatch_error": {"error": "synthetic expected TORCH_CHECK", "traceback": "synthetic fixture"}})
                          for label in a.host_labels())
            report["checks"] = checks
            negative_labels = {label for label, row in matrix.items() if row[1]} | set(a.host_labels())
            report["artifacts"] = [{"path": root + "/negative_" + label + ".pt", "copy_errors": []}
                                   for label in sorted(negative_labels)]
            for row in report["artifacts"]:
                self.memory[row["path"]] = b"SYNTHETIC raw artifact, not torch serialization"
        else:
            matrix = a.native_matrix(c)
            report["cases"] = [self.pack(label, entry, "actual_native_chunk_FP32_final") for label, entry in matrix.items()]
            report.update(native_prefill_verified=True, decode_feedback_verified=True)
            checks = self.pack_checks(report["cases"])
            for name in ("actual_native_chunk_dispatch", "native_chunk_all_inputs_and_packed_arena_immutable",
                         "native_pack_prepare_dispatch", "native_pack_prepare_entire_inputs_raw_immutable",
                         "decode_prepare_dispatch", "decode_prepare_all_inputs_raw_immutable"):
                checks.extend(self.ck(name, copy.deepcopy(a.HEALTH) if name.endswith("_dispatch") else None) for _ in range(8))
            for name in ("selected_unpack_dispatch", "selected_unpack_all_inputs_raw_immutable",
                         "service_unpack_vs_independent_FP32_bitwise"):
                checks.extend(self.ck(name, copy.deepcopy(a.HEALTH) if name.endswith("_dispatch") else None) for _ in range(4))
            cases = []
            for label, entry in matrix.items():
                p = entry[0]
                steps = []
                for i in range(160):
                    metric = {"finite": True, "relative_l2": 0.0, "max_head_relative_l2": 0.0,
                              "max_absolute": 0.0, "expected_norm": 1.0}
                    row = {"step": i + 1, "indices": c.selection(p, p + 3, i),
                           "metrics": {key: dict(metric) for key in ("selected_state", "complete_state", "output")},
                           "guards": {key: True for key in a.FEEDBACK_GUARDS}, "passed": True,
                           # False is legitimate diagnostic, NOT a numerical failure.
                           "packed_bitwise_diagnostic": {"high": True, "low": False, "scales": True}}
                    steps.append(row)
                    checks.extend((self.ck("decode_dispatch", copy.deepcopy(a.HEALTH)),
                                   self.ck(label + "_step_" + str(i + 1), copy.deepcopy(row))))
                cases.append({"label": label + "_feedback", "stage": "prefill_seeded_decode",
                              "p": p, "status": "passed", "steps": steps})
            report["checks"], report["feedback_cases"] = checks, cases
            anchor_path = "/cache/cch/qwen36-damp-20261006/production-integer-compaction-general-v1/gate/report.json"
            native = c.validate_anchor(a.json_ref(a.Ref(anchor_path, a.ANCHOR_SHA), self.read))
            report["native_bindings"] = {"anchor_path": anchor_path, "anchor_sha256": a.ANCHOR_SHA,
                "native_runtime": native,
                "reference_library": "/cache/cch/qwen36-damp-20261006/native-sr-reference-build-v1/libqwen36_damp_native_reference_ops.so",
                "reference_library_sha256": a.REFERENCE_SO,
                "decode_library": "/cache/cch/qwen36-damp-20261006/all-batch-wrapper-v3-build-v1/cmake/libqwen36_gdn_damp_all_batch_v3_decode_ops.so",
                "decode_library_sha256": c.ALL_BATCH_SO_SHA, "decode_build_receipt_sha256": c.ALL_BATCH_BUILD_SHA}
        return report
    def make_run(self, stage):
        root = "/cache/cch/qwen36-damp-20261006/SOFTWARE-ONLY-SYNTHETIC-" + stage
        when = 1800000000000000000
        card = 4 if stage == "isolated" else 7
        proof = {"physical_npu_ids": [card], "logical_to_physical": {"0": card}, "privileged": False,
                 "exclusive_resource_check_passed": True, "observed_at_unix_ns": when - 1000000000}
        proof_ref = self.put(root + "/owner.json", proof)
        report = self.report(stage, proof, root, when + 1000000000)
        report_ref = self.put(root + "/report.json", report)
        args = ("-B", a.REPO + "/" + a.BASE + "/run.py", "--execute", "--stage", stage,
                "--physical-card", str(card), "--preflight", proof_ref.path,
                "--build-receipt", report["bindings"]["build_receipt"]["path"],
                "--library", report["bindings"]["library"]["path"], "--out", root,
                "--runtime-manifest", report["bindings"]["runtime_manifest"]["path"],
                "--runtime-manifest-sha256", a.RUNTIME_SHA, "--batches", "1", "16")
        loaded = {report["bindings"]["library"]["path"]: self.c.SELECTED_SO_SHA}
        if stage == "native_feedback":
            nb = report["native_bindings"]
            args += ("--native-anchor-report", nb["anchor_path"], "--reference-library", nb["reference_library"],
                     "--reference-library-sha256", a.REFERENCE_SO,
                     "--decode-library", nb["decode_library"], "--decode-library-sha256", self.c.ALL_BATCH_SO_SHA,
                     "--decode-build-receipt", "/cache/cch/qwen36-damp-20261006/all-batch-wrapper-v3-build-v1/build-receipt.json")
            loaded.update({nb["reference_library"]: a.REFERENCE_SO, nb["decode_library"]: self.c.ALL_BATCH_SO_SHA,
                           nb["native_runtime"]["native_runtime_library_path"]: a.NATIVE_SO})
        # Actual binary evidence is INSIDE the immutable image. On this host the
        # native path need not exist; fixture reads raw bytes from parent's pinned
        # native build snapshot if available. No synthetic binary SHA is issued.
        self.native_binary_pending = False
        native_path = report.get("native_bindings", {}).get("native_runtime", {}).get("native_runtime_library_path")
        if native_path and not Path(native_path).is_file():
            self.native_binary_pending = True
        controller = self.put(root + "/controller.py", {"synthetic": "not executed"})
        child = {"schema": "damp-selected-prefill-child/v1", "stage": stage,
                 "report": a.ref_dict(report_ref), "controller_sources": {controller.path: controller.sha256},
                 "owner_proof": a.ref_dict(proof_ref),
                 "execution": {"command": "/usr/bin/python3", "args": list(args), "cwd": a.REPO,
                    "state": "completed", "returncode": 0, "error": None, "cancelled": False, "timed_out": False,
                    "stdout": "SYNTHETIC fixture only", "stderr": "", "started_ns": when,
                    "completed_ns": when + 2000000000, "duration_ms": 2000},
                 "container": {"id": "a" * 64, "image_id": self.c.IMAGE, "physical_npu_ids": [card],
                               "logical_to_physical": {"0": card}, "privileged": False},
                 "runtime_manifest": report["bindings"]["runtime_manifest"],
                 "runtime": {"soc": "Ascend910B4", "torch": "2.10.0+cpu", "torch_npu": "2.10.0.post4",
                             "opp_version_info_sha256": self.c.OPP_SHA},
                 "runtime_image_sources": self.runtime["actual_image_sources"] if stage == "native_feedback" else {},
                 "loaded_libraries": loaded,
                 "artifacts": [a.ref_dict(a.Ref(row["path"], a.digest(self.read(row["path"]))))
                               for row in report.get("artifacts", [])]}
        child_ref = self.put(root + "/child.json", child)
        opid = "exec-SOFTWARE-ONLY-" + stage
        marker = "MAIN_SELECTED_PREFILL_CHILD " + json.dumps(
            {"child": a.ref_dict(child_ref), "report": a.ref_dict(report_ref), "stage": stage}, sort_keys=True)
        terminal = {"schema": "agentweb.operation/v1", "kind": "exec", "operationId": opid,
                    "terminal": True, "status": "completed", "succeeded": True, "error": None,
                    "operation": {"routeDecision": "peer_direct", "targetPeerId": a.PEER, "result": {"record": {
                        "id": opid, "state": "completed", "exitCode": 0, "error": None,
                        "cancelled": False, "timedOut": False, "command": "/usr/bin/python3",
                        "args": ["-B", controller.path], "cwd": a.REPO, "stdout": marker, "stderr": "",
                        "durationMs": 2200}}}}
        terminal_ref = self.put(root + "/terminal.json", terminal)
        t = a.TerminalAuthority(terminal_ref, a.PEER, opid, "/usr/bin/python3", ("-B", controller.path), a.REPO)
        return a.RunAuthority(stage, report_ref, child_ref, t, "/usr/bin/python3", args, a.REPO,
                              "a" * 64, card, proof_ref, (controller,))
    def mutate_report(self, index, edit):
        old = self.runs[index]
        report = self.obj(old.report)
        edit(report)
        ref = self.put(old.report.path, report)
        self.reseal(index, report_ref=ref)
    def mutate_child(self, index, edit):
        child = self.obj(self.runs[index].child)
        edit(child)
        self.reseal(index, child_obj=child)
    def reseal(self, index, report_ref=None, child_obj=None):
        old = self.runs[index]
        new_report = report_ref or old.report
        child = child_obj or self.obj(old.child)
        child["report"] = a.ref_dict(new_report)
        child_ref = self.put(old.child.path, child)
        terminal = self.obj(old.terminal.receipt)
        terminal["operation"]["result"]["record"]["stdout"] = "MAIN_SELECTED_PREFILL_CHILD " + json.dumps(
            {"child": a.ref_dict(child_ref), "report": a.ref_dict(new_report), "stage": old.stage}, sort_keys=True)
        tref = self.put(old.terminal.receipt.path, terminal)
        self.runs[index] = replace(old, report=new_report, child=child_ref, terminal=replace(old.terminal, receipt=tref))
    def validate(self):
        return a.validate_complete(*self.runs, self.read, source_manifest=self.manifest, enabled=True)

class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.f = Fixture()
    def rejected(self):
        with self.assertRaises(a.Pending):
            self.f.validate()
    def test_default_off_before_reads(self):
        def forbidden(_):
            raise AssertionError("default OFF must not read")
        with self.assertRaises(a.Pending):
            a.validate_complete(None, None, forbidden, source_manifest=None)
    def test_matrix_contract_without_issuing_tool_authenticity(self):
        a.isolated(self.f.obj(self.f.runs[0].report), self.f.c)
        a.native_feedback(self.f.obj(self.f.runs[1].report), self.f.c)
        self.assertEqual(len(a.pack_matrix(self.f.c)), 134)
        self.assertEqual(len(a.host_labels()), 57)
    def test_full_validator_cannot_invent_missing_native_binary(self):
        # On a source-only host real image-native binary bytes are unavailable.
        # This is an expected pending authority, not a skipped test or mock SHA.
        if self.f.native_binary_pending:
            with self.assertRaises(a.Pending) as caught:
                self.f.validate()
            self.assertIn("original bytes unavailable: /vllm-workspace/vllm-ascend/vllm_ascend/", str(caught.exception))
        else:
            authority = self.f.validate()
            self.assertFalse(authority.serving_ready)
            self.assertFalse(authority.graph_supported)
            self.assertFalse(authority.performance_measurement_admitted)
            self.assertIsNone(authority.plan_index)
            with self.assertRaises(FrozenInstanceError):
                authority.serving_ready = True
    def test_isolated_run_actual_source_contract(self):
        report, libs = a.run_authority(self.f.runs[0], self.f.runtime, self.f.c, self.f.read)
        self.assertEqual(report["status"], "isolated_selected_packing_pass")
        self.assertEqual(len(libs), 1)
    def test_short_trajectory(self):
        report = self.f.obj(self.f.runs[1].report)
        report["feedback_cases"][0]["steps"].pop()
        with self.assertRaises(a.Pending):
            a.native_feedback(report, self.f.c)
    def test_each_feedback_guard_and_metric_required(self):
        report = self.f.obj(self.f.runs[1].report)
        for key in a.FEEDBACK_GUARDS:
            bad = copy.deepcopy(report)
            bad["feedback_cases"][0]["steps"][79]["guards"][key] = False
            with self.assertRaises(a.Pending):
                a.native_feedback(bad, self.f.c)
        for role in ("selected_state", "complete_state", "output"):
            bad = copy.deepcopy(report)
            bad["feedback_cases"][0]["steps"][44]["metrics"][role]["max_head_relative_l2"] = 0.01
            with self.assertRaises(a.Pending):
                a.native_feedback(bad, self.f.c)
    def test_nonfinite_other_metric_not_hidden(self):
        report = self.f.obj(self.f.runs[1].report)
        report["feedback_cases"][0]["steps"][44]["metrics"]["output"]["max_absolute"] = {"nonfinite": "nan"}
        with self.assertRaises(a.Pending):
            a.native_feedback(report, self.f.c)
    def test_packed_bitwise_false_is_diagnostic_not_new_threshold(self):
        a.native_feedback(self.f.obj(self.f.runs[1].report), self.f.c)
    def test_per_step_check_must_match_complete_row(self):
        report = self.f.obj(self.f.runs[1].report)
        next(r for r in report["checks"] if "_step_45" in r["name"])["details"]["indices"] = [-1]
        with self.assertRaises(a.Pending):
            a.native_feedback(report, self.f.c)
    def test_missing_fresh_continuation_case(self):
        report = self.f.obj(self.f.runs[1].report)
        report["cases"].pop()
        with self.assertRaises(a.Pending):
            a.native_feedback(report, self.f.c)
    def test_fixed_slots_not_dynamic(self):
        report = self.f.obj(self.f.runs[1].report)
        for row in report["feedback_cases"][0]["steps"]:
            row["indices"] = [0]
        with self.assertRaises(a.Pending):
            a.native_feedback(report, self.f.c)
    def test_all_head_status_and_pre_writer_zero(self):
        report = self.f.obj(self.f.runs[0].report)
        for label in ("P1_adjacent_PAD", "P16_guard_gaps_duplicate"):
            bad = copy.deepcopy(report)
            next(r for r in bad["cases"] if r["label"] == label)["status_rows"][0][2] = 1
            with self.assertRaises(a.Pending):
                a.isolated(bad, self.f.c)
    def test_numeric_error_retire_whole_call_no_retry(self):
        report = self.f.obj(self.f.runs[0].report)
        for edit in (lambda r: r.pop(), lambda r: r[0].update(retry_allowed=True),
                     lambda r: r[0].update(whole_call=False)):
            bad = copy.deepcopy(report)
            edit(bad["retired_calls"])
            with self.assertRaises(a.Pending):
                a.isolated(bad, self.f.c)
    def test_host_negative_and_guards_complete(self):
        report = self.f.obj(self.f.runs[0].report)
        report["host_negatives"].pop()
        with self.assertRaises(a.Pending):
            a.isolated(report, self.f.c)
    def test_reset_hash_or_changing_input_missing(self):
        report = self.f.obj(self.f.runs[0].report)
        next(r for r in report["cases"] if r["label"] == "P1_adjacent_reset_7")["raw_after_sha256"] = "f" * 64
        with self.assertRaises(a.Pending):
            a.isolated(report, self.f.c)
    def test_poisoned_after_query_not_original_error_replaced(self):
        report = self.f.obj(self.f.runs[0].report)
        next(r for r in report["checks"] if r["name"].endswith("_dispatch_and_nullable_D2H"))[
            "details"]["pointer_query_errors"] = [{"error": "poisoned"}]
        with self.assertRaises(a.Pending):
            a.isolated(report, self.f.c)
    def test_child_timeout_and_wrong_mapping(self):
        for edit in (lambda r: r["execution"].update(timed_out=True),
                     lambda r: r["container"].update(physical_npu_ids=[0]),
                     lambda r: r["loaded_libraries"].clear(),
                     lambda r: r["execution"].pop("error")):
            f = Fixture()
            f.mutate_child(0, edit)
            with self.assertRaises(a.Pending):
                a.run_authority(f.runs[0], f.runtime, f.c, f.read)
    def test_outer_terminal_must_bind_operation_direct_peer_and_raw_marker(self):
        for edit in (lambda r: r.update(succeeded=False),
                     lambda r: r["operation"].update(targetPeerId="other"),
                     lambda r: r["operation"]["result"]["record"].update(exitCode=7),
                     lambda r: r["operation"]["result"]["record"].update(stdout="unrelated success"),
                     lambda r: r["operation"]["result"]["record"].update(timedOut=True)):
            f = Fixture()
            old = f.runs[0]
            terminal = f.obj(old.terminal.receipt)
            edit(terminal)
            ref = f.put(old.terminal.receipt.path, terminal)
            bad = replace(old, terminal=replace(old.terminal, receipt=ref))
            with self.assertRaises(a.Pending):
                a.run_authority(bad, f.runtime, f.c, f.read)
    def test_source_byte_and_artifact_hash_missing(self):
        f = self.f
        artifact = f.obj(f.runs[0].report)["artifacts"][0]["path"]
        f.memory[artifact] += b"tampered"
        with self.assertRaises(a.Pending):
            a.run_authority(f.runs[0], f.runtime, f.c, f.read)
    def test_serving_promotion_and_partial_scope_rejected(self):
        for edit in (lambda r: r.update(serving_ready=True),
                     lambda r: r.update(graph_supported=True),
                     lambda r: r.update(limits={"state": 0.001, "output": .00303}),
                     lambda r: r.update(npu_executed=False)):
            f = Fixture()
            f.mutate_report(0, edit)
            with self.assertRaises(a.Pending):
                a.run_authority(f.runs[0], f.runtime, f.c, f.read)
    def test_frozen_source_changed_is_not_self_authorized(self):
        path = a.REPO + "/" + a.BASE + "/evidence.py"
        self.f.memory[path] = self.f.read(path) + b"\\n# synthetic tamper"
        with self.assertRaises(a.Pending) as caught:
            self.f.validate()
        self.assertIn("byte SHA mismatch: " + path, str(caught.exception))
    def test_report_sha_bytes_not_status_parser(self):
        f = self.f
        f.memory[f.runs[0].report.path] += b" "
        with self.assertRaises(a.Pending):
            a.run_authority(f.runs[0], f.runtime, f.c, f.read)
    def test_strict_json_duplicate_nan_and_relative_ref(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}'):
            with self.assertRaises(a.Pending):
                a.json_bytes(raw)
        with self.assertRaises(a.Pending):
            a.Ref("relative/report.json", "a" * 64)
    def test_missing_authority_stays_pending(self):
        with self.assertRaises(a.Pending):
            a.validate_complete(None, None, self.f.read, source_manifest=self.f.manifest, enabled=True)

if __name__ == "__main__":
    unittest.main()

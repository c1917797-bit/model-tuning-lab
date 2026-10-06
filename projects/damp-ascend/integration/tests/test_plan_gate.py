"""Manifest validation only: synthetic fixtures are NOT experimental receipts."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from damp_integration.contract import GDN_LAYERS, Unsupported
from damp_integration.plan import MODEL_CONFIG_SHA256, PlanStore, sha256

class PlanGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.library = self.root / "synthetic-library-bytes"
        self.library.write_bytes(b"validator fixture only")
        self.plan = self.root / "synthetic-plan-bytes"
        self.plan.write_bytes(b"not a loadable plan")
        guards = {name: True for name in (
            "untouched_regions_bitwise", "storage_pointers_stable",
            "static_inputs_unchanged", "turn_inputs_unchanged", "indices_unchanged")}
        self.gate = {"schema":"damp-independent-packed-oracle/v1", "status":"numerical_pass",
                     "mode":"npu-operator", "matrix_class":"complete-160-step", "steps":160,
                     "operator_library":{"sha256":sha256(self.library)},
                     "checks":[{"passed":True}],
                     "recurrence_cases":[{"batch":b, "mode":"value-major-custom-operator",
                         "status":"passed", "steps":[{"passed":True, "guards":guards} for _ in range(160)]}
                         for b in (1,16)]}
        self.receipt = self.root / "synthetic-validator-receipt.json"
        self.manifest = {
            "schema":"damp-serving-plan/v1", "model_config_sha256":MODEL_CONFIG_SHA256,
            "tp":4, "purpose":"integration-smoke", "operator_sha256":sha256(self.library),
            "operator_gate":{"compressed_recurrence":True, "untouched_slots":True,
                             "changing_inputs":True, "multiple_steps":True},
            "plans":[{"rank":r,"layer":l,"path":str(self.plan),"sha256":sha256(self.plan)}
                     for r in range(4) for l in GDN_LAYERS]}
        self.manifest_path = self.root / "manifest.json"

    def tearDown(self):
        self.temp.cleanup()

    def load(self):
        self.receipt.write_text(json.dumps(self.gate))
        self.manifest["operator_gate"].update(receipt_path=str(self.receipt), receipt_sha256=sha256(self.receipt))
        self.manifest_path.write_text(json.dumps(self.manifest))
        return PlanStore(self.manifest_path, self.library, None)

    def test_all_rank_layer_coverage(self):
        self.assertEqual(len(self.load().entries), 192)

    def test_pytorch_or_smoke_or_failed_not_custom_operator_gate(self):
        for mutation in ({"mode":"npu-reference"}, {"mode":"cpu"}, {"status":"failed"},
                         {"matrix_class":"smoke-only"}, {"steps":1}):
            with self.subTest(mutation=mutation):
                original = copy.deepcopy(self.gate)
                self.gate.update(mutation)
                with self.assertRaises(Unsupported):
                    self.load()
                self.gate = original

    def test_missing_layer_and_duplicate(self):
        original = copy.deepcopy(self.manifest)
        self.manifest["plans"].pop()
        with self.assertRaises(Unsupported):
            self.load()
        self.manifest = original
        self.manifest["plans"].append(self.manifest["plans"][0])
        with self.assertRaises(Unsupported):
            self.load()

    def test_binary_drift(self):
        self.gate["operator_library"]["sha256"] = "0"*64
        with self.assertRaises(Unsupported):
            self.load()

    def test_untouched_guard_cannot_be_omitted(self):
        self.gate["recurrence_cases"][0]["steps"][0]["guards"].pop("untouched_regions_bitwise")
        with self.assertRaises(Unsupported):
            self.load()

    def test_full_calibration_cannot_be_declared_without_data(self):
        self.manifest["purpose"] = "calibrated-candidate"
        with self.assertRaises(Unsupported):
            self.load()

if __name__ == "__main__":
    unittest.main()


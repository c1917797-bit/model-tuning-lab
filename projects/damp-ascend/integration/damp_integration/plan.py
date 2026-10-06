"""External immutable calibration/plan identity; never supplies fake full calibration."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import math
from .contract import GDN_LAYERS, require

MODEL_CONFIG_SHA256 = "69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c"

def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

@dataclass
class DevicePlan:
    pk: object
    pv: object
    inv_pv: object
    sr: object

class PlanStore:
    def __init__(self, path, library, torch):
        self.torch = torch
        manifest_path = Path(path).resolve(strict=True)
        require(manifest_path.is_file() and manifest_path.stat().st_size < 4 * 1024 * 1024,
                "plan manifest missing/oversized")
        self.manifest = json.loads(manifest_path.read_text())
        m = self.manifest
        require(m.get("schema") == "damp-serving-plan/v1", "unsupported plan schema")
        require(m.get("model_config_sha256") == MODEL_CONFIG_SHA256 and m.get("tp") == 4,
                "plan does not match installed checkpoint/TP4")
        require(m.get("purpose") in ("integration-smoke", "calibrated-candidate"), "unlabelled plan purpose")
        if m["purpose"] == "calibrated-candidate":
            calibration = m.get("calibration", {})
            require(calibration.get("full_manifest_sha256") and calibration.get("train_only") is True
                    and calibration.get("prompts") == 36 and calibration.get("input_tokens") == 1024
                    and calibration.get("output_tokens") == 4096, "full calibration identity incomplete")
            require(calibration.get("manifest_path") and sha256(calibration["manifest_path"]) ==
                    calibration["full_manifest_sha256"], "full calibration bytes missing/drifted")
        require(sha256(library) == m.get("operator_sha256"), "operator library hash mismatch")
        # Parent writes this receipt only after actual independently frozen NPU gates.
        receipt = m.get("operator_gate", {})
        require(receipt.get("compressed_recurrence") is True and receipt.get("untouched_slots") is True
                and receipt.get("changing_inputs") is True and receipt.get("multiple_steps") is True,
                "compressed operator numerical gate is not complete")
        require(receipt.get("receipt_path") and sha256(receipt["receipt_path"]) == receipt.get("receipt_sha256"),
                "operator gate receipt missing/hash mismatch")
        gate = json.loads(Path(receipt["receipt_path"]).read_text())
        require(gate.get("schema") == "damp-independent-packed-oracle/v1" and
                gate.get("status") == "numerical_pass" and gate.get("mode") == "npu-operator" and
                gate.get("matrix_class") == "complete-160-step" and gate.get("steps") == 160,
                "receipt is not the complete real-NPU compressed-operator gate")
        require(gate.get("operator_library", {}).get("sha256") == m["operator_sha256"],
                "passing receipt covers a different operator binary")
        checks = gate.get("checks", [])
        require(checks and all(c.get("passed") is True for c in checks), "receipt has missing/failed checks")
        cases = gate.get("recurrence_cases", [])
        require(len(cases) == 2 and {c.get("batch") for c in cases} == {1, 16},
                "complete B1/B16 compressed gate required")
        for case in cases:
            require(case.get("mode") == "value-major-custom-operator" and case.get("status") == "passed"
                    and len(case.get("steps", [])) == 160, "incomplete/failed packed case")
            for step in case["steps"]:
                require(step.get("passed") is True and
                        all(step.get("guards", {}).get(k) is True for k in (
                            "untouched_regions_bitwise", "storage_pointers_stable",
                            "static_inputs_unchanged", "turn_inputs_unchanged", "indices_unchanged")),
                        "state/input guard missing/failed in operator receipt")
        self.entries = {}
        for entry in m.get("plans", []):
            key = (entry.get("rank"), entry.get("layer"))
            require(key not in self.entries, "duplicate layer/rank plan")
            require(sha256(entry["path"]) == entry.get("sha256"), "plan bytes drift")
            self.entries[key] = entry
        require(set(self.entries) == {(r, l) for r in range(4) for l in GDN_LAYERS},
                "all 48 GDN layers and all TP4 ranks are mandatory")
        self.resident = {}

    def get(self, rank, layer, device):
        key = (int(rank), int(layer), str(device))
        if key in self.resident:
            return self.resident[key]
        torch = self.torch
        entry = self.entries[key[:2]]
        # Compact static plans only; no recurrent state can exist in this file.
        require(sha256(entry["path"]) == entry["sha256"], "plan changed after startup")
        raw = torch.load(entry["path"], map_location="cpu", weights_only=True)
        require(set(raw) == {"pk", "pv", "sr"}, "plan contains unknown tensors/persistent state")
        pk, pv, sr = (raw[name] for name in ("pk", "pv", "sr"))
        require(all(tuple(t.shape) == (12, 128) and t.device.type == "cpu" for t in (pk, pv, sr)),
                "plan must contain CPU [12,128] tensors")
        require(pk.dtype == pv.dtype == torch.int32 and sr.dtype == torch.float32, "plan dtype mismatch")
        ordered = list(range(128))
        require(all(sorted(row) == ordered for row in pk.tolist()) and
                all(sorted(row) == ordered for row in pv.tolist()), "invalid plan permutation")
        require(all(math.isfinite(x) and x > 0 for row in sr.tolist() for x in row), "invalid SR")
        inv = torch.empty_like(pv)
        for head, row in enumerate(pv.tolist()):
            for i, v in enumerate(row):
                inv[head, v] = i
        plan = DevicePlan(*(t.to(device=device).contiguous() for t in (pk, pv, inv, sr)))
        self.resident[key] = plan
        return plan

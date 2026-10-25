"""HOST-only G1-G4 current-runtime full40 audit; never launches a workload.

Run from the owning workstream. The new auditor is separately hash-bound by
r26_host_audit.source_sha256 and must not enter the frozen inference manifest.
One phase is not a paired/repeated matrix, task-quality or deployment decision.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

_WS = Path(__file__).resolve().parent.parent
if str(_WS) not in sys.path:
    sys.path.insert(0, str(_WS))

from audit_r18_terminal_base import audit_r18_base
from audit_r18_partition_performance import audit_timed_partition
from audit_r19_lazy_performance import validate_lazy_receipts
from audit_r20_metadata_canary_v2 import audit_metadata_receipts
from audit_r21_c2_finite_canary import audit_finite_receipts
from audit_r24_c2_snapshot_canary import audit_snapshot_receipts
from audit_formal_full40_pdc import bind_full40_pic_starts, audit_full40_pdc
from audit_formal_pdc_terminal import validate_contract as validate_g4_pdc_contract
from formal_pdc_metrics_tp4 import check_contract as check_native_pdc_contract
from native_pdc_metrics import audit_delta

_SELF = "host_audits/r26_group_performance.py"
_AXES = {"G1": (False, False), "G2": (False, True),
         "G3": (True, False), "G4": (True, True)}
_GROUP_SOURCE = "verified-native-full-attention-spec"


def _bytes(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("regular immutable host-audit input required")
    return path.read_bytes()


def _json(path):
    value = json.loads(_bytes(path))
    if not isinstance(value, dict):
        raise ValueError("host-audit JSON object required")
    return value


def _sha(path):
    return hashlib.sha256(_bytes(path)).hexdigest()


def _inside(base, name):
    if not isinstance(name, str) or not name:
        raise ValueError("exact relative source path required")
    path = (base / name).resolve()
    if Path(name).is_absolute() or not path.is_relative_to(base.resolve()):
        raise ValueError("host-audit source escaped owning workstream")
    return path


def _host_binding(c, base):
    binding = c.get("r26_host_audit")
    if (not isinstance(binding, dict)
            or set(binding) != {"source_sha256"}
            or not isinstance(binding["source_sha256"], dict)
            or set(binding["source_sha256"]) != {_SELF}):
        raise ValueError("separate exact production-only R26 host binding required")
    path = _inside(base, _SELF)
    if path != Path(__file__).resolve() or _sha(path) != binding["source_sha256"][_SELF]:
        raise ValueError("R26 host auditor source drift")
    return dict(binding["source_sha256"])


def _prerequisite(c, base):
    """Preserve the accepted R24 ON gate from the frozen R25 outer audit."""
    prior_name = c.get("required_canary_contract")
    prior_path = _inside(base, prior_name)
    prior_sha = _sha(prior_path)
    if prior_sha != c.get("required_canary_sha256"):
        raise ValueError("required R24 canary contract drift")
    prior = _json(prior_path)
    if prior.get("controller_sha256") != c.get("controller_sha256"):
        raise ValueError("accepted canary/current controller identity mismatch")
    evidence = c.get("numerical_prerequisite_evidence")
    if not isinstance(evidence, dict):
        raise ValueError("accepted R24 ON evidence binding required")
    evidence_path = _inside(base, evidence.get("path"))
    if _sha(evidence_path) != evidence.get("sha256"):
        raise ValueError("accepted R24 ON evidence missing or drifted")
    proof = _json(evidence_path)
    accepted = proof.get("audit", {})
    if (proof.get("arm") != "ON" or proof.get("contract") != prior_name
            or proof.get("contract_sha256") != prior_sha
            or proof.get("raw_root") != prior.get("raw_root")
            or not isinstance(accepted, dict)
            or accepted.get("bounded_canary_valid") is not True
            or accepted.get("live_release_verified") is not True):
        raise ValueError("R24 ON prerequisite report/contract/raw identity not accepted")
    raw = Path(proof["raw_root"])
    digests = proof.get("raw_sha256")
    if (not raw.is_absolute() or raw.is_symlink()
            or not isinstance(digests, dict)
            or not {"result.json", "responses.json", "release.json"}.issubset(digests)):
        raise ValueError("accepted R24 immutable raw digest inventory missing")
    for name, digest in digests.items():
        _inside(raw, name)
        if _sha(raw / name) != digest:
            raise ValueError("R24 immutable raw evidence drift")
    return dict(contract=prior_name, contract_sha256=prior_sha,
        evidence_path=evidence["path"], evidence_sha256=evidence["sha256"],
        raw_root=str(raw), raw_sha256=dict(digests),
        scope="accepted bounded R24 ON; not native/PIC lossless equivalence")


def _manifest(c, base):
    name = c.get("successor_manifest")
    path = _inside(base, name)
    manifest = _json(path)
    runtime = manifest.get("source_sha256")
    if not isinstance(runtime, dict) or not runtime:
        raise ValueError("frozen inference source closure required")
    if any(Path(n).parts and Path(n).parts[0] == "host_audits" for n in runtime):
        raise ValueError("HOST-only audit must not enter inference allowlist")
    for name, digest in runtime.items():
        if _sha(_inside(base, name)) != digest:
            raise ValueError("inference source drift: " + name)
    config_name = manifest.get("config")
    config_path = _inside(base, config_name)
    if runtime.get(config_name) != _sha(config_path):
        raise ValueError("runtime configuration binding missing")
    sources = c.get("baseline_host_source_sha256") or c.get("cache_diagnostic", {}).get("source_sha256", {})
    digest = _sha(path)
    if not isinstance(sources, dict) or sources.get(c["successor_manifest"]) != digest:
        raise ValueError("common successor manifest binding absent")
    return _json(config_path), digest


def validate_policy(c, cfg):
    """Keep the actual performance-group name; validate its two real axes."""
    group = c.get("performance_group")
    if group not in _AXES:
        raise ValueError("actual G1-G4 group required")
    algorithm, pdc = _AXES[group]
    if (c.get("formal_performance") is not True or c.get("formal_quality") is not False
            or c.get("enable_prefix_caching") is not pdc
            or c.get("physical_npus") != [0, 1, 2, 3]
            or type(c.get("tp")) is not int or c["tp"] != 4
            or c.get("enforce_eager") is not True
            or type(c.get("performance_round")) is not int
            or c["performance_round"] not in (1, 2, 3)):
        raise ValueError("formal group/PDC/eager/physical identity contradiction")
    if (cfg.get("prefill_prompt_snapshot") is not True
            or type(cfg.get("prompt_snapshot_probe_batches")) is not int
            or cfg["prompt_snapshot_probe_batches"] != 0
            or cfg.get("c1_performance_mode") is not True
            or cfg.get("c1_layer_shadow_validation") is not False
            or cfg.get("c1_first_divergence") is not False
            or cfg.get("c1_async_material_verify") is not False
            or c.get("protocol_notes", {}).get("timed_diagnostics") is not False):
        raise ValueError("timed mode/probe/shadow/transfer verification contradiction")
    if (c.get("transfer_treatment") != ("async" if algorithm else "native")
            or cfg.get("c1_async_material_transfer") is not algorithm
            or c.get("lazy_snapshot_treatment") != ("on" if algorithm else "native")
            or cfg.get("c1_lazy_initial_snapshot") is not algorithm
            or cfg.get("c1_partitioned_render") is not algorithm
            or c.get("r18_partitioned_acceptance", {}).get("enabled") is not algorithm):
        raise ValueError("timed transfer/lazy/partition axis contradiction")
    if not algorithm:
        if (c.get("cache_diagnostic")
                or c.get("independent_acceptance", {}).get("require_hypic_markers_absent") is not True):
            raise ValueError("native group must have no algorithm and explicit marker absence")
    else:
        diagnostic = c.get("cache_diagnostic")
        if (not isinstance(diagnostic, dict)
                or diagnostic.get("compact_manifest") != c.get("successor_manifest")):
            raise ValueError("algorithm group active manifest mismatch")
        required = ("c1_packed_wave", "native_decode_batch", "c1_layer_completion_barrier",
                    "c2_layer_completion_barrier", "forward_metadata_snapshot",
                    "c2_layer_finite_gate", "c1_short_suffix_recurrent",
                    "c2_block_table_snapshot", "c2_block_table_diagnostic")
        if any(cfg.get(name) is not True for name in required):
            raise ValueError("current algorithm safety/snapshot profile missing")
        accept = c.get("c2_snapshot_acceptance")
        if (not isinstance(accept, dict) or accept.get("enabled") is not True
                or accept.get("group_source") != _GROUP_SOURCE):
            raise ValueError("frozen independent snapshot acceptance required")
    return dict(group=group, algorithm_on=algorithm, pdc_on=pdc)


def _events(raw, prefix):
    rows = []
    for path in sorted((raw / "diagnostics").glob(prefix + "*.jsonl")):
        for line in _bytes(path).decode("utf-8").splitlines():
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError("structured immutable worker event required")
            rows.append(event)
    return rows


def _algorithm_evidence(c, cfg, report, events, manifest, algorithm):
    partition = audit_timed_partition(events, manifest, enabled=algorithm)
    if not algorithm:
        return {"partition": partition}
    workers = {int(rank): pid for rank, pid in report["hot"]["worker_pids"].items()}
    installs = [e for e in events if e.get("event") == "compact_hypic_hooks_installed"]
    for e in installs:
        for name in ("c1_async_material_transfer", "prefill_prompt_snapshot",
                     "native_decode_batch", "c1_layer_completion_barrier",
                     "c2_layer_completion_barrier", "c1_short_suffix_recurrent",
                     "forward_metadata_snapshot", "c2_layer_finite_gate",
                     "c2_block_table_snapshot", "c2_block_table_diagnostic"):
            if e.get(name) is not True:
                raise ValueError("actual worker algorithm profile mismatch")
        if (e.get("c1_async_material_verify") is not False
                or type(e.get("prompt_snapshot_probe_batches")) is not int
                or e["prompt_snapshot_probe_batches"] != 0):
            raise ValueError("actual worker timed transfer/probe mismatch")
    return {
        "partition": partition,
        "lazy": validate_lazy_receipts(events, True),
        "metadata_snapshot": audit_metadata_receipts(events, workers, manifest),
        "c2_finite": audit_finite_receipts(events, workers, manifest),
        # Do not filter warmups/native captures or mixed forwards to measured IDs.
        "c2_block_table_snapshot": audit_snapshot_receipts(
            events, workers, manifest, enabled=True, expected_group=None,
            expected_layers=c["c2_snapshot_acceptance"].get("layers", ())),
    }


def _native_pdc_observation(c, contract_path, raw):
    check_native_pdc_contract(c)
    receipt_path = raw / "native-pdc-observation.json"
    receipt = _json(receipt_path)
    start = _json(raw / "service-start.json")
    spec = c["native_pdc_metrics"]
    if (receipt.get("schema") != "native-pdc-metrics/v1" or receipt.get("error")
            or receipt.get("container_id") != start["container_id"]
            or receipt.get("image") != c["image"]
            or receipt.get("contract_sha256") != _sha(contract_path)
            or receipt.get("official_logger_sha256") != spec["official_logger_sha256"]
            or receipt.get("observer_sources") != spec["source_sha256"]):
        raise ValueError("native observer source/CID/contract/error identity mismatch")
    measured = audit_delta(receipt["before"], receipt["after"])
    if receipt.get("audit") != measured:
        raise ValueError("native observer independent counter recompute mismatch")
    return dict(measured, observation_sha256=_sha(receipt_path))


def _g4_pdc_evidence(c, base, raw, report, events, manifest):
    # Reuse only the G4 policy/source guard and pure full40 helpers, not the
    # older outer R15 auditor whose packed-state schedule differs.
    validate_g4_pdc_contract(c, base)
    unit = _json(raw / "performance-unit.json")
    spec = c["formal_token_artifact"]
    mapping = report["request_map"]
    workers = {int(rank): pid for rank, pid in report["hot"]["worker_pids"].items()}
    starts = bind_full40_pic_starts(spec["path"], spec["sha256"], unit["results"], mapping)
    scheduler = _events(raw, "compact-scheduler-")
    return audit_full40_pdc(events, scheduler, mapping, workers, starts,
                            manifest_sha256=manifest)


def audit(path, *, live_release=False):
    """Read one actual phase; never rename groups, launch or relax PDC proof."""
    cp = Path(path).resolve()
    base = cp.parent
    if Path.cwd().resolve() != base:
        raise ValueError("run R26 host audit from the owning workstream")
    c = _json(cp)
    binding = _host_binding(c, base)
    prerequisite = _prerequisite(c, base)
    cfg, manifest = _manifest(c, base)
    policy = validate_policy(c, cfg)
    if policy["pdc_on"]:
        check_native_pdc_contract(c)
    # Unchanged actual-source/full40/physical/isolation/release base.
    report = audit_r18_base(cp, live_release=live_release)
    report["numerical_prerequisite"] = prerequisite
    raw = Path(c["raw_root"])
    events = _events(raw, "compact-worker-")
    report.update(_algorithm_evidence(c, cfg, report, events, manifest, policy["algorithm_on"]))
    if policy["pdc_on"]:
        report["native_pdc_observed"] = _native_pdc_observation(c, cp, raw)
    if policy["group"] == "G4":
        report["full40_pdc"] = _g4_pdc_evidence(c, base, raw, report, events, manifest)
    report["r26_host_audit"] = dict(policy, source_sha256=binding,
        contract_sha256=_sha(cp), retained_evidence_overhead_in_e2e=True)
    report["scope"] = (
        "one actual current-source G1/G2/G3/G4 full40 phase; retained safety/"
        "mechanism receipt overhead included; paired three-round matrix, task "
        "quality, lifecycle and deployment acceptance remain separate; G2 PDC "
        "counter evidence is aggregate, G4 additionally requires all40 PIC proof")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True)
    parser.add_argument("--live-release", action="store_true")
    args = parser.parse_args()
    print(json.dumps(audit(args.contract, live_release=args.live_release)))

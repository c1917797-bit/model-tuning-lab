"""Stdlib-only preregistered contract for general_sr_native_gate.py."""
from __future__ import annotations

STEPS = 160
LIMITS = {"state": 1e-5, "output": 0.00303}
ANCHOR_VARIANTS = ("SR1_identity_plans", "SR1_perHv_permutations", "power2_perHv_permutations")
GENERAL_VARIANTS = ("general_positive_FP32_random", "general_positive_FP32_near_half_stress")
PREPARE_INPUT_NAMES = ("q", "hi", "pk", "pv", "inv_pv", "sr")
NATIVE_COMMIT = "5cb98caaadeff42b5b62b996e34bb2aaa29d20fd"
NATIVE_HEADER_SHA = "96e6d9667af1e3457316ffce92a8a983fcb90096df08e3efd13ec0b35b8b1c5b"


def validate_device_proof(proof, now_ns):
    """External parent authority only; never substitute this for a live check."""
    ids = proof.get("physical_npu_ids")
    if not isinstance(ids, list) or not ids or len(ids) != len(set(ids)):
        raise ValueError("physical_npu_ids must be a unique nonempty list")
    if any(type(x) is not int or x not in (4, 5, 6, 7) for x in ids):
        raise ValueError("only physical NPU4-7 authorized")
    mapping = proof.get("logical_to_physical")
    if not isinstance(mapping, dict) or mapping.get("0") != 4:
        raise ValueError("logical0 must be freshly proved physical4")
    if any(type(v) is not int or v not in ids for v in mapping.values()):
        raise ValueError("mapping must stay in declared physical IDs")
    if proof.get("privileged") is not False:
        raise ValueError("nonprivileged mapping required")
    if proof.get("exclusive_resource_check_passed") is not True:
        raise ValueError("fresh exclusive resource check required")
    when = proof.get("observed_at_unix_ns")
    if type(when) is not int or not 0 <= now_ns-when <= 1800*10**9:
        raise ValueError("device proof must be nonfuture and <=30 minutes old")
    return True


def validate_source_manifest(manifest, reference_hashes, candidate_hashes):
    """Parent must bind audited source to the independently built libraries."""
    if manifest.get("native_commit") != NATIVE_COMMIT:
        raise ValueError("native source commit mismatch")
    if manifest.get("native_header_sha256") != NATIVE_HEADER_SHA:
        raise ValueError("ordinary DAV2201 native header identity mismatch")
    if manifest.get("reference_source_hashes") != reference_hashes:
        raise ValueError("reference source/build binding mismatch")
    if manifest.get("candidate_source_hashes") != candidate_hashes:
        raise ValueError("candidate source/build binding mismatch")
    for name in ("image_id", "native_runtime_library_path", "native_runtime_library_sha256"):
        if not isinstance(manifest.get(name), str) or not manifest[name]:
            raise ValueError("manifest requires " + name)
    digest = manifest["native_runtime_library_sha256"]
    if len(digest) != 64 or any(x not in "0123456789abcdef" for x in digest):
        raise ValueError("native runtime library must have a frozen lowercase SHA256")
    if manifest.get("source_contract_passed") is not True:
        raise ValueError("exact source-contract receipt required before NPU")
    return True


def assert_matrix_order(cases, require_complete_anchor=False):
    expected = {(b, v) for b in (1, 16) for v in ANCHOR_VARIANTS}
    seen = set()
    general_seen = False
    for case in cases:
        if case.get("stage") == "anchor":
            if general_seen:
                raise ValueError("anchor may not run after compressed general-SR stage")
            key = (case.get("batch"), case.get("variant"))
            if key not in expected or key in seen:
                raise ValueError("unknown or duplicate anchor case")
            if case.get("status") != "passed":
                raise ValueError("general-SR cannot use a failed/incomplete anchor")
            seen.add(key)
        elif case.get("stage") == "general":
            if seen != expected:
                raise ValueError("ALL six anchors must pass before ANY general-SR")
            general_seen = True
        else:
            raise ValueError("unknown stage")
    if require_complete_anchor and seen != expected:
        raise ValueError("six B1/B16 native anchors missing")
    return True

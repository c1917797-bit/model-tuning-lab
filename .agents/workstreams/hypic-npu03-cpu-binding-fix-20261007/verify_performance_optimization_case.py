#!/usr/bin/env python3
"""Replay the bounded official-config optimization choice from raw NPU runs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

from verify_inference_tuning_loop_case import verify as verify_formal_repeats


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PARENT = REPO / ".agents/experiments/exp-20261007-hypic-npu03-comm-root.yaml"
EXPERIMENT = REPO / ".agents/experiments/exp-20261007-hypic-npu03-cpu-binding-fix.yaml"
PROBE_ROOT = Path("/cache/cch/hypic-npu03-comm-root-20261007")
RAW_SHA256 = {
    "graph-on/probe-contract.json": "dcdd79886b4b004def99ef3e21bb03a93d4ad8bd5df326dc67872b73ebee8a71",
    "binding-off/probe-contract.json": "d52fd46e6ba0c7b74798b69ad1929db7c59119cfb2b1b26b4461807bf60212e1",
    "graph-on/profiles/no-cache/decode/profile-workload.json": "84c9a9cafe0f5d0754805d68a8e25e55741416d8a4cead5fa462a32b6ede2ced",
    "binding-off/profiles/no-cache/decode/profile-workload.json": "46a60423e2d42512d799494222611421e9568890cabb9649dfb983f033a2fa7f",
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def verify() -> dict:
    parent = yaml.safe_load(PARENT.read_text(encoding="utf-8"))
    record = yaml.safe_load(EXPERIMENT.read_text(encoding="utf-8"))
    require(record["parent_diagnosis"] == parent["id"]
            and record["status"] == "partial_component",
            "diagnosis or partial decision drift")
    require(record["candidate"]["class"] == "supported_upstream_configuration"
            and record["candidate"]["primary_variable"]
            == "Add only --additional-config '{\"enable_cpu_binding\":false}' to the frozen serving command.",
            "candidate mechanism drift")
    require("approximately 358 ms/token" in record["candidate"]["opportunity_bound"],
            "predeclared opportunity bound absent")
    require("binding_off_probe_result" in parent["measured_20261007"]
            and "Partially overlapping" in parent["measured_20261007"]["binding_off_probe_result"]["classification"],
            "source-level cause uncertainty lost")
    raw = {}
    for relative, expected in RAW_SHA256.items():
        path = PROBE_ROOT / relative
        require(path.is_file(), f"probe artifact missing: {path}")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == expected,
                f"probe artifact hash drift: {path}")
        raw[relative] = json.loads(path.read_text(encoding="utf-8"))
    control = raw["graph-on/probe-contract.json"]
    candidate = raw["binding-off/probe-contract.json"]
    for key in ("image", "source_commit", "source_snapshot_sha256",
                "benchmark_sha256", "physical_npus"):
        require(control[key] == candidate[key], f"probe identity drift: {key}")
    require(candidate["physical_npus"] == [0, 1, 2, 3]
            and candidate["diagnostic_only"] is True
            and control["diagnostic_only"] is True,
            "probe lane/scope drift")
    require(candidate["service_command"] == control["service_command"]
            + " --additional-config '{\"enable_cpu_binding\":false}'",
            "probe changed more than the supported switch")
    ctrl = raw["graph-on/profiles/no-cache/decode/profile-workload.json"]
    cand = raw["binding-off/profiles/no-cache/decode/profile-workload.json"]
    require(ctrl["config"] == cand["config"], "probe workload drift")
    for arm, result in (("control", ctrl), ("candidate", cand)):
        summary = result["summary"]
        require(summary["fixed_output_verified"] is True
                and summary["fixed_output_requests"] == 4
                and summary["failed"] == 0,
                f"{arm} probe validity failure")
    control_tpot = float(ctrl["summary"]["tpot_weighted_ms"])
    candidate_tpot = float(cand["summary"]["tpot_weighted_ms"])
    require(candidate_tpot < control_tpot, "probe disproof signal observed")
    formal = verify_formal_repeats()
    require(formal["raw_runs_verified"] == 6
            and formal["candidate_exact_output_and_cleanup_verified"] == 3,
            "formal screen/repetition evidence incomplete")
    return {
        "schema": "ascend-performance-optimization-bounded-replay/v1",
        "candidate_class": record["candidate"]["class"],
        "probe_control_tpot_ms": control_tpot,
        "probe_candidate_tpot_ms": candidate_tpot,
        "probe_tpot_reduction_percent": 100 * (control_tpot - candidate_tpot) / control_tpot,
        "probe_raw_json_hashes_verified": len(RAW_SHA256),
        "formal_raw_runs_verified": formal["raw_runs_verified"],
        "formal_median_tpot_reduction_percent": formal["median_tpot_reduction_percent"],
        "underlying_cpu_pool_subcause_proven": False,
        "full_2048_quality_verified": False,
        "optimization_accepted": False,
    }


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))
